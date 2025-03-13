import { createApp } from 'vue'
import mitt from 'mitt'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'


const app = createApp(App)
const emitter = mitt()
const pinia = createPinia()

app.config.globalProperties.emitter = emitter
app.use(router)
app.use(pinia)
app.mount("#app")

