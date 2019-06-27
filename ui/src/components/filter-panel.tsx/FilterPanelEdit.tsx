import { FilterPanel } from "./FilterPanel";

import * as React from 'react';
import { Icon, Menu, Dropdown, Select } from 'antd';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { SampleMethod } from '../../stores/Interfaces';

export class FilterPanelRewrite extends FilterPanel {

    protected renderRewriteSelectList(): JSX.Element {
        const dataList = store._.rewriteHashes.slice();
        dataList.push( "(Exclude rewrite)");
        return <Select 
            style={{minWidth: '150px'}}
            onChange={(v) => {  
                const value = v === "(Exclude rewrite)" ? "unrewritten" : v as string;
                store._.setSelectedRewrite(value) 
            }}
            value={ store._.sampleRewrite }
            dropdownMatchSelectWidth={false}
            placeholder="Select rewrite rules"
            size="small">
                {dataList.map(d => {
                    return <Select.Option 
                    key={d}>{d}</Select.Option>
                })}
        </Select>
    }


    public renderSampleStrategy(): JSX.Element {
        const genSampleMethodName = (key: SampleMethod) => {
            let menu = '';
            switch(key) {
                case 'rand':  menu = 'randomly from instances rewritten by'; break;
                case 'correct_flip': menu = `prioritizing ${store._.anchorPredictor} flipped to correct by`; break;
                case 'incorrect_flip': menu = `prioritizing ${store._.anchorPredictor} flipped to incorrect by`; break;
                case 'changed': menu = `prioritizing ${store._.anchorPredictor} prediction changed by`; break;
                case 'unchanged': menu = `prioritizing ${store._.anchorPredictor} prediction not changed by`; break;
            }
            return menu;
        }
        const sampleMethods = ['rand', 'correct_flip', 'incorrect_flip', 'changed', 'unchanged'];
        const sampleMenu = <Menu 
            onClick={(e) => {store._.sampleMethod = e.key as SampleMethod;}}>
            {sampleMethods.map((key: SampleMethod) =>
                <Menu.Item key={key}>{genSampleMethodName(key)}</Menu.Item>)}
        </Menu>
        const includeList = this.renderGroupSelectList("include");
        const excludeList = this.renderGroupSelectList("exclude");

        const msg = <div>
            Sample 10 instances
            <Dropdown overlay={sampleMenu}>
                <a className="ant-dropdown-link" href="#">
                    {` ${genSampleMethodName(store._.sampleMethod)} `} 
                    <Icon type="down" /></a></Dropdown>
                { this.renderRewriteSelectList() }
                (originally in {includeList} and not in {excludeList})
            </div>;
        return msg;
    }

    protected renderStatsInfo(): JSX.Element {
        const info = store._.sampleInfo;
        return info === null ? null : 
            <div>
                {`Rewritten instances: ${info.counts.rewritten} 
                (${utils.percent(info.stats.coverage)} of total), `}
                {`Prediction changed: ${info.counts.prediction_changed} 
                (${utils.percent(info.stats.changed_coverage)} of total instances, 
                ${utils.percent(info.stats.changed_rate)} of rewritten instances)`}
            </div>
    }
}