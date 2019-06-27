import * as React from 'react';
import * as d3 from 'd3';
import { observer } from 'mobx-react';
import { store } from '../../stores/Store';
import { utils } from '../../stores/Utils';

interface StackDatum {
    y: number;
    y0: number;
    y0_ori: number;
    y_ori: number;
    type: string;
    group: string;
}
export interface Value {
    name: string;
    counts: {
        correct?: number;
        incorrect?: number;
        flip_to_correct?: number;
        flip_to_incorrect?: number;
        other?: number;
    }
}

interface GroupBarMeta {
    domain?: [number, number];
    isPreview: boolean;
    width: number;
    height: number;
    values: Value[];
    showPercent: boolean;
    containerId: string;
    anchorPredictor: string;
}

@observer
export class GroupBar extends React.Component<GroupBarMeta, {}> {
    private margin: {top: number, right: number; bottom: number; left: number; };
    private size: {svgHeight: number; svgWidth: number; width: number; height: number; };
    private scale: {
        colorScale: d3.ScaleOrdinal<string, string>;
        labelScale: d3.ScaleBand<string>;
        barScale: d3.ScaleLinear<number, number>;
    };
    private barData: StackDatum[];
    private hovertip: any;

    private node: any;
    private svg: any;//d3.Selection<any, number, any, {}>; // svg
    private panel: d3.Selection<any, number, any, {}>; // main part
    
    constructor(props: any, context: any) {
        super(props, context);
        this.margin = { top: 2, right: 20, bottom: 2, left: 45 };
        this.size = { svgWidth: 0, width: 0, height: 0, svgHeight: 0 };
        this.init = this.init.bind(this);
    }

    public computeStack(): StackDatum[] {
        const data: StackDatum[] = [];
        const base = this.scale.barScale.domain()[0];
        this.props.values.forEach((v: Value) => {
            const total = d3.sum(Object.values(v.counts));
            const dividend = (this.props.showPercent || v.name === "all_instances") && total > 0 ? total : 1;
            if (!this.props.anchorPredictor) {
                data.push({  
                    type: 'total',
                    y0: this.scale.barScale.domain()[0] / dividend, 
                    y: total / dividend,
                    y0_ori: this.scale.barScale.domain()[0], 
                    y_ori: total, group: v.name 
                });
            } else {
                const flip_to_correct = utils.getAttr(v.counts, 'flip_to_correct', 0);
                const flip_to_incorrect = utils.getAttr(v.counts, 'flip_to_incorrect', 0);
                const incorrect = utils.getAttr(v.counts, 'incorrect', 0);
                const correct = utils.getAttr(v.counts, 'correct', 0);
                const other = utils.getAttr(v.counts, 'other', 0);
                data.push({ 
                    type: 'flip_to_correct',
                    y0: base * 1.0 / dividend, 
                    y: flip_to_correct * 1.0 / dividend,
                    y0_ori: base, 
                    y_ori: flip_to_correct, 
                    group: v.name});
                data.push({ 
                    type: 'flip_to_incorrect',
                    y0: (base + flip_to_correct) * 1.0 / dividend,
                    y0_ori: (base + flip_to_correct),
                    y: flip_to_incorrect * 1.0 / dividend,
                    y_ori: flip_to_incorrect, group: v.name});
                data.push({ 
                    type: 'incorrect',
                    y0: (base + flip_to_incorrect + flip_to_correct) * 1.0 / dividend,
                    y0_ori: (base + flip_to_incorrect + flip_to_correct),
                    y: incorrect * 1.0 / dividend,
                    y_ori: incorrect, group: v.name});
                data.push({ 
                    type: 'correct',
                    y0: (base + flip_to_incorrect + flip_to_correct + incorrect) * 1.0 / dividend,
                    y0_ori: (base + flip_to_incorrect + flip_to_correct + incorrect),
                    y: correct * 1.0 / dividend,
                    y_ori: correct, group: v.name});
                data.push({ 
                    type: 'other',
                    y0: (base + flip_to_incorrect + flip_to_correct + incorrect + correct) * 1.0 / dividend,
                    y0_ori: (base + flip_to_incorrect + flip_to_correct + incorrect + correct),
                    y: other * 1.0 / dividend,
                    y_ori: other, group: v.name});
            }
        });
        return data;
    }

    /**
     * Rendering function called whenever new logs are generated.
     */
    public render(): JSX.Element {
        return <svg ref={node => this.node = node} 
        width={this.size.svgWidth} height={this.size.svgHeight}></svg>
     }

