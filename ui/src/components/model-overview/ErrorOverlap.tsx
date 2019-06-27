
/**
 * The predictor comparison matrix for finding error leak
 * wtshuang@cs.uw.edu
 * 2018/03/19
 */

import * as React from 'react';
import * as d3 from 'd3';
import * as _d3Tip from "d3-tip";
const d3Tip = (_d3Tip as any).bind(d3);
import * as d3Legend from 'd3-svg-legend';
import { observer } from 'mobx-react';

import { ErrOverlap } from '../../stores/Interfaces';
import { utils } from '../../stores/Utils';
import { store } from '../../stores/Store';


export interface PredictorMatProp { // the property interface for this view
    overlaps: ErrOverlap[];
}

@observer
export class ErrorOverlapPanel extends React.Component<PredictorMatProp, {}> {
    private overlaps: ErrOverlap[];

    private margin: {top: number, right: number; bottom: number; left: number;};
    private size: {svgHeight: number; svgWidth: number; width: number; height: number;};
    private scale: {
        // x and y scale, where to put the circles
        xScale: d3.ScaleBand<number|string>;
        yScale: d3.ScaleBand<number|string>;
        // the r of one circle
        rScale: d3.ScaleLinear<number, number>;
    };

    private node: SVGElement;
    private svg: d3.Selection<any, number, any, {}>; // svg
    private panel: d3.Selection<any, number, any, {}>; // primary part
    private hovertip: any;
    private containerId: string;

    constructor(props: any, context: any) {
        super(props, context);
        this.containerId = 'predictor-mat';
        this.margin = { top: 10, right: 50, bottom: 80, left: 80 };
        this.size = { svgWidth: 0, width: 0, height: 0, svgHeight: 0 };
        /*
        this.filterIdentifiers = this.filterIdentifiers.bind(this);
        this.clickHandler = this.clickHandler.bind(this);
        this.hoverHandler = this.hoverHandler.bind(this);
        */
        this.overlaps = [];
    }

