/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the question. Integrated in instance panel.
 */

import * as React from 'react';
import { observer } from 'mobx-react';

import { Answer } from '../../stores/Answer';
import { Token } from '../../stores/Interfaces';
import { Question } from '../../stores/Question';
import { Context } from '../../stores/Context';
import { InstanceKey } from '../../stores/InstanceKey';

export interface BlockPopupProps {
    target: string; // question, paragraph, answer
    token?: Token;
    instance: InstanceKey;
    question?: Question;
    paragraph?: Context;
    answer?: Answer;
    groundtruths?: Answer[];
}

@observer
export class BlockPopup extends React.Component<BlockPopupProps, {}> {

    constructor (props: BlockPopupProps, context: any) {
        super(props, context);
    }

    private showTags(type: string, token: Token): JSX.Element {
        if (token === undefined || token === null || (type in token && token[type] === '')) {
            return null;
        } else {
            const data = <div ><b>{type.toLocaleUpperCase()}</b>: {token[type]}</div>
            return data;
        }
    }

    private infer(): JSX.Element {
        const token = this.props.token;
        const popup: JSX.Element = <span>
            {this.showTags('ner', token)}
            {this.showTags('pos', token)}
            {this.showTags('lemma', token)}
        </span>;
        return popup;
    }
    /**
     * Render the question bar.
     */
    public render(): JSX.Element {
        return this.infer();
    }
}