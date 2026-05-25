<template>
  <div>
    <el-card shadow="never">
      <template #header><span>区域管理</span></template>
      <el-table :data="regions" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="区域名称" />
        <el-table-column prop="parent_id" label="上级区域ID" width="120" />
        <el-table-column prop="manager_id" label="管理者ID" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import http from '../api'

const regions = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    regions.value = await http.get('/admin/regions')
  } catch (e) { } finally { loading.value = false }
})
</script>
