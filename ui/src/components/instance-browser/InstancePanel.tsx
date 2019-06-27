/**
 * wtshuang@cs.uw.edu
 * 2018/01/14
 * The panel for the question
 */

import * as React from 'react';
import { action, observable } from 'mobx';
import { observer } from 'mobx-react';
import { Row, Col, Button, Tooltip, Alert, Icon } from 'antd';

import { Answer, VQAAnswer, QAAnswer } from '../../stores/Answer';
import { Question, VQAQuestion } from '../../stores/Question';

import { Token, Suggestion } from '../../stores/Interfaces';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

import { QuestionPanel } from './QuestionPanel';
import { InstanceKey } from '../../stores/InstanceKey';
import { QueryCoder } from '../shared-components/QueryCoder';

export interface InstanceProps {
    // an array of identifiers with the same qid
    instances: InstanceKey[];
}

@observer
export class InstancePanel extends React.Component<InstanceProps, {}> {
    // instance meta
    public questions: Question[]; // save all the versions
    public oriQuestion: Question; // always save the origin
    // answer related.
    public answers: Answer[]; // total answer saved
    public groundtruths: Answer[]; // the groundtruths
    
    public instances: InstanceKey[];
    public oriInstance: InstanceKey;

    // the ids
    public qid: string;
    @observable public selected: boolean;
    @observable public vid: number;
    // if this panel is freely rewriteable
    @observable public rewriteable: boolean;

    // if we should show the rewritten versions. This is in a modal
    @observable public displayRewrite: boolean; 
    // the inputs from modifications.
    @observable public qinput: string;
    // indicators
    // suggest filters
    @observable public suggestAttr: Suggestion[];
    @observable public showGeneralSuggest: boolean;

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
        this.suggestAttr = [];
        this.showGeneralSuggest = false;
        this.vid = 0;
        this.selected = false;

