import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from payment import verify_notify, _is_configured
from database import get_db
from models.order import Order
from models.payment import PaymentRecord
from schemas.payment import PayParamsOut, RefundIn

logger = logging.getLogger("app.pay")

router = APIRouter(prefix="/api/common/pay", tags=["公共-支付"])


@router.post("/notify")
async def pay_notify(request: Request):
    """
    微信支付回调通知
    无需鉴权，通过微信签名验证安全性
    """
    body = await request.body()
    body_str = body.decode("utf-8")
    signature = request.headers.get("Wechatpay-Signature", "")
    timestamp = request.headers.get("Wechatpay-Timestamp", "")
    nonce = request.headers.get("Wechatpay-Nonce", "")
    serial = request.headers.get("Wechatpay-Serial", "")

    data = verify_notify(body_str, signature, timestamp, nonce, serial)

    out_trade_no = data.get("out_trade_no", "")
    transaction_id = data.get("transaction_id", "")
    trade_state = data.get("trade_state", "")

    db = next(get_db())
    try:
        order = db.query(Order).filter(Order.order_no == out_trade_no).first()
        if not order:
            return {"code": "FAIL", "message": "订单不存在"}

        if trade_state == "SUCCESS":
            order.status = "pending_accept"
            order.paid_at = datetime.now()
            db.add(PaymentRecord(
                order_id=order.id,
                transaction_id=transaction_id,
                out_trade_no=out_trade_no,
                amount=order.total_price,
                status="success",
                raw_notify=data,
            ))
            db.commit()
            logger.info("Payment callback SUCCESS | order_no=%s txn=%s amount=%s",
                        out_trade_no, transaction_id, order.total_price)

        return {"code": "SUCCESS", "message": "成功"}
    finally:
        db.close()
