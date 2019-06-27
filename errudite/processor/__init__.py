from .spacy_annotator import SpacyAnnotator
from .helpers import *
from .ling_consts import *

spacy_annotator = SpacyAnnotator() # use_whitespace=True
#spacy_annotator_quick = SpacyAnnotator(disable=['parser', 'ner', 'textcat'])
DUMMY_FLAG = spacy_annotator.model.vocab.add_flag(lambda text: True)