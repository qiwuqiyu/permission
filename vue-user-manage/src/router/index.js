// 路由配置 —— 类比 vue-router 的 createRouter，但这里是整个前端应用的"页面地图"
import { createRouter, createWebHistory } from 'vue-router'

// 路由表：path -> 页面组件（懒加载 = 打开到这个页面才下载代码，类比 React.lazy）
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')  // 登录页（不需要登录就能访问）
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'), // 外壳页面：左侧菜单 + 顶部栏
    redirect: '/users', // 访问 / 时默认跳到 /users
    children: [
      // 嵌套路由：会在 Layout 里的 <router-view/> 中渲染（类比父组件里的 slot）
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('../views/UserManage.vue'), // 用户管理菜单页
        meta: { title: '用户管理' }
      },
      {
        path: 'menus',
        name: 'MenuManage',
        component: () => import('../views/MenuManage.vue'), // 菜单管理菜单页
        meta: { title: '菜单管理' }
      },
      {
        path: 'roles',
        name: 'RoleManage',
        component: () => import('../views/RoleManage.vue'), // 角色管理菜单页
        meta: { title: '角色管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫 —— 每次路由跳转前都会执行
// 类比 axios 拦截器，但拦截的是"页面跳转"；作用：没登录就强制跳登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token') // 拿登录时存的令牌
  if (to.path === '/login') {
    // 已登录的人再访问登录页 -> 直接放行去首页（可选体验优化）
    token ? next('/') : next()
  } else if (!token) {
    // 没登录访问任何其他页面 -> 强制跳登录
    next('/login')
  } else {
    next() // 正常放行
  }
})

export default router
