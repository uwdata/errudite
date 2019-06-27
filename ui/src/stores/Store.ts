/**
 * The main data storage file.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */
import { observable, action } from 'mobx';
import { Service, RawSamples } from './Service';

import { Predictor } from './Predictor';
import { Attribute } from './Attribute';
import { RewriteRule } from './RewriteRule';
import { QAAnswer, VQAAnswer } from './Answer';
import { Context } from './Context';
import { Question, VQAQuestion } from './Question';

import { DataGroup } from './DataGroup';
import { SampleMethod, BuiltType, ErrOverlap, HistoryMeta } from './Interfaces';
import { InstanceKey, QAInstanceKey } from './InstanceKey';
import { utils } from './Utils';

export class StoreClass {
    // linking to database and backend
    public dataType: string;
    public service: Service; 
    // sampling strategy and data loading status
    @observable public sampleMethod: SampleMethod;
    @observable public testSize: number;
    @observable public rewriteTestSize: number;
    @observable public includeSampleGroups: string[];
    @observable public excludeSampleGroups: string[];
    @observable public loadingData: string; // state for store.
    @observable public validFetchMsg: string; // state for store.

    // performance supported
    public metricNames: string[];

    // the loaded instances
    @observable public totalSize: number;
    @observable public sampleInfo: {
        counts: {
            incorrect?: number;
            correct?: number;
            rewritten?: number;
            prediction_changed?: number;
        }, 
        stats: {
            coverage?: number; 
            error_coverage?: number;
            local_error_rate?: number;
            global_error_rate?: number;
            changed_coverage?: number;
            changed_rate?: number;
        }
    };
    // save the filtered instances into one list.
    @observable public sampledInstances: InstanceKey[];

    // some meta, template, and rule information
    public rewriteStore: {[key: string]: RewriteRule}; // the rewritting metadata
    @observable public rewriteHashes: string[];
    @observable public sampleRewrite: string;

    public attrStore: {[key: string]: Attribute};
    @observable public attrHashes: string[]; // the attribute metadata

    // all the loaded predictors: bidaf-elmo, bidaf baseline, etc
    public predictorStore: {[key: string]: Predictor};
    // the selected predictors that are used for analysis currently
    @observable public selectedPredictors: string[];
    // one anchor predictor; supposedly other comparisons are to this.
    @observable public anchorPredictor: string;
    @observable public comparePredictor: string;

    // data slice information
    public dataGroupStore: {[key: string] : DataGroup};
    @observable public dataGroupHashs: string[];
    @observable public selectedDataGroup: string;

    // the cmd str 
    @observable public activeCmd: string;
    public lastExecutedCmd: string;
    @observable public setCmd: number;
    // info that controls new slice status. displays success, loading, or error.
    // highlight info
    @observable public highlightedInstances: InstanceKey[];

    // render the manager
    @observable public browserTarget: 'group'|'rewrite';
    // attribute filter
    @observable public filteredAttrList: Attribute[]; 
    @observable public showFilteredAttr:  boolean;
    @observable public showRewriteAttr:  boolean;
    // group filter and rewriting filter
    @observable public filteredGroupList: DataGroup[]; 
    @observable public showFilteredGroup:  boolean;
    @observable public filteredRewriteList: RewriteRule[]; 
    @observable public showFilteredRewrite:  boolean;
    @observable public showFilteredErrOverlap: boolean;


    // the error overlap
    @observable public errOverlaps: ErrOverlap[];

    // the analysis procedure list
    @observable public historyList: HistoryMeta[];
    @observable public procedureIdx: number;
    
    @observable public sampleCacheIdx: number;

