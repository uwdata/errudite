import * as React from 'react';
import * as d3 from 'd3';
import * as _d3Tip from "d3-tip";
const d3Tip = (_d3Tip as any).bind(d3);
import * as vegaStat from 'vega-statistics';

import { store } from '../../stores/Store';
import { InstanceKey } from '../../stores/InstanceKey';
import { Attribute, AttrValue, AttrItem } from '../../stores/Attribute';
import { utils } from '../../stores/Utils';

export interface AttrPreviewProps {
    height?: number;
    attr: Attribute;
    showPercent: boolean;
    filteredAttrList: Attribute[];
    anchorPredictor: string;
    isPreview?: boolean;
    highlightedInstances: InstanceKey[];
    containerId: string;
    width: number;
}

export interface FlatDatum {
    idx: number;
    incorrect: number;
    correct: number;
}

export class AttrBar extends React.Component<AttrPreviewProps, {}> {
    private margin: {top: number, right: number; bottom: number; left: number; };
    private size: {svgHeight: number; svgWidth: number; width: number; height: number; };
    private scale: {
        bins: (string|number)[];
        colorScale: d3.ScaleOrdinal<string, string>;
        attrScale_discrete: d3.ScaleBand<string>;
        attrScale_continue: d3.ScaleLinear<number, number>;
        barScale: d3.ScaleLinear<number, number>;
        barScaleRewrite: d3.ScaleLinear<number, number>;
    };
    private hovertip: any;
    private node: any;
    private svg: any;//d3.Selection<any, number, any, {}>; // svg
    private panel: d3.Selection<any, number, any, {}>; // main part
    private axisPanel: d3.Selection<any, number, any, {}>; 

    private binCount: number;
    private flatValues: FlatDatum[];
    private flatValuesRewrite: FlatDatum[]; 

    private domain: (string|number)[];
    private counts: { correct: AttrItem[], incorrect: AttrItem[] };
    private countsRewrite: { correct: AttrItem[], incorrect: AttrItem[] };

    private flatCounts: { correct: AttrValue[], incorrect: AttrValue[] };
    private flatCountsRewrite: { correct: AttrValue[], incorrect: AttrValue[] };

    constructor(props: any, context: any) {
        super(props, context);
        this.margin = { top: 10, right: 10, bottom: 100, left: 35 };
        this.size = { svgWidth: 0, width: 0, height: 0, svgHeight: 0 };
        this.binCount = 10;
        this.flatValues = [];
        this.domain = [];
        this.counts = { correct: [], incorrect: [] };
        this.countsRewrite = { correct: [], incorrect: [] };
        this.flatCounts = { correct: [], incorrect: [] };
        this.flatCountsRewrite = { correct: [], incorrect: [] };
    }

    private hasRewrite(): boolean {
        return d3.sum(this.countsRewrite.correct.map(c => c[1])) +
            d3.sum(this.countsRewrite.incorrect.map(c => c[1])) > 0;
    }
     /**
     * Rendering function called whenever new logs are generated.
     */
    public render(): JSX.Element {
        return <svg ref={node => this.node = node}
            width={this.size.svgWidth} height={this.size.svgHeight}>
        </svg>
     }

     /**
      * Get the bin idx for a specific number / string
      * @param d 
      */
    private binIdx (d: number|string): number {
        if (this.props.attr.dtype === 'continuous') {
            const domain = this.scale.bins;
            for (let i = 0; i < domain.length - 1; i++) {
                if (d >= domain[i] && d < domain[i + 1]) {
                    return i;
                } else if (i === domain.length - 2 && d === domain[i + 1]) {
                    return i;
                }
            }
            return 0;
        } else {
            const idx = this.scale.bins.indexOf(d);
            return idx === -1 ? 0 : idx;
        }
    }

