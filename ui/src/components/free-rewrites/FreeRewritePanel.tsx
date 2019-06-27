/**
 * wtshuang@cs.uw.edu
 * 2018/01/17
 * The panel for the question. Integrated in instance panel.
 */

import * as React from 'react';
import { observable, action } from 'mobx';
import { observer } from 'mobx-react';
import { Col, Row, Input, Icon, Form, Tooltip, Popover, Button, Checkbox, Divider } from 'antd';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { RewriteRule } from '../../stores/RewriteRule';
import { Token, RewrittenReturn } from '../../stores/Interfaces';
import { RewriteTemplateName } from '../shared-components/RewriteTemplateName';
import { Answer } from '../../stores/Answer';
import { InstanceKey } from '../../stores/InstanceKey';
import { QueryCoder } from '../shared-components/QueryCoder';


export interface FreeRewriteProps {
    qid: string;
    rewriteNames: string[];  // a list of rewrite names 
    groundtruths: string[];
    predictorName: string;
    prediction: Answer;
    qinput: string; // this item
    cinput: string; // this item
    onCancelRewrite: (rewriteable: boolean) => void;
    onSwitchNewVersion: (vid: InstanceKey) => void;
}

@observer
export class FreeRewritePanel extends React.Component<FreeRewriteProps, {}> {
    public qinput: string;
    public cinput: string;
    public groundtruths: string[];
    public versionName: string;
    public returnedRules: RewriteRule[];
    public savedRules: string[];
    public targetCmd: string;
    public setCmdCount: number;
    // what is the raw rewrite return from the backend. Should be used to further call predictions.
    @observable public returnedRewrite: RewrittenReturn;
    // what's the last tested rewrite
    @observable public testedRewriteName: string;
    @observable public returnedPrediction: string;
    @observable public returnedPerform: number;

    constructor(props: FreeRewriteProps, context: any) {
        super(props, context);
        this.groundtruths = this.props.groundtruths;
        this.qinput = this.props.qinput;
        this.cinput = this.props.cinput;
        this.returnedPerform = 0;
        this.returnedRules = [];
        this.targetCmd = 'question';
        this.setCmdCount = 0;

        this.returnedRewrite = null;
        this.testedRewriteName = null;

        this.returnedPrediction = '';
        this.versionName = '';
        this.savedRules = [];
        this.onCancel = this.onCancel.bind(this);
        this.onFormalizePredict = this.onFormalizePredict.bind(this);
        this.setCmd = this.setCmd.bind(this);
        this.generateRule = this.generateRule.bind(this);
    }

    /**
     * Automatically rewrite this specific instance based on selected edit.
     * @param {RewriteRule} rewrite A rewriting template.
     */
    @action public async onAutoRewrite(rewrite: RewriteRule): Promise<void> {
        if (rewrite) {
            store._.loadingData = 'pending';
            const returnedRawRewrite = await store._.service.rewriteOneInstanceByRid(rewrite.rid, this.props.qid);
            this.returnedRewrite = returnedRawRewrite;
            this.testedRewriteName = rewrite.hash();
            store._.loadingData = 'done';
        }
    }

    public setCmd(cmd: string): void {
        this.targetCmd = cmd;
        this.setCmdCount++;
    }
    public async generateRule(): Promise<void> {
        store._.loadingData = 'pending';
        let atext: string, btext: string;
        if (this.targetCmd === 'question') {
            atext = this.props.qinput;
            btext = this.qinput;
        } else if (this.targetCmd === 'groundtruth') {
            atext = this.props.groundtruths[0];
            btext = this.groundtruths[0];
        } else {
            atext = this.props.cinput;
            btext = this.cinput;
        }
        const outputs = await store._.service.detectRuleFromRewrite(
            atext, btext, this.targetCmd);
        if (outputs) {
            this.savedRules = [];
            this.returnedRules = outputs.map(t => {
                return new RewriteRule(
                    t.rid, t.description, t.category, t.target,
                    t.target_cmd, t.counts, t.examples);
            });
        } else {
            return null;
        }
        store._.loadingData = 'done';      
    }


