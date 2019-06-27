import * as React from 'react';
import AceEditor from 'react-ace';
import { observer } from 'mobx-react';
import * as d3 from 'd3';
import { CustomPythonMode } from './CustomHighlight';
import { store } from '../../stores/Store';

import 'brace/mode/python';
import 'brace/theme/textmate';
import 'brace/ext/language_tools';
import "brace/snippets/python";

export interface CoderProps {
    readOnly: boolean;
    cmd: string;
    changeCmd: (cmd: string) => void;
    multiLines: boolean;
}

@observer
export class QueryCoder extends React.Component<CoderProps, {}> {
    private aceEditor: any;
    private cmd: string;
    private customMode: CustomPythonMode;
    constructor(props: any, context: any) {
        super(props, context);
        this.aceEditor = null;
        this.cmd = this.formatCmd(this.props.cmd);
        this.onChange = this.onChange.bind(this);
        this.customMode = new CustomPythonMode();
    }

    onSelectionChange(selection) {
        const content = this.aceEditor.editor.session.getTextRange(selection.getRange());
        // use content
    }

    private normalizeCmd(cmd: string): string {
        cmd = cmd.replace(/[\n\t]+/g, ' ');
        cmd = cmd.replace(/[\'|\“|\”]/g, '"');
        cmd = cmd.replace(/[\']/g, '"');
        return cmd;
    }

    private formatCmd(cmd: string): string {
        cmd = this.normalizeCmd(cmd);
        if (this.props.multiLines) {
            cmd = cmd.replace(/\s+and\s+/g, ' and \n\t');
            cmd = cmd.replace(/\s+or\s+/g, ' or \n\t');
        }
        return cmd;
    }

    public onChange(string: string) {
        //const content = this.aceEditor.editor.session.getTextRange(selection.getRange());

        /*
        console.log(string);
        console.log(this.aceEditor.editor);
        this.aceEditor.editor.focus();
        const cursor = this.aceEditor.editor.selection.getCursor(); 
        */
        this.cmd = string;
        if (this.props.changeCmd) {
            this.props.changeCmd(this.normalizeCmd(string));
        }
    }
    public componentDidMount(){
        const self = this;
        this.aceEditor = this.refs.aceEditor as any;
        this.aceEditor.editor.getSession().setMode(this.customMode);

        // editor.find(searchRegex, 
        //    {backwards: false, wrap: true, caseSensitive: false, wholeWord: false,regExp: true});

        this.customMode.setNewCompletion(store._.attrHashes, 'attr');
        this.customMode.setNewCompletion(store._.dataGroupHashs, 'group');
        this.aceEditor.editor.completers = [{
            getCompletions: function(editor, session, pos, prefix, callback) {
                callback(null, d3.merge(Object.values(self.customMode.completions)));
            }
        }];
    }

    public render(): JSX.Element {
        
        const self = this;
        this.customMode.setNewCompletion(store._.attrHashes, 'attr');
        this.customMode.setNewCompletion(store._.dataGroupHashs, 'group');
        if (this.aceEditor) {
            this.aceEditor.editor.getSession().setMode(this.customMode);
            this.aceEditor.editor.completers = [{
                getCompletions: function(editor, session, pos, prefix, callback) {
                    callback(null, d3.merge(Object.values(self.customMode.completions)));
                }
            }];
        }
            
        return  <AceEditor className={'full-width'}
                maxLines={ this.props.multiLines ? 3 : 2 } 
                ref="aceEditor"
                minLines={ 1 }
                value={ this.cmd }
                readOnly={this.props.readOnly}
                highlightActiveLine={true}
                showGutter={false}
                //onSelection={(s) => {console.log(s)}}
                //onCursorChange={(selection) => { console.log(selection)}}
                fontSize={this.props.multiLines || !this.props.readOnly ? 14 : 12}
                theme="textmate"
                mode='python'
                onChange={ (s) => { this.onChange(s) }}
                name="UNIQUE_ID_OF_DIV"
                editorProps={{$blockScrolling: true}}
                setOptions={{
                    enableBasicAutocompletion: false,
                    enableLiveAutocompletion: true,
                    enableSnippets: true,
                    showLineNumbers: false,
                    tabSize: 4,
                }}
            />
    }
}