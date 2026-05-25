"""
初始化种子数据 — 默认区域、系统配置、超级管理员
首次部署时运行: python seed.py
"""
from database import engine, Base, SessionLocal
from models.user import User
from models.region import Region, SystemConfig
from auth import hash_password

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # ---- 区域 ----
        regions = [
            Region(id=1, name="全城", sort_order=1, status=1),
            Region(id=2, name="朝阳区", parent_id=1, sort_order=2, status=1),
            Region(id=3, name="海淀区", parent_id=1, sort_order=3, status=1),
        ]
        for r in regions:
            if not db.query(Region).filter(Region.id == r.id).first():
                db.add(r)

        # ---- 系统配置 ----
        configs = [
            ("platform_fee_rate", "0.15", "平台抽成比例"),
            ("delivery_fee_default", "5", "默认配送费(元)"),
            ("rider_per_order", "5", "骑手每单收入(元)"),
            ("auto_cancel_minutes", "15", "未支付自动取消时间(分钟)"),
        ]
        for key, value, desc in configs:
            if not db.query(SystemConfig).filter(SystemConfig.config_key == key).first():
                db.add(SystemConfig(config_key=key, config_value=value, description=desc))

        # ---- 超级管理员 ----
        admin = db.query(User).filter(User.role == "super_admin").first()
        if not admin:
            admin = User(
                openid="admin_super",
                nickname="超级管理员",
                phone="13800000000",
                role="super_admin",
                hashed_password=hash_password("admin123"),
            )
            db.add(admin)
            print("  Super admin created: phone=13800000000, password=admin123")
        elif not admin.hashed_password:
            admin.hashed_password = hash_password("admin123")
            print("  Super admin password set: phone=13800000000, password=admin123")
        else:
            print(f"  Super admin already exists: phone={admin.phone}")

        db.commit()
        print("Seed data completed.")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
