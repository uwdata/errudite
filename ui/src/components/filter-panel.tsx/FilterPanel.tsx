/**
 * The control panel for everything.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */

import * as React from 'react';
import { Button, Row, Col, Icon, Menu, Dropdown, Modal, InputNumber, Select } from 'antd';
import { observable } from 'mobx';
import { observer } from 'mobx-react';
import { store } from '../../stores/Store';
import { QueryCoder } from '../shared-components/QueryCoder';
import { BuiltGroupPanel } from '../built-panel/BuiltGroupPanel';
import { DataGroup } from '../../stores/DataGroup';

export class FilterBar extends React.Component<{title: string|JSX.Element; child: JSX.Element}, {}> {
    constructor(props: {title: string|JSX.Element; child: JSX.Element}, context: any) {
        super(props, context);
    }
    public render(): JSX.Element {
        return <Row className='filter-background'>
            <Col className='filter-title' span={8}>{this.props.title}</Col>
            <Col className='filter-foreground' span={16}>{this.props.child}</Col>
        </Row>
    }
}

@observer
export class FilterPanel extends React.Component<{}, {}> {
    @observable protected displayModal: boolean;
    @observable protected name: string;

    protected description: string;
    protected cmd: string;

    constructor(props: {}, context: any) {
        super(props, context);
        this.displayModal = false;
        this.setInfo(null);
        this.changeGroupList = this.changeGroupList.bind(this);
    }
    protected setInfo(group: DataGroup): void {
        if (group === null) {
            this.description = '';
            this.cmd = '';
            this.name = '';
        } else {
            this.description = group.description;
            this.cmd = group.cmd;
            this.name = group.name;
        }
    }

    protected changeGroupList(values: string[], listType: "include"|"exclude"): void {
        if (listType === 'include') {
            store._.includeSampleGroups = values.slice();
            store._.excludeSampleGroups = store._.excludeSampleGroups
                .filter(v => values.indexOf(v) === -1);
        } else {
            store._.excludeSampleGroups = values.slice();
            store._.includeSampleGroups = store._.includeSampleGroups
                .filter(v => values.indexOf(v) === -1);
        }
        store._.computeActiveCmdBasedOnGroups();
    }

