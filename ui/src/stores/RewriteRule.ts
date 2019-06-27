import { RewrtieTarget } from './Interfaces';

export interface RewriteStatCount {
    flip_to_correct: number;
    flip_to_incorrect: number;
    unflip: number;
}
export class RewriteRule {
    
    public rid: string;
    public description: string;
    public category: string;
    public target: RewrtieTarget;
    public targetCmd: string;
    public counts: RewriteStatCount;
    public examples: string[][];

    /**
     * @param {string} rid <string> rule id / rule name
     * @param {string} category <string> category; auto, manual, semantic
     * @param {IEntry<number[]>} delta_f1s the performance differences
     * @param {IEntry<number>} unstable_scores unstable score for each model
     */
    constructor (rid: string, description: string, category: string, target: RewrtieTarget,
        targetCmd: string, counts: RewriteStatCount, examples: string[][]) {
        this.rid = rid;
        this.description = description;
        this.target = target;
        this.category = category;
        this.targetCmd = targetCmd;
        this.counts = counts;
        this.examples = examples;
    }
    public hash(): string {
        return this.rid;
    }

    public getCount(): number {
        return this.counts.flip_to_correct + 
            this.counts.flip_to_incorrect + 
            this.counts.unflip;
    }
}
