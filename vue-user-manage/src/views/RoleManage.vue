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
        <el-table-column prop="name" label="角色名称" width="140" />
        <el-table-column prop="description" label="角色描述" />
        <!-- 新增：这个角色能访问哪些菜单，一眼可见 -->
        <el-table-column label="可访问菜单" min-width="200">
          <template #default="{ row }">
            <!-- 后端 GET /roles 已把 menu_names 一起返回，这里直接渲染，不用额外发请求 -->
            <template v-if="row.menu_names.length">
              <el-tag v-for="n in row.menu_names" :key="n" size="small" class="menu-tag">{{ n }}</el-tag>
            </template>
            <span v-else class="no-menu">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openEditModal(row)">编辑</el-button>
            <!-- 新增入口：单独弹窗勾选菜单，不和「改名/改描述」挤在一个表单里 -->
            <el-button size="small" type="success" plain @click="openAssignModal(row)">分配菜单</el-button>
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

    <!-- 分配菜单弹窗：勾选项来自菜单表，保存写 role_menus 中间表 -->
    <el-dialog v-model="assignShow" title="分配可访问菜单" width="460px">
      <div class="assign-tip">
        勾选「<b>{{ assignRole.name }}</b>」能访问的菜单
      </div>
      <!-- 快捷操作：菜单多了时逐个点麻烦，给两个一键按钮 -->
      <div class="assign-quick">
        <el-button link type="primary" @click="assignMenuIds = menuList.map((m) => m.id)">全选</el-button>
        <el-button link type="info" @click="assignMenuIds = []">清空</el-button>
      </div>
      <!-- el-checkbox-group：一组复选框共用一个数组 v-model，勾上就把 :value 追加进数组 -->
      <el-checkbox-group v-model="assignMenuIds">
        <div v-for="m in menuList" :key="m.id" class="menu-row">
          <el-checkbox :value="m.id">
            {{ m.name }}
            <span class="menu-path">{{ m.path }}</span>
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <!-- 菜单表被清空时的空状态，避免弹窗里一片空白 -->
      <el-empty v-if="!menuList.length" description="菜单表为空，请先到「菜单管理」新增" :image-size="60" />
      <template #footer>
        <el-button @click="assignShow = false">取消</el-button>
        <el-button type="primary" :loading="assignSubmitting" @click="submitAssign">保存</el-button>
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

// 全部菜单（勾选框的数据源）：从 GET /menus 拉，与侧边栏/菜单管理页同一张表
const menuList = ref([])
// 分配菜单弹窗的状态
const assignShow = ref(false)
const assignSubmitting = ref(false)
const assignRole = ref({ id: null, name: '' })   // 当前正在分配的角色
const assignMenuIds = ref([])                    // 勾选中的菜单 id 数组

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

// 获取可勾选的菜单列表
const getMenuList = async () => {
  const res = await request.get('/menus')
  menuList.value = res.data
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

// 打开分配菜单弹窗
const openAssignModal = async (row) => {
  assignRole.value = { id: row.id, name: row.name }
  // 用 slice() 拷一份：el-checkbox-group 会直接改这个数组，
  // 如果直接写 row.menu_ids，点几下就把关掉弹窗前的表格数据也改了
  assignMenuIds.value = [...row.menu_ids]
  assignShow.value = true
  // 每次打开重新拉一次菜单：防止在「菜单管理」页新加了菜单这里却没同步
  await getMenuList()
}

// 保存角色 ↔ 菜单 绑定
const submitAssign = async () => {
  assignSubmitting.value = true
  try {
    await request.put(`/roles/${assignRole.value.id}/menus`, { menu_ids: assignMenuIds.value })
    ElMessage.success('菜单授权已保存')
    assignShow.value = false
    getList() // 刷新表格，重新拉取最新的 menu_names
  } catch (e) {
    // 后端兜底提示：如 "菜单不存在：[3]"（菜单已被别人删掉）
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    assignSubmitting.value = false
  }
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
/* 表格里的菜单标签：多个标签并排，微间距 */
.menu-tag {
  margin-right: 6px;
}
.no-menu {
  color: #bbb;
  font-size: 13px;
}
/* 分配弹窗 */
.assign-tip {
  color: #666;
  font-size: 13px;
  margin-bottom: 4px;
}
.assign-quick {
  margin-bottom: 8px;
}
/* 每个菜单占一行，比横着排成一片更易读 */
.menu-row {
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
}
.menu-path {
  color: #aaa;
  font-size: 12px;
  margin-left: 6px;
}
</style>
