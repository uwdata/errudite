/**
 * 2018/05/07
 * wtshuang@cs.uw.edu
 * This is the answer panel for showing the answer info integrated in the instance panel.
 */

import * as React from 'react';
import ResizeAware from 'react-resize-aware';
import { Row, Col, Popover, Divider, Checkbox, Button, Modal, Tooltip } from 'antd';
import { observer } from 'mobx-react';
import { observable } from 'mobx';
import { store } from '../../stores/Store';

import { AttrBar } from './AttrBar';
import { InstanceKey } from '../../stores/InstanceKey';
import { Attribute } from '../../stores/Attribute';
import { QueryCoder } from '../shared-components/QueryCoder';
import { BuiltAttrPanel } from '../built-panel/BuiltAttrPanel';
import { ExportPanel } from '../shared-components/ExportPanel';



@observer
export class AttrPanel extends React.Component<{isPreview: boolean}, {}> {
    @observable private showPercent: boolean;
    @observable private displayModal: "rewrite_attr"|"save_attr"|"";

    @observable private name: string;
    private description: string;
    private cmd: string;

    constructor (props: any, context: any) {
        super(props, context);
        this.renderAttrOverview = this.renderAttrOverview.bind(this);
        this.renderAttrDetail = this.renderAttrDetail.bind(this);
        this.renderPreview = this.renderPreview.bind(this);
        this.toggleShowFilteredAttr = this.toggleShowFilteredAttr.bind(this);
        this.toggleShowRewrites = this.toggleShowRewrites.bind(this);
        this.showPercent = false;
        this.displayModal = '';
        this.setInfo = this.setInfo.bind(this);
        this.setInfo(null);
    }

    private setInfo(attr: Attribute): void {
        if (attr === null) {
            this.description = '';
            this.cmd = '';
            this.name = '';
        } else {
            this.description = attr.description;
            this.cmd = attr.cmd;
            this.name = attr.name;
        }
    }

    /**
     * The function used when the attribute panel is in compact mode.
     * @param name the name of the attribute.
     */
    private renderAttrOverview(name: string, filteredAttrList: Attribute[]): JSX.Element {
        const highlightedInstances = store._.highlightedInstances.slice();
        const id = `attr-distribution-${name}-preview-${store._.anchorPredictor}`;
        const attr = name in store._.attrStore ? store._.attrStore[name] : null;
        return <Row key={id}>
            <Popover title={`Hovered attribute: ${name}`} placement='topLeft'
                content={this.renderPreview(attr, highlightedInstances)} >
                <Col span={24}><small className='ellipsis clickable'>{name}</small></Col>
            </Popover>
            <Col span={24} className='full-height'><div id={id} className='container'>
            <ResizeAware style={{ position: 'relative' }}>
                {({ width, height }) => {
                    return width > 100 ? null : <AttrBar 
                        anchorPredictor={store._.anchorPredictor}
                        filteredAttrList={filteredAttrList}
                        showPercent={this.showPercent}
                        key={`${id}-${width}`}
                        isPreview={true} width={width}
                        attr={ attr }
                        highlightedInstances={highlightedInstances}
                        containerId={id} /> }}
            </ResizeAware>
            </div></Col>
            <Col span={24}><Divider className='divider-compact'/></Col>
        </Row>
    }

    /**
     * The function used when the attribute panel is in expanded mode.
     * @param name the name of the attribute.
     */
    private renderAttrDetail(name: string, filteredAttrList: Attribute[]): JSX.Element {
        const highlightedInstances = store._.highlightedInstances.slice();
        const id = `attr-distribution-${name}-detail-${store._.anchorPredictor}`;
        const attr = name in store._.attrStore ? store._.attrStore[name] : null;
        return <Row key={id}>
            <Col span={16} ><div id={id} className='container'>
                <ResizeAware style={{ position: 'relative' }}>
                    {({ width, height }) => {
                        return width < 0.15 * document.body.clientWidth ? null :  <AttrBar 
                            anchorPredictor={store._.anchorPredictor}
                            filteredAttrList={filteredAttrList}
                            showPercent={this.showPercent}
                            key={`${id}-${width}`} 
                            highlightedInstances={highlightedInstances}
                            isPreview={false} 
                            width={width}
                            attr={ attr }
                            containerId={id}/>}}
                </ResizeAware>
            </div></Col>
            <Col span={8} className='full-height'>
                <Popover 
                    title={`Hovered attribute: ${name}`} placement='topLeft'
                    content={this.renderPreview(attr, highlightedInstances)} >
                    <h4 className='ant-list-item-meta ant-list-item-meta-title ellipsis'>
                        {name}
                    </h4>
                </Popover>
                
                <QueryCoder cmd={attr ? attr.cmd : ''} changeCmd={null}
                    multiLines={true} readOnly={true}/>
                {/*<div className='ant-list-item-meta ant-list-item-meta-description'>
                    <div className='full-width'>{store._.attrStore[name].description}</div>
                </div>*/}
                <Row style={{textAlign: 'right'}}> { this.renderInfoButton(attr) } </Row>
            </Col>
            <Col span={24}><Divider className='divider-compact'/></Col>
        </Row>
    }

