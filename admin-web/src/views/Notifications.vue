<template>
  <div class="notifications-page">
    <!-- 发送通知 -->
    <el-card shadow="never" class="send-card">
      <template #header>
        <span class="card-hdr-title">📢 发送推送通知</span>
      </template>
      <el-form :model="form" label-width="80px" @submit.prevent>
        <el-form-item label="通知标题">
          <el-input v-model="form.title" placeholder="请输入通知标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="通知内容">
          <el-input
            v-model="form.content" type="textarea" :rows="4"
            placeholder="请输入通知内容" maxlength="500" show-word-limit
          />
        </el-form-item>
        <el-form-item label="目标角色">
          <el-radio-group v-model="form.target_role">
            <el-radio-button value="user">用户</el-radio-button>
            <el-radio-button value="merchant">商家</el-radio-button>
            <el-radio-button value="rider">骑手</el-radio-button>
            <el-radio-button value="all">全部</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="isSuperAdmin" label="目标分区">
          <el-select v-model="form.district_id" placeholder="全平台（不选即全部）" clearable style="width:240px">
            <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="sendNotification" :loading="sending" :disabled="!form.title">
            <el-icon><Promotion /></el-icon> 立即发送
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 已发送记录 -->
    <el-card shadow="never" style="margin-top:20px">
      <template #header>
        <span class="card-hdr-title">📋 发送记录</span>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="title" label="标题" min-width="160">
          <template #default="{ row }">
            <span class="notif-title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="200">
          <template #default="{ row }">
            <span class="notif-content">{{ row.content }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="target_role" label="目标角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round>
              {{ roleLabel(row.target_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="district_id" label="分区ID" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.district_id">{{ row.district_id }}</span>
            <span v-else class="na">全部</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发送时间" width="170" align="center">
          <template #default="{ row }">
            <span class="time">{{ row.created_at?.slice(0, 19) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          :total="total" :page-size="pageSize"
          layout="prev, pager, next" background
          @current-change="loadHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import http from '../api'

const isSuperAdmin = inject('isSuperAdmin', ref(true))
const districts = ref([])

const form = ref({ title: '', content: '', target_role: 'user', district_id: null })
const sending = ref(false)

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

function roleLabel(r) {
  const map = { user: '用户', merchant: '商家', rider: '骑手', all: '全部' }
  return map[r] || r
}

async function sendNotification() {
  if (!form.value.title) return
  sending.value = true
  try {
    await http.post('/admin/notifications/send', {
      title: form.value.title,
      content: form.value.content,
      target_role: form.value.target_role,
      district_id: form.value.district_id,
    })
    ElMessage.success('通知已发送')
    form.value.title = ''
    form.value.content = ''
    page.value = 1
    loadHistory()
  } catch (e) { /* ignore */ } finally { sending.value = false }
}

async function loadHistory() {
  loading.value = true
  try {
    const res = await http.get('/admin/notifications', {
      params: { page: page.value, page_size: pageSize.value }
    })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function loadDistricts() {
  try {
    const res = await http.get('/admin/districts')
    districts.value = res.districts || res || []
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  loadDistricts()
  loadHistory()
})
</script>

<style scoped>
.notifications-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }

.notif-title { font-weight: 600; color: #333; }
.notif-content { color: #666; font-size: 13px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.time { color: #999; font-size: 13px; }
.na { color: #ccc; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

@media (max-width: 767px) {
  .el-form-item { flex-direction: column; align-items: flex-start; }
  .el-form-item :deep(.el-form-item__label) { margin-bottom: 6px; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
