from typing import Dict, List
import pandas as pd
from tqdm import tqdm
import json
import gzip

from ..io import DatasetReader
from ..processor.helpers import normalize_text
from ..targets.instance import Instance

from ..targets.qa import Question, Context, QAAnswer
from ..targets.label import Label
from ..utils import normalize_file_path, qa_score

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@DatasetReader.register("mrqa")
class MRQAReader(DatasetReader):
    """
    This loads the data from MRQA, for the Machine Comprehension
    task: https://mrqa.github.io
    
    * default evaluation metric: f1
    * target entries in an instance: question, context, predictions, groundtruths.

    This can be queried via:
    
    .. code-block:: python

        from errudite.io import DatasetReader
        DatasetReader.by_name("mrqa")
    """
    def __init__(self, cache_folder_path: str=None) -> None:
        super().__init__(cache_folder_path)
        Label.set_task_evaluator(qa_score, 'f1')
    
    def _read(self, file_path: str, lazy: bool, sample_size: int):
        datasets = []
        file_paths = file_path.split(',')
        per_set_sample_size = round(sample_size / len(file_paths)) if sample_size else None
        for ind, single_file_path in enumerate(file_paths):
            zip_handle = gzip.open(normalize_file_path(single_file_path), 'rb')
            datasets.append({'single_file_path':single_file_path, \
                'file_handle': zip_handle, \
                'num_of_questions':0, 'inst_remainder':[], \
                'dataset_weight':1 })
            datasets[ind]['header'] = json.loads(datasets[ind]['file_handle'].readline())['header']
            is_in_domain = "in_domain" in single_file_path
            datasets[ind]['header']["domain"] = "in" if is_in_domain else "out"
        instances = []
        questions, answers = [], []        
        is_done = [False for _ in datasets]
        while not all(is_done):
            for ind, dataset in enumerate(datasets):
                dataset_header = dataset["header"]
                logger.info(f"Reading from dataset: {dataset_header['dataset']} ({dataset_header['domain']}).")
                if is_done[ind]:
                    continue
                for cidx, example in tqdm(enumerate(dataset['file_handle'])):
                    p_raw = json.loads(example)
                    if p_raw["context"].startswith("[[Hrothgar]]"):
                        print(p_raw)
                    cid = f'{dataset_header["dataset"]}_{cidx}'
                    if not p_raw['context']:
                        continue
                    if lazy:
                        context = p_raw['context']
                    else:
                        context = Context(
                            aid="0", cid=cid, text=p_raw['context'], vid=0, qid=None, 
                            metas={"dataset": dataset_header["dataset"], "domain": dataset_header['domain']})
                    # for each question
                    for q_raw in p_raw['qas']:
                        if lazy:
                            questions.append(q_raw['question'])
                            answers += q_raw['answers']
                        else:
                            instance = self._text_to_instance(dataset_header, q_raw['qid'], q_raw, context)
                            if instance is not None:
                                dataset['num_of_questions'] += 1
                                instances.append(instance)
                                #yield instance
                            if per_set_sample_size and dataset['num_of_questions'] >= per_set_sample_size:
                                is_done[ind] = True
                                break
                    if is_done[ind]:
                        break
                else:
                    # No more lines to be read from file
                    is_done[ind] = True
        for dataset in datasets:
            #logger.info("Total number of processed questions for %s is %d",dataset['header']['dataset'], dataset['num_of_questions'])
            dataset['file_handle'].close()
        if lazy:
            return { "question": questions, "answer": answers}
        else:
            return instances
    
    def _text_to_instance(self, dataset_header: dict, qid: str, q_raw, context: Context) -> Instance:  # type: ignore
        if not q_raw['detected_answers']:
            return None
        question = Question(
            qid=qid, text=q_raw['question'], vid=0, 
            metas={"dataset": dataset_header["dataset"], "domain": dataset_header['domain']})
        # load the groundtruth
        answers = self._load_groundtruths(
            ans_raw=q_raw['detected_answers'], 
            context=context, 
            question=question)
        additional_keys = {"aid":context.aid, "cid":context.cid}
        additional_keys.update(dataset_header)
        return self.create_instance(
            qid=qid,
            additional_keys=additional_keys,
            question=question,
            context=context,
            groundtruths=answers,
        )

    def _load_groundtruths(self, 
        ans_raw: List, context: Context, question: Question) -> List[QAAnswer]:
        """load the groundtruths.
        
        Arguments:
            ans_raw {List} -- {text: str, char_spans: int[]}[] the raw answer in dev set
            context {Paragraph} -- the source context of the answer
            question {Question} -- the question we are trying to answer
        
        Returns:
            List[Answer] -- A list of groundtruth answers
        """

        answer_hash = []
        answers = []
        for an_raw in ans_raw:
            # include not only the text, but also the position
            for idxes in an_raw['char_spans']:
                answer_start = idxes[0]
                an_norm = '{0}-{1}'.format(normalize_text(an_raw['text']), answer_start)
                if an_norm in answer_hash:
                    continue
                answer_hash.append(an_norm)
                answer = QAAnswer(
                    model='groundtruth', 
                    qid=question.qid,
                    text=an_raw['text'], vid=0, metas=question.metas)
                answer.add_attributes(context=context, \
                    predicted=None, groundtruths=None, char_start=answer_start, \
                    span_start=None)
                answers.append(answer)
        return answers