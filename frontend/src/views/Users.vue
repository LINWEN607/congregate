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
      axios.get('http://localhost:8000/data/users').then(response => {
        console.log(response.data)
        this.rows = response.data
      }).catch(function (error) {
        console.log(error)
      })
    },
    stageData: function () {
      if (this.$refs['users-table'].selectedRows) {
        const ids = []
        this.$refs['users-table'].selectedRows.forEach(element => {
          ids.push(element.id)
        })
        console.log(ids)
      }
    }
  }
}
</script>
