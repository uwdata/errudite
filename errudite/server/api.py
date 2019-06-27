import logging
import random
import numpy as np
from tqdm import tqdm
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from collections import defaultdict
from typing import List, Dict
from ..targets.interfaces import InstanceKey
from ..utils import Registrable, Store, ConfigurationError, convert_list, set_cache_folder
from ..io import DatasetReader
from ..targets.instance import Instance
from ..targets.label import Label
from ..predictors.predictor import Predictor
from ..builts import BuiltBlock, Attribute, Group
from ..build_blocks.build_block_detector import BuildBlockDetector
from ..build_blocks.prim_funcs import perform, truncate

from ..rewrites import Rewrite
from ..rewrites import SemanticRule, SemanticRuleDetector

from ..targets.qa import QAAnswer, Question, Context
from ..targets.vqa import VQAAnswer, VQAQuestion
from ..processor import spacy_annotator



class API(Registrable):
    def __init__(self, 
        cache_path: str,
        model_metas: List[dict],
        attr_file_name: str, 
        group_file_name: str, 
        rewrite_file_name: str, 
        task: str):
        # set necessary info.
        self.task = task
        # save the last rewritten instances so they can be retrieved and really saved..
        self.prev_tried_rewrite_examples = {}
        # instances
        try:
            logger.info(f'{self.task}: Finding cache folder and loading instances...')
            # first, get the dataset reader
            self.dr = DatasetReader(cache_path)
            self.dr.load_preprocessed()
            logger.info(f'DONE loading instances: {len(Instance.qid_hash)} in total')
            logger.info(f'Loading models...')     
            self.predictors = self.load_predictors(model_metas)
            self.set_anchor_predictor(None, True)
            logger.info(f'DONE loading models: {list(self.predictors.keys())}')
            logger.info('Loading default attributes...')
            self.load_attrs(attr_file_name)
            logger.info('Loading default groups...')
            self.load_groups(group_file_name)
            logger.info('Loading the rewrite rules...')
            self.load_rewrites(rewrite_file_name)
            logger.info('Init sample cache...')
            self.sample_cache_idx = -1
            self.sampled_instances = []
            logger.info('Init the build block detectors...')
            self.bbd = BuildBlockDetector.by_name(task)()
            logger.info('Init the semantic rule detectors...')
            self.rd = SemanticRuleDetector()
            logger.info('Initialization finished.')
        except Exception as e:
            raise(e)
    
    def load_predictors(self, model_metas: List[dict]):
        predictors = {}
        try:
            for meta in tqdm(model_metas):
                try:
                    predictor = Predictor.create_from_json(meta)
                    predictors[predictor.name] = predictor
                    Instance.set_default_model(predictor.name)
                    predictor.evaluate_performance(list(Instance.instance_hash.values()))
                except Exception as e:
                    logger.error(e)
            return predictors
        except Exception as e:
            raise(e)
    
    def load_attrs(self, attr_file_name: str):
        try:
            Attribute.import_from_file(attr_file_name)
        except Exception as e:
            logger.warn(e)
            from ..builts.task_defaults import QA_ATTRS, VQA_ATTRS
            attr_hash = QA_ATTRS if self.task == 'qa' else VQA_ATTRS
            for attr in attr_hash.values():
                Attribute.save(attr)
        instance_groups = Instance.create_instance_dicts()
        for a in tqdm(Attribute.values()):
            # on init, do not allow cross reference between attrs and groups
            a.set_instances(a.cmd, instance_groups, attr_hash=Attribute.store_hash())
            
    def load_groups(self, group_file_name: str):
        try:
            Group.import_from_file(group_file_name)
        except Exception as e:
            logger.error(e)
            from ..builts.task_defaults import QA_GROUPS, VQA_GROUPS
            group_hash = QA_GROUPS if self.task == 'qa' else VQA_GROUPS
            for group in group_hash.values():
                Group.save(group)
        instance_groups = Instance.create_instance_dicts()
        for a in tqdm(Group.values()):
            # on init, do not allow cross reference between attrs and groups
            a.set_instances(a.cmd, instance_groups, 
                attr_hash=Attribute.store_hash(), 
                group_hash=Group.store_hash())
    
    def load_rewrites(self, rewrite_file_name: str):
        try:
            Rewrite.import_from_file(rewrite_file_name)
        except Exception as e:
            logger.error(e)
            from ..rewrites.task_defaults import QA_REWRITES, VQA_REWRITES
            rewrite_hash = QA_REWRITES if self.task == 'qa' else VQA_REWRITES
            for rewrite in rewrite_hash.values():
                Rewrite.save(rewrite)
        for rewrite in tqdm(Rewrite.values()):
            pass
            #self.rewrite_instances_by_rid(rewrite.rid, None, sample_size=100, save=True)
    
    def set_anchor_predictor(self, model: str, is_global_update: bool=True) -> str:
        """Only taking 1e-5s"""
        model = Instance.resolve_default_model(model)
        if not getattr(self, "compare_predictor", None) or (model and model != Instance.model):
            Instance.set_default_model(model)
            if is_global_update:
                self.set_compare_predictor()
                self.recompute_attr_on_select_switch("model")
        else:
            logger.warn(f"Already chosen the model {model}.")
        return model
    def get_anchor_predictor(self) -> str:
        return Instance.resolve_default_model()

    def set_compare_predictor(self, model: str=None):
        predictors = [ m for m in getattr(self, 'predictors', []) \
            if m != self.get_anchor_predictor() ]
        model = Instance.resolve_default_model(model)
        if model and model in predictors:
            self.compare_predictor = model
        else:
            self.compare_predictor = predictors[0] if predictors else ''

    def get_compare_predictor(self) -> str:
        return self.compare_predictor
    def set_selected_rewrite(self, rid: str, is_global_update: bool=True) -> str:
        rid = Instance.resolve_default_rewrite(rid)
        if rid and rid != Instance.resolve_default_rewrite():
            Instance.set_default_rewrite(rid)
            if is_global_update:
                self.recompute_attr_on_select_switch("rewrite")
        return rid
    def get_selected_rewrite(self) -> str:
        return Instance.resolve_default_rewrite()
    
    def recompute_attr_on_select_switch(self, switched: str) -> None:
        if switched not in [ 'model', 'rewrite' ]:
            logger.warn(f"The switch type does not exist: {switched}. Skip the rest.")
            return
        # if we have attrs
        switched_names = []
        for attr in Attribute.values():
            if attr.should_recompute(switched):
                switched_names.append(attr.name)
                Attribute.create(
                    name=attr.name, description=attr.description,
                    cmd=attr.cmd,
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    save=True, force_recompute=True)
        for group in Group.values():
            if group.should_recompute(switched):
                switched_names.append(group.name)
                Group.create(
                    name=group.name, description=group.description, 
                    cmd=group.cmd, 
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    save=True, force_recompute=True)
        logger.info(f"Recomputed attrs: {switched_names}.")
    
    def _get_filterered_instances(self, 
        filter_cmd: str, 
        sample_rewrite: str=None,
        use_sampled_data: Dict[str, bool]=None,
        test_size: int=None):
        try:
            filtered_instances = None
            if Rewrite.exists(sample_rewrite):
                rewrite = Rewrite.get(sample_rewrite)
                rewrite_keys = rewrite.get_instances()
            else:  
                rewrite_keys = None
            if use_sampled_data:
                filtered_instances = self.sampled_instances
                if rewrite_keys:
                    rewrite_qids = { key.qid: True for key in rewrite_keys }
                    filtered_instances = { key: True for key in filtered_instances if key.qid in rewrite_qids  }
            else:
                filter_cmd = filter_cmd if filter_cmd else ''    
                temp_group = Group.create(
                    name="temp", description="", 
                    cmd=filter_cmd, 
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    save=False,
                    test_size=test_size,
                    sample_list=rewrite_keys)
                filtered_instances = temp_group.get_instances()
            return filtered_instances
        except:
            raise

    def create_rewrite(self, 
        from_cmd: str, to_cmd: str, target_cmd: str, save: bool=True) -> Attribute:
        try: 
            rewrite = Rewrite.create_with_cmd(
                save=False,
                from_cmd=from_cmd, 
                to_cmd=to_cmd,
                target_cmd=target_cmd)
            if Rewrite.exists(rewrite.rid):
                return Rewrite.get(rewrite.rid)
            if save:
                Rewrite.save(rewrite)
            return rewrite
        except:
            raise
    
    def delete_built(self, name: str, built_type: str) -> bool:
        if built_type == 'attr':
            return Attribute.remove_saved(name)
        elif built_type == 'rewrite':
            return Rewrite.remove_saved(name)
        elif built_type == 'group':
            return Group.remove_saved(name)
        return False

    def delete_selected_rules(self, rids: List[str]) -> None:
        for rid in rids:
            self.delete_built(rid, 'rewrite')
        return True

    def export_built(self, file_name: str, built_type: str) -> bool:
        if built_type == 'attr':
            return Attribute.export_to_file(file_name)
        elif built_type == 'rewrite':
            return Rewrite.export_to_file(file_name)
        elif built_type == 'group':
            return Group.export_to_file(file_name)
        return False

    def get_attr_distribution(self, 
        attr_names: List[str], 
        filter_cmd: str, 
        use_sampled_data: bool=False,
        test_size: int=None,
        include_rewrite: str=None,
        include_model: str=None):
        # set the selected rewrite
        if include_rewrite:
            selected_rewrite = Instance.resolve_default_rewrite(include_rewrite)
            # self.get_selected_rewrite() if include_rewrite else None
        else:
            selected_rewrite = None
        prev_model = self.get_anchor_predictor()
        prev_rewrite = self.get_selected_rewrite()
        self.set_anchor_predictor(include_model, False)
        self.set_selected_rewrite(include_rewrite, False)
        switched_model = "model" if include_model and include_model != prev_model else None
        switched_rewrite = "rewrite" if include_rewrite and include_rewrite != prev_rewrite else None
        filtered_instances = self._get_filterered_instances(
            sample_rewrite=selected_rewrite,
            filter_cmd=filter_cmd, 
            use_sampled_data=use_sampled_data, 
            test_size=test_size)
        if attr_names == None:
            attr_names = list(Attribute.keys())
        output = []
        for aname in attr_names:
            if not Attribute.exists(aname):
                logger.warn(f"Attr name {aname} does not exist.")
                continue
            attr = Attribute.get(aname)
            if attr.should_recompute(switched_model) or attr.should_recompute(switched_rewrite):
                attr = Attribute.create(
                    name=attr.name, 
                    description=attr.description,
                    cmd=attr.cmd,
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    save=False,
                    sample_list=filtered_instances,
                    force_recompute=True)
            attrs = [ attr ]
            # only do the recompute for attrs that do not already have rewrite
            if "apply" not in attr.cmd and "rewrite" not in attr.cmd and \
                Rewrite.exists(selected_rewrite):
                attr_rewritten = Attribute.create(
                    name=attr.name + "_on_rewritten", 
                    description=attr.description, 
                    cmd=f'(apply({attr.cmd}, rewrite="SELECTED"))',
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    sample_list=filtered_instances, #self.rewrite_hash[selected_rewrite].get_instances(),
                    save=False, test_size=test_size)
                attrs.append(attr_rewritten)
            for attr in attrs:
                output.append(attr.serialize (
                    model=include_model,
                    filtered_instances=filtered_instances,
                    instance_hash=Instance.instance_hash,
                    instance_hash_rewritten=Instance.instance_hash_rewritten)
                )
        self.set_anchor_predictor(prev_model, False)
        self.set_selected_rewrite(prev_rewrite, False)
        return output
    
    def get_built_distribution (self,
        built_type: str,
        built_names: List[str], 
        filter_cmd: str='',
        use_sampled_data: bool=False,
        include_model: str=None,
        test_size: int=None):
        prev_model = self.get_anchor_predictor()
        switched = "model" if include_model and include_model != prev_model else None
        self.set_anchor_predictor(include_model, False)
        filtered_instances = self._get_filterered_instances(
            filter_cmd=filter_cmd, 
            use_sampled_data=use_sampled_data,
            test_size=test_size)
        output = []
        if built_type == "group":
            if built_names == None:
                built_names = list(Group.keys())
            hashes = Group.store_hash()
        else:
            if built_names == None:
                built_names = list(Rewrite.keys())
            hashes = Rewrite.store_hash()
        for mname in built_names:
            meta = hashes[mname]
            if built_type == "group" and hashes[mname].should_recompute(switched):
                meta = Group.create(
                    name=meta.name, description=meta.description, 
                    cmd=meta.cmd, 
                    group_hash=Group.store_hash(),
                    attr_hash=Attribute.store_hash(),
                    force_recompute=True, save=False)
            output.append(meta.serialize (model=include_model, filtered_instances=filtered_instances)
            )
        self.set_anchor_predictor(prev_model, False)
        return output
    
    def get_err_overlap(self, 
        show_filtered_err_overlap: bool=True, 
        compare_predictor: str=None) -> Dict:
        if compare_predictor:
            self.set_compare_predictor(compare_predictor)
        return Group.eval_slice_model_compare(
            models=[self.get_anchor_predictor(), self.get_compare_predictor()], 
            filtered_instances=self.sampled_instances if show_filtered_err_overlap else None)

    def get_one_attr_of_instances(self, attr_name: str, instance_keys: List[InstanceKey]) -> List[any]: 
        output = []
        if Attribute.exists(attr_name):
            attr = Attribute.get(attr_name)
            for key in instance_keys:
                instance = Instance.get(key)
                if not instance:
                    logger.warn(f"Instance does not exist: {key}")
                    output.append(None)
                else:
                    output.append(attr.test_one_instance(instance))
            return output
        else:
            logger.error(f"[ get_one_attr_of_instances ]: {attr_name} does not exist.")
        return None

    def get_groups_of_instances(self, instance_keys: List[InstanceKey]) -> List[any]: 
        output = []
        for group in Group.values():
            for key in instance_keys:
                instance = Instance.get(key)
                if instance and group.test_one_instance(instance):
                    output.append(group.name)
                    break
        return output
    
    def get_rewrites_of_instances(self, instance_keys: List[InstanceKey]) -> List[any]: 
        output = []
        for rewrite in Rewrite.values():
            for key in instance_keys:
                if rewrite.retrive_instance_key(key.qid):
                    output.append(rewrite.rid)
                    break
        return output

    def rewrite_instances_by_rid(
        self, rid: str, qids: List[str]=None, sample_size: int=10, 
        save: bool=False) -> List:
        try:
            if not rid in self.prev_tried_rewrite_examples: # reset the raw save
                self.prev_tried_rewrite_examples = { rid: defaultdict(lambda: None) }
            output = []
            qids = qids or list(Instance.qid_hash.keys())
            if not Rewrite.exists(rid):
                raise(ConfigurationError(f"[ rewrite_instances_by_rid ]: {rid} does not exist."))
            rewrite = Rewrite.get(rid)
            for idx, qid in enumerate(qids):
                ori_key = InstanceKey(qid=qid, vid=0)
                if not Instance.exists(ori_key):
                    raise(ConfigurationError(f"[ rewrite_instances_by_rid ]: {ori_key} does not exist."))
                if qid in self.prev_tried_rewrite_examples[rid]:
                    o = self.prev_tried_rewrite_examples[rid][qid]
                else:
                    ori_i = Instance.get(ori_key)
                    rewritten_key = rewrite.retrive_instance_key(qid)
                    if Instance.exists(rewritten_key):
                        rewrite_i = Instance.get(rewritten_key)
                        rewrite_i_serialized = rewrite_i.serialize()
                    else:
                        rewritten_output = rewrite.rewrite_one_instance(ori_i)
                        if not rewritten_output:
                            #logger.warn(f"{rewrite.rid} cannot rewrite {ori_i}.")
                            continue
                        q_rewrite = rewritten_output.text if rewrite.target == 'question' \
                            else ori_i.get_entry('question').doc.text
                        g_rewrites = [ rewritten_output.text ] if rewrite.target == 'groundtruth' else \
                            [ g.doc.text for g in ori_i.get_entry('groundtruths') ]
                        if self.task == 'qa':
                            c_rewrite = rewritten_output.text \
                                if rewrite.target == 'context' \
                                else ori_i.get_entry('context').doc.text                        
                        else:
                            c_rewrite = ori_i.get_entry('question').img_id if ori_i.get_entry('question') else ''
                        if save: # officially save it.
                            rewrite_output = self.predict_formalize(qid, rid, q_rewrite, g_rewrites, c_rewrite)
                            if not rewrite_output:
                                logger.warn(f"{rewrite.rid} cannot rewrite {qid}.")
                                continue
                            rewritten_key = InstanceKey(qid=rewrite_output['key']['qid'], vid=rewrite_output['key']['vid'])
                            if not rewrite_output or not Instance.exists(rewritten_key):
                                logger.warn(f"{rewrite.rid} cannot rewrite {qid}.")
                                continue
                            rewrite_i = Instance.get(rewritten_key)
                            rewrite_i_serialized = rewrite_i.serialize()
                        else:
                            predicted = self.predict_on_manual_rewrite (q_rewrite, g_rewrites, c_rewrite)
                            if not predicted:
                                continue
                            rewrite_i_serialized = {
                                'key': { 'qid': qid },
                                'question': q_rewrite, 
                                'groundtruths': g_rewrites, 
                                'context': c_rewrite, 
                                'prediction': predicted['prediction'],
                                'perform': predicted['perform']
                            }
                    o = {
                        'qid': qid, 
                        'ori_instance': ori_i.serialize(),
                        'rewrite_instance': rewrite_i_serialized
                    }
                output.append(o)
                self.prev_tried_rewrite_examples[rid][qid] = o
                bucket_size = max([sample_size, 100])
                if len(output) >= sample_size or idx > bucket_size:
                    break
            return output[:20]
        except:
            raise

    def formalize_prev_tried_rewrites(self, rid: str):
        if rid not in self.prev_tried_rewrite_examples or not Rewrite.exists(rid):
            logger.warn(f"{rid} does not exist.")
            return
        rewrite = Rewrite.get(rid)
        for p in self.prev_tried_rewrite_examples[rid].values():
            e = p['rewrite_instance']
            qid, q_rewrite, g_rewrites = p['qid'], e['question'], e['groundtruths']
            c_rewrite = e['context'] if 'context' in e else None
            rewritten_key = rewrite.retrive_instance_key(qid)
            if rewritten_key and Instance.exists(rewritten_key):
                logger.warn(f"{rewritten_key} already exist.")
                continue
            self.predict_formalize(qid, rid, q_rewrite, g_rewrites, c_rewrite)
        self.prev_tried_rewrite_examples = {} # reset
        return True #self.evaluate_rewrites_on_groups(rid, list(self.group_hash.keys()))

    def rewrite_group_instances(self, 
        rid: str, group_name: str, 
        sample_size: int=100, 
        instance_correctness: str='all', 
        save: bool=False):
        try:
            if not Rewrite.exists(rid) or not Group.exists(group_name):
                raise(ConfigurationError(f"[ rewrite_group_instances ]: {rid} or {group_name} doesn't exist."))
            def get_instance_correctness(key):
                if instance_correctness == 'all':
                    return True
                else:
                    instance = Instance.get(key)
                    if instance:
                        incorrect = instance.is_incorrect()
                        return incorrect if instance_correctness == 'incorrect' else not incorrect
                    return False
            g = Group.get(group_name)
            qids = list(set([key.qid for key in \
                g.get_instance_list() if get_instance_correctness(key) ]))
            output = self.rewrite_instances_by_rid(rid, qids, sample_size, save=False)
            output = sorted(output,
                key=lambda o: (
                    abs(int(o['ori_instance']['perform'] == 1) - int(o['rewrite_instance']['perform'] == 1)),
                    int(o['ori_instance']['prediction'] != o['rewrite_instance']['prediction'])),
                reverse=True)
            return output
        except:
            raise
    
    def evaluate_tried_rewrites(self, rids: List[str], gnames: List[str]):
        rids, gnames = convert_list(rids), convert_list(gnames)
        output = []
        for g in gnames:
            if not Group.exists(g):
                logger.warn(f"{g} does not exist.")
                continue
            group = Group.get(g)
            for rid in rids:
                if not Rewrite.exists(rid):
                    logger.warn(f"{rid} does not exist.")
                    continue
                rule = Rewrite.get(rid)
                qids = {}
                for key in group.get_instances():
                    if key.qid not in qids:
                        qids[key.qid] = True
                counts = Rewrite.count_flips(
                    Rewrite.get_delta_performance(rule, qids)['delta_f1s'])
                output.append({ 'rid': rid, 'group': g, 'counts': counts })
        return output

    def evaluate_rewrites_on_groups(self, rids: List[str], gnames: List[str], on_tried: bool=False):
        rids, gnames = convert_list(rids), convert_list(gnames)
        print(rids, gnames)
        output = []
        for g in gnames:
            if not Group.exists(g):
                logger.warn(f"{g} does not exist.")
                continue
            group = Group.get(g)
            for rid in rids:
                if not Rewrite.exists(rid):
                    logger.warn(f"{rid} does not exist.")
                    continue
                rule = Rewrite.get(rid)
                if on_tried and rid in self.prev_tried_rewrite_examples:
                    delta_performance = []
                    for key in group.get_instances():
                        if key.qid in self.prev_tried_rewrite_examples[rid]:
                            o = self.prev_tried_rewrite_examples[rid][key.qid]
                            delta_performance.append(
                                int(o['rewrite_instance']['perform'] == 1) - 
                                int(o['ori_instance']['perform'] == 1)
                            )
                elif len(rule.get_instances()) > 0:
                    qids = { key.qid for key in group.get_instances() }
                    delta_performance = Rewrite.get_delta_performance(rule, qids)['delta_f1s']
                else:
                    delta_performance = []
                counts = Rewrite.count_flips(delta_performance)
                print(counts)
                output.append({
                    'rid': rid,
                    'group': g,
                    'counts': counts
                })
        print(output)
        return output


    def detect_build_blocks(self, target, qid, vid, start_idx, end_idx):
        self.bbd.on_select(target, qid, vid, start_idx, end_idx)
        return self.bbd.suggestions

    def detect_rule_from_rewrite(self, adoc, bdoc, target_cmd):
        adoc = spacy_annotator.process_text(adoc) if type(adoc) == str else adoc
        bdoc = spacy_annotator.process_text(bdoc) if type(bdoc) == str else bdoc
        rules = self.rd.detect_rule_wrapper(
            adoc=adoc, 
            bdoc=bdoc, 
            instances=list(Instance.instance_hash.values()),
            target_cmd=target_cmd,
            sample_size=100)
        for r in self.rd.rules:
            Rewrite.save(self.rd.rules[r])
        self.rd.rules = {}
        return rules

    def predict_on_manual_rewrite (self, 
        q_rewrite: str, 
        groundtruths: List[str], c_rewrite: str=None) -> Dict:
        # use c_rewrite to be the img_id
        """Generate predictions on manual rewrites. Do not generate any version
        or run any processing; Just give the prediction, and evaluate the result.
        
        Arguments:
            q_rewrite {str} -- question text
            groundtruths {List[str]} -- the groundtruth text
        
        Returns:
            Dict -- [description]
        """
        #if True:
        predictor = self.predictors[Instance.model]
        if not predictor:
            return None
        prediction = predictor.predict(q_rewrite, c_rewrite)
        if not prediction:
            return None
        perform = Label.task_evaluator(prediction['text'], groundtruths)[Label.task_primary_metric]
        return { 'prediction': prediction['text'], 'perform': perform }
    def predict_formalize(self, qid: str, rid: str, q_rewrite: str, groundtruths: List[str], c_rewrite: str=None):
        raise NotImplementedError

    def get_serialized_instance_with_qids(self, qids: List[str]):
        questions, contexts, answers, sampled_keys = {}, {}, {}, []
        for qid in qids:
            instances = [ Instance.get(key) for key in Instance.qid_hash[qid] ]
            sampled_keys += [ i.get_all_keys() for i in instances ]
            #sampled_keys += [ i.get_all_keys() for i in instances ]
            for instance in instances:
                question = instance.get_entry('question')
                if question and question.key() not in questions:
                    questions[question.key()] = question
                if self.task == 'qa':
                    context = instance.get_entry('context')
                    if context and context.key() not in contexts:
                        contexts[context.key()] = context
                groundtruths = instance.get_entry('groundtruths')
                if groundtruths:
                    for g in groundtruths:
                        if g and g.key() not in answers:
                            answers[g.key()] = g
                predictions = instance.get_entry('predictions')
                if predictions:
                    for g in predictions:
                        if g and g.key() not in answers:
                            answers[g.key()] = g
        return {
            'sampled_keys': sampled_keys,
            'questions': list(questions.values()),
            'contexts': list(contexts.values()),
            'answers': list(answers.values())
        }

    def get_more_samples(self, direction: int=1, sample_size: int=10):
        try:
            if direction == -1 and self.sample_cache_idx <= 0:
                raise(ConfigurationError("Already reached the beginning of the sample!"))
            elif direction == 1 and self.sample_cache_idx >= len(self.sampled_instances)-1:
                raise(ConfigurationError("Already reached the end of the sample!"))
            move_to_idx = truncate(
                direction * sample_size + self.sample_cache_idx,
                min_value=0, max_value=len(self.sampled_instances))
            from_idx, to_idx = move_to_idx, move_to_idx + sample_size
            keys = self.sampled_instances[from_idx:to_idx]
            qids = []
            for key in keys:
                if key.qid not in qids:
                    qids.append(key.qid)
                    if len(qids) == sample_size:
                        break
            serialized = self.get_serialized_instance_with_qids(qids)
            self.sample_cache_idx = move_to_idx
            return {
                'sample_cache_idx': self.sample_cache_idx,
                'sampled_keys': serialized['sampled_keys'],
                'questions': serialized['questions'],
                'contexts': serialized['contexts'],
                'answers': serialized['answers']
            }
        except:
            raise


    def sample_instances(self,
        selected_predictor: str=None, 
        cmd: str='',
        sample_method: str='rand', 
        sample_rewrite: str=None, 
        sample_size: int=10,
        test_size: int=None,
        show_filtered_arr: bool=False, 
        show_filtered_err_overlap: bool=False,
        show_filtered_group: bool=False,
        show_filtered_rewrite: bool=False,
        qids_input: List[str]=[]):
        """Sample instances based on certain sampling criteria
        
        Arguments:
            cmd {str} -- the cmd str
            selected_predictor {str} -- a selected predictor
            sample_method {str} -- random, best, worst by the selected model
            sample_rewrite {str} -- the rewriteing to sample
        
        Keyword Arguments:
            sample_size {int} -- how many instances to return (default: {10})
        
        Returns:
            [Dict] -- information
        """
        prev_rewrite = self.get_selected_rewrite()
        self.set_selected_rewrite(sample_rewrite, False)
        sample_rewrite = Instance.resolve_default_rewrite(sample_rewrite)
        selected_predictor = Instance.resolve_default_model(selected_predictor)
        # get the same space
        try:
            # compute the filter
            # the cmd overwrites all the other semantic filters
            if qids_input:
                qids = { q: True for q in qids_input }
                keys = { key: True for key in Instance.instance_hash if key.qid in qids }
            else:
                keys = self._get_filterered_instances(
                    filter_cmd=cmd, 
                    sample_rewrite=sample_rewrite,
                    use_sampled_data=False,
                    test_size=test_size)
                # get the rewritten instances for a selected rewrite method
                # with the ori version in the sample space (e.g., group)  
            self.sampled_instances = list(keys)
            self.sample_cache_idx = 0
            if sample_rewrite and Rewrite.exists(sample_rewrite):
                # first, reset the rewrite
                stats = Rewrite.eval_stats(
                    Rewrite.get(sample_rewrite),
                    [k.qid for k in keys],
                    model=selected_predictor if selected_predictor else self.get_anchor_predictor()
                )
            else:
                stats = Group.eval_stats(keys)
            # compute the attr distribution
            attrs = None if not show_filtered_arr else \
                self.get_attr_distribution(
                    None, cmd, use_sampled_data=True,
                    test_size=test_size, include_rewrite=sample_rewrite)
            # get the error overlap
            err_overlaps = None if not show_filtered_err_overlap else \
                self.get_err_overlap()
            # get the group distribution
            groups = None if not show_filtered_group else \
                self.get_built_distribution("group", None, 
                cmd, use_sampled_data=True, test_size=test_size) 
            # get the group distribution
            rewrites = None if not show_filtered_rewrite else \
                self.get_built_distribution("rewrite", None, 
                cmd, use_sampled_data=True, test_size=test_size) 
            # get the instances for display
            if not qids_input:
                if sample_method == 'rand':
                    
                    if len(keys) > sample_size:
                        keys = random.sample(list(keys.keys()), sample_size)
                elif selected_predictor and selected_predictor in self.predictors:
                    if sample_rewrite and Rewrite.exists(sample_rewrite):
                        rewrite = Rewrite.get(sample_rewrite)
                        if sample_method in ['correct_flip', 'incorrect_flip']:
                            isflip = 1 if sample_method == 'correct_flip' else -1
                            delta_f1s = defaultdict(int)
                            for key in keys:
                                ori_key = InstanceKey(qid=key.qid, vid=0)
                                edi_key = rewrite.retrive_instance_key(key.qid)
                                if Instance.exists(edi_key) and Instance.exists(ori_key):
                                    ori_i = Instance.get(ori_key)
                                    rewrite_i = Instance.get(edi_key)
                                    delta_f1s[key] = \
                                        int(rewrite_i.get_perform(selected_predictor) == 1) - \
                                        int(ori_i.get_perform(selected_predictor) == 1)
                            keys = sorted(list(keys.keys()), 
                                key=lambda key: isflip * delta_f1s[key], reverse=True )
                        else:
                            ischange = 1 if sample_method == 'changed' else -1
                            changed_predictions = defaultdict(int)
                            for key in keys:
                                ori_key = InstanceKey(qid=key.qid, vid=0)
                                edi_key = rewrite.retrive_instance_key(key.qid)
                                if Instance.exists(edi_key) and Instance.exists(ori_key):
                                    ori_i = Instance.get(ori_key)
                                    rewrite_i = Instance.get(edi_key)
                                    ori_p = ori_i.get_entry('prediction', selected_predictor)
                                    rewrite_p = rewrite_i.get_entry('prediction', selected_predictor)
                                    if ori_p and rewrite_p:
                                        changed_predictions[key] = int(ori_p.doc.text != rewrite_p.doc.text)
                            keys = sorted(list(keys.keys()), 
                                key=lambda key: ischange * changed_predictions[key], reverse=True )
                    else:
                        is_best = 1 if sample_method == 'best' else -1
                        is_border = -1 if sample_method == 'borderline' else 1
                        keys = sorted(list(keys.keys()), key=lambda key: (
                            is_best * Instance.get(key).get_perform(selected_predictor, Label.task_primary_metric), 
                            is_border * Instance.get(key).get_perform(selected_predictor, "confidence")
                        ), reverse=True)
                # save the sampled keys, and re-init the cache idx
                qids = []
                for key in keys:
                    if key.qid not in qids:
                        qids.append(key.qid)
                        if len(qids) == sample_size:
                            break
            serialized = self.get_serialized_instance_with_qids(qids)
            self.set_selected_rewrite(prev_rewrite, False)
            return {
                'sample_cache_idx': self.sample_cache_idx,
                'sampled_keys': serialized['sampled_keys'],
                'info': stats,
                'questions': serialized['questions'],
                'contexts': serialized['contexts'],
                'answers': serialized['answers'],
                'attrs': attrs,
                'groups': groups,
                'rewrites': rewrites,
                'err_overlaps': err_overlaps
            }
        except Exception as e:
            raise(e)


