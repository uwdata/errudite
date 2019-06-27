import * as d3 from 'd3';
/**
 * wtshuang@cs.uw.edu
 * 2018/02/28
 * The class for attributes.
 */

export type AttrValue = number|string;
export type AttrItem = [AttrValue, number];
export type AttrDataType = "continuous" | "categorical";
export class Attribute {
    public name: string;
    public description: string;
    public cmd: string;
    public domain: (number|string)[];
    public dtype: AttrDataType; // data type. Currently discrete
    public counts: { correct: AttrItem[]; incorrect: AttrItem[]; };
    public flatCounts: { correct: AttrValue[], incorrect: AttrValue[] };

    constructor (
        name: string, 
        description: string, 
        dtype: AttrDataType, // data type. Currently discrete
        cmd: string,
        domain: (number|string)[],
        counts: { correct: AttrItem[]; incorrect: AttrItem[]; }
    ) {
        this.name = name;
        this.description = description;
        this.dtype = dtype;
        this.cmd = cmd;
        this.domain = domain;
        this.counts = counts;
        if (this.dtype === "continuous") {
            this.flatCounts = this.flattenCount(this.counts);
        } else {
            this.flatCounts = { incorrect: [], correct: [] };
        }
    }
    public getCount(ctype: "total"|"correct"|"incorrect"="total"): number {
        if (ctype === 'correct') {
            return d3.sum(this.counts.correct.map(c => c[1]));
        } else if (ctype === 'incorrect') {
            return d3.sum(this.counts.incorrect.map(c => c[1]));
        } 
        return d3.sum(this.counts.correct.map(c => c[1])) +
            d3.sum(this.counts.incorrect.map(c => c[1]));
    }

    private flattenCount(count: {correct: AttrItem[], incorrect: AttrItem[]})
        : {incorrect: AttrValue[], correct: AttrValue[]} {
        const flatCount = { incorrect: [], correct: [] };
        for (let ctype of Object.keys(count)) {
            for (let item of count[ctype]) {
                for (let i = 0; i < item[1]; i++) {
                    flatCount[ctype].push(parseFloat(item[0]));
                }
            }
        }
        return flatCount
    }

    public key(): string {
        return `name:${this.name}-cmd:${this.cmd}-count:${this.getCount()}`;
    }
}
