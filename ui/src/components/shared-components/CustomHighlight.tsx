import 'brace/mode/python';
import * as ace from 'brace';
import { store } from '../../stores/Store';
import * as d3 from 'd3';
import { BuiltType } from '../../stores/Interfaces';
import { POSs, TAGs, ENTs } from './RewriteTemplateName';
/*
var builtinFunctions = (
  "abs|divmod|input|open|staticmethod|all|enumerate|int|ord|str|any|" +
  "eval|isinstance|pow|sum|basestring|execfile|issubclass|print|super|" +
  "binfile|iter|property|tuple|bool|filter|len|range|type|bytearray|" +
  "float|list|raw_input|unichr|callable|format|locals|reduce|unicode|" +
  "chr|frozenset|long|reload|vars|classmethod|getattr|map|repr|xrange|" +
  "cmp|globals|max|reversed|zip|compile|hasattr|memoryview|round|" +
  "__import__|complex|hash|min|set|apply|delattr|help|next|setattr|" +
  "buffer|dict|hex|object|slice|coerce|dir|id|oct|sorted|intern"
)
*/


/**
primitive_funcs =  {
            'token': token,
            # linguistics
            'linguistic': linguistic,
            'has_any': has_any,
            'has_all': has_all,
            'count': count,
            'LEMMA': LEMMA,
            'POS': POS,
            'TAG': TAG,
            'DEP': DEP,
            'ENT_TYPE': ENT_TYPE,
            'ENT': ENT_TYPE,
            'TEXT': TEXT,
            'length': length,
            'freq': freq,
            'question_type': question_type,
            'answer_type': answer_type,
            'confidence': functools.partial(confidence, predictions=instance.get_entry('predictions'))
        }
        if instance_type == 'qa':
            primitive_funcs_ = {
                'sentence': functools.partial(sentence, 
                    context=instance.get_entry('context')),
                'offset': functools.partial(offset, 
                    tos=instance.get_entry('prediction'),
                    context=instance.get_entry('context'),
                    froms=instance.get_entry('groundtruth')),
                'overlap': overlap,
                'dep_distance': functools.partial(dep_distance, 
                    question=instance.get_entry('question'),
                    context=instance.get_entry('context')),
                'f1': functools.partial(F1, predictions=instance.get_entry('predictions')),
                'precision': functools.partial(precision, predictions=instance.get_entry('predictions')),
                'recall': functools.partial(recall, predictions=instance.get_entry('predictions')),
                'exact_match': functools.partial(exact_match, predictions=instance.get_entry('predictions')),
                'correct_sent': functools.partial(correct_sent, predictions=instance.get_entry('predictions')),
            }
        else:
            primitive_funcs_ = {
                'accuracy': functools.partial(F1, predictions=instance.get_entry('predictions'))
            }
 */


var decimalInteger = "(?:(?:[1-9]\\d*)|(?:0))";
var octInteger = "(?:0[oO]?[0-7]+)";
var hexInteger = "(?:0[xX][\\dA-Fa-f]+)";
var binInteger = "(?:0[bB][01]+)";
var integer = "(?:" + decimalInteger + "|" + octInteger + "|" + hexInteger + "|" + binInteger + ")";

var strPre = "(?:r|u|ur|R|U|UR|Ur|uR)?";
var exponent = "(?:[eE][+-]?\\d+)";
var fraction = "(?:\\.\\d+)";
var intPart = "(?:\\d+)";
var pointFloat = "(?:(?:" + intPart + "?" + fraction + ")|(?:" + intPart + "\\.))";
var exponentFloat = "(?:(?:" + pointFloat + "|" +  intPart + ")" + exponent + ")";
var floatNumber = "(?:" + exponentFloat + "|" + pointFloat + ")";
var stringEscape =  "\\\\(x[0-9A-Fa-f]{2}|[0-7]{3}|[\\\\abfnrtv'\"]|U[0-9A-Fa-f]{8}|u[0-9A-Fa-f]{4})";

const LINGUISTICS = "LEMMA|POS|TAG|POS|ENT_TYPE|ENT|ORTH"
const DEFINED_LOGICS = "has_any|has_all|count"
export const FUNCTIONS_SHARE = [
    LINGUISTICS, DEFINED_LOGICS, 
    "overlap|STRING|abs_num|prediction|length|freq|question_type|answer_type|starts_with|ends_with|is_rewritten_by|apply"].join("|");
export const FUNC_PERFORM_QA = "f1|precision|recall|exact_match|is_correct_sent|confidence";
export const FUNC_PERFORM_VQA = "accuracy|confidence";

