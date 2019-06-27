/**
 * wtshuang@cs.uw.edu
 * 2018/01/12
 * The class for connecting to the backend.
 */
import { store } from './Store';
import { SampleMethod, RewrittenReturn, Suggestion, ErrOverlap } from './Interfaces';
import { InstanceKey } from './InstanceKey';
import { AttrValue } from './Attribute';

import { message } from 'antd';


export interface Loaded<T> {
    msg: string;
    output: T
}

export interface RawSamples {
    attrs?: any[];
    rewrites?: any[];
    groups: any[];
    err_overlaps?: ErrOverlap[];
    contexts: any[];
    questions: any[];
    answers: any[];
    info?: any;
    sample_cache_idx:number;
    sampled_keys: {
        qid: string;
        vid: number;
        rid: string;
        aid?: number;
        cid?: number;
    }[];
};

interface RawMeta {
    total_size: number;
    anchor_predictor: string,
    compare_predictor: string,
    selected_rewrite: string;
    attributes: any[], 
    rewrites: any[], 
    predictors: any[], 
    groups: any[];
    err_overlaps: ErrOverlap[];
}

interface RawMetaWithAnchor {
    anchor_predictor: string,
    compare_predictor: string,
    selected_rewrite: string;
    attributes: any[],
    err_overlaps: any[]; 
    rewrites: any[], 
    groups: any[]
}

export class Service {
    SUCCESS_MSG = "Successful!";
    private async fetch(
        url: string,
        method: string = 'GET',
        body: object = null): Promise<any> {
        url = url.startsWith("/api/") ? url : `/api/${url}`;
        url = encodeURIComponent(url);
        var headers = new Headers();
        if (body !== null) {
            headers.append('Content-Type', 'application/json');
            headers.append('Accept', 'application/json');
            return fetch(new Request(url, {
                'method': method,
                'headers': headers,
                'body': JSON.stringify(body)
            }));
        } else {
            return fetch(new Request(url, {
                'method': method,
                'headers': headers
            }));
        }
    }

    private _errMsg<T>(err: any): Loaded<T> {
        return {output: null, msg: `ERR! ${err}`};
    }

    private _buildUrl(...params:any[]): string {
        store._.validFetchMsg = '';
        store._.loadingData = 'pending';
        function unify(param) {
            if (param === null || param === undefined || `${param}` === "") {
                return "None";
            } else if (param instanceof InstanceKey) {
                return param.key();
            }
            else {
                return `${param}`;
            }
        }
        const outputs = params.map(param => {
            if (param instanceof Array) {
                return param.map(p => unify(p)).join(":::");
            } else {
                return unify(param);
            }
        })
        return outputs.join("/");
    }

    private async _fetchReturn<T>(url: string): Promise<T> {
        return await this.fetch(url)
            .then(res => res.clone().json())
            .then(data => {
                return this._isValidFetch(data) as T;
            }).catch(err => {
                return this._isValidFetch(this._errMsg<T>(err));
            }); 
    }

    public _isValidFetch(loaded: Loaded<any>): any {
        if (loaded === null) {
            store._.validFetchMsg = "ERR! Unkown problem."
            return null;
        }
        else if (loaded.msg.startsWith("ERR!")) {
            // is wrong.
            store._.validFetchMsg = loaded.msg;
        } else {
            // not wrong
            store._.validFetchMsg = this.SUCCESS_MSG;
        }
        return loaded.output;
    }

    public async setPredictor(predictorName: string, type: 'anchor'|'compare'): 
        Promise<RawMetaWithAnchor> {
        const url = this._buildUrl(`set_${type}_predictor`, predictorName);
        return await this. _fetchReturn<RawMetaWithAnchor>(url);
    }

    public async getErrOverlap(showFilteredErrOverlap: boolean): Promise<ErrOverlap[]> {
        const url = this._buildUrl(`get_err_overlap`, showFilteredErrOverlap);
        return await this. _fetchReturn<ErrOverlap[]>(url);
    }
    public async getTask(): Promise<string> {
        return await this. _fetchReturn<string>("get_task");
    }

    /**
     * This function loads the info that stays the same throughout the system:
     *  predictors to be compared
     *  attributes
     *  rewriting methods
     */
    public async getMetaData(): Promise<RawMeta> {
        return await this. _fetchReturn<RawMeta>("get_meta_data");
    }

    public async getImg(imgId: string): Promise<string> {
        const url = this._buildUrl(`get_img`, imgId);
        return await this. _fetchReturn<string>(url);
    }

    public async getMoreSamples(direction: -1|1): Promise<RawSamples> {
        const url = this._buildUrl(`get_more_samples`, direction);
        return await this. _fetchReturn<RawSamples>(url);
    }

    public async sampleInstances(
        selectedPredictor: string,
        cmd: string,
        sampleMethod: SampleMethod, 
        sampleRewrite: string, 
        sampleSize: number, 
        testSize: number, 
        showFilteredAttr: boolean, 
        showFilteredErrOverlap: boolean,
        showFilteredGroup: boolean,
        showFilteredRewrite: boolean,
        qids: string[]): Promise<RawSamples> {
        const url = this._buildUrl(
            'sample_instances', 
            selectedPredictor, 
            cmd,
            sampleMethod, 
            sampleRewrite, 
            sampleSize, 
            testSize, 
            showFilteredAttr, 
            showFilteredErrOverlap,
            showFilteredGroup,
            showFilteredRewrite,
            qids
        );
        return await this. _fetchReturn<RawSamples>(url);
    }

