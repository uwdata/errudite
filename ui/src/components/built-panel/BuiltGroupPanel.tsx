import * as React from 'react';
import { Button, Divider, Row, Spin } from 'antd'
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { observable } from 'mobx';
import { observer } from 'mobx-react';
import { GroupBar, Value } from '../shared-components/GroupBar';
import { BuiltPanel } from './BuiltPanel';
import { DataGroup } from '../../stores/DataGroup';


@observer
export class BuiltGroupPanel extends BuiltPanel {
    @observable public showPercent: boolean;
    // @observable public attrList: Attribute[];
    selectedRewrite: string;
    selectedModel: string;
    @observable public filteredGroupList: DataGroup[];

    constructor(props: any, context: any) {
        super(props, context);
        this.showPercent = false;
        this.selectedRewrite = store._.sampleRewrite;
        this.selectedModel = store._.anchorPredictor;
        this.filteredGroupList = [];
        this.getFilteredBuilt = this.getFilteredBuilt.bind(this);
    }

    public async getFilteredBuilt(): Promise<void> {
        if (!this.built) {
            await this.create();
        }
        const output = await store._.getMetaDistribution(
            "group", [this.built.name], '', false, this.selectedModel);
        this.filteredGroupList = output as DataGroup[];
    }

    public renderDistribution(): JSX.Element {
        if (this.built === null) {
            return null;
        }
        let built = this.built;
        if (this.filteredGroupList.length > 0 && this.filteredGroupList[0].name === built.name) {
            built = this.filteredGroupList[0];
        }
        const incorrectCount = built.counts.incorrect as number;
        const correctCount = built.counts.correct as number;
        const count = incorrectCount + correctCount;
        const value: Value = {
            name: this.name, counts: {
                incorrect: built.counts.incorrect as number,
                correct: built.counts.correct as number
            }
        }
        const id = `${this.name}-bar-chart`;
        return <Row className='full-width' gutter={30} 
            style={{textAlign: 'center'}}>
            <Divider />
            { this.renderSelecDropDown() }
            <div style={{ textAlign: 'center' }}>
                    <Button type='primary' onClick={() => { this.getFilteredBuilt()}}>
                        { 'Re-generate the distribution'}
                    </Button>
                </div>
           <div>
               <b>{value.counts.incorrect} incorrect + {value.counts.other} correct = {count} </b>
               instances filtered (<b>{utils.percent(count / store._.totalSize)}</b> of total)
           </div>
           <GroupBar
                isPreview={false}
                anchorPredictor={store._.anchorPredictor}
                width={document.body.clientWidth * 0.4}
                height={30} key={this.name}
                containerId={id}
                values={[value]} 
                showPercent={true} />
        </Row>;
    }

    public renderSelecDropDown(): JSX.Element {
        return <Row style={{ marginBottom: 8 }}>
            See performance on { this.renderSelectModelList() };
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
