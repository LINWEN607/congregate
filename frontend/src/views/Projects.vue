<template>
  <StageTable asset="projects" :columns="columns" addEvent="stageProject" removeEvent="unstageProject"/>
</template>

<script>
import StageTable from '@/components/StageTable.vue'

export default {
  name: 'Projects',
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
      ]
    }
  }
}
</script>
