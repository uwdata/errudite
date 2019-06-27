/**
 * wtshuang@cs.uw.edu
 * 2018/05/28
 * This is the data slicing rule class
 */

export interface DataGroupCounts {
    correct: number; incorrect: number;
}

export interface DataGroupStats {
    coverage: number; 
    error_coverage: number;
    local_error_rate: number;
    global_error_rate: number;
}

export class DataGroup {
    public name: string; // the name of the data group; e.g. semantic_category
    public description: string; // the description on a data group.
    public cmd: string;
    public counts: DataGroupCounts;
    public stats: DataGroupStats;
    constructor ( 
        name: string, 
        description: string,
        cmd: string, 
        counts: DataGroupCounts, stats: DataGroupStats) {
        this.name = name;
        this.description = description;
        this.cmd = cmd;
        this.counts = counts;
        this.stats = stats;
    }

    public getCount(): number {
        return this.counts.correct + this.counts.incorrect;
    }

    public key(): string {
        return `name:${this.name}-cmd:${this.cmd}-count:${this.getCount()}`;
    }
}