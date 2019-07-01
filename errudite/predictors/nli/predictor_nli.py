from typing import List, Dict
from ..predictor import Predictor
from ...utils.evaluator import accuracy_score
from ...targets.label import Label, PredefinedLabel

@Predictor.register("nli_task_class")
class PredictorNLI(Predictor):
    """
    Predictor wrapper for natural language inference tasks.
    perform metrics: ``['accuracy', 'confidence']``

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("nli_task_class")
    """
    def __init__(self, 
        name: str, 
        description: str, 
        model: any):
        perform_metrics = ['accuracy', 'confidence']
        Predictor.__init__(self, name, description, model, perform_metrics)
        Label.set_task_evaluator(accuracy_score, task_primary_metric='accuracy')

    def predict(self, premise: str, hypothesis: str) -> Dict[str, float]:
        """
        run the prediction.

        Raises
        ------
        NotImplementedError
           Should be implemented in subclasses.
        """
        raise NotImplementedError

    @classmethod
    def model_predict(cls, 
        predictor: 'PredictorNLI', 
        premise: 'Target', 
        hypothesis: 'Target', 
        groundtruth: 'Label') -> 'Label':
        """
        Define a class method that takes Target inputs, run model predictions, 
        and wrap the output prediction into Labels.
        
        Parameters
        ----------
        predictor : Predictor
            A predictor object, with the predict method implemented.
        premise : Target
            The premise target. 
        hypothesis : Target
            The hypothesis target. 
        groundtruth : Label
            A groundtruth, typed Label.
        
        Returns
        -------
        Label
            The predicted output, with performance saved.
        """
        answer = None
        if not predictor:
            return answer
        predicted = predictor.predict(premise.get_text(), hypothesis.get_text())
        if not predicted:
            return None
        answer = PredefinedLabel(
            model=predictor.name, 
            qid=premise.qid,
            text=predicted['text'], 
            vid=max([premise.vid, hypothesis.vid, groundtruth.vid] ))
        answer.compute_perform(groundtruths=groundtruth)
        answer.set_perform(confidence=predicted['confidence'])
        return answer