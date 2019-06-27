import * as React from 'react';
import { Alert, Input, Button } from 'antd'
import { BuiltType } from '../../stores/Interfaces';
import { store } from '../../stores/Store';
import { observable } from 'mobx';
import { observer } from 'mobx-react';

export interface ExportPanelProps {
    filename:string;
    builts: string[];
    type: BuiltType;
}

@observer
export class ExportPanel extends React.Component<ExportPanelProps, {}> {
    @observable private name: string;
    constructor(props: ExportPanelProps, context: any) {
        super(props, context);
        store._.resetFetchMsg();
        this.name = this.props.filename;
    }

    public async export(): Promise<void> {
        await store._.service.exportBuilt(this.name, this.props.type);
    }

    public render(): JSX.Element {
        const disableOK = this.name === '';
        return <div className='full-height full-width'>
            <div style={{ marginBottom: 16 }}>
                <Input addonBefore="File name" 
                    defaultValue={this.name}
                    onChange={(e: React.SyntheticEvent<HTMLInputElement>) => { 
                        this.name = (e.target as HTMLInputElement).value; 
                    }} />
                </div>
            <div style={{ textAlign: 'center' }}>
                <Button type='primary'
                    disabled={disableOK} onClick={() => { this.export() }}>
                    {disableOK ? 'Input file name!' : 'Save to file'}
                </Button>
           </div>            
        </div>
    }
}
