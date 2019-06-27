import * as React from 'react';
import ResizeAware from 'react-resize-aware';

import { Button, Row, Divider, Col, Select, Tooltip, Icon, InputNumber } from 'antd';

import { observer } from 'mobx-react';
import { observable } from 'mobx';
import { RewriteRule, RewriteStatCount } from '../../stores/RewriteRule';
import { RewrittenReturn } from '../../stores/Interfaces';

import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { QueryCoder } from '../shared-components/QueryCoder';

import { GroupBar, Value } from '../shared-components/GroupBar';
import { RawRewritePreview, RawRewritePreviewQA } from './RawRewritePreview';

interface PreviewdGroupRewrite {
    rid: string; group: string; counts: RewriteStatCount;
}

interface RewriteInspectProps {
    rewriteName: string;
    previewdGroupRewrites: PreviewdGroupRewrite[];
}



@observer
export class RewriteInspectPanel extends React.Component<RewriteInspectProps, {}> {
    private fromCmd: string;
    private toCmd: string;
    private targetCmd: string;
    @observable public msg: string;
    @observable public msgSave: string;
    @observable private inspectRewrite: RewriteRule;
    @observable private returnedRawRewrites: RewrittenReturn[];
    @observable private previewdGroupRewrites: PreviewdGroupRewrite[];
    @observable private confirmedPatternPreview: boolean;

    constructor (props: any, context: any) {
        super(props, context);
        this.msg = '';
        this.msgSave = '';
        this.inspectRewrite = null;
        this.confirmedPatternPreview = false;
        this.returnedRawRewrites = [];
        this.previewdGroupRewrites = this.props.previewdGroupRewrites;
        this.reset();
        this.setInspectRewrite(this.props.rewriteName);

        this.setInfo = this.setInfo.bind(this);
        this.create = this.create.bind(this);
        this.rewriteGroupInstances = this.rewriteGroupInstances.bind(this);
        this.formalizeRewrittenExamples = this.formalizeRewrittenExamples.bind(this);
    }