    constructor () {
        this.service = new Service();
        this.totalSize = 0;
        this.sampledInstances = [];

        this.rewriteStore = {};
        this.rewriteHashes = [];
        this.attrStore = {};
        this.attrHashes = [];
        this.highlightedInstances = [];

        // predictors
        this.predictorStore = {};
        this.selectedPredictors = []; // name
        this.anchorPredictor = null; // name
        this.comparePredictor = null;

        
        this.dataGroupStore = {};
        this.dataGroupHashs = [];
        this.sampleRewrite = null;
        this.selectedDataGroup = '';
        this.includeSampleGroups = [];
        this.excludeSampleGroups = [];
        this.activeCmd = '';
        this.setCmd = 0;
        this.lastExecutedCmd = '';

        this.browserTarget = 'group';
        this.dataType = '';

        this.setActiveCmd = this.setActiveCmd.bind(this);
        this.filteredAttrList = null;
        this.showFilteredAttr = false;
        this.showRewriteAttr = false;
        this.filteredGroupList = null;
        this.filteredRewriteList = null;
        this.showFilteredGroup = false;
        this.showFilteredRewrite = false;
        this.showFilteredErrOverlap = false;

        this.testSize = 0;
        this.rewriteTestSize = 100;
        // overlap 
        this.errOverlaps = [];
        this.historyList = [];
        this.procedureIdx = -1;
        this.sampleCacheIdx = -1;

        // sampling
        this.sampleInfo = null;
        this.sampleMethod = 'rand';
        this.loadingData = '';
        this.validFetchMsg = this.service.SUCCESS_MSG;
    }

    public async init(): Promise<void> {
        this.loadingData = 'loading';
        await this.loadMetas();
        const curData = this.showFilteredAttr;
        this.showFilteredAttr = false;
        await this.sampleInstance(this.activeCmd, this.sampleMethod, this.sampleRewrite, null, null);
        this.showFilteredAttr = curData;
        this.loadingData = 'done';
    }

    public async redoUndoHandler(direction: 1|-1): Promise<void> {
        this.loadingData = 'loading';
        if (this.procedureIdx + direction >= 0 && this.procedureIdx + direction < this.historyList.length) {
            this.procedureIdx += direction;
            const procedure = this.historyList[this.procedureIdx];
            // get back the cmd
            this.setActiveCmd(procedure.cmd, true, true);
            await this.sampleInstance(procedure.cmd, this.sampleMethod, 
                this.sampleRewrite, null, procedure.instances, false);
        }
        this.loadingData = 'done';
    }

    public isValidFetch(): boolean {
        return this.validFetchMsg === this.service.SUCCESS_MSG;
    }

    public resetFetchMsg(): void {
        this.validFetchMsg = this.service.SUCCESS_MSG;
    }

    public recordProcedure(): void {
        // get the history
        // if it's starting half way, overwrite the already-created "future" histories
        let history: HistoryMeta[] = this.historyList.slice(0, this.procedureIdx + 1);
        history.push({
            cmd: this.activeCmd,
            instances: this.sampledInstances.slice()
        })
        // if the history is getting too long
        history = history.slice(history.length - 10, history.length);
        this.historyList = history;
        this.procedureIdx = this.historyList.length - 1;
    }

    @action public async loadMetas(): Promise<void> {
        this.loadingData = 'pending';
        const loadedMetas = await this.service.getMetaData();
        if (loadedMetas !== null) {
            // save the total size
            this.totalSize = loadedMetas.total_size;
            // set the test size to be everything
            this.testSize = this.totalSize;
            // first, get some meta data that stays the same for the whole system
            this.anchorPredictor = loadedMetas.anchor_predictor;
            this.comparePredictor = loadedMetas.compare_predictor;
            loadedMetas.predictors.forEach((p: any) => {
                this.predictorStore[p.name] = new Predictor(p.name, p.description, p.perform);
            });
            // originally, display all the loaded predictors.
            this.selectedPredictors = Object.keys(this.predictorStore);
            // get the metas and sort by p value
            // TODO: do we need to sort????
            loadedMetas.attributes.forEach((a: any) => {
                this.attrStore[a.name] = new Attribute(
                    a.name, a.description, a.dtype, a.cmd, a.domain, a.counts);
                });
            // load the rewrites and data groups
            loadedMetas.rewrites.forEach((e: any) => {            
                this.rewriteStore[e.rid] = new RewriteRule(
                    e.rid, e.description, e.category, e.target, 
                    e.target_cmd, e.counts, e.examples);
            });
            loadedMetas.groups.forEach((g: any) => {
                this.dataGroupStore[g.name] = new DataGroup(
                    g.name, g.description, g.cmd, g.counts, g.stats);
                //this.dataGroupStore[g.name].getEdits(Object.values(this.editTemplateStore));
            });
            // load the err overlaps
            this.errOverlaps = loadedMetas.err_overlaps;       
        } 
        this.rewriteHashes = Object.keys(this.rewriteStore);
        this.dataGroupHashs = Object.keys(this.dataGroupStore);
        this.attrHashes = Object.keys(this.attrStore);
    }

