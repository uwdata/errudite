import random
import argparse
import os
from tqdm import tqdm
import traceback
from typing import List, Dict
from .evaluator import normalize_answer
from ...utils.io import load_json, dump_caches, load_caches
from ...targets.target import Target
from ...targets.label import Label
from ...targets.qa.question import Question
from ...targets.qa.context import Context
from ...targets.qa.answer import QAAnswer

def load_groundtruths(
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
        an_norm = '{0}-{1}'.format(normalize_answer(an_raw['text']), an_raw['answer_start'])
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

def load_from_file(
    filepath: str, 
    sample_size: int, 
    sampled_qids: List=None) -> Dict[str, List]:
    """Load the article from the raw json file.
    
    Returns:
        Dict[str, List] -- {[qid]: {article: Article, context: Paragraph, question: Question, groundtruths: Answers}}
    """

    json_data = load_json(filepath)
    aRaws = json_data['data']
    output = []
    # each article
    for aid, a_raw in tqdm(enumerate(aRaws)):
        # each context
        for cid, p_raw in enumerate(a_raw['paragraphs']):
            context = None
            if not p_raw['context']:
                continue
            # for each question
            for q_raw in p_raw['qas']:
                qid = q_raw['id']
                if not q_raw['answers'] or (sampled_qids and qid not in sampled_qids):
                    continue
                if not context:
                    context = Context(aid=aid, cid=cid, text=p_raw['context'], vid=0, qid=None)
                question = Question(qid=qid, text=q_raw['question'], vid=0)
                # load the groundtruth
                answers = load_groundtruths(ans_raw=q_raw['answers'], context=context, question=question)
                output.append({
                    'key': {'qid': question.qid, 'vid': 0, 'cid': context.cid, 'aid': context.aid},
                    'context': context,
                    'question': question,
                    'groundtruths': answers,
                })
            if sample_size <= 100:
                break
        #break
    # run the prediction
    if len(output) > sample_size:
        output = random.sample(output, sample_size)
    return output
'''
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='en', type=str, help='the language model for spacy annotator.')
    parser.add_argument('--input_file_path', type=str, help='the path of the data file.')
    parser.add_argument('--output_file_folder', type=str, help='the path of the saved caches.')
    parser.add_argument('--sample_size', default=100, type=int, help='Sampling size.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    DB_NAME = f'instance-squad-{args.sample_size}/'
    # create the general file
    cache_path = os.path.join(args.output_file_folder, DB_NAME)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    # create the evaluation file
    eval_folder = os.path.join(cache_path, 'evaluations/')
    if not os.path.exists(eval_folder):
        os.makedirs(eval_folder)
    # create the analysis file
    analysis_folder = os.path.join(cache_path, 'analysis/')
    if not os.path.exists(analysis_folder):
        os.makedirs(analysis_folder)
    
    # get the instances
    if os.path.isfile(cache_path + 'instances.pkl'):
        hashes = load_instance_caches(annotator, DB_NAME, None)
        instances = Instance.form_instances(hashes['keys'], instance_type='qa')
        """
        for f in os.listdir(eval_folder):
            if f.endswith('.pkl'):
                os.remove(eval_folder + f)
        """
        for i in instances:
            i.set_entries(hashes['q_hash'], hashes['c_hash'], hashes['g_hash'], hashes['p_hash'])
        instances = [{
            'question': i.get_entry('question'),
            'groundtruths': i.get_entry('groundtruths'),
            'context': i.get_entry('context'),
            'key': {'qid': i.qid, 'vid': 0, 'cid': i.cid, 'aid': i.aid}
        } for i in instances ]
    else:
        instances = load_from_file(annotator, args.file_path, args.sample_size)
    # get the models
    predictors = load_predictors(PREDICTOR_METADATAS_QA, ARTIFICIAL_MODELS)
    # get the predictions
    predictions = load_predictions(eval_folder, instances, predictors)
    dump_instance_caches(instances, predictions, predictors, cache_path, eval_folder)
'''