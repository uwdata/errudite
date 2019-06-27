from nltk.corpus import wordnet as wn
from typing import Union
from spacy.tokens import Span, Token, Doc
import functools

from ...processor import spacy_annotator
from ...utils.check import DSLValueError
from ..prim_func import PrimFunc

def match_super(orgin: str, new: str) -> str:
    if orgin[0].isupper():
        new = new[0].upper() + new[1:]
    return new

def find_similar_token(word: Union[Token, str], search_type: str) -> str:
    """
    Find related words from wordnet, given a token's text and POS. 
    If cannot find one, return itself.
    
    *When using the DSL parser*, this function can be called in alternative ways, 
    with ``search_type`` being automatically filled in: 
    ``[get_synonym|get_antonym](word)``.

    Parameters
    ----------
    word : Union[Token, str]
        The given word. Can be a spacy token or just a string (in which case, 
        the POS tag will not be specified.)
    search_type : str
        "synonym" or "antonym".
    
    Returns
    -------
    str
        The synonym or the antonym string.
    """
    lemma = ""
    words = set()
    if search_type not in ["synonym", "antonym"]:
        raise DSLValueError(f"Invalid token search_type: [ {search_type} ]. Has to be 'synonym' or 'antonym'. ")
    if type(word) == str:
        word = spacy_annotator.process_text(word)
        if len(word) > 0:
            word = word[0]
    if type(word) == Token:
        synsets = wn.synsets(word.lemma_, getattr(wn, word.pos_, None))
        lemma = word.lemma_
    else:
        raise DSLValueError(f"Invalid input to find_similar_token: [ {word} ({type(word)}) ].")
    for syn in synsets:
        for l in syn.lemmas(): 
            if search_type == "synonym":
                words.add(l.name()) 
            elif search_type == "antonym":
                if l.antonyms(): 
                    words.add(l.antonyms()[0].name()) 
    if lemma in words:
        words.remove(word.lemma_)
    if words:
        words = sorted(list(words), 
            key=lambda l: word.similarity(spacy_annotator.process_text(l)), 
            reverse=True)
        return match_super(word.text, words[0].lower())
    else:
        #raise DSLValueError(f"Invalid input to find_similar_token: [ {word} ({type(word)}) ].")
        return word.text

PrimFunc.register("get_synonym")(functools.partial(find_similar_token, search_type='synonym'))
PrimFunc.register("get_antonym")(functools.partial(find_similar_token, search_type='antonym'))