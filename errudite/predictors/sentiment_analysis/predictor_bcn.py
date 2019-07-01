from typing import Dict
import traceback
import numpy as np
from allennlp.models.archival import load_archive
from .predictor_sentiment_analysis import PredictorSA
from ..predictor_allennlp import PredictorAllennlp

from ..predictor import Predictor

@Predictor.register("bcn")
class PredictorBCN(PredictorSA, PredictorAllennlp):
    """
    The wrapper for a sentiment analysis model, as implemented in Allennlp:
    https://allenai.github.io/allennlp-docs/api/allennlp.predictors.html#text-classifier

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("bcn")
    """
    def __init__(self, name: str, 
        model_path: str=None,
        model_online_path: str=None,
        description: str='') -> None:
        PredictorAllennlp.__init__(self, 
            name,
            model_path,
            model_online_path,
            description,
            "text_classifier")
        PredictorSA.__init__(self, name, description, self.predictor)

    def predict(self, query: str) -> Dict[str, float]:
        try:
            predicted = self._predict_json(sentence=query.split())
            return {
                'logits': predicted['logits'],
                'confidence': max(predicted['class_probabilities']),
                'text': predicted["label"],
            }
        except Exception as e:
            print(f'[predict] {self.__class__.__name__}')
            traceback.print_exc()
            return None