        this.switchVersion = this.switchVersion.bind(this);
        this.questionRewriteHandler = this.questionRewriteHandler.bind(this);
        this.setRewriteable = this.setRewriteable.bind(this);
        this.onSetFreeformRewrite = this.onSetFreeformRewrite.bind(this);
        this.setSuggestion = this.setSuggestion.bind(this);

    }

    /**
     * Get the identifier based on the vis
     * @param vid 
     */
    public getInstance(vid: number): InstanceKey {
        const instances = this.instances.filter(i => i.vid === vid);
        if (instances.length > 0) { 
            return instances[0];
        } else if (this.instances.length > 0) {
            return this.instances[0];
        }
        return null;
    }

    /**
     * get the question w/ qid and vid. If this version does not exist, jut 0.
     * @param {string} qid the question id
     * @param {number} vid the version id
     * @return a question instances with the qid.
     */
    public getQuestion (qid: string, vid: number = 0): Question {
        const ids = vid === 0 ? [vid] : [vid, 0];
        for (var i = 0; i < ids.length; i++) {
            const qArr: Question[] = this.questions
                .filter((q: Question) => { return q.qid === qid && q.vid === ids[i]; });
            if (qArr.length > 0) { return qArr[0]; }
        }
        return null;
    }

    /**
     * Filter the answer id.
     * @param {string} qid the question id
     * @param {number} vid the version id
     * @return answer instance arr[] associated with the qid, provided by multiple models
     */
    public getPredictions (qid: string, vid: number = 0): Answer[] {
        const aArr: Answer[] = this.answers
            .filter((a: Answer) => { return a.qid === qid 
                && a.vid === vid && !a.isGroundtruth; });
        return aArr;
    }

    public getPrediction (qid: string, vid: number = 0, model: string): Answer {
        const aArr: Answer[] = this.answers
            .filter((a: Answer) => { return a.qid === qid 
                && a.vid === vid && !a.isGroundtruth && a.model === model; });
        return aArr.length > 0 ? aArr[0] : null;
    }

    /**
     * Filter the answer id.
     * @param {string} qid the question id
     * @param {number} vid the version id
     * @return answer instance arr[] associated with the qid, provided by multiple models
     */
    public getGroundtruths (qid: string, vid: number = 0): Answer[] {

        const ids = vid === 0 ? [vid] : [vid, 0];
        for (var i = 0; i < ids.length; i++) {
            const pArr: Answer[] = this.answers
            .filter((p: Answer) => {
                return p.qid === qid && p.isGroundtruth && p.vid === ids[i];
            });
            if (pArr.length > 0) { return pArr; }
        }
        return null;
    }

    /**
     * Compute the aid, pid, qid
     * @param {number} vid the vid for computing the others
     */
    public getFilterIds(vid: number): void {
        if (vid === -1) { return; }
        const identifier = this.getInstance(vid);
        if (!identifier) {
            return;
        } else {
            this.qid = identifier.qid;
        }
    }

    /**
     * Wrapper function to gather all the filter info.
     * @param {number} vid the vid for computing the others
     */
    @action public getFilteredInfo(vid: number): void {
        // get the id
        this.getFilterIds(vid);
        this.questions = (store._.questions as (Question|VQAQuestion)[]).filter(q => q.qid === this.qid);
        this.answers = (store._.answers as (VQAAnswer|QAAnswer)[]).filter(a => a.qid === this.qid);
        this.groundtruths = this.getGroundtruths(this.qid, vid);
        // get the display info.
        this.oriQuestion = this.getQuestion(this.qid, 0);
        this.qinput = this.oriQuestion.textize();
        this.vid = vid;
    }

    /**
     * Render the question bar
     */
    protected renderQuestion(vid: number): JSX.Element {
        const instance = this.getInstance(vid);
        if (!instance) { return null; }
        const qtokens = utils.computeRewrite(
            this.oriQuestion.doc,
            this.getQuestion(this.qid, vid).doc) as Token[];
        const elementClass = utils.genClass(
            'instance-detail', 
            'qpanel', [ this.qid, vid ]);
        return <QuestionPanel
            key={elementClass.key}
            setSuggestion={ this.setSuggestion }
            rewriteable={ false }
            qid= { this.qid }
            qtokens={  qtokens }
            instance= { instance }
            indicators= { [] }
            qinput={ this.qinput }
            rewriteHandler={ this.questionRewriteHandler }
        />
    }

    

    public renderInfoButton(): JSX.Element {
        return (
            <div style={{textAlign: 'right', marginBottom: 15}}>
                <Tooltip title="See attribute information"><Button 
                    shape='circle' icon='info' size='small' className='info-button'
                    style={{backgroundColor: this.selected ? '#31a354' : null}}
                    type={this.selected ? 'primary' : 'default'}
                    onClick={ () => {
                        const nodes = document.getElementsByClassName('info-button');
                        Array.prototype.forEach.call(nodes, function(node) {
                            node.style.backgroundColor = null
                        });
                        if (this.selected) {
                            this.selected = false;
                            store._.highlightedInstances = [];
                        } else {
                            this.selected = true;
                            store._.highlightedInstances = this.instances.filter(
                                i => store._.browserTarget !== 'group' || i.vid === 0
                            );
                        }
                     } }/></Tooltip>
                     <Tooltip title="See general filter suggestions for finding similar instances..."><Button 
                        shape='circle' icon='filter' size='small' className='info-button'
                        onClick={ () => {
                            console.log(this.qid);
                            this.showGeneralSuggest = true;
                            this.setSuggestionWithIdx(
                                'question', this.qid, this.vid, null, null);
                        } }/></Tooltip>
                {store._.sampleRewrite && store._.browserTarget === 'rewrite' ? null :
                    <Tooltip title="Rewrite the instance"><Button 
                        shape='circle'  icon='edit' size='small' className='info-button'
                        onClick={ () => { this.displayRewrite = true; } } /></Tooltip>  }
            </div>
        )
    }


    public renderSuggestFilter(): JSX.Element {
        if (!this.suggestAttr || this.suggestAttr.length === 0) { return null }
        const showedSuggests = this.showGeneralSuggest ?
            this.suggestAttr : this.suggestAttr.filter( s => 
                s.type !== 'general' && s.type !== 'perform' );
        let content: JSX.Element = null;
        if (showedSuggests.length === 0 && !this.showGeneralSuggest) {
            content = <Row>
                <p>We didn't detect any valuable suggestion from your selected text.</p>
            </Row>
        } else {
            content = <Row>
                <b className='info-header'>Did you mean to filter instances that are...</b>
                {
                    showedSuggests.map(f => {
                    const span = 21;//f.domain ? 12 : 22;
                    const hasCmd = store._.activeCmd.indexOf(f.cmd) > -1 ;
                    const btn = <Tooltip title={`${hasCmd ? 'Remove' : 'Add' } the ${f.type}`}><Icon 
                        twoToneColor={hasCmd ? 'lightgrey' : 'blue'}
                        type={hasCmd ? 'minus-circle' : 'plus-circle'}
                        theme="twoTone" style={{cursor: 'pointer'}}
                        onClick={ () => {
                            if (hasCmd) {
                                store._.setActiveCmd(
                                    store._.refactorCmd(f.cmd, store._.activeCmd, false, false) as string, true, true);
                            }else if (store._.activeCmd.trim() !== '' && !hasCmd) {
                                //predicate.rules.push(store.activeCmd);
                                store._.setActiveCmd(`${store._.activeCmd.trim()} and ${f.cmd}`, true, true);
                            } else if (store._.activeCmd.trim() === '') {
                                store._.setActiveCmd(f.cmd, true, true);
                            }
                            //store.activeCmd = predicate;
                        } } /></Tooltip>
                    return <Row gutter={30} key={f.cmd}>
                        <Col xs={4} sm={2}	lg={1}>{btn}</Col>
                        <Col xs={span-2} sm={span} lg={span+1} >
                            <QueryCoder readOnly={true} cmd={f.cmd} multiLines={false} changeCmd={null} /></Col>
                        { false ? <Col sm={22-span} // f.domain ?
                            className='ant-list-item-meta ant-list-item-meta-description' 
                            >Domain: [ {f.domain.length > 5 ? 
                                f.domain.slice(0, 5).join(', ') + ', ...' :
                                f.domain.join(', ')} ]</Col> : null}
                        </Row>;
                    })}
                </Row>;
        }
        const option_to_see_more = this.showGeneralSuggest && 
            this.suggestAttr.filter( s => s.type === 'general' || s.type === 'perform' ).length > 0 ? null :
        <Row><a onClick={() => {this.showGeneralSuggest = true;} }
            style={{ marginTop: 8, cursor: 'pointer' }}>
                See more general suggestions?</a></Row>
        return  <Alert 
            key={this.suggestAttr.length} 
            message={<Row>{content}{option_to_see_more}</Row>} 
            onClose={ () => { 
                this.suggestAttr = [];
                this.showGeneralSuggest = false;
            }} type="info" closeText="Close Now" />
    }

    /**
     * Interaction. Click on the version tag.
     * @param iid <int> the identifier idx for computing the others
     */
    public switchVersion(key: InstanceKey): void {
        this.instances.push(key);
        this.getFilteredInfo(key.vid);
    }

    /**
     * Interaction. rewrite the question raw text. Passed onto question panel
     * @param qinput: <string> the import string
     */
    public questionRewriteHandler (qinput: string): void {
        this.qinput = qinput;
    }

    @action public setRewriteable(rewriteable: boolean): void {
        this.rewriteable = rewriteable;
    }

    @action public onSetFreeformRewrite(vid: number): void {
        this.qinput = this.getQuestion(this.qid, vid).textize();
        this.rewriteable = true;
        this.vid = vid;
    }

    public getIdxFromId(container): number {
        const node: any = container.firstChild ? container.firstChild : container.parentNode;
        if (!node || !node.id) {
            return -1;
        }
        const elements = node.id.split('-');
        let output = -1;
        let type = null;
        if (elements.length >= 1) {
            output = parseInt(elements[elements.length - 1]);
        }
        if (elements.length >= 2)  {
            type = elements[elements.length - 2]
        }
        return isNaN(output) || type === null || type === "remove" ? -1 : output;
    }

    public async setSuggestionWithIdx(target: string, 
        qid: string, vid: number, startIdx: number, endIdx: number): Promise<void> {
        store._.loadingData = 'pending';
        const suggestAttr = await store._.service.detectBuildBlocks(
            target, qid, vid, startIdx, endIdx + 1);
        this.suggestAttr = suggestAttr === null ? [] : suggestAttr;
        store._.loadingData = 'done';
    }
    public async setSuggestion(instance: InstanceKey, target: string): Promise<void> {
        const selection = window.getSelection();
        const range = selection.getRangeAt(0);
        if (!selection || (selection.rangeCount === 0)) { return; }
        // get the idx of the texts.
        const startIdx = this.getIdxFromId(range.startContainer);
        const endIdx = this.getIdxFromId(range.endContainer);
        if (startIdx === -1 || endIdx === -1) { return; }
        this.showGeneralSuggest = false;
        await this.setSuggestionWithIdx(target, instance.qid, instance.vid, startIdx, endIdx);
    }


    /**
     * The main rendering function
     */
    public render(): JSX.Element {
        return null
    }
}