import re
import traceback
from typing import List, Dict
from ..label import SpanLabel, Label
from .context import Context
from ...task_helpers.qa.qc_ner import classify_answer
from ...utils.evaluator import qa_score

class Answer(SpanLabel):
    def __init__(self, 
        model: str,
        qid: str, 
        text: str, 
        vid: int=0,
        answer_type: str=None,
        metas: Dict[str, any]={},
        annotator=None) -> None:
        """Initial an answer instance
        
        Arguments:
            model {str} -- the model that generate the result
            qid {str} -- question id
            text {str} -- the question context
        
        Keyword Arguments:
            is_groundtruth {bool} if the answer is a groundtruth answer
            vid {int} -- the version id. This is to handle edits. (default: {0})
        """
        SpanLabel.__init__(self, model=model, qid=qid, text=text, vid=vid, metas=metas, annotator=annotator)
        self.sid = -1 # sentence id
        Label.set_task_evaluator(qa_score, 'f1')
        # the following only matters for predicted results.
        self.answer_type = answer_type if answer_type else self.get_answer_type()
    
    def get_answer_type(self):
        """Classify the answer type based on TREC classifier
        
        Returns:
            str -- [description]
        """

        return classify_answer(self.doc, use_question=False)

class QAAnswer(Answer):
    def __init__(self,
        model: str, 
        qid: str, 
        text: str, 
        vid: int=0,
        answer_type: str=None, 
        metas: Dict[str, any]={},
        annotator=None) -> None:
        Answer.__init__(self, model, qid, text, vid, answer_type, metas=metas, annotator=annotator)
        self.span_start = -1 # token level
        self.span_end = -1 # no need to plus one
        # the parsing tree information
        # the following only matters for predicted results
        self.perform = {
            'em': 0, 
            'f1': 0, 
            'precision': 0, 
            'recall': 0, 'confidence': 0, 'sent': 0
        }
    
    def generate_id(self) -> str:
        return 'qid:{0}-vid:{1}-model:{2}-start:{3}-end:{4}'.format(
            self.qid, self.vid, self.model, self.span_start, self.span_end)
    
    def char_to_span_offset(self, context: Context, char_start) -> int:
        """change char offset to span offset.
        
        Arguments:
            context {Context} -- the source context
            char_start {[type]} -- the char level offset
        
        Returns:
            int -- the span level offset
        """
        span_offset = 0
        for token in context.doc:
            if token.idx == char_start:
                return token.i
            elif token.idx < char_start:
                span_offset += 1
        return span_offset

    def set_source_info(self, context: Context, char_start: int=None, span_start: int=None) -> None:
        """Set the source info, 
        including article, context, sentence id, and the offset info.
        
        Arguments:
            context {context} -- [description]
        
        Keyword Arguments:
            char_start {int} -- the char level offset (default: {None})
            span_start {int} -- the span level offset (default: {None})
        
        Returns:
            None -- [description]
        """

        # if nothing is given, try to get the span_start based on index
        if char_start is None and span_start is None:
            if self.doc.text in context.doc.text:
                char_start = context.doc.text.index(self.doc.text)
            else:
                answer_str = re.sub('[^A-Za-z0-9 ]', '', self.doc.text)
                context_str = re.sub('[^A-Za-z0-9 ]', '', context.doc.text)
                if answer_str in context_str:
                    char_start = context_str.index(answer_str)
                else:
                    char_start = 0
        # if only char_start is given, convert to span_start
        if char_start is not None and char_start != -1:
            span_start = self.char_to_span_offset(context, char_start)
        # TODO: multiple sentence answers
        self.sid = 0
        for sid, sentence in enumerate(context.doc.sents):
            if span_start >= sentence.start and span_start < sentence.end:
                self.sid = sid
                break
        # global level offset.
        self.span_start = span_start #- sentence.start
        self.span_end = self.span_start + len(self.doc)

    def compute_perform(self, groundtruths: List['Answer']=None, groundtruths_text: List[str]=None) -> None:
        '''
        Evaluate exact match and f1 score based on text
        @param <List[str]> groundtruths_text: a string list for only the texts of the groundtruth
        '''
        try:
            if groundtruths:
                self.perform['sent'] = 1 if any([g.sid == self.sid for g in groundtruths]) else 0
            if not groundtruths_text and groundtruths:
                groundtruths_text = [g.doc.text for g in groundtruths]
            if groundtruths_text:
                perform = qa_score(self.doc.text, groundtruths_text)
                for key, val in perform.items():
                    self.perform[key] = val
            return self.perform
        except ValueError:
            print('[compute_perform]')
            traceback.print_exc()
            self.perform = {'em': 0, 'f1': 0, 'precision': 0, 'recall': 0, 'confidence': 0}
            return self.perform

    def is_incorrect_sentence(self):
        return self.perform['sent'] < 1

    def add_attributes(self, context: 'Context', \
        predicted: Dict[str, any], 
        groundtruths: List['Answer'] = None, char_start = None, \
        span_start = None) -> None:
        '''
        wrapper function for adding dimensions to the answer
        @param answer <Answer> targeting answer
        @param question <Question> targeting question
        @param question <Question> targeting paragraph
        @param paragraph: Paragraph, the source paragraph
        @param char_start: the char level offset
        @param span_start: the span level offset
        '''
        if context:
            self.set_source_info(context, char_start=char_start, span_start=span_start)
        if groundtruths:
            self.compute_perform(groundtruths=groundtruths)
        if predicted:
            self.set_perform(confidence=predicted.confidence)