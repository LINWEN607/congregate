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
import {EditorState} from "@codemirror/state"
import {json} from "@codemirror/lang-json"

export default {
  name: 'DiffEditor',
  props: {
    left: {
      type: String,
      default: ''
    },
    right: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      editor: null
    };
  },
  mounted() {
    this.editor = new MergeView({
      a: {
        doc: this.left,
        extensions: [
          basicSetup,
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
          json()
        ]
      },
      b: {
        doc: this.right !== null ? this.right : this.left,
        extensions: [
          basicSetup, 
          json()
        ]
      },
      parent: document.getElementById('editor-container')
    })
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
}
</style>