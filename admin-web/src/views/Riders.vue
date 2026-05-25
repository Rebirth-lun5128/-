<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>骑手管理</span>
          <el-select v-model="filterStatus" placeholder="审核状态" clearable style="width:150px" @change="loadData">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </div>
      </template>
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="real_name" label="姓名" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : row.status === 'busy' ? 'warning' : 'info'">
              {{ row.status === 'online' ? '在线' : row.status === 'busy' ? '配送中' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_orders" label="累计配送" width="100" />
        <el-table-column prop="balance" label="余额" width="100">
          <template #default="{ row }">¥{{ row.balance }}</template>
        </el-table-column>
        <el-table-column prop="audit_status" label="审核状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.audit_status === 'approved' ? 'success' : row.audit_status === 'rejected' ? 'danger' : 'warning'">
              {{ row.audit_status === 'approved' ? '已通过' : row.audit_status === 'rejected' ? '已拒绝' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button v-if="row.audit_status === 'pending'" size="small" type="success" @click="audit(row.id, 'approved')">通过</el-button>
            <el-button v-if="row.audit_status === 'pending'" size="small" type="danger" @click="audit(row.id, 'rejected')">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top:20px;justify-content:flex-end"
        v-model:current-page="page"
        :total="total"
        :page-size="10"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStatus = ref('')

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/admin/riders', { params: { page: page.value, page_size: 10, audit_status: filterStatus.value } })
    items.value = res.items
    total.value = res.total
  } catch (e) { } finally { loading.value = false }
}

async function audit(id, status) {
  try {
    await http.put(`/admin/riders/${id}/audit?audit_status=${status}`)
    ElMessage.success('审核完成')
    loadData()
  } catch (e) { }
}

loadData()
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
