import pyparsing as pp
import traceback
from .operators import UnOp, BinOp, KwargOp, ArgOp, FuncOp, OpNode, BuildBlockOp, NoneNode

# define the logic and match operations
lp, rp, comma, eq = pp.Suppress("("), pp.Suppress(")"), pp.Suppress(","), pp.Suppress("=")
identifier = pp\
    .Word(pp.alphanums + "_[]") \
    .setParseAction(lambda t: [ t[0] ])
blocks = pp.Group((pp.Literal("attr") | pp.Literal("group")) + pp.Suppress(":") + identifier).setParseAction(BuildBlockOp)
operator = pp.Regex(r">=|<=|!=|>|<|==|in|\*|/|%")
not_ = pp.oneOf(['not','^', '~'], caseless=True)
and_ = pp.oneOf(['and','&'], caseless=True)
or_ = pp.oneOf(['or' ,'|'], caseless=True)

# instead of generic 'value', define specific value types
# integer = pyparsing.Regex(r'[+-]?\d+').setParseAction(lambda t:int(t[0]))
# float_ = pyparsing.Regex(r'[+-]?\d+\.\d*').setParseAction(lambda t:float(t[0]))
# use pyparsing's QuotedString class for this, it gives you quote escaping, and
# automatically strips quotes from the parsed text
quote = pp.QuotedString('"')
number = pp \
    .Regex(r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?") \
    .setParseAction(lambda t: [ float(t[0])])
# when you are doing boolean expressions, it's always handy to add TRUE and FALSE literals
literal_true = pp.Keyword('true', caseless=True).setParseAction(lambda t: True)
literal_false = pp.Keyword('false', caseless=True).setParseAction(lambda t: False)
literal_none = pp.Keyword('None', caseless=False).setParseAction(NoneNode)
boolean_literal = literal_none | literal_true | literal_false

functor = pp.Forward()


lists = pp.Group(pp.Suppress("[") + pp.delimitedList(number | quote | functor) + pp.Suppress("]"))\
    .setParseAction(lambda t: [[ z for z in t[0] ]])
# define the functions
# allow expression to be used recursively
# define the math operators
comparison_term = functor | blocks | lists | number | boolean_literal | quote | functor | identifier 

compounds = pp.operatorPrecedence(comparison_term, [
    # leading sign 
    (not_, 1, pp.opAssoc.RIGHT, UnOp),
    (pp.oneOf("+ -"), 1, pp.opAssoc.RIGHT, UnOp), 
    # multiplication and division 
    (pp.oneOf("* /"), 2, pp.opAssoc.LEFT, BinOp), 
    # addition and subtraction 
    (pp.oneOf("+ -"), 2, pp.opAssoc.LEFT, BinOp)
])

# define arg and kwarg
kw_term = compounds | comparison_term
kwarg = pp.Group(identifier + eq + kw_term).setParseAction(KwargOp)
arg = pp.Group(kw_term).setParseAction(ArgOp)
args = pp.Group(pp.delimitedList(kwarg | arg))
functor << pp \
    .Group((identifier("function") + lp + args("args") + rp)) \
    .setParseAction(FuncOp)

condition_un = compounds
condition_bin = pp.Group(compounds + operator + compounds).setParseAction(BinOp)
condition = condition_bin | condition_un
# define the logic operators
conditions = pp.infixNotation(condition,[
    (not_, 1, pp.opAssoc.RIGHT, UnOp),
    (and_, 2, pp.opAssoc.LEFT, BinOp),
    (or_, 2, pp.opAssoc.LEFT, BinOp),
]).setResultsName("conditions")

def parse_cmd(cmd: str) -> OpNode:
    try:
        parsed = conditions.parseString(cmd)["conditions"]
        if isinstance(parsed, OpNode): 
            return parsed
        else:
            return OpNode()
    except Exception as e:
        print('[parse_cmd]')
        traceback.print_exc()
        return OpNode()
