from typing import Dict, List
import logging
import pandas as pd
from tqdm import tqdm

from overrides import overrides
from nltk.tree import Tree

from .dataset_reader import DatasetReader
from ..utils import ConfigurationError, normalize_file_path
from ..targets.instance import Instance
from ..targets.target import Target
from ..targets.label import Label, PredefinedLabel
from ..utils import normalize_file_path, load_json, qa_score, accuracy_score


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

@DatasetReader.register("snli")
class SNLIReader(DatasetReader):
    """
    This loads the data from The Stanford Natural Language Inference (SNLI) Corpus:
    https://nlp.stanford.edu/projects/snli/

    * default evaluation metric: accuracy
    * target entries in an instance: hypothesis, premise, predictions, groundtruth.

    This can be queried via:
    
    .. code-block:: python

        from errudite.io import DatasetReader
        DatasetReader.by_name("snli")
    """
    def __init__(self, cache_folder_path: str=None) -> None:
        super().__init__(cache_folder_path)
        Label.set_task_evaluator(accuracy_score, 'accuracy')
    
    @overrides
    def _read(self, file_path: str, lazy: bool, sample_size: int):
        instances = []
        premises, hypotheses = [], []
        logger.info("Reading instances from lines in file at: %s", file_path)
        df = pd.read_csv(normalize_file_path(file_path), sep='\t')
        for idx, row in tqdm(df.iterrows()):
            if lazy:
                premises.append(row['sentence1'])
                hypotheses.append(row['sentence2'])
            else:
                instance = self._text_to_instance(f'q:{idx}', row)
                if instance is not None:
                    instances.append(instance)
                if sample_size and idx > sample_size:
                    break
        if lazy:
            return { "premise": premises, "hypoethsis": hypotheses }
        else:
            return instances

    
    @overrides
    def _text_to_instance(self, id: str, row) -> Instance:  # type: ignore
        premise = Target(qid=row['pairID'], text=row['sentence1'], vid=0, metas={'type': 'premise'})
        hypothesis = Target(qid=row['pairID'], text=row['sentence2'], vid=0, metas={'type': 'hypothesis'})
        # label
        raw_labels = [row[f'label{i}']  for i in range(1,6)]
        groundtruth = PredefinedLabel(
            model='groundtruth', 
            qid=row['pairID'], 
            text=row['gold_label'], 
            vid=0, 
            metas={'raw_labels': raw_labels}
        )
        return self.create_instance(row['pairID'], 
            hypothesis=hypothesis, 
            premise=premise, 
            groundtruth=groundtruth)