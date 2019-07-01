import itertools
import difflib
import random
import numpy as np
# import copy
from collections import Counter
from typing import Tuple, List, Dict
from spacy.tokens import Doc, Token

from .helpers import REWRITE_TYPE_DICT, sequence_matcher
from .semantic_rule import SemanticRule
from ..targets.interfaces import OpcodeMeta, PatternMeta, MatchedTokenMeta, RewriteTypeMeta
from ..processor import DUMMY_FLAG
from ..processor.ling_consts import NOT_INCLUDE_POS, WHs,  NNs, VBs, MDs
from ..utils import get_token_feature
from ..task_helpers.qa.evaluator import f1_score

# a flag to help decide if some printing is needed.
IS_DEBUGGING = ''#'rule-name'

# 'replace-wrapper': the overall detect_replace_rule function, 
# 'rule-name': generate rule function. How the rule is named.
# 'detect-rewrite-type': If the algorithm can find related ops where the tokens are overlapped 
#   --- Meaning things are moved or re-structured
# 'match_func': if the on_match function is correctly generated so the rule can be used to generate recover the bsentence.
# 'structural-temp': if to test the structural template extraction
# 'skip-match-func': skip the matching function generation to speed up and only test the rule extraction
# 'change_matched_token_form': this is for generating the match function for form change


