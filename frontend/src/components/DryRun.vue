<template>
    <div id="dry-run-container" v-if="visible">
        <div>Migration Overview<button id="hide-button" @click="hide()">X</button></div>
        <div v-if="!dryRun">
          <div class="warn">{{ commitInstructions }}</div>
          <button @click="confirmMigration" :disabled="isConfirming">
            {{ isConfirming ? 'Processing...' : 'Confirm' }}
          </button>
        </div>
        <div class="sub" v-if="dryRun">{{ dryRunInstructions }}</div>
        <div v-if="jsonError">
          <span>The modified payload is not valid JSON. Please update the payload.</span>
          <span>{{ jsonError }}</span>
        </div>
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
        dryRun: true,
        dryRunInstructions: `The following data is slated to migrate. 
              The left editor is what was generated from Congregate. 
              On the right, you can modify the payload before starting the migration to tweak as you see fit.`,
        commitInstructions: `You are about to commit this migration run. 
              Please review the payload on the right and click confirm to proceed.`,
        jsonError: "",
        isConfirming: false // Flag to prevent multiple submissions
    }
  },
  mounted: function() {
    this.emitter.on('show-dry-run', (data) => {
        this.visible = true
        this.left = JSON.stringify(data.left, null, 2)
        if (data.right) {
            this.right = JSON.stringify(data.right, null, 2)
        }
        this.dryRun = data.dryRun
        // Reset the confirmation flag when showing the dialog
        this.isConfirming = false
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
      try {
        JSON.parse(this.$refs['diff-editor'].editor.b.state.doc.toString())
        this.visible = false
        this.saveModifiedPayload()
        this.jsonError = ""
      } catch (e) {
        this.emitter.emit('alert', {
          'message': 'The modified payload is not valid JSON. Please update the payload.',
          'messageType': 'error'
        })
        this.jsonError = e.message
      }
    },
    saveModifiedPayload: function() {
      this.emitter.emit('save-modified-payload', JSON.parse(this.$refs['diff-editor'].editor.b.state.doc.toString()))
    },
    confirmMigration: function() {
      // Prevent multiple submissions
      if (this.isConfirming) {
        return
      }
      
      // Set the flag immediately to block subsequent calls
      this.isConfirming = true
      
      try {
        // Validate JSON before proceeding
        const payload = JSON.parse(this.$refs['diff-editor'].editor.b.state.doc.toString())
        
        // Save the modified payload
        this.emitter.emit('save-modified-payload', payload)

        // Emit the confirmation event
        this.emitter.emit('confirm-migration')
        
        // Use nextTick to ensure DOM updates are processed
        this.$nextTick(() => {
          
          // Hide the dialog
          this.visible = false
          
          // Reset the flag after a short delay to allow for re-opening the dialog
          setTimeout(() => {
            this.isConfirming = false
          }, 500)
        })
      } catch (e) {
        // Handle JSON parsing error
        this.emitter.emit('alert', {
          'message': 'The modified payload is not valid JSON. Please update the payload.',
          'messageType': 'error'
        })
        this.jsonError = e.message
        
        // Reset the flag on error
        this.isConfirming = false
      }
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

.warn {
  margin: 1em;
  text-align: center;
  font-weight: bold;
  font-size: smaller;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #ccc;
}
</style>