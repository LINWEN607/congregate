<template>
    <div id='stage-table'>
        <h2>Stage {{ capitalizedAssetName }}</h2>
        <div id="table-stats">
            <span>Total Selected: {{ totalSelectedCount }} </span>
            <sub>
            <details v-if="pendingChanges">
                <summary>Pending Changes</summary>
                <ul>Unstaged IDs:
                    <li v-for="id in diffIds">{{ id }}</li>
                </ul>
            </details>
            </sub>
        </div>
        <div id="table-control">
            <button @click="selectAll()">Select All</button>
            <button @click="deselectAll()">Deselect All</button>
            <button v-on:click="stageData()" :id="asset"
                class="stage_button">Stage {{ asset }}</button>
            Filter <input type="text" v-model="filterQuery">
            
        </div>
        <div ref="table" id = "staging-table"></div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  import { mapStores } from 'pinia'
  import {TabulatorFull as Tabulator} from 'tabulator-tables';
  import _ from 'lodash'
  import { useSystemStore } from '@/stores/system'
  
  export default {
    name: 'StageTable',
    props: {
        asset: String,
        columns: Array,
        addEvent: String,
        removeEvent: String,
        assetStore: String,
        storeGetter: String
    },
    components: {},
    computed: {
        ...mapStores(useSystemStore),
        pendingChanges() {
            return !_.isEqual(this.totalSelectedCount, this.stagedDataFromMongo.length)
        }
    },
    data () {
      return {
        tabulator: null, //variable to hold your table
        tableData: [],
        rows: [],
        totalSelectedCount: 0,
        filterQuery: '',
        capitalizedAssetName: '',
        stagedDataFromMongo: [],
        diffIds: []
      }
    },
    mounted: function () {
        this.initializeTable()
        // Once the table is fully built, select the currently staged data
        this.tabulator.on("tableBuilt", () => {
            this.getStagedData()
        })
        // When a row is selected, store that speciifc row ID in the pinia store
        this.tabulator.on("rowSelected", (row) => {
            console.log("Updating store")
            this.systemStore[this.addEvent](row._row.data.id).then(() => {
                this.totalSelectedCount = this.systemStore[this.assetStore].size
                this.diffIds = _.difference(Array.from(this.systemStore[this.assetStore]), this.stagedDataFromMongo)
            })
        })
        // When a row is deselected, remove that speciifc row ID in the pinia store
        this.tabulator.on("rowDeselected", (row) => {
            console.log("Removing from store")
            this.systemStore[this.removeEvent](row._row.data.id).then(() => {
                this.totalSelectedCount = this.systemStore[this.assetStore].size
                this.diffIds = _.difference(Array.from(this.systemStore[this.assetStore]), this.stagedDataFromMongo)
            })
        })
        // If there is data in the store, iterate over the IDs and progammatically select rows accordingly
        // This is necessary for programmatically setting the staged data when the page loads
        this.tabulator.on("dataProcessed", (data) => {
            if (this.systemStore[this.assetStore].size > 0) {
                let rows = []
                for (let row of data) {
                    if (this.systemStore[this.assetStore].has(row.id)) {
                        rows.push(row.id)
                    }
                }
                this.tabulator.selectRow(rows)
            }
        });
        this.capitalizedAssetName = this.asset[0].toUpperCase() + this.asset.slice(1)
    },
    watch: {
        filterQuery: function(val, oldVal) {
            setTimeout(() => {
                if (val == this.filterQuery) {
                    /* 
                    The '*' and 'like' get stripped out when we make the request.
                    They need to exist here so tabulator can build out the initial filter object
                    */
                    this.tabulator.setFilter("*", "like", val)
                }
            }, 500)
        }
    },
    methods: {
        selectAll() {
            this.tabulator.selectRow()
        },
        deselectAll() {
            this.tabulator.deselectRow()
        },
        updateSelectedRowCount() {
            this.totalSelected = this.assetStore.size
            console.log(this.totalSelected)
        },
        initializeTable: function() {
            this.tabulator = new Tabulator(this.$refs.table, {
                index: "id",
                ajaxURL: `${import.meta.env.VITE_API_ROOT}/api/data/${this.asset}`,
                ajaxConfig:{
                    method: "GET"
                },
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
                    "size":"per_page",
                    "filter": "filter_by"
                },
                dataLoader: true,
                layout:"fitDataStretch",
                filterMode:"remote",
                // Replace the 'filter_by' object with just the filter term 
                // since we are doing a multi-column partial word search
                ajaxURLGenerator:function(url, config, params){
                    if ('filter_by' in params) {
                        if ((params.filter_by.length) > 0) {
                            let filterValue = params.filter_by[0].value
                            params.filter_by = filterValue
                        }
                    }
                    let queryString = new URLSearchParams(params).toString()
                    return url + "?" + queryString;
                },
            })
        },
        getStagedData: function () {
            axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged/${this.asset}`).then(response => {
                let ids = []
                this.stagedDataFromMongo = response.data.map((d) => d.id)
                if (this.systemStore[this.assetStore].size == 0) {
                    response.data.forEach(element => {
                        ids.push(element.id)
                        this.systemStore[this.addEvent](element.id).then(() => {
                            this.totalSelectedCount = this.systemStore[this.assetStore].size
                        })
                    })
                    this.tabulator.selectRow(ids)
                }
                
            }).catch(function (error) {
                console.log(error)
            })
        },
        stageData: function () {
            if (this.systemStore[this.assetStore]) {
                axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/${this.asset}`, String(Array.from(this.systemStore[this.assetStore]))).then(response => {
                    console.log(response)
                    this.emitter.emit('alert', {
                        'message': response.data,
                        'messageType': 'done'
                    })
                }).catch(response => {
                    console.log(response)
                    this.emitter.emit('alert', {
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
#table-control, #table-stats {
    width: 100%;
    text-align: left;
    margin-bottom: 1%;
}
#table-control button {
    margin-right: 1%;
}
button {
    cursor: pointer;
}
</style>