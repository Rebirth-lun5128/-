<template>
  <div class="orders-page">
    <el-tabs v-model="activeTab" @tab-change="onTabChange" class="orders-tabs">
      <el-tab-pane label="订单列表" name="orders">
        <el-card shadow="never">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">📋 订单监控</span>
              <div class="hdr-controls">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索订单号..."
                  clearable
                  style="width:220px"
                  @input="onSearch"
                >
                  <template #prefix><el-icon><Search /></el-icon></template>
                </el-input>
                <el-select
                  v-model="filterStatus" placeholder="订单状态" clearable
                  style="width:140px" @change="loadOrders"
                >
                  <el-option label="全部" value="" />
                  <el-option label="待支付" value="pending_pay" />
                  <el-option label="处理中" value="pending" />
                  <el-option label="配送中" value="delivering" />
                  <el-option label="已完成" value="completed" />
                  <el-option label="已取消" value="cancelled" />
                  <el-option label="部分完成" value="partial" />
                </el-select>
              </div>
            </div>
          </template>

          <el-table :data="items" stripe v-loading="loading" @row-click="openDetail">
            <el-table-column prop="order_no" label="订单号" width="195" />
            <el-table-column label="店铺" min-width="170">
              <template #default="{ row }">
                <span v-if="row.store_count > 1" class="multi-store">
                  <el-icon><Connection /></el-icon>
                  {{ row.store_count }} 店合单
                </span>
                <span v-else>{{ row.store_names?.[0] || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="rider_name" label="骑手" width="100">
              <template #default="{ row }">
                <span v-if="row.rider_name" class="rider-name">{{ row.rider_name }}</span>
                <span v-else class="na">未分配</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="100" align="center">
              <template #default="{ row }">
                <span class="amount">¥{{ row.total_price }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="110" align="center">
              <template #default="{ row }">
                <span class="status-badge" :class="row.status">{{ statusText(row.status) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="80" fixed="right" align="center">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click.stop="openDetail(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span class="total-hint">共 {{ total }} 条记录</span>
            <el-pagination
              v-model:current-page="page"
              :total="total" :page-size="10"
              layout="prev, pager, next" background
              @current-change="loadOrders"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="修改审核" name="modifications">
        <el-card shadow="never">
          <template #header>
            <div class="card-hdr">
              <span class="card-hdr-title">🔍 订单修改审核</span>
              <el-select
                v-model="modStatus" placeholder="审核状态" clearable
                style="width:140px" @change="loadModifications"
              >
                <el-option label="待审核" value="pending_review" />
                <el-option label="已同意" value="approved" />
                <el-option label="已拒绝" value="rejected" />
              </el-select>
            </div>
          </template>

          <el-table :data="modifications" stripe v-loading="modLoading">
            <el-table-column prop="order_no" label="订单号" width="190" />
            <el-table-column prop="store_name" label="店铺" min-width="120" />
            <el-table-column prop="user_name" label="用户" width="100" />
            <el-table-column label="类型" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="modTypeTag(row.type)" effect="plain" round>
                  {{ modTypeText(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" min-width="140" show-overflow-tooltip />
            <el-table-column label="金额" width="90" align="center">
              <template #default="{ row }">
                <span class="amount">¥{{ row.items_total || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="审核状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'"
                  effect="plain" round
                >
                  {{ row.status === 'approved' ? '已同意' : row.status === 'rejected' ? '已拒绝' : '待审核' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="申请时间" width="170" />
            <el-table-column label="操作" width="170" fixed="right" align="center">
              <template #default="{ row }">
                <template v-if="row.status === 'pending_review'">
                  <el-button size="small" type="success" @click="approveMod(row.id)" round>
                    同意
                  </el-button>
                  <el-button size="small" type="danger" @click="rejectMod(row.id)" round>
                    拒绝
                  </el-button>
                </template>
                <span v-else class="na">{{ row.review_comment || '已处理' }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span class="total-hint">共 {{ modTotal }} 条记录</span>
            <el-pagination
              v-model:current-page="modPage"
              :total="modTotal" :page-size="10"
              layout="prev, pager, next" background
              @current-change="loadModifications"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 订单详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="订单详情"
      size="540px"
      :close-on-click-modal="true"
      destroy-on-close
    >
      <template v-if="detail">
        <div class="drawer-body">
          <!-- 订单头部 -->
          <div class="detail-hero">
            <div class="detail-hero-top">
              <span class="detail-no">{{ detail.order_no }}</span>
              <span class="status-badge" :class="detail.status">{{ statusText(detail.status) }}</span>
            </div>
            <div class="detail-hero-price">¥{{ detail.total_price }}</div>
          </div>

          <!-- 基本信息 -->
          <div class="detail-block">
            <div class="detail-block-title">基本信息</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">商品合计</span>
                <span class="info-val">¥{{ detail.items_total }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">配送费</span>
                <span class="info-val">¥{{ detail.delivery_fee }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">骑手</span>
                <span class="info-val">{{ detail.rider_name || '未分配' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">骑手电话</span>
                <span class="info-val">{{ detail.rider_phone || '—' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间</span>
                <span class="info-val">{{ detail.created_at }}</span>
              </div>
            </div>
          </div>

          <!-- 收货地址 -->
          <div v-if="detail.address_snapshot?.detail" class="detail-block">
            <div class="detail-block-title">收货地址</div>
            <div class="address-card">
              <div class="addr-contact">
                <span class="addr-name">{{ detail.address_snapshot.contact_name }}</span>
                <span class="addr-phone">{{ detail.address_snapshot.contact_phone }}</span>
              </div>
              <div class="addr-detail">{{ detail.address_snapshot.detail }}</div>
            </div>
          </div>

          <!-- 用户备注 -->
          <div v-if="detail.remark" class="detail-block">
            <div class="detail-block-title">用户备注</div>
            <div class="remark-box">{{ detail.remark }}</div>
          </div>

          <!-- 子订单 -->
          <div v-for="(sub, si) in detail.sub_orders" :key="sub.id" class="detail-block">
            <div class="sub-head">
              <div class="sub-head-left">
                <span class="sub-index">#{{ si + 1 }}</span>
                <span class="sub-store">{{ sub.store_name }}</span>
                <span class="status-badge small" :class="sub.status">{{ statusText(sub.status) }}</span>
              </div>
              <el-tag size="small" type="info" effect="plain" round>
                抽成 {{ (sub.commission_rate * 100).toFixed(0) }}%
              </el-tag>
            </div>

            <table class="item-table">
              <thead>
                <tr><th>商品</th><th style="width:60px">单价</th><th style="width:40px">数量</th><th style="width:60px">小计</th></tr>
              </thead>
              <tbody>
                <tr v-for="it in sub.items" :key="it.id">
                  <td>{{ it.name }}</td>
                  <td class="num">¥{{ it.price }}</td>
                  <td class="num">x{{ it.quantity }}</td>
                  <td class="num bold">¥{{ (it.price * it.quantity).toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="sub-total">子单合计: <b>¥{{ sub.items_total }}</b></div>

            <!-- 时间线 -->
            <div v-if="sub.timeline?.length" class="timeline-box">
              <div v-for="t in sub.timeline" :key="t.created_at" class="tl-item">
                <div class="tl-dot"></div>
                <div class="tl-content">
                  <span class="tl-desc">{{ t.description }}</span>
                  <span class="tl-time">{{ t.created_at }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 操作 -->
          <div class="detail-actions">
            <el-popconfirm title="确定强制取消此订单？" @confirm="forceCancel(detail.id)">
              <template #reference>
                <el-button
                  type="danger" round
                  :disabled="detail.status === 'completed' || detail.status === 'cancelled'"
                >
                  强制取消订单
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </template>
      <div v-else class="drawer-loading">加载中...</div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api'

const activeTab = ref('orders')

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStatus = ref('')
const searchKeyword = ref('')
let searchTimer = null

const modifications = ref([])
const modTotal = ref(0)
const modPage = ref(1)
const modLoading = ref(false)
const modStatus = ref('pending_review')

const drawerVisible = ref(false)
const detail = ref(null)

function statusText(s) {
  const map = {
    pending_pay: '待支付', pending: '处理中',
    delivering: '配送中', completed: '已完成', cancelled: '已取消',
    partial: '部分完成', pending_accept: '待接单', preparing: '备餐中',
    ready: '待取餐',
  }
  return map[s] || s
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadOrders() }, 300)
}

async function loadOrders() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    if (filterStatus.value) params.status = filterStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await http.get('/admin/orders', { params })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function openDetail(row) {
  drawerVisible.value = true
  detail.value = null
  try {
    detail.value = await http.get(`/admin/orders/${row.id}/detail`)
  } catch (e) { drawerVisible.value = false }
}

async function forceCancel(id) {
  try {
    await http.put(`/admin/orders/${id}/force-cancel?reason=平台介入取消`)
    ElMessage.success('订单已强制取消')
    drawerVisible.value = false
    loadOrders()
  } catch (e) { /* ignore */ }
}

function modTypeText(t) {
  const m = { cancel: '退单', address_change: '改地址', refund: '退款', other: '其他' }
  return m[t] || t
}
function modTypeTag(t) {
  const m = { cancel: 'danger', address_change: 'info', refund: 'warning', other: '' }
  return m[t] || ''
}

async function loadModifications() {
  modLoading.value = true
  try {
    const params = { page: modPage.value, page_size: 10 }
    if (modStatus.value) params.status = modStatus.value
    const res = await http.get('/admin/orders/modifications', { params })
    modifications.value = res.items
    modTotal.value = res.total
  } catch (e) { /* ignore */ } finally { modLoading.value = false }
}

async function approveMod(id) {
  try {
    await http.put(`/admin/orders/modifications/${id}/approve?comment=平台审核通过`)
    ElMessage.success('已同意')
    loadModifications()
  } catch (e) { /* ignore */ }
}

async function rejectMod(id) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝申请', {
      confirmButtonText: '确认', cancelButtonText: '取消',
      inputPlaceholder: '拒绝原因（选填）',
    })
    await http.put(`/admin/orders/modifications/${id}/reject?comment=${encodeURIComponent(value || '平台审核不通过')}`)
    ElMessage.success('已拒绝')
    loadModifications()
  } catch (e) { /* user cancelled */ }
}

function onTabChange(tab) {
  if (tab === 'modifications' && modifications.value.length === 0) loadModifications()
}

loadOrders()
</script>

<style scoped>
.orders-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.hdr-controls { display: flex; gap: 12px; align-items: center; }

/* -------- 状态标签 -------- */
.status-badge {
  display: inline-block;
  padding: 3px 14px;
  border-radius: 20px;
  font-size: 12px; font-weight: 600;
  letter-spacing: 0.3px;
}
.status-badge.small { padding: 1px 10px; font-size: 11px; }
.status-badge.pending_pay     { background: #FFF3E0; color: #E17055; }
.status-badge.pending,
.status-badge.pending_accept  { background: #FFF8E1; color: #f39c12; }
.status-badge.preparing       { background: #E3F2FD; color: #0984e3; }
.status-badge.ready           { background: #E8F5E9; color: #00B894; }
.status-badge.delivering      { background: #EDE7F6; color: #6C5CE7; }
.status-badge.completed       { background: #E8F5E9; color: #00B894; }
.status-badge.cancelled       { background: #FFEBEE; color: #d63031; }
.status-badge.partial         { background: #FFF8E1; color: #f39c12; }

.multi-store { display: inline-flex; align-items: center; gap: 4px; color: #6C5CE7; font-weight: 600; }
.rider-name { font-weight: 500; }
.amount { font-weight: 700; color: #333; }
.na { color: #ccc; font-size: 13px; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

/* -------- 订单详情抽屉 -------- */
.drawer-body { padding: 0 4px; }
.detail-hero {
  background: linear-gradient(135deg, #f8f7ff, #ede7ff);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  text-align: center;
}
.detail-hero-top {
  display: flex; justify-content: center; align-items: center; gap: 12px;
  margin-bottom: 10px;
}
.detail-no { font-size: 16px; font-weight: 700; color: #333; letter-spacing: 0.5px; }
.detail-hero-price { font-size: 32px; font-weight: 800; color: #6C5CE7; }

.detail-block {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}
.detail-block:last-of-type { border-bottom: none; }
.detail-block-title {
  font-size: 14px; font-weight: 700; color: #333;
  margin-bottom: 14px;
  display: flex; align-items: center; gap: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.info-item {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 14px;
  background: #f8f9fc;
  border-radius: 10px;
}
.info-label { font-size: 12px; color: #999; }
.info-val { font-size: 14px; font-weight: 600; color: #333; }

.address-card {
  background: #f8f9fc;
  border-radius: 12px;
  padding: 16px;
}
.addr-contact { display: flex; gap: 14px; margin-bottom: 6px; }
.addr-name { font-weight: 700; color: #333; }
.addr-phone { color: #666; }
.addr-detail { color: #999; font-size: 13px; }
.remark-box {
  background: #fff8e1; border-left: 4px solid #f39c12;
  padding: 12px 16px; border-radius: 6px; color: #555; font-size: 14px;
}

.sub-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.sub-head-left { display: flex; align-items: center; gap: 10px; }
.sub-index { color: #ccc; font-size: 12px; }
.sub-store { font-weight: 700; color: #333; font-size: 15px; }

.item-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.item-table th, .item-table td {
  padding: 8px 10px;
  text-align: left;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}
.item-table th { color: #999; font-weight: 500; font-size: 12px; }
.item-table td.num { text-align: center; }
.item-table td.bold { font-weight: 600; color: #333; }

.sub-total { text-align: right; font-size: 13px; color: #666; margin-top: 8px; }
.sub-total b { font-size: 15px; color: #333; }

.timeline-box { margin-top: 14px; padding-left: 6px; }
.tl-item { display: flex; gap: 12px; margin-bottom: 10px; }
.tl-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #6C5CE7;
  margin-top: 6px;
  flex-shrink: 0;
}
.tl-content { display: flex; flex-direction: column; gap: 1px; }
.tl-desc { font-size: 13px; color: #555; }
.tl-time { font-size: 11px; color: #bbb; }

.detail-actions { padding-top: 16px; text-align: center; border-top: 1px solid #eee; }
.drawer-loading { text-align: center; padding: 80px 0; color: #ccc; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr-title { font-size: 14px; }
  .hdr-controls { flex-wrap: wrap; width: 100%; }
  .hdr-controls .el-input { width: 100% !important; }
  .hdr-controls .el-select { width: 100% !important; }
  .detail-hero { padding: 18px; }
  .detail-hero-price { font-size: 26px; }
  .detail-no { font-size: 14px; }
  .info-grid { grid-template-columns: 1fr; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
