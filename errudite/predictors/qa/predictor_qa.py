from typing import List, Dict
from ..predictor import Predictor
from ...utils.evaluator import qa_score
from ...targets.label import Label
from ...targets.qa.answer import QAAnswer

@Predictor.register("qa_task_class")
class PredictorQA(Predictor):
    """
    Predictor wrapper for question answering/machine comprehension tasks.
    Perform metrics: ``['f1', 'em', 'sent', 'precision', 'recall', 'confidence']``

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("qa_task_class")
    """
    def __init__(self, 
        name: str, 
        description: str, 
        model: any):
        perform_metrics = ['f1', 'em', 'sent', 'precision', 'recall', 'confidence']
        Predictor.__init__(self, name, description, model, perform_metrics)
        Label.set_task_evaluator(qa_score, 'f1')

    def predict(self, qtext: str, ptext: str) -> Dict[str, float]:
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
        predictor: 'Predictor', 
        question: 'Question', 
        context: 'Context', 
        groundtruths: List['QAAnswer']) -> 'QAAnswer':
        """
        Define a class method that takes Target inputs, run model predictions, 
        and wrap the output prediction into Labels.
        
        Parameters
        ----------
        predictor : Predictor
            A predictor object, with the predict method implemented.
        question : Question
            Question target. 
        context : Context
            Context target. 
        groundtruths : List[QAAnswer]
            A list of groundtruths, typed QAAnswer.
        
        Returns
        -------
        QAAnswer
            The predicted output, with performance saved.
        """
        answer = None
        if not predictor:
            return answer
        predicted = predictor.predict(question.get_text(), context.get_text())
        if not predicted:
            return None
        answer = QAAnswer(
            model=predictor.name, 
            qid=question.qid,
            text=predicted['text'], 
            vid=max([question.vid, context.vid] + [g.vid for g in groundtruths]), 
            annotator=None)
        if context:
            answer.set_source_info(
                context, 
                char_start=None, 
                span_start=predicted['span_start'])
        if groundtruths:
            answer.compute_perform(groundtruths=groundtruths)
        if predicted:
            answer.set_perform(confidence=predicted['confidence'])
        return answer