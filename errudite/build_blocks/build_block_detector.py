import numpy as np
import itertools
from typing import NamedTuple, Any
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..targets.instance import Instance
from ..targets.label import Label
from ..targets.qa import Answer
from ..targets.interfaces import InstanceKey, PatternCoverMeta
from ..builts import Attribute, Group
from ..utils.helpers import convert_list
from ..utils import Registrable
from ..processor import WHs, VBs, NNs, get_token_feature

class TargetMeta(NamedTuple):
    target: str
    target_cmd: str
    target_entry: Any
    start_idx: int
    end_idx: int

class BuildBlockDetector(Registrable):
    def __init__(self):
        self.instance = None
        self.targets = []
        self.suggestions = []
    
    def _wrap_cmd(self, cmd: str) -> str:
        if not self.instance or self.instance.vid == 0:
            return cmd
        #return f'apply({cmd}, rewrite="{self.instance.rid}")'
        return f'apply({cmd}, rewrite="SELECTED")'

    def set_suggest(self, cmd: str, suggest_type: str, domain=None) -> str:
        if not self.instance:
            return
        cmd_hash = [ v['cmd'] for v in self.suggestions ]
        if cmd not in cmd_hash:
            self.suggestions.append({
                'cmd': cmd,
                'type': suggest_type,
                'domain': domain
            })

    def get_cmd(self, raw_cmd: str) -> str:
        attr = Attribute('', '', cmd=raw_cmd)
        for g in Attribute.values():
            if g.bbw.operator == attr.bbw.operator:
                return f'attr:{g.name}'
        return raw_cmd
    
    def set_instance(self, qid: str, vid: int) -> None:
        self.instance = None
        self.targets = []
        self.suggestions = []
        key = InstanceKey(qid=qid, vid=vid)
        if Instance.exists(key):
            self.instance = Instance.get(key)
        else:
            logger.error(f"{key} does not exist for computing suggestions.")
            self.instance = None
        """
        self.question = self.instance.get_entry('question')
        self.context = self.instance.get_entry('context')
        self.groundtruths = self.instance.get_entry('groundtruths')
        self.predictions = self.instance.get_entry('predictions')
        """

    def set_targets(self, target: str, start_idx: int, end_idx: int):
        raise NotImplementedError
    def _detect_from_question(self, start_idx: int, end_idx: int) -> None:
        raise NotImplementedError
    def _set_performace_info(self):
        prediction = self.instance.get_entry('prediction')
        if not prediction:
            logger.warn(f"Instance does not have prediction.")
        if prediction.get_perform() == 1:
            return 
        if prediction.get_perform() < 1:
            count_g_cmd = self._wrap_cmd('count(groundtruths)')
            count_g_val = Attribute('', '', count_g_cmd).test_one_instance(
                self.instance, Attribute.store_hash(), Group.store_hash())
            if count_g_val > 1:
                self.set_suggest(f'{self.get_cmd(count_g_cmd)} > 1', 'perform')
            cmd = self.get_cmd(self._wrap_cmd(f'perform(model="{Instance.model}", perform_name="{Label.task_primary_metric}")'))
            self.set_suggest(f'{cmd} < 1', 'perform')

    def _get_outlier_attrs(self) -> None:
        for g in Attribute.values():
            value = g.test_one_instance(self.instance, 
            Attribute.store_hash(), Group.store_hash())
            if (type(value) in [float, int]):
                value = int(value * 1000) / 1000
            if g.is_outlier(value):
                if g.dtype == 'continuous':
                    self.set_suggest(f'attr:{g.name} == {value}', 'outlier', g.domain())
                else:
                    self.set_suggest(f'attr:{g.name} == "{value}"', 'outlier', g.domain())

    def _get_data_groups(self) -> None:
        if not self.instance or self.instance.vid == 0:
            return 
        for g in Group.values():
            if g.test_one_instance(self.instance, Attribute.store_hash(), Group.store_hash()):
                self.set_suggest(f'instance in group:{g.name}', 'group', None)

    def on_select(self, 
        target: str, 
        qid: str, vid: int, 
        start_idx: int, end_idx: int) -> None:
        # first reset
        self.set_instance(qid, vid)
        if start_idx == None or end_idx == None:
            self._set_general_info()
        else:
            # set "selected" based on target
            self.set_targets(target, start_idx, end_idx)
            if not self.instance:
                logger.error(f"Instance does not exist for computing suggestions.")
                return
            # get the answer types
            self._set_answer_type()
            # get the attributes if the attr is an outlier
            ## self._get_outlier_attrs()
            # get the included group
            ## self._get_data_groups()
            # get other data based on the target and the interaction
            self._get_ling_feature()
            if target == 'question':
                self._set_question_type(set_general=False)
                self._detect_from_question(start_idx, end_idx)
                        # get the suggestions based on the overlap
            self._set_performace_info()
            self._set_general_info()

    def _set_general_info(self) -> None:
        self._set_question_type(set_general=True)
        self._set_answer_type(set_general=True)

    def _set_question_type(self, set_general: bool=False) -> None:
        if not self.instance or not self.instance.get_entry("question"):
            logger.warn(f"Instance does not have 'question' target.")
            return 
        output_type = 'general' if set_general else 'filter'
        question_type_cmd = self._wrap_cmd('question_type(question)')
        question_type_val = Attribute('', '', question_type_cmd).test_one_instance(
            {self.instance.rid: self.instance}, 
            Attribute.store_hash(), 
            Group.store_hash())
        self.set_suggest(
            f'{self.get_cmd(question_type_cmd)} == "{question_type_val}"', 
            output_type)

    def _set_answer_type(self, set_general: bool=False) -> None:
        output_type = 'general' if set_general else 'filter'
        if not set_general and all([ not isinstance(t.target_entry, Answer) for t in self.targets ]):
            logger.warn(f"Instance does not have 'answer_type'.")
            return
        pred_cmd = f'prediction(model="{Instance.model}")'
        # if the same answer type
        answer_type_g_cmd = f'answer_type(groundtruths)'
        answer_type_g_val = Attribute('', '', answer_type_g_cmd).test_one_instance(
            {self.instance.rid: self.instance}, 
            Attribute.store_hash(), 
            Group.store_hash())
        answer_type_p_cmd = self._wrap_cmd(f'answer_type({pred_cmd})')
        answer_type_p_val = Attribute('', '', answer_type_p_cmd).test_one_instance(
            {self.instance.rid: self.instance}, 
            Attribute.store_hash(), 
            Group.store_hash())
        self.set_suggest(f'{self.get_cmd(answer_type_g_cmd)} == "{answer_type_g_val}"', output_type)
        if answer_type_g_val == answer_type_p_val:
            self.set_suggest(
                f'{self.get_cmd(answer_type_g_cmd)} == {self.get_cmd(answer_type_p_cmd)}',
                output_type, None)
        else:
            self.set_suggest(f'{self.get_cmd(answer_type_g_cmd)} != {self.get_cmd(answer_type_p_cmd)}', output_type)
            self.set_suggest(f'{self.get_cmd(answer_type_p_cmd)} == "{answer_type_p_val}"', output_type)
    
    def _get_ling_feature(self) -> None:
        ling_features = []
        TAG_LISTS = ['ent_type', 'lower', 'pos', 'tag']
        if not Instance.ling_perform_dict:
            logger.warn(f"Instance does not have the dict for linguistic feature-performance.")
            return
        for t in self.targets:
            # first decide the function
            start_idx, end_idx, pattern_func = t.start_idx, t.end_idx, 'has_pattern'
            infos = [ ]
            include_front = t.end_idx <= 3 and t.start_idx <= len(t.target_entry.doc) - t.end_idx
            include_end = t.start_idx >= len(t.target_entry.doc) - 4 and \
                t.start_idx > len(t.target_entry.doc) - t.end_idx
            include_pattern = (not include_front and not include_end) or \
                (t.start_idx != 0 and t.end_idx != len(t.target_entry.doc) and \
                not (t.end_idx == len(t.target_entry.doc)-1 and \
                    t.target_cmd == 'question' and t.target_entry.doc[-1].text == '?'))
            if include_pattern:
                infos.append((start_idx, end_idx, pattern_func))
            if include_front:
                infos.append((0, end_idx, 'starts_with'))
            if include_end:
                end_idx, pattern_func = len(t.target_entry.doc), 'ends_with'
                if t.target_cmd == 'question' and t.target_entry.doc[-1].text == '?':
                    end_idx = len(t.target_entry.doc) - 1
                infos.append((start_idx, end_idx, pattern_func))
            for start_idx, end_idx, pattern_func in infos:
                spans = t.target_entry.doc[start_idx:end_idx]
                if len(spans) <= 3:
                    for feature_list in itertools.product(TAG_LISTS, repeat=len(spans)):
                        span_features = [ get_token_feature(t, feature_list[idx]) for idx, t in enumerate(spans) ]
                        if any([ f not in VBs +WHs + NNs and feature_list[idx] == 'tag' for idx, f in enumerate(span_features) ]):
                            continue
                        pattern = ' '.join(span_features)
                        if t.target in Instance.ling_perform_dict and \
                            pattern in Instance.ling_perform_dict[t.target] and \
                            Instance.model in Instance.ling_perform_dict[t.target][pattern]:
                            ling_features.append({
                                'cmd': self._wrap_cmd(f'{pattern_func}({t.target_cmd}, pattern="{pattern}")'),
                                'perform_meta': Instance.ling_perform_dict[t.target][pattern][Instance.model]
                            })
                if len(spans) > 3 or len(ling_features) == 0:
                    span_features = [ get_token_feature(t, 'lower') for idx, t in enumerate(spans) ]
                    pattern = ' '.join(span_features)
                    ling_features.append({
                        'cmd': self._wrap_cmd(f'{pattern_func}({t.target_cmd}, pattern="{pattern}")'),
                        'perform_meta': PatternCoverMeta(0, 0, 0)
                    })
        # with all valid data saved, sort and return top3
        ling_features = sorted(ling_features, 
            key=lambda k: (
                # higher error coverage than general coverage. This value: larger the better
                k['perform_meta'].err_cover - k['perform_meta'].cover, 
                # not too high or too low coverage. This value: smaller the better
                -1 * abs(k['perform_meta'].cover - 0.5),
                # higher in-group coverage. This value: larger the better
                k['perform_meta'].err_rate
            ), reverse=True )
        ling_features = ling_features[:3]
        ling_features = sorted(ling_features, key=lambda k: k['perform_meta'].cover)
        for l in ling_features:
            #if l['perform_meta'].cover < 0.001:
            #    continue
            self.set_suggest(self.get_cmd(l['cmd']), 'linguistic')

