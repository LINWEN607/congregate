<template>
  <div class="users">
    Users
    <div class="table">
        <vue-good-table
            ref="users-table"
            :columns="columns"
            :rows="rows"
            :search-options="{enabled: true}"
            :select-options="{ enabled: true }"
        />
    </div>
    <Footer msg="Stage" asset="stage-users"/>
  </div>
</template>

<script>
import 'vue-good-table/dist/vue-good-table.css'
import { VueGoodTable } from 'vue-good-table'
import axios from 'axios'
import Footer from '@/components/Footer.vue'
import { EventBus } from '@/event-bus.js'

export default {
  name: 'Users',
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
          label: 'Username',
          field: 'username'
        },
        {
          label: 'Email',
          field: 'email'
        }
      ],
      rows: []
    }
  },
  mounted: function () {
    this.getData()
    EventBus.$on('stage-users', event => {
      this.stageData()
    })
  },
  methods: {
    getData: function () {
      axios.get('/data/users').then(response => {
        this.rows = response.data
        this.getStagedData()
      }).catch(function (error) {
        console.log(error)
      })
    },
    getStagedData: function () {
      axios.get('/data/staged_users').then(response => {
        var ids = []
        response.data.forEach(element => {
          ids.push(element.id)
        })
        console.log(ids)
        const table = this.$refs['users-table']
        this.$refs['users-table'].rows.forEach((element, ind) => {
          if (ids.includes(element.id)) {
            table.$set(table.rows[ind], 'vgtSelected', true)
          }
        })
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['users-table'].selectedRows) {
        const usernames = []
        this.$refs['users-table'].selectedRows.forEach(element => {
          usernames.push(element.username)
        })
        axios.post('/append_users', String(usernames)).then(response => {
          console.log(response)
        })
      }
    }
  }
}
</script>
