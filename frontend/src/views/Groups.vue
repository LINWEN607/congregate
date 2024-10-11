<template>
  <StageTable asset="groups" :columns="columns"/>
</template>

<script>
import StageTable from '@/components/StageTable.vue'

export default {
  name: 'Groups',
  components: {
    StageTable
  },
  data () {
    return {
      columns: [
        {
          title: 'ID',
          field: 'id',
          type: 'number'
        },
        {
          title: 'Name',
          field: 'name'
        },
        {
          title: 'Visibility',
          field: 'visibility'
        },
        {
          title: 'Full Path',
          field: 'full_path'
        }
      ],
    }
  },
  // mounted: function () {
  //   this.getData()
  //   this.$emitter.on('stage-groups', event => {
  //     this.stageData()
  //   })
  // },
  // beforeDestroy: function() {
  //   this.$emitter.off('stage-groups')
  // },
  // methods: {
  //   getData: function () {
  //     axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/groups`).then(response => {
  //       this.rows = response.data
  //       this.getStagedData()
  //     }).catch(function (error) {
  //       console.log(error)
  //     })
  //   },
  //   getStagedData: function () {
  //     axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged_groups`).then(response => {
  //       var ids = []
  //       response.data.forEach(element => {
  //         ids.push(element.id)
  //       })
  //       let table = this.$refs['groups-table']
  //       this.$refs['groups-table'].rows.forEach((element, ind) => {
  //         if (ids.includes(element.id)) {
  //           console.log("updating group table")
  //           table.$set(table.rows[ind], 'vgtSelected', true)
  //         }
  //       })
  //     }).catch(function (error) {
  //       console.log(error)
  //     })
  //   },
  //   stageData: function () {
  //     if (this.$refs['groups-table'].selectedRows) {
  //       let ids = []
  //       this.$refs['groups-table'].selectedRows.forEach(element => {
  //         ids.push(element.id)
  //       })
  //       axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/groups`, String(ids)).then(response => {
  //         console.log(response)
  //         this.$emitter.emit('alert', {
  //           'message': response.data,
  //           'messageType': 'done'
  //         })
  //       }).catch(response => {
  //         console.log(response)
  //         this.$emitter.emit('alert', {
  //           'message': 'Unable to stage groups',
  //           'messageType': 'error'
  //         })
  //       })
  //     }
  //   }
  // }
}
</script>
