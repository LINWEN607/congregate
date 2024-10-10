<template>
    <div id='stage-table'>
        <h2>Stage {{ asset }}</h2>
        <div id="table-control">
            <button>Select All</button>
            <button>Deselect All</button>
            <span>Total Selected: {{ selected }}</span>
            <button v-on:click="stageData()" :id="asset"
                class="stage_button">Stage {{ asset }}</button>
        </div>
        <div ref="table" id = "staging-table"></div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  import {TabulatorFull as Tabulator} from 'tabulator-tables';
  
  
  export default {
    name: 'StageTable',
    props: {
        asset: String,
        columns: Array
    },
    components: {},
    data () {
      return {
        tabulator: null, //variable to hold your table
        tableData: [],
        rows: [],
        selected: 0
      }
    },
    mounted: function () {
        
        this.getData()
      //instantiate Tabulator when element is mounted
    },
    methods: {
        updateSelectedRowCount(data) {
            this.selected = data.length
            console.log(this.selected)
        },
        getData: function () {
            axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`).then(response => {
                this.tableData = response.data
                this.tabulator = new Tabulator(this.$refs.table, {
                // ajaxURL: `${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`,
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
                paginationSize: 50,
                dataLoader: true
                });
                this.tabulator.on("rowSelectionChanged", (data) => {
                    this.updateSelectedRowCount(data)
                })
            }).catch(function (error) {
                console.log(error)
            })
        },
        getStagedData: function () {
            axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged_${this.asset}`).then(response => {
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
            if (this.tabulator.getSelectedData()) {
                let ids = []
                this.tabulator.getSelectedData().forEach(element => {
                    ids.push(element.id)
                })
                console.log(ids)
                axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/${this.asset}`, String(ids)).then(response => {
                    console.log(response)
                    this.$emitter.emit('alert', {
                        'message': response.data,
                        'messageType': 'done'
                    })
                }).catch(response => {
                    console.log(response)
                    this.$emitter.emit('alert', {
                        'message': 'Unable to stage '+this.asset,
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