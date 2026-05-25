"""
后台定时任务 — 超时未支付订单自动取消
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from database import SessionLocal
from models.order import Order, OrderTimeline

logger = logging.getLogger("app.tasks")

AUTO_CANCEL_MINUTES = 15  # 未支付订单超时时间


async def auto_cancel_pending_orders():
    """每 60 秒检查一次，取消超过 15 分钟未支付的订单"""
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=AUTO_CANCEL_MINUTES)
            orders = db.query(Order).filter(
                Order.status == "pending_pay",
                Order.created_at < cutoff,
            ).all()

            for order in orders:
                order.status = "cancelled"
                order.cancel_reason = f"超时{AUTO_CANCEL_MINUTES}分钟未支付，系统自动取消"
                order.cancel_by = "system"
                db.add(OrderTimeline(
                    order_id=order.id,
                    status="cancelled",
                    description=f"超时{AUTO_CANCEL_MINUTES}分钟未支付",
                ))
                logger.info("Auto-cancelled unpaid order | order_no=%s order_id=%d",
                            order.order_no, order.id)

            if orders:
                db.commit()
                logger.info("Auto-cancel batch done | count=%d", len(orders))
        except Exception:
            db.rollback()
            logger.exception("Auto-cancel task error")
        finally:
            db.close()
