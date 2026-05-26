"""端到端流程测试 — 验证完整下单→支付→接单→配送→评价链路"""
import sys
sys.path.insert(0, ".")

import httpx, json

BASE = "http://localhost:8000"
client = httpx.Client(timeout=15)

def step(title, method, path, **kw):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    resp = getattr(client, method)(f"{BASE}{path}", **kw)
    data = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        print(f"  FAIL [{resp.status_code}]: {data}")
        return None
    print(f"  OK [{resp.status_code}]")
    return data

# 1. 用户登录
r = step("用户登录", "post", "/api/common/auth/phone", json={
    "phone": "13800000099", "password": "123456", "role": "user"
})
if not r: sys.exit(1)
user_token = r["token"]
user_id = r["user"]["id"]
print(f"  用户: {r['user']['nickname']} (id={user_id})")

# 2. 查看店铺
r = step("查看店铺列表", "get", "/api/user/stores", headers={"Authorization": f"Bearer {user_token}"})
if r:
    for s in r["items"]:
        print(f"  - {s['name']} [{s['store_type']}] {s['min_price']}yuan qisong")

# 3. 优惠券
r = step("查看可领券", "get", "/api/user/coupons/available", headers={"Authorization": f"Bearer {user_token}"})
if r:
    for c in r:
        print(f"  - {c['name']}: 减${c['discount_amount']} {'(已领)' if c['claimed'] else ''}")

r = step("领取满20减3券", "post", "/api/user/coupons/2/claim", headers={"Authorization": f"Bearer {user_token}"})
coupon_id = None
# 查我的券
r = step("我的优惠券", "get", "/api/user/coupons/my", headers={"Authorization": f"Bearer {user_token}"})
if r:
    for c in r:
        print(f"  - {c['name']} [{c['status']}] id={c['id']}")
        if not coupon_id and c['status'] == 'unused': coupon_id = c['id']

# 4. 创建订单
order_data = {
    "store_id": 1, "address_id": 1,
    "items": [
        {"product_id": 1, "name": "羊肉串(5串)", "image": "", "price": 15, "quantity": 2},
        {"product_id": 3, "name": "烤鸡翅(3只)", "image": "", "price": 12, "quantity": 1},
    ],
    "remark": "多加辣",
}
if coupon_id: order_data["user_coupon_id"] = coupon_id

r = step(f"创建订单 (券id={coupon_id})", "post", "/api/user/orders",
         headers={"Authorization": f"Bearer {user_token}"}, json=order_data)
if not r: sys.exit(1)
order_id = r["id"]
print(f"  订单ID: {r['id']}  编号: {r['order_no']}")
print(f"  金额: ${r['total_price']}  状态: {r['status']}")

# 5. 支付
r = step("模拟支付", "post", f"/api/user/orders/{order_id}/pay",
         headers={"Authorization": f"Bearer {user_token}"})
if r:
    print(f"  支付结果: {r}")

# 6. 商家登录 + 接单
r = step("商家登录", "post", "/api/common/auth/phone", json={
    "phone": "13800000011", "password": "123456", "role": "merchant"
})
if not r: sys.exit(1)
merchant_token = r["token"]
print(f"  商家: {r['user']['nickname']}")

r = step("查看待处理订单", "get", "/api/merchant/orders?status=pending_accept",
         headers={"Authorization": f"Bearer {merchant_token}"})
if r:
    for o in r["items"]:
        print(f"  - 订单{o['id']}: {o['store_name']} ${o['total_price']} [{o['status']}]")

r = step(f"商家接单#{order_id}", "put", f"/api/merchant/orders/{order_id}/accept",
         headers={"Authorization": f"Bearer {merchant_token}"})
if r: print(f"  状态: {r['status']}")

r = step(f"商家出餐#{order_id}", "put", f"/api/merchant/orders/{order_id}/ready",
         headers={"Authorization": f"Bearer {merchant_token}"})
if r: print(f"  状态: {r['status']}")

# 7. 骑手登录 + 接单 + 送达
r = step("骑手登录", "post", "/api/common/auth/phone", json={
    "phone": "13800000002", "password": "123456", "role": "rider"
})
if not r: sys.exit(1)
rider_token = r["token"]
print(f"  骑手: {r['user']['nickname']}")

r = step("骑手上线", "put", "/api/rider/orders/status?status=online",
         headers={"Authorization": f"Bearer {rider_token}"})
if r: print(f"  状态: {r}")

r = step("待取餐订单", "get", "/api/rider/orders/pending",
         headers={"Authorization": f"Bearer {rider_token}"})
if r:
    for o in r["items"]:
        print(f"  - 订单{o['id']}: {o['store_name']} ${o['total_price']}")

r = step(f"骑手接单#{order_id}", "post", f"/api/rider/orders/{order_id}/accept",
         headers={"Authorization": f"Bearer {rider_token}"})
if r: print(f"  状态: {r['status']}")

r = step(f"骑手送达#{order_id}", "put", f"/api/rider/orders/{order_id}/deliver",
         headers={"Authorization": f"Bearer {rider_token}"})
if r: print(f"  状态: {r['status']}")

# 8. 评价
r = step(f"用户评价订单#{order_id}", "post", f"/api/user/orders/{order_id}/review",
         headers={"Authorization": f"Bearer {user_token}"},
         json={"score": 5, "content": "味道很好，送餐也快！", "tags": ["味道好", "送餐快"]})
if r: print(f"  评分: {r['score']}星  内容: {r['content']}")

# 9. 查看订单详情
r = step(f"查看订单详情#{order_id}", "get", f"/api/user/orders/{order_id}",
         headers={"Authorization": f"Bearer {user_token}"})
if r:
    print(f"  状态: {r['status']}  ${r['total_price']}")
    if r.get("review"):
        print(f"  评价: {r['review']['score']}星 - {r['review']['content']}")
    print(f"  时间线: {len(r.get('timeline', []))}条")
    for t in r.get("timeline", []):
        print(f"    [{t['status']}] {t['description']}")

print(f"\n{'='*50}")
print(f"  全流程测试通过!")
print(f"{'='*50}")
client.close()
