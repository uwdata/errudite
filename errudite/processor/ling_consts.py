# TODO: make sure this part is correct
NNs = """
NN NNP NP NNS NNPS
""".split()

WHs =  """
WRB WP WDT WP$
""".split()

VBs = """
VB VBG VBD VBN VBP VBZ
""".split()

# delete these tokens when computing phrase tags
POS = """
ADJ ADP ADV AUX 
CONJ CCONJ DET 
INTJ NOUN NOUN NUM PART PRON PROPN PUNCT SCONJ SYM
VERB
""".split()

NOT_INCLUDE_POS = """
ADP IN RP RB DET CONJ PUNCT CCONJ PART SCONJ SYM
""".split()

MDs = """MD""".split()

# ners
NNP_NERS = """
PERSON NORP FAC ORG GPE LOC PRODUCT EVENT
WORK_OF_ART LAW LANGUAGE DATE TIME PERCENT
MONEY QUANTITY ORDINAL CARDINAL
""".split()
# NNP_NERS = ['PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 
#    'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE']

# dep
DEPs = """
acl acomp advcl advmod agent amod appos attr aux auxpass 
case cc ccomp compound conj cop csubj csubjpass
dative dep det dobj expl intj mark meta
neg nn nounmod npmod nsubj nsubjpass nummod 
oprd obj obl 
parataxis pcomp pobj poss preconj prep prt punct 
quantmod 
relcl root xcomp
""".split()

STOP_WORDS_semantic = set("""
a about above across after afterwards again against all almost alone along
already also although always am among amongst amount an and another any anyhow
anyone anything anyway anywhere are around as at

back be became because become becomes becoming been before beforehand behind
being below beside besides between beyond both bottom but by

can cannot ca could

did do does doing done down due during

each either else elsewhere empty enough even ever every
everyone everything everywhere except

few for former formerly from front full further

get give go

had has have he hence her here hereafter hereby herein hereupon hers herself
him himself his however

i if in indeed into is it its itself

keep

last latter latterly least less

just

made make many may me meanwhile might mine more moreover most mostly move much
must my myself

name namely neither never nevertheless next no nobody none noone nor not
nothing now nowhere

of off often on once one only onto or other others otherwise our ours ourselves
out over own

part per perhaps please put

quite

rather re really regarding

same say see seem seemed seeming seems serious several she should show side
since so some somehow someone something sometime sometimes somewhere
still such

take than that the their them themselves then thence there thereafter
thereby therefore therein thereupon these they this those though
through throughout thru thus to together too top toward towards

under until up unless upon us used using

various very very via was we well were whatever whence whenever
whereafter whereas whereby wherein whereupon wherever whether while
whither whoever whole will with within without would

yet you your yours yourself yourselves
""".split())
