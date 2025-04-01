<template>
    <ActionCard title="Migrate Data">
        <div class="not-implemented" v-if="!directTransfer">
          File-based migrations via the UI are currently not supported.
          <br>
          Please use the Congregate CLI or switch to using Direct transfer
          to migrate via the UI.
        </div>
        <div v-if="directTransfer && !migrationInProgress">
          Migrate staged data to destination GitLab instance
          <br>
          <button @click="promptConfirmation">Migrate</button>
          <ParamForm formId="migrate-params" :params="params"/>
        </div>
        <div class="in-progress" v-else>
          <span class="loader"></span>
          <span><b v-if="dryRun == true">DRY RUN </b>Migration in progress</span>
          <StatusTable :headers="statusColumns" :data="statusData"/>
        </div>
        <br>
        <br>
        <div v-if="directTransferGeneratedRequest">
          <sub>
            A dry run was recently cached. Please review before you commit the migration.
            <br>
            <button @click="showDryRun">View/Edit Migration Payload</button>
          </sub>
          <br>
        </div>
        
        <i>
          <sub>
            Congregate is currently configured to migrate from 
            {{ this.sourceType }} (<a :href="this.sourceUrl">{{ this.sourceUrl }}</a>) 
            to GitLab (<a :href="this.destinationUrl">{{ this.destinationUrl }}</a>)
          </sub>
        </i>
    </ActionCard>
</template>

<script>
import { toRaw } from 'vue'
import axios from 'axios'
import { mapStores } from 'pinia'
import { poll } from '@/scripts/poll.js'
import { useSystemStore } from '@/stores/system'
import ActionCard from '@/components/ActionCard.vue'
import ParamForm from '@/components/ParamForm.vue'
import StatusTable from '@/components/StatusTable.vue'

