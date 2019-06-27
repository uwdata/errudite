import * as React from 'react';
import { utils } from '../../stores/Utils';
import { RewrittenReturn, Token } from '../../stores/Interfaces';
import { Alert, Divider } from 'antd';

interface RawRewritePreviewProps {
    rewrittenReturned: RewrittenReturn;
}

export class RawRewritePreview extends React.Component<RawRewritePreviewProps, {}> {
    public viewType: string;
    public rawRewrite: RewrittenReturn;
    constructor(props: any, context: any) {
        super(props, context);
        this.viewType = 'rewrite-preview';
        this.rawRewrite = this.props.rewrittenReturned;

    }

    public renderToken(t: Token): JSX.Element {
        // generate the current class for the token
        // mark how is the rewritting
        const rewriteClass = `token-rewrite-${t.etype}`;
        // get the current span
        const curClass = utils.genClass(this.viewType, 'token', [utils.genKeywordId(t.text), t.idx]);
        const curSpan: JSX.Element = <span key={ curClass.key }
            className={ `token ${curClass.total} ${rewriteClass}` }
            id={ curClass.key }>{ t.text + ' ' }</span>;
        return curSpan;
    }

    public renderQuestion(): JSX.Element {
        const qtokens = utils.computeRewriteStr(
            this.rawRewrite.ori_instance.question, this.rawRewrite.rewrite_instance.question
        );
        return <div className={'full-width'}>
            <b>{qtokens.map((t: Token, idx: number) => 
            this.renderToken(t))}</b></div>;
    }

    public renderPrediction(): JSX.Element {
        const instancePrediction = (instance) => {
            const color = instance.perform === 1 ? utils.answerColor.correct.dark : utils.answerColor.incorrect.dark;
            return <span style={{color: color}}>{instance.prediction}</span>
        }

        return <div className={'full-width'}>
            {instancePrediction(this.rawRewrite.ori_instance)}
            ->
            {instancePrediction(this.rawRewrite.rewrite_instance)}
        </div>
    }

    public render(): JSX.Element {
        return <div className='full-width'>
            {this.renderQuestion()}
            {this.renderPrediction()}
        <div><Divider></Divider></div>
    </div>
    }
}

export class RawRewritePreviewQA extends RawRewritePreview {
    constructor(props: any, context: any) {
        super(props, context);
    }
    public renderContext(): JSX.Element {
        const ptokens = utils.computeRewriteStr(
            this.rawRewrite.ori_instance.context, this.rawRewrite.rewrite_instance.context
        );
        const msg = <div className={'full-width'}>
            {ptokens.map((t: Token, idx: number) => this.renderToken(t))}</div>;

        return <Alert 
        className='full-width' message={msg} type='warning' 
        style={{backgroundColor: 'white'}}/>
    }

    public render(): JSX.Element {
        return <div className='full-width'>
        {this.renderQuestion()}
        {this.renderContext()}
        {this.renderPrediction()}
        <div><Divider></Divider></div>
    </div>
    }
}