    public async onSaveRules(): Promise<void> {
        // first, save each template into a new rewrite
        const deleteRules = this.returnedRules
            .filter(r => this.savedRules.indexOf(r.rid) === -1);
        const savedRules = this.returnedRules
            .filter(r => this.savedRules.indexOf(r.rid) !== -1);
        
        savedRules.forEach(rewrite => {
            store._.rewriteStore[rewrite.hash()] = rewrite;
        });
        store._.rewriteHashes = Object.keys(store._.rewriteStore).slice();
        // second delete all the other templates in the backend.
        await store._.service.deleteSelectedRules(
            deleteRules.map(t => t.rid)
                .filter(name => this.savedRules.indexOf(name) === -1));
        store._.loadingData = 'done';
        this.returnedRules = [];
        this.savedRules = [];
    }
    public onToggleKeepRules(rid: string): void {
        const idx = this.savedRules.indexOf(rid);
        if (idx > -1) {
            this.savedRules = this.savedRules.splice(idx, 1);
        } else {
            this.savedRules.push(rid);
        }
    }

    public getTargetCmd(): void {
        let cmd = '';
        if (this.qinput !== this.props.qinput) {
            cmd = 'question';
        } else if (this.groundtruths.join(';') !== this.props.groundtruths.join(';')) {
            cmd = 'groundtruth';
        } else if (this.cinput !== this.props.cinput) {
            cmd = 'context';
        }
        this.setCmd(cmd);
    }

    public onRewriteText(
        e: React.SyntheticEvent<HTMLInputElement> | React.FormEvent<HTMLTextAreaElement>,
        type: 'question' | 'context' | 'groundtruth'): void {
        const str = (e.target as HTMLInputElement).value;
        switch (type) {
            case 'question': this.qinput = str; break;
            case 'context': this.cinput = str; break;
            case 'groundtruth': this.groundtruths = str.split(';').map(v => v.trim()); break;
        }
        this.getTargetCmd();
    }

    public async onCancel(): Promise<void> {
        if (this.returnedRules) {
            for (let r of this.returnedRules) {
                await store._.deleteBuilt(r.rid, 'rewrite');
            }
        }
        this.qinput = this.props.qinput;
        this.cinput = this.props.cinput;
        this.groundtruths = this.props.groundtruths;
        this.returnedPerform = 0;
        this.returnedPrediction = '';
        this.versionName = '';
        this.returnedRules = null;
        this.savedRules = [];
        this.props.onCancelRewrite(false);
        store._.loadingData = "done";
    }

    public async onFormalizePredict(): Promise<void> {
        store._.loadingData = 'pending';
        const output = await store._.predictFormalize(
            this.props.qid, this.versionName, 
            this.qinput, this.groundtruths, this.cinput);
        if (output) {
            await store._.formalizeRewrittenExamples(this.versionName);
            this.props.onSwitchNewVersion(output);
        }
        store._.loadingData = 'done';
    }

    public async onPreviewManualPredict(): Promise<void> {
        const output = await store._.service.predictOnManualRewrite(
            this.qinput, this.groundtruths, this.cinput);
        if (output !== null) {
            this.returnedPerform = output.perform;
            this.returnedPrediction = output.prediction;
        }
        store._.loadingData = 'done';
    }

    public renderF1Icon(returnedPrediction: string, perform: number): JSX.Element {
        const color = perform === 1 ? '#52c41a' : '#d62728';
        const msg = perform === 1 ? 'Correct prediction' : 'Incorrect prediction';
        const icon = perform === 1 ? 'check-circle' : 'close-circle';
        return returnedPrediction === '' ? null :
            <Tooltip title={msg}><Icon type={icon} theme="twoTone" twoToneColor={color} className='eval-icon' /></Tooltip>
    }

    public renderChangePredictionIcon(returnedPrediction): JSX.Element {
        const color = returnedPrediction === this.props.prediction.textize() ? '#7f7f7f' : '#d62728';
        const msg = returnedPrediction === this.props.prediction.textize() ? 'Prediction unchanged' : 'Prediction changed';
        return returnedPrediction === '' ? null :
            <Tooltip title={msg}><Icon type='diff' theme="twoTone" twoToneColor={color} className='eval-icon' /></Tooltip>
    }

