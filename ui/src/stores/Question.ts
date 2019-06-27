/**
 * wtshuang@cs.uw.edu
 * 2018/01/12
 * The class for the questions
 */
import { Token } from './Interfaces';

export class Question {
    public key: string;
    public qid: string; // question id
    public vid: number; // version id
    public doc: Token[]; // rewriting type
    public questionType

    constructor (key: string, qid: string, vid: number, doc: Token[], questionType: string) {
        this.key = key;
        this.qid = qid;
        this.vid = vid;
        this.doc = doc;
        this.questionType = questionType;
    }

    /**
     * Make the instances into raw text
     * @return plain text of the instance.
     */
    public textize(): string {
        let text: string = '';
        this.doc.forEach((d: Token) => { text += d.text + d.whitespace; });
        return text;
    }
}


export class VQAQuestion extends Question{
    public imgId: string;

    constructor (key: string, qid: string, vid: number, doc: Token[], questionType: string, imgId: string) {
        super(key, qid, vid, doc, questionType);
        this.imgId = imgId;
    }

    /**
     * Make the instances into raw text
     * @return plain text of the instance.
     */
    public textize(): string {
        let text: string = '';
        this.doc.forEach((d: Token) => { text += d.text + d.whitespace; });
        return text;
    }
}