    public async buildInstancesWithQueries(queried: RawSamples): Promise<void> {
        return;
    }

    public async getMoreSamples(direction: 1|-1): Promise<void> {
        this.loadingData = 'pending';
        const queried = await this.service.getMoreSamples(direction);
        if (queried !== null) {
            await this.buildInstancesWithQueries(queried);
            this.sampleCacheIdx = queried.sample_cache_idx;
        }
        this.loadingData = 'done';
    }

    public async sampleInstance(
        cmd: string, 
        sampleMethod: SampleMethod, 
        sampleRewrite: string,
        testSize: number, instanceKeys: InstanceKey[], 
        saveNewProcedure: boolean=true): Promise<void> {
        this.loadingData = 'pending';
        const queried = await this.queryInstances(
            cmd, sampleMethod, sampleRewrite, testSize, instanceKeys);
        if (queried !== null) {
            await this.buildInstancesWithQueries(queried);
            this.sampleCacheIdx = queried.sample_cache_idx;
            if (saveNewProcedure) {
                this.recordProcedure();
            }
            this.lastExecutedCmd = this.activeCmd;
        }
        this.loadingData = 'done';
    }

        
    public async queryInstances(
        cmd: string, 
        sampleMethod: SampleMethod, 
        sampleRewrite: string, 
        testSize: number, instanceKeys: InstanceKey[]): Promise<RawSamples> {
        this.loadingData = 'pending';
        const qids = instanceKeys ? instanceKeys.map(i => i.qid).filter(utils.uniques) : null;
        const queried = await this.service.sampleInstances( 
            this.anchorPredictor, 
            cmd, sampleMethod, sampleRewrite, 
            10, testSize,
            this.showFilteredAttr, 
            this.showFilteredErrOverlap,
            this.showFilteredGroup,
            this.showFilteredRewrite,
            qids);
        if (queried !== null) {
            this.filteredAttrList = queried.attrs ? queried.attrs.map(g => 
                new Attribute(g.name, g.description, 
                    g.dtype, g.cmd, g.domain, g.counts)) : this.filteredAttrList;
            this.filteredRewriteList = queried.rewrites ? queried.rewrites.map((e: any) => 
                new RewriteRule(e.rid, e.description, e.category, 
                    e.target, e.target_cmd, e.counts, e.examples)) : this.filteredRewriteList;
            this.filteredGroupList = queried.groups ? queried.groups.map((g: any) => 
                new DataGroup(g.name, g.description, 
                    g.cmd, g.counts, g.stats)) : this.filteredGroupList;
            // load the err overlaps
            this.errOverlaps = (queried.err_overlaps !== null && queried.err_overlaps !== undefined) ? 
                queried.err_overlaps : this.errOverlaps;
            this.sampleInfo = queried.info;
        }
        return queried;
    }

    public refactorCmd(matchCmd: string, cmd: string, 
        isNot: boolean, onlyTest: boolean): boolean|string {
        const notCmd = isNot ? 'not\\s+[\(]*\\s*' : ''
        const rep = new RegExp(`[and\\s|or\\s]*\\s*[\(]*\\s*${notCmd}${
            matchCmd
                .replace(/\(/g, '\\(')
                .replace(/\)/g, '\\)')
                .replace(/\"/g, '\\"')
            }\\s*[\)]*\\s*`,'g');
        if (onlyTest) {
            return rep.test(cmd);
        } else {
            cmd = cmd.replace(rep, ' ');
            if (cmd.startsWith('and ')) { cmd = cmd.slice(4); }
            if (cmd.startsWith('or ')) { cmd = cmd.slice(3); }
            return cmd.trim();
        }
    }
    // , refreshOnSet: boolean=true
    @action public setActiveCmd(
        cmd: string, immediate_update: boolean=false, refreshOnSet: boolean=false): void {
        const setGroups = () => {
            if (this.activeCmd !== cmd) {
                this.activeCmd = cmd;
                const includeSampleGroups = [];
                const excludeSampleGroups = [];
                for (let name of this.dataGroupHashs) {
                    const groupName = `instance in group:${name}`;
                    if (this.refactorCmd(groupName, cmd, true, true)) {
                        excludeSampleGroups.push(name);
                    } else if (this.refactorCmd(groupName, cmd, false, true)) {
                        includeSampleGroups.push(name);
                    }
                }
                this.includeSampleGroups = includeSampleGroups;
                this.excludeSampleGroups = excludeSampleGroups;
                if (refreshOnSet) {
                    this.setCmd += 1;
                }
            }
        }
        if (immediate_update) {
            setGroups();
        } else {
            setTimeout(() => { setGroups(); }, 500);
        }
        
    }
    
