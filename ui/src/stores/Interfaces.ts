import { InstanceKey } from "./InstanceKey";

export type SampleMethod = 'best'|'worst'|'rand'|'borderline'|'changed'|'unchanged'|'correct_flip'|'incorrect_flip';
export type BuiltType = 'attr'|'group'|'rewrite';
export type SampleDirection = 'from'|'not from';
export type RewrtieTarget = 'question'|'context'|'groundtruth'|'prediction';

export interface HistoryMeta {
    cmd: string;
    instances: InstanceKey[];
}

export interface ErrOverlap {
    model_a: string;
    model_b: string;
    perform_a: 'correct'|'incorrect';
    perform_b: 'correct'|'incorrect';
    count: number;
}

export interface Suggestion {
    cmd: string;
    domain: string[];
    type: string;
}



export type RewrittenReturn = {
    qid: string, 
    ori_instance: {
        key: { [key: string]: number|string };
        question: string;
        context?: string;
        groundtruths: string[];
        prediction: string;
        perform: number;
    };
    rewrite_instance: {
        key: { [key: string]: number|string };
        question: string;
        context?: string;
        groundtruths: string[];
        prediction: string;
        perform: number;
    }
};

export interface PredictInputMeta {
    qid: string;
    qtext: string;
    ptext: string;
    rid: string;
}

export interface RewriteMeta {
    rid: string;
    config: string;
}

export interface Annotation {
    tidx: number; 
    annotate: string;
}

export interface Indicator {
    target: string; 
    key: string;
    annotations: Annotation[];
}

export interface QuestionHash {
    qid: string;
    vid: number;
}

export interface DeltaF1Meta {
    pair: QuestionHash[];
    delta_f1: number;
}

/**
 * Token datum
 */
export interface Token {
    idx: number; // the idx of the span in doc
    sid: number; // the sentence id containing the span.
    text: string; // text of one word
    ner: string; // named speech recognition
    pos: string; // part-of-speech tag in detail
    tag: string; // simplified the tag
    lemma: string; // lemma in lower case
    whitespace: number; // the space
    etype?: string; // add|remove|delete
    matches?: {token: Token, dist: number}[];
}

/**
 * The performance information
 */
export interface QAPerformance<T> {
    f1: T;
    em: T;
    precision: T;
    recall: T;
    confidence?: T;
}

/**
 * The performance information
 */
export interface VQAPerformance<T> {
    accuracy: T;
    confidence?: T;
}

// general class name generator
export interface ClassDatum {
    view: string; // view key
    element: string; // element key
    key: string; // 
    total: string;
}

export interface IEntry<T> {
    [key: string]: T;
}

export interface TokenPatternMeta {
    tag?: string;
    pos?: string;
    dep?: string;
    orth?:string;
    lemma?: string;
}


export interface PatternMeta {
    before: TokenPatternMeta[];
    after: TokenPatternMeta[];
}

export interface SubTemplateMeta {
    key: string;
    count: number;
    delta_f1s: number[];
    pattern: PatternMeta;
}