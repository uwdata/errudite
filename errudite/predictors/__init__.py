from .predictor import Predictor
from .qa.predictor_qa import PredictorQA
from .nli.predictor_nli import PredictorNLI
from .sentiment_analysis.predictor_sentiment_analysis import PredictorSA


try:
    from .qa.predictor_bidaf import PredictorBiDAF
except:
    pass
try:
    from .qa.predictor_mrqa_bert import PredictorBertMRQA
except:
    pass

try:
    from .nli.predictor_decompose_att import PredictorDecomposeAtt
except:
    pass

#from .vqa.predictor_vqa import PredictorVQA

try:
    from .sentiment_analysis.predictor_bcn import PredictorBCN
except:
    pass
