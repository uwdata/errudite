import re
import string
from typing import Dict, List, Callable, Any, Union
from spacy.tokens import Span, Token, Doc

def normalize_text(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace/
    
    Arguments:
        s {str} -- input string
    
    Returns:
        str -- normalized string
    """
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))



def gen_text_from_sent_list(sentences: List[Span]) -> str:
    '''
    #TODO: to comment
    '''
    return ''.join([s.text + s[-1].whitespace_ for s in sentences])

def span_to_json(sentence: Span, sid: int = 0) -> List[Dict]:
    '''
    @param  <Span> sentence: sentence in span type
    @return <Dict> json-seralized sentences
    '''
    if sentence is None:
        return None
    j_sentence = [{
        'idx': t.i,
        'text': t.text,
        'ner': t.ent_type_,
        'lemma': t.lemma_,
        'pos': t.pos_,
        'tag': t.tag_,
        'whitespace': t.whitespace_,
        'sid': sid #,
        #'matches': []
        } for t in sentence]
    return j_sentence

def spans_to_json(sentences: List[Span]) -> Dict:
    '''
    @param  <Span[]> sentences: sentence in span type
    @return <Dict> json-seralized sentences
    '''
    spans = []
    for sid, sentence in enumerate(sentences):
        spans += span_to_json(sentence, sid=sid)
    return spans

def print_token(token):
    '''
    Print the important of a token
    @token: Token
    '''
    print('[token]')
    print('id\t%d' % token.i)
    print('text\t%s' % token.text)
    print('ner\t%s' % token.ent_type_)
    print('lemma\t%s' % token.lemma_)
    print('is_punct\t%s' % token.is_punct)
    print('is_stop\t%s' % token.is_stop)
    print('pos\t%s'% token.pos_)
    print('tag\t%s'% token.tag_)


def get_token_feature(t: Token, label: str) -> str:
    """Get the linguistic feature given a Spacy.Token obj and a label
    
    Arguments:
        t {Token} -- input token
        label {str} -- linguistic feature to return 
    
    Returns:
        str -- linguistic feature
    """

    if label in ['text', 'orth']:
        return t.text
    if label.lower() == 'ent':
        label = 'ent_type'
    return getattr(t, '{}_'.format(label.lower()), '')