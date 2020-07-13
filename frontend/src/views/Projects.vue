<template>
  <div class='projects'>
    Projects
    <div class="table">
      <vue-good-table
            ref="projects-table"
            :columns="columns"
            :rows="rows"
            :search-options="{enabled: true}"
            :select-options="{ enabled: true }"
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
import { EventBus } from '@/event-bus.js'

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
          label: 'Project Name',
          field: 'path'
        },
        {
          label: 'Description',
          field: 'description'
        },
        {
          label: 'Namespace',
          field: 'namespace.full_path'
        },
        {
          label: 'Project Type',
          field: 'namespace.kind'
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
    EventBus.$on('stage-projects', event => {
      this.stageData()
    })
  },
  methods: {
    getData: function () {
      axios.get('/data/project_json').then(response => {
        this.rows = response.data
        this.getStagedData()
      }).catch(function (error) {
        console.log(error)
      })
    },
    getStagedData: function () {
      axios.get('/data/staged_projects').then(response => {
        var ids = []
        response.data.forEach(element => {
          ids.push(element.id)
        })
        const table = this.$refs['projects-table']
        this.$refs['projects-table'].rows.forEach((element, ind) => {
          if (ids.includes(element.id)) {
            table.$set(table.rows[ind], 'vgtSelected', true)
          }
        })
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['projects-table'].selectedRows) {
        const ids = []
        this.$refs['projects-table'].selectedRows.forEach(element => {
          ids.push(element.id)
        })
        axios.post('/stage', String(ids)).then(response => {
          console.log(response)
        })
      }
    }
  }
}
</script>
