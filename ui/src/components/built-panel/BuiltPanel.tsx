import * as React from 'react';
import { Alert, Input, Button, Spin, Select } from 'antd'
import { BuiltType } from '../../stores/Interfaces';
import { store } from '../../stores/Store';
import { QueryCoder } from '../shared-components/QueryCoder';
import { observable } from 'mobx';
import { observer } from 'mobx-react';
import { Attribute } from '../../stores/Attribute';
import { DataGroup } from '../../stores/DataGroup';

export interface BuiltPanelProps {
    name: string;
    description: string;
    cmd: string;
    filter_cmd?: string;
    type: BuiltType;
}


@observer
export class BuiltPanel extends React.Component<BuiltPanelProps, {}> {
    public description: string;
    public name: string;
    public cmd: string;
    public selectedModel: string;

    @observable public msg: string;
    @observable public built: Attribute|DataGroup;

    constructor(props: BuiltPanelProps, context: any) {
        super(props, context);
        store._.resetFetchMsg();
        this.description = this.props.description;
        this.name = this.props.name;
        this.built =  this.props.type === 'attr' ?
             (this.name in store._.attrStore ? store._.attrStore[this.name] : null) :
             (this.name in store._.dataGroupStore ? store._.dataGroupStore[this.name] : null)
        this.cmd = this.props.cmd;
        this.changeCmd = this.changeCmd.bind(this);
        this.create = this.create.bind(this);
        this.msg = '';
    }

    public async create(): Promise<void> {
        store._.resetFetchMsg();
        if (!this.name || !this.description || !this.cmd) {
            this.msg = 'Input name, description, and command!'
            return;
        } else {
            this.msg = '';
            this.built = await store._.createBuiltsWithCmd(
                this.name, this.description, this.cmd, this.props.type);
        }
        store._.loadingData = "done";
    }

    public changeCmd(cmd: string): void {
        this.cmd = cmd;
    }

    public renderButtons(): JSX.Element {
        return <div style={{ textAlign: 'center' }}>
                <Button type='primary' onClick={() => { this.create()}}>
                    { this.built  ? 'Rewrite' : 'Create' }  { this.props.type }
                </Button>
                <Button type='primary' disabled={this.built === null} 
                    onClick={() => { 
                        store._.deleteBuilt(this.name, this.props.type);
                        this.msg = `${this.name} deleted!`
                        this.built = null;
                    }}>
                    Delete { this.props.type }
                </Button>
                <div className='ant-list-item-meta-description'>{this.msg}</div>
           </div>
    }

    public renderDistribution(): JSX.Element {
        return null;
    }

    public renderCreation(): JSX.Element {
        return <div className='full-height full-width'>
            <div style={{ marginBottom: 16 }}>
                <Input addonBefore="Name" defaultValue={this.props.name}
                    onChange={(e: React.SyntheticEvent<HTMLInputElement>) => { 
                        this.name = (e.target as HTMLInputElement).value.replace(/\s+/g, '_'); 
                    }} />
                </div>
            <div style={{ marginBottom: 16 }}>
                <Input addonBefore="Description"  defaultValue={this.props.description}
                    onChange={(e: React.SyntheticEvent<HTMLInputElement>) => { 
                        this.description = (e.target as HTMLInputElement).value; 
                    }} />
            </div>
            <div style={{ marginBottom: 16 }}>
                <div className='info-header'>Command</div>
                <QueryCoder 
                    cmd={ this.props.cmd } 
                    readOnly={ false } 
                    changeCmd={ this.changeCmd }
                    multiLines={ true } />
            </div>
            { this.renderButtons() }
        </div>
    }
    protected renderSelectModelList(): JSX.Element {
        const dataList = store._.selectedPredictors.slice();
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => {  this.selectedModel = v as string; }}
            defaultValue={ this.selectedModel }
            dropdownMatchSelectWidth={false}
            placeholder="Select rewrite rules"
            size="small">
                {dataList.map(d => {
                    return <Select.Option 
                    key={d}>{d}</Select.Option>
                })}
        </Select>
    }

    public render(): JSX.Element {
        return <div className='full-height full-width'>
        <Spin style={{height: '100%', width: '100%'}} size='large' 
            spinning={store._.loadingData === 'pending'}>
            { this.renderCreation() }
            { this.renderDistribution() }
        </Spin>
        </div>
    }
}
