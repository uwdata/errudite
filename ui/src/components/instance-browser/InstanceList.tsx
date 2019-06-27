/**
 * The whole instance list
 * wtshuang@cs.uw.edu
 * 2018/01/15
 */

import * as React from 'react';
import { observer } from 'mobx-react';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';
import { InstanceKey } from '../../stores/InstanceKey';
import { QAInstancePanel } from './QAInstancePanel';
import { VQAInstancePanel } from './VQAInstancePanel';
import { Button } from 'antd';

@observer
export class InstanceList extends React.Component<{}, {}> {
    private viewType: string;
    constructor(props: any, context: any) {
        super(props, context);
        this.viewType = 'qlist';
    }

    public renderButtons(instanceCount: number): JSX.Element {
        let total: number = 0;
        if (store._.sampleInfo !== null) {
            if (store._.browserTarget === "group") {
                total = store._.sampleInfo.counts.correct + store._.sampleInfo.counts.incorrect;
            } else {
                total = store._.sampleInfo.counts.rewritten;
            }
        }
        return <div style={{textAlign: "center"}}>
            <Button type='primary' size='small' 
                onClick={() => { store._.getMoreSamples(-1) }}
                disabled={store._.sampleCacheIdx <= 0} >
                Prev page
            </Button>
            <Button type='primary' size='small'
                onClick={() => { store._.getMoreSamples(1) }}
                disabled={store._.sampleCacheIdx + instanceCount >= total}>
                Next page
            </Button>
            <div>
                <i style={{color: '#999999'}}>Displaying #{store._.sampleCacheIdx}-
                    {store._.sampleCacheIdx + instanceCount} samples.</i>
            </div>
        </div>
    }

    /**
     * Rendering function called whenever new logs are generated.
     */
    public render(): JSX.Element {
        // group the identifiers based on the qid.
        if (store._.sampledInstances.length === 0) { return null; }
        const qids = store._.sampledInstances.map(s => s.qid).filter(utils.uniques);
        const instanceHash = utils.groupBy<InstanceKey>(store._.sampledInstances, 'qid');
        /*
        if (store.sampleMethod === 'best' || store.sampleMethod === 'worst') {
            qids = store.instanceListQids.slice().sort((aqid: string, bqid: string) => {
                return (store.sampleMethod === 'best' ? 1 : -1) * (
                    store.iStoreOrigin[aqid].perform.f1[store.anchorPredictor] - 
                    store.iStoreOrigin[bqid].perform.f1[store.anchorPredictor]);
            });
        }
        */
        return (
        <div key={this.viewType} className='full-width full-height'>
            
            <div key={qids.map(i => i).join('-')}
            style={{left: 0, right: 0, top: 25, bottom: 50, position: 'absolute'}} className='overflow'>
            {qids.map((qid: string) => {
                const curClass = utils.genClass(
                    this.viewType, 'instance-panel', [qid, instanceHash[qid].length]);
                if (store._.dataType === 'qa') {
                    return <QAInstancePanel 
                        instances={instanceHash[qid]} key={curClass.key}/>
                } else {
                    return <VQAInstancePanel 
                        instances={instanceHash[qid]} key={curClass.key}/>
                }
            }) }
            </div>
            <div style={{bottom: 10, left: 0, right: 0, position: 'absolute'}}>
                { this.renderButtons(Object.keys(instanceHash).length) }
            </div>
        </div>);
     }
}    