class SemanticRuleDetector(object):
    """This is the rule detecting class.
    """
    def __init__(self):
        self.rules = {}
        self.max_token_count = 4

    ########## DEBUGGING FUNCTIONS ##########

    def _merge_noun_chunks(self, doc: Doc) -> Doc:
        """Merge the parsing tree for the noun chunks. Used for detecting structural templates
        
        Arguments:
            doc {Doc} -- processed query text, in the form of spacy doc.
        
        Returns:
            Doc -- In-line modified doc
        """

        for noun_phrase in list(doc.noun_chunks):
            if any([t.tag_ in WHs or \
                t.tag_ in ['JJR', 'JJS', 'CD', 'MD'] or \
                t.ent_type_ != noun_phrase.root.ent_type_ or \
                t.pos_ in ['NUM'] or t.text in ['can'] for t in list(noun_phrase)]):
                continue
            noun_phrase.merge(noun_phrase.root.tag_, noun_phrase.root.lemma_, noun_phrase.root.ent_type_)
        return doc
    
    def _print_queries(self, ops: List[OpcodeMeta], adoc: Doc, bdoc: Doc) -> None:
        """Used for debugging. Print linguistic features of the queries
        
        Arguments:
            ops {List[OpcodeMeta]} -- rewriteing ops [(op=str, fromIdxes=int[], toIdxes=int[])]
            aquery {Query} -- The original query for rewriteing
            bquery {Query} -- The rewritten-to query.
        
        Returns:
            None -- No return
        """

        print('\n')
        print(adoc)
        print(bdoc)
        print([t.pos_ for t in adoc])
        print([t.pos_ for t in bdoc])
        print([t.tag_ for t in adoc])
        print([t.tag_ for t in bdoc])
        print([t.dep_ for t in adoc])
        print([t.dep_ for t in bdoc])
        print([t.ent_type_ for t in adoc])
        print([t.ent_type_ for t in bdoc])
        print(ops)

    ########## COMPUTE THE EDITING OPERATION ##########
    
    def _get_rewrite_ops_text(self, atokens: List[str], btokens: List[str], merge: bool, use_natural: bool) -> List[OpcodeMeta]:
        """Compare two text and get the rewriteing ops

        Arguments:
            atokens {List[str]} -- The original token str list
            btokens {List[str]} -- The rewritten-to token str list
            merge {bool} -- merge continuously rewritten ops (default: {True})
            use_natural {bool} -- use difflib library / self-implemented function (default: {False})
                difflib cannot handle change of preprosition well. 
            
        Returns:
            List[OpcodeMeta] -- list of rewriteing operations
        """
        if use_natural:
            rewritten_raw_native = difflib.SequenceMatcher(a=atokens, b=btokens)
            rewritten_raw_native = ([x for x in rewritten_raw_native.get_opcodes()])
            return [OpcodeMeta(op=l[0], fromIdxes=l[1:3], toIdxes=l[3:5]) for l in rewritten_raw_native]
        else:
            return sequence_matcher(atokens, btokens, merge=merge)['rewrites']

    def _get_rewrite_ops(self, adoc: Doc, bdoc: Doc, key: str='text', merge: bool=True, use_natural: bool=True) -> List[OpcodeMeta]:
        """Compare two queries and get the rewriteing ops
        
        Arguments:
            aquery {Query} -- The original query for rewriteing
            bquery {Query} -- The rewritten-to query.
        
        Keyword Arguments:
            key {str} -- the linguistic feature. (default: {'text'})
            merge {bool} -- merge continuously rewritten ops (default: {True})
            use_natural {bool} -- use difflib library / self-implemented function (default: {False})
                difflib cannot handle change of preprosition well. 
        
        Returns:
            List[OpcodeMeta] -- list of rewriteing operations
        """
        return self._get_rewrite_ops_text(
            list(map(lambda p: get_token_feature(p, key), adoc)), 
            list(map(lambda p: get_token_feature(p, key), bdoc)),
            merge=merge, use_natural=use_natural)



    ########## PATTERN GENERATION ##########
    def _extend_label(self, tokens: List[Token], label: str) -> List[str]:
        """Based on the token and the provided label, determin if more labels should be provided
        
        Arguments:
            tokens {List[Token]} -- list of tokens that need to find linguistic features
            label {str} -- provided label
        
        Returns:
            List[str] -- a list labels, including the original input
        """
        labels = [label]
        if len(tokens) > 1: # too many things need to be determined
            return labels
        if  True: #label in ['orth', 'lemma']: # already most specified
            return labels
        for token in tokens:
            if token.tag_ in WHs or token.tag_ in MDs: # add the wh-word features
                if 'tag' not in labels:
                    labels.append('tag')
            if token.dep_ == 'acl' and token.tag_ == 'VBN':
                if 'dep' not in labels:
                    labels.append('dep')
                if 'tag' not in labels:
                    labels.append('tag')
            if token.pos_ == 'NUM':
                # if number, just go with the pos. Do not include the actual number anymore.
                labels = ['pos']
        #if label == 'tag' and 'pos' not in labels:
        #    labels.append('pos') # if has tag, just add its pos.
        return labels
    
    def _gen_token_pattern(self, token: Token, label: str, use_orth: bool=False, match_op: str=None) -> Dict[str, str]:
        """generate the matcher token 
        
        Arguments:
            token {Token} -- A token
            label {str} -- provided label (orth, lemma, dep, pos, tag, etc.)
        
        Keyword Arguments:
            use_orth {bool} -- just use the orth (default: {False})
            match_op {str} -- repeat match. Can be (+, *, ?, !) (default: {None})
                
        Returns:
            Dict[str, str] -- Generated pattern that could input to the SPACY matcher
        """
        if use_orth:
            label =  'lower' #'orth'
        if not label and match_op: # dummy match that allow a blank to be filled in
            return {'OP': match_op, DUMMY_FLAG: True}
        if not token or not label: # just want to match this token, but no label
            return None
        pattern = {}
        for label in self._extend_label([token], label):
            feature = get_token_feature(token, label)
            if label.lower() == "tag" and feature not in VBs + WHs + NNs:
                return None
            pattern[label.upper()] = get_token_feature(token, label)
        if match_op: # match 0-N times of this token
            pattern['OP'] = match_op
        return pattern
    
    def _gen_pattern_list(self, inspect_index: OpcodeMeta, ops: List[OpcodeMeta], 
        adoc: Doc, bdoc: Doc, rewrite_type: str, matched_op_token_idxes: List[MatchedTokenMeta]) -> List[PatternMeta]:
        """Generate a list of patterns given the phrases being inspected
        
        Arguments:
            inspect_index {OpcodeMeta} -- Pair of inspect idxes
            ops {List[OpcodeMeta]} -- rewriteing ops [(op=str, fromIdxes=int[], toIdxes=int[])]
            aquery {Query} -- The original query for rewriteing
            bquery {Query} -- The rewritten-to query.
            rewrite_type {str} -- Editing type.
            matched_op_token_idxes {List[MatchedTokenMeta]} -- For inner restructing; which op match with which? What's the matched token

        Returns:
            List[PatternMeta] -- A list of rule patterns
        """
        def gen_label_sequence(caregory_meta: RewriteTypeMeta, length: int) -> List[List[str]]: 
            # get all the possible linguistic feature label combinations for a given length
            # if too many tokens in a given sequence, then just remove the combinations. 
            if caregory_meta.allow_product and length <= self.max_token_count:
                return list(itertools.product(caregory_meta.labels, repeat=length))
            else:
                return [[label] * length for label in caregory_meta.labels]
        def extend_pattern_sequence(caregory_meta: RewriteTypeMeta, rule_patterns: List[PatternMeta], 
            atokens: List[Token], btokens: List[Token]) -> List[PatternMeta]:
            # get the existing rule patterns by including additional phrases
            rule_patterns_new = []
            # get label sequences for newly added tokens
            alabels_arr = gen_label_sequence(caregory_meta, len(atokens))
            blabels_arr = gen_label_sequence(caregory_meta, len(btokens))
            # create the label pairs based on if production is allowed
            if caregory_meta.allow_product and len(atokens) <= self.max_token_count and len(btokens) <= self.max_token_count:
                labels = [(alabels, blabels) for alabels, blabels in itertools.product(alabels_arr, blabels_arr)]
            else:
                labels = zip(alabels_arr, blabels_arr)
            for rule_pattern in rule_patterns:
                for alabels, blabels in labels:
                    apatterns = [ self._gen_token_pattern(token=t, label=alabels[idx]) for idx, t in enumerate(atokens) ]
                    bpatterns = [ self._gen_token_pattern(token=t, label=blabels[idx]) for idx, t in enumerate(btokens) ]
                    if any([a == None for a in apatterns]) or any([b == None for b in bpatterns]):
                        continue
                    rule_patterns_new.append(PatternMeta(
                        before=rule_pattern.before + apatterns,
                        after=rule_pattern.after + bpatterns
                    ))
            return rule_patterns_new
        # compute the base.
        a_prev_idx, b_prev_idx = inspect_index.fromIdxes[0], inspect_index.toIdxes[0]
        rule_patterns = [ PatternMeta(before=[], after=[]) ]
        # extend the patterns
        for op in ops: # extend patterns
            rule_patterns = extend_pattern_sequence(caregory_meta=REWRITE_TYPE_DICT['unchange'], rule_patterns=rule_patterns, 
                atokens=list(adoc[a_prev_idx:op.fromIdxes[0]]), btokens=list(bdoc[b_prev_idx:op.toIdxes[0]]))
            rule_patterns = extend_pattern_sequence(caregory_meta=REWRITE_TYPE_DICT[rewrite_type], rule_patterns=rule_patterns, 
                atokens=list(adoc[op.fromIdxes[0]:op.fromIdxes[1]]), btokens=list(bdoc[op.toIdxes[0]:op.toIdxes[1]]))
            a_prev_idx, b_prev_idx = op.fromIdxes[1], op.toIdxes[1]
        rule_patterns = extend_pattern_sequence(caregory_meta=REWRITE_TYPE_DICT['unchange'], rule_patterns=rule_patterns, 
            atokens=list(adoc[a_prev_idx:inspect_index.fromIdxes[1]]), btokens=list(bdoc[b_prev_idx:inspect_index.toIdxes[1]]))
        #### This part starts filtering. Some patterns will be fitlered before reaching the next step.
        rule_patterns_to_keep = [True for _ in rule_patterns]
        for idx, rule_pattern in enumerate(rule_patterns): # for each rule
            if not rule_patterns_to_keep[idx]: # already know it's a removed rule
                continue
            # second, if there are some matches
            for matched in matched_op_token_idxes: # for each matched place
                # convert local idxes to global idxes *in the pattern*
                before_token_idxes = [ops[matched.ops_idxes[0]].fromIdxes[0] + t_idxes[0] - inspect_index.fromIdxes[0] for t_idxes in matched.tokens_idxes]
                after_token_idxes = [ops[matched.ops_idxes[1]].toIdxes[0] + t_idxes[1]  - inspect_index.toIdxes[0] for t_idxes in matched.tokens_idxes]
                # if any of these matched tokens have strange matches
                if any ([ # if for the matched tokens, the used linguistic label do not match
                    len(set(rule_pattern.before[before_idx].keys()) - set(rule_pattern.after[after_idx].keys()) | 
                    set(rule_pattern.after[after_idx].keys()) - set(rule_pattern.before[before_idx].keys())) != 0
                    for before_idx, after_idx in zip(before_token_idxes, after_token_idxes)]):
                    rule_patterns_to_keep[idx] = False
                    break # already know this is not going to be included, so just break to increase spead
        rule_patterns = [r for idx, r in enumerate(rule_patterns) if rule_patterns_to_keep[idx]]
        return rule_patterns
    
    def _extract_phrase_tag(self, doc: Doc, idxes: List[int], label: str = 'pos', merge_into_one: bool=True) -> List[str]:
        """extract some phrase tag.
        
        Arguments:
            doc {Doc} -- the complete doc
            idxes {List[int]} -- the token idxes for the phrase
        
        Keyword Arguments:
            label {str} -- linguistic feature tag (default: {'pos'})
            merge_into_one {bool} -- if we want to just merge and find the most common tag for a phrase
        
        Returns:
            List[str] -- linguistic features for the given phrase
        """
        if idxes[1] == idxes[0]: # if no tokens in the given indexes
            return ''
        elif idxes[1] - idxes[0] == 1: # only one token. Return that.
            return get_token_feature(doc[idxes[0]], label)
        else:
            span = doc[idxes[0]:idxes[1]] # extract the span
            if span in list(doc.noun_chunks) and label in ['pos', 'tag']: # if we are sure this is NOUN
                return 'NOUN' if label == 'pos' else 'NN'
            # delete unnecessary tags
            span_list = list(span)
            #span_filter_words = [t for t in span_list if t.text not in STOP_WORDS and t.lemma_ not in STOP_WORDS]
            filtered_span = [t for t in span_list if t.pos_ not in NOT_INCLUDE_POS]
            filtered_span = span_list if not filtered_span else filtered_span
            token_features = [get_token_feature(t, label) for t in filtered_span]
            if merge_into_one:
                c = Counter(token_features)
                feature, _ = c.most_common()[0] # get the most frequently occurring linguistic feature
                return feature
            else: 
                return token_features

    ########## DETECT THE EDITING TYPE ##########

    def _detect_rewrite_type(self, ops: List[OpcodeMeta], adoc: Doc, bdoc: Doc) -> Tuple[str, List[MatchedTokenMeta]]:
        """First step in the rule extraction; Find the rewriteing type. Could be:
            unchange: same query
            structural: fill in blanks.
            change form: NN -> NNS (dog -> dogs), VB -> VBN (text -> texting)
            change-semantic: no words matched in the op; some more interesting change.
            local-restructure: change the structures within a op
            global-resturcture: mess around the entire sentence, but still could find matched tokens
            large-change: everything else
        
        Arguments:
            ops {List[OpcodeMeta]} -- rewriteing ops [(op=str, fromIdxes=int[], toIdxes=int[])]
            aquery {Query} -- The original query for rewriteing
            bquery {Query} -- The rewritten-to query.
        
        Returns:
            Tuple[str, List[MatchedTokenMeta]] -- [rewrite_type, matched_op_token_idxes]
                matched_op_token_idxes: which op match with which? What's the matched token 
        """

        rewrite_type = ''
        # first, if no change happened
        if not ops:
            return 'unchange', []
        # get the tokens
        a_tokens_ops = [list(adoc[op.fromIdxes[0]:op.fromIdxes[1]]) for op in ops] #[tokens] per op
        b_tokens_ops = [list(bdoc[op.toIdxes[0]:op.toIdxes[1]]) for op in ops]        
        # get the lemma
        #a_lemmas = [remove_stopwords(tokens=tokens) for tokens in a_tokens]
        #b_lemmas = [remove_stopwords(tokens=tokens) for tokens in b_tokens]
        a_lemmas_ops = [[t.lemma_ for t in tokens] for tokens in a_tokens_ops]
        b_lemmas_ops = [[t.lemma_ for t in tokens] for tokens in b_tokens_ops]
        # compute the local matched tokens in the *global* rewrite phrases
        matched_op_token_idxes = []
        # ops_idxes=(from, to) the op indexes with certain matched tokens
        # tokens_idxes=[(from, to)] (from, to); this is the idx in the sub-ops, not in the original sentence.
        for from_op_i, a_lemmas in enumerate(a_lemmas_ops):
            for to_op_i, b_lemmas in enumerate(b_lemmas_ops):
                if f1_score(a_lemmas, b_lemmas)['f1'] > 0.3: #TODO: threshod????
                    matched_token_idxes = [(from_idx, b_lemmas.index(lemma)) 
                        for from_idx, lemma in enumerate(a_lemmas) if lemma in b_lemmas]
                    matched_op_token_idxes.append(MatchedTokenMeta(ops_idxes=(from_op_i, to_op_i), tokens_idxes=matched_token_idxes))
                    continue
        # self matched
        self_matched_op_token_idxes = [match for match in matched_op_token_idxes if match.ops_idxes[0] == match.ops_idxes[1]]        
        if not matched_op_token_idxes: # no matched at all
            rewrite_type = 'change-semantic' if len(ops) == 1 else 'large-change' # TODO: delete this part?
            # this part can compute the wordnet similarity
        elif len(self_matched_op_token_idxes) == len(ops) and len(self_matched_op_token_idxes) == len(matched_op_token_idxes):# all matches are self-matches
            # all the lemmas are the same, meaning only the form is changed
            if all([' '.join([t.lemma_ for t in a_tokens_ops[matched_token.ops_idxes[0]]]) == 
                ' '.join([t.lemma_ for t in b_tokens_ops[matched_token.ops_idxes[1]]]) 
                 for matched_token in self_matched_op_token_idxes]):
                rewrite_type = 'change-form' #  Self-changed form: the changed match should go all the way to tags: [orth, tag]
            else:
                rewrite_type = 'local-restructure' 
        elif len(matched_op_token_idxes) == len(ops) or \
            (len([op for op in ops if op.op =='insert']) == len([op for op in ops if op.op =='delete']) and \
                len(ops) - 2 * len([op for op in ops if op.op =='insert']) == len(matched_op_token_idxes) - len([op for op in ops if op.op =='insert']) ): 
            # replacing at several places or "insert" moves to "delete"
            rewrite_type = 'move'
        else:
            rewrite_type = 'global-restructure'
        
        if IS_DEBUGGING == 'detect-rewrite-type':
            print(IS_DEBUGGING)
            self._print_queries(ops, adoc, bdoc)
            print(rewrite_type)
            print(matched_op_token_idxes)
        return rewrite_type, matched_op_token_idxes

    def detect_rules_per_pair(self, adoc: Doc, bdoc: Doc, target_cmd: str) -> None:
        """Detect rules and templates for each pair of queries.
        
        Arguments:
            aquery {Query} -- The original query for rewriteing
            bquery {Query} -- The rewritten-to query.
        
        Returns:
            None -- No return.
        """
        def check_pos(a_patterns: List[Dict[str, str]], b_patterns: List[Dict[str, str]]) -> bool: 
            # if doing replace, then we need at least one actual text
            # TODO Do we need this??
            counter = Counter()
            if len(a_patterns) == 0: # If no a_pattern, then cannot be applied to on-match function later, then just remove
                return False
            for p in b_patterns:
                p_key, p_values = list(p.keys())[0], list(p.values())[0]
                if p_key.lower() not in ['orth', 'lemma', 'lower']:
                    counter[p_values] += 1
            for p in a_patterns:
                p_key, p_values = list(p.keys())[0], list(p.values())[0]
                if p_key.lower() not in ['orth', 'lemma', 'lower']:
                    counter[p_values] -= 1
            most_common = counter.most_common(1)
            if len(most_common) == 0 or most_common[0][1] <= 0:
                return True
            return False
        if adoc.text == bdoc.text: # same query
            return # since this dataset do not contain any actual occurrence information, just jump
        # actually find the rules
        ops = self._get_rewrite_ops(adoc, bdoc, key='text', use_natural=True) # compute the rewrites
        ops = [op for op in ops if op.op != 'equal'] # filter the kept ops
        rewrite_type, matched_op_token_idxes = self._detect_rewrite_type(ops, adoc, bdoc)
        '''
        if rewrite_type  == 'move': # give one more chance to fix the NOUN OF NOUN case
            ops_ = self._get_rewrite_ops(aquery_.doc, bquery_.doc, use_natural=False) # compute the rewrites
            ops_ = [op for op in ops_ if op.op != 'equal'] # filter the kept ops
            rewrite_type_, matched_op_token_idxes_ = self._detect_rewrite_type(ops_, aquery_, bquery_)
            #if 'restructure' in rewrite_type_:
            rewrite_type, matched_op_token_idxes, ops = rewrite_type_, matched_op_token_idxes_, ops_
        '''
        if not rewrite_type or rewrite_type == 'unchange': # if cannot understand the category --- just return
            return None
        if IS_DEBUGGING == 'structural-temp' and rewrite_type == 'structural':
            self._print_queries(ops, adoc, bdoc)
        # the first and last rewritten idxes in both queries
        from_start, from_end, to_start, to_end = ops[0].fromIdxes[0], ops[-1].fromIdxes[1], ops[0].toIdxes[0], ops[-1].toIdxes[1]
        # create pairs of inspect idxes. each inspect index is [start, end]. The total range for inspecting.
        inspect_indexes = [ OpcodeMeta(op='replace', fromIdxes=[from_start, from_end], toIdxes=[to_start, to_end])]
        ###### insert neighboring words
        if rewrite_type != 'move' and rewrite_type != 'structural' and rewrite_type != 'change-form': 
            # add some additional neighbors if the category is not move
            # this is one word off.
            if from_start > 0 and to_start > 0:
                inspect_indexes.append(OpcodeMeta(op='replace', fromIdxes=[from_start-1, from_end], toIdxes=[to_start-1, to_end]))
            if from_end < len(adoc) and to_end < len(bdoc):
                inspect_indexes.append(OpcodeMeta(op='replace', fromIdxes=[from_start, from_end+1], toIdxes=[to_start, to_end+1]))
            # two way off.
            if from_start > 0 and to_start > 0 and from_end < len(adoc) and to_end < len(bdoc):
                inspect_indexes.append(OpcodeMeta(op='replace', fromIdxes=[from_start-1, from_end+1], toIdxes=[to_start-1, to_end+1]))
            elif from_start > 1 and to_start > 1:
                inspect_indexes.append(OpcodeMeta(op='replace', fromIdxes=[from_start-2, from_end], toIdxes=[to_start-2, to_end]))
            elif from_end < len(adoc)-1 and to_end < len(bdoc)-1:
                inspect_indexes.append(OpcodeMeta(op='replace', fromIdxes=[from_start, from_end+2], toIdxes=[to_start, to_end+2]))
        for inspect_index in inspect_indexes: # [::-1] start from the longest one
            # generate pattern
            rule_patterns = self._gen_pattern_list(
                inspect_index, ops, adoc, bdoc, rewrite_type, matched_op_token_idxes)
            for rule_pattern in rule_patterns: # for each rule
                # first, if the RHS had less information than LHS, delete.
                # TODO: Not sure if this is useful...
                # skip the structural part
                #if not check_pos(rule_pattern.before, rule_pattern.after):
                #    continue
                rule = SemanticRule(pattern=rule_pattern, target_cmd=target_cmd)
                self.rules[rule.rid] = rule

    def detect_rule_wrapper(self, 
        adoc, bdoc, 
        instances: List['Instance'],
        target_cmd: str='question',
        sample_size: int=50) -> int:
        """The wrapper function for extracting rules.
        
        Arguments:
            queries {List[Query]} -- A list of queries that are paraphrases of each other.
        
        Returns:
            int -- Number of query pairs generated based on the input query.
        """
        #pairs = list(itertools.combinations(queries, 2))
        #for adoc, bdoc in pairs:                
        #if IS_DEBUGGING:
        #    self._print_queries(ops, aquery, bquery)
        try:
            print(adoc, bdoc)
            self.detect_rules_per_pair(adoc, bdoc, target_cmd)
            if len(instances) <= sample_size:
                samples = instances
            else:
                samples = random.sample(instances, sample_size)
            rules = SemanticRule.filter_rules_via_sample_augment(self.rules, samples)
            return rules
        except:
            raise