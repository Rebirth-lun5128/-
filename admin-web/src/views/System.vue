<template>
  <div class="system-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-hdr">
          <span class="card-hdr-title">⚙️ 系统配置</span>
          <el-tag size="small" type="warning" effect="plain" round>仅超级管理员可修改</el-tag>
        </div>
      </template>

      <el-table :data="configs" stripe v-loading="loading">
        <el-table-column prop="key" label="配置项" width="240">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" type="info" class="cfg-key-tag">{{ row.key }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前值" min-width="200">
          <template #default="{ row }">
            <span class="cfg-value">{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="220">
          <template #default="{ row }">
            <span class="cfg-desc">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="editConfig(row)" round>
              <el-icon><EditPen /></el-icon> 编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      title="编辑配置"
      width="460px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="配置项">
          <el-input v-model="editForm.key" disabled size="large">
            <template #prefix><el-icon><Setting /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="editForm.value" autofocus size="large" placeholder="请输入新值" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="editForm.description" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" round>取消</el-button>
        <el-button type="primary" @click="saveConfig" round :loading="saving">
          <el-icon><Check /></el-icon> 保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editForm = ref({ key: '', value: '', description: '' })

async function loadConfigs() {
  loading.value = true
  try {
    configs.value = await http.get('/admin/system/configs')
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function editConfig(row) {
  editForm.value = { ...row }
  dialogVisible.value = true
}

async function saveConfig() {
  saving.value = true
  try {
    await http.put(`/admin/system/configs/${editForm.value.key}?value=${editForm.value.value}`)
    ElMessage.success('已更新')
    dialogVisible.value = false
    configs.value = await http.get('/admin/system/configs')
  } catch (e) { /* ignore */ } finally { saving.value = false }
}

loadConfigs()
</script>

<style scoped>
.system-page { animation: fadeIn 0.35s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.card-hdr { display: flex; justify-content: space-between; align-items: center; }
.card-hdr-title { font-size: 15px; font-weight: 600; color: #333; }

.cfg-key-tag { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px; }
.cfg-value { font-weight: 700; color: #6C5CE7; font-size: 15px; }
.cfg-desc { color: #999; font-size: 13px; }

@media (max-width: 767px) {
  .card-hdr { flex-wrap: wrap; gap: 10px; }
  .cfg-key-tag { font-size: 10px; }
  .cfg-value { font-size: 13px; }
}
</style>
