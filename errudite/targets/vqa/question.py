from typing import List, Dict, Union
from ..qa.question import Question

class VQAQuestion(Question):
    def __init__(self, 
        qid: Union[str, int], 
        text: str, 
        img_id: Union[str, int], 
        vid: int=0, question_type: str=None) -> None:
        qid, img_id = str(qid), str(img_id)
        
        Question.__init__(self, qid, text, vid, question_type)
        self.img_id = img_id