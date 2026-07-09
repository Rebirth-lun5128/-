<template>
  <div class="stores-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">🏪 商家管理（夜市摊位）</span>
          <div class="hdr-controls">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索摊位名称..."
              clearable
              style="width:220px"
              @input="onSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select
              v-model="filterStatus"
              placeholder="核验状态"
              clearable
              style="width:140px"
              @change="loadData"
            >
              <el-option label="全部" value="" />
              <el-option label="待核验" value="unverified" />
              <el-option label="已核验" value="verified" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="摊位名称" min-width="140">
          <template #default="{ row }">
            <span class="store-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="stall_location" label="摊位位置" min-width="110" />
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" round>{{ storeTypeLabel(row.store_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分区" width="130" align="center">
          <template #default="{ row }">
            <el-tag type="" effect="plain" round size="small">{{ row.district_name || '未分配' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="跨区合单" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              v-if="row.combinable_districts && row.combinable_districts.length > 0"
              type="success" effect="plain" round size="small"
            >{{ row.combinable_districts.length }} 个区</el-tag>
            <span v-else class="text-muted">仅本区</span>
          </template>
        </el-table-column>

        <!-- 抽成比例 - 显式可点击 -->
        <el-table-column label="抽成比例" width="150" align="center">
          <template #default="{ row }">
            <div v-if="editRateId !== row.id" class="clickable-cell" @click="startEditRate(row)">
              <el-icon class="click-icon"><EditPen /></el-icon>
              <span class="click-value">{{ (row.commission_rate * 100).toFixed(1) }}%</span>
              <span class="click-hint">点击修改</span>
            </div>
            <div v-else class="inline-edit">
              <el-input-number
                v-model="editRateVal"
                :min="0" :max="100" :step="0.5"
                size="small" controls-position="right"
                style="width:90px"
                ref="rateInputRef"
              />
              <el-button size="small" type="primary" @click="saveRate(row)" round>保存</el-button>
              <el-button size="small" @click="editRateId = null" round>取消</el-button>
            </div>
          </template>
        </el-table-column>

        <!-- 配送附加费 -->
        <el-table-column label="配送附加费" width="150" align="center">
          <template #default="{ row }">
            <div v-if="editSurchargeId !== row.id" class="clickable-cell" @click="startEditSurcharge(row)">
              <el-icon class="click-icon"><EditPen /></el-icon>
              <span class="click-value">¥{{ row.delivery_surcharge || 0 }}</span>
              <span class="click-hint">点击修改</span>
            </div>
            <div v-else class="inline-edit">
              <el-input-number
                v-model="editSurchargeVal"
                :min="0" :max="50" :step="0.5"
                size="small" controls-position="right"
                style="width:90px"
              />
              <el-button size="small" type="primary" @click="saveSurcharge(row)" round>保存</el-button>
              <el-button size="small" @click="editSurchargeId = null" round>取消</el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="verify_status" label="核验状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.verify_status === 'verified' ? 'success' : row.verify_status === 'rejected' ? 'danger' : 'warning'"
              effect="plain" round size="small"
            >
              {{ row.verify_status === 'verified' ? '已核验' : row.verify_status === 'rejected' ? '已拒绝' : '待核验' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <div v-if="row.verify_status === 'unverified'" class="action-group">
              <el-button size="small" type="success" @click="verify(row.id, 'verified', '现场核验')" round>
                <el-icon><Check /></el-icon> 通过-现场
              </el-button>
              <el-button size="small" type="primary" @click="verify(row.id, 'verified', '视频核验')" round>
                <el-icon><VideoCamera /></el-icon> 通过-视频
              </el-button>
              <el-button size="small" type="danger" @click="verify(row.id, 'rejected', '')" round>
                <el-icon><Close /></el-icon> 拒绝
              </el-button>
            </div>
            <template v-else>
              <el-button size="small" type="warning" @click="openEdit(row)" round>
                <el-icon><EditPen /></el-icon>
              </el-button>
              <el-button size="small" type="info" @click="openQR(row)" round>
                <el-icon><Picture /></el-icon> 二维码
              </el-button>
              <el-button
                size="small"
                :type="row.status === 'open' ? 'danger' : 'success'"
                @click="toggleStatus(row.id, row.status === 'open' ? 'closed' : 'open')"
                round
              >
                {{ row.status === 'open' ? '强制关店' : '恢复营业' }}
              </el-button>
              <el-popconfirm title="确定删除该店铺？" @confirm="deleteStore(row.id)">
                <template #reference>
                  <el-button size="small" type="danger" round plain>
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="10"
          layout="prev, pager, next"
          background
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 编辑店铺弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑店铺设置" width="500px" destroy-on-close>
      <el-form label-width="100px" v-if="editRow">
        <el-form-item label="店铺名称">
          <span class="form-static">{{ editRow.name }}</span>
        </el-form-item>
        <el-form-item label="店铺类型">
          <el-select v-model="editForm.store_type" placeholder="选择店铺类型">
            <el-option label="夜市摊位" value="stall" />
            <el-option label="私房菜" value="home_kitchen" />
            <el-option label="平台自营" value="self_operated" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属分区">
          <el-select v-model="editForm.district_id" placeholder="选择分区" clearable>
            <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="可合单分区">
          <el-select
            v-model="editForm.combinable_districts"
            multiple
            placeholder="选择可跨区合单的分区（可选）"
            collapse-tags
            collapse-tags-tooltip
            style="width:100%"
          >
            <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
          <div class="form-hint">留空 = 仅本区合单；勾选后可与所选分区的店铺合并下单</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 二维码弹窗 -->
    <el-dialog v-model="qrDialogVisible" title="店铺二维码" width="420px" destroy-on-close center>
      <div v-if="qrLoading" style="text-align:center;padding:40px">
        <el-icon class="is-loading" size="32"><Loading /></el-icon>
        <p style="margin-top:12px;color:#999">生成中...</p>
      </div>
      <div v-else-if="qrCodeUrl" style="text-align:center">
        <img :src="qrCodeUrl" style="width:260px;height:260px;border:8px solid #fff;box-shadow:0 2px 16px rgba(0,0,0,0.12)" />
        <p style="margin-top:12px;color:#666;font-size:13px">
          {{ qrStoreName }}
        </p>
        <p style="color:#999;font-size:12px;margin-top:4px">
          用户扫码直接进入店铺页面
        </p>
        <el-button type="primary" size="small" round style="margin-top:12px" @click="generateQR(qrStoreId)">
          重新生成
        </el-button>
      </div>
      <div v-else style="text-align:center;padding:40px">
        <p style="color:#999;margin-bottom:16px">尚未生成二维码</p>
        <el-button type="primary" @click="generateQR(qrStoreId)">生成二维码</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStatus = ref('')
const searchKeyword = ref('')
let searchTimer = null

// 抽成比例编辑
const editRateId = ref(null)
const editRateVal = ref(12)
const rateInputRef = ref(null)

async function startEditRate(row) {
  editRateId.value = row.id
  editRateVal.value = (row.commission_rate || 0.12) * 100
  await nextTick()
  // 聚焦到 input
  const el = document.querySelector('.inline-edit .el-input-number input')
  el?.focus()
}

async function saveRate(row) {
  try {
    const rate = editRateVal.value / 100
    await http.put(`/admin/stores/${row.id}/commission-rate`, null, { params: { rate } })
    row.commission_rate = rate
    editRateId.value = null
    ElMessage.success('抽成比例已更新')
  } catch (e) { /* ignore */ }
}

// 配送附加费编辑
const editSurchargeId = ref(null)
const editSurchargeVal = ref(0)

async function startEditSurcharge(row) {
  editSurchargeId.value = row.id
  editSurchargeVal.value = row.delivery_surcharge || 0
  await nextTick()
  const el = document.querySelector('.inline-edit .el-input-number input')
  el?.focus()
}

async function saveSurcharge(row) {
  try {
    await http.put(`/admin/stores/${row.id}/delivery-surcharge`, null, {
      params: { surcharge: editSurchargeVal.value }
    })
    row.delivery_surcharge = editSurchargeVal.value
    editSurchargeId.value = null
    ElMessage.success('配送附加费已更新')
  } catch (e) { /* ignore */ }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadData() }, 300)
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10 }
    if (filterStatus.value) params.verify_status = filterStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await http.get('/admin/stores', { params })
    items.value = res.items
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function verify(id, status, method) {
  try {
    await http.put(`/admin/stores/${id}/verify`, null, {
      params: { verify_status: status, verify_method: method, verify_note: method }
    })
    ElMessage.success(status === 'verified' ? '核验通过' : '已拒绝')
    loadData()
  } catch (e) { /* ignore */ }
}

async function toggleStatus(id, status) {
  try {
    await http.put(`/admin/stores/${id}/toggle-status?status=${status}`)
    ElMessage.success('已更新')
    loadData()
  } catch (e) { /* ignore */ }
}

async function deleteStore(id) {
  try {
    await http.delete(`/admin/stores/${id}`)
    ElMessage.success('已删除')
    loadData()
  } catch (e) { /* ignore */ }
}

// ===== 店铺编辑弹窗 =====
const districts = ref([])
const editDialogVisible = ref(false)
const editRow = ref(null)
const editForm = ref({ district_id: null, combinable_districts: [] })
const saving = ref(false)

async function loadDistricts() {
  try {
    const res = await http.get('/admin/districts')
    districts.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) { /* ignore */ }
}

function storeTypeLabel(type) {
  const map = { stall: '夜市摊位', home_kitchen: '私房菜', self_operated: '平台自营' }
  return map[type] || type || '未知'
}

function openEdit(row) {
  editRow.value = row
  editForm.value = {
    store_type: row.store_type || 'stall',
    district_id: row.district_id || null,
    combinable_districts: row.combinable_districts ? [...row.combinable_districts] : [],
  }
  editDialogVisible.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await http.put(`/admin/stores/${editRow.value.id}`, {
      store_type: editForm.value.store_type,
      district_id: editForm.value.district_id,
      combinable_districts: editForm.value.combinable_districts,
    })
    editRow.value.store_type = editForm.value.store_type
    editRow.value.district_id = editForm.value.district_id
    editRow.value.combinable_districts = editForm.value.combinable_districts
    // refresh district name display
    const d = districts.value.find(d => d.id === editForm.value.district_id)
    if (d) editRow.value.district_name = d.name
    else editRow.value.district_name = ''
    editDialogVisible.value = false
    ElMessage.success('已保存')
  } catch (e) { /* ignore */ } finally { saving.value = false }
}

// ===== 二维码 =====
const qrDialogVisible = ref(false)
const qrStoreId = ref(null)
const qrStoreName = ref('')
const qrCodeUrl = ref('')
const qrLoading = ref(false)

async function openQR(row) {
  qrDialogVisible.value = true
  qrStoreId.value = row.id
  qrStoreName.value = row.name
  qrCodeUrl.value = row.qr_code || ''
  if (!qrCodeUrl.value) {
    await generateQR(row.id)
  }
}

async function generateQR(storeId) {
  qrLoading.value = true
  try {
    const res = await http.post(`/admin/stores/${storeId}/qrcode`)
    qrCodeUrl.value = res.qr_code
    // 更新表格行数据
    const row = items.value.find(r => r.id === storeId)
    if (row) row.qr_code = res.qr_code
    ElMessage.success('二维码已生成')
  } catch { } finally { qrLoading.value = false }
}

loadData()
loadDistricts()
</script>

<style scoped>
.stores-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.hdr-controls { display: flex; gap: 12px; align-items: center; }

.store-name { font-weight: 600; color: #333; }

/* -------- 可点击单元格 -------- */
.clickable-cell {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 20px;
  background: #f5f3ff;
  border: 1.5px dashed #c4b5fd;
  color: #6C5CE7;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
  user-select: none;
}
.clickable-cell:hover {
  background: #ede7ff;
  border-color: #6C5CE7;
  border-style: solid;
  transform: scale(1.04);
  box-shadow: 0 2px 12px rgba(108,92,231,0.18);
}
.click-icon { font-size: 13px; flex-shrink: 0; }
.click-value { letter-spacing: 0.3px; }
.click-hint {
  font-size: 10px; font-weight: 400;
  color: #b4a5e0;
  margin-left: 2px;
}

/* -------- 内联编辑 -------- */
.inline-edit {
  display: flex; gap: 6px; align-items: center; justify-content: center;
}

/* -------- 操作按钮组 -------- */
.action-group { display: flex; gap: 6px; flex-wrap: wrap; }

/* -------- 表脚 -------- */
.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 20px;
}
.total-hint { font-size: 13px; color: #999; }

.form-static { font-weight: 600; color: #333; }
.form-hint { font-size: 12px; color: #999; margin-top: 4px; }
.text-muted { color: #ccc; font-size: 12px; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr-title { font-size: 14px; }
  .hdr-controls { flex-wrap: wrap; width: 100%; }
  .hdr-controls .el-input { width: 100% !important; }
  .hdr-controls .el-select { width: 100% !important; }
  .clickable-cell { padding: 4px 9px; font-size: 12px; border-radius: 16px; }
  .click-hint { display: none; }
  .click-value { font-size: 12px; }
  .inline-edit { flex-wrap: wrap; }
  .action-group { flex-wrap: wrap; }
  .action-group .el-button { font-size: 11px; padding: 5px 10px; }
  .table-footer { flex-direction: column; gap: 12px; align-items: stretch; }
  .el-pagination { justify-content: center; }
}
</style>