@BuildBlockDetector.register("vqa")
class BuildBlockDetectorVQA(BuildBlockDetector):
    def set_targets(self, target: str, start_idx: int, end_idx: int):
        self.targets = []
        predictor_names = [ p.model for p in self.instance.get_entry("predictions") ]
        if target == 'question':
            self.targets.append(
                TargetMeta(
                    target='question', 
                    target_cmd=f'question', 
                    target_entry=self.instance.get_entry("question"),
                    start_idx=start_idx, end_idx=end_idx
                )
            )
        elif 'groundtruth' in target:
            separate = target.split('::')
            groundtruths = self.instance.get_entry("groundtruths") or []
            if len(separate) == 2:
                groundtruths = [g for g in groundtruths if g.doc.text == separate[1] ]
            if groundtruths:
                self.targets.append(
                    TargetMeta(
                        target='groundtruths',
                        target_cmd=f'groundtruths', 
                        target_entry=groundtruths[0],
                        start_idx=start_idx, end_idx=end_idx)
                )
        elif target in predictor_names:
            predictions = self.instance.get_entry("predictions") or []
            selected_predictions = [ g for g in predictions if g.model == target ]
            if selected_predictions:
                self.targets.append(
                    TargetMeta(target='predictions', 
                        target_cmd=f'prediction(model="{target}")',
                        target_entry=selected_predictions[0],
                        start_idx=start_idx, end_idx=end_idx)
                )

    def _detect_from_question(self, start_idx: int, end_idx: int) -> None:
        question = self.instance.get_entry("question")
        if not question:
            logger.warn("No [ question ] to do detection.")
            return
        prediction = self.instance.get_entry('prediction')
        if prediction.get_perform() == 1:
            return
        doc = list(question.doc[start_idx : end_idx+1])
        if not doc:
            return
        if len(doc) > 5 or len(doc) == 0: 
            return 
        pred_cmd = f'prediction(model="{Instance.model}")'
        overlap_cmd_g = self._wrap_cmd(f'overlap(question, groundtruth, label="lemma")')
        overlap_cmd_p = self._wrap_cmd(f'overlap(question, {pred_cmd}, label="lemma")')
        overlap_g = Attribute('', '', overlap_cmd_g).test_one_instance(
            self.instance, Attribute.store_hash(), Group.store_hash())
        overlap_p = Attribute('', '', overlap_cmd_p).test_one_instance(
            self.instance, Attribute.store_hash(), Group.store_hash())
        if overlap_g and overlap_g > 0:
            self.set_suggest(f'{self.get_cmd(overlap_cmd_g)} > 0', 'filter')
        if overlap_p and overlap_p > 0:
            self.set_suggest(f'{self.get_cmd(overlap_cmd_p)} > 0', 'filter')

