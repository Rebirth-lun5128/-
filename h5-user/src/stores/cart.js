import { reactive } from 'vue'

export const cartStore = reactive({
  items: JSON.parse(localStorage.getItem('cart') || '[]'),
  selectedStoreIds: [],

  _save() {
    localStorage.setItem('cart', JSON.stringify(this.items))
  },

  get totalCount() {
    return this.items.reduce((sum, i) => sum + i.quantity, 0)
  },

  get totalPrice() {
    return this.items.reduce((sum, i) => sum + i.price * i.quantity, 0)
  },

  /** 按 storeId 分组的 store ID 列表 */
  get storeIds() {
    return [...new Set(this.items.map((i) => i.storeId))]
  },

  /** 已选中店铺的总数量 */
  get selectedCount() {
    return this.items
      .filter((i) => this.selectedStoreIds.includes(i.storeId))
      .reduce((s, i) => s + i.quantity, 0)
  },

  /** 已选中店铺的总金额 */
  get selectedTotal() {
    return this.items
      .filter((i) => this.selectedStoreIds.includes(i.storeId))
      .reduce((s, i) => s + i.price * i.quantity, 0)
  },

  /** 选中店铺是否跨区 */
  get crossDistrict() {
    const districts = new Set(
      this.items
        .filter((i) => this.selectedStoreIds.includes(i.storeId))
        .map((i) => i.districtId)
        .filter(Boolean)
    )
    return districts.size > 1
  },

  addItem(item) {
    const exist = this.items.find(
      (i) => i.productId === item.productId && i.storeId === item.storeId,
    )
    if (exist) {
      exist.quantity += item.quantity || 1
    } else {
      this.items.push({
        productId: item.productId,
        storeId: item.storeId,
        storeName: item.storeName || '',
        districtId: item.districtId || null,
        combinableDistricts: item.combinableDistricts || [],
        name: item.name,
        image: item.image || '',
        price: item.price,
        quantity: item.quantity || 1,
      })
    }
    if (!this.selectedStoreIds.includes(item.storeId)) {
      this.selectedStoreIds.push(item.storeId)
    }
    this._save()
  },

  updateQuantity(productId, storeId, quantity) {
    const idx = this.items.findIndex(
      (i) => i.productId === productId && i.storeId === storeId,
    )
    if (idx >= 0) {
      if (quantity <= 0) {
        this.items.splice(idx, 1)
        if (this.getItemsByStore(storeId).length === 0) {
          this.selectedStoreIds = this.selectedStoreIds.filter((id) => id !== storeId)
        }
      } else {
        this.items[idx].quantity = quantity
      }
    }
    this._save()
  },

  removeItem(productId, storeId) {
    this.items = this.items.filter(
      (i) => !(i.productId === productId && i.storeId === storeId),
    )
    if (this.getItemsByStore(storeId).length === 0) {
      this.selectedStoreIds = this.selectedStoreIds.filter((id) => id !== storeId)
    }
    this._save()
  },

  clearByStore(storeId) {
    this.items = this.items.filter((i) => i.storeId !== storeId)
    this.selectedStoreIds = this.selectedStoreIds.filter((id) => id !== storeId)
    this._save()
  },

  clearAll() {
    this.items = []
    this.selectedStoreIds = []
    this._save()
  },

  getItemsByStore(storeId) {
    return this.items.filter((i) => i.storeId === storeId)
  },

  toggleStore(storeId) {
    const idx = this.selectedStoreIds.indexOf(storeId)
    if (idx >= 0) {
      this.selectedStoreIds.splice(idx, 1)
    } else {
      this.selectedStoreIds.push(storeId)
    }
  },

  selectAll() {
    this.selectedStoreIds = [...this.storeIds]
  },

  deselectAll() {
    this.selectedStoreIds = []
  },
})
