<template>
  <div class="customers-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">👤 客户列表</span>
          <div class="card-hdr-right">
            <el-input
              v-model="keyword" placeholder="搜索昵称/手机号" clearable
              style="width:220px" @input="onSearch" @clear="loadData"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select
              v-if="isSuperAdmin"
              v-model="filterDistrictId" placeholder="按分区筛选" clearable
              style="width:160px;margin-left:10px" @change="loadData"
            >
              <el-option label="全部分区" :value="null" />
              <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="头像" width="70" align="center">
          <template #default="{ row }">
            <el-avatar :src="row.avatar" :size="36">{{ row.nickname?.charAt(0) }}</el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" min-width="120">
          <template #default="{ row }">
            <span class="cust-name">{{ row.nickname || '未设置' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="district_id" label="分区ID" width="80" align="center" />
        <el-table-column prop="created_at" label="注册时间" width="170" align="center">
          <template #default="{ row }">
            <span class="time">{{ row.created_at?.slice(0, 10) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          :total="total" :page-size="pageSize"
          layout="prev, pager, next" background
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import http from '../api'

const isSuperAdmin = inject('isSuperAdmin', ref(true))
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const keyword = ref('')
const filterDistrictId = ref(null)
const districts = ref([])
let searchTimer = null

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value, keyword: keyword.value }
    if (filterDistrictId.value) params.district_id = filterDistrictId.value
    const res = await http.get('/admin/customers', { params })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 300)
}

async function loadDistricts() {
  try {
    const res = await http.get('/admin/districts')
    districts.value = res.districts || res || []
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  loadDistricts()
  loadData()
})
</script>

<style scoped>
.customers-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.card-hdr-right { display: flex; align-items: center; }

.cust-name { font-weight: 600; color: #333; }
.time { color: #999; font-size: 13px; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr-right { width: 100%; flex-wrap: wrap; gap: 8px; }
  .card-hdr-right .el-input,
  .card-hdr-right .el-select { width: 100% !important; margin-left: 0 !important; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
