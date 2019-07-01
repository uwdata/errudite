import functools
from typing import List, Dict
from spacy.tokens import Token
from spacy.matcher import Matcher # pylint: disable=E0611

import difflib
from spacy.tokens import Token, Doc, Span
from pattern.en import referenced # pylint: disable=E0401,E0611

from .rewrite import Rewrite
from ..targets.instance import Instance
from .helpers import match_super, get_str_from_pattern, sequence_matcher, change_matched_token_form
from ..utils import convert_doc, convert_list, merge_list
    
from ..utils import str_to_func, func_to_str

#from backend.utils.helpers import convert_list
#from backend.build_block.prim_funcs.overlap import overlap

from ..build_blocks.prim_funcs.pattern_parser_operators import \
    matcher, parse_cmd, CUR_SAVED_RULE
from ..processor import spacy_annotator
from ..targets.interfaces import PatternMeta, OpcodeMeta

@Rewrite.register("ReplacePattern")
class ReplacePattern (Rewrite):
    """
    A rule that rewrites the target_cmd part of an instance 
    by replacing from_cmd with to_cmd. The rid is: ``{from_cmd} -> {to_cmd}``.
    
    Both from_cmd and to_cmd can include linguistic annotations, in ALL CAPS.
    For example, you can input ``from_cmd="what NOUN"``, and ``to_cmd="which NOUN"``.
    If no linguistic annotation, this will automatically switch to  
    ``errudite.rewrites.replace_str.ReplaceStr``

    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("ReplacePattern")
        
    Parameters
    ----------
    from_cmd : str, optional
        The pattern that can be replaced. By default ''
    to_cmd : str, optional
        The pattern to replace to, by default ''
    description : str, optional
        The description, by default 'Change one pattern to another.'
    target_cmd : str, optional
        The target to be rewritten. It has to be a member of ``Instance.instance_entries``, 
        by default 'context'
    """
    def __init__(self,
        from_cmd: str='',
        to_cmd: str='',
        description: str='Change one pattern to another.',
        target_cmd: str='context', **kwargs):
        rid = f'{from_cmd} -> {to_cmd}'
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)
        self.from_cmd = str_to_func(from_cmd)
        self.to_cmd = str_to_func(to_cmd)
        self.matcher = Matcher(spacy_annotator.model.vocab)
        
        if self.from_cmd and self.to_cmd:
            self.pattern = PatternMeta(
                before=self.cmd_to_pattern(self.from_cmd),
                after=self.cmd_to_pattern(self.to_cmd)
            )
            self.ops = self._get_rewrite_ops(self.pattern)
    
    def get_json(self):
        return {
            'rid': self.rid,
            'category': self.category,
            'from_cmd': func_to_str(self.from_cmd),
            'to_cmd': func_to_str(self.to_cmd),             
            'description': self.description,
            'target_cmd': func_to_str(self.target_cmd),
            'class': self.__class__.__name__
        }

    def is_pure_str_replace(self):
        return \
            "STRING" in self.from_cmd or "STRING" in self.to_cmd or \
            (all([get_str_from_pattern(p) != None for p in self.normalize_pattern(self.pattern.before) ]) and \
            all([get_str_from_pattern(p) != None for p in self.normalize_pattern(self.pattern.after) ]))

    def normalize_pattern(self, pattern_arr):
        pattern_arr = convert_list(pattern_arr)
        if not pattern_arr or type(pattern_arr) not in [ list, tuple ]:
            return pattern_arr
        while type(pattern_arr[0]) in [ list, tuple ]:
            pattern_arr = pattern_arr[0]
        return pattern_arr

    def convert_one_pattern(self, pattern_arr: List):
        pattern_arr = self.normalize_pattern(pattern_arr)
        key_arr = []
        for p in pattern_arr:
            keys = [key for key in p.keys() if key != 'OP']
            if not keys:
                continue
            val = p[keys[0]]
            if 'OP' in list(p.keys()) and keys[0] != 'ENT_TYPE':
                val += p['OP']
            if p.get('op', None) == '!' and p.get('ENT_TYPE', None) == '':
                val = 'ENT'
            key_arr.append([keys[0], val])
        return key_arr

    def cmd_to_pattern (self, pattern_cmd: str):
        if not pattern_cmd:
            return None
        pattern_cmd = convert_list(pattern_cmd)
        try:
            patterns = merge_list([parse_cmd(p).gen_pattern_list() for p in pattern_cmd])
            while type(patterns[0]) in [ list, tuple ]:
                patterns = patterns[0]
            return patterns
        except Exception as e:
            print(e)
            pass
    
    def pattern_to_cmd (self, pattern: PatternMeta):
        from_cmd = ' '.join([v[1] for v in self.convert_one_pattern(pattern.before)])
        to_cmd = ' '.join([v[1] for v in self.convert_one_pattern(pattern.after)])
        return from_cmd, to_cmd

    def _get_rewrite_ops(self, pattern: PatternMeta, use_natural: bool=True) -> List[OpcodeMeta]:
        icons = ['TAG', 'POS', 'LEMMA', 'TAG', 'ENT_TYPE', 'LOWER', 'ORTH']
        if use_natural:
            atokens = [v[1] for v in self.convert_one_pattern(pattern.before)]
            btokens = [v[1] for v in self.convert_one_pattern(pattern.after)]
            rewritten_raw_native = difflib.SequenceMatcher(a=atokens, b=btokens)
            rewritten_raw_native = ([x for x in rewritten_raw_native.get_opcodes()])
            return [OpcodeMeta(op=l[0], fromIdxes=l[1:3], toIdxes=l[3:5]) for l in rewritten_raw_native]
        else:
            atokens = merge_list(self.convert_one_pattern(pattern.before))
            btokens = merge_list(self.convert_one_pattern(pattern.after))
            from_idx, to_idx = 0, 0
            output = sequence_matcher(atokens, btokens, merge=False)['rewrites']
            output_refactored = []
            for o in output:
                cur_from_idx = from_idx
                if not (o.fromIdxes[0] == o.fromIdxes[1] or atokens[o.fromIdxes[0]] in icons):
                    from_idx += 1
                cur_to_idx = to_idx
                if not (o.toIdxes[0] == o.toIdxes[1] or btokens[o.toIdxes[0]] in icons):
                    to_idx += 1
                if from_idx == cur_from_idx and cur_to_idx == to_idx:
                    continue
                else:
                    output_refactored.append(OpcodeMeta(
                        op=o.op, 
                        fromIdxes=[cur_from_idx, o.fromIdxes[1] - o.fromIdxes[0] + cur_from_idx], 
                        toIdxes=[cur_to_idx, o.toIdxes[1] - o.toIdxes[0] + cur_to_idx]))
            
            return output_refactored
    

    def get_match_func(self, pattern):
        def _on_match_rewrite(matcher, doc, i, matches, pattern):
            match_id, start, end = matches[i]
            # get meta information for this on-match function
            rule_pattern = PatternMeta(
                before=self.normalize_pattern(pattern.before),
                after=self.normalize_pattern(pattern.after)
            )
            prev_text, after_text = doc[:start].text.strip(), doc[end:].text.strip()
            # keep all the orth in the pattern.
            between_tokens = [get_str_from_pattern(r) for r in rule_pattern.after]

            # fill in all the other None
            for idx, _ in enumerate(between_tokens):
                # if between_tokens[idx]:  # already filled in
                #    continue
                # check what OP it is.
                for op in self.ops:
                    # idx is the idx in the toIdxes
                    # make sure this is in the right count of words. 
                    # Should be because we are using one word a time
                    if op.toIdxes[0] <= idx and op.toIdxes[1] > idx and \
                        op.fromIdxes[1] - op.fromIdxes[0] == op.toIdxes[1] - op.toIdxes[0]:
                        # before, it is from the start to the fromIdx 0
                        # offset of the idx w.r.t op.toIdxes[0], then add the offset to the fromIdx
                        before_idx = idx - op.toIdxes[0] + op.fromIdxes[0]
                        before_doc_idx = before_idx + start
                        # then the after idx.
                        after_idx = idx #+ op.toIdxes[0]
                        
                        if before_idx < 0 or before_idx >= op.fromIdxes[1] or \
                            after_idx < 0 or after_idx >= op.toIdxes[1] or \
                            before_doc_idx < 0 or before_doc_idx >= len(doc):
                            continue
                        between_tokens[idx] = match_super(doc[before_doc_idx].text, 
                            change_matched_token_form(  # form change
                                a_token=doc[before_doc_idx],
                                a_pattern=rule_pattern.before[before_idx],
                                b_pattern=rule_pattern.after[after_idx]))
                        break
            # fill in all the other None
            for idx, _ in enumerate(between_tokens):
                if between_tokens[idx]:  # already filled in
                    continue
                # add appropriate DET
                if 'POS' in rule_pattern.after[idx] and rule_pattern.after[idx]['POS'] == 'DET':
                    if idx < len(between_tokens) - 1 and between_tokens[idx+1]:
                        between_tokens[idx] = referenced(between_tokens[idx+1]).split()[0]
                    elif (start + idx - 1 < len(doc)) and \
                         (start + idx - 1 >= 0):
                        between_tokens[idx] = referenced(doc[start + idx - 1].text).split()[0]  # noqa: E501
            if not None in between_tokens:
                generated_text = ' '.join([prev_text] + between_tokens + [after_text]).strip()
                return (match_id, generated_text)
            return None 
        return functools.partial(_on_match_rewrite, pattern=pattern)

    def add_matcher(self):
        if self.rid in self.matcher:
            return True
        match_func = self.get_match_func(self.pattern)
        if match_func:
            def on_match(matcher, doc, i, matches):
                output = match_func(matcher, doc, i, matches)
                if not output:
                    return False
                matched_id, paraphrase_text = output
                rule_id = spacy_annotator.model.vocab.strings[matched_id]
                if (rule_id, paraphrase_text) not in doc._.paraphrases \
                    and paraphrase_text.lower() != doc.text.lower(): 
                    # TODO: change this to only include unique ones?
                    doc._.paraphrases.append((rule_id, paraphrase_text))
            if type(self.pattern.before) in [tuple, list] and \
                len(self.pattern.before) > 0 and \
                type(self.pattern.before[0]) in [tuple, list]:
                self.matcher.add(self.rid, on_match, *self.pattern.before)
            else:
                self.matcher.add(self.rid, on_match, self.pattern.before)
            return True
        else:
            return False
   
    def _rewrite_target(self, instance) -> str:
        if not self.add_matcher():
            return None
        doc = self._get_target(instance)
        if not doc or not type(doc) == Doc:
            #print('Not a rewriteable doc!!')
            return None
        doc._.paraphrases = []
        self.matcher(doc)
        outputs = [d for d in list(doc._.paraphrases) if d[0] == self.rid]
        doc._.paraphrases = []
        if len(outputs) > 0:
            return outputs[0][1]
        return None

    def __repr__(self) -> str:
        """Override the print func

        Returns:
            str -- The printed function
        """
        return f"[{self.__class__.__name__}] {self.key()}"