<template>
  <div id="app">
    <div id="nav">
      <h1>Congregate</h1>
      <router-link to="/">Home</router-link>
      <!-- <router-link to="/list">List Data</router-link> -->
      <details class="collapsible-nav">
        <summary>Stage Data</summary>
        <ul class = "nested-nav">
          <li><router-link to="/projects">Projects</router-link></li>
          <li><router-link to="/groups">Groups</router-link></li>
          <li><router-link to="/users">Users</router-link></li>
        </ul>
      </details>
      <!-- <router-link to="/migrate">Migrate Data</router-link> -->
      <hr>
      <a :href="flowerUrl" target="_blank">Task Queue</a>
      <router-link to="/settings">Settings</router-link>
    </div>
    <div id = "content">
      <router-view/>
    </div>
    <Toaster/>
  </div>
</template>
<script>
import axios from 'axios'
import { mapStores } from 'pinia'
import Toaster from '@/components/Toaster.vue'
import { useSystemStore } from '@/stores/system'
import { listJobs, migrateJobs, matchFunction } from '@/scripts/job-status'

export default {
  name: 'App',
  components: {
    Toaster
  },
  data() {
    return {
      flowerUrl: import.meta.env.VITE_FLOWER_URL
    }
  },
  computed: {
    ...mapStores(useSystemStore)
  },
  mounted: function() {
    axios.get(`${import.meta.env.VITE_API_ROOT}/api/settings`).then(response => {
      this.systemStore.updateSettings(response.data)
      this.$emitter.emit('settings-updated')
    })
    this.$emitter.on('check-jobs', () => {
      this.getJobsByStatus()
    })
  },
  methods: {
    getJobsByStatus: function() {
      axios.get(`${import.meta.env.VITE_API_ROOT}/api/jobs/status/started/count`).then(response => {
        let match = null
        if ((match = matchFunction(listJobs, response.data))) {
          axios.get(`${import.meta.env.VITE_API_ROOT}/api/jobs/name/${match}`).then(response => {
            this.$emitter.emit('listing-in-progress', response.data[0].id)
          })
        }
        if ((match = matchFunction(migrateJobs, response.data))) {
          axios.get(`${import.meta.env.VITE_API_ROOT}/api/jobs/name/${match}`).then(response => {
            this.$emitter.emit('migration-in-progress', response.data[0].id)
          })
        }
      })
    }
  }
}
</script>

<style lang="less">
#app {
  font-family: Arial, Helvetica, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  height: 100%;
  display: flex;
  flex-wrap: nowrap;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  color: #111;
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: url("assets/congregate_logo.png");
  background-repeat: no-repeat;
  background-attachment: fixed;
  background-position: center;
}

h2 {
  text-align: left;
}

.nested-nav {
  font-weight: bold;
  margin: 0;
  padding-left: 0;
}

.collapsible-nav summary {
  font-weight: bold;
  padding: 0.5em;
}

.nested-nav li {
  padding-left: 1em;
}

.collapsible-nav summary:hover {
  background-color: #663000;
  color: #FF851B;
  text-decoration-line: underline;
  cursor: pointer;
}

.collapsible-nav > summary {
  list-style: none;
}

#nav {
  background-color: #FF851B;
  color :#663000;
  text-align: left;
  flex: 0 0 11em;
  h1 {
    font-size: 1.5em;
    text-indent: 0.5em;
    padding: 0.5em 0;
  }

  h2 {
    font-size: 1em;
    padding: 0;
  }

  hr {
    border: 1px solid #663000;
    width: 90%;
  }

  a {
    font-weight: bold;
    color: #663000;
    display: block;
    text-indent: 0.5em;
    padding: 0.5em 0;

    &.router-link-exact-active {
      background-color: #663000;
      color: #FF851B;
    }

    &:link {
      display: block;
      padding: 0.5em 0;
      text-decoration-line: none;
      width: 100%;
    }

    &:hover {
      background-color: #663000;
      color: #FF851B;
      text-decoration-line: underline;
    }

    p {
      margin-left: 0.5em;
    }
  }

}

#content {
  flex-grow: 12;
  padding: 1em 1em 0 1em;
  color: #111;
}

#content h1 {
  font-size: 1.5em;
  display: inline;
  border: 1px solid #FF851B;
  border-bottom: none;
  padding: 0.05em 0.2em;
}

.table {
  padding: 1em 1em 10em;
}

a {
  font-weight: bold;
  color: #000;
}
a:hover {
  font-weight: bold;
  color: #FF851B;
  text-decoration: none;
}

.loader {
    width: 25px;
    height: 25px;
    border: 3px solid #FF851B;
    border-bottom-color: transparent;
    border-radius: 50%;
    display: inline-block;
    box-sizing: border-box;
    animation: rotation 1s linear infinite;
    }

    @keyframes rotation {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
    } 
</style>
