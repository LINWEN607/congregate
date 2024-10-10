<template>
  <div id='projects'>
    <h2>Stage Projects</h2>
    <div id="table-control"><button>Select All</button><button>Deselect All</button><span>Total Selected: {{ selected }}</span></div>
    <div ref="table" id = "staging-table">
      
    </div>
    <Footer msg='Stage' asset='stage-projects' />
  </div>
</template>

<script>
import axios from 'axios'
import {TabulatorFull as Tabulator} from 'tabulator-tables';
import Footer from '@/components/Footer.vue'


export default {
  name: 'Projects',
  components: {
    Footer
  },
  data () {
    return {
      tabulator: null, //variable to hold your table
      tableData: [],
      columns: [
        {
          title: 'ID',
          field: 'id',
        },
        {
          title: 'Name',
          field: 'name'
        },
        {
          title: 'Namespace',
          field: 'path_with_namespace'
        },
        {
          title: 'Type',
          field: 'namespace.kind'
        },
        {
          title: 'Visibility',
          field: 'visibility'
        },
        {
          title: 'Archived',
          field: 'archived'
        },
        {
          title: 'Last Activity',
          field: 'last_activity_at'
        }
      ],
      rows: [],
      selected: 0
    }
  },
  mounted: function () {
    this.getData()
    //instantiate Tabulator when element is mounted
    
    
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
        this.tableData = response.data
        this.tabulator = new Tabulator(this.$refs.table, {
        // ajaxURL: `${import.meta.env.VITE_API_ROOT}/api/data/projects`,
          data: this.tableData, //link data to table
          reactiveData:true, //enable data reactivity
          columns: this.columns, //define table columns
          selectableRows: true,
          rowHeader:{
            formatter:"rowSelection", 
            titleFormatter:"rowSelection", 
            headerSort:false, 
            resizable: false, 
            frozen:true, 
            headerHozAlign:"center", 
            hozAlign:"center"
          },
          pagination: true,
          paginationSize: 50
        });
        let that = this
        this.tabulator.on("rowSelectionChanged", function(data, rows){
          console.log("Row count changed")
          that.selected = data.length
          console.log(that.selected)
        });
        // this.tabulator.replaceData()
        // this.getStagedData()
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
<style>
@import "../../node_modules/tabulator-tables/dist/css/tabulator.css";
#staging-table {
  margin-bottom: 10%;
}
#table-control {
  width: 100%;
  text-align: left;
}
</style>