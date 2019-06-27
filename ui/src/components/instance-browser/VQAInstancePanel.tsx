/**
 * wtshuang@cs.uw.edu
 * 2018/01/14
 * The panel for the question
 */

import * as React from 'react';
import * as d3 from 'd3';
import { action, observable } from 'mobx';
import { observer } from 'mobx-react';
import { Divider, Row, Col, Button,  Modal, Collapse, Spin } from 'antd';

import { QAAnswer, VQAAnswer } from '../../stores/Answer';

import { Indicator } from '../../stores/Interfaces';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { RewriteTemplateName } from '../shared-components/RewriteTemplateName';
import { VQAFreeRewritePanel } from '../free-rewrites/VQAFreeRewritePanel';
import { QAInstanceKey } from '../../stores/InstanceKey';
import { InstancePanel } from './InstancePanel';
import { AnswerPanel } from './AnswerPanel';
import { VQAQuestion } from '../../stores/Question';

export interface InstanceProps {
    // an array of identifiers with the same qid
    instances: QAInstanceKey[];
}

@observer
export class VQAInstancePanel extends InstancePanel {
    // indicators
    @observable public indicators: Indicator[];
    // suggest filters
    @observable public filterMetas: string[];
    @observable public imgStream: any;
    

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

        this.switchVersion = this.switchVersion.bind(this);
        this.setIndicators = this.setIndicators.bind(this);
        this.setRewriteable = this.setRewriteable.bind(this);
        this.onSetFreeformRewrite = this.onSetFreeformRewrite.bind(this);
        this.setSuggestion = this.setSuggestion.bind(this);
        this.imgStream = null;
    }

    public async componentDidMount(): Promise<void> {
        const img_id = (this.oriQuestion as VQAQuestion).imgId;
        this.imgStream = await store._.service.getImg(img_id);
    }

    /**
     * Render the question bar
     */
    private renderAnswer(vid: number): JSX.Element {
        const instance = this.getInstance(vid);
        if (!instance) { return null; }
        const predictions = this.getPredictions(this.qid, vid);
        const elementClass = utils.genClass(
            'instance-detail', 
            'apanel', [ this.qid, vid ]);
        const groundtruths = this.getGroundtruths(this.qid, vid);
        return <AnswerPanel
            key={elementClass.key}
            groundtruths={groundtruths as VQAAnswer[]}
            predictions={predictions as VQAAnswer[]}            
            qid= { this.qid }
            setSuggestion={this.setSuggestion}
            instance= { instance }
        />
    }

    /**
     * Render the rewrite pop up panel
     */
    public renderRwritePanel(): JSX.Element {
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
            width={document.body.clientWidth * 0.9}
            visible={this.displayRewrite}
            footer={null}
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
                        const loadToFreeRewriteIcon = <Button disabled={this.rewriteable}
                            shape='circle' type='primary' icon='export' size='small'
                            onClick={ () => { this.onSetFreeformRewrite(instance.vid) } }/>
                        const prediction = this.getPrediction(this.qid, instance.vid, store._.anchorPredictor);
                        const header = <div>
                                <RewriteTemplateName rewriteName={instance.rid} rewrite={null} />
                                {` `}{loadToFreeRewriteIcon}</div>
                        return <Collapse.Panel
                            style={{background: prediction !== null && 
                                (prediction as QAAnswer).getPerform() < 1 ? '#fdae6b' : null }}
                            header={header} 
                            key={`${instance.vid}`}>
                            { this.renderQuestion(instance.vid) }
                            { this.renderAnswer(instance.vid) }
                            </Collapse.Panel>
                    })}                    
                </Collapse>
            </Row>
            {this.rewriteable ? 
                <Row className='full-width' style={{height: document.body.clientHeight * 0.4 - 30, marginTop: 30}}>
                    <VQAFreeRewritePanel 
                        key={ this.qinput }
                        rewriteNames={ rewriteNames }
                        qinput={this.qinput }
                        cinput={ (this.oriQuestion as VQAQuestion).imgId }
                        predictorName={store._.anchorPredictor}
                        prediction={prediction}
                        groundtruths={
                            d3.merge(this.groundtruths.map((g: VQAAnswer) => {
                                return d3.range(g.count).map(_ => g.textize());
                            }))
                        }
                        onSwitchNewVersion={ this.switchVersion }
                        onCancelRewrite={this.setRewriteable }
                        qid={this.qid} />
                </Row> : null        
            }
            </Spin>
        </Modal>
    }

    @action public setIndicators(indicators: Indicator[]): void {
        this.indicators = indicators.slice();
    }

    public renderImg(): JSX.Element {
        try {
            return <div style={{textAlign:'center'}}>
                <img style={{textAlign:'center', maxHeight: '150px', maxWidth: '100%'}}
                    src={`data:imgage/jpeg;base64,${this.imgStream}`} />
            </div>
        } catch {
            return null;
        }
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
                { this.renderAnswer(0) }
            </Row>
        } else {
            const instances = this.instances.filter(i =>i.vid === 0 || i.rid === store._.sampleRewrite);
            const sampleRewrite = store._.sampleRewrite ? store._.sampleRewrite : "unrewritten";
            display = <Collapse defaultActiveKey={[sampleRewrite]}>
                {instances.map(instance => {
                    const prediction = this.getPrediction(this.qid, instance.vid, store._.anchorPredictor);
                    const header = <RewriteTemplateName 
                    rewriteName={ instance.rid} rewrite={null} />
                    return <Collapse.Panel 
                        header={header} 
                        style={{background: prediction !== null && 
                            (prediction as QAAnswer).getPerform() < 1 ? 
                            utils.answerColor.incorrect.light : utils.answerColor.correct.light }}
                            key={instance.rid}>
                        { this.renderQuestion(instance.vid) }
                        { this.renderAnswer(instance.vid) }
                        </Collapse.Panel>
                })}
            </Collapse>;
        }
        return <Row gutter={30} key={ elementClass.key } className={ `${elementClass.total} full-width` }>
                <Row gutter={30}><Col span={8}>
                { this.renderImg() }
                </Col>
                <Col span={16}>{display}</Col></Row>
                { this.renderInfoButton() }
                <Row>{ this.renderSuggestFilter() }</Row>
            <Divider />
            { this.renderRwritePanel() }
        </Row>;
    }
}