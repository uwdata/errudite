/**
 * The main entry of the instance browser.
 */

import * as React from 'react';
import * as d3 from 'd3';
import { InstanceList } from './InstanceList';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

import { observer } from 'mobx-react';
import { Tag, Switch } from 'antd';
import { FilterPanelGroup } from '../filter-panel.tsx/FilterPanelGroup';
import { FilterPanelRewrite } from '../filter-panel.tsx/FilterPanelEdit';

@observer
export class InstanceBrowser extends React.Component<{}, {}> {
    public renderEncoder(): JSX.Element {
        if (store._.dataType === 'qa') {
            return <span>
                answer encoding:
                <b>groundtruth</b>,
                <span className='token primary-answer'>prediction by {store._.anchorPredictor }</span>
                (
                    <span className='token primary-answer correct'>correct</span>, 
                    <span className='token primary-answer incorrect'>incorrect</span>
                ),
                <span style={{backgroundColor: d3.schemeGreys[9][2]}}>
                    model prediction distributions</span>
            </span>;
        } else {
            return <span>
                <Tag color={ utils.answerColor.correct.dark }>Correct prediction</Tag>
                <Tag color={ utils.answerColor.incorrect.dark }>Incorrect prediction</Tag>
            </span>
        }
    }

    public render(): JSX.Element {
        //const rules = store.dataSliceStore[store.selectedDataSlice].slice();
        return (
            <div style={{ top: 24, bottom: 24, left: 24, right: 24, position: 'absolute' }}>
                <div style={{height: 200}}>
                    <h4 className='header'>
                        Find instances to explore (
                            <Switch 
                                size="small"
                                onChange={(checked: boolean) => { 
                                    const view = checked ? "rewrite" : "group";
                                    store._.switchBrowserTarget(view);
                                }}
                                checkedChildren="with" 
                                checked={store._.browserTarget === "rewrite"}
                                unCheckedChildren="without" /> rewrites)
                    </h4>
                    <div style={{ top: 25, left: 0, right: 0, position: 'absolute' }}>
                        { store._.browserTarget === "group" ? <FilterPanelGroup /> : <FilterPanelRewrite /> }
                    </div>
                </div>
                <div style={{ top: 220, bottom: 0, left: 0, right: 0, position: 'absolute' }}>
                    <h4 className='header'>Returned instances ({this.renderEncoder()})</h4>
                    <div style={{ top: 25, bottom: 0, left: 20, right: 20, position: 'absolute' }}>
                        <InstanceList/></div>
                </div>
            </div>
        )
    }
}