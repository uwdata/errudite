from typing import Dict
import traceback
from ...utils.evaluator import qa_score
from ...targets.label import Label

from .predictor_qa import PredictorQA
from ..predictor import Predictor
from ..predictor_allennlp import PredictorAllennlp

@Predictor.register("bidaf")
class PredictorBiDAF(PredictorQA, PredictorAllennlp, Predictor):
    """
    The wrapper for BidirectionalAttentionFlow model, as implemented in Allennlp:
    https://allenai.github.io/allennlp-docs/api/allennlp.predictors.html#bidaf

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("bidaf")
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
        PredictorQA.__init__(self, name, description, self.predictor)
        Label.set_task_evaluator(qa_score, 'f1')

    def predict(self, qtext: str, ptext: str) -> Dict[str, float]:
        try:
            predicted = self._predict_json(passage=ptext, question=qtext)
            span_start, span_end = predicted['best_span'][0], predicted['best_span'][1]
            return {
                'confidence': predicted['span_start_probs'][span_start] * predicted['span_end_probs'][span_end],
                'text': predicted['best_span_str'],
                'span_start': predicted['best_span'][0]
            }
        except Exception as e:
            print('[get_img]')
            traceback.print_exc()
            return None