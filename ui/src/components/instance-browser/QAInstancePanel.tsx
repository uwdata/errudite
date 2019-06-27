/**
 * wtshuang@cs.uw.edu
 * 2018/01/14
 * The panel for the question
 */

import * as React from 'react';
import { action, observable } from 'mobx';
import { observer } from 'mobx-react';
import { Divider, Row, Button,  Modal, Collapse, Spin } from 'antd';

import { QAAnswer, VQAAnswer } from '../../stores/Answer';
import { Context } from '../../stores/Context';

import { Token, Indicator } from '../../stores/Interfaces';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

import { ContextPanel } from './ParagraphPanel';
import { RewriteTemplateName } from '../shared-components/RewriteTemplateName';
import { FreeRewritePanel } from '../free-rewrites/FreeRewritePanel';
import { QAInstanceKey } from '../../stores/InstanceKey';
import { InstancePanel } from './InstancePanel';
import { Question, VQAQuestion } from '../../stores/Question';

export interface InstanceProps {
    // an array of identifiers with the same qid
    instances: QAInstanceKey[];
}

@observer
export class QAInstancePanel extends InstancePanel {
    public contexts: Context[];
    public oriContext: Context;
    public cid: number;
    public aid: number;
    @observable public cinput: string;
    // indicators
    // @observable
    public indicators: Indicator[];
    // suggest filters
    @observable public filterMetas: string[];
    

    constructor (props: any, context: any) {
        super(props, context);
        // identifiers
        this.instances = this.props.instances.sort((a, b) => a.vid - b.vid);
        if (this.instances.length === 0) {
            return;
        }
        this.oriInstance = this.instances.filter(i => i.vid === 0)[0];
        // ids and save the orignal identifiers
        this.getFilteredInfo(0);
        // the observable instances
        this.rewriteable = false;
        this.displayRewrite = false;
        this.indicators = [];
        this.filterMetas = [];
        this.vid = 0;
        this.selected = false;

        this.paragraphRewriteHandler = this.paragraphRewriteHandler.bind(this);
        this.questionRewriteHandler = this.questionRewriteHandler.bind(this);
        this.setIndicators = this.setIndicators.bind(this);
        this.setRewriteable = this.setRewriteable.bind(this);
        this.onSetFreeformRewrite = this.onSetFreeformRewrite.bind(this);
        this.setSuggestion = this.setSuggestion.bind(this);

    }


    /**
     * get the paragraph w/ ids and vid. If this version does not exist, jut 0.
     * @param {number} aid the article id
     * @param {number} cid the paragraph id
     * @param {string} qid the question id
     * @param {number} vid the version id
     * @return a paragraph instances with the qid.
     */
    public getContext (aid: number, cid: number, qid: string, vid: number = 0): Context {
        //console.log(this.context);
        const ids = vid === 0 ? [vid] : [vid, 0];
        for (var i = 0; i < ids.length; i++) {
            const pArr: Context[] = this.contexts
            .filter((p: Context) => {
                const check: boolean = p.aid === aid && p.cid === cid && p.vid === ids[i];
                return ids[i] === 0 ? check : check && p.qid === qid;
            });
            if (pArr.length > 0) { return pArr[0]; }
        }
        return null;
    }


    /**
     * Compute the aid, pid, qid
     * @param {number} vid the vid for computing the others
     */
    public getFilterIds(vid: number): void {
        if (vid === -1) { return; }
        const instance = this.getInstance(vid) as QAInstanceKey;
        if (!instance) {
            return;
        } else {
            this.aid = instance.aid;
            this.cid = instance.cid;
            this.qid = instance.qid;
        }
    }

    /**
     * Wrapper function to gather all the filter info.
     * @param {number} vid the vid for computing the others
     */
    @action public getFilteredInfo(vid: number): void {
        // get the id

        this.getFilterIds(vid);
        this.questions = (store._.questions as (VQAQuestion|Question)[]).filter(q => q.qid === this.qid);
        this.contexts = store._.contexts.filter(
            p => p.aid === this.aid && p.cid === this.cid);

        this.answers = (store._.answers as (VQAAnswer|QAAnswer)[]).filter(a => a.qid === this.qid);
        this.groundtruths = this.getGroundtruths(this.qid, vid);
        // get the display info.
        this.oriQuestion = this.getQuestion(this.qid, 0);
        this.oriContext = this.getContext(this.aid, this.cid, this.qid, 0);
        this.qinput = this.oriQuestion.textize();
        this.cinput = this.oriContext.textize();
        this.vid = vid;


    }

    /**
     * Render the paragraph block.
     */
    protected renderContext(vid: number): JSX.Element {
        const instance = this.getInstance(vid);
        if (!instance) { return null; }
        const ptokens = utils.computeRewrite(
            this.oriContext.doc,
            this.getContext(this.aid, this.cid, this.qid, vid).doc) as Token[];
        const indicators = this.indicators.filter(i => i.target === 'paragraph');
        const elementClass = utils.genClass('qa-instance', 'ppanel', [this.qid, vid, String(this.rewriteable)]);
        return <ContextPanel
            qid = { this.qid }
            instance={ instance }
            key={ elementClass.key }
            setSuggestion={ this.setSuggestion }
            indicators= {indicators}
            rewriteable={ false }
            groundtruths= { this.getGroundtruths(this.qid, vid) as QAAnswer[] }
            predictions={ this.getPredictions(this.qid, vid) as QAAnswer[] }
            ptokens={ ptokens }
            pinput={ this.cinput }
            rewriteHandler={ this.paragraphRewriteHandler }
        />
    }

