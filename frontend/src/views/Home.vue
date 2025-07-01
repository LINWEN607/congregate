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
    <h2>Actions</h2>
    <ListCard/>
    <ActionCard title="Stage Data">
      Select different pieces of data to migrate to the destination
      <ul id="stage-list">
        <li><router-link to="/projects">Projects</router-link></li>
        <li><router-link to="/groups">Groups</router-link></li>
        <li><router-link to="/users">Users</router-link></li>
      </ul>
    </ActionCard>
    <MigrateCard/>
    <DryRun/>
  </div>
</template>

<script>
import axios from 'axios'
import SummaryTable from '@/components/SummaryTable.vue'
import ActionCard from '@/components/ActionCard.vue'
import ListCard from '@/components/ListCard.vue'
import MigrateCard from '@/components/MigrateCard.vue'
import DryRun from '@/components/DryRun.vue'

export default {
  name: 'Home',
  components: {
    SummaryTable,
    ActionCard,
    ListCard,
    MigrateCard,
    DryRun
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
    this.getSummary()
    this.emitter.on('update-stage', () => {
      this.getSummary()
    })
    this.emitter.emit('check-jobs')
    this.emitter.on('stream-list-stats', (counts) => {
      this.projectSummary = this.stagedProjects.length + "/" + counts.projects
      this.groupSummary = this.stagedGroups.length + "/" + counts.groups
      this.userSummary = this.stagedUsers.length + "/" + counts.users
    })
  },
  beforeUnmount: function () {
    this.emitter.off('update-stage')
    this.emitter.off('stream-list-stats')
  },
  methods: {
    getSummary: function() {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/data/summary`).then(response => {
        this.projectSummary = response.data['Total Staged Projects']
        this.groupSummary = response.data['Total Staged Groups']
        this.userSummary = response.data['Total Staged Users']
        this.stagedProjects = response.data['Staged Projects']
        this.stagedGroups = response.data['Staged Groups']
        this.stagedUsers = response.data['Staged Users']
      })
    },
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
<style scoped>
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
    border-left: 1px solid #000;
    border-right: 1px solid #000;
  }
  li:last-child {
    border-bottom: 1px solid #000;
  }
}

#actions-list {
  text-align: left;
}

#stage-list {
  list-style-type: none;
  margin: 0;
  padding-left: 0;
}

</style>
