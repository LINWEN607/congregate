<template>
    <div ref="editorContainer" id="editor-container"></div>
  </template>
  
<script>
import {MergeView} from "@codemirror/merge"
import {EditorView, basicSetup} from "codemirror"
import {EditorState} from "@codemirror/state"
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
        extensions: [basicSetup, json()]
      },
      parent: document.getElementById('editor-container')
    })
  },
  beforeUnmount() {
  },
  methods: {
  }
}
</script>
  
<style scoped>
</style>