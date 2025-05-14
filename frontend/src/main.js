// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 确保 router 导入正确
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

app.use(createPinia())
app.use(router) // 确保在 use(ElementPlus) 之前或之后都可以，但必须 use
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app') // 确保挂载到了正确的 ID