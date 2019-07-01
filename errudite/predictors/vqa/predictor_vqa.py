from typing import List, Dict
from ..predictor import Predictor
from ...targets.vqa.answer import VQAAnswer

@Predictor.register("vqa_task_class")
class PredictorVQA(Predictor):
    """
    Predictor wrapper for visual question answering tasks.
    Perform metrics: ``['accuracy', 'confidence']``
    """
    def __init__(self, name: str, description: str, model: any):
        perform_metrics = ['accuracy', 'confidence']
        Predictor.__init__(self, name, description, model, perform_metrics)

    def predict(self, qtext: str, img_id: str) -> Dict[str, float]:
        return None

    @classmethod
    def model_predict(cls, 
        predictor: 'PredictorVQA',
        question: 'Question', 
        groundtruths: List['VQAAnswer']) -> 'VQAAnswer':
        """
        Define a class method that takes Target inputs, run model predictions, 
        and wrap the output prediction into Labels.
        
        Parameters
        ----------
        predictor : Predictor
            A predictor object, with the predict method implemented.
        query : Target
            A sentence, transferred to the target. 
        groundtruth : List[VQAAnswer]
            A list of groundtruths, typed VQAAnswer.
        
        Returns
        -------
        VQAAnswer
            The predicted output, with performance saved.
        """
        answer = None
        if not predictor:
            return answer
        predicted = predictor.predict(question.doc.text, question.img_id)
        if not predicted:
            return None
        answer = VQAAnswer(
            model=predictor.name, 
            qid=question.qid,
            count=1,
            text=predicted.text, 
            vid=max([question.vid] + [g.vid for g in groundtruths]))
        
        answer.add_attributes(
            predicted=predicted, 
            groundtruths=groundtruths)
        answer.compute_performance(groundtruths=groundtruths)
        return answer