/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the paragraph. Integrated in instance panel.
 */

import * as d3 from 'd3';
import * as React from 'react';
import { observer } from 'mobx-react';

import { Tooltip, Input, Alert } from 'antd';
import { QAAnswer } from '../../stores/Answer';
import { store } from '../../stores/Store';
import { Token, Indicator, Annotation } from '../../stores/Interfaces';
import { utils } from '../../stores/Utils';
import { InstanceKey } from '../../stores/InstanceKey';

export interface ContextProps {
    qid: string;
    rewriteable: boolean; // if this paragraph is under edting
    instance: InstanceKey;
    groundtruths: QAAnswer[];
    predictions: QAAnswer[];
    ptokens: Token[];
    pinput: string;
    rewriteHandler: (d: string) => void;
    setSuggestion: (identifier: InstanceKey, target: 'question'|'context') => Promise<void>;
    indicators: Indicator[];
}

@observer
export class ContextPanel extends React.Component<ContextProps, {}> {
    // view related
    private viewType: string;
    // imported from the upper view
    private rewriteable: boolean;
    private qid: string;
    private selectedAnswer: QAAnswer;
    private ptokens: Token[];
    // input
    private pinput: string;
    // imported function
    private editHandler: (d: string) => void;

    private groundtruths: QAAnswer[];
    private predictions: QAAnswer[];
    private predictionCountColor:  d3.ScaleOrdinal<number, string>;
    
    constructor (props: ContextProps, context: any) {
        super(props, context);
        this.viewType = 'ppanel';
        this.qid = this.props.qid;
        this.rewriteable = this.props.rewriteable;

        this.ptokens = this.props.ptokens;
        this.editHandler = this.props.rewriteHandler;
        // initiate the input
        this.pinput = this.props.pinput;

        this.groundtruths = this.props.groundtruths;
        this.predictions = this.props.predictions;
        this.predictionCountColor = d3.scaleOrdinal<number, string>(d3.schemeGreys[9].slice(1))
                .domain(d3.range(1, 1 + store._.selectedPredictors.length));
        this.selectedAnswer = null;
    }

    /**
     * get the color for a given t, based on the currently selected answer
     * @param {Token} t the targeting token.
     * @param answers <Answer[]> the answers
     * @return <string> a color.
     */
    private answerUnderlineFunc (t: Token, selectedAnswer: QAAnswer): string {
        let undelineCls = '';
        if (t.etype !== 'remove' && selectedAnswer !== undefined && selectedAnswer !== null) {
            if (selectedAnswer.span_start <= t.idx && selectedAnswer.span_end > t.idx) {
                undelineCls = 'primary-answer';
            }
            undelineCls += selectedAnswer.getPerform()  === 1 ? ' correct' : ' incorrect';
        }
        return undelineCls;
    }
    

    /**
     * get the background color for a given t, based on the currently selected answer
     * @param t <Token> the targeting token.
     * @return <string> a color.
     */
    private answerBackgroundColorFunc (t: Token, predictions: QAAnswer[]): string {
        // color the tokens based on how many predictors predict it to be an answer
        let color = 'rgba(255, 255, 255, 0)';
        const overlappedPredictions = predictions.filter(a => 
            a !== undefined && store._.selectedPredictors.indexOf(a.model) > -1 && 
            a.span_start <= t.idx && a.span_end > t.idx);
        if (t.etype !== 'remove' && overlappedPredictions.length > 0) {
            color = this.predictionCountColor(overlappedPredictions.length);
        }
        return color;
    }


    public renderTokens(sentenceGroups: {[key: string]: Token[]}, sid: string): JSX.Element {
        const curClass = utils.genClass(this.viewType, 'psentence', [this.qid, sid]);
        return <div key={curClass.key}>{sentenceGroups[sid].map((t: Token, idx: number) => {
            // generate the current class for the token
            const editClass = `token-rewrite-${t.etype}`;
            const curClass = utils.genClass(this.viewType, 'ptoken', 
                [this.qid, utils.genStrId(t.text), `${t.etype}`, t.idx]);
            let answerToken: string = '';
            this.groundtruths.forEach(a => {
                if (a !== undefined && a.span_start <= t.idx && a.span_end > t.idx) {
                    answerToken = 'groundtruth';
                    return;
                }
            });
            const annotations: Annotation[] = d3.merge(this.props.indicators.map(i => i.annotations));
            const idxHash = annotations.map(a => a.tidx);
            let annotation: string = '';
            if (idxHash.indexOf(t.idx) > -1 && t.etype !== 'remove') {
                annotation = annotations[idxHash.indexOf(t.idx)].annotate.toString();
            }
            // get the current span
            const curSpan: JSX.Element = <span 
                key={ curClass.key }
                className={ `token ${editClass} ${curClass.total} ${answerToken}` }>
                    <div style={{paddingTop: 1, verticalAlign: 'bottom'}} className='token-info-block'>{annotation.toUpperCase()}</div>
                    <div 
                        id={ curClass.key }
                        className={ `token ${editClass} ${curClass.total} ${answerToken} ${this.answerUnderlineFunc(t, this.selectedAnswer)}` }
                        style={{paddingTop: 0, marginTop: -5, paddingBottom: 0, marginBottom: 0,
                            backgroundColor: this.answerBackgroundColorFunc(t, this.predictions)}}>
                    { t.text + t.whitespace }</div>
                    </span>;
                 
                    const popup = <span>
                    <b>NER: </b>{t.ner} | 
                    <b>POS: </b>{t.pos} | 
                    <b>LEMMA: </b>{t.lemma}</span>;
                    return t.etype === 'remove' ? curSpan: 
                        <Tooltip placement="top"  key={ `${curClass.key}-popup` } title={popup}>{curSpan}</Tooltip>;
                    
                return curSpan;
            })}</div>
    }

    /**
     * Render the paragraph.
     */
    public render (): JSX.Element {
        const temp = this.predictions.filter(p => p.model === store._.anchorPredictor);
        if (temp.length > 0) {
            this.selectedAnswer = temp[0];
        } else {
            this.selectedAnswer = null;
        }
        this.predictionCountColor.domain(d3.range(1, store._.selectedPredictors.length + 1))
        let msg: JSX.Element;
        if (this.rewriteable) {
            // this part will be an input box
            const elementClass = utils.genClass(this.viewType, 'pinput', this.qid);
            msg = <Input.TextArea rows={10}
                key={ elementClass.key }
                className={ `${elementClass.total} full-width` }
                defaultValue={ this.pinput }
                onChange={(e: React.FormEvent<HTMLTextAreaElement>) => 
                    { this.editHandler((e.target as HTMLInputElement).value); }} />
        } else {
            const sentenceGroups: {[key: string]: Token[]} = utils.groupBy<Token>(this.ptokens, 'sid');
            const sids = Object.keys(sentenceGroups).sort((a, b) => parseInt(a, 10) - parseInt(b));
            msg = <div className='full-width' onMouseUp={() => {
                    this.props.setSuggestion(this.props.instance, 'context');
                }}>{sids.map((sid: string) => {
                return this.renderTokens(sentenceGroups, sid);
                })}</div>
        }
        return <Alert className='full-width' message={msg} type='warning' style={{backgroundColor: 'white'}}/>
    }
}