"""
结构化日志 — 控制台文本格式 + 文件按天轮转
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    # 清掉已存在的 handler，避免重入
    root.handlers.clear()

    # 控制台: 简洁文本格式
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(console)

    # 文件: 按天轮转，保留30天
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s %(pathname)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(file_handler)

    # 降低第三方库日志噪音
    for name in ("uvicorn", "uvicorn.access", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