    private renderPreview(attr: Attribute, highlightedInstances: InstanceKey[]): JSX.Element {
        if (attr === null ) {
            return null;
        }
        return <Row style={{width: document.body.clientWidth * 0.3}}>
        <Row className='full-height overflow'>
            <h4 className='ant-list-item-meta ant-list-item-meta-title'>
                { attr.name }
            </h4>
            {/*<QueryCoder changeCmd={null} cmd={attr ? attr.cmd : ''} multiLines={true} readOnly={true}/>*/}
            <div className='ant-list-item-meta ant-list-item-meta-description'>
                <div>{ attr.description }</div>
                
            </div>
        </Row>
        <Col span={24}><Divider style={{marginTop: 0, marginBottom: 5, marginLeft: 8, marginRight: 8 }}/></Col>
    </Row>
    }

    private renderRewriteAttrModal(): JSX.Element {
        return <Modal
            key={this.name}
            title={`Customize Data Attribute`}
            destroyOnClose={true}
            width={document.body.clientWidth*0.7}
            //style={{ top: document.body.clientHeight * 0.05, height: document.body.clientHeight * 0.4}}
            visible={ this.displayModal === 'rewrite_attr' }
            onCancel={ () => { this.setInfo(null); this.displayModal= '' }}
            footer={null}>
            <BuiltAttrPanel
                filter_cmd={ null }  
                //key={ this.name + store._.activeCmd }
                name={ this.name }
                description={ this.description }  
                cmd={ this.cmd } type='attr' />
        </Modal>
    }

    public renderExportModal(): JSX.Element {
        if (!this.displayModal) { return null; }
        return <Modal
            key={this.displayModal}
            destroyOnClose={true}
            title={`Export the Data Attribute!`}
            visible={ this.displayModal === "save_attr" }
            footer={null}
            onCancel={() => { this.displayModal = ''; }}>
            <ExportPanel key={this.displayModal} 
                builts={store._.attrHashes.slice()}
                filename={this.displayModal} type="attr" />
        </Modal>
    }

    public renderInfoButton(attr: Attribute): JSX.Element {
        return (
            <div style={{textAlign: 'left'}}>
                <Tooltip title="Rewrite attr / Inspect distribution"><Button 
                    shape='circle' icon='edit' size='small' className='info-button'
                    onClick={ () => {
                        this.setInfo(attr);
                        this.displayModal = "rewrite_attr";
                    } } /></Tooltip>
                <Tooltip title="Delete the attribute"><Button 
                    shape='circle' icon='delete' size='small' className='info-button'
                    onClick={ () => { store._.deleteBuilt(attr.name, 'attr') } } /></Tooltip>
            </div>
        )
    }


    private renderAttrs(): JSX.Element {
        const filteredAttrList = store._.filteredAttrList;
        const renderFunc = this.props.isPreview ? this.renderAttrOverview : this.renderAttrDetail;
        /*
        const performs = store._.attrHashes.filter(name => {
            for (let metric of store._.metricNames) {
                if (name.startsWith(metric + '_')) { return true; }
            }
            return false;
        });
        const otherAttrs = store._.attrHashes.filter(name => 
            performs.indexOf(name) === -1);
        */

        return <div>
            { store._.attrHashes.map(name => renderFunc(name, filteredAttrList)) }
        </div>
    }

    public async toggleShowFilteredAttr(): Promise<void> {
        store._.showFilteredAttr = !store._.showFilteredAttr;
        if (store._.showFilteredAttr) {
            if (store._.lastExecutedCmd !== '') {
                store._.filteredAttrList = await store._.getAttrDistribution(
                    store._.attrHashes.slice(), 
                    store._.lastExecutedCmd, true, null, null);
            }
        } else {
            store._.showRewriteAttr = false;
            store._.filteredAttrList = [];
        }
    }

    public async toggleShowRewrites(): Promise<void> {
        store._.showRewriteAttr = !store._.showRewriteAttr;
        store._.filteredAttrList = await store._.getAttrDistribution(
            store._.attrHashes.slice(), store._.lastExecutedCmd, false,
            null, null);
    }

    public renderCtrlButtons(): JSX.Element {
        const onCreate = () => {
            store._.resetFetchMsg();
            this.setInfo(null);
            this.displayModal = "rewrite_attr";
        }
        const onSave = () => {
            this.displayModal = "save_attr";
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
            { buildBtn('Add Attr', 'plus', onCreate) }
            { buildBtn('Save Attrs', 'save', onSave) }
        </div>
    }

    /**
     * Render the answers.
     */
    public render(): JSX.Element {
        const topMargin = this.props.isPreview ? 80 : 100;
        return <div className='full-width full-height' style={{position: 'relative'}}>
            {!this.props.isPreview ? 
                <div>
                    <h4 className='header'>Attributes</h4>
                    <div  style={{textAlign: 'center'}}>
                        <Checkbox checked={this.showPercent} onChange={() => { 
                            this.showPercent = !this.showPercent; }}>Proportion</Checkbox>
                        <Checkbox checked={store._.showFilteredAttr} onChange={() => { 
                            this.toggleShowFilteredAttr();
                        }}>Show filtered distribution</Checkbox>
                        <Checkbox 
                            disabled={!store._.showFilteredAttr}
                            checked={store._.showRewriteAttr} 
                            onChange={() => { 
                            this.toggleShowRewrites();
                        }}>Show Rewritten instances</Checkbox>
                    </div>
                    { this.renderCtrlButtons() }
                </div> : 
                <div>
                    <Divider />
                    <div className='info-header ellipsis'>ATTRIBUTES</div>
                    { this.renderCtrlButtons() }
                </div>
            }
            <div className='overflow'
                style={{top: topMargin, bottom: 0,right: 0, left: 0, position: 'absolute'}}>
                { this.renderAttrs() }
            </div>
            { this.renderExportModal() }
            { this.renderRewriteAttrModal() }
        </div>;
    }
}