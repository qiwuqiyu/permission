<!-- 菜单管理页：和 UserManage 套路一模一样（表格 + 弹窗表单 + 增删改查） -->
<!-- 特别之处：这里增删改的数据，就是左侧导航栏渲染的数据源 —— 改完刷新，导航就变 -->
<template>
  <div class="page">
    <!-- 工具栏：新增按钮 -->
    <div class="toolbar">
      <el-button type="primary" @click="openAddModal">新增菜单</el-button>
    </div>

    <!-- 表格区：撑满剩余高度 -->
    <div class="table-box">
      <el-table :data="menuList" height="100%" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="菜单名称" />
        <el-table-column prop="path" label="路由地址" />
        <el-table-column prop="sort" label="排序号" width="100" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditModal(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗：新增 / 编辑 共用一个，isEdit 区分 -->
    <el-dialog v-model="modalShow" :title="isEdit ? '编辑菜单' : '新增菜单'" width="420px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="菜单名称" prop="name">
          <el-input v-model="form.name" placeholder="如：订单管理" />
        </el-form-item>
        <el-form-item label="路由地址" prop="path">
          <el-input v-model="form.path" placeholder="如：/orders（必须以 / 开头）" />
        </el-form-item>
        <el-form-item label="排序号" prop="sort">
          <!-- el-input-number：数字输入框，自带加减按钮，值必须是数字 -->
          <el-input-number v-model="form.sort" :min="0" />
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

const menuList = ref([])
const loading = ref(false)
const submitting = ref(false)
const modalShow = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  name: '',
  path: '',
  sort: 0
})

// 前端表单校验：名称必填；路由必填且必须以 / 开头（和后端规则一致，双重保险）
const rules = {
  name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  path: [
    { required: true, message: '请输入路由地址', trigger: 'blur' },
    { pattern: /^\//, message: '路由地址必须以 / 开头', trigger: 'blur' }
  ]
}

// 获取菜单列表
const getList = async () => {
  loading.value = true
  try {
    const res = await request.get('/menus')
    menuList.value = res.data // 后端已按 sort 升序返回
  } finally {
    loading.value = false
  }
}

// 打开新增弹窗
const openAddModal = () => {
  isEdit.value = false
  form.value = { id: null, name: '', path: '', sort: 0 }
  modalShow.value = true
}

// 打开编辑弹窗
const openEditModal = (row) => {
  isEdit.value = true
  form.value = { ...row } // 浅拷贝，避免直接改表格行数据
  modalShow.value = true
}

// 提交（新增 or 修改）
const submit = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        await request.put(`/menus/${form.value.id}`, {
          name: form.value.name,
          path: form.value.path,
          sort: form.value.sort
        })
        ElMessage.success('修改成功')
      } else {
        await request.post('/menus', {
          name: form.value.name,
          path: form.value.path,
          sort: form.value.sort
        })
        ElMessage.success('新增成功')
      }
      modalShow.value = false
      getList() // 刷新表格
    } catch (e) {
      // 后端兜底提示：如 "该路由地址已存在"、"路由地址必须以 / 开头"
      ElMessage.error(e.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除
const handleDel = (row) => {
  ElMessageBox.confirm(`确定删除菜单「${row.name}」吗？删除后左侧导航将不再显示它`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/menus/${row.id}`)
    ElMessage.success('删除成功')
    getList()
  }).catch(() => {}) // 点取消：什么都不做
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
/* 页面外壳：占满父容器（el-main）高度，纵向 flex 布局（和 UserManage 一致） */
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.toolbar {
  margin-bottom: 16px;
}
.table-box {
  flex: 1;
  overflow: hidden;
}
</style>
