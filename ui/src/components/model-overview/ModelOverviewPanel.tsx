/**
 * The control panel for everything.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */

import * as React from 'react';
import { observer } from 'mobx-react';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { Dropdown, Menu, Icon, Table, Tabs, Checkbox } from 'antd';
import { ErrorOverlapPanel } from './ErrorOverlap';
import { Predictor } from '../../stores/Predictor';

@observer
export class ModelOverviewPanel extends React.Component<{}, {}> {

    constructor(props: {}, context: any) {
        super(props, context);
        // necessary texts
        // bind
        this.onChangeModelSelection = this.onChangeModelSelection.bind(this);
        this.toggleShowFilteredErrOverlap = this.toggleShowFilteredErrOverlap.bind(this);
    }

    public async toggleShowFilteredErrOverlap(): Promise<void> {
        store._.showFilteredErrOverlap = !store._.showFilteredErrOverlap;
        if (store._.lastExecutedCmd !== '') {
            store._.loadingData = "pending";
            const output = await store._.service.getErrOverlap(store._.showFilteredErrOverlap);
            store._.errOverlaps = output === null ? [] : output; 
            store._.loadingData = "done";
        }
    }

    /**
     * Toggle the selected models
     * @param {string[]} selectedPredictorNames the names of selected predictors for inspection 
     */
    private onChangeModelSelection(selectedPredictorNames: string[]): void {
        store._.selectedPredictors = selectedPredictorNames;
    }
    

    /**
     * Render the predictor performance table. 
     * Note the predictors must be sort by f1 before put in
     * @param {Predictor[]} predictors list of predictors.
     * @return {JSX.Element} the table item.
     */
    private renderModelTable(predictors: Predictor[]): JSX.Element {
        // compute the container
        console.log(store._.anchorPredictor);
        //store.selectFilters.predictors.map(p => `${p.name}-${p.value.dimension}`);
        let columns = [{
            title: 'Model', dataIndex: 'model', key: 'model', align: "center" as "center" | "left" | "right",
            render: (_, predictor: Predictor, idx: number) => <div 
                style={{
                    cursor: 'pointer',
                    color: predictor.name === store._.anchorPredictor ? utils.selectedModelColor : 'black' }}
                onClick={() => { store._.setAnchorPredictor(predictor.name); }}>{predictor.name}</div>
        }];
        let columnPerform = store._.metricNames.map(perform => {
            return {
                title: perform, dataIndex: perform, key: perform, align: "center" as "center" | "left" | "right",
                render: (_, predictor: Predictor, pidx: number) => {
                    const elementClass = utils.genClass('perform-table-body', 'range', [predictor.name, perform]);
                    return <div key={elementClass.key}>
                    {(predictor.perform[perform]).toFixed(2)}
                </div>
                }
            }
        })
        columns = columns.concat(columnPerform);
        store._.selectedPredictors
        const rowSelection = {
            selectedRowKeys: store._.selectedPredictors.slice(),
            onChange: this.onChangeModelSelection,
          };
        return <Table columns={columns} size='small' bordered rowSelection={rowSelection}
            rowClassName={(predictor: Predictor) => predictor.name}
            pagination={false}//{{ pageSize: this.pageSize }}
            rowKey={(predictor: Predictor) => predictor.name}
            //scroll={{ y: this.height }}
            dataSource={predictors} />
    }

    public renderComparePredictorSelector(): JSX.Element {
        const models = store._.selectedPredictors.filter(m => m !== store._.anchorPredictor);
        const modelMenu = <Menu 
            onClick={(e) => { store._.setComparePredictor(e.key) }}>
            {models.map((m: string) => <Menu.Item key={m}>{m}</Menu.Item>)}
        </Menu>
        return <div style={{ textAlign: 'center', marginBottom: 10 }}>
            Compare {store._.anchorPredictor} with 
            <Dropdown overlay={modelMenu}>
                <a className="ant-dropdown-link" href="#">
                    {` ${ store._.comparePredictor } `} 
                    <Icon type="down" /></a></Dropdown>
            <Checkbox checked={store._.showFilteredErrOverlap} onChange={() => { 
                 this.toggleShowFilteredErrOverlap();
            }}>Show filtered distribution</Checkbox>
            </div>
    }
    /**
     * The major rendering
     */
    public render(): JSX.Element {
        const container = document.getElementById('model-overview');
        const height = container ? container.clientHeight : 300;
        const predictors = Object.values(store._.predictorStore)
            .sort((p1, p2) => {
                if(utils.getAttr(p1.perform, 'f1', 0) === utils.getAttr(p2.perform, 'f1', 0)) {
                    return utils.getAttr(p1.perform, 'accuracy', 0) - utils.getAttr(p2.perform, 'accuracy', 0)
                }
                return utils.getAttr(p1.perform, 'f1', 0) - utils.getAttr(p2.perform, 'f1', 0)
            });

        //const identifiers = store.visualizeQids.map(qid => store.iStoreOrigin[qid]);
        const errMat = <div id='predictor-mat' 
            className='full-width' style={{height: height - 100}}>
            <ErrorOverlapPanel overlaps={store._.errOverlaps.slice()} />
        </div>

        const scoreTable = <div
            className='full-width overflow' style={{height: 0.8 * height}}>
            {this.renderModelTable(predictors)}
        </div>
        return (
            <Tabs defaultActiveKey="1" className='full-width full-height' 
                style={{position: 'relative'}}>
                <Tabs.TabPane tab="Metrics Overview" key="1">
                    { scoreTable }
                    </Tabs.TabPane>
                <Tabs.TabPane tab="Model Comparison" key="2">
                    { this.renderComparePredictorSelector() }
                    { errMat }
                </Tabs.TabPane>
            </Tabs>)
    }
}