    @action public computeActiveCmdBasedOnGroups() {
        let cmd = this.activeCmd;
        for (let name of this.dataGroupHashs) {
            //name = name.replace('_', '\_');
            const groupName = `instance in group:${name}`;
            cmd = this.refactorCmd(groupName, cmd, true, false) as string;
            cmd = this.refactorCmd(groupName, cmd, false, false) as string;
            if (this.includeSampleGroups.indexOf(name) > -1) {
                if (cmd === '') {
                    cmd = `instance in group:${name}`;
                } else {
                    cmd += ` and (instance in group:${name})`;
                }
            } else if (this.excludeSampleGroups.indexOf(name) > -1) {
                //const rep = new RegExp(`[and\\s+|or\\s+]*\\s*[\(]*\\s*instance in group:${name}\\s*[\)]*\\s*`,'g');
                //cmd = cmd.replace(rep, ' ');
                if (cmd === '') {
                    cmd = `not instance in group:${name}`;
                } else {
                    cmd += ` and (not instance in group:${name})`;
                }
            }
        }
        this.activeCmd = cmd;
        this.setCmd++;
    }

    @action public async setCmdFromGroup(group: DataGroup): Promise<void> {
        
        this.excludeSampleGroups = [];
        this.includeSampleGroups = [group.name];
        //this.sampleMethod = 'rand';
        //this.sampleDirection = 'from';
        this.activeCmd = group.cmd;
        this.setCmd++;
        this.browserTarget = 'group';
        this.testSize = this.totalSize;
        this.sampleRewrite = null;
        await this.sampleInstance(this.activeCmd, this.sampleMethod, null, null, null);
    }

    @action public switchBrowserTarget(view: "group"|"rewrite"): void {
        this.browserTarget = view;
        if (view === "rewrite") {
            this.sampleMethod = 'changed';
            this.sampleRewrite = this.rewriteHashes.length > 0 ? this.rewriteHashes[0] : null;
        } else {
            this.sampleMethod = 'rand';
            this.sampleRewrite = null;
            this.showRewriteAttr = false;
        }
        //this.testSize = this.totalSize;
    }

    @action public async setSelectedRewrite(rid: string): Promise<void> {
        if (rid === "unrewritten") {
            this.sampleRewrite = null;
        } else {
            this.sampleRewrite = rid;
        }
        this.browserTarget = 'rewrite';
        //this.setActiveCmd(`is_rewritten_by(rewrite="SELECTED")`, true, true);
        //this.lastExecutedCmd = `is_rewritten_by(rewrite="${rid}")`;
        //this.setActiveCmd('', true, true);
        //this.testSize = this.totalSize;
    }

