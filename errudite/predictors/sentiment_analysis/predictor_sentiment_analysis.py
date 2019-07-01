from typing import List, Dict
from ..predictor import Predictor
from ...utils.evaluator import accuracy_score
from ...targets.label import Label, PredefinedLabel
import torch 

@Predictor.register("sentiment_task_class")
class PredictorSA(Predictor):
    """
    Predictor wrapper for sentiment analysis tasks.
    Perform metrics: ``['accuracy', 'confidence']``

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("sentiment_task_class")
    """
    def __init__(self, 
        name: str, 
        description: str, 
        model: any):
        perform_metrics = ['accuracy', 'confidence']
        Predictor.__init__(self, name, description, model, perform_metrics)
        Label.set_task_evaluator(accuracy_score, task_primary_metric='accuracy')

    def predict(self, premise: str, hypothesis: str) -> Dict[str, float]:
        return {
            'confidence': '',
            'text': '',
        }

    @classmethod
    def model_predict(cls, 
        predictor: 'Predictor', 
        query: 'Target', 
        groundtruth: 'Label') -> 'Label':
        """
        Define a class method that takes Target inputs, run model predictions, 
        and wrap the output prediction into Labels.
        
        Parameters
        ----------
        predictor : Predictor
            A predictor object, with the predict method implemented.
        query : Target
            A sentence, transferred to the target. 
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
        predicted = predictor.predict(query.get_text())
        if not predicted:
            return None
        idx = predictor.predictor._model.vocab.get_token_index(
            groundtruth.label, namespace="labels")
        label = torch.tensor([idx], dtype=torch.long) #pylint: disable=E1102, E1101
        tensor = torch.tensor([predicted["logits"]]) #pylint: disable=E1102
        loss = predictor.predictor._model.loss(tensor, label)
        answer = PredefinedLabel(
            model=predictor.name, 
            qid=query.qid,
            text=predicted['text'], 
            vid=max([query.vid, query.vid, groundtruth.vid] ), 
            metas={"loss": loss.item()})
        answer.compute_perform(groundtruths=groundtruth)
        answer.set_perform(confidence=predicted['confidence'])
        return answer