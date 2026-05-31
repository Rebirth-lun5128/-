"""
阿里云 OSS 客户端封装
- 未配置 OSS 环境变量时自动降级（不阻塞业务）
- 上传失败自动回退，不影响主流程
"""
import logging
import uuid
from pathlib import Path

logger = logging.getLogger("oss")


class OSSClient:
    """OSS 客户端，配置缺失时静默降级为不可用状态"""

    def __init__(self):
        self._available = False
        self._bucket = None
        self._url_base = ""

        # 延迟导入，oss2 未安装时不报错
        try:
            import oss2
            from config import settings

            self._endpoint = settings.OSS_ENDPOINT
            self._key_id = settings.OSS_ACCESS_KEY_ID
            self._key_secret = settings.OSS_ACCESS_KEY_SECRET
            self._bucket_name = settings.OSS_BUCKET_NAME
            self._url_base = settings.OSS_URL_BASE.rstrip("/") if settings.OSS_URL_BASE else ""

            if not all([self._endpoint, self._key_id, self._key_secret, self._bucket_name]):
                logger.info("OSS 未完整配置，使用本地文件存储")
                return

            auth = oss2.Auth(self._key_id, self._key_secret)
            self._bucket = oss2.Bucket(auth, self._endpoint, self._bucket_name)
            self._available = True
            logger.info("OSS 客户端已就绪，Bucket: %s", self._bucket_name)

        except ImportError:
            logger.info("oss2 SDK 未安装，使用本地文件存储")
        except Exception as e:
            logger.warning("OSS 初始化失败: %s，回退到本地存储", e)

    @property
    def available(self) -> bool:
        return self._available

    def upload_image(self, content: bytes, ext: str = ".png") -> dict:
        """
        上传图片到 OSS
        返回 {"url": "https://...", "key": "uploads/xxx.png"}
        失败时返回 None，由调用方回退到本地存储
        """
        if not self._available:
            return None

        key = f"uploads/{uuid.uuid4().hex}{ext}"
        try:
            import oss2
            from oss2.exceptions import ServerError, RequestError

            result = self._bucket.put_object(key, content)
            if result.status != 200:
                logger.error("OSS 上传返回非 200: %s", result.status)
                return None

            url = f"{self._url_base}/{key}" if self._url_base else self._make_url(key)
            logger.info("OSS 上传成功: %s", key)
            return {"url": url, "key": key}

        except (ServerError, RequestError) as e:
            logger.error("OSS 上传失败（网络/服务端错误）: %s", e)
            return None
        except Exception as e:
            logger.exception("OSS 上传异常: %s", e)
            return None

    def upload_backup(self, file_path: str) -> str | None:
        """
        上传备份文件到 OSS（backups/ 目录）
        返回 OSS URL，失败返回 None
        """
        if not self._available:
            return None

        key = f"backups/{Path(file_path).name}"
        try:
            import oss2
            from oss2.exceptions import ServerError, RequestError

            self._bucket.put_object_from_file(key, file_path)
            logger.info("备份已上传 OSS: %s", key)
            return key
        except Exception as e:
            logger.error("备份上传 OSS 失败: %s", e)
            return None

    def delete(self, key: str) -> bool:
        """删除 OSS 上的文件"""
        if not self._available:
            return False
        try:
            self._bucket.delete_object(key)
            return True
        except Exception as e:
            logger.error("OSS 删除失败: %s — %s", key, e)
            return False

    def _make_url(self, key: str) -> str:
        """拼装 OSS 公开访问 URL"""
        # https://<bucket>.<endpoint>/<key>
        return f"https://{self._bucket_name}.{self._endpoint}/{key}"


# 全局单例
oss_client = OSSClient()
