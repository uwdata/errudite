/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the question. Integrated in instance panel.
 */

import * as React from 'react';
import { observer } from 'mobx-react';
import { Alert, Tag } from 'antd';
import { Token } from '../../stores/Interfaces';
import { utils } from '../../stores/Utils';
import { InstanceKey } from '../../stores/InstanceKey';
import { VQAAnswer } from '../../stores/Answer';
import { store } from '../../stores/Store';

export interface QuestionProps {
    instance: InstanceKey;
    qid: string;
    groundtruths: VQAAnswer[]; // the groundtruth of the question
    predictions: VQAAnswer[]; // predicted answers from all the models
    setSuggestion: (instance: InstanceKey, target: string) => void;
}

@observer
export class AnswerPanel extends React.Component<QuestionProps, {}> {
    // view related
    rewriteable: boolean; // this item
    private viewType: string;
    // imported from the upper view
    private qid: string
    private groundtruths: VQAAnswer[];
    private predictions: VQAAnswer[];

    constructor (props: QuestionProps, context: any) {
        super(props, context);
        this.viewType = 'qpanel';
        this.groundtruths = this.props.groundtruths;
        this.predictions = this.props.predictions;
        this.qid = this.props.qid;
    }


    public renderToken(t: Token, idx: number): JSX.Element {
        // generate the current class for the token
        // mark how is the rewriting

        const rewriteClass = `token-rewrite-${t.etype}`;
        // get the current span
        const curClass = utils.genClass(this.viewType, 'qtoken', 
            [this.qid, utils.genStrId(t.text), `${t.etype}`, t.idx]);
        const curSpan: JSX.Element = <span 
            onSelect={(e ) => { console.log(e) }}
            key={ curClass.key }
            className={ `token ${curClass.total} ${rewriteClass}` }>
            <div style={{
                paddingTop: 0, marginTop: -5, paddingBottom: 0, marginBottom: 0,
            }}>
            <b id={ curClass.key }>{ t.text + t.whitespace }</b></div></span>;
        /*
        const popup: JSX.Element = <BlockPopup 
            target='question' token={t} instance={this.props.instance}/>;
        return (
            <Tooltip key={idx} style={{ width: 500 }} title={popup}
                trigger="hover">
                {curSpan}
            </Tooltip>
        )*/
        return curSpan;
    }


    public renderAnswer(answer: VQAAnswer): JSX.Element {
        let color = null;
        if (!answer.isGroundtruth) {
            if (answer.model === store._.anchorPredictor) {
                color = answer.perform.accuracy === 1 ? 
                    utils.answerColor.correct.dark :
                    utils.answerColor.incorrect.dark;
            } else {
                color = answer.perform.accuracy === 1 ? 'blue' : 'volcano';
            }
        }
        return <Tag
            key={answer.key + answer.textize()} color={color}>
            <span>{answer.model}:</span>
            <span onMouseUp={() => {
                if (answer.isGroundtruth) {
                    this.props.setSuggestion(this.props.instance, `${answer.model}::${answer.textize()}`);
                } else {
                    this.props.setSuggestion(this.props.instance, answer.model);
                }
            }}>{answer.doc.map((t: Token, idx: number) => this.renderToken(t, idx))}</span>
            { answer.isGroundtruth ?  <i> ( * {answer.count})</i> : null }
        </Tag>
    }
    
    /**
     * Render the question bar.
     */
    public render(): JSX.Element {
        const msg = <div>
            <div style={{marginBottom: 16}}>
             {this.groundtruths.map(answer => this.renderAnswer(answer) )}</div>
            <div>{this.predictions
                .filter(p => store._.selectedPredictors.indexOf(p.model)> -1)
                .map(answer => this.renderAnswer(answer) )}</div>

        </div>;
        return <Alert className='full-width' message={msg} type='warning' style={{backgroundColor: 'white'}}/>
    }
}