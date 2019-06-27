export class InstanceKey {
    public qid: string;
    public vid: number;
    public rid: string;
    constructor(qid: string, vid: number, rid: string) {
        this.qid = qid;
        this.vid = vid;
        this.rid = rid;
    }

    public key() {
        return `qid:${this.qid}-vid:${this.vid}`;
    }
}

export class QAInstanceKey extends InstanceKey {
    public aid: number;
    public cid: number;
    constructor(qid: string, vid: number, rid: string, cid: number, aid: number) {
        super(qid, vid, rid);
        this.cid = cid;
        this.aid = aid;
    }

    public key() {
        return `qid:${this.qid}-vid:${this.vid}`;
    }
}