    public componentDidMount(): void {
        if (this.props.values.length === 0 ) { return null; }
        this.init();
        if (!this.size.svgWidth || !this.size.svgHeight || 
            (this.size.svgWidth < 50 && !this.props.isPreview)) { return null; }
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node);
        this.svg.selectAll('*').remove();
        if (!this.panel) { this.panel = this.svg.append('g'); }
        this.panel.attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.genScales();
        this.barData = this.computeStack();
        this.renderAttrBar();
        if (this.props.isPreview) {
            this.panel.selectAll('text').remove();
        } else {
            this.renderText();
            this.renderCount();
        }
     }

     public componentDidUpdate(): void {
        if (this.props.values.length === 0 ) { return null; }
        this.init();
        if (!this.size.svgWidth || !this.size.svgHeight || 
            (this.size.svgWidth < 50 && !this.props.isPreview)) { return null; }
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node);
        if (!this.panel) {
            this.panel = this.svg.append('g');
        }
        this.panel.attr('transform', `translate(${this.margin.left}, ${this.margin.top})`);
        this.genScales();
        this.barData = this.computeStack();
        this.renderAttrBar();
        if (this.props.isPreview) {
            this.panel.selectAll('text').remove();
        } else {
            this.renderText();
            this.renderCount();
        }
     }

    
     private init(): void {
        if (this.props.isPreview) {
            this.margin = { top: 2, right: 0, bottom: 2, left: 0 };
        } else {
            this.margin = { top: 2, right: 10, bottom: 2, left: 60 };
        }
        if (this.props.height) {
            this.size.svgHeight = this.props.height;
        } else if (document.getElementById(this.props.containerId) !== null) {
            this.size.svgHeight = document.getElementById(this.props.containerId).clientHeight;
        } else {
            this.size.svgHeight = 20;
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
    }

    private genScales(): void {
        if (!this.scale) {
            this.scale = {
                colorScale: d3.scaleOrdinal<string, string>()
                    .domain(['flip_to_incorrect', 
                        'flip_to_correct', 'incorrect', 'correct', 'other', 'total'])
                    .range([
                        utils.answerColor.incorrect.dark,
                        utils.answerColor.correct.dark,
                        utils.answerColor.incorrect.light,
                        utils.answerColor.correct.light,
                        utils.answerColor.groundtruth.light,
                        utils.answerColor.groundtruth.light]),
                barScale: d3.scaleLinear<number, number>().range([0, this.size.width]),
                labelScale: d3.scaleBand<string>().range([this.size.height, 0]).padding(0.2),
            };
        }

        let domain: [number, number];
        if (this.props.domain) {
            domain = this.props.domain;
            if (domain[0] === domain[1]) { domain[0] = 0; }
            domain[0] = 0;
        } else {
            domain = d3.extent(this.props.values.map(v => d3.sum(Object.values(v.counts)) ));
            if (domain[0] > 0) { domain[0] = 0; }
        }
        this.scale.barScale.domain(this.props.showPercent || 
            this.props.values.filter(v => v.name ===  "all_instances").length > 0 ? [0, 1]: domain );
        this.scale.labelScale.domain(this.props.values.map(d => d.name));
    }

    private renderAttrBar(): void {
        const bar = this.panel.selectAll('.bar').data(this.barData, (d: StackDatum) => 
            `bar-${store._.dataGroupStore[d.group]}-${this.props.anchorPredictor}-${d.type}`);
        const enter = bar.enter()
            .append('rect').attr('class', 'bar')
            .on('click', (d) => { console.log(d); })
        // enter & update
        enter.merge(bar as any)//.transition().duration(1000)
            .attr('y', d => this.scale.labelScale(d.group) || 0)
            .attr('height', this.scale.labelScale.bandwidth() || 0)
            .attr('x', d => this.scale.barScale(d.y0) || 0)
            .attr('width', d => this.scale.barScale(d.y) > 0 ? this.scale.barScale(d.y) : 0)
            .attr('fill', d => this.scale.colorScale(d.type));
        //EXIT
        bar.exit().remove();
        if (this.barData.length === 0) {
            this.panel.selectAll('.bar').remove();
            return;
        }
    }

    private renderCount(): void {
        const count = this.panel.selectAll('.count')
            .data(this.props.values, (d: Value) => `count-${d.name}`);
        const enter = count.enter()
            .append('text').attr('class', 'count')
            .on('click', (d) => { console.log(d); })
        // enter & update
        enter.merge(count as any)//.transition().duration(1000)
            .attr('y', d => (this.scale.labelScale(d.name) + this.scale.labelScale.bandwidth() / 2) || 0)
            .attr("text-anchor", 'end')
            .attr('dy', 2)
            .attr('x', -10)
            .attr('font-size', 12)
            .text(d => d3.max(this.barData
                    .filter(b => b.group === d.name)
                    .map(d => d.y_ori + d.y0_ori)) || 0)
        //EXIT
        count.exit().remove();
        if (this.props.values.length === 0) {
            this.panel.selectAll('.count').remove();
            return;
        }
    }

    private renderText(): void {
        const text = this.panel.selectAll('.text').data(this.barData, (d: StackDatum) => 
            `text-${store._.dataGroupStore[d.group]}-${this.props.anchorPredictor}-${d.type}`);
            
        const enter = text.enter().append('text').attr('class', 'text');
        // enter & update
        enter.merge(text as any)//.transition().duration(1000)
            .attr('y', d => this.scale.labelScale(d.group) + this.scale.labelScale.bandwidth() / 2)
            .attr("text-anchor", 'middle')
            .attr('dy', 3)
            //.attr('dx', -5)
            .attr('x', d => this.scale.barScale(d.y0) + this.scale.barScale(d.y) / 2)
            .attr('font-size', 10)
            //.attr('fill', 'white')
            .text(d => d.y === 0 ? '' : this.props.showPercent ? d3.format(".0%")(d.y) : d.y_ori)
        //EXIT
        text.exit().remove();
        if (this.barData.length === 0) {
            this.panel.selectAll('.text').remove();
            return;
        }
    }

    private renderHovertip(groupName: string, hoveredObj: any) {
        const self = this;
        const cls = `${groupName}-inspect`;
        this.hovertip.html(`<div></div>`);
        this.hovertip.show(groupName, hoveredObj);
        d3.selectAll(`.${cls}-rewrite`).on('click', () =>{ console.log(groupName, 'rewrite'); self.hovertip.hide();});
        d3.selectAll(`.${cls}-info`).on('click', () =>{ console.log(groupName, 'info'); self.hovertip.hide(); })
    }
}