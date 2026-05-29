<template>
  <div class="admins-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">👤 管理员管理</span>
          <el-button type="primary" size="small" round @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建管理员
          </el-button>
        </div>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="nickname" label="昵称" min-width="120">
          <template #default="{ row }">
            <span class="admin-name">{{ row.nickname || '未设置' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'super_admin' ? 'danger' : 'warning'" effect="plain" round size="small">
              {{ row.role === 'super_admin' ? '超级管理员' : '分区管理员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="district_id" label="分区ID" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.district_id">{{ row.district_id }}</span>
            <span v-else class="na">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 1"
              @change="(v) => toggleStatus(row, v)"
              active-color="#00B894"
              inline-prompt
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">
            <span class="time">{{ row.created_at?.slice(0, 10) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确定删除此管理员？" @confirm="deleteAdmin(row.id)">
              <template #reference>
                <el-button size="small" text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="total-hint">共 {{ items.length }} 条记录</span>
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑管理员' : '新建管理员'"
      width="480px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="手机号">
          <el-input v-model="form.phone" :disabled="isEditing" placeholder="用于登录" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" :placeholder="isEditing ? '留空则不修改' : '登录密码'" show-password />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="管理员昵称" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio-button value="district_admin">分区管理员</el-radio-button>
            <el-radio-button value="super_admin">超级管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.role === 'district_admin'" label="所属分区">
          <el-select v-model="form.district_id" placeholder="选择分区" style="width:100%">
            <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import http from '../api'

const items = ref([])
const districts = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)

const form = ref({ phone: '', password: '', nickname: '', role: 'district_admin', district_id: null })

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/admin/admins')
    items.value = res
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function loadDistricts() {
  try {
    const res = await http.get('/admin/districts')
    districts.value = res.districts || res || []
  } catch (e) { /* ignore */ }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  form.value = { phone: '', password: '', nickname: '', role: 'district_admin', district_id: null }
  dialogVisible.value = true
}

function openEditDialog(row) {
  isEditing.value = true
  editingId.value = row.id
  form.value = {
    phone: row.phone,
    password: '',
    nickname: row.nickname || '',
    role: row.role,
    district_id: row.district_id || null,
  }
  dialogVisible.value = true
}

async function submitForm() {
  submitting.value = true
  try {
    if (isEditing.value) {
      const body = { nickname: form.value.nickname, district_id: form.value.district_id }
      if (form.value.password) body.password = form.value.password
      await http.put(`/admin/admins/${editingId.value}`, body)
      ElMessage.success('已更新')
    } else {
      await http.post('/admin/admins', null, {
        params: {
          phone: form.value.phone,
          password: form.value.password,
          nickname: form.value.nickname,
          role: form.value.role,
          district_id: form.value.role === 'district_admin' ? form.value.district_id : undefined,
        },
      })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function toggleStatus(row, v) {
  try {
    await http.put(`/admin/admins/${row.id}/toggle-status`)
    row.status = v ? 1 : 0
    ElMessage.success(v ? '已启用' : '已禁用')
  } catch (e) { /* ignore */ }
}

async function deleteAdmin(id) {
  try {
    await http.delete(`/admin/admins/${id}`)
    ElMessage.success('已删除')
    loadData()
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  loadData()
  loadDistricts()
})
</script>

<style scoped>
.admins-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }

.admin-name { font-weight: 600; color: #333; }
.time { color: #999; font-size: 13px; }
.na { color: #ccc; }

.table-footer { display: flex; justify-content: flex-end; margin-top: 20px; }
.total-hint { font-size: 13px; color: #999; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .table-footer { justify-content: center; }
}
</style>
