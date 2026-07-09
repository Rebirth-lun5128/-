<template>
  <div class="page">
    <van-nav-bar title="菜品管理" left-text="返回" left-arrow @click-left="$router.back()" />

    <div class="menu-layout">
      <!-- 左侧分类 -->
      <div class="cat-side">
        <div v-for="(cat, i) in categories" :key="cat.id"
          class="cat-tab" :class="{ active: activeCat === i }"
          @click="activeCat = i">
          {{ cat.name }}
        </div>
        <div class="cat-add" @click="showCatModal = true">+ 分类</div>
      </div>

      <!-- 右侧商品 -->
      <div class="item-list">
        <van-empty v-if="!filteredItems.length" description="暂无商品" />
        <div v-for="item in filteredItems" :key="item.id" class="menu-item" :class="{ off: item.status === 0 }">
          <van-image :src="item.image" width="60" height="60" fit="cover" radius="6" />
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-meta">
              <span class="price">¥{{ item.price }}</span>
              <van-tag size="small" :type="item.status === 1 ? 'success' : 'default'">
                {{ item.status === 1 ? '上架' : '下架' }}
              </van-tag>
            </div>
          </div>
          <div class="item-act">
            <van-icon name="edit" size="18" color="#999" @click="goEdit(item.id)" />
          </div>
        </div>
        <van-button block plain size="small" @click="goEdit()" style="margin-top:12px">+ 添加商品</van-button>
      </div>
    </div>

    <!-- 分类弹窗 -->
    <van-dialog v-model:show="showCatModal" :title="editingCat ? '编辑分类' : '添加分类'"
      show-cancel-button @confirm="saveCategory">
      <van-field v-model="catName" placeholder="请输入分类名称" style="padding:12px" />
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { merchantApi } from '../../utils/api.js'
import { showToast } from 'vant'

const categories = ref([])
const allItems = ref([])
const activeCat = ref(0)
const showCatModal = ref(false)
const catName = ref('')
const editingCat = ref(null)

const activeCatId = computed(() => categories.value[activeCat.value]?.id)

const filteredItems = computed(() => {
  if (!categories.value.length) return allItems.value
  const cid = activeCatId.value
  return cid ? allItems.value.filter(i => i.category_id === cid) : allItems.value
})

const load = async () => {
  try {
    const cats = await merchantApi.get('/api/merchant/menu/categories')
    const items = await merchantApi.get('/api/merchant/menu/items')
    categories.value = cats || []
    allItems.value = items || []
  } catch {}
}

const goEdit = (id) => {
  const cid = activeCatId.value || ''
  const url = id ? `#/m/menu-edit/${id}` : `#/m/menu-edit/new?cat=${cid}`
  window.location.hash = url
}

const saveCategory = async () => {
  const name = catName.value.trim()
  if (!name) { showToast('请输入名称'); return }
  try {
    if (editingCat.value) {
      await merchantApi.put(`/api/merchant/menu/categories/${editingCat.value.id}`, { name, sort_order: 0 })
    } else {
      await merchantApi.post('/api/merchant/menu/categories', { name, sort_order: 0 })
    }
    showToast(editingCat.value ? '已更新' : '已添加')
    catName.value = ''
    editingCat.value = null
    load()
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; }
.menu-layout { display: flex; height: calc(100vh - 46px); }
.cat-side { width: 100px; background: #f5f5f5; overflow-y: auto; padding: 4px 0; flex-shrink: 0; }
.cat-tab { padding: 12px 8px; font-size: 13px; text-align: center; border-left: 3px solid transparent; cursor: pointer; }
.cat-tab.active { background: #fff; border-left-color: #ff6b35; color: #ff6b35; font-weight: bold; }
.cat-add { padding: 12px 8px; font-size: 13px; text-align: center; color: #ff6b35; cursor: pointer; }
.item-list { flex: 1; overflow-y: auto; padding: 8px; }
.menu-item { display: flex; align-items: center; background: #fff; padding: 8px; border-radius: 8px; margin-bottom: 8px; gap: 8px; }
.menu-item.off { opacity: 0.5; }
.item-info { flex: 1; }
.item-name { font-size: 14px; margin-bottom: 4px; }
.item-meta { display: flex; align-items: center; gap: 8px; }
.price { color: #ff6b35; font-weight: bold; }
.item-act { cursor: pointer; }
</style>