    /**
     * Flatten the values to fit into bins.
     */
    private genFlatValue(): void {
        const initFlatValue = () => {
            let flatValues: FlatDatum[] = [];
            if (this.props.attr.dtype === 'continuous') {
                flatValues = this.scale.bins.slice(0, this.scale.bins.length).map((b, idx) => {
                    return { idx: idx, correct: 0, incorrect: 0 };
                });
            } else {
                flatValues = this.scale.bins.map((b, idx) => {
                    return { idx: idx, correct: 0, incorrect: 0};
                });
            }
            return flatValues
        }

        let flatValues: FlatDatum[] = initFlatValue();
        let flatValuesRewrite: FlatDatum[] = initFlatValue();
        const convertFunc = (data: AttrItem[], isCorrect: "correct"|"incorrect", flatValues) => {
            for (let item of data) {
                const binIdx = this.binIdx(item[0]);
                if (binIdx < flatValues.length && binIdx > -1) {
                    flatValues[binIdx][isCorrect] += item[1];
                }
            }
            return flatValues;
        }
        flatValues = convertFunc(this.counts.correct, "correct", flatValues);
        flatValues = convertFunc(this.counts.incorrect, "incorrect", flatValues);
        flatValuesRewrite = convertFunc(this.countsRewrite.correct, "correct", flatValuesRewrite);
        flatValuesRewrite = convertFunc(this.countsRewrite.incorrect, "incorrect", flatValuesRewrite);

        // convert the discrete data
        if ( this.props.attr.dtype === 'categorical') {
            flatValues = flatValues.sort((a, b) => {
                return b.correct + b.incorrect - a.correct - a.incorrect;
            });
            //this.binCount = 5;
            const flatValues_sliced = flatValues.slice(0, this.binCount);
            const flatValues_removed = flatValues.slice(this.binCount);
            // build the idx list for the slices
            const idxes_sliced = flatValues_sliced.map( f => f.idx );
            const flatValuesRewrite_sliced = flatValuesRewrite
                .filter(f => idxes_sliced.indexOf(f.idx) !== -1)
                .sort((a, b) => idxes_sliced.indexOf(a.idx) - idxes_sliced.indexOf(b.idx));
            const flatValuesRewrite_removed = flatValuesRewrite
                .filter(f => idxes_sliced.indexOf(f.idx) === -1);
            let bins = flatValues_sliced.map(f => this.scale.bins[f.idx]);
            bins.push('other');
            const computeOther: FlatDatum = {
                idx: bins.length,
                correct: d3.sum(flatValues_removed.map(c => c.correct)),
                incorrect: d3.sum(flatValues_removed.map(c => c.incorrect))
            }
            const computeOtherRewrite: FlatDatum = {
                idx: bins.length,
                correct: d3.sum(flatValuesRewrite_removed.map(c => c.correct)),
                incorrect: d3.sum(flatValuesRewrite_removed.map(c => c.incorrect))
            }
            flatValues_sliced.push(computeOther);
            flatValuesRewrite_sliced.push(computeOtherRewrite);
            flatValues = flatValues_sliced.map((f, idx) => {
                return {idx: idx, correct: f.correct, incorrect: f.incorrect}
            });
            flatValuesRewrite = flatValuesRewrite_sliced.map((f, idx) => {
                return {idx: idx, correct: f.correct, incorrect: f.incorrect}
            });
            this.scale.bins = bins;
            this.scale.attrScale_discrete.domain(this.scale.bins as string[]);
        }
        this.flatValues = flatValues;
        this.flatValuesRewrite = flatValuesRewrite;
    }

