/**
 * The control panel for everything.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */
import * as d3 from 'd3';
import * as React from 'react';
import { observer } from 'mobx-react';
import { action, observable } from 'mobx';

import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

import { DataGroup } from '../../stores/DataGroup';
import { RewriteStatCount } from '../../stores/RewriteRule';

import { Button, Row, Divider, Col, Popover, Modal, Tooltip, Checkbox, Spin, Select } from 'antd';

import { GroupBar, Value } from '../shared-components/GroupBar';
import { RewriteTemplateName } from '../shared-components/RewriteTemplateName';
import ResizeAware from 'react-resize-aware';
import { QueryCoder } from '../shared-components/QueryCoder';
import { ExportPanel } from '../shared-components/ExportPanel';
import { BuiltGroupPanel } from '../built-panel/BuiltGroupPanel';
import { InstanceKey } from '../../stores/InstanceKey';


@observer
export class GroupManager extends React.Component<{
    isPreview: boolean, highlightedInstances: InstanceKey[]}, {}> {
    @observable private showPercent: boolean;
    @observable private hoverGroup: string;
    @observable private displayModal: "rewrite_group"|"save_group"|"model_compare"|"";
    @observable private name: string;
    @observable private previewdGroupRewrite: {
        rid: string; group: string; counts: RewriteStatCount;
    }[];
    @observable private highlightedGroup: string[];

    private description: string;
    private cmd: string;
    private highlightedQids: string[];
    private comparedModels: string[];
    @observable private groupListPerModel: {model: string, groups: DataGroup[]}[];


    constructor(props: any, context: any) {
        super(props, context);
        // necessary texts
        this.showPercent = true;
        this.toggleShowPercent = this.toggleShowPercent.bind(this);
        this.loadRewriteRuleInfo = this.loadRewriteRuleInfo.bind(this);
        this.renderGroupOverview = this.renderGroupOverview.bind(this);
        this.renderGroupDetail = this.renderGroupDetail.bind(this);
        this.renderPreview = this.renderPreview.bind(this);
        this.toggleShowFilteredGroup = this.toggleShowFilteredGroup.bind(this);
        this.getModelComparisons = this.getModelComparisons.bind(this);
        
        this.displayModal = '';
        this.hoverGroup = '';
        this.previewdGroupRewrite = [];
        this.highlightedGroup = [];
        this.highlightedQids = [];
        this.comparedModels = [];
        this.groupListPerModel = [];
        this.setInfo(null);
    }

    public async toggleShowFilteredGroup(): Promise<void> {
        store._.showFilteredGroup = !store._.showFilteredGroup;
        if (store._.showFilteredGroup &&store._.lastExecutedCmd !== '') {
            store._.filteredGroupList = await store._.getMetaDistribution(
                "group", store._.dataGroupHashs.slice(), 
                store._.lastExecutedCmd, true) as DataGroup[];
        } else {
            store._.filteredGroupList = [];
        }
    }

    @action private toggleShowPercent(): void {
        this.showPercent = !this.showPercent;
    }

    public async componentDidUpdate(): Promise<void> {
        if (this.props.highlightedInstances.length === 0) {
            if (this.highlightedQids.length > 0) {
                this.highlightedQids = [];
                this.highlightedGroup = [];
            }
        }
        const qids = this.props.highlightedInstances.map(h => h.qid).filter(utils.uniques);
        const intersection = utils.intersection([
            qids,
            this.highlightedQids,
        ])
        if (intersection.length !== qids.length) {
            this.highlightedQids = qids;
            const queried = await store._.service.getBuiltsOfInstances(
                this.props.highlightedInstances, "group");
            this.highlightedGroup = queried === null ? [] : queried;
        }
    }
    

    private async loadRewriteRuleInfo(group: DataGroup): Promise<void> {
        const data = await store._.service.evalRewritesOnGroups(
            store._.rewriteHashes, [group.name]);
        if (data) {
            this.previewdGroupRewrite = data;
        }
    }

    public renderPreviewRewrite(group: DataGroup): JSX.Element {
        const btn = <Button 
            onClick={() => { this.loadRewriteRuleInfo(group); }}
            disabled={this.previewdGroupRewrite.length !== 0}
            size='small' type='primary'>See previous applied rewrites</Button>
        const list = this.previewdGroupRewrite
            .filter(d => d.group === group.name)
            .map((d) => {
            const id = `e:${d.rid}-g:${d.counts}`;
            const value: Value = {
                name: d.rid, counts: {
                    flip_to_correct: d.counts.flip_to_correct,
                    flip_to_incorrect: d.counts.flip_to_incorrect,
                    other: d.counts.unflip
                }
            }
            return <Row key={id} gutter={20}>
                <Col span={16}>
                    <RewriteTemplateName key={d.rid} rewriteName={d.rid} rewrite={null} />
                </Col>
                <Col span={8} style={{height: 20}} id={id}>
                    <ResizeAware style={{ position: 'relative' }}>
                    {({ width, height }) => {
                    return <GroupBar
                        isPreview={false}
                        anchorPredictor={store._.anchorPredictor}
                        width={width} height={20} key={width}
                        containerId={id}
                        values={[value]} 
                        showPercent={false} />}}
                    </ResizeAware>
                </Col>
                <Col span={24} ><Divider style={{margin: 8}}/></Col>
            </Row>
            
        })
        return <div className='full-width overflow' style={{maxHeight: '100px'}}>
        <div style={{textAlign: 'center'}}>{btn}</div>
            {list}
        </div>
    }

    public renderPreview(group: DataGroup): JSX.Element {
        if (!group) { return null; }
        return <Row gutter={30} 
                key={group.cmd+group.name}
                style={{width: 0.5 * document.body.clientWidth}}>
                <Col span={12}>
                <div><span className='info-header'>STATS</span></div>
                <div>{`Coverage: ${group.getCount()} (${utils.percent(group.stats.coverage)}), `}</div>
                <div>{`Error: ${group.counts.incorrect} (${utils.percent(group.stats.global_error_rate)} of total, 
                    ${utils.percent(group.stats.local_error_rate)} of slice), ${utils.percent(group.stats.error_coverage)} of errors)`}</div>
                <div><span className='info-header'>DESCRIPTION</span></div>
                <div className='ant-list-item-meta ant-list-item-meta-description'>{group.description}</div>
                <div><span className='info-header'>Filter Command</span></div>
                <div><QueryCoder readOnly={true} cmd={group.cmd} multiLines={false} changeCmd={null} /></div>
                </Col>
                <Col span={12}>
                    <div><span className='info-header'>APPLIED REWRITES</span></div>
                    {this.renderPreviewRewrite(group)}
                </Col>
            </Row>
    }


    public renderGroupOverview(gName: string, gValue: Value, domain:[number, number]): JSX.Element {
        const group = store._.dataGroupStore[gName];
        const id = `label-panel-${utils.genKeywordId(gName)}-${store._.anchorPredictor}`;
        const preview = this.renderPreview(group);
        const isSelected = this.highlightedGroup.indexOf(gName) > -1;
        return <Row key={id} gutter={20}
                onMouseOut={() => { this.hoverGroup = ''; }}
                onMouseOver={() => { this.hoverGroup = gName; }}>
            <Col span={24}
             style={{ backgroundColor: isSelected ? 'yellow' : 'none' }}
             key={`${isSelected}`}>
                <Popover 
                    placement="topLeft"
                    mouseLeaveDelay={0.2}
                    mouseEnterDelay={0.2}
                    title={`Hovered group: ${gName}`}
                    content={preview} >
                    <small onMouseOver={() => { this.previewdGroupRewrite = []; }}
                        className='ellipsis' style={{cursor: 'pointer'}}>{gName}</small>
                </Popover>
            </Col>
            <Col key={id} span={24} style={{height: 20}} id={id}>
            <ResizeAware style={{ position: 'relative' }}>
                {({ width, height }) => {
                    return width > 100 ? null : 
                <GroupBar
                    domain={domain}
                    isPreview={true}
                    anchorPredictor={null} // this.showPrecent ? store._.anchorPredictor : null
                    width={width} height={20} key={width}
                    containerId={id}
                    values={[gValue]} 
                    showPercent={false} />}}
                </ResizeAware>
            </Col>
            <Col span={24} ><Divider style={{margin: 8}}/></Col>
        </Row>
    }
 
    public renderGroupDetail(gName: string, gValue: Value, domain:[number, number]): JSX.Element {
        const group = store._.dataGroupStore[gName];
        const id = `label-panel-${utils.genKeywordId(gName)}-${store._.anchorPredictor}`;
        const isSelected = this.highlightedGroup.indexOf(gName) > -1;
        const preview = this.renderPreview(group);
        const groupbarWidth = this.hoverGroup === gName ? 3 : 8;
        return <Row key={id} gutter={20}
                onMouseOut={() => { this.hoverGroup = ''; }}
                onMouseOver={() => { this.hoverGroup = gName; }}>
            <Col span={7}
                key={`${isSelected}`}
                style={{ backgroundColor: isSelected ? 'yellow' : 'none' }}>
                <Popover 
                    placement="topLeft"
                    mouseLeaveDelay={0.2}
                    mouseEnterDelay={0.2}
                    title={`Hovered group: ${gName}`}
                    content={preview} >
                    <b onMouseOver={() => { this.previewdGroupRewrite = []; }}
                        className='ellipsis' style={{cursor: 'pointer'}}>{gName}</b>
                </Popover>
            </Col>
            <Col span={9}>
                <QueryCoder readOnly={true} cmd={group.cmd} multiLines={false} changeCmd={null} />
            </Col>
            <Col key={id} span={groupbarWidth} style={{height: 20}} id={id}>
                <ResizeAware style={{ position: 'relative' }}>
                {({ width, height }) => {
                    return <GroupBar
                    domain={domain}
                    isPreview={false}
                    anchorPredictor={store._.anchorPredictor}
                    width={width} height={25} key={width}
                    containerId={id}
                    values={[gValue]} 
                    showPercent={this.showPercent} />}}
                </ResizeAware>
            </Col>
            <Col span={8-groupbarWidth} style={{height: 20}} id={id}>
                {this.renderInfoButton (group)}
            </Col>
            <Col span={24} ><Divider style={{margin: 8}}/></Col>
        </Row>
    }

    public constructValue(gName: string, filteredGroupList: DataGroup[], forceShowFiltered: boolean=false): Value {
        let group = store._.dataGroupStore[gName];
        if ((store._.showFilteredGroup || forceShowFiltered) && filteredGroupList) {
            const groupList = filteredGroupList
                .filter(a => a.name === gName);
            group = groupList.length > 0 ? groupList[0] : group;
        }
        return {
            name: group.name, counts: {
                incorrect: group.counts.incorrect,
                correct: group.counts.correct
            }
        }
    }

    public renderGroupList(dataGroupHashs: string[]): JSX.Element {
        const groupHashes = dataGroupHashs.slice()
            .sort((a, b) => store._.dataGroupStore[b].getCount() - store._.dataGroupStore[a].getCount());
        const values: Value[] = groupHashes.map(g => 
            this.constructValue(g, store._.filteredGroupList));
        const domain = d3.extent(values
            .filter(b => b.name !== "all_instances")
            .map(b => d3.sum(Object.values(b.counts)) ));
        const renderFunc = this.props.isPreview ? 
            this.renderGroupOverview : this.renderGroupDetail;
        const list = groupHashes.map((eName, idx: number) => 
            renderFunc(values[idx].name, values[idx], domain) );
        return <div className='full-height full-width overflow' 
            key={groupHashes.length}>{list}</div>
    }

    public renderGroupListForCompare(dataGroupHashs: string[]): JSX.Element {
        const groupHashes = dataGroupHashs.slice()
            .sort((a, b) => store._.dataGroupStore[b].getCount() - store._.dataGroupStore[a].getCount());
        const values: {[key: string]: Value[]} = {};
        const groupListPerModel = this.groupListPerModel.slice();
        const models = groupListPerModel.map(m => m.model).filter(utils.uniques);
        for (let o of groupListPerModel) {
            values[o.model] = groupHashes.map(g => this.constructValue(g, o.groups, true));
        }
        const domain = d3.extent(d3.merge<Value>(Object.values(values))
            .filter(b => b.name !== "all_instances")
            .map(b => d3.sum(Object.values(b.counts)) ));
        const col = Math.floor( 16/ (models.length));
        return <div className='full-height full-width overflow' 
            key={`${groupHashes.length}`}>
            <h4 className='header ellipsis'>Model Performances on Groups</h4>
            <Row gutter={20}>
                <Col span={24 - col * models.length}></Col>
                {models.map(model => <Col style={{textAlign: 'center'}}
                span={col} key={`${model}-title`}><b>{model}</b></Col>)}
            </Row>
            {groupHashes.map((gName, idx: number) => {
                return <Row gutter={20} key={idx}>
                    <Col span={24 - col * models.length}><b className='ellipsis'>{gName}</b></Col>
                    {models.map(model => {
                        const id = `${gName}-${model}`;
                        return <Col span={col} id={id} key={`${model}`}>
                        <GroupBar
                            domain={domain}
                            isPreview={false}
                            anchorPredictor={model}
                            width={null} height={20} 
                            containerId={id}
                            key={`${id}`}
                            values={[values[model][idx]]} 
                            showPercent={true} />
                        </Col>
                    })}
                    <Col span={24} ><Divider style={{margin: 3}}/></Col>
                </Row>
            })}
            
            </div>
    }

    public renderExportModal(): JSX.Element {
        if (!this.displayModal) { return null; }
        return <Modal
            key={this.displayModal}
            title={`Export the Data Groups!`}
            visible={ this.displayModal === "save_group"}
            footer={null}
            onCancel={() => { this.displayModal = ''; }}>
            <ExportPanel type="group"
                key={this.displayModal} 
                filename={this.displayModal}
                builts={store._.dataGroupHashs.slice()} />
        </Modal>
    }

    private renderRewriteGroupModal(): JSX.Element {
        return <Modal
            key={this.name}
            title={`Customize Data Group`}
            destroyOnClose={true}
            width={ document.body.clientWidth * 0.7 }
            style={{ top: document.body.clientHeight * 0.05, height: document.body.clientHeight * 0.4}}
            visible={ this.displayModal === "rewrite_group" }
            onCancel={ () => { this.setInfo(null); this.displayModal= '' }}
            footer={null}>
            <BuiltGroupPanel  
                key={this.name}
                name={ this.name }
                description={ this.description }  
                cmd={ this.cmd } type='group' />
        </Modal>
    }

    protected renderGroupSelectList(): JSX.Element {
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => { this.comparedModels = v as string[]; }}
            defaultValue={this.comparedModels}
            dropdownMatchSelectWidth={false}
            placeholder="Select groups"
            size="small"
            mode="multiple" >
                {Object.keys(store._.predictorStore).map(d => {
                    return <Select.Option key={d}>{d}</Select.Option>
                })}
        </Select>
    }
    private async getModelComparisons(): Promise<void> {
        let values = [];
        for (let model of this.comparedModels) {
            const output = await store._.getMetaDistribution("group", null, null, false, model) as DataGroup[];
            if (output.length !== store._.dataGroupHashs.length) {
                return;
            }
            values.push({model: model, groups: output});
        }
        this.groupListPerModel = values.slice();
    }
    
    private rendermodelCompareModal(): JSX.Element {
        return <Modal
            key={this.name + ' model_compare'}
            title={`Compare Model Performances on Groups`}
            destroyOnClose={true}
            width={ document.body.clientWidth * 0.7 }
            style={{ 
                top: document.body.clientHeight * 0.05, 
                height: document.body.clientHeight * 0.4}}
            visible={ this.displayModal === "model_compare" }
            onCancel={ () => { 
                this.setInfo(null); 
                this.displayModal= '' 
            }}
            footer={null}>
            <Spin style={{height: '100%', width: '100%'}} size='large' 
                spinning={store._.loadingData === 'pending'}>
                <Row className='full-width full-height' 
                    style={{height: document.body.clientHeight * 0.4}}>
                    <div>See models: { this.renderGroupSelectList() } 
                    to compare their performances on groups.
                    <Button onClick={this.getModelComparisons}
                        size='small' type='primary'>Ok</Button></div>
                <Row style={{margin: 20}}>
                {this.renderGroupListForCompare(store._.dataGroupHashs)}
                </Row>
            </Row>
            </Spin>
        </Modal>
    }

    private setInfo(group: DataGroup): void {
        if (group === null) {
            this.description = '';
            this.cmd = '';
            this.name = '';
        } else {
            this.description = group.description;
            this.cmd = group.cmd;
            this.name = group.name;
        }
        this.groupListPerModel = [];
    }

    public renderInfoButton(group: DataGroup): JSX.Element {
        return (
            <div style={{textAlign: 'right'}}>
                <Tooltip title="Load cmd into Instance Browser"><Button 
                    shape='circle' icon='upload' size='small' className='info-button'
                    onClick={ () => { store._.setCmdFromGroup(group) } }/></Tooltip>
                <Tooltip title="Rewrite the group"><Button 
                    shape='circle' icon='edit' size='small' className='info-button'
                    onClick={ () => {
                        store._.resetFetchMsg();
                        this.setInfo(group);
                        this.displayModal = "rewrite_group";
                    } } /></Tooltip>
                <Tooltip title="Delete the group"><Button 
                    shape='circle' icon='delete' size='small' className='info-button'
                    onClick={ () => { store._.deleteBuilt(group.name, 'group') } } /></Tooltip>
            </div>
        )
    }

    public renderCtrlButtons(): JSX.Element {
        const onSave = () => {
            store._.resetFetchMsg();
            this.displayModal = 'save_group';
        }
        const onCompareModel = () => {
            store._.resetFetchMsg();
            this.displayModal = "model_compare";
        }
        /*<Button type='primary' size='small' onClick={() => { store._.startNewFilterSection() }}>Add a New Group</Button>*/

        const buildBtn = (title: string, icon: string, func) => {
            return this.props.isPreview ?
                <Tooltip title={title}><Button 
                    shape='circle' icon={icon} size='small' className='info-button'
                    onClick={() => { func() }}/></Tooltip> :
                <Button size='small' type='primary' 
                    onClick={() => { func()}}>{title}</Button>
        }
        return <div style={{textAlign: 'center', marginTop: this.props.isPreview ? 5 : 0 }}>
            { buildBtn('Export the Groups', 'save', onSave) }
            { buildBtn('Compare models', 'diff', onCompareModel) }
        </div>
    }

    /**
     * The major rendering
     */
    public render(): JSX.Element {
        //const selectedAnchor = store.anchorPredictor ? store.anchorPredictor : '(unselected)'
        const topMargin = this.props.isPreview ? 50 : 80;
        const title = this.props.isPreview ? 
            <div className='info-header ellipsis'>GROUPS</div> :
            <div> 
                <h4 className='header'>Data Groups</h4>
                <div style={{textAlign: 'center'}}> 
                <Checkbox checked={this.showPercent} onChange={() => { 
                    this.showPercent = !this.showPercent; }}>Proportion</Checkbox>
                <Checkbox checked={store._.showFilteredGroup} onChange={() => { 
                    this.toggleShowFilteredGroup();
                }}>Show filtered distribution</Checkbox>
                </div>
            </div>
        return (
        <div className='full-width full-height' style={{position: 'relative'}}>                        
            <Row>{title}</Row>
            <Row>{this.renderCtrlButtons()}</Row>
            <div className='overflow'
                style={{top: topMargin, bottom: 0,right: 0, left: 0, position: 'absolute'}}>
                { this.renderGroupList(store._.dataGroupHashs) }</div>
            { this.renderExportModal() }
            { this.renderRewriteGroupModal() }
            { this.rendermodelCompareModal() }
        </div>);
    }
}