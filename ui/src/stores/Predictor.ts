/**
 * wtshuang@cs.uw.edu
 * 2018/02/28
 * The class for predictors
 */

import { QAPerformance, VQAPerformance } from './Interfaces';

export class Predictor {
    public name: string;
    public description: string;
    public perform: QAPerformance<number>|VQAPerformance<number>;

    constructor (
        name: string, 
        description: string, 
        perform: QAPerformance<number>|VQAPerformance<number>) {
        this.name = name;
        this.description = description;
        this.perform = perform;
    }
}
