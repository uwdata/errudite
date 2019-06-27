/**
 * wtshuang@cs.uw.edu
 * 2018/01/12
 * The class for the answers
 */

import { Token, QAPerformance, VQAPerformance } from './Interfaces';
export class AnswerKey {
    public model: string; // which model generated this answer
    public qid: string; // question id    
    public vid: number; // version id

    constructor(qid: string, vid: number, model: string) {
        this.qid = qid;
        this.vid = vid;
        this.model = model;
    }
    

    public key() {
        return `qid:${this.qid}-vid:${this.vid}-model:${this.model}`;
    }

}

export class Answer {
    public key: string;
    public model: string; // which model generated this answer
    public qid: string; // question id    
    public vid: number; // version id
    public isGroundtruth: boolean; // is the ground truth by default
    
    public doc: Token[]; // editing type
    public answerType: string; // TODO could remove the attention.

    constructor (key: string, model: string, qid: string, vid: number,
                 isGroundtruth: boolean, doc: Token[], answerType: string) {
        this.key = key;
        this.model = model;
        this.qid = qid;
        this.vid = vid;
        this.isGroundtruth = isGroundtruth;
        this.doc = doc;
        this.answerType = answerType;
    }

    public getPerform(metric: string) {
        return 0;
    }


    /**
     * Make the instances into raw text
     * @return {string} plain text of the instance.
     */
    public textize(): string {
        let text: string = '';
        this.doc.forEach((d: Token) => { text += d.text + d.whitespace; });
        return text;
    }
}


export class QAAnswer extends Answer {
    public span_start: number; // the span idx of the first token in answer.
    public span_end: number; // the span idx of the last token in answer.
    public perform: QAPerformance<number>;
    public sid: number; // the sentence id

    constructor (key: string, model: string, qid: string, vid: number, sid: number,
        isGroundtruth: boolean, span_start: number, span_end: number,
        doc: Token[], answerType: string, perform: QAPerformance<number>) {
        super(key, model, qid, vid, isGroundtruth, doc, answerType)
        this.sid = sid;
        this.span_start = span_start;
        this.span_end = span_end;
        this.isGroundtruth = isGroundtruth;
        this.perform = perform;
    }

    public getPerform(metric: string='f1') {
        return this.perform[metric] ? this.perform[metric] : 0;
    }
}


export class VQAAnswer extends Answer {
    public count: number; // the span idx of the last token in answer.
    public perform: VQAPerformance<number>;

    constructor (key: string, model: string, qid: string, vid: number,
        isGroundtruth: boolean, doc: Token[], answerType: string, 
        count: number, perform: VQAPerformance<number>) {
        super(key, model, qid, vid, isGroundtruth, doc, answerType)
        this.count = count;
        this.perform = perform;
    }

    public getPerform(metric: string='accuracy') {
        return this.perform[metric] ? this.perform[metric] : 0;
    }

}