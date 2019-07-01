import sys
sys.path.append('..')
from typing import Dict
import traceback

import drqa.reader as DrQAReader
from ..predictor import Predictor
from .predictor_qa import PredictorQA

@Predictor.register("drqa")
class PredictorDrQA(PredictorQA):
    """
    The wrapper for DrQA.
    !! Important! To run this script, setup DrQA:
    https://github.com/facebookresearch/DrQA
    cd errudite/predictors/qa
    git clone https://github.com/facebookresearch/DrQA.git .
    pip install -r ./drqa/requirements.txt
    cd ./drqa/
    python setup.py develop

    This can be queried via:
    
    .. code-block:: python

        from errudite.predictors import Predictor
        Predictor.by_name("drqa")
    """
    def __init__(self, name: str, model_path: str, description: str='') -> None:
        model = DrQAReader.Predictor(model=model_path, tokenizer='spacy', num_workers=0)
        PredictorQA.__init__(self, name, description, model)
        
    def predict(self, qtext: str, ptext: str) -> Dict[str, float]:
        try:
            predicted = self.predictor.predict(ptext, qtext)
            if predicted:
                return {
                    'confidence': float(predicted[0]['confidence']),
                    'text': str(predicted[0]['text']),
                    'span_start': int(predicted[0]['span_start'])
                }
        except Exception as e:
            print('[get_img]')
            traceback.print_exc()
            return None