import Vue from 'vue'
import mitt from 'mitt'
import App from './App.vue'
import router from './router'

Vue.config.productionTip = false

const emitter = mitt()
Vue.prototype.$emitter = emitter

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