    protected renderTargetSelectList(): JSX.Element {
        const dataList = ["question", "groundtruth"]
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => { this.setInfo(v as string, "targetCmd") }}
            defaultValue={ this.targetCmd }
            dropdownMatchSelectWidth={false}
            placeholder="Select rewrite rules"
            size="small">
                {dataList.map(d => {
                    return <Select.Option key={d}>{d}</Select.Option>
                })}
        </Select>
    }


    public setInspectRewrite(rewriteName: string): void {
        if (rewriteName in store._.rewriteStore) {
            this.inspectRewrite = store._.rewriteStore[rewriteName];
            this.confirmedPatternPreview = true;
        } else {
            this.inspectRewrite = null;
            this.confirmedPatternPreview = false;
        }
    }

    public async create(): Promise<void> {
        store._.loadingData = 'loading';
        store._.resetFetchMsg();
        let inspectRewrite = null;
        if (!this.fromCmd || !this.toCmd || !this.targetCmd) {
            this.msg = 'Input the target, and from and to patterns!'
            return;
        } else {
            if (this.inspectRewrite) {
                await store._.deleteBuilt(this.inspectRewrite.rid, 'rewrite');
                this.inspectRewrite = null;
            }
            inspectRewrite = await store._.createRewrite(this.fromCmd, this.toCmd, this.targetCmd);
            this.inspectRewrite = inspectRewrite;
            if (inspectRewrite) {
                const previewdGroupRewrites = await store._.service.evalRewritesOnGroups(
                    [this.inspectRewrite.rid], store._.dataGroupHashs);
                this.previewdGroupRewrites = previewdGroupRewrites === null 
                    ? [] : previewdGroupRewrites.slice();
                const data = await store._.service.rewriteGroupInstances(
                    this.inspectRewrite.rid, "all_instances", 10);
                if (data) {
                    this.returnedRawRewrites = data;
                }
                this.msg = '';
                this.msgSave = '';
            }
        }
        store._.loadingData = 'done';
    }

    private setInfo(str: string, target: 'fromCmd'|'toCmd'|'targetCmd'): void {
        this[target] = str;
    }

    private reset(): void {
        this.fromCmd = '';
        this.toCmd = '';
        this.targetCmd = '';
        this.inspectRewrite = null;
    }

    public async rewriteGroupInstances(rid: string, group: string): Promise<void> {    
        store._.loadingData = 'pending';
        const data = await store._.service.rewriteGroupInstances(
            rid, group, store._.rewriteTestSize);
        if (data) {
            this.returnedRawRewrites = data;
            const evals = await store._.service.evalRewritesOnGroups(
                [rid], store._.dataGroupHashs, true); // [group]
            this.previewdGroupRewrites = evals === null ? [] : evals.slice();
            if (evals) {
                /*
                const e = evals[0];
                const hash = this.previewdGroupEdits.map(p => `${p.rid}-${p.group}`);
                const idx = hash.indexOf(`${e.rid}-${e.group}`);
                if (idx > -1){
                    this.previewdGroupEdits[idx] = e;
                } else {
                    this.previewdGroupEdits.push(e);
                }*/
            }
        }
        store._.loadingData = 'done';
    }

    public async formalizeRewrittenExamples(rid: string): Promise<void> {    
        store._.loadingData = 'pending';
        await store._.formalizeRewrittenExamples(rid);
        this.msgSave = 'Saved!';
        store._.loadingData = 'done';
    }



    public renderPreviewGroups(rewrite: RewriteRule): JSX.Element {
        console.log(this.previewdGroupRewrites);
        const list = this.previewdGroupRewrites
            .filter(d => d.rid === rewrite.rid)
            .map((d) => {
                const id = `e:${d.rid}-g:${d.group}`;
                const count = 
                    d.counts.flip_to_correct + 
                    d.counts.flip_to_incorrect + 
                    d.counts.unflip;
                const totalCount = store._.dataGroupStore[d.group].getCount() || 0;
                const btn = <Tooltip 
                    title={`${count > 0 ? 'See' : 'Apply' } the rewrite on ${d.group}`}>
                    <Icon twoToneColor='blue' type='edit'
                        theme="twoTone" style={{cursor: 'pointer'}}
                        onClick={ () => {
                        this.rewriteGroupInstances(d.rid, d.group);
                        //store.activeCmd = predicate;
                        } } /></Tooltip>
                const value: Value = {
                    name: d.rid, counts: {
                        flip_to_correct: d.counts.flip_to_correct,
                        flip_to_incorrect: d.counts.flip_to_incorrect,
                        other: d.counts.unflip
                    }
                }
                const proportion = totalCount === 0 ? 0 : count / totalCount;
                return <Row key={id} gutter={20}>
                    <Col span={2}>{btn}</Col>
                    <Col span={6}><b className='ellipsis'>{d.group}</b></Col>
                    <Col span={10}>{count} rewritten / {totalCount} in total ({utils.percent(proportion)})</Col>
                    <Col key={id} span={6} style={{height: 20}} id={id}>
                    <ResizeAware style={{ position: 'relative' }}>
                        {({ width, height }) => {
                        return<GroupBar
                            isPreview={false}
                            anchorPredictor={store._.anchorPredictor}
                            width={width} height={20} key={width}
                            containerId={id}
                            values={[value]} 
                            showPercent={true} />}}
                        </ResizeAware>
                    </Col>
                    <Col span={24} ><Divider style={{margin: 8}}/></Col>
                    </Row>
            })
        return <div className='full-width full-height overflow'>{list}</div>    
       }

    public renderRewrittenReturns(): JSX.Element {
        if (!this.inspectRewrite) {
            return null;
        }
        if (this.returnedRawRewrites.length === 0) {
            return <p style={{margin: 30, textAlign: 'center'}}>No rewritten instances displayed!</p>
        }
        return <Row className='full-height overflow'>
            {this.returnedRawRewrites.map(raw => {
                return store._.dataType === 'qa' ?
                    <RawRewritePreviewQA rewrittenReturned={raw} key={raw.qid}/>: 
                    <RawRewritePreview rewrittenReturned={raw} key={raw.qid}/>
            })}
        </Row>
    }

    public renderActionButtons(canCreate: boolean): JSX.Element {
        return <div style={{ textAlign: 'center' }}>
            {canCreate ? <Button type='primary'
                onClick={() => { this.create()}}>
                { this.inspectRewrite ? 'Rewrite' : 'Create'} rule
            </Button> : null}
        <Button type='primary' disabled={this.inspectRewrite === null} 
            onClick={() => { 
                store._.deleteBuilt(this.inspectRewrite.rid, 'rewrite');
                this.inspectRewrite = null;
                this.returnedRawRewrites = [];
            }}>
            Delete the rewrite rule
        </Button>
        <div>{this.msg}</div>
    </div>
    }

    private renderRewriteInspectPanel(): JSX.Element {
        if (!this.inspectRewrite) {
            return null;
        }
        const count = this.inspectRewrite.getCount();
        const totalCount = store._.totalSize;
        const proportion = totalCount === 0 ? 0 : count / totalCount;
        return <Row className='full-height full-width' gutter={30} >
            <Col span={12} className='full-height'>
                <Row><span className='info-header'>NAME</span>: {this.inspectRewrite ? this.inspectRewrite.rid : this.props.rewriteName}</Row>
                <Row><span className='info-header'>COUNT</span>: {count} ({utils.percent(proportion)})</Row>
                <Row>
                    <span className='info-header'>DESCRIPTION</span>: 
                    {this.inspectRewrite.description}
                </Row>
                <Row>{ this.renderActionButtons(false) } </Row>
                <Row>
                    Try the rewrite rule on <InputNumber size='small' key={store._.totalSize}
                        min={0} max={store._.totalSize} value={store._.rewriteTestSize}
                        onChange={(d: number) => {
                            store._.rewriteTestSize = d < 0 ? 0 : 
                                d > store._.totalSize ? store._.totalSize : d;
                        }} /> random instances from the selected group...
                </Row>
                <Row><span className='info-header'>Groups</span></Row>
                <Row  style={{left: 30, right: 30, 
                        top: 170, bottom: 0, position: 'absolute'}}>
                
                {this.renderPreviewGroups(this.inspectRewrite)}
                </Row>
                </Col>
                <Col span={12} className='full-height'>
                    <div className='info-header'>Applied Raw Rewrites</div>
                    <div className='full-width overflow' 
                    style={{left: 30, right: 0, 
                        top: 25, bottom: 0, position: 'absolute'}}>
                        {this.renderRewrittenReturns()}</div>
                    {/*confirmButton*/}
                    {/*
                    <div style={{ textAlign: 'center' }}>
                    <Button type='primary' disabled={this.inspectEdit === null} 
                        onClick={() => { 
                            store._.getUpdatedEdit(this.inspectEdit.rid);
                        }}>Confirm the edits
                    </Button>
                    </div>*/}
                </Col>
            </Row>
    }

    private renderCreatRewrites(): JSX.Element {
        const titles = {
            "fromCmd": "Change from pattern",
            "toCmd": "Change to pattern",
            "targetCmd": "Apply the change to"
        }
        const modal = (target: "fromCmd"|"toCmd"|"targetCmd") => {
            return <Row style={{ marginBottom: 16 }}>
                <Col span={8}><div className='info-header'>
                    {titles[target]}
                </div></Col>
                <Col span={16}>
                { store._.dataType === 'vqa' && target === 'targetCmd' ? 
                    this.renderTargetSelectList() : 
                    <QueryCoder 
                        cmd={ this[target] } 
                        readOnly={ false } 
                        changeCmd={ (d) => { this.setInfo(d, target) } }
                    multiLines={ true } />}
                    </Col>
            </Row>}
        return <Row 
            className='full-height full-width'>
            { modal("targetCmd") }
            { modal("fromCmd") }
            { modal("toCmd") }
            { this.renderActionButtons(true) }
            <div className='full-width overflow' 
            style={{ top: 200, bottom: 0, position: 'absolute'}}>
                {this.renderRewrittenReturns()}
            </div>
        </Row>
    }

    public globalProceedBtn(): JSX.Element {
        let btn: JSX.Element = null;
        if (this.inspectRewrite) {
            if (this.confirmedPatternPreview) {
                btn = <Button  type='primary' size='small'  onClick={() => {  
                    this.formalizeRewrittenExamples(this.inspectRewrite.rid); }}>
                    Save the rewritten instances</Button>
            } else {
                btn = <Button type='primary' size='small' 
                    onClick={() => {
                        this.returnedRawRewrites = [];
                        this.confirmedPatternPreview = true; 
                    }}
                >Confirm the rewrite rule</Button>
            }
        }
        return btn;
    }

    public render(): JSX.Element {
        const up = this.inspectRewrite === null || !this.confirmedPatternPreview ?
            this.renderCreatRewrites() :
            this.renderRewriteInspectPanel();
        let sides = this.inspectRewrite === null || !this.confirmedPatternPreview ?
            document.body.clientWidth * 0.45 - 500 : 0;
        sides = sides > 0 ? sides : 0;
        return <div className='full-width full-height'>
            <div style={{left: sides, right: sides, 
                top: 0, bottom: 50, position: 'absolute'}}>{up}</div>
            <div style={{
                textAlign: 'center',
                bottom: 20, left: 0, right: 0, 
                position: 'absolute'}}>
                {this.globalProceedBtn()}
                <div>{this.msgSave}</div>
                </div>
        </div>;
    }
}