    public renderConfirmRuleBtn(): JSX.Element {
        return <Button.Group size='small' style={{ marginTop: 10 }}>
            <Button type='primary' onClick={() => { this.onSaveRules() }}>Confirm rules</Button>
            <Button type='primary' onClick={() => { this.onCancel() }}>Delete all returned rules</Button>
        </Button.Group>;
    }
    /**
    * Free-form rewriting
    */
    public renderFreeRewrite(): JSX.Element {
        const content = <div>
            <Input.Search
                placeholder="Name the new version!"
                onSearch={value => {
                    this.versionName = value;
                    this.onFormalizePredict();
                }}
                enterButton={<Button icon='check'></Button>}
                style={{ width: 300 }}
            />
        </div>
        return <Button.Group size='small' style={{ marginTop: 10 }}>
            <Button type='primary' onClick={() => { this.onPreviewManualPredict() }}>Run Prediction</Button>
            <Button type='primary' onClick={() => { this.onCancel() }}>Cancel</Button>
            <Popover content={content} title={null} trigger='click'><Button type='primary'>Save Version</Button></Popover>
        </Button.Group>;
    }


    public renderRewriteForm(): JSX.Element {
        const formItemLayout = {
            colon: false,
            labelCol: { xs: { span: 24 }, sm: { span: 8 }, md: { span: 4 }, lg: { span: 2 } },
            wrapperCol: { xs: { span: 24 }, sm: { span: 16 }, md: { span: 20 }, lg: { span: 22 } },
        };
        this.qinput = this.returnedRewrite ? this.returnedRewrite.rewrite_instance.question : this.qinput;
        this.cinput = this.returnedRewrite ? this.returnedRewrite.rewrite_instance.context : this.cinput;
        return <Form
            key={this.returnedRewrite ? 
                this.returnedRewrite.rewrite_instance.question + 
                this.returnedRewrite.rewrite_instance.context +
                this.returnedRewrite.rewrite_instance.groundtruths.join() : ''}
            onSubmit={this.onPreviewManualPredict} className='full-width full-height'>
            <Form.Item {...formItemLayout} label='Question'>
                <Input className='full-width' defaultValue={this.qinput} key={this.qinput}
                    onChange={(e) => { this.onRewriteText(e, 'question'); }} />
            </Form.Item>
            <Form.Item {...formItemLayout} label='Groundtruths'>
                <Input className='full-width' key={this.groundtruths.join('; ')}
                    defaultValue={this.groundtruths.join('; ')}
                    onChange={(e) => { this.onRewriteText(e, 'groundtruth'); }} />
            </Form.Item>
            <Form.Item {...formItemLayout} label='Context'>
                <Input.TextArea className='full-width'
                    autosize={{ minRows: 2, maxRows: 8 }}
                    defaultValue={this.cinput} key={this.cinput}
                    onChange={(e) => { this.onRewriteText(e, 'context'); }} />
            </Form.Item>
        </Form>;
    }

    public renderToken(t: Token): JSX.Element {
        // generate the current class for the token
        // mark how is the rewriting

        const rewriteClass = `token-rewrite-${t.etype}`;
        // get the current span
        const curClass = utils.genClass('free-rewrite-panel', 'token', [utils.genKeywordId(t.text), t.idx]);
        const curSpan: JSX.Element = <span key={curClass.key}
            className={`token ${curClass.total} ${rewriteClass}`}
            id={curClass.key}>{t.text + ' '}</span>;
        return curSpan;
    }

    public renderTextPair(atext: string, btext: string): JSX.Element {
        const tokens = utils.computeRewriteStr(atext, btext);
        return <span style={{ width: 800 }}>{tokens.map(t => this.renderToken(t))}</span>
    }

    public renderGeneratedTemplates(): JSX.Element {
        const list = this.returnedRules.map(rule => {
            const content = <div>{rule.examples.slice(0, 3).map((t, tidx: number) =>
                <Row key={`text-pairs-${rule.rid}-${tidx}`}>
                    {this.renderTextPair(t[0], t[1])}</Row>)}</div>;
            return <Row key={rule.rid} gutter={20}>
                <Col span={18}>
                    <Popover content={content} title='Rewritten examples'>
                        <span className='ellipsis'>
                        <RewriteTemplateName rewriteName={rule.rid} rewrite={null} /></span>
                    </Popover>
                </Col>
                <Col span={6} style={{ textAlign: 'right' }}>
                    <Checkbox
                        onChange={(e) => { this.onToggleKeepRules(rule.rid) }}>keep</Checkbox>
                </Col>
                <Col span={24} ><Divider style={{ margin: 8 }} /></Col>
            </Row>
        });
        return <Row>{list}</Row>;
    }

