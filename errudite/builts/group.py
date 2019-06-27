import logging
import altair as alt
import pandas as pd
import os
import random
from typing import Dict, List, Union
import datetime
import itertools
from .built_block import BuiltBlock
from ..targets.instance import Instance
from ..targets.interfaces import InstanceKey
from ..utils import DSLValueError, ConfigurationError, load_json, CACHE_FOLDERS, normalize_file_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

class Group(BuiltBlock):
    """
    A class that helps group instances that share similar attributes 
    together, through filters created through the DSL.
    """
    def __init__(self, name: str, description: str, cmd: str):
        BuiltBlock.__init__(self, name, description, cmd)
        try:
            self.set_cmd(cmd, 'group')
        except Exception as e:
            raise(e)
    
    def test_one_instance(self,
        instance_group: Union[Instance, Dict[str, Instance]],
        attr_hash: Dict[str, 'Attribute']=None, 
        group_hash: Dict[str, 'Group']=None) -> bool:
        """Test and see if an instance belongs to the group.
        
        Parameters
        ----------
        instance_group : Union[Instance, Dict[str, Instance]]
            Each instance group saves all versions of a given instance, 
            as ``{ instance.rid : instance }``.
            If the input is just one instance, we will automatically 
            transfer it into a group.
        attr_hash : Dict[str, Attribute], optional
            The hash store of the Group objects -- ``{ attr.name: attr }``, 
            by default None. This is for resolving ``attr:attr_name`` in DSL.
        group_hash : Dict[str, Group], optional
            The hash store of the Group objects -- ``{ group.name: group }``, 
            by default None. This is for resolving ``group:group_name`` in DSL.

        Returns
        -------
        bool
            Whether or not the testing instance is in the group.
        """
        if not instance_group:
            return False
        if isinstance(instance_group, Instance):
            instance_group = { instance_group.rid : instance_group }
        exist_key = self.get_existing_instance_key(instance_group, self.instance_dict)
        if exist_key:
            return True
        data = self.bbw.test_instances(
            [instance_group], attr_hash=attr_hash, group_hash=group_hash)
        return self.get_existing_instance_key(instance_group, data) is not None
    
    def print_stats(self, instances: List[Instance], time_t):
        # print the info
        instance_hash = { i.key(): i for i in  instances }
        TOTAL_SIZE = len(instances)
        ERROR_SIZE = len([ i for i in instances if i.is_incorrect() ])
        info_seralized = self.serialize(instance_hash, instance_hash)
        output = f"NAME\t: {self.name}\n" + \
            "COVER\t: {} ({:.2%})\n".format(len(self.instance_dict), len(self.instance_dict) / TOTAL_SIZE) + \
            "ERROR\t: {} ({:.2%} of total, {:.2%} of slice, {:.2%} of errors)\n".format(
                info_seralized['counts']['incorrect'], 
                info_seralized['counts']['incorrect'] / TOTAL_SIZE, 
                info_seralized['counts']['incorrect'] / len(self.instance_dict) if self.instance_dict else 0, 
                info_seralized['counts']['incorrect'] / ERROR_SIZE) + \
            "Time\t: {:.2}s\n".format((datetime.datetime.utcnow() - time_t).total_seconds())
        print('---' * 33)
        print(self.bbw.operator)
        print(output)
        # get one example:
        if self.instance_dict:
            print(instance_hash[self.get_instance_list()[0]])

    def set_instances(self, 
        cmd: str, 
        instance_groups: List[Union[Instance, Dict[str, Instance]]],
        attr_hash: Dict[str, 'Attribute']=None, 
        group_hash: Dict[str, 'Group']=None) -> None:
        """
        Test the filter on a list of instances, and save the ones that 
        belong to the group to ``self.instance_dict``: Dict[InstanceKey, True].
        
        Parameters
        ----------
        cmd : Union[str, Callable]
            The command that extracts attributes from instances / 
            filter instances to form groups.
            If it's a string, it's parsed by the DSL to actual functions.
            If the input is a function already, it's directly called 
            to get the attribute.
        instance_groups : List[Union[Instance, Dict[str, Instance]]]
            A list of instance_group -- Each instance group saves all versions
            of a given instance, as ``{ instance.rid : instance }``
        attr_hash : Dict[str, Attribute], optional
            The hash store of the Group objects -- ``{ attr.name: attr }``, 
            by default None. This is for resolving ``attr:attr_name`` in DSL.
        group_hash : Dict[str, Group], optional
            The hash store of the Group objects -- ``{ group.name: group }``, 
            by default None. This is for resolving ``group:group_name`` in DSL.
        
        Returns
        -------
        None
        """
        self.test_size = len(instance_groups)
        if cmd and cmd != self.cmd:
            self.set_cmd(cmd, 'group')
        if cmd:
            time_t = datetime.datetime.utcnow()
            self.instance_dict = self.bbw.test_instances(
                instance_groups, 
                attr_hash=attr_hash, group_hash=group_hash)
        else:
            # only save the unedited instance
            self.instance_dict = { }
            for group in instance_groups:
                instances = [i for i in group.values() if i.vid == 0]
                if instances:
                    self.instance_dict[instances[0].key()] = True
        #self.print_stats(instances, time_t)

    def get_instance_list(self) -> List[InstanceKey]:
        """Get the list of keys for the instances that 
        are in the group.
        
        Returns
        -------
        List[InstanceKey]
            The instance key list.
        """
        return list(self.instance_dict.keys())
    
    def show_instances(self,
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        filtered_instances: List[InstanceKey]=None) -> None:
        """Print the instances that are in the group.
        
        Parameters
        ----------
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash_rewritten``.
        filtered_instances : List[InstanceKey], optional
            A selected list of instances. If given, only display the distribution
            of the selected instances, by default None
        
        Returns
        -------
        None
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        
        if not filtered_instances:
            filtered_instances = self.get_instances()
        else:
            qids = { key.qid: True for key in filtered_instances }
            filtered_instances = {key for key in self.get_instances() if key.qid in qids }
        for key in filtered_instances:
            instance = Instance.get(key, instance_hash, instance_hash_rewritten)
            instance.show_instance()

    def __repr__(self):
        """
        Override the print func by displaying the name, cmd, and count.
        """
        return f'[{self.__class__.__name__}]({self.name}): \n' + \
            f'\tCMD\t: {self.cmd}\n' + \
            f'\tCOUNT\t: {len(self.instance_dict)}\n'
    
    def serialize(self, 
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        filtered_instances: List[InstanceKey]=None,
        model: str=None) -> Dict:
        """Seralize the instance into a json format, for sending over
        to the frontend.
        
        Returns
        -------
        Dict[str, Any]
            The serialized version.
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten

        if not filtered_instances:
            filtered_instances = self.get_instances()
        else:
            qids = { key.qid: True for key in filtered_instances }
            filtered_instances = {key for key in self.get_instances() if key.qid in qids }
        stats = Group.eval_stats(
            filtered_instances,
            instance_hash, instance_hash_rewritten, model)
        return {
            'name': self.name,
            'cmd': self.cmd,
            'description': self.description,
            'counts': stats['counts'],
            'stats': stats['stats']
        }
    
    def visualize_models(self, 
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        filtered_instances: List[InstanceKey]=None,
        models: List[str]=[]):
        """
        Visualize the group distribution. 
        It's a one-bar histogram that displays the count of instances in the group, and
        the proportion of incorrect predictions.
        Because of the incorrect prediction proportion, this historgram is different
        for each different model. 
        
        Parameters
        ----------
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash_rewritten``.
        filtered_instances : List[InstanceKey], optional
            A selected list of instances. If given, only display the distribution
            of the selected instances, by default None
        models : List[str], optional
            A list of instances, with the bars for each group concated vertically.
            By default []. If [], resolve to ``[ Instance.model ]``.
        
        Returns
        -------
        alt.Chart
            An altair chart object. 
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        models = models or [ Instance.resolve_default_model(None) ]
        output = []
        for model in models:
            #Instance.set_default_model(model=model)
            data = self.serialize(instance_hash, instance_hash_rewritten, filtered_instances, model)
            for correctness, count in data["counts"].items():
                output.append({
                    "correctness": correctness,
                    "count": count,
                    "model": model
                })
        
        df = pd.DataFrame(output)
        chart = alt.Chart(df).mark_bar().encode(
            y=alt.Y('model:N'),
            x=alt.X('count:Q', stack="zero"),
            color=alt.Color('correctness:N', scale=alt.Scale(domain=["correct", "incorrect"])),
            tooltip=['model:N', 'count:Q', 'correctness:N']
        ).properties(width=100)#.configure_facet(spacing=5)#
        return chart
    """
    @classmethod
    def get_ungrouped_keys(
        cls, total_keys: List[InstanceKey], 
        groups: Dict[str, 'Group']) -> List[str]:
        key_set = set(total_keys)
        for g in groups.values():
            key_set -= set(g.qids)
        return list(key_set)
    """
    
    @classmethod
    def eval_stats(cls, 
        filtered_instances: List[InstanceKey],
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        model: str=None) -> dict:
        """
        Evaluate the instance correctness for the given filtering instance.
        If it's for a group, could do ``filtered_instances=group.get_instance_list()``
        
        Parameters
        ----------
        filtered_instances : List[InstanceKey]
            A selected list of instances.
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash_rewritten``.
        model : str, optional
            A selected model to test correctness, by default ``None``. 
            If ``None``, resolve to ``Instance.model``.
        
        Returns
        -------
        dict

            .. code-block:: js

                {
                    'counts': {
                        'correct': The number of correct predictions in filtered_instances,
                        'incorrect': The number of incorrect predictions in filtered_instances,
                    },
                    'stats': {
                        'coverage': (count_correct + count_incorrect) / TOTAL_SIZE,
                        'error_coverage': The ratio of how many incorrect instances are covered.
                        'local_error_rate': The ratio of incorrect instances within filtered_instances.
                        'global_error_rate': count_incorrect / TOTAL_SIZE
                    }
                }
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        
        if type(filtered_instances) == list:
            filtered_instances = { key: True for key in filtered_instances }
        if not filtered_instances:
            filtered_instances = {}
        if all([ i.vid == 0 for i in filtered_instances ]):
            TOTAL_SIZE = len(instance_hash)
            ERROR_INSTANCES = { i.key(): True for i in instance_hash.values() if i.is_incorrect(model) }
        else:
            TOTAL_SIZE = len(instance_hash_rewritten)
            ERROR_INSTANCES = { i.key(): True for i in instance_hash_rewritten.values() if i.is_incorrect(model) }
        count_correct = len([key for key in filtered_instances if not key in ERROR_INSTANCES])
        count_incorrect = len([key for key in filtered_instances if key in ERROR_INSTANCES])
        return {
            'counts': {
                'correct': count_correct,
                'incorrect': count_incorrect
            },
            'stats': {
                'coverage': (count_correct + count_incorrect) / TOTAL_SIZE,
                'error_coverage': count_incorrect / len(ERROR_INSTANCES) if ERROR_INSTANCES else 0,
                'local_error_rate': count_incorrect / len(filtered_instances) if filtered_instances else 0,
                'global_error_rate': count_incorrect / TOTAL_SIZE
            }
        }
    
    @classmethod
    def eval_slice_model_compare(cls, 
        models: List[str],
        filtered_instances: List[InstanceKey],
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={}) \
        -> List[Dict[str, Union[str, float]]]:
        """
        Given two models, compute the "confusion matrix".
        
        Parameters
        ----------
        models : List[str]
            Two models are compared.
        filtered_instances : List[InstanceKey]
            A selected list of instances.
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default {}. 
            It denotes by the corresponding instance keys.
            If ``{}``, resolve to ``Instance.instance_hash_rewritten``.
        
        Returns
        -------
        List[Dict[str, Union[str, float]]]

            .. code-block:: js
            
                [{
                    'model_a': model_a,
                    'model_b': model_b, 
                    'perform_a': 'correct'|'incorrect',
                    'perform_b': 'correct'|'incorrect',
                    'count': The number of instances that have the matching performance.
                }]
        """
        def test_include(is_incorrect, correct_str):
            should_be_incorrect = correct_str == 'incorrect'
            return (is_incorrect and should_be_incorrect) or \
                (not is_incorrect and not should_be_incorrect)
        def get_instance_by_key(key: InstanceKey) -> Instance:
            if not key:
                return None
            if key.vid == 0 and key in instance_hash:
                return instance_hash[key]
            if key.vid != 0 and key in instance_hash_rewritten:
                return instance_hash_rewritten[key]
            return None
        
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        
        if filtered_instances == None:
            filtered_instances = instance_hash.keys()
        models = models[:2]
        if len(models) != 2:
            return []
        model_performs, err_overlaps = {}, []
        model_a, model_b = models[0], models[1]
        for model in models:
            model_performs[model] = { }
            for key in filtered_instances:
                instance = get_instance_by_key(key)
                if not instance:
                    continue
                model_performs[model][key] = instance.is_incorrect(model=model)

        for a, b in itertools.product (['correct', 'incorrect'], repeat=2):
            filtered_instances_ = [
                key for key in filtered_instances \
                if test_include(model_performs[model_a][key], a) and \
                     test_include(model_performs[model_b][key], b)
            ]
            err_overlaps.append({
                'model_a': model_a,
                'model_b': model_b, 
                'perform_a': a,
                'perform_b': b,
                'count': len(filtered_instances_)
            })
        return err_overlaps

    @classmethod
    def create_from_json(cls, raw: Dict[str, str]) -> 'Group':
        """
        Recreate the group from its seralized raw json.
        
        Parameters
        ----------
        raw : Dict[str, str]
            The json version definition of the group, with 
            name, cmd, and description in a dict.

        Returns
        -------
        Group
            The re-created group.
        """
        return Group(raw['name'], raw['description'], raw['cmd'])

    @staticmethod 
    def create(
        name: str, 
        description: str, 
        cmd: str,
        qid_hash: Dict[str, List[InstanceKey]]={},
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        save: bool=True,
        test_size: int=None,
        attr_hash: Dict[str, 'Group']={},
        group_hash: Dict[str, 'Group']={},
        force_recompute: bool=False,
        sample_list: List[InstanceKey]=None) -> 'Group':

        """
        Create a group object, and filter instances to form the group.
        The satisfying ones are saved to ``attr.instance_dict.``
        
        Parameters
        ----------
        name : str
            The group name.
        description : str
            The description of the group.
        cmd : Union[str, Callable]
            The command that filter instances to form groups.
            If it's a string, it's parsed by the DSL to actual functions.
            If the input is a function already, it's directly called 
            to get the attribute.
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash_rewritten``.
        qid_hash : Dict[str, List[InstanceKey]]
            A dict that denotes wraps different versions of instance keys.
            If ``None``, resolve to ``Instance.qid_hash``.
        save : bool, optional
            Whether to save it to the store hash. By default True.
        test_size : int, optional
            If set to a number, only get a small testing sample of the output. 
            By default None, which will test the group filtering on all instances.
        attr_hash : Dict[str, Attribute], optional
            The hash store of the Group objects -- ``{ attr.name: attr }``, 
            by default {}. This is for resolving ``attr:attr_name`` in DSL.
        group_hash : Dict[str, Group], optional
            The hash store of the Group objects -- ``{ group.name: group }``, 
            by default {}. This is for resolving ``group:group_name`` in DSL.

        force_recompute : bool, optional
            If a group already exist, whether to reset the group
            and recompute & filter instances. By default False.
        sample_list : List[InstanceKey], optional
            Run the group filtering on a predefined instance key list. 
            By default None.
        
        Returns
        -------
        Group
            The created group.
        """

        qid_hash = qid_hash or Instance.qid_hash
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        try:
            group = Group(name, description, cmd=cmd)
            # see if there is an existing group
            recompute_instance = True
            if not sample_list:
                sample_list_ = list(instance_hash.keys())
            elif type(sample_list) == dict:
                sample_list_ = list(sample_list.keys())
            else:
                sample_list_ = sample_list
            if not test_size:
                test_size = len(instance_hash)
            if not force_recompute and not sample_list_:
                for g in group_hash.values():
                    if g.bbw.operator == group.bbw.operator and g.test_size >= test_size:
                        logger.info('Found an existing group: ' + g.cmd)
                        group.instance_dict = g.instance_dict
                        recompute_instance = False
                        break
            if recompute_instance:
                if len(sample_list_) > test_size:
                    sample_list_ = random.sample(sample_list_, test_size)
                instance_groups = [
                    Instance.create_instance_dict_given_qid(
                        key.qid, qid_hash, instance_hash, instance_hash_rewritten)
                    for key in sample_list_ ]
                group.set_instances(
                    cmd=cmd, 
                    instance_groups=instance_groups,
                    attr_hash=attr_hash, group_hash=group_hash)
            if save:
                Group.save(group)
            logger.info(f'Created group: {name}')
            return group
        except:
            raise