@API.register("qa")
class APIQA(API):
    def __init__(self, 
        cache_path: str,
        model_metas: List[dict],
        attr_file_name: str, 
        group_file_name: str, 
        rewrite_file_name: str):
        super().__init__(
            cache_path, 
            model_metas, 
            attr_file_name, group_file_name, rewrite_file_name, 'qa')

    def predict_formalize(self, 
        qid: str,
        rid: str,
        q_rewrite: str, 
        groundtruths: List[str],
        c_rewrite: str):
        ori_key = InstanceKey(qid=qid, vid=0)
        if not Instance.exists(ori_key):
            logger.warn(f"{ori_key} does not exist.")
            return None
        i_ori = Instance.get(ori_key)
        q_ori, p_ori = i_ori.get_entry('question'), i_ori.get_entry('context')
        if not q_ori or not p_ori:
            return None
        qrewritten, prewritten = q_ori.doc.text != q_rewrite, p_ori.doc.text != c_rewrite
        # get groundtruths
        g_texts = [ g.doc.text for g in i_ori.get_entry('groundtruths') ]
        if prewritten or not groundtruths or all([g in g_texts for g in groundtruths]):
            grewritten = False
        else:
            grewritten = True
        if not qrewritten and not prewritten:
            return None
        vid = len(Instance.qid_hash[qid])
        #vid = max(versions) + 1 if versions else 1
        question = Question(qid=i_ori.qid, text=q_rewrite, vid=vid) if qrewritten else q_ori
        context = Context(aid=i_ori.aid, cid=i_ori.cid, text=c_rewrite, vid=vid, qid=i_ori.qid) \
            if prewritten else p_ori
        # get groundtruths
        if not grewritten:
            groundtruths = i_ori.get_entry('groundtruths')
        else:
            groundtruths = [ 
                QAAnswer(model='groundtruth', qid=question.qid, text=g, vid=vid) for g in groundtruths ]
            for g in groundtruths:
                g.add_attributes(context=context, predicted=None, 
                groundtruths=None, char_start=None, span_start=None)
        # run the prediction
        predictions = []
        for predictor in self.predictors.values():
            predicted = Predictor.by_name("qa_task_class").model_predict(predictor, question, context, groundtruths)
            if predicted:
                predictions.append(predicted)
        instance = Instance(qid, vid, rid, additional_keys={"aid":context.aid, "cid":context.cid})
        instance.set_entries(
            question=question, context=context, 
            groundtruths=groundtruths, predictions=predictions)
        # save the rewrite
        if not Rewrite.exists(rid):
            Rewrite.save(Rewrite(rid, "manual", ""))
        rewrite = Rewrite.get(rid)
        rewrite.add_instance(instance.key())
        Instance.save(instance)
        return {
            'key': instance.get_all_keys(),
            'question': instance.get_entry('question') if qrewritten else None,
            'context': instance.get_entry('context') if prewritten else None,
            'groundtruths': instance.get_entry('groundtruths') if grewritten else None,
            'predictions': instance.get_entry('predictions')
        }


