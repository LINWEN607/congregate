<template>
  <div class="groups">
    Groups
    <div class="table">
        <vue-good-table
            :columns="columns"
            :rows="rows"
            :search-options="{enabled: true}"
            :select-options="{ enabled: true }"
        />
    </div>
    <Footer msg="Stage" asset="stage_groups"/>
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
  },
  methods: {
    getData: function () {
      axios.get('http://localhost:8000/data/groups').then(response => {
        console.log(response.data)
        this.rows = response.data
      }).catch(function (error) {
        console.log(error)
      })
    }
  }
}
</script>
