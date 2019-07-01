from typing import Dict
import traceback
import numpy as np
from .predictor_nli import PredictorNLI
from ..predictor_allennlp import PredictorAllennlp

from ..predictor import Predictor

@Predictor.register("nli_decompose_att")
class PredictorDecomposeAtt(PredictorNLI, PredictorAllennlp, Predictor):
    """
    The wrapper for DecomposableAttention model, as implemented in Allennlp:
    https://allenai.github.io/allennlp-docs/api/allennlp.predictors.html#decomposable-attention


    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("snli")
    """
    def __init__(self, name: str, 
        model_path: str=None,
        model_online_path: str=None,
        description: str='') -> None:
        PredictorAllennlp.__init__(self, 
            name=name,
            model_path=model_path,
            model_online_path=model_online_path,
            description=description)
        PredictorNLI.__init__(self, name, description, self.predictor)

    def predict(self, premise: str, hypothesis: str) -> Dict[str, float]:
        try:
            labels = ['entailment', 'contradiction', 'neutral']
            predicted = self._predict_json(
                premise=premise, 
                hypothesis=hypothesis)
            label_probs = predicted['label_probs']
            return {
                'confidence': max(label_probs),
                'text': labels[np.argmax(label_probs)],
            }
        except:
            raise