<!-- 外壳页 Layout：登录后的整体页面框架 = 左侧菜单 + 顶部栏 + 内容区 -->
<!-- 内容区放 <router-view/>，点菜单切换子页面（用户管理）在里面渲染 -->
<template>
  <el-container class="layout">
    <!-- 左侧菜单栏 -->
    <el-aside width="200px" class="aside">
      <div class="logo">后台管理系统</div>
      <!-- el-menu 侧边菜单；router 模式：点菜单项自动跳转 index 对应的 path -->
      <!-- v-for 渲染后端返回的菜单列表：在“菜单管理”页增删改，刷新后这里就变 -->
      <el-menu :default-active="$route.path" router background-color="#001529"
               text-color="#c8c8c8" active-text-color="#fff">
        <el-menu-item v-for="m in menus" :key="m.id" :index="m.path">
          {{ m.name }}
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部栏：面包屑标题 + 右侧退出登录 -->
      <el-header class="header">
        <span>{{ $route.meta.title || '' }}</span>
        <div class="header-right">
          <span class="username">{{ username }}</span>
          <el-button link type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <!-- 内容区：子页面（用户管理）在这里渲染，类比父组件里的 <slot/> -->
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
// 侧边栏菜单数据：从后端拉取（以前是硬编码在模板里的，现在改数据库就能改导航）
const menus = ref([])

// 拉取菜单列表（接口返回时已按 sort 升序）
const getMenus = async () => {
  const res = await request.get('/menus')
  menus.value = res.data
}

onMounted(() => {
  getMenus()
})

// 显示当前登录用户名（登录时存的）
const username = computed(() => localStorage.getItem('username') || '')

// 退出登录：清掉本地令牌，回登录页
// 路由守卫发现 token 没了，自然不允许再访问内部页面
const handleLogout = () => {
  ElMessageBox.confirm('确定退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    ElMessage.success('已退出')
    router.push('/login')
  }).catch(() => {}) // 点取消：什么都不做
}
</script>

<style scoped>
.layout {
  height: 100%; /* 靠全局的 html/body/#app 100% 高度链撑满，不用再写 100vh */
}
.aside {
  background: #001529;
}
.logo {
  color: #fff;
  text-align: center;
  line-height: 60px;
  font-weight: bold;
  font-size: 16px;
}
.aside :deep(.el-menu) {
  border-right: none; /* 去掉 Element 默认右侧边线 */
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  font-size: 16px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #666;
  font-size: 14px;
}
</style>
