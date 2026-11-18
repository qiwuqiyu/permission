<template>
  <div style="padding:30px">
    <h2>用户管理</h2>
    <button @click="openAddModal">新增用户</button>
    <table border="1" cellpadding="8" style="margin-top:20px">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名</th>
          <th>邮箱</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in userList" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.username }}</td>
          <td>{{ item.email }}</td>
          <td>
            <button @click="openEditModal(item)">编辑</button>
            <button @click="handleDel(item.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 弹窗：新增 / 编辑 -->
    <div v-if="modalShow" style="margin-top:20px;border:1px solid #ccc;padding:20px;width:300px">
      <h3>{{ isEdit ? '编辑用户' : '新增用户' }}</h3>
      <div>用户名：<input v-model="form.username"/></div>
      <div style="margin-top:8px">密码：<input v-model="form.password"/></div>
      <div style="margin-top:8px">邮箱：<input v-model="form.email"/></div>
      <div style="margin-top:15px">
        <button @click="submit">提交</button>
        <button @click="modalShow=false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from './utils/request'

const userList = ref([])
const modalShow = ref(false)
const isEdit = ref(false)
const form = ref({
  id: null,
  username: '',
  password: '',
  email: ''
})

// 获取用户列表
const getList = async () => {
  const res = await request.get('/users')
  userList.value = res.data
}

// 打开新增弹窗
const openAddModal = () => {
  isEdit.value = false
  form.value = {username:'',password:'',email:''}
  modalShow.value = true
}

// 打开编辑弹窗
const openEditModal = (row) => {
  isEdit.value = true
  form.value = {...row}
  modalShow.value = true
}

// 提交（新增 or 修改）
const submit = async () => {
  if(isEdit.value){
    // PUT 更新
    await request.put(`/users/${form.value.id}`, form.value)
  }else{
    // 新增前校验：用户名不能是纯数字
    if(/^\d+$/.test(form.value.username)){
      window.alert('用户名不能是纯数字，请重新输入')
      return
    }
    // POST 新增
    await request.post('/users', form.value)
  }
  modalShow.value = false
  getList() // 刷新列表
}

// 删除
const handleDel = async (id) => {
  if(window.confirm('确定删除？')){
    await request.delete(`/users/${id}`)
    getList()
  }
}

// 页面加载自动拉取列表
onMounted(()=>{
  getList()
})
</script>
