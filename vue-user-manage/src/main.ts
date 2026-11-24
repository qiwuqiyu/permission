import './assets/main.css'

// Element Plus 组件库：全局引入最简单（demo/学习阶段够用）
// 以后项目大了可以改成按需引入，减小打包体积
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 路由：决定当前 URL 显示哪个页面

createApp(App)
  .use(router)        // 挂载路由：类似 app.use(pinia) / app.use(store)
  .use(ElementPlus)  // 挂载组件库：所有 el-xxx 组件全局可用
  .mount('#app')
