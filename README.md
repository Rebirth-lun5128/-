# 社区夜市外卖平台

社区夜市跨店合单外卖配送平台。支持用户一次下单多家摊位，由一位骑手统一配送。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 |
| 数据库 | SQLite（开发）/ MySQL（生产） |
| 缓存 | Redis（可选，用于限流器） |
| 用户端小程序 | 微信原生小程序 |
| 商家端小程序 | 微信原生小程序 |
| 骑手端小程序 | 微信原生小程序 |
| 管理端小程序 | 微信原生小程序 |
| H5 用户端 | Vue 3 + Vant 4 + Vite |
| 网页管理后台 | Vue 3 + Element Plus + Vite |

## 项目结构

```
CC/
├── server/                  # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置（环境变量）
│   ├── auth.py              # JWT 认证 + 角色拦截
│   ├── database.py          # 数据库连接管理
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── routers/             # API 路由
│   │   ├── admin/           # 管理后台 API
│   │   ├── user/            # 用户端 API
│   │   ├── merchant/        # 商家端 API
│   │   ├── rider/           # 骑手端 API
│   │   └── common/          # 公共 API（认证、上传、WebSocket）
│   ├── websocket.py         # WebSocket 连接管理
│   ├── tasks.py             # 后台定时任务
│   ├── ratelimit.py         # IP 滑动窗口限流器
│   ├── seed.py              # 开发种子数据
│   └── tests/               # 测试
├── miniprogram-user/        # 用户端小程序
├── miniprogram-merchant/    # 商家端小程序
├── miniprogram-rider/       # 骑手端小程序
├── miniprogram-admin/       # 管理端小程序
├── h5-user/                 # H5 用户网页端
├── admin-web/               # Vue3 网页管理后台
└── docker-compose.yml       # Docker 编排
```

## 快速开始

### 前提条件

- Python 3.10+
- Node.js 18+
- （可选）MySQL 8.0+
- （可选）Redis 7+

### 1. 启动后端

```bash
cd server
pip install -r requirements.txt

# 复制并编辑环境变量
cp .env.example .env
# 编辑 .env，设置 SECRET_KEY 等关键配置

# 初始化种子数据
python seed.py

# 启动开发服务器
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 2. 启动网页管理后台

```bash
cd admin-web
npm install
npm run dev          # localhost:3000，/api 代理到 :8000
```

### 3. 启动 H5 用户端

```bash
cd h5-user
npm install
npx vite --host 0.0.0.0 --port 3001
```

### 4. 微信小程序

用微信开发者工具分别导入以下目录：
- `miniprogram-user/` — 用户端（AppID 替换为你的）
- `miniprogram-merchant/` — 商家端
- `miniprogram-rider/` — 骑手端
- `miniprogram-admin/` — 管理端

小程序默认连接 `http://localhost:8000`，可在各端 `utils/config.js` 中修改。

### 5. Docker 部署

```bash
# 后端 + 管理后台 (SQLite)
docker-compose up --build

# 含 MySQL
docker-compose --profile mysql up --build

# 含 MySQL + Redis
docker-compose --profile full up --build
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 签名密钥（生产必设） | `change-me-in-production-please` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./food_delivery.db` |
| `REDIS_URL` | Redis 连接串 | 空（使用内存限流器） |
| `DEBUG` | 调试模式 | `false` |
| `CORS_ORIGINS` | CORS 白名单（逗号分隔） | `*` |
| `WECHAT_APPID` | 微信小程序 AppID | 空 |
| `WECHAT_SECRET` | 微信小程序 Secret | 空 |
| `WECHAT_PAY_MCHID` | 微信支付商户号 | 空 |
| `UPLOAD_DIR` | 文件上传目录 | `./uploads` |

## 测试

```bash
cd server
python -m pytest tests/ -v --tb=short         # 全部
python -m pytest tests/test_auth.py -v         # 单个文件
python -m pytest tests/ -k "wechat" -v         # 按名称筛选
```

## 测试账号

| 角色 | 手机号 | 密码 |
|------|--------|------|
| 超级管理员 | 13800000000 | admin123 |
| 分区管理员 | 13800000001 | admin123 |
| 骑手 | 13800000002 | 123456 |
| 商家 | 13800000011-13 | 123456 |
| 用户 | 13800000099 | 无（微信登录） |

## 核心架构

### 总单+子单 (CombinedOrder + SubOrder)

用户一次下单可跨多个店铺，由一位骑手统一配送。

```
CombinedOrder（总单）               SubOrder（子单，按店铺分）
├─ order_no                        ├─ store_id
├─ user_id                         ├─ items_total / commission_rate
├─ address_snapshot (JSON)         ├─ status（独立流转）
├─ delivery_fee / total_price      │   pending_accept → preparing → ready
├─ status（由子单聚合推导）           │   → delivering → completed / cancelled
│   pending_pay / pending          └─ SubOrderItem[] + SubOrderTimeline[]
│   / delivering / completed
│   / partial / cancelled
├─ rider_id（统一配送）
└─ district_id
```

### 配送费计算

1. 基础配送费 = 当前是否高峰期 → `District.peak_delivery_fee` : `District.delivery_fee`
2. 跨店附加费 = max(各店 `Store.delivery_surcharge`)
3. 满减优惠 = 匹配 `District.delivery_fee_rules`

### 角色体系

| 角色 | 路由前缀 | 前端 |
|------|----------|------|
| `user` | `/api/user/*` | 用户端小程序 + H5 |
| `merchant` | `/api/merchant/*` | 商家端小程序 |
| `rider` | `/api/rider/*` | 骑手端小程序 |
| `district_admin` | `/api/admin/*` (部分) | 管理端小程序 |
| `super_admin` | `/api/admin/*` (全部) | 管理端小程序 + 网页后台 |

### 佣金结算

送达时按阶梯佣金率计算：
1. 查店铺当月累计销售额
2. 匹配平台佣金阶梯 → platform_fee
3. 匹配分区佣金阶梯 → district_fee
4. 商家净收入 = items_total - platform_fee - district_fee

## 生产部署检查清单

- [ ] 设置强随机 `SECRET_KEY` 环境变量
- [ ] 配置 `CORS_ORIGINS` 为实际域名
- [ ] 切换到 MySQL 数据库
- [ ] 配置 Redis（多 worker 部署必需）
- [ ] 配置微信小程序 AppID/Secret
- [ ] 配置微信支付商户参数
- [ ] 配置 HTTPS 证书
- [ ] 设置日志收集/监控（如 UptimeRobot 监控 `/health`）
- [ ] 确认依赖版本已更新至安全版本
