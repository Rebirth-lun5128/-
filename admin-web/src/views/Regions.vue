<template>
  <div class="regions-page">
    <!-- 分区列表 -->
    <el-card shadow="never" class="region-list-card">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">📍 分区管理</span>
          <el-button type="primary" size="default" @click="showCreate = true" round>
            <el-icon><Plus /></el-icon> 新增分区
          </el-button>
        </div>
      </template>

      <el-table
        :data="regions"
        stripe
        v-loading="loading"
        highlight-current-row
        @row-click="selectDistrict"
      >
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="分区名称" min-width="120">
          <template #default="{ row }">
            <span class="district-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="基础配送费" width="120" align="center">
          <template #default="{ row }">
            <span class="fee-value">¥{{ (row.delivery_fee / 100).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="高峰期配送费" width="130" align="center">
          <template #default="{ row }">
            <span v-if="row.peak_delivery_fee" class="fee-value peak">
              ¥{{ (row.peak_delivery_fee / 100).toFixed(2) }}
            </span>
            <span v-else class="fee-na">—</span>
          </template>
        </el-table-column>
        <el-table-column label="高峰时段" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.peak_start_hour != null" class="peak-time">
              <el-icon><Clock /></el-icon>
              {{ row.peak_start_hour }}:00 — {{ row.peak_end_hour }}:00
            </span>
            <span v-else class="fee-na">—</span>
          </template>
        </el-table-column>
        <el-table-column label="满减规则" min-width="200">
          <template #default="{ row }">
            <div v-if="row.delivery_fee_rules && row.delivery_fee_rules.length > 0" class="rule-tags">
              <el-tag
                v-for="(rule, i) in row.delivery_fee_rules"
                :key="i"
                size="small"
                :type="rule.type === 'free' ? 'success' : 'warning'"
                effect="light"
                round
              >
                {{ rule.desc || (rule.type === 'free' ? `满${rule.threshold}免配送费` : `满${rule.threshold}减${rule.reduce}`) }}
              </el-tag>
            </div>
            <span v-else class="fee-na">暂未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="openEditDialog(row)" round>
              <el-icon><EditPen /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 配送费设置 -->
    <el-card shadow="never" v-if="active" class="setting-card">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">⚙️ 配送费设置 — <b>{{ active.name }}</b></span>
        </div>
      </template>
      <el-form label-width="150px" class="fee-form">
        <el-row :gutter="30">
          <el-col :span="12">
            <el-form-item label="基础配送费 (元)">
              <el-input-number
                v-model="feeForm.base_fee"
                :min="0" :max="100" :step="0.5"
                controls-position="right"
                style="width:180px"
              />
              <span class="form-hint">非高峰时段默认配送费</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="高峰期配送费 (元)">
              <el-input-number
                v-model="feeForm.peak_fee"
                :min="0" :max="100" :step="0.5"
                controls-position="right"
                style="width:180px"
              />
              <span class="form-hint">设为 0 则不启用高峰期</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="30">
          <el-col :span="12">
            <el-form-item label="高峰时段">
              <div class="time-range">
                <el-time-select
                  v-model="feeForm.peak_start"
                  :max-time="feeForm.peak_end || '23:00'"
                  placeholder="开始时间"
                  start="00:00" step="01:00" end="23:00"
                  style="width:130px"
                />
                <span class="time-sep">至</span>
                <el-time-select
                  v-model="feeForm.peak_end"
                  :min-time="feeForm.peak_start || '00:00'"
                  placeholder="结束时间"
                  start="00:00" step="01:00" end="23:00"
                  style="width:130px"
                />
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item>
              <el-button type="primary" @click="saveDeliveryFee" round>
                <el-icon><Check /></el-icon> 保存配送费设置
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 满减规则 -->
    <el-card shadow="never" v-if="active" class="setting-card">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">🏷️ 满减配送费规则 — <b>{{ active.name }}</b></span>
          <el-button type="primary" size="default" @click="addRule" round plain>
            <el-icon><Plus /></el-icon> 添加规则
          </el-button>
        </div>
      </template>
      <el-table :data="ruleList" stripe>
        <el-table-column label="类型" width="160" align="center">
          <template #default="{ row }">
            <el-select v-model="row.type" style="width:140px">
              <el-option label="🆓 满X免配送费" value="free" />
              <el-option label="💰 满X减Y" value="reduce" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="满减门槛 (元)" width="150" align="center">
          <template #default="{ row }">
            <el-input-number
              v-model="row.threshold"
              :min="1" :step="5"
              controls-position="right"
              style="width:120px"
            />
          </template>
        </el-table-column>
        <el-table-column label="减免金额 (元)" width="150" align="center">
          <template #default="{ row }">
            <el-input-number
              v-if="row.type === 'reduce'"
              v-model="row.reduce"
              :min="0" :step="1"
              controls-position="right"
              style="width:120px"
            />
            <el-tag v-else type="success" size="small" effect="plain" round>全额减免</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.desc" placeholder="如: 满20元免配送费" clearable />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ $index }">
            <el-button size="small" type="danger" @click="removeRule($index)" circle plain>
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="ruleList.length > 0" class="save-bar">
        <el-button type="primary" @click="saveRules" round>
          <el-icon><Check /></el-icon> 保存满减规则
        </el-button>
      </div>
      <div v-else class="empty-hint">暂未设置满减规则，点击「添加规则」开始配置</div>
    </el-card>

    <!-- 编辑分区信息 -->
    <el-dialog
      v-model="showEdit"
      title="编辑分区信息"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-width="110px" v-if="editForm">
        <el-form-item label="分区名称">
          <el-input v-model="editForm.name" placeholder="分区名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="覆盖小区">
          <el-input v-model="editForm.coverage" placeholder="用逗号分隔，如: 阳光花园,翠苑新村" />
        </el-form-item>
        <el-form-item label="配送范围 (km)">
          <el-input-number v-model="editForm.delivery_range" :min="1" :max="50" style="width:160px" />
        </el-form-item>
        <el-form-item label="分区公告">
          <el-input v-model="editForm.notice" placeholder="公告内容" maxlength="200" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="editForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false" round>取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="editSaving" round>
          <el-icon><Check /></el-icon> 保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 新增分区 -->
    <el-dialog
      v-model="showCreate"
      title="新增分区"
      width="460px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form label-width="110px">
        <el-form-item label="分区名称">
          <el-input v-model="createForm.name" placeholder="如: 幸福夜市A区" size="large">
            <template #prefix><el-icon><Location /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="基础配送费 (元)">
          <el-input-number
            v-model="createForm.delivery_fee"
            :min="0" :step="0.5"
            controls-position="right"
            size="large"
            style="width:200px"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false" round>取消</el-button>
        <el-button type="primary" @click="createDistrict" round :loading="creating">
          <el-icon><Plus /></el-icon> 确认创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import http from '../api'

const regions = ref([])
const loading = ref(false)
const active = ref(null)

const feeForm = reactive({ base_fee: 0, peak_fee: 0, peak_start: '', peak_end: '' })
const ruleList = ref([])

const showCreate = ref(false)
const creating = ref(false)
const createForm = reactive({ name: '', delivery_fee: 0 })

const showEdit = ref(false)
const editSaving = ref(false)
const editForm = ref(null)
let editingDistrictId = null

function openEditDialog(row) {
  editingDistrictId = row.id
  editForm.value = {
    name: row.name || '',
    coverage: (row.coverage || []).join('、'),
    delivery_range: row.delivery_range || 3,
    notice: row.notice || '',
    status: row.status ?? 1,
  }
  showEdit.value = true
}

async function saveEdit() {
  if (!editForm.value.name.trim()) { ElMessage.warning('请输入分区名称'); return }
  editSaving.value = true
  try {
    const coverage = editForm.value.coverage
      ? JSON.stringify(editForm.value.coverage.split(/[,，、\s]+/).filter(Boolean))
      : '[]'
    await http.put(`/admin/districts/${editingDistrictId}`, {
      name: editForm.value.name.trim(),
      coverage,
      delivery_range: editForm.value.delivery_range,
      notice: editForm.value.notice || '',
      status: editForm.value.status,
    })
    ElMessage.success('分区信息已更新')
    showEdit.value = false
    loadRegions()
  } catch (e) { /* ignore */ } finally { editSaving.value = false }
}

async function loadRegions() {
  loading.value = true
  try {
    regions.value = await http.get('/admin/districts')
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function selectDistrict(row) {
  active.value = row
  feeForm.base_fee = (row.delivery_fee || 0) / 100
  feeForm.peak_fee = (row.peak_delivery_fee || 0) / 100
  feeForm.peak_start = row.peak_start_hour != null
    ? String(row.peak_start_hour).padStart(2, '0') + ':00' : ''
  feeForm.peak_end = row.peak_end_hour != null
    ? String(row.peak_end_hour).padStart(2, '0') + ':00' : ''
  ruleList.value = (row.delivery_fee_rules || []).map(r => ({
    ...r, threshold: Number(r.threshold) || 0, reduce: Number(r.reduce) || 0
  }))
}

async function saveDeliveryFee() {
  if (!active.value) return
  const base_fee = Math.round(feeForm.base_fee * 100)
  const peak_fee = Math.round(feeForm.peak_fee * 100)
  let peak_start = null, peak_end = null
  if (feeForm.peak_start) peak_start = parseInt(feeForm.peak_start.split(':')[0])
  if (feeForm.peak_end) peak_end = parseInt(feeForm.peak_end.split(':')[0])
  try {
    await http.put(`/admin/districts/${active.value.id}/delivery-fee-settings`, null, {
      params: { base_fee, peak_fee, peak_start_hour: peak_start, peak_end_hour: peak_end }
    })
    ElMessage.success('配送费设置已保存')
    loadRegions()
  } catch (e) { /* ignore */ }
}

function addRule() {
  ruleList.value.push({ type: 'free', threshold: 20, reduce: 0, desc: '' })
}

function removeRule(index) {
  ruleList.value.splice(index, 1)
}

async function saveRules() {
  if (!active.value) return
  const rules = ruleList.value
    .map(r => ({
      type: r.type,
      threshold: Number(r.threshold),
      reduce: r.type === 'reduce' ? Number(r.reduce) : 0,
      desc: r.desc || (r.type === 'free'
        ? `满${r.threshold}元免配送费`
        : `满${r.threshold}元减${r.reduce}元配送费`)
    }))
    .sort((a, b) => b.threshold - a.threshold)
  try {
    await http.put(`/admin/districts/${active.value.id}/delivery-rules`, rules)
    ElMessage.success('满减规则已保存')
    loadRegions()
  } catch (e) { /* ignore */ }
}

async function createDistrict() {
  if (!createForm.name) { ElMessage.warning('请输入分区名称'); return }
  creating.value = true
  try {
    const feeFen = Math.round(createForm.delivery_fee * 100)
    await http.post('/admin/districts', null, {
      params: { name: createForm.name, delivery_fee: feeFen }
    })
    ElMessage.success('分区已创建')
    showCreate.value = false
    createForm.name = ''
    createForm.delivery_fee = 0
    loadRegions()
  } catch (e) { /* ignore */ } finally { creating.value = false }
}

loadRegions()
</script>

<style scoped>
.regions-page {
  display: flex; flex-direction: column; gap: 22px;
  animation: fadeIn 0.35s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

/* ====== 卡片头部 ====== */
.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.card-hdr-title b { color: var(--app-primary, #6C5CE7); }

/* ====== 分区名称 ====== */
.district-name { font-weight: 600; color: #333; }

/* ====== 配送费 ====== */
.fee-value { font-weight: 700; color: #333; font-size: 14px; }
.fee-value.peak { color: #E17055; }
.fee-na { color: #ccc; font-size: 13px; }
.peak-time { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: #555; }
.peak-time .el-icon { color: #74B9FF; }

/* ====== 满减规则标签 ====== */
.rule-tags { display: flex; flex-wrap: wrap; gap: 4px; }

/* ====== 设置卡片 ====== */
.setting-card { transition: box-shadow 0.3s; }

/* ====== 表单 ====== */
.fee-form { padding: 4px 0; }
.form-hint { margin-left: 12px; font-size: 12px; color: #bbb; }
.time-range { display: flex; align-items: center; gap: 10px; }
.time-sep { color: #999; font-size: 13px; }

/* ====== 保存栏 ====== */
.save-bar { margin-top: 18px; text-align: right; }
.empty-hint { text-align: center; padding: 40px 0; color: #ccc; font-size: 14px; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .card-hdr-title { font-size: 14px; }
  .rule-tags { gap: 2px; }
  .fee-form .el-row { flex-direction: column; }
  .fee-form .el-col { width: 100% !important; margin-bottom: 12px; }
  .time-range { flex-wrap: wrap; }
  .form-hint { display: block; margin: 4px 0 0 0; }
}
</style>
