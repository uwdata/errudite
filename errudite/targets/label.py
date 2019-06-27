import traceback
from typing import Union, List, Dict, Callable
from collections import defaultdict
from .target import Target
from .interfaces import LabelKey
from ..processor import SpacyAnnotator, spans_to_json
from ..utils.helpers import convert_list
from ..utils.check import DSLValueError


class Label(Target):
    """
    ``Label`` is a special subclass of Target, denoting *groundtruth* 
    and *prediction*. It takes an additional input ``model``, which 
    predictor the label is producied by. For groundtruths, make sure 
    this model is ``groundtruth``.

    Parameters
    ----------
    model : str
        Denote the predictor the label is producied by. 
        For groundtruths, make sure this model is ``groundtruth``.
    qid : str
        The id of the instance.
    text : str
        The raw text will be processed with SpaCy.
    vid : int, optional
        The version, by default 0. When an instance/a target is rewritten, the version 
        will automatically grow.
    annotator : SpacyAnnotator, optional
        The annotator, by default None. If None, use the default annotator.
    metas : Dict[str, any], optional
        Additional metas associated with a target, in the format of {key: value}, by default {}
    """
    
    #: ``task_evaluation_func(pred: str, labels: Union[str, List[str]]) -> Dict[str, float]``, 
    # the evaluation function that accepts pred and groundtruths, and 
    #: return a dict of metrics: { metric_name: metric_score }
    task_evaluation_func = lambda pred, labels: {}

    #: The primary task metric name, ideally a key of ``task_evaluation_func`` 's return.
    #: This is what DSL resolve to when we set ``perform_name="DEFAULT"``
    task_primary_metric: str = 'accuracy'

    def __init__(self, 
        model: str,
        qid: str, 
        text: str, vid: int=0, 
        metas: Dict[str, any]={},
        annotator: SpacyAnnotator=None) -> None:
        Target.__init__(self, qid, text, vid, metas=metas, annotator=annotator)
        self.model = model
        self.label = text
        self.is_groundtruth = model == 'groundtruth'
        self.perform = { }

    def key(self) -> LabelKey:
        """Return the key of the label as a Named Tuple.

        Returns
        -------
        InstanceKey
            The key: ``LabelKey(qid=self.qid, vid=self.vid, model=self.model, label=self.label)``
        """
        return LabelKey(qid=self.qid, vid=self.vid, model=self.model, label=self.label)

    def generate_id(self) -> str:
        """Get the string key: 'qid:{self.qid}-vid:{self.vid}-model:{self.model}'
        
        Returns
        -------
        str
            The stringed key.
        """
        return f'qid:{self.qid}-vid:{self.vid}-model:{self.model}'
    
    def get_label(self) -> str:
        """Get the label string.
        
        Returns
        -------
        str
            The string
        """
        return self.label
    
    def is_incorrect(self) -> bool:
        """Check if the prediction is correct.
        This is done by checking whether the primary metric 
        ``Label.task_primary_metric < 1``.
        
        Returns
        -------
        bool
            If the model is incorrect.
        """
        try:
            return self.get_perform(Label.task_primary_metric) < 1
        except:
            return False
    
    def set_perform(self, **kwargs) -> None:
        """All kwargs should be a {name: score} format. Can freely input."""
        """
        Save the performance metrics. It accepts ``**kwargs``, so the names of 
        the metrics can be easily customized. It's supposed to be called 
        by ``instance.set_perform(accuracy=0.1, confidence=0.5).``
        
        Returns
        -------
        None
            [description]
        """
        for key, val in kwargs.items():
            if key is None or val is None:
                continue
            self.perform[str(key)] = float(val)
    
    def get_perform(self, perform_name: str=None) -> float:
        """Get a performance metric from this label with the performance name.
        
        Parameters
        ----------
        perform_name : str, optional
            The selected model, by default ``None``. 
            If ``None``, resolve to ``Label.primary_task_metric``.
        
        Returns
        -------
        float
            The performance score. If the perform name does not exist, return 0.
        """
        output = 0
        perform_name = Label.resolve_default_perform_name(perform_name)
        try:
            if perform_name in self.perform:
                output = self.perform[perform_name]
            else:
                raise DSLValueError(f"Invalid perform name [ {perform_name} ] to {self}.")
        except DSLValueError as e:
            raise e
        finally:
            return output
        
    
    def compute_perform(self, 
        groundtruths: Union['Label', List['Label']]=None, 
        groundtruths_text: Union[str, List[str]]=None) -> None:
        """
        Compute the performances of this Label.
        This function calls ``Label.task_evaluator``, and
        save all the keys and values returned to ``self.perform``.
        **!!** This can be computed with either just ``groundtruths`` or
        ``groundtruths_text``, but you cannot have neither!

        Parameters
        ----------
        groundtruths : Union[Label, List[Label]], optional
            The groundtruth Label objects, by default None
        groundtruths_text : Union[str, List[str]], optional
            The groundtruth string(s), by default None
        
        Returns
        -------
        None
        """
        if not groundtruths_text and groundtruths:
            if type(groundtruths) == list:
                groundtruths_text = [g.label for g in groundtruths]
            else:
                try:
                    groundtruths_text = groundtruths.get_label()
                except:
                    pass
        if groundtruths_text:
            metrics = Label.task_evaluator(self.label, groundtruths_text)
            self.set_perform(**metrics)

    def __repr__(self) -> str:
        """Override the print func by displaying the key."""
        return f"""[{self.__class__.__name__}] {[self.key()]}\n""" + \
            f"""{self.label} ({self.perform})"""

    @classmethod
    def set_task_evaluator(cls, 
        task_evaluation_func: Callable[[str, Union[str, List[str]]], Dict[str, float]],
        task_primary_metric: str) -> None:
        """
        Because different task has different evaluation metrics and methods, 
        This function sets the evaluation function and primary metric.
        
        Parameters
        ----------
        task_evaluation_func : Callable[[pred: str, labels: Union[str, List[str]]], Dict[str, float]]
            the evaluation function that accepts pred and groundtruths, and 
            return a dict of metrics: { metric_name: metric_score }.
            This is saved as ``Label.task_evaluation_func``.
        task_primary_metric : str
            The primary task metric name, ideally a key of ``task_evaluation_func`` 's return.
            This is saved as ``Label.task_primary_metric``.
            This is what DSL resolve to when we set ``perform_name="DEFAULT"``
        
        Returns
        -------
        None
        """
        
        Label.task_evaluation_func = task_evaluation_func
        Label.task_primary_metric = task_primary_metric

    @classmethod
    def task_evaluator(cls, 
        pred: str, labels: Union[str, List[str]]) -> Dict[str, float]:
        """The wrapper for computing the performances.
        
        Parameters
        ----------
        pred : str
            The predicted string.
        labels : Union[list, str]
            The groundtruth or a list of groundtruths.
        
        Returns
        -------
        Dict[str, float]
            A dict of metrics: { metric_name: metric_score }
        """
        try:
            if not Label.task_evaluation_func or len(Label.task_evaluation_func(pred, labels)) == 0:
                print('Define the task evaluation function!')
                return {}
            else:
                return Label.task_evaluation_func(pred, labels)
        except Exception:
            print('[task_evaluator]')
            traceback.print_exc()
            return {}
    
    @classmethod
    def resolve_default_perform_name(cls, perform_name: str=None) -> str:
        """Resolve the actual selected perform_name.
        If ``perform_name`` is given, return perform_name. Otherwise
        (``perform_name=None or perform_name="DEFAULT"``), 
        return ``Label.perform_name``. 
        
        Parameters
        ----------
        perform_name : str, optional
            The input named model, by default None
        
        Returns
        -------
        str
            The resolved model
        """
        if not perform_name or perform_name == 'DEFAULT':
            return Label.task_primary_metric
        else:
            return perform_name

class SpanLabel(Label):
    """
    When the label is from a predefined list of numbers or strs, not need to process.
    """
    def __init__(self, 
        model: str,
        qid: str, 
        text: str, vid: int=0, 
        metas: Dict[str, any]={},
        annotator: SpacyAnnotator=None) -> None:
        Label.__init__(self, model, qid, text, vid, metas=metas, annotator=annotator)
    
class PredefinedLabel(Label):
    """
    When the label is from a predefined list of numbers or strs, no need to process.
    """
    def __init__(self, 
        model: str,
        qid: str, 
        text: Union[str, int, float], vid: int=0, 
        metas: Dict[str, any]={},
        annotator: SpacyAnnotator=None) -> None:
        Label.__init__(self, model, qid, None, vid, metas=metas, annotator=annotator)
        self.label = str(text)
    
    def get_text(self):
        """Get the label string. This works exactly the same as ``self.get_label()``
        
        Returns
        -------
        str
            The string
        """
        label = getattr(self, 'label', None)
        if label:
            return label
        return ''