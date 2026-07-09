import os
import secrets


class Settings:
    APP_NAME: str = "外卖平台"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # 数据库 — 开发阶段使用 SQLite，生产换 MySQL
    # MySQL: mysql+pymysql://root:root@localhost:3306/food_delivery?charset=utf8mb4
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./food_delivery.db",
    )

    # JWT — 生产环境必须设置 SECRET_KEY 环境变量
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "change-me-in-production-please" if DEBUG else "",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
    )  # 默认7天，生产建议15-60分钟 + refresh token

    # 微信公众号 (JS-SDK 分享)
    WECHAT_MP_APPID: str = os.getenv("WECHAT_MP_APPID", "")
    WECHAT_MP_SECRET: str = os.getenv("WECHAT_MP_SECRET", "")

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

    # 阿里云 OSS（可选 — 不配则使用本地存储）
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME", "")
    # OSS_URL_BASE: CDN 域名或 OSS 公开域名（如 https://cdn.your-domain.com），留空自动生成
    OSS_URL_BASE: str = os.getenv("OSS_URL_BASE", "")

    # Redis (可选 - 用于限流器和缓存)
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # CORS 白名单（逗号分隔）
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # 分页
    PAGE_SIZE_DEFAULT: int = 10


settings = Settings()

# 生产环境安全检查
if not settings.DEBUG:
    if settings.SECRET_KEY == "change-me-in-production-please":
        raise RuntimeError(
            "生产环境必须设置 SECRET_KEY 环境变量！\n"
            "示例: export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')"
        )
    if settings.DATABASE_URL.startswith("sqlite"):
        import warnings
        warnings.warn(
            "生产环境检测到 SQLite 数据库，建议切换到 MySQL。\n"
            "设置 DATABASE_URL=mysql+pymysql://user:pass@host:3306/food_delivery?charset=utf8mb4",
            RuntimeWarning,
        )
