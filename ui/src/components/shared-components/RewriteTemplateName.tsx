import * as React from 'react';
import { Row, Tag, Popover, Icon } from 'antd';
import { RewriteRule } from '../../stores/RewriteRule';
import { Token } from '../../stores/Interfaces';
import { utils } from '../../stores/Utils';
import { store } from '../../stores/Store';
//import { POSs, TAGs, ENTs } from './CustomHighlight';


export const POSs = "ADJ|ADP|ADV|AUX|CONJ|CCONJ|DET|INTJ|NOUN|NUM|PART|PRON|PROPN|PUNCT|SCONJ|SYM|VERB";
export const TAGs = "WRB|WP|WDT|NN|NNP|NP|NNS|NNPS|VB|VBG|VBD|VBN|VBP|VBZ";
export const ENTs = "PERSON|NORP|FACILITY|ORG|GPE|LOC|PRODUCT|EVENT|WORK_OF_ART|LANGUAGE|DATE|TIME|PERCENT|MONEY|QUANTITY|ORDINAL|CARDINAL";

interface RewriteTemplateNameProps {
    rewriteName: string;
    rewrite: RewriteRule;
}

const highlights = [POSs, TAGs, ENTs].join("|");

export class RewriteTemplateName extends React.Component<RewriteTemplateNameProps, {}> {
    private viewType: string;
    constructor(props: any, context: any) {
        super(props, context);
        this.viewType = 'rewrite-template-name';
        
    }

    private renderToken(t: Token): JSX.Element {
        // generate the current class for the token
        // mark how is the editting

        const rewriteClass = `token-rewrite-${t.etype}`;
        // get the current span
        const curClass = utils.genClass(this.viewType, 'token', [utils.genKeywordId(t.text), t.idx]);
        const curSpan: JSX.Element = <span key={ curClass.key }
            className={ `token ${curClass.total} ${rewriteClass}` }
            id={ curClass.key }>{ t.text + ' ' }</span>;
        return curSpan;
    }

    private renderTextPair(atext: string, btext: string): JSX.Element {
        const tokens = utils.computeRewriteStr(atext, btext);
        return <span style={{width: 800}}>{tokens.map(t => this.renderToken(t))}</span>
    }

    private renderRuleName(ruleName: string): JSX.Element {
        const splitName = ruleName.split(' ');
        const spans = [];
        splitName.forEach((token: string, idx: number) => {
            if (token === '[BLANK]') {
                spans.push(<span key={idx}>___ </span>);
            }  else if (token === '->') {
                spans.push(<span key={idx}><Icon type="arrow-right" /> </span>);
            } else {
                spans.push(<b key={idx} 
                    style={{color: highlights.indexOf(token) === -1 ? 'black' : 'grey'}}
                    >{token} </b>);
            }
        });
        return <span>{spans.map(s => s)}</span>
    }

    public renderOtherTag(ruleName: string): JSX.Element {
        return <b>{ruleName}</b>
    }

    public renderPreview(rewrite: RewriteRule): JSX.Element {
        let preview: JSX.Element = null;
        const count = rewrite.getCount();
        const totalCount = store._.totalSize;
        const proportion = totalCount === 0 ? 0 : count / totalCount;
        const texts = rewrite.examples.slice(0, 3).map((t, tidx: number) => 
            <Row key={`text-pairs-${rewrite.rid}-${tidx}`}>{this.renderTextPair(t[0], t[1] )}</Row>);
        preview = <div>
            <div><b style={{color: 'steelblue'}}>EXAMPLES</b></div>
            {texts}</div>
        return <div style={{width: 0.3 * document.body.clientWidth}}>
            <div><b style={{color: 'steelblue'}}>COUNT</b>: {count} ({utils.percent(proportion)})</div>
            <div><b style={{color: 'steelblue'}}>DESCRIPTION</b></div>
            <div className='ant-list-item-meta ant-list-item-meta-description'>{rewrite.description}</div>
            {preview}
        </div>
    }

    public render(): JSX.Element {
        const name = this.props.rewrite ? this.props.rewrite.hash() : this.props.rewriteName;
        let renderedName: JSX.Element = null;
        if (this.props.rewriteName.includes('->') || this.props.rewriteName.includes('[')) {
            renderedName = this.renderRuleName(name);
        } else {
            renderedName = this.renderOtherTag(name);
        }
        
        if (this.props.rewrite) {
            const preview =  this.renderPreview(this.props.rewrite);
            return <Popover placement='rightTop' 
                content={preview} title={name}>{renderedName}</Popover>
        } else {
            return renderedName;
        }
    }
}