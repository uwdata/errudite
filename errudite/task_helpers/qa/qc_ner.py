'''
wtshuang@cs.uw.edu
Adjusted from sQuAD analysis scripts.
Refer to https://spacy.io/api/annotation for the annotation specs.
'''

import sys
sys.path.append('..')
from spacy.tokens import Token
# answe for too long.
LONG_ANSWER_THRESH = 5

# define the formal name for the categories

CATEGORIES = {
    'year': 'YEAR',
    'month': 'MONTH',
    'date': 'DATE',
    'numeric': 'NUM',
    'person': 'HUM',
    'location': 'LOC',
    'entity': 'ENTY',
    'other': 'DESC'
}

# pos: VERB
# basic | gerund or present participle | past tense, past participle |
# non-3rd person singular present | 3rd person singular presen | verb phrase
VBP = set( ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ', 'VP'] ) # tag

# pos: ADJ
# adjective | comparative | superlative | adjective phrase
ADJP = set( ['JJ', 'JJR', 'JJS', 'ADJP'] )
# adverb | comparative | superlative | phrase
ADVP = set( ['RB', 'RBR', 'RBS', 'ADVP'] )

# pos: NOUN, general Noun
# singular or mass | plural | noun phrase | NOT USING | prepositional phrase
NN = set( ['NN', 'NNS', 'NP', 'NP-TMP', 'PP'] )

# pos: PRONPN, proper noun (专有名词)
# noun phrase | NOT USING | proper singular | proper plural | prepositional phrase
NNP = set( ['NP', 'NP-TMP', 'NNP', 'NNPS', 'PP'] )
# all the basic proper noun
NNPS = set(['NNP', 'NNPS'])
# MAKE SURE THIS IS ALL THE TAGS.
# proper singular | proper plural | conjunction, coordinating | 
# left round bracket | right round bracket | comma | determiner | 
# subordinating or preposition | sentence closer | list item marker |
# adjective | pronoun, personal | possessive ending
NNP_POS = set(['NNP', 'NNPS', 'CC', '-LRB-', '-RRB-', ',', 'DT', 'IN', '.', 'LS', 'JJ', 'PRP', 'POS'])
# ners
# NNP_NERS = set(['PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', \
# 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'])
NNP_NERS = ['PERSON', 'NORP', 'FACILITY', 'ORG', 'GPE', 'LOC', 
    'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE']


# Not using | subordinating conjunction | NOT USING ...
CLAUSE = set( ['S', 'SBAR', 'SBARQ', 'SINV', 'SQ'] )

def is_year(token: Token) -> bool:
    '''
    If the time is year
    '''
    try:
        year_str = token.text
        if year_str.endswith('s'):
            year_str = year_str[:-1]
        year = int(year_str)
        if year >= 1000 and year <= 2100:
            return True
    except ValueError:
        pass
    return False

def is_month(token: Token) -> bool:
    MONTHS = set(['january', 'february', 'march', 'april', \
        'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'])
    return token.lemma_ in MONTHS

def is_date(token: Token) -> bool:
    return is_year(token) or is_month(token) or token.ent_type_ in ['DATE', 'TIME'] 

def is_location(token: Token) -> bool:
    return token.ent_type_ in ['LOC', 'GPE']

def is_numeric(token: Token) -> bool:
    return token.tag_ == 'CD' #or token.ent_type_ in ['PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']

def is_person(token: Token) -> bool:
    return token.ent_type_ == 'PERSON'

def is_prop_noun(token: Token) -> bool:
    return token.tag_ in NNP_POS or token.ent_type_ in NNP_NERS

def is_entity(token: Token) -> bool:
    return token.ent_type_ != None

def classify_year(doc) -> bool:
    if len([token for token in doc]) >= LONG_ANSWER_THRESH: # too long
        return False
    return all([is_year(token) for token in doc])

def classify_month(doc) -> bool:
    if len([token for token in doc]) >= LONG_ANSWER_THRESH: # too long
        return False
    return all([is_month(token) for token in doc])

def classify_date(doc) -> bool:
    '''
    If an answer is about date.
    @param <Answer> a targeting answer.
    @return <bool> if is date.
    '''
    if len([token for token in doc]) >= LONG_ANSWER_THRESH: # too long
        return False
    
    return any([is_date(token) for token in doc])

def classify_other_numeric(doc) -> bool:
    '''
    If the answer is a general numeric answer
    @param <Answer> a targeting answer.
    @return <bool> if is other numeric
    '''
    # too long
    if len([token for token in doc]) >= LONG_ANSWER_THRESH:
        return False
    # CD: [tag] cardinal number; [pos] NUM number
    # tag_ == 'CD'
    return any([is_numeric(token) or token.ent_type_ in ['PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'] for token in doc])

def classify_noun(doc) -> bool:
    '''
    @param <Answer> a targeting answer.
    @return <bool> if the answer is a general noun.
    '''
    return all(['NN' in token.tag_ and 'NNP' not in token.tag_ for token in doc])

def classify_proper_noun(doc) -> bool:
    '''
    @param <Answer> a targeting answer.
    @return <bool> if the answer is a general noun.
    '''
    tags = [a.tag_ for a in doc]

    if all([is_prop_noun(token) for token in doc]):
        return True
    if not any([token.tag_ in NNPS for token in doc]):
        return False
    if any([tag in NN for tag in tags]) in NNP and \
        not all( [token.is_lower() for token in list(doc.sents)[0]] ):
        return True
    return False

def classify_person(doc) -> bool:
    '''
    @param <Answer> a targeting answer.
    @return <bool> if the answer is about person.
    '''
    if all([is_person(token) or token.tag_ == 'CC' for token in doc]):
        return True
    num_person = sum([token.ent_type_ == 'PERSON' for token in doc])
    num_tokens = len(doc)
    return 1.0 * num_person / num_tokens >= 0.5

def classify_location(doc) -> bool:
    '''
    @param <Answer> a targeting answer.
    @return <bool> if the answer is about location.
    '''
    num_location = sum([is_location(token) for token in doc])
    num_tokens = len(doc)
    return 1.0 * num_location / num_tokens >= 0.5

def classify_other_entity(doc) -> bool:
    '''
    @param <Answer> a targeting answer.
    @return <bool> if the answer is about other entities.
    '''
    num_ent = sum([int(is_entity(token)) for token in doc])
    num_tokens = len(doc)
    return 1.0 * num_ent / num_tokens >= 0.5

def classify_answer(answer: 'Answer', 
    question: "Question"=None, 
    use_question: bool=True) -> str:
    '''
    @param <Answer> a targeting answer.
    @param <str> an inputing tag generated from the question phrase.
    @return <str> the category of the answer.
    '''
    if classify_year(answer.doc):
        return CATEGORIES['year']
    if classify_month(answer.doc):
        return CATEGORIES['month']
    if classify_date(answer.doc):
        return CATEGORIES['date']
    if classify_proper_noun(answer):
        if classify_person(answer.doc):
            return CATEGORIES['person']
        if classify_location(answer.doc):
            return CATEGORIES['location']
        if classify_other_entity(answer.doc):
            return CATEGORIES['entity']
    if classify_other_numeric(answer.doc):
        return CATEGORIES['numeric']
    return classify_question(question) if use_question else CATEGORIES["other"]

def classify_question(question: 'Question'):
    '''
    Classify the question based on the 
    '''
    # check the question wh-word
    wh_token = question.get_wh_word()
    if wh_token is None: # cannot find the token at all
        return  CATEGORIES['other']
    # build the dependencies
    edge_types = set()
    edge_lemmas = set()

    # ancestors of this nodes
    for child in wh_token.children:
        if child.lemma_ == 'in':
            continue
        edge_types.add(wh_token.lemma_ + ' - ' + child.dep_ + ' -> ' + child.tag_)
        edge_lemmas.add(wh_token.lemma_ + ' - ' + child.dep_ + ' -> ' + child.lemma_)
    # children
    for ancestor in wh_token.ancestors:
        if ancestor.lemma_ == 'in':
            continue
        edge_types.add(wh_token.lemma_ +  ' <- ' + wh_token.dep_ + ' - ' + ancestor.tag_)
        edge_lemmas.add(wh_token.lemma_ +  ' <- ' + wh_token.dep_ + ' - ' + ancestor.lemma_)

    if wh_token.lemma_ in ['what', 'which'] and wh_token.lemma_ + ' <- det - name' in edge_lemmas \
        or wh_token.lemma_ + ' - nsubj -> name' in edge_lemmas \
        or wh_token.lemma_ + ' <- dobj - call' in edge_lemmas or \
        wh_token.lemma_ + ' <- nsubjpass - call' in edge_lemmas:
        return CATEGORIES['entity']
    
    for time_type in ['year', 'date', 'day', 'month', 'time']:
        if wh_token.lemma_ == 'when' \
            or 'what <- det - ' + time_type in edge_lemmas \
            or 'what - nsubj -> ' + time_type in edge_lemmas:
            return CATEGORIES['date'] #'When / What year?'
    
    if 'how <- advmod - many' in edge_lemmas or 'how <- advmod - much' in edge_lemmas:
        return CATEGORIES['numeric'] #'How much / many?'
    
    if wh_token.lemma_ in ['who', 'whom', 'whose']:
        return CATEGORIES['person'] # 'Who?'
    
    for loc_type in ['place', 'city', 'country', 'place', 'state', 'county']:
        if wh_token.lemma_ == 'where' \
            or 'what <- det - ' + loc_type in edge_lemmas \
            or 'what - nsubj -> ' + loc_type in edge_lemmas:
            return CATEGORIES['location'] #'WHERE?'
    '''
    for edge_type in [' <- dobj - ', ' <- nsubjpass - ', ' <- nsubj - ', ' - nsubj -> ', ' - dep -> ']:
        for verb_type in VBP:
            if 'what' + edge_type + verb_type in edge_types:
                return CATEGORIES['verb'] # 'What VB[*]?'
    '''
    for wh_token_type in ['what', 'which']:
        for edge_type in [' <- det - ', ' - nsubj -> ', ' <- nsubj - ', ' <- dobj - ', ' - dep -> ', ' <- nmod - ']:
            for noun_type in NNP:
                if wh_token_type + edge_type + noun_type in edge_types:
                    return CATEGORIES['entity'] # what/which NN[*]
            '''
            for noun_type in NN:
                if wh_token_type + edge_type + noun_type in edge_types:
                    return CATEGORIES['noun'] # what/which NN[*]
            '''
    '''
    if wh_token.lemma_ == 'how':
        return CATEGORIES['noun'] # 'How?'
    '''
    return CATEGORIES['other']

if __name__ == '__main__':
    q ="Question(qid='1', text='What organization is University of Washington in?', vid=0)"
    print(classify_question(q))

    
    #print(classify_answer(a, q))