export default {
  name: 'MigrateCard',
  components: {
    ActionCard,
    ParamForm,
    StatusTable
  },
  computed: {
    ...mapStores(useSystemStore),
    sourceType() {
      if (!this.isSettingsStoreEmpty) {
        return this.systemStore.settings.SOURCE.src_type
      }
    },
    sourceUrl() {
      if (!this.isSettingsStoreEmpty) {
        return this.systemStore.settings.SOURCE.src_hostname
      }
    },
    destinationUrl() {
      if (!this.isSettingsStoreEmpty) {
        return this.systemStore.settings.DESTINATION.dstn_hostname
      }
    },
    directTransfer() {
      if (!this.isSettingsStoreEmpty) {
        return Boolean(this.systemStore.settings.APP.direct_transfer)
      }
    },
    migrationInProgress() {
      return this.systemStore.migrationInProgress
    },
    isSettingsStoreEmpty() {
      return JSON.stringify(this.systemStore.settings) === '{}'
    },
    directTransferGeneratedRequest() {
      return Object.keys(this.systemStore.directTransferGeneratedRequest).length > 0
    }
  },
  data () {
    return {
      statusColumns: [
        'task_id',
        'status',
        'task_name',
        'entity_name'
      ],
      statusData: [],
      params: [
          {param: 'skip_users', label: 'Skip Users'},
          {param: 'skip_groups', label: 'Skip Groups'},
          {param: 'skip_projects', label: 'Skip Projects'},
          {param: 'commit', label: 'Commit'}
      ],
      dryRun: true
    }
  },
  mounted: function () {
    this.emitter.on('migration-in-progress', () => {
      this.systemStore.updateMigrationInProgress(true)
      this.pollMigrationStatus()
    })
    this.emitter.on('save-modified-payload', (data) => {
      this.systemStore.updateDirectTransferModifiedRequest(data)
    })
    this.emitter.on('confirm-migration', () => {
      this.triggerMigration()
    })
  },
  beforeDestroy: function() {
    this.emitter.off('migration-in-progress')
  },
  methods: {
    promptConfirmation: function() {
      let params = {}
      let form = new FormData(document.getElementById('migrate-params'))
      for (const [key, value] of form) {
          params[key] = Boolean(value)
      }
      if (params.hasOwnProperty('commit')) {
        this.dryRun = false
        this.emitter.emit('show-dry-run', {
          left: this.systemStore.directTransferGeneratedRequest, 
          right: this.systemStore.directTransferModifiedRequest,
          dryRun: false
        })
      } else {
        this.triggerMigration()
      }
      
    },
    triggerMigration: function() {
      this.systemStore.updateMigrationInProgress(true)
      let params = {}
      let form = new FormData(document.getElementById('migrate-params'))
      for (const [key, value] of form) {
          params[key] = Boolean(value)
      }
      if (this.directTransfer === true) {
        let migrateEndpoint = `${import.meta.env.VITE_API_ROOT}/api/direct_transfer/migrate`
        if (params.hasOwnProperty('skip_projects')) {
          migrateEndpoint += '/groups'
        } else if (params.hasOwnProperty('skip_groups')) {
          migrateEndpoint += '/projects'
        } else {
          migrateEndpoint += '/groups'
        }
        if (params) {
          migrateEndpoint += '?' + new URLSearchParams(params).toString()
        }
        if (params.hasOwnProperty('commit')) {
          this.dryRun = false
        }
        var payload = null
        if (!Object.keys(this.systemStore.directTransferModifiedRequest).length == 0) {
          payload = {"payload": toRaw(this.systemStore.directTransferModifiedRequest)}
        }
        axios.post(migrateEndpoint, payload).then(response => {
          if (!params.hasOwnProperty('commit')) {
            this.pollDryRunStatus(response.data.task_id)
          } else {
            this.dryRun = false
            this.pollInitialRequest(response.data.task_id)
          }
        })
      } else {
        // trigger file-based or other SCM import request
      }
    },
    updateStatusTable: function(endpoint) {
      return axios.get(`${import.meta.env.VITE_API_ROOT}/api/direct_transfer/${endpoint}`).then(response => {
        if (response.data.length > 1) {
          this.dryRun = false
        }
        this.statusData = response.data
        return response
      })
    },
    pollDryRunStatus: async function(id) {
      let pollStatus = () => this.updateStatusTable(`import-status/${id}`)
      let validate = result => result.data.status == 'STARTED'
      let response = await poll(pollStatus, validate, 2500)
      if (response.data.result != null) {
        
        this.systemStore.updateMigrationInProgress(false)
        this.systemStore.updateDirectTransferGeneratedRequest(response.data.result.dry_run_data).then(() => {
          this.emitter.emit('show-dry-run', {
            left: this.systemStore.directTransferGeneratedRequest, 
            right: null,
            dryRun: true
          })
        })
        
        this.dryRun = true
      } else {
        this.updateStatusTable('migration-status')
      }
      this.systemStore.updateMigrationInProgress(false)
    },
    pollInitialRequest: async function(id) {
      let pollStatus = () => this.updateStatusTable(`import-status/${id}`)
      let validate = result => result.data.status == 'STARTED'
      let response = await poll(pollStatus, validate, 2500)
      if (response.data.result != null && !response.data.result.hasOwnProperty('errors')) {
        this.pollMigrationStatus()
      } else if (response.data.result.hasOwnProperty('errors')) {
        this.systemStore.updateMigrationInProgress(false)
        this.emitter.emit('alert', {
          'message': `Failed to trigger migration. Refer to task ${id} in the Task Queue`,
          'messageType': 'error'
        })
      }
    },
    pollMigrationStatus: async function() {
      let pollStatus = () => this.updateStatusTable('migration-status')
      let validate = result => result.data.length != 0
      let response = await poll(pollStatus, validate, 5000)
      if (response.data.length == 0) {
        this.emitter.emit('alert', {
          'message': 'Migration is complete',
          'messageType': 'done'
        })
        this.dryRun = true
      } else {
        this.updateStatusTable('migration-status')
      }
      this.systemStore.updateMigrationInProgress(false)
    },
    showDryRun: function() {
      this.emitter.emit('show-dry-run', {
        left: this.systemStore.directTransferGeneratedRequest, 
        right: this.systemStore.directTransferModifiedRequest,
        dryRun: true
      })
    }
  }
}
</script>

<style scoped>
.disable-box {
  position: absolute;
  background-color: #ccc;
  z-index: 5;
  /* width: 100%;
  height: 100%; */
}
</style>
