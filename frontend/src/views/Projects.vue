<template>
  <div class='projects'>
    Projects
    <div class="table">
      <vue-good-table
            :columns="columns"
            :rows="rows"
            :search-options="{enabled: true}"
            :select-options="{ enabled: true }"
        />
    </div>
    <Footer msg='Stage' asset='stage_button' />
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
      rows: []
    }
  },
  mounted: function () {
    this.getData()
  },
  methods: {
    getData: function () {
      axios.get('http://localhost:8000/data/project_json').then(response => {
        console.log(response.data)
        this.rows = response.data
      }).catch(function (error) {
        console.log(error)
      })
    }
  }
}
</script>
