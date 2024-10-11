<template>
  <StageTable asset="users" :columns="columns" addEvent="stageUser" removeEvent="unstageUser" assetStore="stagedUsers"/>
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
  }
}
</script>
