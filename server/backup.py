"""
数据库 + 上传文件备份脚本
- 支持 SQLite / MySQL
- 优先上传备份到 OSS（如已配置），同时保留本地副本
- 自动清理过期备份
- 用法: python backup.py [备份目录，默认 ./backups]
"""
import os
import sys
import shutil
import datetime
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backup")


def backup_sqlite(db_path: str, backup_dir: Path) -> str:
    """SQLite: 直接复制文件（写入安全，SQLite 支持并发读）"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = Path(db_path).stem
    backup_name = f"{db_name}_{timestamp}.db"
    backup_path = backup_dir / backup_name

    shutil.copy2(db_path, backup_path)
    return str(backup_path)


def backup_mysql(url: str, backup_dir: Path) -> str:
    """MySQL: 使用 mysqldump"""
    import re

    m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)', url)
    if not m:
        raise ValueError(f"无法解析 MySQL URL: {url}")

    user, password, host, port, dbname = m.groups()
    port = port or "3306"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{dbname}_{timestamp}.sql"
    backup_path = backup_dir / backup_name

    cmd = f'mysqldump -h{host} -P{port} -u{user} -p"{password}" --single-transaction --routines --triggers {dbname} > "{backup_path}"'
    ret = os.system(cmd)
    if ret != 0:
        raise RuntimeError(f"mysqldump 失败，返回码: {ret}")
    return str(backup_path)


def backup_uploads(upload_dir: str, backup_dir: Path) -> str | None:
    """打包 uploads 目录为 tar.gz"""
    if not os.path.isdir(upload_dir):
        logger.warning("uploads 目录不存在，跳过: %s", upload_dir)
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"uploads_{timestamp}.tar.gz"
    archive_path = backup_dir / archive_name

    import tarfile
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(upload_dir, arcname="uploads")
    return str(archive_path)


def clean_old_backups(backup_dir: Path, keep_days: int = 30):
    """删除超过 keep_days 天的本地备份"""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    cleaned = 0
    for f in backup_dir.glob("*"):
        if f.is_file():
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                cleaned += 1
                logger.info("  已清理过期备份: %s", f.name)
    if cleaned == 0:
        logger.info("  无过期备份需要清理")


def upload_to_oss(local_path: str) -> bool:
    """将备份文件上传到 OSS，失败不阻塞"""
    try:
        from utils.oss import oss_client
        result = oss_client.upload_backup(local_path)
        return result is not None
    except Exception as e:
        logger.warning("OSS 备份上传失败（不影响本地备份）: %s", e)
        return False


def main():
    backup_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "./backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    from config import settings
    db_url = settings.DATABASE_URL

    logger.info("=" * 50)
    logger.info("开始备份任务")
    logger.info("  数据库类型: %s", "SQLite" if "sqlite" in db_url else "MySQL")
    logger.info("  本地备份目录: %s", backup_dir.absolute())

    # ---- 1. 数据库备份 ----
    try:
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "")
            backup_path = backup_sqlite(db_path, backup_dir)
        elif "mysql" in db_url or "pymysql" in db_url:
            backup_path = backup_mysql(db_url, backup_dir)
        else:
            logger.error("不支持的数据库类型: %s", db_url)
            sys.exit(1)

        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        logger.info("  ✓ 数据库备份完成: %s (%.1f MB)", os.path.basename(backup_path), size_mb)

        # 上传数据库备份到 OSS
        upload_to_oss(backup_path)

    except Exception as e:
        logger.error("  ✗ 数据库备份失败: %s", e)
        sys.exit(1)

    # ---- 2. uploads 目录备份 ----
    try:
        upload_dir = settings.UPLOAD_DIR
        archive_path = backup_uploads(upload_dir, backup_dir)
        if archive_path:
            size_mb = os.path.getsize(archive_path) / (1024 * 1024)
            logger.info("  ✓ uploads 备份完成: %s (%.1f MB)", os.path.basename(archive_path), size_mb)
            upload_to_oss(archive_path)
    except Exception as e:
        logger.warning("  ⚠ uploads 备份失败（不阻塞）: %s", e)

    # ---- 3. 清理 ----
    clean_old_backups(backup_dir, keep_days=30)
    logger.info("备份任务完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
