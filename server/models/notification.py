"""社区运营 — 推送通知"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)  # null=全平台
    target_role = Column(String(20), default="user")  # user / merchant / rider / all
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