    /**
     * Render the rewrite pop up panel
     * @param {string} testedEditName the rewrite tested. For compute the opened new panel.
     */
    public renderEditPanel(): JSX.Element {
        if (!this.displayRewrite) { return null; }
        const rewriteNamesInIdentifiers = this.props.instances.map(i => i.rid);
        const rewriteNamesInStore = store._.rewriteHashes.slice();
        const rewriteNames = rewriteNamesInStore.filter(e => rewriteNamesInIdentifiers.indexOf(e) === -1);
        const prediction = this.getPrediction(this.qid, 0, store._.anchorPredictor);
        return <Modal
            title={`Augmented versions of the selected instance`}
            style={{ 
                top: document.body.clientHeight * 0.05,
                height: document.body.clientHeight * 0.8}}
            destroyOnClose={true}
            footer={null}
            width={document.body.clientWidth * 0.9}
            visible={this.displayRewrite}
            onOk={() => {this.displayRewrite = false;} }
            onCancel={() => { 
                this.rewriteable = false; this.displayRewrite = false;
                const hashes = store._.sampledInstances.map(k => k.key())
                for (let key of this.instances) {
                    if (hashes.indexOf(key.key()) === -1) {
                        store._.sampledInstances.push(key);
                    }
                }
            }}>
            <Spin className='full-height full-width' size='large' 
                spinning={store._.loadingData === 'pending'}>
            <Row className='full-width overflow' style={{
                height: document.body.clientHeight * (this.rewriteable ? 0.2 : 0.6 )}}>
                <Collapse defaultActiveKey={[`${this.vid}`]}>
                    {this.instances.map(instance => {
                        const loadToFreeEditIcon = <Button disabled={this.rewriteable}
                            shape='circle' type='primary' icon='export' size='small'
                            onClick={ () => { this.onSetFreeformRewrite(instance.vid) } }/>
                        const header = <div>
                                <RewriteTemplateName rewriteName={instance.rid} rewrite={null} />
                                {` `}{loadToFreeEditIcon}</div>
                        const prediction = this.getPrediction(this.qid, instance.vid, store._.anchorPredictor);
                        return <Collapse.Panel
                            style={{background: prediction !== null && 
                                (prediction as QAAnswer).getPerform() < 1 ? '#fdae6b' : null }}
                            header={header} 
                            key={`${instance.vid}`}>
                            { this.renderQuestion(instance.vid) }
                            { this.renderContext(instance.vid) }
                            </Collapse.Panel>
                    })}                    
                </Collapse>
            </Row>
            {this.rewriteable ? 
                <Row className='full-width' style={{height: document.body.clientHeight * 0.4 - 30, marginTop: 30}}>
                    <FreeRewritePanel 
                        key={ this.qinput + this.cinput }
                        rewriteNames={ rewriteNames }
                        qinput={this.qinput }
                        cinput={this.cinput }
                        predictorName={store._.anchorPredictor}
                        prediction={prediction}
                        groundtruths={this.groundtruths.map(g => g.textize())}
                        onSwitchNewVersion={ this.switchVersion }
                        onCancelRewrite={this.setRewriteable }
                        qid={this.qid} />
                </Row> : null        
            }
            </Spin>
        </Modal>
    }

    /**
     * Interaction. rewrite the paragraph raw text. Passed onto paragraph panel
     * @param pinput: <string> the import string
     */
    public paragraphRewriteHandler (pinput: string): void {
        this.cinput = pinput;
    }
    @action public setIndicators(indicators: Indicator[]): void {
        this.indicators = indicators.slice();
    }

    /**
     * The main rendering function
     */
    public render(): JSX.Element {
        const elementClass = utils.genClass('qa-instance', 'qcell', this.qid);
        let display: JSX.Element = null;
        if (store._.browserTarget === 'group') {
            display = <Row>
                { this.renderQuestion(0) }
                { this.renderContext(0) }
            </Row>
        } else {
            //  i.etype.rid === store.sampleEdit || 
            const instances = this.instances.filter(i =>i.vid === 0 || i.rid === store._.sampleRewrite);
            const sampleEdit = store._.sampleRewrite ? store._.sampleRewrite : "unrewritten";
            display = <Collapse defaultActiveKey={[sampleEdit]}>
                {instances.map(instance => {
                    const prediction = this.getPrediction(this.qid, instance.vid, store._.anchorPredictor);
                    const header = <RewriteTemplateName 
                    rewriteName={instance.rid} rewrite={null} />
                    return <Collapse.Panel 
                        header={header} 
                        style={{background: prediction !== null && (prediction as QAAnswer).getPerform() < 1 ? 
                            utils.answerColor.incorrect.light : utils.answerColor.correct.light }}
                        key={instance.rid}>
                        { this.renderQuestion(instance.vid) }
                        { this.renderContext(instance.vid) }
                        </Collapse.Panel>
                })}
            </Collapse>;
        }
        return <Row key={ elementClass.key } className={ `${elementClass.total} full-width` }>
            {display}
            { this.renderInfoButton() }
            { this.renderSuggestFilter() }
            <Divider />
            { this.renderEditPanel() }
        </Row>;
    }
}