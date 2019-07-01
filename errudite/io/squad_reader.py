from typing import Dict, List
import pandas as pd
from tqdm import tqdm
from overrides import overrides

from .dataset_reader import DatasetReader
from ..processor.helpers import normalize_text
from ..targets.instance import Instance

from ..targets.qa import Question, Context, QAAnswer
from ..targets.label import Label
from ..utils import normalize_file_path, load_json, qa_score


@DatasetReader.register("squad")
class SQUADReader(DatasetReader):
    """
    This loads the data from squad v1.1, for the Machine Comprehension
    task: https://rajpurkar.github.io/SQuAD-explorer/.
    
    * default evaluation metric: f1
    * target entries in an instance: question, context, predictions, groundtruths.

    This can be queried via:
    
    .. code-block:: python

        from errudite.io import DatasetReader
        DatasetReader.by_name("squad")
    """
    def __init__(self, cache_folder_path: str=None) -> None:
        super().__init__(cache_folder_path)
        Label.set_task_evaluator(qa_score, 'f1')
    
    @overrides
    def _read(self, file_path: str, lazy: bool, sample_size: int):
        json_data = load_json(normalize_file_path(file_path))
        aRaws = json_data['data']
        questions, answers = [], []
        # each article
        instances = []
        count, stop = 0, False
        for aid, a_raw in tqdm(enumerate(aRaws)):
            # each context
            for cid, p_raw in enumerate(a_raw['paragraphs']):
                if not p_raw['context']:
                    continue
                if lazy:
                    context = p_raw['context']
                else:
                    context = Context(aid=aid, cid=cid, text=p_raw['context'], vid=0, qid=None)
                # for each question
                for q_raw in p_raw['qas']:
                    if lazy:
                        questions.append(q_raw['question'])
                        answers += [a['text'] for a in q_raw['answers']]
                    else:
                        instance = self._text_to_instance(q_raw['id'], q_raw, context)
                        if instance is not None:
                            count += 1
                            instances.append(instance)
                            #yield instance
                        if sample_size and count > sample_size:
                            stop = True
                            break
                if stop: 
                    break
            if stop: 
                break
        if lazy:
            return { "question": questions, "answer": answers }
        else:
            return instances

    
    @overrides
    def _text_to_instance(self, qid: str, q_raw, context: Context) -> Instance:  # type: ignore
        if not q_raw['answers']:
            return None
        question = Question(qid=qid, text=q_raw['question'], vid=0)
        # load the groundtruth
        answers = self._load_groundtruths(ans_raw=q_raw['answers'], context=context, question=question)
        return self.create_instance(
            qid=qid,
            additional_keys={"aid":context.aid, "cid":context.cid},
            question=question,
            context=context,
            groundtruths=answers
        )

    def _load_groundtruths(self, 
        ans_raw: List, context: Context, question: Question) -> List[QAAnswer]:
        """load the groundtruths.
        
        Arguments:
            ans_raw {List} -- {text: str, answer_start: int}[] the raw answer in dev set
            context {Paragraph} -- the source context of the answer
            question {Question} -- the question we are trying to answer
        
        Returns:
            List[Answer] -- A list of groundtruth answers
        """

        answer_hash = []
        answers = []
        for an_raw in ans_raw:
            # include not only the text, but also the position
            an_norm = '{0}-{1}'.format(normalize_text(an_raw['text']), an_raw['answer_start'])
            if an_norm in answer_hash:
                continue
            answer_hash.append(an_norm)
            answer = QAAnswer(
                model='groundtruth', 
                qid=question.qid,
                text=an_raw['text'], vid=0)
            answer.add_attributes(context=context, \
                predicted=None, groundtruths=None, char_start=an_raw['answer_start'], \
                span_start=None)
            answers.append(answer)
        return answers
