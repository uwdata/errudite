from typing import List, Dict
import traceback
from ..qa.answer import Answer
from ...utils.helpers import convert_list
from ...processor.helpers import span_to_json
from ...utils.evaluator import vqa_accuracy
from ...targets.label import Label

class VQAAnswer(Answer):
    def __init__(self, 
        model: str, 
        qid: str, 
        text: str, 
        count: int,
        vid: int=0,
        answer_type: str=None, 
        metas: Dict[str, any]={},
        annotator=None) -> None:
        Answer.__init__(self, model, qid, text, vid, answer_type, metas, annotator)
        self.count = count
        Label.set_task_evaluator(vqa_accuracy, 'accuracy')
        # the parsing tree information
        # the following only matters for predicted results
        self.perform = {
            'accuracy': 0, 'confidence': 0
        }
        if not self.is_groundtruth or not answer_type:
            self.answer_type = self.rectify_answer_type()

    def rectify_answer_type(self):
        if not self.doc:
            return 'other'
        if self.doc.text.lower() in ['yes', 'no']:
            return 'yes/no'
        if any([i.pos_ == "NUM" or i.is_digit for i in self.doc]):
            return 'number'
        return 'other'
    
    def compute_performance(self, groundtruths: List['Answer']=None, groundtruths_text: List[str]=None) -> None:
        '''
        Evaluate exact match and f1 score based on text
        @param <List[str]> groundtruths_text: a string list for only the texts of the groundtruth
        '''
        try:
            if not groundtruths_text and groundtruths:
                groundtruths = convert_list(groundtruths)
                groundtruths_text = []
                for g in groundtruths:
                    groundtruths_text += [ g.doc.text ] * g.count
            if groundtruths_text:
                groundtruths_text = convert_list(groundtruths_text)
                self.perform['accuracy'] = vqa_accuracy(self.doc.text, groundtruths_text)['accuracy']
                return self.perform
        except ValueError:
            print('[_compute_performance]')
            traceback.print_exc()
            self.perform = { 'accuracy': 0, 'confidence': 0}
            return self.perform

    def add_attributes(self, predicted: 'PredictOutput', groundtruths: List['Answer'] = None) -> None:
        if groundtruths:
            self.compute_performance(groundtruths=groundtruths)
        if predicted:
            self.set_perform(confidence=predicted.confidence)
