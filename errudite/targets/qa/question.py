from ..target import Target
from ...processor.ling_consts import WHs

class Question(Target):
    """initialize a question instance.
        
        Arguments:
            qid {str} -- question id
            text {str} -- the question context
        
        Keyword Arguments:
            vid {int} -- version id (default: {0})
            question_type {str} -- "are", "is this", "what". 
                VQA naturally has this. QA is self-computed
        
        Returns:
            None -- [description]
        """
    
    def __init__(self, qid: str, text: str, vid: int=0, annotator=None, question_type: str=None) -> None:
        Target.__init__(self, qid, text, vid, annotator)
        self.question_type = question_type if question_type else self.get_question_type()

    def get_question_type(self) -> str:
        """get the question type
        
        Returns:
            Token -- [description]
        """

        if self is None or self.doc is None:
            return None
        qtokens = [token for token in self.doc if token.tag_ in WHs and token.lemma_ != 'that']
        if (len(qtokens) > 1):
            lemmas = [q.lemma_ for q in qtokens]
            for word in ['what', 'how']:
                if word in lemmas:
                    idx = lemmas.index(word)
                    return qtokens[idx].lemma_
            return qtokens[0].lemma_
        elif len(qtokens) == 1:
            return qtokens[0].lemma_
        return self.doc[0].lemma_