    protected renderGroupSelectList(listType: "include"|"exclude"): JSX.Element {
        const dataList = store._.dataGroupHashs.slice();
        const disableList = listType === 'include' ? 
            store._.excludeSampleGroups.slice() :
            store._.includeSampleGroups.slice();
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => {  this.changeGroupList(v as string[], listType) }}
            value={listType === "include" ? store._.includeSampleGroups : store._.excludeSampleGroups}
            dropdownMatchSelectWidth={false}
            placeholder="Select groups"
            size="small"
            mode="multiple" >
                {dataList.map(d => {
                    return <Select.Option 
                    key={d} 
                    disabled={disableList.indexOf(d) > -1}>{d}</Select.Option>
                })}
        </Select>
    }

    protected renderRewriteGroupModal(): JSX.Element {
        return <Modal
            key={this.name}
            title={`Customize Data Group`}
            destroyOnClose={true}
            width={ document.body.clientWidth * 0.8 }
            style={{ top: document.body.clientHeight * 0.05, height: document.body.clientHeight * 0.4}}
            visible={ this.displayModal }
            onCancel={ () => { this.setInfo(null); this.displayModal = false; }}
            footer={null}>
            <BuiltGroupPanel  
                key={this.name}
                name={ this.name }
                description={ this.description }  
                cmd={ this.cmd } type='group' />
        </Modal>
    }

    public renderSampleStrategy(): JSX.Element {
        return null;
    }

    protected renderCmd(): JSX.Element {
        //store._.includeSampleGroups.join('-') + store._.excludeSampleGroups.join('-') + 
        return <div className='full-width'> 
            <QueryCoder key={ 
                `${store._.setCmd}` }
                readOnly={false} 
                cmd={store._.activeCmd}
                multiLines={true} 
                changeCmd={  store._.setActiveCmd } />
            <div>Preview the filter on <InputNumber size='small' key={store._.totalSize}
                min={0} max={store._.totalSize} value={store._.testSize}
                onChange={(d: number) => {
                    store._.testSize = d < 0 ? 0 : 
                        d > store._.totalSize ? store._.totalSize : d;
                }} /> instances
            </div>
        </div>
    }

    protected renderCreateGroupBtn(): JSX.Element {
        const menu = <Menu 
            onClick={(e) => {}}>
            <Menu.Item key="create" onClick={() => { 
                this.setInfo(null);
                this.cmd = store._.activeCmd;
                this.displayModal = true; 
            }}>Create a new group</Menu.Item>
            <Menu.SubMenu title='Update an existing group'>
                {store._.dataGroupHashs.map((key: string) => 
                    <Menu.Item key={key} onClick={() => {
                        if (key in store._.dataGroupStore) {
                            this.setInfo(store._.dataGroupStore[key]);
                            if (this.cmd !== '') {
                                this.cmd = store._.activeCmd;
                            }
                            this.displayModal = true; 
                        }
                    }}>{key}</Menu.Item>
                )}
            </Menu.SubMenu>
            <Menu.SubMenu title='Merge into an existing group'>
                {store._.dataGroupHashs.map((key: string) => 
                    <Menu.Item key={key} onClick={() => {
                        if (key in store._.dataGroupStore) {
                            this.setInfo(store._.dataGroupStore[key]);
                            this.cmd = store._.activeCmd;
                            this.displayModal = true; 
                            const group = store._.dataGroupStore[key];
                            let cmd = store._.activeCmd;
                            if (group.cmd && store._.activeCmd) {
                                cmd = `(${group.cmd}) or (${store._.activeCmd})`
                            } else if (group.cmd) {
                                cmd = group.cmd;
                            } else if (store._.activeCmd) {
                                cmd = store._.activeCmd;
                            }
                            this.cmd = cmd;
                            this.displayModal = true; 
                        }
                    }}>{key}</Menu.Item>
                )}
            </Menu.SubMenu>
        </Menu>
        const disable = store._.activeCmd === null;
        return <Dropdown overlay={menu} disabled={disable}>
        <Button style={{ marginLeft: 8 }}  size='small' type='primary'>
            <Icon type="save" />{
                disable ? 'Build predicates first!' : 'Record the Group '}<Icon type="down" />
        </Button>
        </Dropdown>
    }

    protected renderStatsInfo(): JSX.Element {
        return null;
    }

    protected renderBtnGroup(): JSX.Element {
        const recordButton = this.renderCreateGroupBtn();
        let infoDisplay = this.renderStatsInfo();            
        return <div style={{paddingTop: 5, textAlign: "center"}}> 
            <i style={{color: '#999999'}}>{infoDisplay}</i>
            {recordButton}
            <Button type='primary' size='small'
                onClick={ () => {
                    if (store._.browserTarget === 'group') {
                        store._.sampleInstance(
                            store._.activeCmd,
                            store._.sampleMethod, 
                            null, store._.testSize, null)

                    } else {
                        store._.sampleInstance(
                            store._.activeCmd,
                            store._.sampleMethod, 
                            store._.sampleRewrite, store._.testSize, null);
                    }
                }}>
                <Icon type="filter" />Get samples
            </Button>
            </div>
    }

    protected renderSubRow(title: string, child: JSX.Element): JSX.Element {
        return <Row gutter={10}>
        <Col sm={8}	lg={4} xxl={4}><div className='filter-subtitle'>{title}</div></Col>
        <Col sm={16} lg={20} xxl={20}>{child}</Col>
    </Row>
    }

    /**
     * The major rendering
     */
    public render(): JSX.Element {
        //const rules = store.dataSliceStore[store.selectedDataSlice].slice()
        return <div className='full-width full-height'>
            <div className='overflow'
                style={{backgroundColor: '#f9f9f9', 
                top: 15, maxHeight: 110, 
                left: 0, right: 0, position: 'absolute'}}>
                {this.renderSubRow('Get Instances', this.renderSampleStrategy())}
                {this.renderSubRow('Filter CMD', this.renderCmd())}
            </div>
            <div style={{top: 120, left: 0, right: 0, position: 'absolute'}}>
                {this.renderBtnGroup()}
            </div>
            {this.renderRewriteGroupModal()}
        </div>
    }
}