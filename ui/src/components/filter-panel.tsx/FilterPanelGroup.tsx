import { FilterPanel } from "./FilterPanel";

import * as React from 'react';
import { Icon, Menu, Dropdown } from 'antd';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { SampleMethod } from '../../stores/Interfaces';

export class FilterPanelGroup extends FilterPanel {
    public renderSampleStrategy(): JSX.Element {
        const genSampleMethodName = (key: SampleMethod) => {
            let menu = '';
            switch(key) {
                case 'worst': menu = `${key} predicted by ${store._.anchorPredictor}`; break;
                case 'best': menu = `${key} predicted by ${store._.anchorPredictor}`; break;
                case 'borderline': menu = `that ${store._.anchorPredictor} has lowest confidence on`; break;
                case 'rand':  menu = `randomly`; break;
            }
            return menu;
        }
        const sampleMethods = ['worst', 'best', 'borderline', 'rand'];
        const sampleMenu = <Menu 
            onClick={(e) => {store._.sampleMethod = e.key as SampleMethod;}}>
            {sampleMethods.map((key: SampleMethod) =>
                <Menu.Item key={key}>{genSampleMethodName(key)}</Menu.Item>)}
        </Menu>
        const includeList = this.renderGroupSelectList("include");
        const excludeList = this.renderGroupSelectList("exclude");

        let msg = <div>
            Sample 10 instances
            <Dropdown overlay={sampleMenu}>
                <a className="ant-dropdown-link" href="#">
                    {` ${genSampleMethodName(store._.sampleMethod)} `} 
                    <Icon type="down" /></a></Dropdown>
                that are in {includeList} and not in {excludeList}
            </div>;
        return msg;
    }

    protected renderStatsInfo(): JSX.Element {
        const info = store._.sampleInfo;
        return info === null ? null : 
           <div>
               {`Filtered instances: ${info.counts.correct + info.counts.incorrect} 
               (${utils.percent(info.stats.coverage)} of total), `}
               {`Error: ${info.counts.incorrect} 
               (${utils.percent(info.stats.local_error_rate)} of slice, 
               ${utils.percent(info.stats.global_error_rate)} of total, 
               ${utils.percent(info.stats.error_coverage)} of all errors)`}
       </div>;
    }
}