    /**
     * Set the anchor predictor by name.
     * @param predictorName the name of the predictor.
     */
    @action public async setAnchorPredictor(predictorName: string): Promise<void> {
        if (predictorName === this.anchorPredictor) {
            return;
        }
        this.loadingData = 'pending';
        const loadedMetas = await this.service.setPredictor(predictorName, 'anchor');
        if (loadedMetas !== null) {
            loadedMetas.attributes
            .forEach((a: any) => {
                this.attrStore[a.name] = new Attribute(
                    a.name, a.description, a.dtype, a.cmd, a.domain, a.counts);
            });
            // load the rewrites and data groups
            loadedMetas.rewrites.forEach((e: any) => {            
                this.rewriteStore[e.rid] = new RewriteRule(
                    e.rid, e.description, e.category, e.target, 
                    e.target_cmd, e.counts, e.examples);
            });
            loadedMetas.groups.forEach((g: any) => {
                this.dataGroupStore[g.name] = new DataGroup(
                    g.name, g.description, g.cmd, g.counts, g.stats);
                //this.dataGroupStore[g.name].getEdits(Object.values(this.editTemplateStore));
            });
            this.errOverlaps = loadedMetas.err_overlaps; 
            this.anchorPredictor = loadedMetas.anchor_predictor;
            this.comparePredictor = loadedMetas.compare_predictor;
            this.sampleRewrite = loadedMetas.selected_rewrite === "unrewritten" ? 
                null : loadedMetas.selected_rewrite;
        }
        this.loadingData = 'done';
    }
    @action public async setComparePredictor(predictorName: string): Promise<void> {
        if (predictorName === this.comparePredictor) {
            return;
        }
        this.loadingData = 'pending';
        const loadedMetas = await this.service.setPredictor(predictorName, 'compare');
        if (loadedMetas !== null) {
            this.errOverlaps = loadedMetas.err_overlaps;
            this.comparePredictor = loadedMetas.compare_predictor;
        }
        this.loadingData = 'done';
    }
    /**
     * Start a new section of filtering
     */
    @action public startNewFilterSection(): void {
        // first, get the current state
        this.recordProcedure();
        // and then, do the reset;
        this.includeSampleGroups = [];
        this.excludeSampleGroups = [];
        this.validFetchMsg = this.service.SUCCESS_MSG;
        this.sampleMethod = 'rand';
        this.activeCmd = '';
        this.setCmd++;
        this.testSize = this.totalSize;
        this.sampleInstance(this.activeCmd, this.sampleMethod, null, null, null);
    }

    @action public async deleteBuilt(name: string, type: BuiltType): Promise<void> {
        const deleted = await this.service.deleteBuilt(name, type);
        if (deleted) {
            if (type === 'attr') {
                this.attrHashes = this.attrHashes.filter(a => a !== name);
                if (name in this.attrStore) {
                    delete this.attrStore[name];
                }
            } else if (type === 'group') {
                this.dataGroupHashs = this.dataGroupHashs.filter(a => a !== name);
                if (name in this.dataGroupStore) {
                    delete this.dataGroupStore[name];
                }
            } else if (type === 'rewrite') {
                this.rewriteHashes = this.rewriteHashes.filter(a => a !== name);
                if (name in this.rewriteStore) {
                    delete this.rewriteStore[name];
                }
            }
        }
        this.loadingData = "done";
    }    

    public async createBuiltsWithCmd(name: string, description: string, cmd: string, type: BuiltType): 
        Promise<Attribute|DataGroup> {
        // check whether the group already exist
        this.loadingData = 'pending';
        const g = await this.service.createBuilt(name, description, cmd, type);
        if (g !== null && type == 'group') {
            this.dataGroupStore[g.name] = new DataGroup(
                g.name, g.description, g.cmd, g.counts, g.stats);
            const groupHashes = this.dataGroupHashs.filter(d => d !== g.name);
            groupHashes.push(g.name);
            this.dataGroupHashs = groupHashes.slice();
            this.loadingData = 'done';
            return this.dataGroupStore[g.name];
        } else if (g !== null && type == 'attr') {
            this.attrStore[g.name] = new Attribute(g.name, g.description, g.dtype, g.cmd, g.domain, g.counts);
            const attrHashes = this.attrHashes.filter(d => d !== g.name);
            attrHashes.push(g.name);
            // get the attributes
            if (this.showFilteredAttr) {
                const data = await this.getAttrDistribution([g.name], this.lastExecutedCmd, true);
                const filteredHashes = this.filteredAttrList.map(f => f.name);
                const idx = filteredHashes.indexOf(g.name);
                if (idx > -1) {
                    this.filteredAttrList[idx] = data[0];
                } else {
                    this.filteredAttrList.push(data[0]);
                }
            } 
            this.attrHashes = attrHashes.slice();
            this.loadingData = 'done';
            return this.attrStore[g.name];
        }
        this.loadingData = 'done';
        return null;
    }


