"""分区模型 — 社区运营的核心单元, 1~N 个小区组成一个分区"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    admin_id = Column(Integer, nullable=True)                    # 分区管理员 user_id
    coverage = Column(JSON, nullable=True)                       # 覆盖的小区列表 ["阳光花园", "翠苑新村"]
    delivery_fee = Column(Integer, default=0)                    # 基础配送费(分)
    peak_delivery_fee = Column(Integer, default=0)               # 高峰期配送费(分)
    peak_start_hour = Column(Integer, nullable=True)             # 高峰期开始(如17)
    peak_end_hour = Column(Integer, nullable=True)               # 高峰期结束(如20)
    delivery_fee_rules = Column(JSON, default=[])                # 满减配送费规则 [{type, threshold, reduce?, desc}]
    delivery_range = Column(Integer, default=3)                  # 配送范围(km)
    notice = Column(String(500), default="")                     # 分区公告
    status = Column(Integer, default=1)                          # 1=启用 0=停用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
