/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the question. Integrated in instance panel.
 */

import * as React from 'react';
import { observer } from 'mobx-react';
import { Input, Form } from 'antd';
import { FreeRewritePanel, FreeRewriteProps } from './FreeRewritePanel';

@observer
export class VQAFreeRewritePanel extends FreeRewritePanel {

    constructor(props: FreeRewriteProps, context: any) {
        super(props, context);
    }

    public onRewriteText(
        e: React.SyntheticEvent<HTMLInputElement> | React.FormEvent<HTMLTextAreaElement>,
        type: 'question' | 'context' | 'groundtruth'): void {
        const str = (e.target as HTMLInputElement).value;
        switch (type) {
            case 'question': this.qinput = str; break;
            case 'groundtruth': 
                const groundtruths = str.split(';').map(v => v.trim());
                this.groundtruths = [];
                for (let g of groundtruths) {
                    const split = g.split('*');
                    if (split.length === 2) {
                        for (let i = 0; i < parseInt(split[1]); i++){
                            this.groundtruths.push(split[0])
                        } 
                    } else {
                        this.groundtruths.push(split[0]);
                    }
                }
                break;
        }
        this.getTargetCmd();
    }

    public _getGroundtruthDisplay(): string {
        const keys = {}
        for (let g of this.groundtruths) {
            if (!(g in keys)) {
                keys[g] = 0;
            }
            keys[g]++;
        }
        return Object.keys(keys).map(k => `${k}*${keys[k]}`).join('; ')
    }

    public renderRewriteForm(): JSX.Element {
        const formItemLayout = {
            colon: false,
            labelCol: { xs: { span: 24 }, sm: { span: 8 }, md: { span: 4 }, lg: { span: 4 } },
            wrapperCol: { xs: { span: 24 }, sm: { span: 16 }, md: { span: 20 }, lg: { span: 20 } },
        };
        this.qinput = this.returnedRewrite ? this.returnedRewrite.rewrite_instance.question : this.qinput;
        return <Form
            key={this.returnedRewrite ? 
                this.returnedRewrite.rewrite_instance.question + 
                this.returnedRewrite.rewrite_instance.groundtruths.join() : ''}
            onSubmit={this.onPreviewManualPredict} className='full-width full-height'>
            <Form.Item {...formItemLayout} label='Question'>
                <Input className='full-width' defaultValue={this.qinput} key={this.qinput}
                    onChange={(e) => { this.onRewriteText(e, 'question'); }} />
            </Form.Item>
            <Form.Item {...formItemLayout} label='Groundtruths'>
                <Input className='full-width' key={this.groundtruths.join('; ')}
                    defaultValue={this._getGroundtruthDisplay()}
                    onChange={(e) => { this.onRewriteText(e, 'groundtruth'); }} />
            </Form.Item>
        </Form>;
    }
}