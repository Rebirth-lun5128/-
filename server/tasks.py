"""
后台定时任务 — 超时未支付订单自动取消（同时覆盖 Order 和 CombinedOrder）
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from database import SessionLocal
from models.order import Order, OrderTimeline, CombinedOrder, SubOrder, SubOrderTimeline

logger = logging.getLogger("app.tasks")

AUTO_CANCEL_MINUTES = 15  # 未支付订单超时时间


async def auto_cancel_pending_orders():
    """每 60 秒检查一次，取消超过 15 分钟未支付的订单（同时处理旧 Order 和新 CombinedOrder）"""
    while True:
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Auto-cancel task cancelled")
            break
        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=AUTO_CANCEL_MINUTES)
            cancelled_count = 0

            # 1. 旧 Order 模型（向后兼容）
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
                cancelled_count += 1

            # 2. 新 CombinedOrder 模型
            combined_orders = db.query(CombinedOrder).filter(
                CombinedOrder.status == "pending_pay",
                CombinedOrder.created_at < cutoff,
            ).all()
            for co in combined_orders:
                co.status = "cancelled"
                co.cancel_reason = f"超时{AUTO_CANCEL_MINUTES}分钟未支付，系统自动取消"
                co.cancel_by = "system"
                # 同时取消所有子单
                for sub in co.sub_orders:
                    if sub.status not in ("completed", "cancelled"):
                        sub.status = "cancelled"
                        sub.cancel_reason = f"总单超时未支付，系统自动取消"
                        sub.cancel_by = "system"
                        db.add(SubOrderTimeline(
                            sub_order_id=sub.id,
                            status="cancelled",
                            description=f"总单超时{AUTO_CANCEL_MINUTES}分钟未支付",
                        ))
                cancelled_count += 1
                logger.info("Auto-cancelled unpaid combined order | order_no=%s id=%d",
                            co.order_no, co.id)

            if cancelled_count:
                db.commit()
                logger.info("Auto-cancel batch done | count=%d", cancelled_count)
        except asyncio.CancelledError:
            break
        except Exception:
            db.rollback()
            logger.exception("Auto-cancel task error")
        finally:
            db.close()
