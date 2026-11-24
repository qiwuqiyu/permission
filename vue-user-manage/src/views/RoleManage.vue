<!-- 角色管理页：和 MenuManage 套路完全一样（第三遍写，流程已固化）
     RBAC 里的"角色"：给用户打标签分组，为以后"按角色控制能看到哪些菜单"做铺垫 -->
<template>
  <div class="page">
    <!-- 工具栏：新增按钮 -->
    <div class="toolbar">
      <el-button type="primary" @click="openAddModal">新增角色</el-button>
    </div>

    <!-- 表格区：撑满剩余高度 -->
    <div class="table-box">
      <el-table :data="roleList" height="100%" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="description" label="角色描述" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditModal(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 弹窗：新增 / 编辑 共用一个，isEdit 区分 -->
    <el-dialog v-model="modalShow" :title="isEdit ? '编辑角色' : '新增角色'" width="420px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="如：运营" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <!-- type="textarea"：多行文本框，描述类字段常用 -->
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="这个角色能干什么" />
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

const roleList = ref([])
const loading = ref(false)
const submitting = ref(false)
const modalShow = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  name: '',
  description: ''
})

// 前端表单校验：角色名必填（和后端规则一致；后端还查重名，走 catch 兜底提示）
const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

// 获取角色列表
const getList = async () => {
  loading.value = true
  try {
    const res = await request.get('/roles')
    roleList.value = res.data
  } finally {
    loading.value = false
  }
}

// 打开新增弹窗
const openAddModal = () => {
  isEdit.value = false
  form.value = { id: null, name: '', description: '' }
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
        await request.put(`/roles/${form.value.id}`, {
          name: form.value.name,
          description: form.value.description
        })
        ElMessage.success('修改成功')
      } else {
        await request.post('/roles', {
          name: form.value.name,
          description: form.value.description
        })
        ElMessage.success('新增成功')
      }
      modalShow.value = false
      getList() // 刷新表格
    } catch (e) {
      // 后端兜底提示：如 "该角色名已存在"
      ElMessage.error(e.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 删除
const handleDel = (row) => {
  ElMessageBox.confirm(`确定删除角色「${row.name}」吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/roles/${row.id}`)
    ElMessage.success('删除成功')
    getList()
  }).catch(() => {}) // 点取消：什么都不做
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
/* 页面外壳：占满父容器（el-main）高度，纵向 flex 布局（和 UserManage/MenuManage 一致） */
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
