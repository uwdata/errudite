import math
import numbers
import os
import numpy as np
import datetime
import random
import altair as alt
import pandas as pd

from typing import Dict, List, Tuple, Callable, Union, TypeVar
from collections import defaultdict
from itertools import groupby
from .built_block import BuiltBlock
from ..targets.instance import Instance
from ..targets.interfaces import InstanceKey, UNREWRITTEN_RID
from ..utils import DSLValueError, ConfigurationError, load_json, CACHE_FOLDERS, normalize_file_path

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

T = TypeVar('T')

class Attribute(BuiltBlock):
    """
    A class that helps define complex attributes of instances, and allow users 
    to test their distributions.

    Attributes
    ----------
    dtype : str
        The data type, which is "continuous" or "categorical".
    """
    def __init__(self, name: str, description: str, cmd: Union[str, Callable]):
        BuiltBlock.__init__(self, name, description, cmd)
        try:
            self.set_cmd(cmd, 'attr')
        except Exception as e:
            raise(e)
        self.dtype = ''

    def _transfer_data_group(self, 
        instance_group: Instance, include_fake_val: bool=True) -> Dict[str, Instance]:
        """
        Transfer instance to instance group.
        
        Parameters
        ----------
        instance_group : Union[Instance, Dict[str, Instance]],
            If it's already an instance group, do nothing. Otherwise, transfer it to 
            instance group.
        include_fake_val : bool, optional
            By default True. If true, pretend the rewritten instance is also an
            unrewritten instance, so to extract the attribute.
        
        Returns
        -------
        Dict[str, Instance]
            The instance group.
        """
        if isinstance(instance_group, Instance):
            if include_fake_val and instance_group.rid != UNREWRITTEN_RID:
                instance_group = { instance_group.rid : instance_group, UNREWRITTEN_RID : instance_group  }
            else:
                instance_group = { instance_group.rid : instance_group  }
        return instance_group
    
    def test_one_instance(self, 
        instance_group: Union[Instance, Dict[str, Instance]],
        attr_hash: Dict[str, 'Attribute']=None, 
        group_hash: Dict[str, 'Group']=None, 
        include_fake_val: bool=True) -> T:
        """Test and get the attribute of one instance.
        
        Parameters
        ----------
        instance_group : Union[Instance, Dict[str, Instance]]
            Each instance group saves all versions of a given instance, 
            as: 

            .. code-block:: js

                { instance.rid : instance }
            
            If the input is just one instance, we will automatically 
            transfer it into a group.
        attr_hash : Dict[str, Attribute], optional
            The hash store of the Group objects -- ``{ attr.name: attr }``, 
            by default None. This is for resolving ``attr:attr_name`` in DSL.
        group_hash : Dict[str, Group], optional
            The hash store of the Group objects -- ``{ group.name: group }``, 
            by default None. This is for resolving ``group:group_name`` in DSL.
        include_fake_val : bool, optional
            If ``instance_group`` is inputted as an Instance and it is rewritten, 
            with ``include_fake_val == True``, we will run the attribute 
            extraction on the rewritten instance, even when the attribute is 
            only defined for unrewritten instances. By default True
        
        Returns
        -------
        T
            The attribute of the instance. If the instance does not have the 
            attribute, return None.
        """
        if not instance_group:
            return None
        instance_group = self._transfer_data_group(instance_group, include_fake_val)
        #print(instance_group)
        exist_key = self.get_existing_instance_key(instance_group, self.instance_dict)
        if exist_key:
            return self.instance_dict[exist_key]
        data = self.bbw.test_instances(
            [instance_group], 
            attr_hash=attr_hash, 
            group_hash=group_hash)
        #print(data)
        exist_key = self.get_existing_instance_key(instance_group, data)
        if  not exist_key:
            return None
        return data[exist_key]

    def set_instances(self, 
        cmd: Union[str, Callable],
        instance_groups: List[Union[Instance, Dict[str, Instance]]],
        attr_hash: Dict[str, 'Attribute']=None, 
        group_hash: Dict[str, 'Group']=None) -> None:
        """
        Compute the instances' corresponding attributes, and 
        save them to ``self.instance_dict``: ``Dict[InstanceKey, Union[int, float, str]]``
        
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
        time_t = datetime.datetime.utcnow()
        if cmd and cmd != self.cmd:
            self.set_cmd(cmd, 'attr')
        self.instance_dict = self.bbw.test_instances(
            instance_groups, attr_hash=attr_hash, group_hash=group_hash)
        should_delete = [
            key for key in self.instance_dict.keys() if self.instance_dict[key] == None]
        for key in should_delete:
            del self.instance_dict[key]
        # self.print_stats(instances, time_t)
    
    def __repr__(self):
        """
        Override the print func by displaying the name, cmd, and count.
        """
        return f'[{self.__class__.__name__}]({self.name}): \n' + \
            f'\tCMD\t: {self.cmd}\n' + \
            f'\tCOUNT\t: {len(self.instance_dict)}\n' + \
            f'\tDOMAIN\t: {self.domain()}\n'
    
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
        if filtered_instances:
            filtered_instances = { key.qid: True for key in filtered_instances }            
        def track_key(keys):
            corrects, incorrects = defaultdict(int), defaultdict(int)
            for key in keys:
                instance = Instance.get(key, instance_hash, instance_hash_rewritten)
                if instance:
                    if instance.is_incorrect(model):
                        if type(self.instance_dict[key]) == list:
                            continue
                        incorrects[self.instance_dict[key]] += 1
                    else:
                        if type(self.instance_dict[key]) == list:
                            continue
                        corrects[self.instance_dict[key]] += 1
            return corrects, incorrects
        if filtered_instances != None:
            corrects, incorrects = track_key({key: True for key in self.instance_dict if key.qid in filtered_instances})
        else:
            corrects, incorrects = track_key(self.instance_dict)
        return {
            'name': self.name,
            'description': self.description,
            'cmd': self.cmd,
            'domain': self.domain(filtered_instances),
            'dtype': self.dtype,
            'counts': { 'correct': list(corrects.items()), 'incorrect': list(incorrects.items()) }
        }

    def domain(self, filtered_instances: List[InstanceKey]=[]) -> List[T]:
        """Compute the domain of the attribute.
        
        Parameters
        ----------
        filtered_instances : List[InstanceKey], optional
            If the filtered instances is input, then only compute the domain
            for the filtered instances. By default []
        
        Returns
        -------
        List[Union[str, int, float]]
            The domain. If this is a categorical attribute, the domain list is 
            all the unique values of the attributes. If it's continuous, then 
            it's [min_value, max_value]
        """
        if not self.instance_dict:
            return []
        if type(filtered_instances) == list:
            filtered_instances = { f: True for f in filtered_instances }
        total_values = {}
        for v in self.instance_dict.items():
            if v[1] != None and type(v[1]) != list and (not filtered_instances or v[0].qid in filtered_instances):
                total_values[v[1]] = True
        if not total_values:
            return []
        total_values = list(total_values.keys())
        if isinstance(total_values[0], numbers.Number):
            self.dtype = 'continuous'
            return [float(min(total_values)), float(max(total_values))]
        else:
            self.dtype = 'categorical'
            return sorted(total_values)

    def print_stats(self, instances: List[Instance], time_t) -> None:
        # print the info
        TOTAL_SIZE = len(instances)
        output = f"NAME\t: {self.name}\n" + \
            "COVER\t: {} ({:.2%})\n".format(len(self.instance_dict), len(self.instance_dict) / TOTAL_SIZE) + \
            "Type\t: {} \n".format(self.dtype) + \
            "DOMAIN\t: {} \n".format(self.domain()) + \
            "Time\t: {:.2}s\n".format((datetime.datetime.utcnow() - time_t).total_seconds())
        print('---' * 33)
        print(self.bbw.operator)
        print(output)

    def visualize_per_model(self, 
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        filtered_instances: List[InstanceKey]=None,
        model: str=None,
        normalize: bool=False):
        """
        Visualize the attribute distribution. 
        The visualization is a histogram that displays the relative frequency 
        of different attribute values, as well as the proportion of incorrect predictions.
        Because of the incorrect prediction proportion, this historgram is different
        for each different model.

        If categorical, each value is a bar. Otherwise, the domain is automatically binned,
        and each bin is a bar.
        
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
        model : str, optional
            The selected model, by default ``None``. 
            If ``None``, resolve to ``Instance.model``.
        normalize : bool, optional
            If normalize, just highlight the incorrect proportion, not the frequency
            of different values, by default False
        
        Returns
        -------
        alt.Chart
            An altair chart object. 
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        model = Instance.resolve_default_model(model)
        data = self.serialize(
            instance_hash, instance_hash_rewritten, filtered_instances, model)
        is_discrete = self.dtype == "categorical"
        sorted_list = None
        if is_discrete:
            sorted_dict = defaultdict(int)
            for correctness in data["counts"]:
                for value, count in data["counts"][correctness]:
                    sorted_dict[value] += count
            sorted_list = sorted(list(sorted_dict), key=lambda x: sorted_dict[x], reverse=True)
        dtype = 'Q' if not is_discrete else 'N'
        bin = alt.Bin(maxbins=10, extent=data["domain"]) if not is_discrete else None
        compute_domain = []
        stack = "normalize" if normalize else "zero"
        for correctness in data["counts"]:
            for value, count in data["counts"][correctness]:
                if sorted_list and sorted_list.index(value) >= 15:
                    continue
                compute_domain.append({self.name: value, "count": count, "correctness": correctness})
        df = pd.DataFrame(compute_domain)
        chart = alt.Chart(df).mark_bar().encode(
            y=alt.Y('count:Q', stack=stack),
            x=alt.X(f'{self.name}:{dtype}', bin=bin),
            color=alt.Color('correctness:N', scale=alt.Scale(domain=["correct", "incorrect"])),
            tooltip=[f'{self.name}:{dtype}', 'count:Q', 'correctness:N']
        ).properties(height=100, title=f'{self.name} on {model}')#.configure_facet(spacing=5)#
        return chart
    
    def visualize_models(self, 
        models: List[str],
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        filtered_instances: List[InstanceKey]=None,
        normalize: bool=False):
        """
        Visualize the attribute distribution for ALL the ``models``. 
        This function calls ``self.visualize_per_model`` and concate the 
        charts returned for each model.
        """
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten
        charts = [ self.visualize_per_model(
            instance_hash=instance_hash,
            instance_hash_rewritten=instance_hash_rewritten,
            model=model,
            filtered_instances=filtered_instances,
            normalize=normalize
        ) for model in models ]
        return alt.vconcat(*charts).resolve_scale(x="shared", y="shared", color="shared")

    def is_outlier(self, value: T, filtered_instances: List[InstanceKey]=[]) -> bool:
        """
        Test whether an instance is an outlier. For continous values, test if it's 
        within the quartile_range. If categorical, see if the count of that value 
        is < 5% of all instance.
        
        Parameters
        ----------
        value : T
            The value to be tested.
        filtered_instances : List[InstanceKey], optional
            A selected list of instances. If given, only test outliers within
            the selected instances, by default None
        
        
        Returns
        -------
        bool
            Whether the value is an outlier.
        """
        if not self.instance_dict or value == None:
            return False
        total_items = [v for v in list(self.instance_dict.items()) if \
            v[1] != None and \
            not filtered_instances or v[0] in filtered_instances]
        total_values = [v[1] for v in total_items]
        if isinstance(total_values[0], numbers.Number):
            q1, q3 = np.percentile(total_values, 25), np.percentile(total_values, 75)
            iqr = q3 - q1
            quartile_range = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
            return bool(value <= quartile_range[0] or value >= quartile_range[1])
        else:
            groups = groupby(sorted(total_values, key=lambda x: x), key=lambda x: x)
            groups = [(key, len(list(val))) for key, val in groups]
            groups = sorted(groups, key=lambda g: g[1], reverse=True)
            for key, val in groups:
                if key == value and val < len(total_values) * 0.05:
                    return True
            return False

    def outliers(self, filtered_instances: List[InstanceKey]=[]) -> List[T]:
        """Get all the outlier values.
        
        Parameters
        ----------
        filtered_instances : List[InstanceKey], optional
            A selected list of instances. If given, only test outliers within
            the selected instances, by default None
        
        Returns
        -------
        List[T]
            The outlier values.
        """
        if not self.instance_dict:
            return []
        total_items = [v for v in list(self.instance_dict.items()) if \
            v[1] != None and \
            not filtered_instances or v[0] in filtered_instances]
        total_values = [v[1] for v in total_items]
        if isinstance(total_values[0], numbers.Number):
            q1, q3 = np.percentile(total_values, 25), np.percentile(total_values, 75)
            iqr = q3 - q1
            quartile_range = [q1 - 1.5 * iqr, q3 + 1.5 * iqr]
            return [
                key for key, value in total_items if 
                bool(value <= quartile_range[0] or value >= quartile_range[1])
            ]
        else:
            groups = groupby(sorted(total_items, key=lambda x: x[1]), key=lambda x: x[1])
            groups = [(key, list(val)) for key, val in groups]
            groups = sorted(groups, key=lambda g: len(g[1]), reverse=True)
            outliers = []
            for _, val in groups:
                if len(val) < len(total_values) * 0.05:
                    outliers += [ v[0] for v in val ]
            return outliers


    def discretize (self) -> List[T]:
        """
        A postprocessing process to bin the continuous data into categorical.
        If it's categorical already, just return the values as-is.

        Returns
        -------
        List[T]
            The discretized version.
        """
        if not self.instance_dict:
            return []
        total_items = [v for v in list(self.instance_dict.items()) if v[1] != None]
        total_values = [v[1] for v in total_items]
        discretized = {}
        if isinstance(total_values[0], numbers.Number):
            # bin
            bin_number = 5
            '''
            # TODO: decide if we are doing quitile or equal size bin????
            min_v, max_v = min(total_values), max(total_values)
            if self.name == 'sentence_length' and min_v > 0:
                bin_edges = np.logspace(np.log10(min_v), np.log10(max_v), num=bin_number+1)
            else:
                bin_edges = np.linspace(min_v, max_v, num=bin_number+1)
            '''
            bin_edges = [np.percentile(total_values, p) for p in range(0, 101, round(100/bin_number))]
            
            # floor the ones that have enough information.
            if total_values[-1] > bin_number:
                bin_edges = [math.floor(b) for b in bin_edges]
            bin_idxes = np.digitize(total_values, bin_edges, right=False)

            for idx, value in enumerate(total_values):
                right_idx = bin_idxes[idx]
                left_idx = right_idx - 1 if right_idx > 0 else 0
                right_idx = right_idx - 1 if right_idx >= len(bin_edges) else right_idx
                left = '{:.2f}'.format(bin_edges[left_idx]).rstrip('0').rstrip('.')
                right = '{:.2f}'.format(bin_edges[right_idx]).rstrip('0').rstrip('.')
                discretized[total_items[idx][0]] = '[{0},{1})'.format(left, right)
        else:
            groups = groupby(sorted(total_items, key=lambda x: x[1]), key=lambda x: x[1])
            groups = [(key, list(val)) for key, val in groups]
            groups = sorted(groups, key=lambda g: len(g[1]), reverse=True)
            # top 10 keys are then keeped. All the others should be changed to "other"
            for _, val in groups[10:]:
                for key, value in val:
                    discretized[value[0]] = 'other'
            for _, val in groups[:10]:
                for key, value in val:
                    discretized[value[0]] = value[1]
        return discretized

    @classmethod
    def create_from_json(cls, raw: Dict[str, str]) -> 'Attribute':
        """
        Recreate the object from its seralized raw json.
        
        Parameters
        ----------
        raw : Dict[str, str]
            The json version definition of the built block, with 
            name, cmd, and description in a dict.

        Returns
        -------
        Attribute
            The re-created attribute.
        """
        return Attribute(
            raw['name'] if "name" in raw else None, 
            raw['description'] if "description" in raw else None, 
            raw['cmd'] if "cmd" in raw else None)

    @staticmethod 
    def create(
        name: str, 
        description: str, 
        cmd: Union[str, Callable],
        qid_hash: Dict[str, List[InstanceKey]]={},
        instance_hash: Dict[InstanceKey, Instance]={},
        instance_hash_rewritten: Dict[InstanceKey, Instance]={},
        save: bool=True,
        test_size: int=None,
        attr_hash: Dict[str, 'Group']={},
        group_hash: Dict[str, 'Group']={},
        force_recompute: bool=False,
        sample_list: List[InstanceKey]=None) -> 'Attribute':
        """
        Create an attribute object, and extract the actual attribute
        values from instances, and save them to ``attr.instance_dict.``
        
        Parameters
        ----------
        name : str
            The attribute name.
        description : str
            The description of the attribute.
        cmd : Union[str, Callable]
            The command that extracts attributes from instances.
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
            By default None, which will test all instances to get and save
            their attributes.
        attr_hash : Dict[str, Attribute], optional
            The hash store of the Group objects -- ``{ attr.name: attr }``, 
            by default {}. This is for resolving ``attr:attr_name`` in DSL.
        group_hash : Dict[str, Group], optional
            The hash store of the Group objects -- ``{ group.name: group }``, 
            by default {}. This is for resolving ``group:group_name`` in DSL.

        force_recompute : bool, optional
            If an attribute already exist, whether to reset the attribute
            and recompute & save instances. By default False.
        sample_list : List[InstanceKey], optional
            Run the attribute extraction on a predefined instance key list. 
            By default None.
        
        Returns
        -------
        Attribute
            The created attribute.
        """

        qid_hash = qid_hash or Instance.qid_hash
        instance_hash = instance_hash or Instance.instance_hash
        instance_hash_rewritten = instance_hash_rewritten or Instance.instance_hash_rewritten

        recompute_instance = True
        if not cmd:
                raise(ConfigurationError("No cmd given to attribute creation."))
        attr = Attribute(name, description, cmd=cmd)
        # see if there is an existing group
        if not sample_list:
            sample_list_ = list(instance_hash.keys())
        elif type(sample_list) == dict:
            sample_list_ = list(sample_list.keys())
        else:
            sample_list_ = sample_list
        if not test_size:
            test_size = len(instance_hash)
        if not force_recompute and not sample_list_:
            for g in Attribute.values():
                if g.bbw.operator == attr.bbw.operator and attr.test_size >= test_size:
                    logger.info('Found an existing attribute: ' + g.cmd)
                    attr.instance_dict = g.instance_dict
                    recompute_instance = False
                    break
        if recompute_instance:
            if len(sample_list_) > test_size:
                sample_list_ = random.sample(sample_list_, test_size)
            instance_groups = [ 
                Instance.create_instance_dict_given_qid(
                    key.qid, 
                    qid_hash, 
                    instance_hash, 
                    instance_hash_rewritten) 
                for key in sample_list_ ]
            attr.set_instances(
                cmd=cmd, instance_groups=instance_groups,
                attr_hash=attr_hash, group_hash=group_hash)
        attr.domain()
        if save:
            Attribute.save(attr)
        logger.info(f'Created attr: {name}')
        return attr