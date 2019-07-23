from typing import Dict
import traceback
import numpy as np

from ...utils.evaluator import qa_score
from ...targets.label import Label
from ...processor import SpacyAnnotator
from .mrqa_allennlp import *

from .predictor_qa import PredictorQA
from ..predictor import Predictor
from ..predictor_allennlp import PredictorAllennlp


@Predictor.register("mrqa")
class PredictorBertMRQA(PredictorQA, PredictorAllennlp, Predictor):
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
        self.spacy_annotator = SpacyAnnotator(disable=['parser', 'ner', 'textcat'])
        self.spacy_annotator.model.max_length = 100000000
        PredictorAllennlp.__init__(self, 
            name=name,
            model_path=model_path,
            model_online_path=model_online_path,
            description=description,
            model_type="mrqa_predictor")
        PredictorQA.__init__(self, name, description, self.predictor)
        Label.set_task_evaluator(qa_score, 'f1')

    def predict(self, qtext: str, ptext: str) -> Dict[str, float]:
        try:
            json_obj = {
                "context": ptext,
                "context_tokens": [ [t.text,t.idx] for t in self.spacy_annotator.process_text(ptext) if t.text != "\n" ],
                "qas": [{
                    "qid": "tmp",
                    "answers": [],
                    "detected_answers": [
                        { "text": "tmp", "char_spans": [[0, 3]], "token_spans": [[0, 1]]}
                    ],
                    "question": qtext,
                    "question_tokens": [ [t.text,t.idx] for t in self.spacy_annotator.process_text(qtext) if t.text != "\n" ],
                }],
            }
            predicted = self.predictor.predict_json(json_obj)
            if predicted:
                predicted = predicted["tmp"]
                #span_start, span_end = predicted['best_span'][0], predicted['best_span'][1]
                return {
                    'confidence': predicted["best_span_logit"], #np.log2(predicted["best_span_logit"]),
                    'text': predicted["best_span_str"], #predicted['best_span_str'],
                    # 5 chars for [SEP], 1 + 1 chars for spaces
                    'char_start': predicted['char_offsets'][0]#- len(qtext) - 7
                }
            else:
                return None
        except Exception as e:
            logger.error(e)
            return None