import os


class Settings:
    APP_NAME: str = "外卖平台"
    DEBUG: bool = True

    # 数据库 — 开发阶段使用 SQLite，生产换 MySQL
    # MySQL: mysql+pymysql://root:root@localhost:3306/food_delivery?charset=utf8mb4
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./food_delivery.db",
    )

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-please")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 微信小程序
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")
    WECHAT_SECRET: str = os.getenv("WECHAT_SECRET", "")

    # 微信支付 (JSAPI / 小程序支付)
    WECHAT_PAY_MCHID: str = os.getenv("WECHAT_PAY_MCHID", "")
    WECHAT_PAY_API_V3_KEY: str = os.getenv("WECHAT_PAY_API_V3_KEY", "")
    WECHAT_PAY_SERIAL_NO: str = os.getenv("WECHAT_PAY_SERIAL_NO", "")
    WECHAT_PAY_PRIVATE_KEY: str = os.getenv("WECHAT_PAY_PRIVATE_KEY", "")
    WECHAT_PAY_NOTIFY_URL: str = os.getenv("WECHAT_PAY_NOTIFY_URL", "")

    # 文件上传
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # Redis (可选 - 用于限流器和缓存)
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # 分页
    PAGE_SIZE_DEFAULT: int = 10


settings = Settings()
