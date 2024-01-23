<template>
    <div id="settings">
      <h2>Settings</h2>
      <div class = "config-section" v-for="(value, key, index) in settings" :key="index">
          <div class = "config-section-header">{{ key }}</div>
          <div class = "section-setting" v-for="(sValue, sKey) in value">
              <b>{{ sKey }}</b>: {{ sValue }}
          </div>
      </div>
    </div>
</template>

<script>
import { mapStores } from 'pinia'
import { useSystemStore } from '@/stores/system' 
export default {
  name: 'Settings',
  computed: {
    ...mapStores(useSystemStore),
    settings() {
      if (JSON.stringify(this.systemStore.settings) !== '{}') {
        return this.systemStore.settings
      }
    }
  }
}
</script>

<style scoped>
#settings {
    width: 50%;
    background-color: #fff;
}
.config-section {
    text-align: left;
    margin-bottom: 1em;
    border: 1px solid #000;
}
.config-section-header {
    font-weight: bold;
    border-bottom: 1px solid #000;
    background-color: #111;
    color: #fff;
}
.section-setting:nth-child(odd) {
    background-color: #ccc;
}

.config-section-header, .section-setting {
  padding: 1%;
}
</style>
