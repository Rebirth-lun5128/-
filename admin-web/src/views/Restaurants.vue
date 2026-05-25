<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>商家管理 (夜市摊位)</span>
          <el-select v-model="filterStatus" placeholder="核验状态" clearable style="width:150px" @change="loadData">
            <el-option label="待核验" value="unverified" />
            <el-option label="已核验" value="verified" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </div>
      </template>
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="摊位名称" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="stall_location" label="摊位位置" />
        <el-table-column prop="category" label="分类" width="80" />
        <el-table-column prop="verify_status" label="核验状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.verify_status === 'verified' ? 'success' : row.verify_status === 'rejected' ? 'danger' : 'warning'">
              {{ row.verify_status === 'verified' ? '已核验' : row.verify_status === 'rejected' ? '已拒绝' : '待核验' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verify_method" label="核验方式" width="100" />
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <div v-if="row.verify_status === 'unverified'" style="display:flex;gap:6px;flex-wrap:wrap">
              <el-button size="small" type="success" @click="verify(row.id, 'verified', '现场核验')">通过-现场</el-button>
              <el-button size="small" type="primary" @click="verify(row.id, 'verified', '视频核验')">通过-视频</el-button>
              <el-button size="small" type="danger" @click="verify(row.id, 'rejected', '')">拒绝</el-button>
            </div>
            <el-button v-else size="small" @click="toggleStatus(row.id, row.status === 'open' ? 'closed' : 'open')">
              {{ row.status === 'open' ? '强制关店' : '恢复营业' }}
            </el-button>
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
const filterStatus = ref('unverified')

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/admin/restaurants', {
      params: { page: page.value, page_size: 10, verify_status: filterStatus.value }
    })
    items.value = res.items
    total.value = res.total
  } catch (e) { } finally { loading.value = false }
}

async function verify(id, status, method) {
  try {
    await http.put(`/admin/restaurants/${id}/verify`, null, {
      params: { verify_status: status, verify_method: method, verify_note: method }
    })
    ElMessage.success(status === 'verified' ? '核验通过' : '已拒绝')
    loadData()
  } catch (e) { }
}

async function toggleStatus(id, status) {
  try {
    await http.put(`/admin/restaurants/${id}/toggle-status?status=${status}`)
    ElMessage.success('已更新')
    loadData()
  } catch (e) { }
}

loadData()
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
