<template>
  <StageTable 
    asset="groups" 
    :columns="columns" 
    addEvent="stageGroup" 
    removeEvent="unstageGroup" 
    assetStore="stagedGroups"
    storeGetter="totalSelectedGroups"
  />
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
  }
}
</script>
