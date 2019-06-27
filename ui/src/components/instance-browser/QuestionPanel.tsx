/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the question. Integrated in instance panel.
 */

import * as d3 from 'd3';
import * as React from 'react';
import { observer } from 'mobx-react';
import { Tooltip, Input } from 'antd';
import { Token, Indicator, Annotation } from '../../stores/Interfaces';
import { utils } from '../../stores/Utils';
import { BlockPopup } from './BlockPopup';
import { InstanceKey } from '../../stores/InstanceKey';

export interface AttentionDatum {
    predictor: string;
    attention: number[];
}

export interface QuestionProps {
    rewriteable: boolean; // this item
    instance: InstanceKey;
    qid: string;
    indicators: Indicator[];
    qtokens: Token[];
    qinput: string;
    rewriteHandler: (d: string) => void;
    setSuggestion: (instance: InstanceKey, target: 'question'|'context') => void;
}

@observer
export class QuestionPanel extends React.Component<QuestionProps, {}> {
    // view related
    private viewType: string;
    // imported from the upper view
    private qid: string
    private qtokens: Token[];
    // input
    private qinput: string;
    // imported function
    private rewriteHandler: (d: string) => void = this.props.rewriteHandler;
    

    constructor (props: QuestionProps, context: any) {
        super(props, context);
        this.viewType = 'qpanel';
        this.qtokens = this.props.qtokens;
        this.qid = this.props.qid;
        // initiate the input
        this.qinput = this.props.qinput;
    }


    public renderToken(t: Token, idx: number): JSX.Element {
        // generate the current class for the token
        // mark how is the editting

        const rewriteClass = `token-rewrite-${t.etype}`;
        // get the current span
        const curClass = utils.genClass(this.viewType, 'qtoken', [
            this.qid, utils.genStrId(t.text), `${t.etype}`, t.idx]);
        const annotations: Annotation[] = d3.merge(this.props.indicators.map(i => i.annotations));
        const idxHash = annotations.map(a => a.tidx);
        let annotation = '';
        if (idxHash.indexOf(t.idx) > -1 && t.etype !== 'remove') {
            annotation = annotations[idxHash.indexOf(t.idx)].annotate.toString();
        }
        const curSpan: JSX.Element = <span 
            onSelect={(e ) => { console.log(e) }}
            key={ curClass.key }
            className={ `token ${curClass.total} ${rewriteClass}` }>
            <div style={{paddingTop: 1, verticalAlign: 'bottom'}} 
                className='token-info-block'>{annotation.toUpperCase()}</div>
            <div style={{
                paddingTop: 0, marginTop: -5, paddingBottom: 0, marginBottom: 0,
            }}>
            <b id={ curClass.key }>{ t.text + t.whitespace }</b></div></span>;
        
        const popup: JSX.Element = <BlockPopup 
            target='question' token={t} instance={this.props.instance}/>;
        return (
            <Tooltip key={idx} style={{ width: 500 }} title={popup}
                trigger="hover">
                {curSpan}
            </Tooltip>
        )
        
       return curSpan;
    }
    
    /**
     * Render the question bar.
     */
    public render(): JSX.Element {
        if (this.props.rewriteable) {
            // this part will be an input box
            const elementClass = utils.genClass(this.viewType, 'qinput', this.qid);
            return <div className='full-width'><Input
                key={ elementClass.key }
                className={ `${elementClass.total} full-width` }
                defaultValue={ this.qinput }
                onChange={(e: React.SyntheticEvent<HTMLInputElement>) => { 
                    this.rewriteHandler((e.target as HTMLInputElement).value); 
                }}/></div>
        } else {
            return <div className={'full-width'} onMouseUp={() => {
                this.props.setSuggestion(this.props.instance, 'question');
            }}>{this.qtokens.map((t: Token, idx: number) => this.renderToken(t, idx))}</div>;
        }
    }
}