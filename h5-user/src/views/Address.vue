<script setup>
import { ref, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { api } from '../utils/api'

const router = useRouter()
const route = useRoute()
const addresses = ref([])
const selectMode = route.query.select === '1'

onActivated(loadAddresses)

async function loadAddresses() {
  try { addresses.value = await api.get('/api/user/addresses') } catch { }
}

function onSelect(addr) {
  if (!selectMode) return
  router.replace({ name: 'OrderConfirm', query: { addr_id: addr.id } })
}

function onEdit(id) { router.push(`/address-form/${id}`) }
function onAdd() { router.push('/address-form') }

async function onDelete(id) {
  try {
    await showDialog({ title: '确认删除', message: '确定删除该地址吗？' })
    await api.del(`/api/user/addresses/${id}`)
    showToast({ message: '已删除', type: 'success' })
    loadAddresses()
  } catch { }
}
</script>

<template>
  <div class="page">
    <van-nav-bar :title="selectMode ? '选择地址' : '地址管理'" left-text="返回" left-arrow @click-left="$router.back()" fixed placeholder />
    <div v-if="addresses.length === 0" class="text-center text-gray p-4">暂无地址</div>
    <div v-for="a in addresses" :key="a.id" class="bg-white m-3 p-3 rounded shadow" @click="onSelect(a)">
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <div class="font-bold">{{ a.contact_name }}
            <span class="text-sm text-gray ml-2">{{ a.contact_phone }}</span>
            <span v-if="a.is_default" class="text-sm ml-2 px-1 rounded" style="background:#FFF3E0;color:#ff6b35">默认</span>
          </div>
          <div class="text-sm text-gray mt-1">{{ a.province }}{{ a.city }}{{ a.district }} {{ a.detail }}</div>
        </div>
        <div class="flex" style="gap:8px" @click.stop>
          <van-button size="small" plain type="primary" @click="onEdit(a.id)">编辑</van-button>
          <van-button size="small" plain type="danger" @click="onDelete(a.id)">删除</van-button>
        </div>
      </div>
    </div>
    <div class="p-3">
      <van-button type="primary" block round color="#ff6b35" @click="onAdd" style="height:44px">新增地址</van-button>
    </div>
  </div>
</template>
