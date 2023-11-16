<template>
  <div class='projects'>
    Projects
    <div class="table">
      <vue-good-table
            ref="projects-table"
            id="projects-table"
            :columns="columns"
            :rows="rows"
            :search-options="{ enabled: true }"
            :select-options="{ enabled: true }"
            :pagination-options="{ enabled: true, perPage: 25 }"
            :line-numbers="true"
        />
    </div>
    <Footer msg='Stage' asset='stage-projects' />
  </div>
</template>

<script>
import 'vue-good-table/dist/vue-good-table.css'
import { VueGoodTable } from 'vue-good-table'
import axios from 'axios'
import Footer from '@/components/Footer.vue'

export default {
  name: 'Projects',
  components: {
    VueGoodTable,
    Footer
  },
  data () {
    return {
      columns: [
        {
          label: 'ID',
          field: 'id',
          type: 'number'
        },
        {
          label: 'Name',
          field: 'name'
        },
        {
          label: 'Namespace',
          field: 'path_with_namespace'
        },
        {
          label: 'Type',
          field: 'namespace.kind'
        },
        {
          label: 'Visibility',
          field: 'visibility'
        },
        {
          label: 'Archived',
          field: 'archived'
        },
        {
          label: 'Last Activity',
          field: 'last_activity_at'
        }
      ],
      rows: [],
      selected: []
    }
  },
  mounted: function () {
    this.getData()
    this.$emitter.on('stage-projects', event => {
      this.stageData()
    })
  },
  beforeDestroy: function() {
    this.$emitter.off('stage-projects')
  },
  methods: {
    getData: function () {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/projects`).then(response => {
        this.rows = response.data
        this.getStagedData()
      }).catch(function (error) {
        console.log(error)
      })
    },
    getStagedData: function () {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged_projects`).then(response => {
        let ids = []
        response.data.forEach(element => {
          ids.push(element.id)
        })
        let table = this.$refs['projects-table']
        
        this.$refs['projects-table'].rows.forEach((element, ind) => {
          
          if (ids.includes(element.id)) {
            console.log("updating projects table")
            table.$set(table.rows[ind], 'vgtSelected', true)
          }
        })
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['projects-table'].selectedRows) {
        let ids = []
        this.$refs['projects-table'].selectedRows.forEach(element => {
          ids.push(element.id)
        })
        axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/projects`, String(ids)).then(response => {
          console.log(response)
          this.$emitter.emit('alert', {
            'message': response.data,
            'messageType': 'done'
          })
        }).catch(response => {
          console.log(response)
          this.$emitter.emit('alert', {
            'message': 'Unable to stage projects',
            'messageType': 'error'
          })
        })
      }
    }
  }
}
</script>
