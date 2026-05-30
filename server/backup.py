"""
数据库备份脚本 — 支持 SQLite 和 MySQL
用法: python backup.py [备份目录，默认 ./backups]
"""
import os
import sys
import shutil
import datetime
from pathlib import Path


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
    # 解析 mysql+pymysql://user:pass@host:port/dbname
    m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)', url)
    if not m:
        raise ValueError(f"无法解析 MySQL URL: {url}")

    user, password, host, port, dbname = m.groups()
    port = port or "3306"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{dbname}_{timestamp}.sql"
    backup_path = backup_dir / backup_name

    # 使用 mysqldump（需在 PATH 中）
    cmd = f'mysqldump -h{host} -P{port} -u{user} -p"{password}" --single-transaction --routines --triggers {dbname} > "{backup_path}"'
    ret = os.system(cmd)
    if ret != 0:
        raise RuntimeError(f"mysqldump 失败，返回码: {ret}")
    return str(backup_path)


def clean_old_backups(backup_dir: Path, keep_days: int = 30):
    """删除超过 keep_days 天的备份"""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    for f in backup_dir.glob("*"):
        if f.is_file():
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                print(f"  已清理过期备份: {f.name}")


def main():
    backup_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "./backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    from config import settings
    db_url = settings.DATABASE_URL

    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] 开始备份...")
    print(f"  数据库: {db_url[:50]}...")
    print(f"  备份目录: {backup_dir.absolute()}")

    try:
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "")
            backup_path = backup_sqlite(db_path, backup_dir)
        elif "mysql" in db_url or "pymysql" in db_url:
            backup_path = backup_mysql(db_url, backup_dir)
        else:
            print(f"  不支持的数据库类型: {db_url}")
            sys.exit(1)

        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"  ✓ 备份完成: {os.path.basename(backup_path)} ({size_mb:.1f} MB)")

        # 清理过期备份
        clean_old_backups(backup_dir, keep_days=30)
        print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] 完成")
    except Exception as e:
        print(f"  ✗ 备份失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
