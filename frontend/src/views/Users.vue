<template>
  <StageTable asset="users" :columns="columns"/>
</template>

<script>
import StageTable from '@/components/StageTable.vue'

export default {
  name: 'Users',
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
          title: 'Username',
          field: 'username'
        },
        {
          title: 'Email',
          field: 'email'
        },
        {
          title: 'State',
          field: 'state'
        }
      ],
      rows: []
    }
  },
  // mounted: function () {
  //   this.getData()
  //   this.$emitter.on('stage-users', event => {
  //     this.stageData()
  //   })
  // },
  // beforeDestroy: function() {
  //   this.$emitter.off('stage-users')
  // },
  // methods: {
  //   getData: function () {
  //     axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/users`).then(response => {
  //       this.rows = response.data
  //       this.getStagedData()
  //     }).catch(function (error) {
  //       console.log(error)
  //     })
  //   },
  //   getStagedData: function () {
  //     axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/staged_users`).then(response => {
  //       let ids = []
  //       response.data.forEach(element => {
  //         ids.push(element.id)
  //       })
  //       console.log(ids)
  //       let table = this.$refs['users-table']
  //       this.$refs['users-table'].rows.forEach((element, ind) => {
          
  //         if (ids.includes(element.id)) {
  //           console.log("updating user table")
  //           table.$set(table.rows[ind], 'vgtSelected', true)
  //         }
  //       })
  //     }).catch(function (error) {
  //       console.log(error)
  //     })
  //   },
  //   stageData: function () {
  //     if (this.$refs['users-table'].selectedRows) {
  //       let usernames = []
  //       this.$refs['users-table'].selectedRows.forEach(element => {
  //         usernames.push(element.username)
  //       })
  //       axios.post(`${import.meta.env.VITE_API_ROOT}/api/stage/users`, String(usernames)).then(response => {
  //         console.log(response)
  //         this.$emitter.emit('alert', {
  //           'message': response.data,
  //           'messageType': 'done'
  //         })
  //       }).catch(response => {
  //         console.log(response)
  //         this.$emitter.emit('alert', {
  //           'message': 'Unable to stage users',
  //           'messageType': 'error'
  //         })
  //       })
  //     }
  //   }
  // }
}
</script>