    public componentDidMount(): void {
        this.init(); 
        if (!this.domain || !this.counts) { return null; }
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node);
        this.svg.selectAll('*').remove();
        this.panel = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.axisPanel = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.genScales();
        this.genFlatValue();
        // if is showPercent and is now preview, always displaying the percentage, so the max is 1
        this.scale.barScale.domain([0, 
            this.props.showPercent && !this.props.isPreview ? 1 :
            d3.max(this.flatValues.map(f => f.correct + f.incorrect)) || 0]);
        this.scale.barScaleRewrite.domain([0, 
            this.props.showPercent && !this.props.isPreview ? 1 :
            d3.max(this.flatValuesRewrite.map(f => f.correct + f.incorrect)) || 0]);
        //if (this.props.showAttrs.length === 0) {
        if (this.props.isPreview) {
            this.renderBackground();
        }
        this.renderAttrBar(this.flatValues, this.scale.barScale, "ori");
        if (!this.props.isPreview) {
            this.renderAttrBar(this.flatValuesRewrite, this.scale.barScaleRewrite, "rewrite");
            this.renderAxis();
        }
        this.renderHighlightedInstances(this.props.highlightedInstances);
        this.hovertip = d3Tip().attr('class', 'tip d3-tip').offset([-8, 0]);
        this.panel.call(this.hovertip);
    }

     public componentDidUpdate(): void {
        this.init();
        if (!this.domain || !this.counts) { return null; }
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node);
        this.svg.selectAll('.tip').remove();
        this.panel.attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.axisPanel.attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.genScales();
        this.genFlatValue();
        this.scale.barScale.domain([0, 
            this.props.showPercent && !this.props.isPreview ? 1 :
            d3.max(this.flatValues.map(f => f.correct + f.incorrect)) || 0]);
        this.scale.barScaleRewrite.domain([0, 
            this.props.showPercent && !this.props.isPreview ? 1 :
            d3.max(this.flatValuesRewrite.map(f => f.correct + f.incorrect)) || 0]);
        if (this.props.isPreview) {
            this.renderBackground();
        }
        this.renderAttrBar(this.flatValues, this.scale.barScale, "ori");
        if (!this.props.isPreview) {
            this.renderAttrBar(this.flatValuesRewrite, this.scale.barScaleRewrite, "rewrite");
            this.renderAxis();
        }
        this.renderHighlightedInstances(this.props.highlightedInstances);
        this.hovertip = d3Tip().attr('class', 'tip d3-tip').offset([-8, 0]);
        this.panel.call(this.hovertip);
     }

     

     private init(): void {
        // get the data
        if (this.props.attr === null) {
            this.domain = null;
            this.counts = null;
            this.countsRewrite = { correct: [], incorrect: [] };
            this.flatCounts = { correct: [], incorrect: [] };
            this.flatCountsRewrite = { correct: [], incorrect: [] };
        }
        else if (this.props.filteredAttrList === null || this.props.filteredAttrList.length === 0) {
            this.domain = this.props.attr.domain;
            this.counts = this.props.attr.counts;
            this.countsRewrite = { correct: [], incorrect: [] };
            this.flatCounts = this.props.attr.flatCounts;
            this.flatCountsRewrite = { correct: [], incorrect: [] };
        } else {
            const attrList = this.props.filteredAttrList
                .filter(a => a.name === this.props.attr.name);
            const attr = attrList.length > 0 ? attrList[0] : null;
            const attrListRewrite = this.props.filteredAttrList
                .filter(a => a.name === this.props.attr.name + "_on_rewritten");
            const attrRewrite = !this.props.isPreview && attrListRewrite.length > 0 ? attrListRewrite[0] : null;
            if (attr === null) { //TODO
                this.domain = this.props.attr.domain;
                this.counts = this.props.attr.counts;
                this.flatCounts = this.props.attr.flatCounts;
            } else {
                this.domain = attr.domain;
                this.counts = attr.counts;
                this.flatCounts = attr.flatCounts;
            }
            if (attrRewrite === null) {
                // update the 
                this.countsRewrite = { correct: [], incorrect: [] };
                this.flatCountsRewrite = { correct: [], incorrect: [] };
            } else {
                if (this.props.attr.dtype === "continuous" && attrRewrite.domain.length >=2) {
                    this.domain[0] = Math.min(this.domain[0] as number, attrRewrite.domain[0] as number) || 0;
                    this.domain[1] = Math.max(this.domain[1] as number, attrRewrite.domain[1] as number) || 1;
                } else {
                    this.domain = this.domain.concat(attrRewrite.domain).filter(utils.uniques);
                }
                this.countsRewrite = attrRewrite.counts;
                this.flatCountsRewrite = attrRewrite.flatCounts;
            }
        }
        this.binCount = this.props.isPreview ? 5 : 10;

        if (this.props.isPreview) {
            this.margin = { top: 0, right: 2, bottom: 0, left: 2 };
            this.size.svgHeight = 15;
        } else {
            this.margin = { top: 10, right: 20, bottom: 60, left: 40 };
            this.size.svgHeight =  this.hasRewrite() ? 140 : 110;
            if (this.props.attr.dtype === 'continuous') {
                this.margin.bottom -= 20;
                this.size.svgHeight -= 20;
            }
        }
        if (this.props.height) {
            this.size.svgHeight = this.props.height;
        }
        if (this.props.width) {
            this.size.svgWidth = this.props.width;
        } else if (document.getElementById(this.props.containerId) !== null) {
            this.size.svgWidth = document.getElementById(this.props.containerId).clientWidth;
        } else {
            this.size.svgWidth = 200;
        }
        this.size.width = this.size.svgWidth - this.margin.right - this.margin.left;
        this.size.height = this.size.svgHeight - this.margin.top - this.margin.bottom;
        
        //console.log(this.props.attr === null, !this.props.filteredAttrList, this.props.filteredAttrList, this.domain, this.counts);
    }

    private genScales(): void {
        const paddingSize = this.props.isPreview ? 0.01 : 0.2;
        const height = this.hasRewrite() ? this.size.height / 2 : this.size.height;
        if (!this.scale) {
            this.scale = {
                bins: [],
                colorScale: d3.scaleOrdinal<string, string>()
                    .domain(['incorrect', 'correct', 'total'])
                    .range([
                        utils.answerColor.incorrect.light,
                        utils.answerColor.correct.light,
                        utils.answerColor.groundtruth.light,
                    ]),
                barScale: d3.scaleLinear<number, number>().range([height, 0]),
                barScaleRewrite: d3.scaleLinear<number, number>().range([height, this.size.height]),
                attrScale_discrete: d3.scaleBand<string>().range([0, this.size.width]).padding(paddingSize),
                attrScale_continue: d3.scaleLinear<number, number>().range([0, this.size.width])
            };
        }
        this.scale.barScale.range([height, 0]);
        this.scale.barScaleRewrite.range([height, this.size.height]);
        if (this.props.attr.dtype === 'continuous') {
            const extent = this.domain.filter(utils.uniques) as number[];
            if (extent.length === 1) {
                extent.push(extent[0] === 1 ? extent[0] + 0.1 : extent[0] + 1);
            }
            // the performance distribution is always [0, 1]
            const binIdxes = d3.range(0, this.binCount - 2);
            const binFunction = d3.scaleQuantile()
                .domain(d3.merge<number>([
                    this.flatCounts.correct.concat(this.flatCountsRewrite.correct) as number[], 
                    this.flatCounts.incorrect.concat(this.flatCountsRewrite.incorrect) as number[]]))
                .range(binIdxes);

            this.scale.attrScale_continue.domain(extent);
            let bins = d3.merge([
                [extent[0]],binFunction.quantiles(), 
                [extent[1]]]).filter(utils.uniques) as number[];            
            if ( (bins[bins.length-1] - bins[0] <= 1) || bins.length < this.binCount * 0.6) {
                const bins_ = vegaStat.bin({extent: extent, nice: false, maxbins: this.binCount });
                this.scale.bins = d3.range(bins_.start, bins_.stop + bins_.step, bins_.step);
            } else {
                //bins.push(extent[1] === 1 ? extent[1] + 0.1 : extent[1] + 1);
                this.scale.bins = bins;
            }
        } else {
            this.scale.bins = this.domain.slice();//this.attr.stats.map(s => s.value);
            this.scale.attrScale_discrete.domain(this.scale.bins as string[]);
        }
        /*
        if (this.props.attr.name === "groundtruths_length") {
            this.scale.attrScale_continue.domain([1, 20]);
            this.scale.bins = [1, 2, 3, 4, 5, 6, 7, 8, 20]
        }
        if (this.props.attr.name === "prediction_length") {
            this.scale.attrScale_continue.domain([1, 50]);
            this.scale.bins = [1, 3, 5, 7, 9, 11, 13, 20, 50]
        }
        */
        this.scale.bins = this.scale.bins.filter(utils.uniques);
    }

    private renderBackground(): void {
        this.svg.selectAll('.axis').remove();
        if (this.panel.selectAll('.preview-background').empty()) {
            this.panel.append('rect')
                .attr('class', 'preview-background')
                .attr('width', this.size.width)
                .attr('width', this.size.width)
                .attr('height', this.size.height)
                .attr('fill', '#f9f9f9')
        }
    }

    private renderAxis(): void {
        const height = this.hasRewrite() ? this.size.height / 2 : this.size.height;
        this.svg.selectAll('.preview-background').remove();
        const scale = this.props.attr.dtype === 'continuous' ? 
            this.scale.attrScale_continue : this.scale.attrScale_discrete;
        if (this.axisPanel.selectAll('.axis').empty()) {
            this.axisPanel.append('g').attr('class', 'x axis');
            this.axisPanel.append('g').attr('class', 'y axis');
        }
        this.axisPanel.selectAll('.yrewrite').remove();
        if (this.hasRewrite()) {
            this.axisPanel.append('g').attr('class', 'yrewrite axis')
                //.attr('transform', `translate(0, ${height})`)
            this.axisPanel.select('.axis.yrewrite')
            .call(d3.axisLeft(this.scale.barScaleRewrite).ticks(2));
        }
        this.axisPanel.select('.axis.y').call(d3.axisLeft(this.scale.barScale).ticks(2));
        //console.log(this.props.attr.name, this.scale.bins)
        this.axisPanel.select('.axis.x')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(scale as any).tickValues(this.scale.bins).tickFormat( 
                this.props.attr.dtype === "categorical"   || this.scale.attrScale_continue.domain()[1] >= 1 ? null : d3.format(".2g")) )
            .selectAll("text")
            .attr("y", 0)
            .attr("x", 9)
            .attr("dy", ".35em")
            .attr("transform", "rotate(90)")
            .style("text-anchor", "start");
    }

    private renderAttrBar(
        flatValues: FlatDatum[], 
        barScale: d3.ScaleLinear<number, number>, type: "rewrite"|"ori"): void {
        const self = this;
        const data = [];
        flatValues.forEach(f => {
            if (this.props.isPreview) {
                data.push({ type: 'total', y0: 0, y: f.correct + f.incorrect, idx: f.idx });
            } else {
                const divider = this.props.showPercent ? f.correct + f.incorrect : 1;
                data.push({ 
                    type:  'anchor-model-incorrect', 
                    y0: 0, y: f.incorrect / divider, idx: f.idx });
                data.push({
                    type: 'others',  y0: f.incorrect / divider,  y: f.correct / divider, idx: f.idx });
            }
        });
        const bar = this.panel.selectAll(`.bar-${type}`).data(data, (d) => `bar-${type}-${d.idx}`);
        const enter = bar.enter().append('rect').attr('class', `bar-${type}`);
        enter.merge(bar as any)//.transition().duration(1000)
            .attr('y', d => (type === "rewrite" ? barScale(d.y0) : barScale(d.y + d.y0)) || 0)
            .attr('height', d => Math.abs(barScale(d.y0) - barScale(d.y + d.y0)) || 0)
            .attr('x', (d) => {
                return this.props.attr.dtype === 'continuous' ?
                    this.scale.attrScale_continue(this.scale.bins[d.idx] as number) :
                    this.scale.attrScale_discrete(this.scale.bins[d.idx] as string);
            })
            .attr('width', (d) => {
                if (this.props.attr.dtype === 'continuous') {
                    let width = this.scale.attrScale_continue(this.scale.bins[d.idx+1] as number) - 
                    this.scale.attrScale_continue(this.scale.bins[d.idx] as number);
                    return width > 0 ? width : 0;
                } else{
                    return this.scale.attrScale_discrete.bandwidth();
                }   
            })
            .style('fill', d => this.scale.colorScale(d.type))
            .style('cursor', 'pointer')
            .on('click', function(d) { self.props.isPreview ? null : self.setCmd(d, type); })
            .on('mouseover', function(d) { 
                self.props.isPreview ? null : self.mouseovered(d, self, this); })
            .on('mouseout', function() { 
                self.props.isPreview ? null : self.mouseouted(self); })
        bar.exit().remove();
        if (flatValues.length === 0) {
            this.panel.selectAll(`.bar-${type}`).remove();
            return;
        }
    }

    public setCmd(d: any, type: "rewrite"|"ori"): void {
        const wrapRewrite = (cmd: string) => {
            return type === "rewrite" ? `apply(${cmd}, rewrite="SELECTED")` : cmd; }
        let value = '';
        const attrName = wrapRewrite(`attr:${this.props.attr.name}`);
        if (this.props.attr.dtype === "continuous") {
            value = `${attrName} >= ${(this.scale.bins[d.idx] as number).toFixed(2)} and ` +
                `${attrName} < ${(this.scale.bins[d.idx+1] as number).toFixed(2)}`
        } else {
            value = `${attrName} == "${this.scale.bins[d.idx]}"`
        }
        if (d.type !== 'total') {
            const metric = store._.dataType === 'qa' ? 'f1' : 'accuracy';
            const not_icon = d.type === 'others' ? '==' : '<';
            const performName = wrapRewrite(`${metric}(model="${store._.anchorPredictor}")`)
            const modelPerform = `${performName} ${not_icon} 1`;
            value = `${value} and ${modelPerform}`;
        }
        if (store._.lastExecutedCmd.trim() === '') {
            store._.setActiveCmd(value, true, true);
        } else {
            store._.setActiveCmd([store._.lastExecutedCmd, value].join(' and '), true, true);
        }
    }

    private async renderHighlightedInstances(instances: InstanceKey[]): Promise<void> {
        if (instances === null || instances.length === 0) {
            this.panel.selectAll('.highlight').remove();
            return;
        }
        const colors = {
            origin: { dark: d3.schemePaired[3], light: d3.schemePaired[3] },
            rewrite: { dark: d3.schemePaired[2], light: d3.schemePaired[2] }
        }
        let highlights_ = await store._.service.getOneAttrOfInstances(this.props.attr.name, instances);
        highlights_ = highlights_ === null ? [] : highlights_;
        highlights_ = highlights_.filter(h => h !== null);
        const highlights = highlights_.map((v: AttrValue, idx: number) => {
                const binIdx = this.binIdx(v);
                const color = instances[idx].vid === 0 ? colors.origin : colors.rewrite;
                return { v:v, idx: binIdx, color: color.dark, instance: instances[idx] };
            });
        
        const lines = this.panel.selectAll('.highlight').data(highlights, 
            (d: {v: AttrValue, idx: number, color: string, instance: InstanceKey}) => 
            `highlight-${d.instance.qid}-${d.instance.vid}`);
        const enter = lines.enter()
            .append('line')
            .attr('class', 'highlight')
            .attr('y1', 0)
            .attr('y2', this.size.height)
            .attr('stroke-width', 3)
        // enter & update
        enter.merge(lines as any)//.transition().duration(1000)
            .attr('stroke', d => d.color)
            .attr('x1', d => {
                return this.props.attr.dtype === 'continuous' ?
                    this.scale.attrScale_continue(d.v as number) :
                    this.scale.attrScale_discrete(this.scale.bins[d.idx] as string) 
                        + this.scale.attrScale_discrete.bandwidth() / 2
            })
            .attr('x2', d => {
                return this.props.attr.dtype === 'continuous' ?
                    this.scale.attrScale_continue(d.v as number) :
                    this.scale.attrScale_discrete(this.scale.bins[d.idx] as string) 
                        + this.scale.attrScale_discrete.bandwidth() / 2
            })
        //EXIT
        lines.exit().remove();
        if (highlights.length === 0) {
            this.panel.selectAll('.highlight').remove();
            return;
        }
    }

    private mouseovered (d, self: AttrBar, obj: any): void {
        //const keywords = node.data.keywords.slice(0,3).map(d => `<div>${d.key}: ${d.count},</div>`).join('');
        const correct_dicorator = d.type === 'correct' ? '' : '!';
        let displayText: string = `<div><b>Value: </b> ${
            self.props.attr.dtype === 'continuous' ? 
                `[${(self.scale.bins[d.idx] as number).toFixed(2)}, 
                ${(self.scale.bins[d.idx+1] as number).toFixed(2)}]` : 
                self.scale.bins[d.idx]}</div>`;
        displayText += `<div><b>Type: </b> ${correct_dicorator}${store._.anchorPredictor}</div>`
        displayText += `<div><b>Count: </b> ${d.y > 1 ? d.y : d.y.toFixed(2)}</div>`
        //d.f1.forEach((f1: F1Datum) => {
        //    displayText += `<div><b>F1 [${f1.predictor}]: </b> ${f1.avg.toFixed(2)}</div>`
        //})
        self.hovertip.html(displayText);
        self.hovertip.show(obj);
    }
    

    /**
     * mouseout event on a node
     * @param node  <NodeDatum>         the node being clicked
     * @param Obj   <KeywordNetwork>    the keywordnetwork
     */
    
    private mouseouted (self: AttrBar): void {
        self.hovertip.hide();
    }
}