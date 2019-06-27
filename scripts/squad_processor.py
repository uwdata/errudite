import os
import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append(os.path.abspath(os.path.expanduser('~/Desktop/sourcetree/errudite/')))
from tqdm import tqdm
import pandas as pd

import errudite
from errudite.io import DatasetReader
from errudite.predictors import Predictor
from errudite.targets.instance import Instance
from errudite.targets.label import Label
from errudite.utils import accuracy_score, normalize_file_path

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

if __name__ == "__main__":
    sample_size = 10570
    DATASET_FOLDER = normalize_file_path("~/datasets/raw_data/squad/")
    MODEL_FOLDER = normalize_file_path("~/datasets/models/bidaf/")
    reader = DatasetReader.by_name("squad")(cache_folder_path=f"~/datasets/caches/error_analysis/squad-{sample_size}")

    instances = reader.read(
        os.path.join(DATASET_FOLDER, "dev-v1.1.json"),
        sample_size=sample_size)
    reader.dump(instances)
    Label.set_task_evaluator(accuracy_score, task_primary_metric='accuracy')

    bidaf = Predictor.by_name("bidaf")(
        name='bidaf', 
        description='Pretrained model from Allennlp, for the BiDAF model (QA)',
        model_online_path="https://s3-us-west-2.amazonaws.com/allennlp/models/bidaf-model-2017.09.15-charpad.tar.gz")
    """
    bidaf_elmo = Predictor.by_name("bidaf")(
        name='bidaf_elmo', 
        description='Pretrained model from Allennlp, for the BiDAF model (QA), with the elmo embedding.',
        model_path=os.path.join(MODEL_FOLDER, "elmo", "model.tar.gz"))
    """
    predictors = { p.name: p for p in [bidaf] }
    predictions = { p: [] for p in predictors }
    logger.info("Running predictions....")
    for instance in tqdm(instances):
        instance_predictions = []
        for predictor in predictors.values():
            prediction = Predictor.by_name("qa_task_class").model_predict(
                predictor, 
                instance.question, 
                instance.context, 
                instance.groundtruths)
            instance_predictions.append(prediction)
            predictions[predictor.name].append(prediction)
        instance.set_entries(predictions=instance_predictions)
    for predictor in predictors.values():
        predictor.evaluate_performance(instances)
    print(pd.DataFrame([ {"predictor": p.name, "f1": p.perform["f1"] } for p in predictors.values() ]))
    Instance.build_instance_hashes(instances)
    reader.count_vocab_freq(os.path.join(DATASET_FOLDER, "train-v1.1.json"))
    reader.compute_ling_perform_dict(list(Instance.instance_hash.values()))
    reader.dump_preprocessed()