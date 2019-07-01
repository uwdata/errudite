import math
import functools
import os
import random
import numpy as np 
from typing import List, Dict
from spacy.tokens import Token, Doc, Span
from spacy.matcher import Matcher # pylint: disable=E0611

from .rewrite import Rewrite
from .replace_pattern import ReplacePattern
from ..targets.interfaces import TextPairMeta, PatternMeta

@Rewrite.register("SemanticRule")
class SemanticRule(ReplacePattern):
    def __init__(self, pattern: PatternMeta, target_cmd: str):
        ReplacePattern.__init__(self, target_cmd=target_cmd)
        self.pattern = pattern
        self.from_cmd, self.to_cmd = self.pattern_to_cmd(self.pattern)
        self.examples = []
        self.rid = f'{self.from_cmd} -> {self.to_cmd}'
        if self.from_cmd and self.to_cmd:
            self.pattern = PatternMeta(
                before=self.cmd_to_pattern(self.from_cmd),
                after=self.cmd_to_pattern(self.to_cmd)
            )
            self.ops = self._get_rewrite_ops(self.pattern)

    def set_descriptions(self, text_pairs: TextPairMeta) -> None:
        if text_pairs:
            self.description = 'Transformation rule generated for instances like {0} -> {1}'.format(
                text_pairs[0].atext, text_pairs[0].btext)
            random.shuffle(text_pairs)
            self.examples = text_pairs[:3]

    def _compute_pattern_concrete(self) -> int:
        """Compute the concreteness score. e.g. ORTH:is is more concrete than POS:VERB
            This is based on pure heuristic; ORTH is much more specific than any others.

        Arguments:
            pattern {PatternMeta} -- A pattern

        Returns:
            int -- A concrete score
        """

        concrete_level = {'POS': 1, 'ORTH': 4, 'LOWER': 4, 'DEP': 2, 'TAG': 2}
        score = 0
        # p_arr:  [{ORTH: 'Google', POS: 'NOUN'}, {ORTH: 'Now'}])
        for p_arr in [
            self.normalize_pattern(self.pattern.before), 
            self.normalize_pattern(self.pattern.after)]:
            for p in p_arr:  # {ORTH: 'Google', POS: 'NOUN'}
                score += max([
                    concrete_level[label]
                    if label in concrete_level else 1 for label in p.keys()])
        return score

    def __repr__(self) -> str:
        """Override the print func

        Returns:
            str -- The printed function
        """
        return f"[{self.__class__.__name__}] {self.key()}"
    
    def _clear_rule(self) -> None:
        """Delete some template if we deem it not useful. Delete it from dict and matcher.
        Returns:
            None -- No return.
        """
        if self.matcher and self.rid in self.matcher:
            self.matcher.remove(self.rid)
        self.matcher = None
    
    @classmethod
    def filter_rules_greedy_add(cls, 
        rules: Dict[str, 'SemanticRule'],
        mat, 
        rule_cover_sets, 
        rule_names, 
        keep_top_n=None) -> None:
        """A (slightly more advanced) template filtering function.
        This function goes through the following steps:
            1. Build a 2D mat: row - all the templates + col - all the text pairs
            2. Compute how many text pairs each template can cover --
                Try to cover more! N_t + 1 (+1 to prevent 0? Don't have to.)
            3. Compute the rareness of each text pair: 1 / N(templates that cover this text pair)
                Intuitively, it means: to cover this instance in the rule,
                how likely we must keep one specific template that has this pair?
                Production of all text pairs' rareness would give the importance of one template:
                If this template is not selected, are the instances under it likely to
                be covered by other templates as well?
                This would penalize extremely large templates that cover everything.
            4. Compute a concreteness score for each template.
                e.g. the -> None is more concrete than DET -> None. See the function for details
            5. Compute a final template score for template t:
                Score_t = Concrete_t * N_t * (all the rareness of the text pairs in this template)
            6. Iteratively add the next candidate template with the largest Score_t
                to the final template bucket.
                Update the rareness after every iteration ---
                No need to consider a text pair rareness if it's already covered by some selected
                rule, so just remove it. Repeat until all the text pairs are covered.
        Returns:
            None -- [description]
        """
        covered_pairs = set()
        # the occurrence
        ridxes = range(len(rule_names))
        text_pair_per_rule = np.sum(mat, axis=1)
        text_pair_rareness = 1 / np.sum(mat, axis=0)
        _, text_pair_length = np.shape(mat)
        # compute the rareness of a text_pair in a template:
        #   mat[i, j]: to include pair j in this rule, how likely the template i has to be here?
        # mat = mat / template_ocurrence_per_text_pair[:, np.newaxis]
        # init the score for each template
        '''
        print(len(self.templates), len(self.text_pairs))
        print(mat[0, :])
        print(text_pair_rareness)
        print(np.prod([mat[0, :], text_pair_rareness], axis=0))
        '''
        r_occurrences = [ rules[r]._compute_pattern_concrete() for r in rule_names ]
        r_scores = np.zeros(len(rule_names))
        for ridx, _ in enumerate(rule_names):
            if len(text_pair_rareness[mat[0, :] > 0]) == 0:
                score = 0
            else:
                score = math.log(
                    r_occurrences[ridx] *
                    (text_pair_per_rule[ridx] + 1)) * \
                    functools.reduce(lambda x, y: x*y, text_pair_rareness[mat[0, :] > 0])
            r_scores[ridx] = score
            # print(np.prod(cur_rareness[cur_rareness > 0], axis=1))
        should_include = {}
        if keep_top_n:
            ridxes = sorted(ridxes, 
                key=lambda idx: (r_scores[idx],
                                len(rule_cover_sets[idx]),
                                r_occurrences[idx]), reverse=True)
            for idx, ridx in enumerate(ridxes):
                r = rules[rule_names[ridx]]
                if idx < keep_top_n or \
                    (all(['ORTH' in t or 'LOWER' in t for t in r.pattern.before]) and \
                    all(['ORTH' in t or 'LOWER' in t for t in r.pattern.after])):
                    should_include[idx] = True
        else:
            # print(r_scores)
            # start to gradually add instances
            while text_pair_length - len(covered_pairs) > 0 and \
                not all([t == -1 for t in r_scores]):  # noqa
                ridx = max(ridxes,
                    key=lambda idx: (r_scores[idx],
                        len(rule_cover_sets[idx]),
                        r_occurrences[idx]))
                # change it to minus so it will never get picked again
                r_scores[ridx] = -1
                if len(rule_cover_sets[ridx] - covered_pairs) == 0:
                    continue
                for text_idx in rule_cover_sets[ridx]:
                    if text_idx not in covered_pairs:
                        for idx, s in enumerate(r_scores):
                            if mat[idx, text_idx]:
                                r_scores[idx] = s / text_pair_rareness[text_idx]
                        # r_scores = [s / text_pair_rareness[text_idx] for idx, s in enumerate(r_scores) if mat[idx, text_idx]] # noqa
                # record this coverage
                covered_pairs |= rule_cover_sets[ridx]
                should_include[ridx] = True
        # '''
        for ridx, rule_name in enumerate(rule_names):
            if ridx not in should_include:
                rules[rule_name]._clear_rule()
                del rules[rule_name]
        # '''
        return rules

    @classmethod
    def filter_rules_via_sample_augment(cls, 
        rules: Dict[str, 'SemanticRule'],
        samples: List['Instance']) -> None:
        rule_names = list(rules.keys())
        rule_cover_set = [set() for r in rule_names]
        generated_text_pairs = []
        mat_idxes = []
        for sample in samples:
            for rid, r_name in enumerate(rule_names):
                input = rules[r_name]._get_target(sample)
                output = rules[r_name]._rewrite_target(sample)
                if not input or not output:
                    continue
                text_pair = TextPairMeta(atext=input.text, btext=output)
                if text_pair not in generated_text_pairs:
                    generated_text_pairs.append(text_pair)
                text_pair_idx = generated_text_pairs.index(text_pair)
                # add the mat index
                mat_idxes.append((rid, text_pair_idx))
                 # put into the set
                if text_pair_idx not in rule_cover_set[rid]:
                    rule_cover_set[rid].add(text_pair_idx)
        mat = np.zeros((len(rules), len(generated_text_pairs)), dtype=int)
        for mat_idx in mat_idxes:
            mat[mat_idx[0]][mat_idx[1]] = 1
        # set the filter
        rules = cls.filter_rules_greedy_add(rules, mat, 
            rule_cover_set, rule_names, keep_top_n=5)
        # setup the examples and descriptions
        for r in rules.values():
            ridx = rule_names.index(r.rid)
            text_pairs = [ 
                generated_text_pairs[idx] for \
                idx in rule_cover_set[ridx] ]
            r.set_descriptions(text_pairs)
        return rules