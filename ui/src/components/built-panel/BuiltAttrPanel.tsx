import * as React from 'react';
import { Button, Divider, Row, Spin, Col, Checkbox, Select } from 'antd'
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { QueryCoder } from '../shared-components/QueryCoder';
import { observable } from 'mobx';
import { observer } from 'mobx-react';
import { Attribute } from '../../stores/Attribute';
import { BuiltPanel } from './BuiltPanel';
import { AttrBar } from '../attr-manager/AttrBar';


@observer
export class BuiltAttrPanel extends BuiltPanel {
    @observable public showPercent: boolean;
    // @observable public attrList: Attribute[];
    public selectedRewrite: string;
    public filterCmd: string;

    @observable public filteredAttrList: Attribute[];

    constructor(props: any, context: any) {
        super(props, context);
        this.filterCmd = store._.activeCmd;
        //this.attrList = null;
        this.getFilteredBuilt = this.getFilteredBuilt.bind(this);
        this.changeFilterCmd = this.changeFilterCmd.bind(this);
        this.showPercent = false;
        this.selectedRewrite = store._.sampleRewrite;
        this.selectedModel = store._.anchorPredictor;
        this.filteredAttrList = [];
    }

    public async getFilteredBuilt(): Promise<void> {
        if (!this.built) {
            await this.create();
        }
        const output = await store._.getAttrDistribution(
            [this.built.name], this.filterCmd, false, 
            this.selectedRewrite, this.selectedModel);
        this.filteredAttrList = output;
    }

    public changeFilterCmd(cmd: string): void {
        this.filterCmd = cmd;
    }

    protected renderRewriteSelectList(): JSX.Element {
        const dataList = store._.rewriteHashes.slice();
        dataList.push("(Exclude rewrite)");
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => { 
                this.selectedRewrite = v === "(Exclude rewrite)" ? 
                "" : v as string; }}
            defaultValue={ this.selectedRewrite }
            dropdownMatchSelectWidth={false}
            placeholder="Select rewrite rules"
            size="small">
                {dataList.map(d => {
                    return <Select.Option 
                    key={d}>{d}</Select.Option>
                })}
        </Select>
    }
    
    public renderDistribution(): JSX.Element {
        if (this.props.type === 'group' || this.built === null) {
            return null;
        } 
        let incorrectCount: number;
        let correctCount: number;
        let count: number;
        if (this.filteredAttrList.length > 0 && this.filteredAttrList[0].name === this.built.name) {
            incorrectCount = this.filteredAttrList[0].getCount("incorrect");
            correctCount = this.filteredAttrList[0].getCount("correct");
            count = incorrectCount + correctCount;
        } else {
            incorrectCount = (this.built as Attribute).getCount("incorrect");
            correctCount = (this.built as Attribute).getCount("correct");
            count = incorrectCount + correctCount;
        }
        

        const id = `${this.name}-bar-chart`;
        return <Row className='full-width' gutter={30}>
            <Divider />
            { this.renderSelecDropDown() }
            <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                    <div className='info-header'>See distribution on filtered instances</div>
                    <QueryCoder 
                        cmd={ this.filterCmd } 
                        readOnly={ false } 
                        changeCmd={ this.changeFilterCmd }
                        multiLines={ true } />
                </div>
                <div style={{textAlign: 'center'}}>
                    <Checkbox checked={this.showPercent} onChange={() => { 
                        this.showPercent = !this.showPercent; }}>Proportion</Checkbox>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <Button type='primary' onClick={() => { this.getFilteredBuilt()}}>
                        { 'Re-generate the distribution'}
                    </Button>
                </div>
           </Col>
           <Col span={12}>
           <div>
               <b>{incorrectCount} incorrect + {correctCount} correct = {count} </b>
               instances filtered (<b>{utils.percent(count / store._.totalSize)}</b> of total)
           </div>
            <AttrBar 
                height={150}
                anchorPredictor={store._.anchorPredictor}
                showPercent={this.showPercent}
                key={this.name}
                filteredAttrList={this.filteredAttrList}
                isPreview={false} width={document.body.clientWidth * 0.3}
                attr={ this.built as Attribute }
                highlightedInstances={[]}
                containerId={id} />
            </Col>            
        </Row>;
    }

    public renderSelecDropDown(): JSX.Element {
        return <Row style={{ marginBottom: 8 }}>
            See performance on { this.renderSelectModelList() }; 
            Include instances that are rewritten by { this.renderRewriteSelectList() }.
        </Row>
    }

    public render(): JSX.Element {
        return <div className='full-height full-width'>
        <Spin style={{height: '100%', width: '100%'}} size='large' spinning={store._.loadingData === 'pending'}>
            { this.renderCreation() }
            { this.renderDistribution() }    
        </Spin>
        </div>
    }
}
