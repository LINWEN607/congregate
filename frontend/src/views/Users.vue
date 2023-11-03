<template>
  <div class="users">
    Users
    <div class="table">
        <vue-good-table
            ref="users-table"
            id="users-table"
            :columns="columns"
            :rows="rows"
            :search-options="{ enabled: true }"
            :select-options="{ enabled: true }"
            :pagination-options="{ enabled: true, perPage: 25 }"
            :line-numbers="true"
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
        },
        {
          label: 'State',
          field: 'state'
        }
      ],
      rows: []
    }
  },
  mounted: function () {
    this.getData()
    this.$emitter.on('stage-users', event => {
      this.stageData()
    })
  },
  beforeDestroy: function() {
    this.$emitter.off('stage-users')
  },
  methods: {
    getData: function () {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/users`).then(response => {
        this.rows = response.data
        this.getStagedData()
      }).catch(function (error) {
        console.log(error)
      })
    },
    getStagedData: function () {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged_users`).then(response => {
        let ids = []
        response.data.forEach(element => {
          ids.push(element.id)
        })
        console.log(ids)
        let table = this.$refs['users-table']
        this.$refs['users-table'].rows.forEach((element, ind) => {
          
          if (ids.includes(element.id)) {
            console.log("updating user table")
            table.$set(table.rows[ind], 'vgtSelected', true)
          }
        })
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['users-table'].selectedRows) {
        let usernames = []
        this.$refs['users-table'].selectedRows.forEach(element => {
          usernames.push(element.username)
        })
        axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/users`, String(usernames)).then(response => {
          console.log(response)
          this.$emitter.emit('alert', {
            'message': response.data,
            'messageType': 'done'
          })
        }).catch(response => {
          console.log(response)
          this.$emitter.emit('alert', {
            'message': 'Unable to stage users',
            'messageType': 'error'
          })
        })
      }
    }
  }
}
</script>