    public renderRewriteTemplates(testedRewriteName): JSX.Element {
        return <div>
            {this.props.rewriteNames.map(eName => {
                const applyIcon = <Button shape='circle' type='primary' icon='form' size='small'
                    onClick={() => { this.onAutoRewrite(store._.rewriteStore[eName]) }} />;
                const content = <div>
                    {store._.rewriteStore[eName].examples.slice(0, 3).map((t, tidx: number) =>
                        <Row key={`text-pairs-${eName}-${tidx}`}>{this.renderTextPair(t[0], t[1])}</Row>)}</div>;
                return <Row key={eName} gutter={20}>
                    <Col span={24}>
                        <Popover content={content} title='Rewritten examples'>
                            <span className='ellipsis'>{applyIcon} <RewriteTemplateName rewriteName={eName} rewrite={null} /></span>
                        </Popover>
                        {this.renderRawRewrite(eName, testedRewriteName)}
                    </Col>
                    <Col span={24} ><Divider style={{ margin: 8 }} /></Col>
                </Row>
            })}
        </div>
    }

    public renderRawRewrite(rewriteName: string, testedRewriteName: string): JSX.Element {
        if (testedRewriteName === null || testedRewriteName !== rewriteName) {
            return null;
        }
        if (!this.returnedRewrite) {
            return <div className='ant-list-item-meta ant-list-item-meta-description' 
                style={{ textAlign: 'center' }}>
                The instance is not rewritable by this template!
            </div>
        } else {
            return null;
        }
    }

    public renderTargetCmd(): JSX.Element {
        return <Row>
            <Col span={24} ><Divider style={{ margin: 8 }} /></Col>
            <Col span={16}>
                <Button onClick={ () => { this.generateRule() }}
                    size='small' type='primary'>
                    Generate rules that can rewrite...</Button>
            </Col>
            <Col span={8}>
                <QueryCoder key={ `${this.setCmdCount}` }
                    readOnly={false} 
                    cmd={ this.targetCmd }
                    multiLines={false} 
                    changeCmd={ this.setCmd } />
            </Col>
        </Row>
    }

    /**
     * Render the question bar.
     */
    public render(): JSX.Element {
        return <div className='full-height full-width' key={`${this.props.qid}-free-rewrite`} >
            <h4 className='header'>Free-form Rewriting</h4>
            <Row gutter={30} className='full-height'>
                <Col span={6} className='full-height overflow'>
                    {this.renderRewriteTemplates(this.testedRewriteName)}
                </Col>
                <Col span={10} className='full-height overflow'>{this.renderRewriteForm()} </Col>
                <Col span={8} className='full-height' key={this.returnedRules.length}>
                    {this.returnedRules.length === 0 ?
                        <div>
                            <Row className='full-width' gutter={20}>
                                <Col xs={12} md={8} lg={6} className='right-align'>
                                    <span className='info-header'>Prediction</span></Col>
                                <Col xs={12} md={16} lg={18}>
                                    {this.renderF1Icon(this.returnedPrediction, this.returnedPerform)}
                                    {this.renderChangePredictionIcon(this.returnedPrediction)}
                                    <b>{` ` + this.returnedPrediction}</b>
                                </Col>
                            </Row>
                            <Row style={{ textAlign: 'center' }} >{this.renderFreeRewrite()}</Row>
                            <Row>{this.renderTargetCmd()}</Row>
                        </div> :
                        <div className='full-height full-width'>
                            <h4 className='info-header'>Did you want to generalize to...</h4>
                            <Row style={{ top: 0, bottom: 30 }} className='overflow'>
                                {this.renderGeneratedTemplates()}
                            </Row>
                            <Row style={{ textAlign: 'center' }}>
                                {this.renderConfirmRuleBtn()}
                            </Row>
                        </div>}
                </Col>
            </Row>
        </div>
    }
}