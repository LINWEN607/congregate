<template>
    <div class='listing'>
        <ActionCard title="List Data">
            Retrieve a list of data from the source instance
            <div v-if="!listingInProgress">
                <button @click="triggerList" id="list-data-button" type="button">List data</button>
                <ParamForm :params="listParams" formId="list-params"/>
            </div>
            <br>
            <span v-if="listingInProgress"><i>Listing data from source instance</i><span class='loader'></span></span>
            <br>
            <i><sub>List was last run on {{ lastRun }}</sub></i>
        </ActionCard>
    </div>
</template>

<script>
import axios from 'axios'
import { mapStores } from 'pinia'
import { useSystemStore } from '@/stores/system'
import { poll, pollingIntervals } from '@/scripts/poll.js'
import ActionCard from '@/components/ActionCard.vue'
import ParamForm from '@/components/ParamForm.vue'

export default {
  name: 'ListCard',
  components: {
    ActionCard,
    ParamForm
  },
  computed: {
    ...mapStores(useSystemStore),
    listingInProgress() {
      if (this.systemStore !== null) {
        return this.systemStore.listingInProgress
      }
    }
  },
  data () {
    return {
        lastRun: null,
        listParams: [
            {param: 'skip_users', label: 'Skip Users'},
            {param: 'skip_groups', label: 'Skip Groups'},
            {param: 'skip_projects', label: 'Skip Projects'},
            {param: 'partial', label: 'Partial'},
            {param: 'skip_project_members', label: 'Skip Project Members'},
            {param: 'skip_ci', label: 'Skip CI'},
            {param: 'src_instances', label: 'src_instances'},
            {param: 'subset', label: 'Subset'}
        ],
        listTaskId: null
    }
  },
  mounted: function () {
    this.checkLastList()
    this.$emitter.on('listing-in-progress', id => {
      this.systemStore.updateListingInProgress(true)
      this.listTaskId = id
      this.pollListStatus()
    })
  },
  beforeDestroy: function() {
    this.$emitter.off('listing-in-progress')
  },
  methods: {
    triggerList: function() {
      let params = {}
      let form = new FormData(document.getElementById('list-params'))
      for (const [key, value] of form) {
          params[key] = Boolean(value)
      }
      axios.post(`${import.meta.env.VITE_API_ROOT}/api/list`, 
        JSON.stringify(params),
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }).then(response => {
        this.listTaskId = response.data['task-id']
        this.$emitter.emit('alert', {
          'message': 'Listing in progress',
          'messageType': 'info'
        })
        this.systemStore.updateListingInProgress(true)
        this.pollListStatus()
      })
    },
    pollListStatus: async function() {
      let pollStatus = () => axios.get(`${import.meta.env.VITE_API_ROOT}/api/list-status/${this.listTaskId}`)
        .catch(() => {
          this.$emitter.emit('alert', {
            'message': 'Listing failed. Check the congregate logs for a traceback',
            'messageType': 'error'
          })
          this.systemStore.updateListingInProgress(false)
        })
      let validate = result => {
        console.log("Checking actual result")
        return !['SUCCESS', 'FAILURE'].includes(result.data.status)
      }
      let updateCounts = result => {
        console.log(this.listingInProgress)
        console.log("Updating counts")
        this.$emitter.emit('stream-list-stats', (result.data.counts))
        return this.listingInProgress
      }
      // Shorter polling time to update the counts in the UI
      poll(pollStatus, updateCounts, pollingIntervals.UPDATE)
      // Longer polling time to fully validate listing is complete
      let response = await poll(pollStatus, validate, pollingIntervals.VALIDATE)
      if (response.data.status == 'SUCCESS') {
        this.$emitter.emit('alert', {
          'message': 'Listing is complete',
          'messageType': 'done'
        })
        axios.post(`${import.meta.env.VITE_API_ROOT}/api/dump-list-data`).then(() => {
          this.checkLastList()
          this.$emitter.emit('update-stage')
        })
      } else if (response.data.status == 'FAILURE') {
        this.$emitter.emit('alert', {
          'message': 'Listing failed. Check the congregate logs for a traceback',
          'messageType': 'error'
        })
      }
      this.systemStore.updateListingInProgress(false)
    },
    checkLastList: function() {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/last-list`).then(response => {
        this.lastRun = response.data['last-modified-date']
      })
    }
  }
}
</script>
