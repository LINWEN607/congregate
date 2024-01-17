import Vue from 'vue'
import mitt from 'mitt'
import App from './App.vue'
import router from './router'
import { createPinia, PiniaVuePlugin } from 'pinia'

Vue.config.productionTip = false

const emitter = mitt()
Vue.prototype.$emitter = emitter

Vue.use(PiniaVuePlugin)
const pinia = createPinia()

new Vue({
  router,
  pinia,
  render: h => h(App)
}).$mount('#app')