@API.register("vqa")
class APIVQA(API):
    def __init__(self, 
        cache_path: str,
        model_metas: List[dict],
        attr_file_name: str, 
        group_file_name: str, 
        rewrite_file_name: str):
        super().__init__(
            cache_path, 
            model_metas, 
            attr_file_name, group_file_name, rewrite_file_name, 'vqa')

    def predict_formalize(self, 
        qid: str,
        rid: str,
        q_rewrite: str, 
        groundtruths: List[str],
        c_rewrite: str=None):
        ori_key = InstanceKey(qid=qid, vid=0)
        if not Instance.exists(ori_key):
            logger.warn(f"{ori_key} does not exist.")
            return None
        i_ori = Instance.get(ori_key)
        q_ori = i_ori.get_entry('question')
        g_texts = sum([ [g.doc.text] * g.count for g in i_ori.get_entry('groundtruths') ], [])
        if not groundtruths or all([g in g_texts for g in groundtruths]):
            grewritten = False
        else:
            grewritten = True
        if (not q_ori or q_ori.doc.text == q_rewrite) and not grewritten: 
            return None
        vid = len(Instance.qid_hash[qid])
        question = VQAQuestion(qid=i_ori.qid,text=q_rewrite, 
            vid=vid, img_id = q_ori.img_id, 
            question_type=q_ori.question_type)
        # get groundtruths
        g_texts = [ g.doc.text for g in i_ori.get_entry('groundtruths') ]
        # get groundtruths
        g_texts = [ g.doc.text for g in i_ori.get_entry('groundtruths') ]
        if not groundtruths or all([g in g_texts for g in groundtruths]):
            grewritten = False
            groundtruths = i_ori.get_entry('groundtruths')
        else:
            grewritten = True
            c = Counter(groundtruths)
            groundtruths = [
                VQAAnswer(
                    model='groundtruth', 
                    answer_type=None,
                    qid=qid, 
                    count=count,
                    text=ans_text, 
                    vid=vid)
                for ans_text, count in c.most_common()
            ]
        # run the prediction
        predictions = []
        for predictor in self.predictors.values():
            predicted = Predictor.by_name("vqa_task_class").model_predict(predictor, question, groundtruths)
            if predicted:
                predictions.append(predicted)
        instance = Instance(qid, vid, rid)
        instance.set_entries(question=question, groundtruths=groundtruths, predictions=predictions)
        # save the rewrite
        if not Rewrite.exists(rid):
            Rewrite.save(Rewrite(rid, "manual", ""))
        rewrite = Rewrite.get(rid)
        rewrite.add_instance(instance.key())
        Instance.save(instance)
        return {
            'key': instance.get_all_keys(),
            'question': instance.get_entry('question'),
            'context': None,
            'groundtruths': instance.get_entry('groundtruths') if grewritten else None,
            'predictions': instance.get_entry('predictions')
        }