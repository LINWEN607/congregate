<template>
  <div class="home">
    <h2>Staged Data Summary</h2>
    <ul class = "summary-list">
      <li class = "summary-title" v-on:click="showHideProjects()">Total Projects: {{ projectSummary }}</li>
      <li v-show="showStagedProjects"><SummaryTable
            v-bind:headers="['id', 'name', 'path']"
            v-bind:data="stagedProjects"
        /></li>
      <li class = "summary-title" v-on:click="showHideGroups()">Total Groups: {{ groupSummary }}</li>
      <li v-show="showStagedGroups"><SummaryTable
            v-bind:headers="['id', 'name', 'path']"
            v-bind:data="stagedGroups"
        /></li>
      <li class = "summary-title" v-on:click="showHideUsers()">Total Users: {{ userSummary }}</li>
      <li v-show="showStagedUsers"><SummaryTable
            v-bind:headers="['id', 'username', 'email']"
            v-bind:data="stagedUsers"
        /></li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios'
import SummaryTable from '@/components/SummaryTable.vue'

export default {
  name: 'Home',
  components: {
    SummaryTable
  },
  data () {
    return {
      projectSummary: '',
      groupSummary: '',
      userSummary: '',
      stagedProjects: [],
      stagedGroups: [],
      stagedUsers: [],
      showStagedProjects: false,
      showStagedGroups: false,
      showStagedUsers: false
    }
  },
  mounted: function () {
    axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/summary`).then(response => {
      this.projectSummary = response.data['Total Staged Projects']
      this.groupSummary = response.data['Total Staged Groups']
      this.userSummary = response.data['Total Staged Users']
      this.stagedProjects = response.data['Staged Projects']
      this.stagedGroups = response.data['Staged Groups']
      this.stagedUsers = response.data['Staged Users']
    })
  },
  methods: {
    getStagedProjects: function () {
      return this.stagedProjects
    },
    showHideProjects: function () {
      if (this.showStagedProjects === false) {
        this.showStagedProjects = true
      } else {
        this.showStagedProjects = false
      }
    },
    showHideGroups: function () {
      if (this.showStagedGroups === false) {
        this.showStagedGroups = true
      } else {
        this.showStagedGroups = false
      }
    },
    showHideUsers: function () {
      if (this.showStagedUsers === false) {
        this.showStagedUsers = true
      } else {
        this.showStagedUsers = false
      }
    }
  }
}
</script>
<style scoped lang="less">
.summary-title {
  cursor: pointer;
}
.summary-list {
  padding-left: 0;
  li {
    list-style: none;
    text-align: left;
    padding: 1em;
    background: #ccc;
    border-top: 1px solid #000;
  }
}
h2 {
  text-align: left;
}
</style>