export const FUNCTIONS_QA = [FUNC_PERFORM_QA, "sentence|answer_offset_delta|answer_offset_span|dep_distance"].join("|");
export const FUNCTIONS_VQA = [FUNC_PERFORM_VQA, "is_digit|digitize|trim"].join("|");

export const TARGETS_SHARE = "instance|question|predictions|groundtruths|groundtruth";
export const TARGETS_QA = "context";

export const LOGICS = "not|and|or|in";
export const OPERATORS = "\\+|\\-|\\*|\\/|\\/\\/|%|&|\\||\\^|~|<|>|<=|=>|==|!=|=";
export const CONSTANTS =  `True|False|None`;

const LINGUISTICS_FUNCS = LINGUISTICS.split('|').map(l => {
    return {
        value: l, caption: l, type: "snippet", meta: "attr-func", score: 1000,
        snippet: l + " (${1:target}, ${2:get_root=False}, ${3:pattern=None})"
    }
});

const DEFINED_LOGICS_FUNCS = DEFINED_LOGICS.split('|').map(l => {
    return {
        value: l, caption: l, type: "snippet", meta: "attr-func", score: 1000,
        snippet: l + " (${1:container}, ${2:contained})"
    }
});
const QA_PERFORMANCES = FUNC_PERFORM_QA.split('|').map(l => {
    return {
        value: l, caption: l, type: "snippet", meta: "attr-func", score: 1000,
        snippet: l + ' (${1:model="ANCHOR"})'
    }
});
const VQA_PERFORMANCES = FUNC_PERFORM_VQA.split('|').map(l => {
    return {
        value: l, caption: l, type: "snippet", meta: "attr-func", score: 1000,
        snippet: l + ' (${1:model="ANCHOR"})'
    }
});

const SHARED_FUNCS = [
    {
        value: "apply",
        caption: "apply",
        type: "snippet", 
        meta: "filter-func", 
        score: 1000,
        snippet: 'apply (${1:func}, ${2:rewrite="SELECTED"})'
    },
    {
        value: "is_rewritten_by",
        caption: "is_rewritten_by",
        type: "snippet", 
        meta: "filter-func", 
        score: 1000,
        snippet: 'is_rewritten_by (${1:rewrite="SELECTED"})'
    },
    {
        value: "STRING",
        caption: "STRING",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'STRING (${1:target})'
    },{
        value: "overlap",
        caption: "overlap",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'overlap (${1:target1}, ${2:target2}, ${3:label="lemma"})'
    }, {
        value: "abs_num",
        caption: "abs_num",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'abs_num (${1:target})'
    }, {
        value: "prediction",
        caption: "prediction",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'prediction (${1:model="ANCHOR"})'
    }, {
        value: "token",
        caption: "token",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "token (${1:target}, ${2:idxes=None}, ${3:pattern=None})"
    }, {
        value: "starts_with",
        caption: "starts_with",
        type: "snippet", 
        meta: "filter-func", 
        score: 1000,
        snippet: "starts_with (${1:target}, ${3:pattern=None})"
    }, {
        value: "ends_with",
        caption: "ends_with",
        type: "snippet", 
        meta: "filter-func", 
        score: 1000,
        snippet: "ends_with (${1:target}, ${3:pattern=None})"
    }, {
        value: "has_pattern",
        caption: "has_pattern",
        type: "snippet", 
        meta: "filter-func", 
        score: 1000,
        snippet: "has_pattern (${1:target}, ${2:idxes=None}, ${3:pattern=None})"
    }, {
        value: "question_type",
        caption: "question_type",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "question_type (question)"
    }, {
        value: "answer_type",
        caption: "answer_type",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "answer_type (${1:target})"
    }, {
        value: "length",
        caption: "length",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "length (${1:target})"
    }, {
        value: "freq",
        caption: "freq",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'freq (${1:target}, ${2:target_type="question"})'
    }, {
        value: "truncate",
        caption: "truncate",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "truncate (${1:value}, ${2:min_value=-1}, ${3:max_value=50})"
    }
];

const QA_FUNCS = [
    {
        value: "sentence",
        caption: "sentence",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "sentence (${1:target}, ${2:shift=0})"
    }, {
        value: "answer_offset_span",
        caption: "answer_offset_span",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'answer_offset_span (${1:prediction=prediction(model="ANCHOR")}, ${2:direction="left"})'
    }, {
        value: "answer_offset_delta",
        caption: "answer_offset_delta",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'answer_offset_delta (${1:prediction=prediction(model="ANCHOR")}, ${2:direction="left"})'
    }, {
        value: "dep_distance",
        caption: "dep_distance",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: 'dep_distance (${1:target}, ${2:pattern=None})'
    }, 
]

