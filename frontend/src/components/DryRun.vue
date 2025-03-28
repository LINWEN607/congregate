<template>
    <div id="dry-run-container" v-if="visible">
        <div>Migration Overview<button id="hide-button" @click="hide()">X</button></div>
        <div class="sub">{{ dryRunInstructions }}</div>
        <hr>
      
        <DiffEditor
          ref="diff-editor"
          :left="left"
          :right="right"
        />
        <!-- Will need to refactor this for non-DT related migrations-->
        <!-- <div v-for="data in dryRunData">
            <div class="entity-card">
                <div>Destination Namespace: {{ data.entity.destination_namespace }}</div>
                <div>Destination Slug: {{ data.entity.destination_slug }}</div>
                <div>Source Full Path: {{ data.entity.source_full_path }}</div>
                <div>Source Type: {{ data.entity.source_type }}</div>
                <div v-if="data.entity.source_type == 'group_entity'">Migrating Projects: {{ data.entity.migrate_projects }}</div>
                <ul v-if="data.projects.length > 0 && data.entity.migrate_projects == true">Projects
                    <li v-for="project in data.projects">{{ project }}</li>
                </ul>
                <ul v-if="data.subgroups.length > 0">Subgroups
                    <li v-for="subgroup in data.subgroups">{{ subgroup }}</li>
                </ul>
            </div>
        </div> -->
    </div>
</template>
<script>
import DiffEditor from '@/components/DiffEditor.vue';
export default {
  name: 'DryRun',
  components: {
    DiffEditor
  },
  data() {
    return {
        visible: false,
        dryRunData: [],
        selectedLanguage: 'json',
        selectedTheme: 'vs-dark',
        output: '',
        left: null,
        right: null,
        dryRunInstructions: `The following data is slated to migrate. 
              The left editor is what was generated from Congregate. 
              On the right, you can modify the payload before starting the migration to tweak as you see fit.`
    }
  },
  mounted: function() {
    this.emitter.on('show-dry-run', (data) => {
        this.visible = true
        this.left = JSON.stringify(data.left, null, 2)
        if (data.right) {
            this.right = JSON.stringify(data.right, null, 2)
        }
    })
  },
  beforeUnmount: function() {
    this.emitter.off('show-dry-run')
    if (this.$refs['diff-editor']) {
      this.saveModifiedPayload()
    }
  },
  methods: {
    hide: function() {
      this.visible = false
      this.saveModifiedPayload()
    },
    saveModifiedPayload: function() {
      this.emitter.emit('save-modified-payload', JSON.parse(this.$refs['diff-editor'].editor.b.state.doc.toString()))
    }
  }
}
</script>
<style scoped>
#dry-run-container {
    border: 1px solid #000;
    /* background: rgba(255, 255, 255, 75%); */
    background: #fff;
    position: absolute;
    top: 10%;
    left: 15%;
    width: 75%;
    height: 85%;
    box-shadow: 0px 0px 10px #666;
    overflow-y: scroll;
}

.entity-card {
    border: 1px solid #000;
    text-align: left;
    margin: 2%;
    padding: 1%;
}

#hide-button {
    position: absolute;
    top: 0;
    right: 0;
    border-left: 1px solid #000;
    border-bottom: 1px solid #000;
    border-right: none;
    border-top: none;
    padding: 5px 10px;
    cursor: pointer;
}

#hide-button:hover {
    background: #ff851b;
}

.sub {
  margin: 1em;
  text-align: left;
  font-size: smaller;
  font-style: italic;
}
</style>