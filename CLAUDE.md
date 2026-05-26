# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

社区夜市外卖平台，支持跨店合单（用户一次下单多家摊位，统一配送）。包含 FastAPI 后端、3个微信小程序（用户端/商家端/骑手端）、1个 Vue3 管理后台。

## 启动命令

```bash
# 后端（开发）
cd E:\CC\server
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 初始化种子数据
python seed.py

# 运行测试
python -m pytest tests/ -v --tb=short                     # 全部 (140个)
python -m pytest tests/test_auth.py -v --tb=short         # 单个文件
python -m pytest tests/test_auth.py::TestWechatLogin -v   # 单个类
python -m pytest tests/test_auth.py -k "wechat" -v        # 按名称筛选

# 管理后台（开发）
cd E:\CC\admin-web
npm install
npm run dev        # localhost:3000, /api → :8000

# Docker
docker-compose up --build              # 后端 + 管理后台 (SQLite)
docker-compose --profile mysql up      # 含 MySQL
docker-compose --profile full up       # 含 MySQL + Redis
```

## 核心架构

### 总单+子单 (CombinedOrder + SubOrder)

这是整个系统最关键的架构。用户一次下单可跨多个店铺，由一位骑手统一配送。

```
CombinedOrder（总单）               SubOrder（子单，按店铺分）
├─ order_no                        ├─ store_id / store_name_snapshot
├─ user_id                         ├─ items_total / commission_rate
├─ address_snapshot (JSON)         ├─ status（独立流转）
├─ delivery_fee / total_price      │   pending_accept → preparing → ready
├─ status（由子单聚合推导）          │   → delivering → completed / cancelled
│   pending_pay / pending          ├─ cancel_reason / cancel_by
│   / delivering / completed       └─ SubOrderItem[] + SubOrderTimeline[]
│   / partial / cancelled
├─ rider_id（统一配送）
└─ district_id
```

- `SubOrder.status` 各自独立流转，商家各自接单/拒单/出餐
- `CombinedOrder.status` 由 `_derive_combined_status()` 从所有子单聚合
- 当所有非取消子单都 `ready` 时，WebSocket 推送给骑手
- 送达时按子单分别结算（`commission_rate` 可每店不同）
- 旧 `Order`/`OrderItem`/`OrderTimeline` 模型已废弃但仍存在，不要在其上添加新功能

### 配送费计算

路径 `server/routers/user/order.py` → `_calculate_delivery_fee()`：
1. 基础配送费 = 当前是否高峰期 → `District.peak_delivery_fee` : `District.delivery_fee`
2. 跨店附加费 = max(各店 `Store.delivery_surcharge`)
3. 满减优惠 = 匹配 `District.delivery_fee_rules`（满X免/满X减Y）

### 角色体系 (5种)

| 角色 | 路由前缀 | 前端 |
|---|---|---|
| `user` | `/api/user/*` | miniprogram-user |
| `merchant` | `/api/merchant/*` | miniprogram-merchant |
| `rider` | `/api/rider/*` | miniprogram-rider |
| `district_admin` | `/api/admin/*` (部分) | miniprogram-admin |
| `super_admin` | `/api/admin/*` (全部) | admin-web |

认证：JWT Bearer token，`auth.py` 中 `RoleChecker` 类做角色拦截。

### WebSocket

端点 `/ws?token={jwt}`，`ConnectionManager` 支持按 user_id / merchant_id / rider_id / 角色广播。推送事件包括 `order_paid`、`new_delivery`、`modification_requested` 等。HTTP 路由中通过 `push_order_event_sync()` 调用（内部用 `asyncio.ensure_future`）。

### 结算流

送达 → 按子单创建 `Settlement`（`net_amount = items_total * (1 - commission_rate)`） → 商家/骑手可提现（创建 paid 状态 Settlement 记录）。

## 前端坑点

### 微信小程序

- **`wx.showModal({editable:true})` 不可靠**：低版本基础库不支持，`res.content` 为 undefined。应使用页面内自定义弹窗（`<input>` + 遮罩层 + `setTimeout(300)` 延迟显示）。
- **`navigator` 优于 `bindtap`**：统计卡片等导航场景用 `<navigator url="...">` 比 `bindtap`/`catchtap` 更可靠。`catchtap` 会阻止事件冒泡，子元素上的 `catchtap` 会导致父元素收不到事件。
- **`hover-class` 中不要用 `transform: scale()`**：会导致部分设备点击区域偏移。
- **事件穿透**：从 `wx.showActionSheet` 回调中弹出的自定义弹窗需要用 `setTimeout(300ms)` 延迟，否则 ActionSheet 关闭的触摸事件会触发弹窗遮罩的关闭回调。

### API 工具 (miniprogram)

- 导出是 `api.del()` 不是 `api.delete()`（`delete` 是 JS 保留字）。
- 401 时自动清除 token 并跳转登录页。

## 后端坑点

- **FastAPI `list[int]` 参数必须加 `Body()`**：`def sort_categories(ids: list[int] = Body(...))`，否则被当作查询参数 `?ids=1&ids=2`，前端发 JSON body 后端收不到。
- 测试用内存 SQLite（`sqlite:///:memory:` + StaticPool），通过 `database.engine` 和 `SessionLocal` 的模块变量覆盖实现注入。
- Alembic 迁移已过时（引用旧模型名 `restaurants`/`regions`），开发不要依赖迁移，直接 `Base.metadata.create_all()`。

## 测试种子账号

| 角色 | 手机号 | 密码 |
|---|---|---|
| super_admin | 13800000000 | admin123 |
| district_admin | 13800000001 | admin123 |
| rider | 13800000002 | 123456 |
| merchant | 13800000011-13 | 123456 |
| user | 13800000099 | 无（微信登录） |
