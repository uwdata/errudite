import os
import sys
import yaml

sys.path.append("..")
sys.path.append("../..")
import base64
import traceback
import argparse
from typing import List

from flask import Flask, render_template, jsonify
from flask_cors import CORS

from errudite.server.converter import \
    ListConverter, IntConverter, StrConverter, IntListConverter, \
    BoolConverter, InstanceKeyConverter, InstanceKeyListConverter
from errudite.server.api import API, APIQA, APIVQA
from errudite.rewrites import Rewrite
from errudite.builts import Attribute, Group
from errudite.targets.interfaces import InstanceKey
from errudite.targets.instance import Instance


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
global api
api = None

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'secret!'
app.url_map.converters['list'] = ListConverter
app.url_map.converters['int_list'] = IntListConverter
app.url_map.converters['str_list'] = ListConverter
app.url_map.converters['int'] = IntConverter
app.url_map.converters['str'] = StrConverter
app.url_map.converters['bool'] = BoolConverter
app.url_map.converters['instance_key'] = InstanceKeyConverter
app.url_map.converters['instance_key_list'] = InstanceKeyListConverter

SUCCESS_MSG = "successful query!"

def get_args():
    """Get the user arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', 
        required=True, 
        help='the configuration file required.')
    args = parser.parse_args()
    return args

args = get_args()
try:
    with open(args.config_file) as f:
        configs = yaml.load(f)
    logger.info(configs)
    # construct the API
    API_CONSTRUCTOR =  API.by_name(configs["task"])
    api = API_CONSTRUCTOR(
        cache_path=configs["cache_path"],
        model_metas=configs["model_metas"],
        attr_file_name=configs["attr_file_name"],
        group_file_name=configs["group_file_name"],
        rewrite_file_name=configs["rewrite_file_name"]
    )
except Exception as e:
    api = None
    traceback.print_exc()
    logger.error(e)

def wrap_output(o, msg=None):
    if msg:
        msg = f'ERR! {msg}'
    else:
        msg = SUCCESS_MSG
    return jsonify({ "output" : o, "msg": msg })

@app.route('/')
def index():
    print(type(api))
    return render_template('index.html')

@app.route('/api/get_task')
def get_task(api: API=api):
    output, msg = None, None
    try:
        output = api.task
        msg = None
    except Exception as e:
        msg = f'{e}'
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/get_img/<img_id>')
def get_img(img_id: str, api: API=api):
    """Get the image"""
    # TODO: understand how to set the folder.
    VQA_FOLDER = ""
    output, msg = None, None
    try:
        imgFilename = 'COCO_val2014_' + str(img_id).zfill(12) + '.jpg'
        img_dir = os.path.join(VQA_FOLDER, 'Images', imgFilename)
        with open(img_dir, 'rb') as f:
            output = base64.b64encode(f.read())
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/get_meta_data')
def get_meta_data(api: API=api):
    output, msg = None, None
    try:
        err_overlaps =api.get_err_overlap(show_filtered_err_overlap=False)
        e_serialized = [ e.serialize() for e in Rewrite.values() ]
        groups = [ g.serialize() for g in Group.values() ]
        attrs = [ a.serialize() for a in Attribute.values() ]
        predictors = [ p.serialize() for p in api.predictors.values() ]
        output = {
            'total_size': len(Instance.qid_hash),
            'anchor_predictor': api.get_anchor_predictor(),
            'compare_predictor': api.get_compare_predictor(),
            'selected_rewrite': api.get_selected_rewrite(),
            'predictors': predictors,
            'attributes': attrs,
            'groups': groups,
            'err_overlaps': err_overlaps,
            'rewrites': e_serialized
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/set_anchor_predictor/<model>')
def set_anchor_predictor(model: str, api: API=api):
    output, msg = None, None
    try:
        api.set_anchor_predictor(model)
        return get_meta_data(api)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
        return wrap_output(output, msg)

@app.route('/api/set_compare_predictor/<model>')
def set_compare_predictor(model: str, api: API=api):
    output, msg = None, None
    try:
        api.set_compare_predictor(model)
        output = {
            'compare_predictor': api.get_compare_predictor(),
            'err_overlaps': api.get_err_overlap(),
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)


inputs_sample_instances = [
    "str:selected_predictor", 
    "str:cmd", 
    "str:sample_method", 
    "str:sample_rewrite",
    "int:sample_size",
    "int:test_size",
    "bool:show_filtered_arr",
    "bool:show_filtered_err_overlap",
    "bool:show_filtered_group",
    "bool:show_filtered_rewrite",
    "str_list:qids",
]
@app.route('/api/sample_instances')
@app.route('/api/sample_instances/<bool:selected_predictor>')
@app.route('/api/sample_instances/' + '/'.join([f'<{i}>' for i in inputs_sample_instances]))
def sample_instances(
        selected_predictor: str=None, 
        cmd: str='', 
        sample_method: str="rand", 
        sample_rewrite: str=None, 
        sample_size: int=10, 
        test_size: int=None,
        show_filtered_arr: bool=False, 
        show_filtered_err_overlap: bool=False,
        show_filtered_group: bool=False,
        show_filtered_rewrite: bool=False,
        qids: List[str]=None,
        api: API=api):
    output, msg = None, None
    try: 
        data = api.sample_instances(
            selected_predictor, cmd, sample_method,
            sample_rewrite, sample_size, test_size, 
            show_filtered_arr, 
            show_filtered_err_overlap,
            show_filtered_group,
            show_filtered_rewrite,
            qids)
        output = {
            'attrs': data['attrs'],
            'rewrites': data['rewrites'],
            'groups': data['groups'],
            'err_overlaps': data['err_overlaps'],
            'sample_cache_idx': data['sample_cache_idx'],
            'sampled_keys': data['sampled_keys'], 
            'info': data['info'],
            'questions': [q.serialize() for q in data['questions']],
            'contexts': [p.serialize() for p in data['contexts']],
            'answers': [a.serialize() for a in data['answers']],
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)


@app.route('/api/get_more_samples/<int:direction>')
@app.route('/api/get_more_samples/<int:direction>/<int:sample_size>')
def get_more_samples(direction: int, sample_size: int=10, api: API=api):
    output, msg = None, None
    try: 
        data = api.get_more_samples(direction, sample_size)        
        output = {
            'sample_cache_idx': data['sample_cache_idx'],
            'sampled_keys': data['sampled_keys'], 
            'questions': [q.serialize() for q in data['questions']],
            'contexts': [p.serialize() for p in data['contexts']],
            'answers': [a.serialize() for a in data['answers']],
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/create_built/<str:name>/<str:description>/<str:cmd>/<str:built_type>')
def creat_built(name: str, description: str, cmd: str, built_type: str, api: API=api):
    output, msg = None, None
    try:
        if built_type == 'group':
            built = Group.create(
                name, description, cmd, 
                attr_hash=Attribute.store_hash(), group_hash=Group.store_hash())
        else:
            built = Attribute.create(
                name, description, cmd,
                attr_hash=Attribute.store_hash(), group_hash=Group.store_hash())
        output = built.serialize()
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/create_rewrite/<str:from_cmd>/<str:to_cmd>/<str:target_cmd>')
def create_rewrite(from_cmd: str, to_cmd: str, target_cmd: str, api: API=api):
    output, msg = None, None
    try:
        rewrite = api.create_rewrite(from_cmd, to_cmd, target_cmd)
        output = rewrite.serialize()
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/delete_built/<str:name>/<str:built_type>')
def delete_built(name: str, built_type: str, api: API=api):
    output, msg = None, None
    try:
        output = api.delete_built(name, built_type) 
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/export_built/<str:file_name>/<str:built_type>')
def export_built(file_name: str, built_type: str, api: API=api):
    output, msg = None, None
    try:
        output = api.export_built(file_name, built_type) 
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/get_one_attr_of_instances/<str:attr_name>/<instance_key_list:instance_keys>')
def get_one_attr_of_instances(attr_name: str, instance_keys: List[InstanceKey], api: API=api):
    output, msg = None, None
    try:
        output = api.get_one_attr_of_instances(attr_name, instance_keys)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/get_groups_of_instances/<instance_key_list:instance_keys>')
def get_groups_of_instances(instance_keys: List[InstanceKey], api: API=api):
    output, msg = None, None
    try:
        output = api.get_groups_of_instances(instance_keys)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)
@app.route('/api/get_rewrites_of_instances/<instance_key_list:instance_keys>')
def get_rewrites_of_instances(instance_keys: List[InstanceKey], api: API=api):
    output, msg = None, None
    try:
        output = api.get_rewrites_of_instances(instance_keys)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)


inputs_attr_distribution = [
    "str_list:attr_names", 
    "str:filter_cmd", 
    "bool:use_sampled_data", 
    "str:include_rewrite",
    "str:include_model",
    "int:test_size"
]
@app.route('/api/get_attr_distribution/' + '/'.join([f'<{i}>' for i in inputs_attr_distribution[:1] ]))
@app.route('/api/get_attr_distribution/' + '/'.join([f'<{i}>' for i in inputs_attr_distribution]))
def get_attr_distribution(
    attr_names: List[str], 
    filter_cmd: str='',
    use_sampled_data: bool=False,
    include_rewrite: str=None,
    include_model: str=None,
    test_size: int=None,
    api: API=api):
    output, msg = None, None
    try:
        output = api.get_attr_distribution(
            attr_names=attr_names, 
            filter_cmd=filter_cmd,
            test_size=test_size,
            use_sampled_data=use_sampled_data, 
            include_model=include_model,
            include_rewrite=include_rewrite)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

inputs_built_distribution = [
    "str:built_type", 
    "str_list:built_names",
    "str:filter_cmd", 
    "bool:use_sampled_data", 
    "str:include_model",
    "int:test_size"
]
@app.route('/api/get_built_distribution/' + '/'.join([f'<{i}>' for i in inputs_built_distribution[:2] ]))
@app.route('/api/get_built_distribution/' + '/'.join([f'<{i}>' for i in inputs_built_distribution]))
def get_built_distribution(
    built_type: str,
    built_names: List[str], 
    filter_cmd: str='',
    use_sampled_data: bool=False,
    include_model: str=None,
    test_size: int=None,
    api: API=api):
    output, msg = None, None
    print
    try:
        output = api.get_built_distribution(
            built_type=built_type, 
            built_names=built_names,
            filter_cmd=filter_cmd,
            test_size=test_size,
            use_sampled_data=use_sampled_data, 
            include_model=include_model)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/get_err_overlap/<bool:show_filtered_err_overlap>')
def get_err_overlap(show_filtered_err_overlap: bool, api: API=api):
    output, msg = None, None
    try:
        output = api.get_err_overlap(show_filtered_err_overlap)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

### Run detections
@app.route('/api/detect_build_blocks/<str:target>/<str:qid>/<int:vid>/<int:start_idx>/<int:end_idx>')
def detect_build_blocks(target: str, qid: str, vid: int, start_idx: int, end_idx: int, api: API=api):
    output, msg = None, None
    try:
        output = api.detect_build_blocks(target, qid, vid, start_idx, end_idx)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/detect_rule_from_rewrite/<str:atext>/<str:btext>/<str:target_cmd>')
def detect_rule_from_rewrite(atext: str, btext: str, target_cmd: str, api: API=api) -> List['Identifier']:
    output, msg = None, None
    try:
        data = api.detect_rule_from_rewrite(atext, btext, target_cmd)
        output = [ r.serialize() for r in data.values() ]
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/evaluate_rewrites_on_groups/<str_list:rids>/<str_list:gnames>/<bool:on_tried>')
def evaluate_rewrites_on_groups(rids: List[str], gnames: List[str], on_tried: bool, API=api):
    output, msg = None, None
    try:
        output = api.evaluate_rewrites_on_groups(rids, gnames, on_tried)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/rewrite_group_instances/<str:rid>/<str:gname>/<int:sample_size>')
def rewrite_group_instances(rid: str, gname: str, sample_size: int, API=api):
    output, msg = None, None
    try:
        output = api.rewrite_group_instances(rid, gname, sample_size)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/rewrite_instances_by_rid')
@app.route('/api/rewrite_instances_by_rid/<str:rid>/<str_list:qids>')
@app.route('/api/rewrite_instances_by_rid/<str:rid>/<str_list:qids>/<int:sample_size>')
@app.route('/api/rewrite_instances_by_rid/<str:rid>/<str_list:qids>/<int:sample_size>/<bool:save>')
def rewrite_instances_by_rid(
    rid: str, qids: List[str]=None, sample_size: int=10, save: bool=False, api: API=api):
    output, msg = None, None
    try:
        output = api.rewrite_instances_by_rid(rid, qids, sample_size, save)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/formalize_rewritten_examples/<str:rid>')
def formalize_rewritten_examples(rid: str, api: API=api):
    output, msg = None, None
    try:
        if Rewrite.exists(rid):
            api.formalize_prev_tried_rewrites(rid)
            e = Rewrite.get(rid)
            output = e.serialize()
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)


@app.route('/api/predict_on_manual_rewrite/<str:qtext>/<str_list:groundtruths>/<str:ctext>')
def predict_on_manual_rewrite(qtext: str, groundtruths: List[str], ctext: str, api: API=api):
    output, msg = None, None
    try:
        output = api.predict_on_manual_rewrite(qtext, groundtruths, ctext)
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)


inputs_predict_formalize = [
    "str:qid", 
    "str:rid",
    "str:q_rewrite", 
    "str_list:groundtruths", 
    "str:c_rewrite",
]
@app.route('/api/predict_formalize/' + '/'.join([f'<{i}>' for i in inputs_predict_formalize[:-1] ]))
@app.route('/api/predict_formalize/' + '/'.join([f'<{i}>' for i in inputs_predict_formalize]))
def predict_formalize(
    qid: str, rid: str, q_rewrite: str, 
    groundtruths: List[str], 
    c_rewrite: str=None, api: API=api) -> List['Identifier']:
    output, msg = None, None
    try:
        data = api.predict_formalize(qid, rid, q_rewrite, groundtruths, c_rewrite)
        output = {
            'key': data['key'],
            'question': data['question'].serialize() if data['question'] else None,
            'context': data['context'].serialize() if data['context'] else None,
            'groundtruths': [g.serialize() for g in data['groundtruths']] if data['groundtruths'] else None,
            'predictions': [g.serialize() for g in data['predictions']] if data['predictions'] else None
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

@app.route('/api/delete_selected_rules/<str_list:rids>')
def delete_selected_rules(rids: List[str], api: API=api):
    output, msg = None, None
    try:
        data = api.delete_selected_rules(rids)
        output = {
            'key': data['key'],
            'question': data['question'].serialize() if data['question'] else None,
            'context': data['context'].serialize() if data['context'] else None,
            'groundtruths': [g.serialize() for g in data['groundtruths']] if data['groundtruths'] else None,
            'predictions': [g.serialize() for g in data['predictions']] if data['predictions'] else None
        }
    except Exception as e:
        msg = e
        logger.error(e)
        traceback.print_exc()
    finally:
        return wrap_output(output, msg)

app.run(debug=True)