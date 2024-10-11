<template>
    <div id='stage-table'>
        <h2>Stage {{ asset }}</h2>
        <div id="table-control">
            <button @click="selectAll()">Select All</button>
            <button @click="deselectAll()">Deselect All</button>
            <input type="text" v-model="filterQuery">Filter
            <span>Total Selected: {{ selected }}</span>
            <button v-on:click="stageData()" :id="asset"
                class="stage_button">Stage {{ asset }}</button>
        </div>
        <div ref="table" id = "staging-table"></div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  import { mapStores } from 'pinia'
  import {TabulatorFull as Tabulator} from 'tabulator-tables';
  import { useSystemStore } from '@/stores/system'
  
  export default {
    name: 'StageTable',
    props: {
        asset: String,
        columns: Array,
        addEvent: String,
        removeEvent: String,
        assetStore: String
    },
    components: {},
    computed: {
        ...mapStores(useSystemStore)
    },
    data () {
      return {
        tabulator: null, //variable to hold your table
        tableData: [],
        rows: [],
        selected: 0,
        filterQuery: ''
      }
    },
    mounted: function () {
        
        // this.getData()
        this.initializeTable()
        this.tabulator.on("rowSelectionChanged", (data) => {
            console.log(data)
            // this.tabulator.selectRow(data[0].id-1)
            // this.updateSelectedRowCount(data)
        })
        this.tabulator.on("tableBuilt", () => {
            this.tabulator.setData(`${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`)
        })
        this.tabulator.on("rowSelected", (row) => {
            this.systemStore[this.addEvent](row._row.data.id)
        })
        this.tabulator.on("rowDeselected", (row) => {
            this.systemStore[this.removeEvent](row._row.data.id)
        })
        this.tabulator.on("dataLoaded", (data) => {
            if (this.systemStore[this.assetStore].size > 0) {
                let rows = []
                for (let row of data) {
                    if (this.systemStore[this.assetStore].has(row.id)) {
                        rows.push(row.id)
                    }
                }
                // let select = this.tabulator.selectRow(this.tabulator.getRows().filter(row => rows.includes(row.getData().id)))
                console.log(this.tabulator.rowManager.rows)
                let currentRows = this.tabulator.rowManager.getDisplayRows()
                console.log(this.tabulator.rowManager.getDisplayRowIndex(currentRows[0]))
                
                console.log(this.tabulator.rowManager.findRow(currentRows[0]))
                this.tabulator.selectRow(currentRows[0])
            }
        });
      //instantiate Tabulator when element is mounted
    },
    watch: {
        filterQuery: function(val, oldVal) {
            console.log("Attempting to apply filter")
            this.tabulator.setFilter(this.matchAny, {value: val})
        }
    },
    methods: {
        selectAll() {
            // this.tabulator.selectRow()
            this.tabulator.selectRow([1, 2, 3])
        },
        deselectAll() {
            this.tabulator.deselectRow()
        },
        matchAny(data, filterParams){
            //data - the data for the row being filtered
            //filterParams - params object passed to the filter

            var match = false;
            for(var key in data){
                if(data[key]) {
                    if(String(data[key]).includes(filterParams.value)){
                        // console.log("Found match with " + filterParams.value + " and " + String(data[key]))
                        match = true;
                    }
                }
            }

            return match;
        },
        updateSelectedRowCount(data) {
            this.selected = data.length
            console.log(this.selected)
        },
        initializeTable: function() {
            this.tabulator = new Tabulator(this.$refs.table, {
                debugEventsInternal:true,
                debugEventsExternal:true,
                index: "id",
                ajaxURL: `${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`,
                ajaxConfig:{
                    method: "GET"
                },
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
                paginationSize: 30,
                paginationMode:"remote",
                dataSendParams:{
                    "size":"per_page", //change page request parameter to "pageNo"
                },
                dataLoader: true,
                layout:"fitDataStretch"
            })
        },
        getData: function () {
            axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`).then(response => {
                this.tableData = response.data
                this.initializeTable()
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