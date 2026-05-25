<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>订单监控</span>
          <el-select v-model="filterStatus" placeholder="订单状态" clearable style="width:150px" @change="loadData">
            <el-option label="待接单" value="pending_accept" />
            <el-option label="备餐中" value="preparing" />
            <el-option label="待取餐" value="ready" />
            <el-option label="配送中" value="delivering" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </div>
      </template>
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="restaurant_name" label="餐厅" />
        <el-table-column prop="rider_name" label="骑手" width="100" />
        <el-table-column prop="total_price" label="金额" width="80">
          <template #default="{ row }">¥{{ row.total_price }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
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
import http from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStatus = ref('')

function statusType(s) {
  const map = { pending_accept: 'warning', preparing: '', ready: 'success', delivering: '', completed: 'info', cancelled: 'danger' }
  return map[s] || ''
}

function statusText(s) {
  const map = { pending_pay: '待支付', pending_accept: '待接单', preparing: '备餐中', ready: '待取餐', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await http.get('/admin/orders', { params })
    items.value = res.items
    total.value = res.total
  } catch (e) { } finally { loading.value = false }
}

loadData()
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
