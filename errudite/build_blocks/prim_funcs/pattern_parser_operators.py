import pyparsing as pp
import traceback
import itertools
from spacy.matcher import Matcher  # pylint: disable=E0611
from typing import List
from ...processor.ling_consts import POS, NNs, WHs, VBs, MDs, NNP_NERS, DEPs
from ...processor import spacy_annotator
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# get one saved rule across the matcher.
CUR_SAVED_RULE = None
matcher = Matcher(spacy_annotator.model.vocab)

class PatternOpWraper(object):
    def __eq__(self, other):
        if isinstance(other, PatternOpWraper):
            return self.__repr__() == other.__repr__()
        else:
            return False
    def get_pattern(self, **kwargs) -> any:
        """get value function.
        
        Returns:
            {any} -- any kind
        """
        raise NotImplementedError

class patternOp(PatternOpWraper):
    """Single pattern operator. lower:lower
    """    
    def __init__(self, tokens, label):
        self.value = tokens[0]
        self.label = label.upper()
        if self.label == 'LOWER':
            self.value = self.value.lower()

    def get_pattern(self):
        if self.label == 'ENT_TYPE' and self.value == 'ENT':
            pattern = {'ENT_TYPE': '', 'OP': '!'}
        elif self.value[-1] in ['*'] and len(self.value) == 1:
             pattern = {'LOWER': '', 'OP': '!'}
        elif self.value[-1] in ['*', '+', '!', '?'] and len(self.value) > 1:
            pattern = {self.label: self.value[:-1], 'OP': self.value[-1] }
        else:
            pattern = {self.label: self.value}
            if self.label == 'ENT_TYPE':
                pattern['OP'] = '+'
        return pattern
    
    def __repr__(self):
        return f"{self.label}:{self.value}"     

class patternSetOp(PatternOpWraper):
    """The or operation: (what, which)
    """
    def __init__(self, tokens):
        while tokens[0].__class__.__name__ == 'ParseResults':
            tokens = tokens[0]
        self.values = tokens
    
    def get_pattern(self):
        if isinstance(self.values, PatternOpWraper):
            return [ self.values[0].get_pattern() ]
        else:
            return [ v.get_pattern() for v in self.values ]
        
    def __repr__(self):
        return f"""{self.values}"""


class patternListOp(PatternOpWraper):
    """Handles the list of patterns for token list. (what, which) NN
    
    """

    def __init__(self, tokens):
        while tokens[0].__class__.__name__ == 'ParseResults':
            tokens = tokens
        self.values = tokens
        
    def gen_pattern_list(self):
        if isinstance(self.values, PatternOpWraper):
            tokens_patterns = [ self.values.get_pattern() ]
        else:
            tokens_patterns = [ v.get_pattern() for v in self.values ]
        tokens_patterns = [ t if type(t) == list else [t] for t in tokens_patterns ]
        if len(tokens_patterns) == 1:
            return tokens_patterns
        else:
            return list(itertools.product(*tokens_patterns))

    def __repr__(self):
        return f"""{self.values}"""
    
def gen_set(pattern_single):
    pattern_set = pp.nestedExpr(
        opener='(', closer=')',
        content=pp.delimitedList(pattern_single, delim=delim)) \
        .setParseAction(patternSetOp)
    pattern_ = pattern_single | pattern_set
    return pattern_


# define a function that can add *+! to the end
def gen_re_list(pattern_list: List[str]):
    pattern_list = [p for p in pattern_list if p !='']
    output = []
    for op in ['+', '*']:
        output += [ p + op for p in pattern_list ]
    output += pattern_list
    return output

# define the logic and match operations
lp = pp.Suppress("(") 
rp = pp.Suppress(")")
delim = pp.Literal("|") | pp.Literal(",")


orth_single = pp.Word((pp.printables + "–" + pp.punc8bit) \
    .replace(',', '').replace('(', '').replace(')', '')) \
    .setParseAction(lambda t: patternOp(t, 'lower') )
orth_ = gen_set(orth_single)

ent_single = pp.oneOf(gen_re_list(NNP_NERS) + ['ENT'], caseless=False) \
    .setParseAction(lambda t: patternOp(t, 'ent_type') )
ent_ = gen_set(ent_single)

tag_single = pp.oneOf(gen_re_list(NNs + WHs + VBs + MDs)) \
    .setParseAction(lambda t: patternOp(t, 'tag') )
tag_ = gen_set(tag_single)

pos_single = pp.oneOf(gen_re_list(POS)) \
    .setParseAction(lambda t: patternOp(t, 'pos') )
pos_ = gen_set(pos_single)

compound_single = ent_ | tag_ | pos_ | orth_
ling_pattern_expr = pp.OneOrMore(compound_single)\
    .setParseAction(patternListOp).setResultsName("conditions")
# pattern = data.gen_pattern_list()

def parse_cmd(cmd: str) -> patternListOp:
    try:
        parsed = ling_pattern_expr.parseString(cmd)["conditions"]
        if isinstance(parsed, PatternOpWraper): 
            return parsed
        else:
            raise DSLValueError(f"No valid input to [ pattern_parser ]. input: {cmd}")
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ length ]: {e}")
        #logger.error(ex)
        raise(ex)