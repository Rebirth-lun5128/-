<template>
  <div class="commission-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">💰 佣金阶梯设置</span>
          <span class="text-muted text-sm">仅超级管理员可配置</span>
        </div>
      </template>

      <!-- 平台佣金阶梯 -->
      <h3 class="section-label">平台佣金阶梯</h3>
      <p class="section-hint">按店铺月累计销售额分档，未配置则使用店铺默认抽成比例</p>
      <el-table :data="platformTiers" stripe size="small" style="margin-bottom:16px">
        <el-table-column label="月销下限 (¥)" width="140" align="center">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.min" :min="0" :step="100" size="small" controls-position="right" style="width:120px" />
          </template>
        </el-table-column>
        <el-table-column label="月销上限 (¥)" width="160" align="center">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.max" :min="0" :step="500" size="small" controls-position="right" style="width:140px" placeholder="-1=无上限" />
            <el-tooltip v-if="row.max === -1 || row.max === '' || row.max === null" content="无上限" placement="top">
              <span style="color:#999;font-size:12px;margin-left:4px">∞</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="抽成比例 (%)" width="140" align="center">
          <template #default="{ row }">
            <el-input-number v-model="row.rate" :min="0" :max="50" :step="0.5" size="small" controls-position="right" style="width:100px" />
          </template>
        </el-table-column>
        <el-table-column label="说明" min-width="180">
          <template #default="{ row, $index }">
            <span v-if="row.max === -1 || !row.max" style="color:#666">
              月销 ≥ ¥{{ row.min || 0 }} — 抽成 {{ (row.rate || 0) * 100 }}%
            </span>
            <span v-else style="color:#666">
              ¥{{ row.min || 0 }} ≤ 月销 ＜ ¥{{ row.max }} — 抽成 {{ (row.rate || 0) * 100 }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ $index }">
            <el-button size="small" type="danger" circle @click="removePlatformTier($index)">✕</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" type="primary" plain @click="addPlatformTier">+ 添加阶梯</el-button>
      <el-button size="small" type="primary" @click="savePlatform" :loading="savingPlatform" style="margin-left:8px">保存平台阶梯</el-button>

      <el-divider />

      <!-- 分区管理佣金阶梯 -->
      <h3 class="section-label">分区管理佣金阶梯</h3>
      <p class="section-hint">分区管理员从辖区店铺销售额中获得的提成</p>
      <el-table :data="districtTiers" stripe size="small" style="margin-bottom:16px">
        <el-table-column label="月销下限 (¥)" width="140" align="center">
          <template #default="{ row }">
            <el-input-number v-model="row.min" :min="0" :step="100" size="small" controls-position="right" style="width:120px" />
          </template>
        </el-table-column>
        <el-table-column label="月销上限 (¥)" width="160" align="center">
          <template #default="{ row }">
            <el-input-number v-model="row.max" :min="0" :step="500" size="small" controls-position="right" style="width:140px" />
            <el-tooltip v-if="row.max === -1 || !row.max" content="无上限" placement="top">
              <span style="color:#999;font-size:12px;margin-left:4px">∞</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="提成比例 (%)" width="140" align="center">
          <template #default="{ row }">
            <el-input-number v-model="row.rate" :min="0" :max="20" :step="0.5" size="small" controls-position="right" style="width:100px" />
          </template>
        </el-table-column>
        <el-table-column label="说明" min-width="180">
          <template #default="{ row }">
            <span v-if="row.max === -1 || !row.max" style="color:#666">
              月销 ≥ ¥{{ row.min || 0 }} — 提成 {{ (row.rate || 0) * 100 }}%
            </span>
            <span v-else style="color:#666">
              ¥{{ row.min || 0 }} ≤ 月销 ＜ ¥{{ row.max }} — 提成 {{ (row.rate || 0) * 100 }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ $index }">
            <el-button size="small" type="danger" circle @click="removeDistrictTier($index)">✕</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" type="primary" plain @click="addDistrictTier">+ 添加阶梯</el-button>
      <el-button size="small" type="primary" @click="saveDistrict" :loading="savingDistrict" style="margin-left:8px">保存分区阶梯</el-button>

      <!-- 快捷预览 -->
      <el-divider />
      <h3 class="section-label">🔍 费率预览</h3>
      <div class="flex items-center" style="gap:12px">
        <span class="text-sm text-gray">输入月销售额:</span>
        <el-input-number v-model="previewSales" :min="0" :step="500" size="small" style="width:150px" />
        <el-button size="small" @click="calcPreview">计算</el-button>
        <span v-if="previewRate !== null" class="text-sm" style="margin-left:12px">
          平台抽成 <span class="font-bold text-primary">{{ (previewRate * 100).toFixed(1) }}%</span> = ¥{{ (previewSales * previewRate).toFixed(2) }}
          <span v-if="previewDistrictRate > 0">
            ＋ 分区提成 <span class="font-bold" style="color:#E65100">{{ (previewDistrictRate * 100).toFixed(1) }}%</span> = ¥{{ (previewSales * previewDistrictRate).toFixed(2) }}
          </span>
          ＝ 商家到手 <span class="font-bold text-success">¥{{ (previewSales * (1 - previewRate - previewDistrictRate)).toFixed(2) }}</span>
        </span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const platformTiers = ref([])
