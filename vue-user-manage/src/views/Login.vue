<!-- 登录页：用 Element Plus 的表单组件搭建 -->
<template>
  <div class="login-box">
    <el-card class="login-card">
      <h2 class="login-title">系统登录</h2>

      <!-- el-form 表单：自带校验、对齐排版，类比手动写 <form> + 校验逻辑 -->
      <!-- :model 绑定数据对象，:rules 校验规则，ref 用来在 JS 里调用方法 -->
      <el-form :model="form" :rules="rules" ref="formRef" label-width="70px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码"
                    @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <!-- :loading 登录中显示转圈并禁用，防止重复提交 -->
          <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  username: '',
  password: ''
})

// 表单校验规则：类比自己写 if (!form.username) alert(...)，el-form 自动处理并红字提示
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 点击登录
const handleLogin = () => {
  // validate() 返回 Promise：校验通过才 resolve，失败会自动标红提示
  formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      // 调后端 POST /login 校验账号密码
      const res = await request.post('/login', form.value)
      // 登录成功：把令牌和用户名存起来（localStorage = 浏览器本地持久化存储）
      // 之后路由守卫靠 localStorage.getItem('token') 判断是否已登录
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('username', res.data.username)
      ElMessage.success('登录成功')
      router.push('/users') // 跳到用户管理页
    } catch (e) {
      // 401 时后端返回 detail: "用户名或密码错误"，取出来弹失败提示
      ElMessage.error(e.response?.data?.detail || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
/* 登录盒：占满全屏、内容水平垂直居中 */
/* height:100% 靠全局高度链（html->body->#app）撑满，比 100vh 更稳，不受手机地址栏影响 */
.login-box {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.login-card {
  width: 380px;
}
.login-title {
  text-align: center;
  margin-bottom: 20px;
}
</style>
