<template>
  <div>
    <el-card shadow="never">
      <template #header><span>系统配置</span></template>
      <el-table :data="configs" stripe v-loading="loading">
        <el-table-column prop="key" label="配置项" width="200" />
        <el-table-column prop="value" label="值" />
        <el-table-column prop="description" label="说明" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editConfig(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑配置" width="400px">
      <el-form :model="editForm">
        <el-form-item label="配置项">
          <el-input v-model="editForm.key" disabled />
        </el-form-item>
        <el-form-item label="值">
          <el-input v-model="editForm.value" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="editForm.description" disabled />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api'

const configs = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editForm = ref({ key: '', value: '', description: '' })

onMounted(async () => {
  loading.value = true
  try {
    configs.value = await http.get('/admin/system/configs')
  } catch (e) { } finally { loading.value = false }
})

function editConfig(row) {
  editForm.value = { ...row }
  dialogVisible.value = true
}

async function saveConfig() {
  try {
    await http.put(`/admin/system/configs/${editForm.value.key}?value=${editForm.value.value}`)
    ElMessage.success('已更新')
    dialogVisible.value = false
    // reload
    configs.value = await http.get('/admin/system/configs')
  } catch (e) { }
}
</script>
