<template>
  <div class="settlements-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">💰 结算审批</span>
          <div class="card-hdr-right">
            <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px" @change="loadData">
              <el-option label="全部" value="" />
              <el-option label="审核中" value="pending" />
              <el-option label="已打款" value="paid" />
            </el-select>
            <el-select v-model="filterType" placeholder="类型" clearable style="width:120px;margin-left:8px" @change="loadData">
              <el-option label="全部" value="" />
              <el-option label="骑手" value="rider" />
              <el-option label="商家" value="store" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.target_type === 'rider' ? 'warning' : 'success'" effect="plain" round size="small">
              {{ row.target_type === 'rider' ? '骑手' : '商家' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_name" label="姓名/店铺" min-width="120" />
        <el-table-column prop="target_phone" label="手机号" width="130" />
        <el-table-column label="申请金额" width="110" align="center" sortable="amount">
          <template #default="{ row }">
            <span class="amount">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="平台抽成" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.fee > 0" class="fee">−¥{{ row.fee }}</span>
            <span v-else class="na">—</span>
          </template>
        </el-table-column>
        <el-table-column label="净收入" width="110" align="center">
          <template #default="{ row }">
            <span class="net-amount">¥{{ row.net_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'paid' ? 'success' : 'warning'" effect="plain" round size="small">
              {{ row.status === 'paid' ? '已打款' : '审核中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="170" align="center">
          <template #default="{ row }">
            <span class="time">{{ row.created_at }}</span>
          </template>
        </el-table-column>
        <el-table-column label="打款时间" width="170" align="center">
          <template #default="{ row }">
            <span v-if="row.paid_at" class="time">{{ row.paid_at }}</span>
            <span v-else class="na">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <div v-if="row.status === 'pending'" class="action-group">
              <el-button size="small" type="success" @click="approve(row.id)" round>
                <el-icon><Check /></el-icon> 确认打款
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
          :total="total" :page-size="20"
          layout="prev, pager, next" background
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import http from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStatus = ref('pending')
const filterType = ref('')

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterType.value) params.target_type = filterType.value
    const res = await http.get('/admin/settlements', { params })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function approve(id) {
  try {
    await ElMessageBox.confirm(
      '确认已线下打款给申请人？确认后将从对方余额中扣减相应金额。',
      '确认结算',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
    await http.put(`/admin/settlements/${id}/approve`)
    ElMessage.success('结算已确认，金额已从余额扣减')
    loadData()
  } catch (e) { /* user cancelled or error */ }
}

loadData()
</script>

<style scoped>
.settlements-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.card-hdr-right { display: flex; align-items: center; }

.amount { font-weight: 700; color: #6C5CE7; }
.fee { font-weight: 600; color: #E17055; font-size: 13px; }
.net-amount { font-weight: 700; color: #00B894; }
.time { font-size: 13px; color: #666; }
.na { color: #ccc; font-size: 13px; }

.action-group { display: flex; gap: 6px; justify-content: center; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr-right { flex-wrap: wrap; gap: 6px; }
  .card-hdr-right .el-select { width: 100px !important; }
  .action-group .el-button { font-size: 11px; padding: 5px 10px; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