    /**
     * function called when the view is created
     */
    public componentDidMount() {
        this.init();
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node); // get the svg
        this.panel = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
        // init the size and scales
        this.overlaps = this.props.overlaps.slice();
        this.genScales();
        this.renderAxis();
        this.renderMat();
        this.renderLegend();
        this.hovertip = d3Tip().attr('class', 'tip d3-tip').offset([-8, 0]);
        this.panel.call(this.hovertip);
     }

    /**
     * The function called when the observable variables are modified
     */
    public componentDidUpdate() {
        this.init();
        this.node.style.width = `${this.size.svgWidth}px`;
        this.node.style.height = `${this.size.svgHeight}px`;
        this.svg = d3.select(this.node); // get the svg
        this.panel
            .attr('transform', `translate(${this.margin.left}, ${this.margin.top})`)
        // init the size and scales
        this.overlaps = this.props.overlaps.slice();
        this.genScales();
        this.renderAxis();
        this.renderMat();
        this.renderLegend();
        this.hovertip = d3Tip().attr('class', 'tip d3-tip').offset([-8, 0]);
        this.panel.call(this.hovertip);
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
     * Init the sizes
     */
    private init(): void {
        if (document.getElementById(this.containerId) !== null) {
            this.size.svgWidth = document.getElementById(this.containerId).clientWidth;
            this.size.svgHeight = document.getElementById(this.containerId).clientHeight;
        } else {
            this.size.svgWidth = 200;
            this.size.svgHeight = 200;
        }
        this.size.width = this.size.svgWidth - this.margin.right - this.margin.left;
        this.size.height = this.size.svgHeight - this.margin.top - this.margin.bottom;
        this.size.width = Math.min(this.size.width, this.size.height);
        this.size.height = this.size.width;
        //this.margin.bottom = this.size.svgHeight - this.margin.top - this.size.height;
        //this.margin.bottom = this.margin.bottom > 0 ? this.margin.bottom : 0;
        this.margin.left = (this.size.svgWidth - this.size.width - 50) / 2;
        this.margin.right = this.size.svgWidth - this.margin.left - this.size.width;
        this.margin.right = this.size.svgWidth - this.size.width - this.margin.left;
        this.margin.right = this.margin.right > 0 ? this.margin.right : 0;

    }

    /**
     * Build the scale
     */
    private genScales(): void {
        const domain = d3.extent(this.overlaps.map(e => e.count));
        if (domain[0] === 0) { domain[0] = 1; }
        this.scale = {xScale: null, yScale: null, rScale: null};
        this.scale.xScale = d3.scaleBand<string>()
            .domain(this.overlaps.map(c => c.perform_a)).range([0, this.size.width]).padding(0.2);
        this.scale.yScale = d3.scaleBand<number|string>()
            .domain(this.overlaps.map(c => c.perform_b)).range([this.size.height, 0]).padding(0.2);
        this.scale.rScale = d3.scaleSqrt<number, number>()
            //.domain([10e-5, d3.max(compareMat.map(e => e.count))])
            .domain(domain)
            .range([5, this.scale.xScale.bandwidth() / 2]);
    }

    /**
     * Render the axis.
     */
    private renderAxis(): void {
        const tickFunc = (e: string|number) => {
            return typeof e === 'string' ? e : e.toFixed(2);
        }
        /*
        const xbrush = d3.brushX<any>().extent([[0, -8], [this.size.width, 8]])
            .on('brush start', () => this.brushstart())
            //.on('brush', () => this.brushing()) // draw the pc
            .on('end', () => this.brushing('x', xbrush));
        const ybrush = d3.brushY<any>().extent([[-8, 0], [8, this.size.height]])
            .on('brush start', () => this.brushstart())
            .on('end', () => this.brushing('y', ybrush));
        */
        this.panel.selectAll('.axis').remove();
        if (this.panel.selectAll('.axis').empty()) {
            const xaxis = this.panel.append('g')
                .attr('class', 'x axis') 
                .attr('transform', `translate(0,${this.size.height})`)

            const yaxis = this.panel.append('g').attr('class', 'y axis');
            this.panel.append("text").attr('class', 'xtext axis')
                .attr("transform", 
                    `translate(${this.size.width/2}, ${this.size.height + this.margin.top + 50})`)
                .style("text-anchor", "middle");

            // text label for the y axis
            this.panel.append("text").attr('class', 'ytext axis')
                .attr("transform", "rotate(-90)")
                .attr("y", -70)
                .attr("x",0 - (this.size.height / 2))
                .attr("dy", "1em")
                .style("text-anchor", "middle");

        }
        this.panel.select('.axis.x')
            .call(d3.axisBottom(this.scale.xScale)
            .tickFormat(t => tickFunc(t)))
            .selectAll("text")
            .attr("y", 0)
            .attr("x", 9)
            .attr("dy", ".35em")
            .attr("transform", "rotate(90)")
            .style("text-anchor", "start");
        this.panel.select('.axis.y').call(d3.axisLeft(
            this.scale.yScale).tickFormat(t => tickFunc(t)) );
    
        const model_a = this.overlaps.length > 0 ? this.overlaps[0].model_a : '';
        const model_b = this.overlaps.length > 0 ? this.overlaps[0].model_b : '';
        // text label for the x axis
        this.panel.select('.xtext').text(model_a);
        this.panel.select('.ytext').text(model_b);

        //this.panel.select('.x.brush').call(xbrush);
        //this.panel.select('.y.brush').call(ybrush); //.selectAll('rect')//.attr('x', -8).attr('width', 16);        
    
    }

    private renderLegend(): void {
        const legendSize = (d3Legend.legendSize()
            .scale(this.scale.rScale) as any)
            .shape('circle')
            .labelAlign('end')
            .shapePadding(this.size.width / 5)
            .labelOffset(15)
            .cells(3)
            .labels([
                this.scale.rScale.domain()[0], 
                (this.scale.rScale.domain()[0] + this.scale.rScale.domain()[1]) / 2,
                this.scale.rScale.domain()[1]].map(s => utils.percent(s / store._.totalSize)))
            .title('Proportion')
            .orient('vertical')
        this.panel.selectAll('.legend').remove();
        if (this.panel.selectAll('.legend').empty()){
            this.panel.append('g')
                .attr('class', 'legend').attr('fill', 'lightgrey')
                .attr('transform', `translate( ${this.size.width + this.scale.rScale.range()[1]}, 0)`)
        }
        this.panel.select('.legend').call(legendSize);
        this.panel.selectAll('text').attr('fill', 'black');
    }

    public setCmd(d: ErrOverlap): void {
        const metric = store._.dataType === 'qa' ? 'f1' : 'accuracy';
        const not_a = d.perform_a === 'correct' ? '==' : '<';
        const not_b = d.perform_b === 'correct' ? '==' : '<';
        store._.setActiveCmd(
            `${metric}(model="${d.model_a}") ${not_a} 1 and ${metric}(model="${d.model_b}") ${not_b} 1`, 
            true, true);
    }

    /**
     * The main rendering for the matrix
     */
    private renderMat(): void {
        const self: ErrorOverlapPanel = this;
        const mat = this.panel.selectAll('.mat')
            .data(this.overlaps, 
                (d: ErrOverlap) => `mat-${d.perform_a}-${d.perform_b}`);
        const enter = mat.enter().append('circle').attr('class', 'mat');
        enter.merge(mat as any)
            .attr('cx', e => self.scale.xScale(e.perform_a) + self.scale.xScale.bandwidth() / 2)
            .attr('cy', e => self.scale.yScale(e.perform_b) + self.scale.yScale.bandwidth() / 2)
            .attr('r', e =>  e.count === 0 ? 0 : self.scale.rScale(e.count))
            .style('fill', 'steelblue')
            .style('cursor', 'pointer')
            .on('mouseover', function(d) { self.mouseovered(d, self, this); })
            .on('mouseout', function() { self.mouseouted(self); })
            .on('click', function(d) { self.setCmd(d); })
        mat.exit().remove();
        if (this.overlaps.length === 0) {
            this.panel.selectAll('.mat').remove();
            return;
        }
    }
    /**
     * mouse out -> delete the hover filtering
     */
    private mouseouted(self: ErrorOverlapPanel): void {
        self.hovertip.hide();
    }

    /**
     * mouse over -> 
     * @param e: <ErrorMat> the error mat cell hovered
     * @param element <d3.BaseType> the hovered element for style changing
     */
    
    private mouseovered(e: ErrOverlap, self: ErrorOverlapPanel, element: any): void {
        const a_correct = e.perform_a === 'correct' ? '' : '!';
        const b_correct = e.perform_b === 'correct' ? '' : '!';
        let displayText: string = `<div><b>Models: </b> (${a_correct}${e.model_a}, ${b_correct}${e.model_b})</div>`
        displayText += `<div><b>#Error: </b> ${e.count} (${utils.percent(e.count / store._.totalSize)})</div>`;
        self.hovertip.html(displayText);
        self.hovertip.show(element);
    }

    private brushstart (): void {
        //d3.event.sourceEvent.stopPropagation();
    }

    /**
     * Brushing in action
     */
    private brushing (target: string, brush: any): void {
        
    };
}