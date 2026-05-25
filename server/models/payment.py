from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.sql import func

from database import Base


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    transaction_id = Column(String(64), default="")       # 微信支付交易号
    out_trade_no = Column(String(64), default="")          # 商户订单号
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending / success / refunded / closed
    pay_type = Column(String(20), default="wechat_jsapi")
    raw_notify = Column(JSON, nullable=True)               # 回调原始数据
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
