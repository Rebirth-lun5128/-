<template>
  <div class="riders-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">🛵 骑手管理</span>
          <el-select
            v-model="filterStatus" placeholder="审核状态" clearable
            style="width:140px" @change="loadData"
          >
            <el-option label="全部" value="" />
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </div>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="real_name" label="姓名" min-width="100">
          <template #default="{ row }">
            <span class="rider-name">{{ row.real_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="工作状态" width="100" align="center">
          <template #default="{ row }">
            <span class="rider-status-dot" :class="row.status">
              {{ row.status === 'online' ? '在线' : row.status === 'busy' ? '配送中' : '离线' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_orders" label="累计配送" width="100" align="center" sortable />
        <el-table-column label="余额" width="100" align="center">
          <template #default="{ row }">
            <span class="balance">¥{{ row.balance }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="rating" label="评分" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.rating" class="rating">⭐ {{ row.rating }}</span>
            <span v-else class="na">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="audit_status" label="审核状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.audit_status === 'approved' ? 'success' : row.audit_status === 'rejected' ? 'danger' : 'warning'"
              effect="plain" round size="small"
            >
              {{ row.audit_status === 'approved' ? '已通过' : row.audit_status === 'rejected' ? '已拒绝' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <div v-if="row.audit_status === 'pending'" class="action-group">
              <el-button size="small" type="success" @click="audit(row.id, 'approved')" round>
                <el-icon><Check /></el-icon> 通过
              </el-button>
              <el-button size="small" type="danger" @click="audit(row.id, 'rejected')" round>
                <el-icon><Close /></el-icon> 拒绝
              </el-button>
            </div>
            <span v-else class="na">—</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          :total="total" :page-size="10"
          layout="prev, pager, next" background
          @current-change="loadData"
        />
      </div>
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
    const res = await http.get('/admin/riders', {
      params: { page: page.value, page_size: 10, audit_status: filterStatus.value }
    })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function audit(id, status) {
  try {
    await http.put(`/admin/riders/${id}/audit?audit_status=${status}`)
    ElMessage.success('审核完成')
    loadData()
  } catch (e) { /* ignore */ }
}

loadData()
</script>

<style scoped>
.riders-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }

.rider-name { font-weight: 600; color: #333; }

.rider-status-dot {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.rider-status-dot::before {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
}
.rider-status-dot.online  { background: #E8F5E9; color: #00B894; }
.rider-status-dot.online::before  { background: #00B894; }
.rider-status-dot.busy    { background: #FFF3E0; color: #E17055; }
.rider-status-dot.busy::before    { background: #E17055; }
.rider-status-dot.offline { background: #f5f5f5; color: #999; }
.rider-status-dot.offline::before { background: #ccc; }

.balance { font-weight: 700; color: #6C5CE7; }
.rating { font-size: 13px; }
.na { color: #ccc; font-size: 13px; }

.action-group { display: flex; gap: 6px; justify-content: center; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr .el-select { width: 100% !important; }
  .action-group { flex-wrap: wrap; }
  .action-group .el-button { font-size: 11px; padding: 5px 10px; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
