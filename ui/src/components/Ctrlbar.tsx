/**
 * The control panel for everything.
 * wtshuang@cs.uw.edu
 * 2018/01/12
 */

import * as React from 'react';
import { observer } from 'mobx-react';
import { Icon, Row, Col, Menu } from 'antd';

import { store } from '../stores/Store';

@observer
export class Ctrlbar extends React.Component<{height: number}, {}> {
    constructor(props: any, context: any) {
        super(props, context);
        this.init = this.init.bind(this);
    }

    /**
     * Load the initial identifiers.
     */
    private async init(): Promise<void> { 
        await store.getHandler();
        store._.init(); 
    }

    /**
     * The major rendering
     */
    public render(): JSX.Element {
        return (
            <Row className='full-width full-height'>
            <Col span={16} className='full-height'><h3 style={{lineHeight: `${this.props.height}px`, color: 'white'}}>
            Errudite: An Interactive Tool for Scalable and Reproducible Error Analysis</h3></Col>
            <Col span={8} className='full-height' style={{textAlign: 'right'}}>
                <Menu theme="dark" mode="horizontal" style={{lineHeight: `${this.props.height}px`}}>
                    {/*<Menu.Item key='upload' onClick={ this.init }>
                        <Icon type='upload' /><span>Load</span>
                    </Menu.Item>*/}
                    <Menu.Item key='undo' 
                        disabled={ store._.procedureIdx <= 0 }
                        onClick={ () => { store._.redoUndoHandler(-1) } }>
                        <Icon type='undo' /><span>Undo Query</span>
                    </Menu.Item>
                    <Menu.Item key='redo' 
                        disabled={ store._.procedureIdx >= store._.historyList.length-1 }
                        onClick={ () => { store._.redoUndoHandler(1) } }>
                        <Icon type='redo' /><span>Redo Query</span>
                    </Menu.Item>
                </Menu>
            </Col>
        </Row>
        )
    }
}