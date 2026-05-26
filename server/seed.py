"""开发环境种子数据 — 运行: python seed.py"""
import sys
sys.path.insert(0, ".")

from database import engine, Base, SessionLocal
from models import *  # noqa — 加载所有模型确保 create_all 能建表
from auth import hash_password

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # ---- 1. 系统配置 ----
        from models.region import SystemConfig
        configs = [
            ("platform_fee_rate", "0.12", "平台抽成比例 (12%)"),
            ("platform_fee_rate_default", "0.12", "新入驻商家默认抽成比例"),
            ("delivery_fee_default", "5", "默认配送费(元)"),
            ("rider_per_order", "5", "骑手每单收入(元)"),
            ("auto_cancel_minutes", "15", "未支付自动取消时间(分钟)"),
            ("peak_delivery_fee_enabled", "0", "高峰期配送费开关"),
        ]
        for key, value, desc in configs:
            if not db.query(SystemConfig).filter(SystemConfig.config_key == key).first():
                db.add(SystemConfig(config_key=key, config_value=value, description=desc))

        # ---- 2. 分区 ----
        from models.district import District
        d = db.query(District).first()
        if not d:
            d = District(
                name="阳光花园美食区",
                coverage=["阳光花园", "翠苑新村", "金都雅苑"],
                delivery_fee=300, delivery_range=3,
                peak_delivery_fee=500, peak_start_hour=17, peak_end_hour=20,
                delivery_fee_rules=[
                    {"type": "free", "threshold": 20, "desc": "满20元免配送费"},
                ],
                notice="欢迎光临阳光花园夜市！每晚17:00-24:00营业",
            )
            db.add(d)
            db.flush()
        district_id = d.id

        # ---- 3. 超级管理员 ----
        from models.user import User
        admin = db.query(User).filter(User.role == "super_admin").first()
        if not admin:
            admin = User(
                openid="admin_super", nickname="超级管理员", phone="13800000000",
                role="super_admin", hashed_password=hash_password("admin123"),
            )
            db.add(admin)
            db.flush()
        d.admin_id = admin.id

        # ---- 4. 骑手 ----
        rider_user = db.query(User).filter(User.phone == "13800000002").first()
        if not rider_user:
            rider_user = User(
                openid="rider_seed", nickname="骑手小王", phone="13800000002",
                role="rider", hashed_password=hash_password("123456"),
            )
            db.add(rider_user)
            db.flush()
            from models.rider import Rider
            rider = Rider(
                user_id=rider_user.id, real_name="王配送", phone="13800000002",
                district_id=district_id, audit_status="approved", status="online",
            )
            db.add(rider)

        # ---- 5. 商家 + 店铺 ----
        from models.store import Store, StoreCategory, Product

        merchants = [
            {
                "phone": "13800000011", "name": "老王烧烤", "store_type": "stall",
                "store_name": "老王烧烤", "category": "烧烤", "rating": 4.8,
                "monthly_sales": 536, "min_price": 15, "delivery_fee": 2,
                "delivery_time": "30分钟", "address": "阳光花园夜市A区01号",
                "stall_location": "夜市入口左侧第一家",
                "notice": "十年老店，新鲜食材每日采购",
                "products": [
                    ("羊肉串(5串)", 15, 20, "新鲜羊肉，现串现烤", -1),
                    ("牛肉串(5串)", 18, 22, "嫩牛肉，秘制酱料", -1),
                    ("烤鸡翅(3只)", 12, 15, "蜜汁烤翅", 50),
                    ("烤茄子", 8, 10, "蒜蓉烤茄子", -1),
                ],
            },
            {
                "phone": "13800000012", "name": "李姐私房菜", "store_type": "home_kitchen",
                "store_name": "李姐私房菜", "category": "家常菜", "rating": 4.9,
                "monthly_sales": 218, "min_price": 20, "delivery_fee": 3,
                "delivery_time": "45分钟", "address": "翠苑新村3栋502",
                "stall_location": "", "notice": "家庭厨房，每日限量",
                "products": [
                    ("红烧肉套餐", 28, None, "软糯红烧肉+米饭+例汤", 10),
                    ("糖醋排骨", 32, None, "酸甜可口，每日限量15份", 15),
                    ("手工水饺(20只)", 22, None, "韭菜鸡蛋/猪肉白菜可选", 20),
                ],
            },
            {
                "phone": "13800000013", "name": "平台优选", "store_type": "self_operated",
                "store_name": "平台优选超市", "category": "超市便利", "rating": 4.7,
                "monthly_sales": 1023, "min_price": 10, "delivery_fee": 1,
                "delivery_time": "25分钟", "address": "阳光花园商业街8号",
                "stall_location": "", "notice": "平台自营，品质保证",
                "products": [
                    ("可口可乐(330ml)", 3, None, "冰镇可乐", -1),
                    ("农夫山泉(550ml)", 2, None, "天然矿泉水", -1),
                    ("乐事薯片", 8, None, "原味/番茄味", 30),
                ],
            },
        ]

        for m in merchants:
            existing = db.query(User).filter(User.phone == m["phone"]).first()
            if existing:
                continue
            user = User(
                openid=f"merchant_{m['phone']}", nickname=m["name"], phone=m["phone"],
                role="merchant", hashed_password=hash_password("123456"),
            )
            db.add(user)
            db.flush()
            store = Store(
                user_id=user.id, district_id=district_id, store_type=m["store_type"],
                name=m["store_name"], phone=m["phone"], address=m["address"],
                stall_location=m["stall_location"], category=m["category"],
                rating=m["rating"], monthly_sales=m["monthly_sales"],
                min_price=m["min_price"], delivery_fee=m["delivery_fee"],
                delivery_time=m["delivery_time"], status="open", verify_status="verified",
                notice=m["notice"],
                commission_rate=0.12, delivery_surcharge=0,
            )
            db.add(store)
            db.flush()
            cat = StoreCategory(store_id=store.id, name="默认分类", sort_order=1)
            db.add(cat)
            db.flush()
            for name, price, orig, desc, stock in m["products"]:
                db.add(Product(
                    store_id=store.id, category_id=cat.id, name=name,
                    price=price, original_price=orig, description=desc, stock=stock,
                    is_recommended=1 if "串" in name or "肉" in name or "可乐" in name else 0,
                ))

        # ---- 6. 普通用户 ----
        normal = db.query(User).filter(User.phone == "13800000099").first()
        if not normal:
            from models.user import UserAddress
            normal = User(
                openid="user_seed", nickname="食客小明", phone="13800000099",
                role="user", hashed_password=hash_password("123456"),
            )
            db.add(normal)
            db.flush()
            addr = UserAddress(
                user_id=normal.id, contact_name="小明", contact_phone="13800000099",
                province="浙江省", city="杭州市", district="西湖区",
                detail="阳光花园12栋301室", is_default=1,
            )
            db.add(addr)

        # ---- 7. 优惠券 ----
        from models.coupon import Coupon
        if db.query(Coupon).count() == 0:
            db.add_all([
                Coupon(name="新用户专享券", coupon_type="new_user", discount_amount=5,
                       total_count=100, status=1),
                Coupon(name="满20减3", coupon_type="full_reduction", discount_amount=3,
                       condition_amount=20, total_count=50, status=1),
                Coupon(name="满30减5", coupon_type="full_reduction", discount_amount=5,
                       condition_amount=30, total_count=30, status=1),
                Coupon(name="立减2元", coupon_type="direct_discount", discount_amount=2,
                       total_count=200, status=1),
            ])

        db.commit()
        print("Seed data created successfully!")

        print("""
╔══════════════════════════════════════╗
║  测试账号 (密码均为 123456):         ║
║  管理员:  13800000000 / admin123     ║
║  骑手:    13800000002               ║
║  商家1:   13800000011 (老王烧烤)     ║
║  商家2:   13800000012 (李姐私房菜)   ║
║  商家3:   13800000013 (平台优选)     ║
║  用户:    13800000099               ║
║                                     ║
║  分区: 阳光花园美食区                ║
║  优惠券: 4张                        ║
╚══════════════════════════════════════╝
""")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