const VQA_FUNCS = [
    {
        value: "digitize",
        caption: "digitize",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "digitize (${1:target})"
    }, {
        value: "is_digit",
        caption: "is_digit",
        type: "snippet", 
        meta: "attr-func", 
        score: 1000,
        snippet: "is_digit (${1:target})"
    }
]

export class CustomHighlightRules extends ace.acequire(
    "ace/mode/text_highlight_rules").TextHighlightRules {
    constructor() {
        super();
    
        this.$rules = {
            "start" : [
                {token : "comment", regex: "#.*$" },
                    { token : "support.function", regex: store._.dataType === 'qa' ? 
                        [FUNCTIONS_SHARE, FUNCTIONS_QA].join("|") :
                        [FUNCTIONS_SHARE, FUNCTIONS_VQA].join("|") },
                    { token : "keyword", regex: store._.dataType === 'qa' ? 
                        [TARGETS_SHARE, TARGETS_QA].join("|") : TARGETS_SHARE },
                    { token : "keyword", regex: CONSTANTS },
                    { token : "keyword", regex: [ POSs, TAGs, ENTs].join("|") },
                    { token : "constant.operator", regex : OPERATORS },
                    { token : "constant.language", regex : LOGICS },
                                
                    { token : "constant.numeric", regex : "(?:" + floatNumber + "|\\d+)[jJ]\\b" },// imaginary
                    { token : "constant.numeric", regex : floatNumber },// float
                    { token : "constant.numeric", regex : integer + "[lL]\\b" },// long integer
                    { token : "constant.numeric", regex : integer + "\\b" },
                    
                    { token : "paren.lparen", regex : "[\\[\\(\\{]" },
                    { token : "paren.rparen", regex : "[\\]\\)\\}]" }, 
                    
                { token : "string", regex : strPre + '"(?=.)', next : "qqstring" }, // " string
                { token : "string", regex : strPre + "'(?=.)", next : "qstring" } // ' string
            ],
            
            "qqstring" : [
                { token : "constant.language.escape", regex : stringEscape }, 
                { token : "string", regex : "\\\\$", next  : "qqstring" }, 
                { token : "string", regex : '"|$', next  : "start" }, 
                { defaultToken: "string" }
            ],
            "qstring" : [
                { token : "constant.language.escape", regex : stringEscape }, 
                { token : "string", regex : "\\\\$", next  : "qstring" }, 
                { token : "string", regex : "'|$", next  : "start" }, 
                { defaultToken: "string" }
            ]
        };
        //console.log(this.$rules);
    }
}

export class CustomPythonMode extends ace.acequire("ace/mode/python").Mode {

    public completions: {
        logics: any[];
        ops: any[];
        consts: any[];
        targets: any[];
        funcs: any[];
        kwargs: any[];
    };
    
    constructor() {
        super();
        this.HighlightRules = CustomHighlightRules;
        const CONSTS = 
        this.completions = {
            logics: LOGICS.split('|').map(t => { return { value: t, meta: 'logic' , score: 800}; }),
            ops: OPERATORS.split('|').map(t => { return { value: t, meta: 'operator', score: 800 }; }),
            consts: CONSTANTS
                .split('|').map(t => { return { value: t, meta: 'keyword' , score: 700 }; }),
            kwargs: [{ value: "rewrite", meta: 'keyword' , score: 700 }],
            targets: store._.dataType === 'qa' ? 
                [TARGETS_SHARE, TARGETS_QA].join("|").split('|').map(t => {
                    return { value: t, caption: t, meta: 'target', score: 900 }}) : 
                TARGETS_SHARE.split('|').map(t => {
                    return { value: t, caption: t, meta: 'target', score: 900 }}),
            funcs: store._.dataType === 'qa' ? 
                d3.merge([SHARED_FUNCS, QA_FUNCS, LINGUISTICS_FUNCS, DEFINED_LOGICS_FUNCS, QA_PERFORMANCES]) : 
                d3.merge([SHARED_FUNCS, LINGUISTICS_FUNCS, DEFINED_LOGICS_FUNCS, VQA_PERFORMANCES])
        }
    }
    
    public setNewCompletion(dataArr: string[], type: BuiltType): void {
        this.completions.funcs = store._.dataType === 'qa' ? 
            d3.merge([SHARED_FUNCS, QA_FUNCS, LINGUISTICS_FUNCS, DEFINED_LOGICS_FUNCS, QA_PERFORMANCES]) : 
            d3.merge([SHARED_FUNCS, VQA_FUNCS, LINGUISTICS_FUNCS, DEFINED_LOGICS_FUNCS, VQA_PERFORMANCES]);
        this.completions[type] = dataArr.map(d => {
            return { value: `${type}:${d}`, meta: 'attr' , score: 900 };
        });
    }

    
}