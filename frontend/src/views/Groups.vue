<template>
  <div class="groups">
    Groups
    <div class="table">
        <vue-good-table
            ref="groups-table"
            id="groups-table"
            :columns="columns"
            :rows="rows"
            :search-options="{ enabled: true }"
            :select-options="{ enabled: true }"
            :pagination-options="{ enabled: true, perPage: 25 }"
            :line-numbers="true"
        />
    </div>
    <Footer msg="Stage" asset="stage-groups"/>
  </div>
</template>

<script>
import 'vue-good-table/dist/vue-good-table.css'
import { VueGoodTable } from 'vue-good-table'
import Footer from '@/components/Footer.vue'
import axios from 'axios'

export default {
  name: 'Groups',
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
          label: 'Visibility',
          field: 'visibility'
        },
        {
          label: 'Full Path',
          field: 'full_path'
        }
      ],
      rows: []
    }
  },
  mounted: function () {
    this.getData()
    this.$emitter.on('stage-groups', event => {
      this.stageData()
    })
  },
  beforeDestroy: function() {
    this.$emitter.off('stage-groups')
  },
  methods: {
    getData: function () {
      axios.get('/data/groups').then(response => {
        this.rows = response.data
        this.getStagedData()
      }).catch(function (error) {
        console.log(error)
      })
    },
    getStagedData: function () {
      axios.get('/data/staged_groups').then(response => {
        var ids = []
        response.data.forEach(element => {
          ids.push(element.id)
        })
        let table = this.$refs['groups-table']
        this.$refs['groups-table'].rows.forEach((element, ind) => {
          if (ids.includes(element.id)) {
            console.log("updating group table")
            table.$set(table.rows[ind], 'vgtSelected', true)
          }
        })
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['groups-table'].selectedRows) {
        let ids = []
        this.$refs['groups-table'].selectedRows.forEach(element => {
          ids.push(element.id)
        })
        axios.post('/api/stage/groups', String(ids)).then(response => {
          console.log(response)
        })
      }
    }
  }
}
</script>