@BuildBlockDetector.register("qa")
class BuildBlockDetectorQA(BuildBlockDetector):
    def set_targets(self, target, start_idx, end_idx):
        self.targets = []
        if target == 'question':
            question = self.instance.get_entry("question")
            if not question:
                logger.warn("No [ question ] to do detection.")
                return
            self.targets.append(
                TargetMeta(
                    target='question', 
                    target_cmd=f'question',
                    target_entry=question,
                    start_idx=start_idx,
                    end_idx=end_idx
                )
            )
        else:
            predictions = self.instance.get_entry("predictions") or []
            selected_predictions = [ g for g in predictions \
                if not (g.span_start >= end_idx or g.span_end <= start_idx) ]
            selected_predictions = sorted(selected_predictions, key=lambda x: int(x.model == Instance.model), reverse=True)
            groundtruths = self.instance.get_entry("groundtruths") or []
            groundtruths = [g for g in groundtruths 
                if not (g.span_start >= end_idx or g.span_end <= start_idx) ]
            if selected_predictions:
                prediction = selected_predictions[0]
                offset_start = prediction.span_start - start_idx
                offset_start = offset_start if offset_start >= 0 else 0
                offset_end = end_idx - start_idx + offset_start
                offset_end = offset_end if offset_end <= prediction.span_end else prediction.span_end
                self.targets.append(
                    TargetMeta(
                        target='predictions', 
                        target_cmd=f'prediction(model="{prediction.model}")',
                        target_entry=prediction,
                        start_idx=offset_start,
                        end_idx=offset_end
                    )
                )
            if groundtruths:
                offset_start = groundtruths[0].span_start - start_idx
                offset_start = offset_start if offset_start >= 0 else 0
                offset_end = end_idx - start_idx + offset_start
                offset_end = offset_end if offset_end <= groundtruths[0].span_end else groundtruths[0].span_end
                self.targets.append(
                    TargetMeta(
                        target='groundtruths', 
                        target_cmd=f'groundtruths',
                        target_entry=groundtruths[0],
                        start_idx=offset_start,
                        end_idx=offset_end
                    )
                )
        print(self.targets)

    def _set_performace_info(self):
        # get the prediction for the default model
        prediction = self.instance.get_entry('prediction')
        if not prediction:
            return
        # check its correctness
        ## Exact match
        if prediction.get_perform() == 1:
            return 
        # partially correct
        pred_cmd = self._wrap_cmd(f'prediction(model="{Instance.model}")')
        sent_g_cmd = self._wrap_cmd(f'sentence(groundtruths)')
        sent_p_cmd = self._wrap_cmd(f'sentence({pred_cmd})')
        # get the precision and recall 
        for metric in ['precision', 'recall']:
            if prediction.get_perform(metric) == 1:
                other_metric = 'recall' if metric == 'precision' else 'precision'
                metrc_cmd = self.get_cmd(self._wrap_cmd(f'{metric}(model="{Instance.model}")'))
                other_cmd = self.get_cmd(self._wrap_cmd(f'{other_metric}(model="{Instance.model}")'))
                self.set_suggest(f'{metrc_cmd} == 1', 'perform')
                self.set_suggest(f'{other_cmd} < 1', 'perform')
        # get the offset span
        for direction in ['left', 'right']:
            other_dir = 'left' if direction == 'right' else 'right'
            dir_cmd = self._wrap_cmd(f'abs_num(answer_offset_delta({pred_cmd}, direction="{direction}"))')
            other_dir_cmd = self._wrap_cmd(f'answer_offset_delta({pred_cmd}, direction="{other_dir}")')
            dir_val = Attribute('', '', dir_cmd).test_one_instance(
                self.instance, Attribute.store_hash(), Group.store_hash())
            other_dir_val = Attribute('', '', other_dir_cmd).test_one_instance(
                self.instance, Attribute.store_hash(), Group.store_hash())
            if dir_val != None and other_dir_val != None and dir_val == 1 and other_dir_val == 0:
                dir_span_cmd = self._wrap_cmd(f'POS(answer_offset_span({pred_cmd}, direction="{direction}"))')
                dir_span_val = Attribute('', '', dir_span_cmd).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                self.set_suggest(f'{self.get_cmd(dir_cmd)} == {dir_val}', 'filter')
                self.set_suggest(f'{self.get_cmd(dir_span_cmd)} == {dir_span_val}', 'filter')
        # if totally not correct
        if prediction.get_perform('f1') == 0:
            cmd = self.get_cmd(self._wrap_cmd(f'f1(model="{Instance.model}")'))
            self.set_suggest(f'{cmd} == 0', 'perform')
            # not correct, but same sentence
            if prediction.get_perform('sent') == 1:
                overlap_cmd_g = self._wrap_cmd(f'overlap(question, {sent_g_cmd}, label="lemma")')
                overlap_g = Attribute('', '', overlap_cmd_g).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                self.set_suggest(f'{self.get_cmd(overlap_cmd_g)} > {overlap_g}', 'filter')
            # if not same sentence
            if prediction.get_perform('sent') == 0:
                self.set_suggest(f'is_correct_sent({pred_cmd}) == 0', 'perform')
                overlap_cmd_g = self._wrap_cmd(f'overlap(question, {sent_g_cmd}, label="lemma")')
                overlap_cmd_p = self._wrap_cmd(f'overlap(question, {sent_p_cmd}, label="lemma")')
                overlap_g = Attribute('', '', overlap_cmd_g).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                overlap_p = Attribute('', '', overlap_cmd_p).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                op = '>' if overlap_p > overlap_g else '<='
                self.set_suggest(
                    f'{self.get_cmd(overlap_cmd_p)} {op} {self.get_cmd(overlap_cmd_g)}', 'filter')
            
    def _detect_from_question(self, start_idx, end_idx):
        question = self.instance.get_entry("question")
        if not question:
            logger.warn("No [ question ] to do detection.")
            return
        prediction = self.instance.get_entry('prediction')
        doc = list(question.doc[start_idx : end_idx])
        if not doc:
            return
        if len(doc) > 5 or len(doc) == 0: 
            return 
        pred_cmd = self._wrap_cmd(f'prediction(model="{Instance.model}")')
        sent_g_cmd = self._wrap_cmd(f'sentence(groundtruths)')
        sent_p_cmd = self._wrap_cmd(f'sentence({pred_cmd})')
        get_token_patterns = []
        """
        # get the verb
        doc_verbs = np.unique([t.tag_ for t in doc if t.pos_ not in ['PUNCT', 'DET'] and t.tag_ in VBs and not t.is_stop])
        if len(doc_verbs) > 0:
            token_q = f'token(question, pattern="VERB")'
            overlap_cmd_g = f'overlap({token_q}, {sent_g_cmd}, label="lemma")'
            overlap_cmd_p = f'overlap({token_q}, {sent_p_cmd}, label="lemma")'
            get_token_patterns.append((overlap_cmd_g, overlap_cmd_p))
        # get the ent
        doc_ents = np.unique([t.ent_type_ for t in doc if t.ent_type_])
        if len(doc_ents) > 0:
            overlap_cmd_g = f'overlap(question, {sent_g_cmd}, label="ent")'
            overlap_cmd_p = f'overlap(question, {sent_p_cmd}, label="ent")'
            get_token_patterns.append((overlap_cmd_g, overlap_cmd_p))
        """
        for overlap_cmd_g, overlap_cmd_p in get_token_patterns:
            overlap_g = Attribute('', '', overlap_cmd_g).test_one_instance(
                self.instance, Attribute.store_hash(), Group.store_hash())
            op = '==' if overlap_g == 0 else '>'
            self.set_suggest(f'{self.get_cmd(overlap_cmd_g)} {op} 0', 'filter')
            if prediction and prediction.get_perform('sent') == 0:
                overlap_p = Attribute('', '', overlap_cmd_p).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                print(overlap_p)
                op = '==' if overlap_p == 0 else '>'
                self.set_suggest(f'{self.get_cmd(overlap_cmd_p)} {op} 0', 'filter')
        # if no specific overlaps
        if True: #not get_token_patterns:
            overlap_cmd_g = self._wrap_cmd(f'overlap(question, {sent_g_cmd}, label="lemma")')
            overlap_cmd_p = self._wrap_cmd(f'overlap(question, {sent_p_cmd}, label="lemma")')
            overlap_g = Attribute('', '', overlap_cmd_g).test_one_instance(
                self.instance, Attribute.store_hash(), Group.store_hash())
            op = '>=' if overlap_g > 0.5 else '<='
            self.set_suggest(f'{self.get_cmd(overlap_cmd_g)} {op} {int(overlap_g * 10) / 10}', 'filter')
            if prediction.get_perform('sent') == 0:
                overlap_p = Attribute('', '', overlap_cmd_p).test_one_instance(
                    self.instance, Attribute.store_hash(), Group.store_hash())
                op = '>=' if overlap_p > 0.5 else '<='
                self.set_suggest(f'{self.get_cmd(overlap_cmd_p)} {op} {int(overlap_p * 10) / 10}', 'filter')

        # check whether the entities are in the sentence

        