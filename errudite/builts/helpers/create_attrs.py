from ..attribute import Attribute

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