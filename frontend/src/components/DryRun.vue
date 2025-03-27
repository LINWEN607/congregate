<template>
    <div id="dry-run-container" v-if="visible">
        Migration Dry Run is complete. The following data is slated to migrate: <button id="hide-button" @click="hide()">X</button>
        <div v-for="data in dryRunData">
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
        </div>
    </div>
</template>
<script>
export default {
  name: 'DryRun',
  components: {
  },
  data() {
    return {
        visible: false,
        dryRunData: [],
        code: 'hello world',
        selectedLanguage: 'json',
        selectedTheme: 'vs-dark',
        output: ''
    }
  },
  mounted: function() {
    this.emitter.on('show-dry-run', (data) => {
        console.log(data)
        this.visible = true
        // this.dryRunData = data['result']
        this.code = data['dry_run_data']
    })
  },
  beforeDestroy: function() {
    this.emitter.off('show-dry-run')
  },
  methods: {
    hide: function() {
        this.visible = false
    },
    handleCodeChange(newCode) {
        this.code = newCode;
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
    left: 25%;
    width: 50%;
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
</style>