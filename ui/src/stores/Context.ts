/**
 * wtshuang@cs.uw.edu
 * 2018/01/12
 * The class for the paragraphs
 */

import { Token } from './Interfaces';

export class Context {
    public key: string;
    public aid: number; // article id
    public cid: number; // paragraph id
    public qid: string; // question id    
    public vid: number; // version id
    public doc: Token[]; // editing type

    constructor (key: string, aid: number, cid: number, qid: string, vid: number, doc: Token[]) {
        this.key = key;
        this.aid = aid;
        this.cid = cid;
        this.qid = qid;
        this.vid = vid;
        this.doc = doc;
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
