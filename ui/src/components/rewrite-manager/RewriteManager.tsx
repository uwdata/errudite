/**
 * The control panel for everything.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */

import * as React from 'react';
import * as d3 from 'd3';

import ResizeAware from 'react-resize-aware';
import { observer } from 'mobx-react';
import { action, observable } from 'mobx';

import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

import { RewriteRule, RewriteStatCount } from '../../stores/RewriteRule';
import { Button, Row, Divider, Col, Modal, Tooltip, Spin, Checkbox, Popover } from 'antd';

import { RewriteTemplateName } from '../shared-components/RewriteTemplateName';
import { GroupBar, Value } from '../shared-components/GroupBar';
import { ExportPanel } from '../shared-components/ExportPanel';
import { RewriteInspectPanel } from './RewriteInspectPanel';
import { InstanceKey } from '../../stores/InstanceKey';

@observer
export class RewriteManager extends React.Component<{
    isPreview: boolean, highlightedInstances: InstanceKey[]}, {}> {
    @observable private showPercent: boolean;
    @observable private displayModal: string;
    @observable private hoverRewrite: string;

    @observable private highlightedRewrites: string[];

    @observable private previewdGroupRewrites: {
        rid: string; group: string; counts: RewriteStatCount;
    }[];

    private highlightedQids: string[];


    constructor(props: any, context: any) {
        super(props, context);
        // necessary texts
        this.showPercent = true;
        this.displayModal = ''
        this.hoverRewrite = '';
        this.previewdGroupRewrites = [];

        this.highlightedRewrites = [];
        this.highlightedQids = [];

        this.renderRewriteDetail = this.renderRewriteDetail.bind(this);
        this.renderRewriteOverview = this.renderRewriteOverview.bind(this);
        this.renderInfoPreview = this.renderInfoPreview.bind(this);

        this.toggleShowPercent = this.toggleShowPercent.bind(this);
        this.loadRewriteToBrowser = this.loadRewriteToBrowser.bind(this);
        this.loadRewriteRuleInfo = this.loadRewriteRuleInfo.bind(this);
        this.toggleShowFilteredGroup = this.toggleShowFilteredGroup.bind(this);
    }

    public async toggleShowFilteredGroup(): Promise<void> {
        store._.showFilteredRewrite = !store._.showFilteredRewrite;
        if (store._.showFilteredRewrite &&store._.lastExecutedCmd !== '') {
            store._.filteredRewriteList = await store._.getMetaDistribution(
                "rewrite", store._.rewriteHashes.slice(), 
                store._.lastExecutedCmd, true) as RewriteRule[];
        } else {
            store._.filteredRewriteList = [];
        }
    }

    public async componentDidUpdate(): Promise<void> {
        //const rewrites = await store._.service.getRewritesOfInstances(store._.highlightedInstances.slice());
        //this.highlightedGroup = 
        if (this.props.highlightedInstances.length === 0) {
            if (this.highlightedQids.length > 0) {
                this.highlightedQids = [];
                this.highlightedRewrites = [];
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
                this.props.highlightedInstances, "rewrite");
            this.highlightedRewrites = queried === null ? [] : queried;
        }
    }

    private async loadRewriteRuleInfo(rewrite: RewriteRule): Promise<void> {
        const data = await store._.service.evalRewritesOnGroups(
            [rewrite.rid], store._.dataGroupHashs);
        if (data) {
            this.previewdGroupRewrites = data;
            this.displayModal = rewrite.hash();
        }
        store._.loadingData = "done";
    }

    @action private toggleShowPercent(): void {
        this.showPercent = !this.showPercent;
    }

    @action private async loadRewriteToBrowser(rewrite: RewriteRule): Promise<void> {
        store._.switchBrowserTarget("rewrite");
        store._.setSelectedRewrite(rewrite.rid);
        await store._.sampleInstance(
            store._.activeCmd, 
            store._.sampleMethod, 
            store._.sampleRewrite, null, null);
        }

    private renderInfoPreview(rewrite: RewriteRule): JSX.Element {
        if (rewrite === null ) { return null; }
        return <Row style={{width: document.body.clientWidth * 0.3}}>
        <Row className='full-height overflow'>
            <h4 className='ant-list-item-meta ant-list-item-meta-title'>
                { <RewriteTemplateName key={rewrite.rid} rewriteName={rewrite.rid} rewrite={null} /> }
            </h4>
            <div className='ant-list-item-meta ant-list-item-meta-description'>
                <div>{ rewrite.description }</div>
            </div>
        </Row>
        <Col span={24}><Divider style={{marginTop: 0, marginBottom: 5, marginLeft: 8, marginRight: 8 }}/></Col>
    </Row>
    }

    public renderRewriteOverview(rid: string, eValue: Value, domain:[number, number]) {
        const id = `rewrite-manager-${utils.genKeywordId(rid)}`;
        const rewrite = store._.rewriteStore[rid];
        const isSelected = this.highlightedRewrites.indexOf(rid) > -1;
        return <Row key={id} gutter={20}>
                <Col span={24} 
                    style={{ backgroundColor: isSelected ? 'yellow' : 'none' }}
                    key={`${isSelected}`}>
                    <Popover title={`Hovered attribute: ${name}`} placement='topLeft'
                        content={this.renderInfoPreview(rewrite)} >
                        <small
                        className='ellipsis clickable'>
                        {rid}
                        </small>
                    </Popover>
                </Col>
                <Col span={24} style={{height: 20}} id={id}>
                <ResizeAware style={{ position: 'relative' }}>
                    {({ width, height }) => {
                    return width > 100 ? null :  <GroupBar 
                        domain={domain}
                        isPreview={true}
                        anchorPredictor={null}
                        width={width} height={20} key={width}
                        containerId={id}
                        values={[eValue]} 
                        showPercent={false} />}}
                    </ResizeAware>
                </Col>
            </Row>
    }

    public renderRewriteDetail(rid: string, eValue: Value, domain:[number, number]): JSX.Element {
        const id = `rewrite-manager-${utils.genKeywordId(rid)}`;
        const rewrite = store._.rewriteStore[rid];
        const isSelected = this.highlightedRewrites.indexOf(rid) > -1;
        const groupbarWidth = this.hoverRewrite === rid ? 3 : 8;
        return <Row key={id} gutter={20}
            onMouseOut={() => { this.hoverRewrite = ''; }}
            onMouseOver={() => { this.hoverRewrite = rid; }}>
            <Col span={16} className='ellipsis' key={`${isSelected}`}
                style={{ backgroundColor: isSelected ? 'yellow' : 'none' }} >
                <RewriteTemplateName key={rid} rewriteName={rid} rewrite={rewrite} />
            </Col>
            <Col span={groupbarWidth} style={{height: 20}} id={id}>
            <ResizeAware style={{ position: 'relative' }}>
                {({ width, height }) => {
                    return <GroupBar 
                    domain={this.showPercent ? null : domain}
                    isPreview={false}
                    anchorPredictor={store._.anchorPredictor}
                    width={width} height={20} key={width}
                    containerId={id}
                    values={[eValue]} 
                    showPercent={this.showPercent} />}}
                </ResizeAware>
            </Col>
            <Col span={8-groupbarWidth} style={{height: 20}} id={id}>
                {this.renderInfoButton (rewrite)} </Col>
            <Col span={24} ><Divider style={{margin: 8}}/></Col>
        </Row>
    }

    public constructValue(rid: string): Value {
        let rewrite: RewriteRule = store._.rewriteStore[rid];
        if (store._.showFilteredRewrite && store._.filteredRewriteList) {
            const groupList = store._.filteredRewriteList
                .filter(a => a.rid === rid);
            rewrite = groupList.length > 0 ? groupList[0] : rewrite;
        }
        return {
            name: rewrite.rid, counts: {
                flip_to_correct: rewrite.counts.flip_to_correct,
                flip_to_incorrect: rewrite.counts.flip_to_incorrect,
                other: rewrite.counts.unflip
            }
        }
    }

    public renderRewriteList(rewriteHashes: string[]): JSX.Element {
        rewriteHashes = rewriteHashes.slice().sort((a, b) => 
            store._.rewriteStore[b].getCount() - store._.rewriteStore[a].getCount());
        const values: Value[] = rewriteHashes.map(g => this.constructValue(g));
        const domain = d3.extent(values.map(b => d3.sum(Object.values(b.counts)) ));
        const renderFunc = this.props.isPreview ? this.renderRewriteOverview : this.renderRewriteDetail;
        const list = rewriteHashes.map((eName, idx: number) => 
            renderFunc(values[idx].name, values[idx], domain) )
        return <div className='full-height full-width overflow' 
            key={rewriteHashes.length}>{list}</div>
    }

    public renderInfoButton(rewrite: RewriteRule): JSX.Element {
        return (
            <div style={{textAlign: 'right'}}>
                <Tooltip title="Load into Instance Browser"><Button 
                    shape='circle' icon='upload' size='small' className='info-button'
                    onClick={ () => { this.loadRewriteToBrowser(rewrite);} }/></Tooltip>
                <Tooltip title="Apply rewrites to certain groups"><Button 
                    shape='circle' icon='edit' size='small' className='info-button'
                    onClick={() => { this.loadRewriteRuleInfo(rewrite) }}/></Tooltip>
                <Tooltip title="Delete the group"><Button 
                    shape='circle' icon='delete' size='small' className='info-button'
                    onClick={ () => { store._.deleteBuilt(rewrite.rid, 'rewrite')} } /></Tooltip>
            </div>
        )
    }

    private renderRewriteInspectModal(): JSX.Element {
        return <Modal
            destroyOnClose={true}
            title={`Details for a rewrite rule`}
            style={{ top: document.body.clientHeight * 0.05, height: document.body.clientHeight * 0.5}}
            width={document.body.clientWidth * 0.9}
            visible={this.displayModal !== '' && this.displayModal !== 'save_rewrite' }
            footer={null}
            onCancel={() => {this.displayModal = ''; }}>
            <Spin style={{height: '100%', width: '100%'}} size='large' 
                spinning={store._.loadingData === 'pending'}>
            <Row className='full-width overflow' style={{
                height: document.body.clientHeight * 0.6 }}>
                <RewriteInspectPanel 
                    key={this.displayModal}
                    previewdGroupRewrites={this.previewdGroupRewrites}
                    rewriteName={this.displayModal} />
            </Row>
            </Spin>
        </Modal>
    }

    public renderExportModal(): JSX.Element {
        if (!this.displayModal) { return null; }
        return <Modal
            key={this.displayModal}
            title={`Export the Rewrite Rules!`}
            visible={ this.displayModal === "save_rewrite" }
            footer={null}
            onCancel={() => { this.displayModal = ''; }}>
            <ExportPanel key={this.displayModal} 
                builts={store._.rewriteHashes.slice()}
                filename={this.displayModal} type="rewrite" />
        </Modal>
    }

    public renderCtrlButtons(): JSX.Element {
        const onCreate = () => { 
            store._.resetFetchMsg();
            this.displayModal = "create_rewrite";
        };
        const onSave = () => {
            this.displayModal = "save_rewrite";
        }

        const buildBtn = (title: string, icon: string, func) => {
            return this.props.isPreview ?
                <Tooltip title={title}><Button 
                    shape='circle' icon={icon} size='small' className='info-button'
                    onClick={() => { func() }}/></Tooltip> :
                <Button size='small' type='primary' 
                    onClick={() => { func()}}>{title}</Button>
        }
        return <div style={{textAlign: 'center', marginTop: this.props.isPreview ? 5 : 0 }}>
            { buildBtn('Add a rule', 'plus', onCreate) }
            { buildBtn('Save rules', 'save', onSave) }
        </div>
    }

    /**
     * The major rendering
     */
    public render(): JSX.Element {
        //const selectedAnchor = store._.anchorPredictor ? store._.anchorPredictor : '(unselected)'
        const topMargin = this.props.isPreview ? 50 : 80;
        const title = this.props.isPreview ? 
            <div className='info-header ellipsis'>REWRITES</div>  :
            <div> 
                <h4 className='header'>Created Re-write Rules</h4>
                <div  style={{textAlign: 'center'}}> 
                <Checkbox checked={this.showPercent} onChange={() => { 
                    this.showPercent = !this.showPercent; }}>Proportion</Checkbox>
                <Checkbox checked={store._.showFilteredRewrite} onChange={() => { 
                    this.toggleShowFilteredGroup();
                }}>Show filtered distribution</Checkbox>
                </div>
            </div>
                
        return (
        <div className='full-width full-height' style={{position: 'relative'}}>    
            <Row>{ title }</Row>
            <Row>{ this.renderCtrlButtons() }</Row>
            <div className='overflow'
                style={{top: topMargin, bottom: 0,right: 0, left: 0, position: 'absolute'}}>
            { this.renderRewriteList(store._.rewriteHashes) }</div>
            {this.renderRewriteInspectModal()}
            { this.renderExportModal() }
        </div>);
    }
}