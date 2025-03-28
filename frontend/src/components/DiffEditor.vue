<template>
    <div>
      <div id="titles">
        <div class="title-container"><span class="title-text">Generated Data (Read-only)</span></div>
        <div class="title-container"><span class="title-text">Editable Data</span></div>
      </div>
      <div ref="editorContainer" id="editor-container"></div>
    </div>
    
  </template>
  
<script>
import {MergeView} from "@codemirror/merge"
import {EditorView, basicSetup} from "codemirror"
import {EditorState, StateField} from "@codemirror/state"
import {json} from "@codemirror/lang-json"

export default {
  name: 'DiffEditor',
  props: {
    code: {
      type: String,
      default: `{"hello": "world"}`
    },
  },
  data() {
    return {
      editor: null
    };
  },
  mounted() {
    // const docField = StateField.define({
    //   create(state) { return state.doc.toString() },
    //   update(value, tr) { return tr.docChanged ? tr.newDoc.toString() : value }
    // });
    this.editor = new MergeView({
      a: {
        doc: this.code,
        extensions: [
          basicSetup,
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
          json()
        ]
      },
      b: {
        doc: this.code,
        extensions: [
          basicSetup, 
          json()
        ]
      },
      parent: document.getElementById('editor-container')
    })
    // console.log(this.editor.right.state)
    // const rightEditor = document.querySelector('#editor-container .cm-content.cm-right')
    // const rightValue = rightEditor ? this.editor.right.state.doc.toString() : '';
    // console.log(rightValue)
  },
  beforeUnmount() {
  },
  methods: {
  }
}
</script>
  
<style scoped>
#editor-container {
  text-align: left;
}
#titles {
  display: flex;
  align-content: stretch;
}
.title-container {
  text-align: left;
  flex: 1 0 50%;
}
.title-text {
  padding: 5px;
  /* border-top: 1px solid #000;
  border-right: 1px solid #000;
  border-left: 1px solid #000; */
}
</style>