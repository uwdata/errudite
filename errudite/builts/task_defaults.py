from .attribute import Attribute
from .group import Group

attr_list = []

attr_list.append(Attribute(
    name='answer_type',
    description='Answer type computed based on the groundtruths.',
    cmd='answer_type(groundtruths)'))

attr_list.append(Attribute(
    name='question_type',
    description='The WH-word or the first word in sentence.',
    cmd='question_type(question)'))

attr_list.append(Attribute(
    name='context_length',
    description='The length of the context paragraph.',
    cmd='length(context)'))

attr_list.append(Attribute(
    name='question_length',
    description='The length of the answer.',
    cmd='length(question)'))

attr_list.append(Attribute(
    name='sentence_length',
    description='The min length of the sentence containing the groundtruths.',
    cmd='length(sentence(groundtruths))'))

attr_list.append(Attribute(
    name='groundtruths_length',
    description='The min length of the groundtruths.',
    cmd='length(groundtruths)'))

QA_ATTRS = { a.name: a for a in attr_list }
VQA_ATTRS = { a.name: a for a in attr_list if \
    a.name not in ['context_length', 'sentence_length'] }


group_list_qa, group_list_vqa = [], []

group_list_qa.append(Group(
    name='all_instances',
    description='The group that includes all the instances.',
    cmd=''))
"""
group_list_qa.append(Group(
    name='exact_match',
    description='The nearest words around the placeholder are also found in the passage surrounding an entity marker.',
    cmd_str='overlap(question, sentence(groundtruths)) >= 0.75 and overlap(question, sentence(groundtruths, shift=[-2,-1,1,2])) < 0.7'))

group_list_qa.append(Group(
    name='distractor',
    description='The presence of entities similar to ground truth.',
    cmd_str='count(ENT(context), ENT(groundtruths, get_most_common=False)) > 0'))


group_list_qa.append(Group(
    name='coreference',
    description='The sentence containing the groundtruth has coreference issue.',
    cmd_str='not has_all( LEMMA(sentence(groundtruths)), LEMMA(question, pattern="ENT"))'))
# and has_all( LEMMA(sentence(groundtruth, shift=[-1,0,1])), LEMMA(question, pattern="ENT"))

group_list_qa.append(Group(
    name='multi_sentence',
    description='Requires reasoning over multiple sentences.',
    cmd_str='(overlap(question, sentence(groundtruths)) < 0.5 and ' + \
        'overlap(question, sentence(groundtruths, shift=[-2,-1,1,2])) >= 0.7)'))

group_list_qa.append(Group(
    name='long_sentence',
    description='The sentence containing the groundtruth is too long for the model to make sense of.',
    cmd_str='length(sentence(groundtruths)) > 50'))

group_list_qa.append(Group(
    name='paraphrase',
    description='After the question is paraphrased into declarative form, its syntactic dependency structure does not match that of the answer sentence even after local modifications.',
    cmd_str= '(overlap(question, sentence(groundtruths)) < 0.75 or ' + \
        'not has_all(LEMMA(sentence(groundtruth)), LEMMA(question, pattern="VERB"))) and ' + \
        'overlap(question, sentence(groundtruths, shift=[-2,-1,1,2])) < 0.5)'))

group_list_qa.append(Group(
    name='rare_token',
    description='The token are rarely presented in the training data.',
    cmd_str='freq(groundtruths, target_type="answer") < 50'))
# freq(prediction (model="ANCHOR"), target_type="answer") > 
group_list_qa.append(Group(
    name='long_dep_distance',
    description='The answer can only be inferred by synthesizing information distributed across multiple sentences.',
    cmd_str='dep_distance(groundtruths) > 30'))
"""

group_list_vqa.append(Group(
    name='all_instances',
    description='The group that includes all the instances.',
    cmd=''))



QA_GROUPS = { a.name: a for a in group_list_qa }
VQA_GROUPS = { a.name: a for a in group_list_vqa }