    public async getAttrDistribution(
        attrHashes: string[], cmd: string, usePrevSamples: boolean, 
        includeRewrite: string=null, includeModel: string=null): Promise<Attribute[]> {
        this.loadingData = 'pending';
        if (includeRewrite === null) {
            includeRewrite = this.showRewriteAttr && this.browserTarget === 'rewrite' ? 
                this.sampleRewrite : null;
        } else if (includeRewrite === "") {
            includeRewrite = null;
        }
        const data = await store._.service.getAttrDistribution(
            attrHashes, cmd, usePrevSamples, includeRewrite, includeModel);
        this.loadingData = 'done';
        return data === null ? [] :
            data.map(g => new Attribute(
                g.name, g.description, g.dtype, g.cmd, g.domain, g.counts));
    }

    public async getMetaDistribution(
        managerType: "group"|"rewrite", hashes: string[], cmd: string, usePrevSamples: boolean, 
        includeModel: string=null): Promise<(DataGroup|RewriteRule)[]> {
        this.loadingData = 'pending';
        const loadedMetas = await store._.service.getBuiltDistribution(
            managerType, hashes, cmd, usePrevSamples, includeModel);
        this.loadingData = 'done';
        if (loadedMetas === null) {
            return [];
        } else {
            return loadedMetas.map((e: any) => managerType === "rewrite" ? 
                new RewriteRule(e.rid, e.description, e.category, e.target, e.target_cmd, e.counts, e.examples) :
                new DataGroup(e.name, e.description, e.cmd, e.counts, e.stats));
        }
    }

    public async predictFormalize(
        qid: string, rid: string, 
        q_rewrite: string, groundtruths: string[], 
        c_rewrite: string): Promise<InstanceKey> {
        // first, formalize the prediction
        return null;
    }

    public saveQueryToRewrite(t: any): RewriteRule {
        if (t !== null) {
            this.rewriteStore[t.rid] = new RewriteRule(
                t.rid, t.description, t.category, t.target,
                t.target_cmd, t.counts, t.examples);
            const rewriteHashes = this.rewriteHashes.filter(d => d !== t.rid);
            rewriteHashes.push(t.rid);
            this.rewriteHashes = rewriteHashes.slice();
            return this.rewriteStore[t.rid];
        }
        return null;
    }

    public async createRewrite (fromCmd: string, toCmd: string, targetCmd: string) {
        this.loadingData = 'pending';
        const t = await this.service.createRewrite(fromCmd, toCmd, targetCmd);
        const output = this.saveQueryToRewrite(t);
        return output;
    }

    public async formalizeRewrittenExamples (rid: string) {
        this.loadingData = 'pending';
        const t = await this.service.formalizeRewrittenExamples(rid);
        const output = this.saveQueryToRewrite(t);
        this.loadingData = 'done';
        return output;
    }
}


export class QAStoreClass extends StoreClass {
    public questions: Question[];
    public answers: QAAnswer[];
    public contexts: Context[];

    constructor() {
        super();
        this.dataType = 'qa';
        this.metricNames = ['em', 'f1', 'sent', 'precision', 'recall']; // 'precision', 'recall', 
        this.contexts = [];
    }

    public async buildInstancesWithQueries(queried: RawSamples): Promise<void> {
        if (queried === null) {
            return;
        }
        this.contexts = queried.contexts.map(p => new Context(
            p.key, p.aid, p.cid, p.qid, p.vid, p.doc));
        this.questions = queried.questions.map(q =>new Question(
            q.key, q.qid, q.vid, q.doc, q.question_type));
        this.answers = queried.answers.map(a =>new QAAnswer(
            a.key, a.model, a.qid, a.vid, a.sid, a.is_groundtruth,
            a.span_start, a.span_end, a.doc, a.answer_type, a.perform));
        this.sampledInstances = queried.sampled_keys.map(
            k => new QAInstanceKey(k.qid, k.vid, k.rid, k.cid, k.aid));
    }