    public async createBuilt(name: string, description: string, cmd: string, type: string): Promise<any> {
        const url = this._buildUrl(`create_built`, name, description, cmd, type);
        return await this. _fetchReturn<any>(url);
    }

    public async exportBuilt(fileName: string, type: string): Promise<boolean> {
        const url = this._buildUrl(`export_built`, fileName, type);
        return await this. _fetchReturn<boolean>(url);
    }

    public async deleteBuilt(name: string, type: string): Promise<boolean> {
        const url = this._buildUrl(`delete_built`, name, type);
        return await this. _fetchReturn<boolean>(url);
    }

    public async getOneAttrOfInstances(attrName: string, instanceKeys: InstanceKey[]): Promise<AttrValue[]> {
        const url = this._buildUrl(`get_one_attr_of_instances`, attrName, instanceKeys);
        return await this. _fetchReturn<AttrValue[]>(url);
    }

    public async getBuiltsOfInstances(instanceKeys: InstanceKey[], type: "group"|"rewrite"): Promise<string[]> {
        const url = this._buildUrl(`get_${type}s_of_instances`, instanceKeys);
        return await this. _fetchReturn<string[]>(url);
    }

    public async getAttrDistribution(
        attrNames: string[], cmd: string, 
        usePrevSamples: boolean, includeRewrite: string, 
        includeModel: string, testSize: number=null): Promise<any[]> {
        const url = this._buildUrl(`get_attr_distribution`, attrNames, cmd, 
        usePrevSamples, includeRewrite, includeModel, testSize);
        return await this. _fetchReturn<any[]>(url);
    }

    public async getBuiltDistribution(
        metaType: string, metaNames: string[], cmd: string, 
        usePrevSamples: boolean, includeModel: string, testSize: number=null): Promise<any[]> {
        const url = this._buildUrl(`get_built_distribution`, metaType, metaNames, cmd, 
        usePrevSamples, includeModel, testSize);
        return await this. _fetchReturn<string[]>(url);
    }

    public async detectBuildBlocks(
        target: string, qid: string, 
        vid: number, start_idx: number, 
        end_idx: number): Promise<Suggestion[]>  {
        const url = this._buildUrl(
            'detect_build_blocks', target, qid, vid, start_idx, end_idx);
        return await this. _fetchReturn<Suggestion[]>(url);
    }

    /*--------- REWRITES ------------*/
    public async createRewrite(fromCmd: string, toCmd: string, targetCmd: string)
        :Promise<any> {
        store._.loadingData = 'pending';
        const url = this._buildUrl('create_rewrite', fromCmd, toCmd, targetCmd);
        return await this. _fetchReturn<Suggestion[]>(url);
    }

    public async formalizeRewrittenExamples(rid: string): Promise<any>  {
        const url = this._buildUrl('formalize_rewritten_examples', rid);
        return await this. _fetchReturn<Suggestion[]>(url);
    }

    public async evalRewritesOnGroups(
        rids: string[], groups: string[], onTried: boolean=true): Promise<any[]>  {
        const url = this._buildUrl('evaluate_rewrites_on_groups', rids, groups, onTried);
        return await this. _fetchReturn<any[]>(url);
    }

    public async rewriteGroupInstances(
        rid: string, group: string, sampleSize: number): Promise<any> {
        const url = this._buildUrl('rewrite_group_instances', rid, group, sampleSize);
        return await this. _fetchReturn<any>(url);
    }

    public async rewriteOneInstanceByRid(
        rid: string, qid: string): Promise<RewrittenReturn> {
        const url = this._buildUrl('rewrite_instances_by_rid', rid, [qid]);
        const output = await this. _fetchReturn<RewrittenReturn[]>(url);
        return output !== null && output.length > 0 ? output[0] : null;
    }

    public async rewriteInstancesByRid(rid: string, qids: string[]): Promise<RewrittenReturn[]> {
        const url = this._buildUrl('rewrite_instances_by_rid', rid, qids);
        return await this. _fetchReturn<RewrittenReturn[]>(url);
    }

    public async predictOnManualRewrite(qRewrite: string, groundtruths: string[], cEdit: string)
        :Promise<{prediction: string, perform: number}> {
        const url = this._buildUrl(
            'predict_on_manual_rewrite', qRewrite, groundtruths, cEdit);
        return await this. _fetchReturn<{prediction: string, perform: number}>(url);
    }

    public async predictFormalize(qid: string, rid: string, qRewrite: string, groundtruths: string[], cEdit: string)
    :Promise<{key: any, question: any, context: any, groundtruths: any, predictions: any}> {
        const url = this._buildUrl('predict_formalize', qid, rid, qRewrite, groundtruths, cEdit);
        return await this. _fetchReturn<{key: any, question: any, context: any, groundtruths: any, predictions: any}>(url);
    }

    public async detectRuleFromRewrite(atext: string, btext: string, targetCmd: string)
        :Promise<any[]> {
        store._.loadingData = 'pending';
        const url = this._buildUrl('detect_rule_from_rewrite', atext, btext, targetCmd);
        return await this. _fetchReturn<any[]>(url);
    }

    /**
     * Use the qids to augment predefined list of queries.
     * @param {string} qids ids of the question that needs augmentations
     * @param {string} tids ids of editing templates used for augmentation  
     */
    public async deleteSelectedRules(rids: string[]): Promise<any> {
        const url = this._buildUrl('delete_selected_rules', rids);
        return await this. _fetchReturn<any[]>(url);
    }
}
