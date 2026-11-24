<!-- 用户管理页：原来 App.vue 里的表格+弹窗，全部换成 Element Plus 组件 -->
<template>
  <!-- 页面外壳：纵向 flex，工具栏占固定高度，表格区 flex:1 撞满剩余空间 -->
  <div class="page">
    <!-- 工具栏：新增按钮 -->
    <div class="toolbar">
      <el-button type="primary" @click="openAddModal">新增用户</el-button>
    </div>

    <!-- 表格区：撞满剩余高度 -->
    <div class="table-box">
      <!-- height="100%"：Element 表格自适应父容器高度，数据多时表头固定、表体内部滚 -->
      <el-table :data="userList" height="100%" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="操作" width="180">
          <!-- template + slot：拿到当前行 row，类比 v-for 里每一项的数据 -->
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditModal(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗：新增 / 编辑 共用一个，isEdit 区分 -->
    <el-dialog v-model="modalShow" :title="isEdit ? '编辑用户' : '新增用户'" width="420px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="70px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="不能是纯数字" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="xxx@xx.com" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modalShow = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const userList = ref([])
const loading = ref(false)
const submitting = ref(false)
const modalShow = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  username: '',
  password: '',
  email: ''
})

// 前端表单校验：用户名必填且不能是纯数字（和后端规则一致，双重保险）
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /\D/, message: '用户名不能是纯数字', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

// 获取用户列表
const getList = async () => {
  loading.value = true
  try {
    const res = await request.get('/users')
    userList.value = res.data
  } finally {
    loading.value = false
  }
}

// 打开新增弹窗
const openAddModal = () => {
  isEdit.value = false
  form.value = { id: null, username: '', password: '', email: '' }
  modalShow.value = true
}

// 打开编辑弹窗
const openEditModal = (row) => {
  isEdit.value = true
  form.value = { ...row } // 浅拷贝：避免直接改表格行数据（取消时不应污染列表）
  modalShow.value = true
}

// 提交（新增 or 修改）
const submit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        // PUT 更新
        await request.put(`/users/${form.value.id}`, {
          username: form.value.username,
          password: form.value.password,
          email: form.value.email
        })
        ElMessage.success('修改成功')
      } else {
        // POST 新增
        await request.post('/users', {
          username: form.value.username,
          password: form.value.password,
          email: form.value.email
        })
        ElMessage.success('新增成功')
      }
      modalShow.value = false
      getList() // 刷新列表
    } catch (e) {
      // 后端校验兜底：比如 400 "用户名不能是纯数字" 从这里弹出来
      ElMessage.error(e.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除
const handleDel = (row) => {
  // 确认弹窗替代原生 window.confirm
  ElMessageBox.confirm(`确定删除用户「${row.username}」吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/users/${row.id}`)
    ElMessage.success('删除成功')
    getList()
  }).catch(() => {}) // 点取消：什么都不做
}

// 页面加载自动拉取列表
onMounted(() => {
  getList()
})
</script>

<style scoped>
/* 页面外壳：占满父容器（el-main）高度，纵向 flex 布局 */
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 工具栏：固定在顶部 */
.toolbar {
  margin-bottom: 16px;
}

/* 表格区：flex:1 撞满剩余高度，溢出隐藏交给表格内部滚动 */
.table-box {
  flex: 1;
  overflow: hidden;
}
</style>