    /**
     * Do the prediction based on the ids and strings
     * @param {PredictInputMeta} predict article id
     * @return {Promise<{identifier: Identifier, rule: SemanticRule}>} 
     */
    public async predictFormalize(
        qid: string, rid: string, 
        q_rewrite: string, groundtruths: string[], 
        c_rewrite: string): Promise<QAInstanceKey> {
        // first, formalize the prediction
        const res = await this.service.predictFormalize(qid, rid, q_rewrite, groundtruths, c_rewrite);
        if (res) {
            const i = res.key;
            const c = res.context;
            const q = res.question;
            const ps = res.predictions;
            const gs = res.groundtruths;
            if (c !== undefined && c !== null) {
                this.contexts.push(new Context(c.key, c.aid, c.pid, c.qid, c.vid, c.doc));
            }
            if (q !== undefined && q !== null) {
                this.questions.push(new Question(q.key, q.qid, q.vid, q.doc, q.question_type));
            }
            if (gs !== undefined && gs !== null) {
                gs.forEach((a: any) => {
                    this.answers.push(new QAAnswer(
                        a.key, a.model, a.qid, a.vid, a.sid, a.is_groundtruth,
                        a.span_start, a.span_end, a.doc, a.answer_type, a.perform));
                });
            }
            if (ps !== undefined && ps !== null) {
                ps.forEach((a: any) => {
                    this.answers.push(new QAAnswer(
                        a.key, a.model, a.qid, a.vid, a.sid, a.is_groundtruth,
                        a.span_start, a.span_end, a.doc, a.answer_type, a.perform));
                });
            }
            
            const instance = new QAInstanceKey(i.qid, i.vid, i.rid, i.cid, i.aid);
            //this.sampledInstances.push(instance);
            this.loadingData = 'done';
            return instance;
        }
        return null;
    }
}

export class VQAStoreClass extends StoreClass {
    public questions: VQAQuestion[];
    public answers: VQAAnswer[];
    public contexts: Context[];

    constructor () {
        super();
        this.metricNames = ['accuracy'];
        this.questions = [];
        this.answers = [];
        this.dataType = 'vqa';
    }

    public async buildInstancesWithQueries(queried: RawSamples): Promise<void> {
        this.questions = queried.questions.map(q =>new VQAQuestion(
            q.key, q.qid, q.vid, q.doc, q.question_type, q.img_id));
        this.answers = queried.answers.map(a =>new VQAAnswer(
            a.key, a.model, a.qid, a.vid, a.is_groundtruth, 
            a.doc, a.answer_type, a.count, a.perform));
        this.sampledInstances = queried.sampled_keys.map(
            k => new InstanceKey(k.qid, k.vid, k.rid));
    }

    /**
     * Do the prediction based on the ids and strings
     * @param {PredictInputMeta} predict article id
     * @return {Promise<{identifier: Identifier, rule: SemanticRule}>} 
     */
    public async predictFormalize(
        qid: string, rid: string, 
        q_rewrite: string, groundtruths: string[], 
        c_rewrite: string): Promise<InstanceKey> {
        // first, formalize the prediction
        const res = await this.service.predictFormalize(qid, rid, q_rewrite, groundtruths, c_rewrite);
        if (res) {
            const i = res.key;
            const q = res.question;
            const ps = res.predictions;
            const gs = res.groundtruths;
            if (q !== undefined && q !== null) {
                this.questions.push(new VQAQuestion(
                    q.key, q.qid, q.vid, q.doc, q.question_type, q.img_id));
            }
            if (gs !== undefined && gs !== null) {
                gs.forEach((a: any) => {
                    this.answers.push(new VQAAnswer(
                        a.key, a.model, a.qid, a.vid, a.is_groundtruth, 
                        a.doc, a.answer_type, a.count, a.perform));
                });
            }
            if (ps !== undefined && ps !== null) {
                ps.forEach((a: any) => {
                    this.answers.push(new VQAAnswer(
                        a.key, a.model, a.qid, a.vid, a.is_groundtruth, 
                        a.doc, a.answer_type, a.count, a.perform));
                });
            }
            const instance = new InstanceKey(i.qid, i.vid, i.rid);
            //this.sampledInstances.push(instance);
            this.loadingData = 'done';
            return instance;
        }
        return null;
    }
}


export class StoreWrapper {
    @observable public _: QAStoreClass|VQAStoreClass;
    constructor() {
        this._ = new QAStoreClass();
    }
    public async getHandler() {
        const service = new Service();
        const dataType = await service.getTask();
        this._ = dataType === 'qa' ? new QAStoreClass() : new VQAStoreClass();
    }
}

export const store = new StoreWrapper();