const districtTiers = ref([])
const savingPlatform = ref(false)
const savingDistrict = ref(false)
const previewSales = ref(5000)
const previewRate = ref(null)
const previewDistrictRate = ref(0)

onMounted(loadTiers)

async function loadTiers() {
  try {
    const res = await http.get('/admin/commission-tiers')
    platformTiers.value = (res.commission_tiers || []).map(t => ({
      min: t.min || 0,
      max: t.max === -1 ? null : (t.max || ''),
      rate: t.rate || 0,
    }))
    districtTiers.value = (res.district_commission_tiers || []).map(t => ({
      min: t.min || 0,
      max: t.max === -1 ? null : (t.max || ''),
      rate: t.rate || 0,
    }))
  } catch { }
}

function addPlatformTier() {
  platformTiers.value.push({ min: 0, max: null, rate: 0.12 })
}
function removePlatformTier(idx) { platformTiers.value.splice(idx, 1) }

async function savePlatform() {
  savingPlatform.value = true
  try {
    const tiers = platformTiers.value.map(t => ({
      min: t.min || 0,
      max: t.max ? t.max : -1,
      rate: t.rate || 0,
    }))
    await http.put('/admin/commission-tiers', tiers)
    ElMessage.success('平台佣金阶梯已保存')
  } catch { } finally { savingPlatform.value = false }
}

function addDistrictTier() {
  districtTiers.value.push({ min: 0, max: null, rate: 0.02 })
}
function removeDistrictTier(idx) { districtTiers.value.splice(idx, 1) }

async function saveDistrict() {
  savingDistrict.value = true
  try {
    const tiers = districtTiers.value.map(t => ({
      min: t.min || 0,
      max: t.max ? t.max : -1,
      rate: t.rate || 0,
    }))
    await http.put('/admin/commission-tiers/district', tiers)
    ElMessage.success('分区佣金阶梯已保存')
  } catch { } finally { savingDistrict.value = false }
}

function calcPreview() {
  const tiers = platformTiers.value.map(t => ({
    min: t.min || 0, max: t.max ? t.max : -1, rate: t.rate || 0,
  }))
  previewRate.value = null
  for (const t of tiers) {
    if (previewSales.value >= t.min && (t.max < 0 || previewSales.value < t.max)) {
      previewRate.value = t.rate
      break
    }
  }
  if (previewRate.value === null) previewRate.value = 0.12

  const dtiers = districtTiers.value.map(t => ({
    min: t.min || 0, max: t.max ? t.max : -1, rate: t.rate || 0,
  }))
  previewDistrictRate.value = 0
  for (const t of dtiers) {
    if (previewSales.value >= t.min && (t.max < 0 || previewSales.value < t.max)) {
      previewDistrictRate.value = t.rate
      break
    }
  }
}
</script>

<style scoped>
.commission-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }
.section-label { font-size: 16px; font-weight: 700; margin: 0 0 4px; color: #333; }
.section-hint { font-size: 13px; color: #999; margin: 0 0 12px; }
</style>
