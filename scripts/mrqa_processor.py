import glob, os
import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append(os.path.abspath(os.path.expanduser('~/Desktop/sourcetree/errudite/')))


import pandas as pd
from tqdm import tqdm
import errudite
from errudite.io import DatasetReader
from errudite.predictors import Predictor
from errudite.targets.instance import Instance
from errudite.targets.label import Label
from errudite.utils import accuracy_score, normalize_file_path

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

if __name__ == "__main__":

    DATASET_FOLDER = normalize_file_path("~/datasets/raw_data/mrqa/out_of_domain_devs")
    sample_size = None
    sample_name = sample_size if sample_size else "dev"
    file_path = ",".join(glob.glob(os.path.join(DATASET_FOLDER, "*.jsonl.gz")))
    reader = DatasetReader.by_name("mrqa")(
        cache_folder_path=f"~/datasets/caches/dataset_debug/mrqa-{sample_name}")
    instances = reader.read(file_path, sample_size=sample_size)

    MODEL_FOLDER = normalize_file_path("~/datasets/models/mrqa/")
    predictor = Predictor.by_name("mrqa")(
        name="mrqa_path", 
        model_path=os.path.join(MODEL_FOLDER, "mrqa_bert_base.gz"))
    
    predictors = { p.name: p for p in [predictor] }
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

    TRAIN_DATASET_FOLDER = normalize_file_path("~/datasets/raw_data/mrqa/trains")
    file_path = ",".join(glob.glob(os.path.join(TRAIN_DATASET_FOLDER, "*.jsonl.gz")))
    reader.count_vocab_freq(file_path)
    reader.compute_ling_perform_dict(list(Instance.instance_hash.values()))
    reader.dump_preprocessed()

