import * as React from 'react';
import { observer } from 'mobx-react';
import { observable } from 'mobx';
import { Spin, Layout, Card, Icon, Popover, Menu, Modal, message } from 'antd';

import { store } from '../stores/Store';
import { Ctrlbar } from './Ctrlbar';
import { GroupManager } from './group-manager/GroupManager';
import { RewriteManager } from './rewrite-manager/RewriteManager';

import { InstanceBrowser } from './instance-browser/InstanceBrowser';
import { ModelOverviewPanel } from './model-overview/ModelOverviewPanel';
import { AttrPanel } from './attr-manager/AttrPanel';

@observer
export class App extends React.Component<{}, {}> {
    /**
     * The entry of all the UI
     */
    @observable private closeLeftPanel: boolean;
    @observable private closeRightPanel: boolean;
    @observable height: number;
    @observable width: number;
    constructor(state: {}, context: any) {
        super(state, context);
        this.closeRightPanel = true;
        this.closeLeftPanel = false;
        this.height = 0;
        this.width = 0;
    }
    public async componentWillMount(): Promise<void> {
        await store.getHandler();
        store._.init(); 
    }

    public async componentDidMount(): Promise<void> {
        this.height = document.getElementById('ui-container').clientHeight;
        this.width = document.getElementById('ui-container').clientWidth;
        window.addEventListener('resize', () => {
            this.height = document.getElementById('ui-container').clientHeight;
            this.width = document.getElementById('ui-container').clientWidth;
        })
    }

    public componentDidUpdate(): void {
        this.renderFetchMsg();
    }

    private renderFetchMsg(): void {
        message.config({ maxCount: 1 });
          
        if (!store._.isValidFetch()) {
            message.error(store._.validFetchMsg);
        }
    }

    public render(): JSX.Element {
        const toolbarHeight = 30;
        const height = this.height - toolbarHeight; //0.95 * clientHeight;
        const ctrlPanel = !this.closeLeftPanel ?
            <Card className='full-width full-height'>
                <div style={{height: '30%' }} id='model-overview'><ModelOverviewPanel/></div>
                <div style={{height: '70%' }}>
                    <AttrPanel key={`${this.closeLeftPanel}`} isPreview={this.closeLeftPanel} />
                </div>
            </Card> :
            <div className='full-width full-height' style={{ position: 'relative'}}>
            <Menu className='full-width' style={{textAlign: 'center' }}
                defaultSelectedKeys={['1']} mode="inline">
                <Menu.SubMenu key="1" title={
                    <Popover placement="rightTop" trigger='click'
                        content={<div id='model-overview' style={{
                            margin: 20, 
                            maxWidth: 0.3 * this.width, 
                            maxHeight: 0.3 * height}}><ModelOverviewPanel/></div>}>
                        <Icon type="book" />
                    </Popover>
                }></Menu.SubMenu>
            </Menu>
            <div style={{top: 50, bottom: 0, left: 24, right: 24, position: 'absolute' }}>
                <AttrPanel key={`${this.closeLeftPanel}`} isPreview={true} />
            </div>
            </div>;
        const attrPanel = <Card className='full-width full-height'>
                <div style={{height: '50%' }} className='group-manager'>
                    <GroupManager isPreview={this.closeRightPanel} 
                        highlightedInstances={store._.highlightedInstances}/></div>
                <div style={{height: '50%' }} className='rewrite-manager'>
                    <RewriteManager isPreview={this.closeRightPanel}
                        highlightedInstances={store._.highlightedInstances}/></div>
            </Card>;
        return (
            <Spin style={{height: '100%', width: '100%'}} size='large' spinning={store._.loadingData === 'pending'}>
            <Layout style={{height: this.height, width: this.width}}>
                <Layout.Header className='full-width' style={{height: toolbarHeight}}> 
                    <Ctrlbar height={toolbarHeight}/>
                </Layout.Header>
                <Layout style={{top: toolbarHeight, bottom: 0, right: 0, left: 0, position: 'absolute' }}>
                <Layout.Sider width={ '30%' }  theme='light' 
                    style={{ height: '100%', }}
                    collapsible={true} collapsedWidth={100}
                    collapsed={this.closeLeftPanel} 
                    onCollapse={() => {this.closeLeftPanel = !this.closeLeftPanel }}>
                    {ctrlPanel}
                </Layout.Sider>
                <Layout.Content style={{ height: '100%', padding: 10}}>
                    <Card className='full-width full-height'>
                        {/* The instance browser */}
                        <InstanceBrowser />
                    </Card>
                </Layout.Content>
                {
                <Layout.Sider 
                    width={ '30%' } 
                    theme='light'
                    style={{ height: '100%' }} 
                    collapsible={true} reverseArrow={true} collapsedWidth={100}
                    collapsed={this.closeRightPanel} 
                    onCollapse={() => {this.closeRightPanel = !this.closeRightPanel }}>
                    {attrPanel}
                </Layout.Sider>
                }
                </Layout>
            </Layout>
            </Spin>
        );
    }
}