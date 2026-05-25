"""
微信支付 API v3 工具模块
JSAPI 小程序支付: 统一下单 / 签名 / 回调验证 / 退款
未配置商户号时自动回退模拟模式
"""
import base64
import json
import time
import random
import string
from functools import lru_cache

import httpx
from fastapi import HTTPException

from config import settings

WECHAT_PAY_HOST = "https://api.mch.weixin.qq.com"

# ---- 内部工具 ----


def _is_configured() -> bool:
    return bool(settings.WECHAT_PAY_MCHID and settings.WECHAT_PAY_API_V3_KEY and settings.WECHAT_PAY_PRIVATE_KEY)


def _load_private_key():
    from cryptography.hazmat.primitives import serialization
    key = settings.WECHAT_PAY_PRIVATE_KEY
    if key.startswith("-----BEGIN"):
        loader = serialization.load_ssh_private_key if "OPENSSH" in key else serialization.load_pem_private_key
        return loader(key.encode(), password=None)
    with open(key, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _rsa_sign(message: str) -> str:
    """SHA256-RSA 签名 → base64"""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    private_key = _load_private_key()
    sig = private_key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


def _gen_nonce(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _api_auth(method: str, path: str, body: str = "") -> dict:
    timestamp = str(int(time.time()))
    nonce = _gen_nonce()
    canonical = f"{method}\n{path}\n{timestamp}\n{nonce}\n{body}\n"
    signature = _rsa_sign(canonical)
    authorization = (
        f'WECHATPAY2-SHA256-RSA2048 mchid="{settings.WECHAT_PAY_MCHID}",'
        f'nonce_str="{nonce}",timestamp="{timestamp}",'
        f'serial_no="{settings.WECHAT_PAY_SERIAL_NO}",signature="{signature}"'
    )
    return {"Authorization": authorization, "Accept": "application/json"}


def _api_call(method: str, path: str, body: dict = None) -> dict:
    body_str = json.dumps(body) if body else ""
    headers = _api_auth(method, path, body_str)
    headers["Content-Type"] = "application/json"
    with httpx.Client(timeout=15.0) as client:  # sync client for sync FastAPI endpoints
        resp = client.request(method, f"{WECHAT_PAY_HOST}{path}", content=body_str, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"微信支付错误: {resp.text[:500]}")
        return resp.json() if resp.text else {}


@lru_cache(maxsize=1)
def _platform_certs() -> dict:
    """获取微信支付平台证书 (缓存)"""
    from cryptography.hazmat.primitives import serialization
    data = _api_call("GET", "/v3/certificates")
    certs = {}
    for entry in data.get("data", []):
        cert = entry["encrypt_certificate"]
        plain = _aead_decrypt(cert["ciphertext"], cert["nonce"], cert["associated_data"])
        certs[entry["serial_no"]] = serialization.load_pem_x509_certificate(plain.encode())
    return certs


def _aead_decrypt(ciphertext: str, nonce: str, associated_data: str = "") -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = settings.WECHAT_PAY_API_V3_KEY.encode()
    aesgcm = AESGCM(key)
    decoded = aesgcm.decrypt(nonce.encode(), bytes.fromhex(ciphertext), associated_data.encode())
    return decoded.decode("utf-8")


# ---- 对外接口 ----


def create_jsapi_order(order_no: str, total: int, description: str, user_openid: str) -> dict:
    """
    JSAPI 统一下单 → 返回 wx.requestPayment 所需参数
    total: 订单金额 (分)
    """
    if not _is_configured():
        return _mock_prepay(order_no)

    body = {
        "appid": settings.WECHAT_APPID,
        "mchid": settings.WECHAT_PAY_MCHID,
        "description": description,
        "out_trade_no": order_no,
        "notify_url": settings.WECHAT_PAY_NOTIFY_URL,
        "amount": {"total": total, "currency": "CNY"},
        "payer": {"openid": user_openid},
    }
    data = _api_call("POST", "/v3/pay/transactions/jsapi", body)
    return _build_pay_params(data["prepay_id"])


def _build_pay_params(prepay_id: str) -> dict:
    """构建 wx.requestPayment 参数 + 签名"""
    nonce = _gen_nonce()
    timestamp = str(int(time.time()))
    package = f"prepay_id={prepay_id}"
    message = f"{settings.WECHAT_APPID}\n{timestamp}\n{nonce}\n{package}\n"
    return {
        "appId": settings.WECHAT_APPID,
        "timeStamp": timestamp,
        "nonceStr": nonce,
        "package": package,
        "signType": "RSA",
        "paySign": _rsa_sign(message),
    }


def _mock_prepay(order_no: str) -> dict:
    return {
        "appId": settings.WECHAT_APPID or "mock_appid",
        "timeStamp": str(int(time.time())),
        "nonceStr": _gen_nonce(),
        "package": f"prepay_id=mock_{order_no}",
        "signType": "RSA",
        "paySign": "mock_signature",
        "isMock": True,
    }


def verify_notify(body: str, wechatpay_signature: str, wechatpay_timestamp: str, wechatpay_nonce: str, wechatpay_serial: str) -> dict:
    """验证回调通知: 验签 + 解密, 返回交易数据"""
    if not _is_configured():
        return json.loads(body)

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # 验签
    message = f"{wechatpay_timestamp}\n{wechatpay_nonce}\n{body}\n"
    try:
        certs = _platform_certs()
        cert = certs.get(wechatpay_serial)
        if not cert:
            certs = _platform_certs.cache_clear() or _platform_certs()  # refresh cache
            cert = certs.get(wechatpay_serial)
        if not cert:
            raise HTTPException(status_code=400, detail="未找到平台证书")
        cert.public_key().verify(
            base64.b64decode(wechatpay_signature),
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="回调验签失败")

    # 解密 resource
    resource = json.loads(body).get("resource", {})
    plain = _aead_decrypt(
        resource.get("ciphertext", ""),
        resource.get("nonce", ""),
        resource.get("associated_data", ""),
    )
    return json.loads(plain)


def apply_refund(order_no: str, refund_amount: int, total_amount: int, reason: str = "") -> dict:
    """申请退款"""
    if not _is_configured():
        return {"status": "SUCCESS", "isMock": True}

    body = {
        "out_trade_no": order_no,
        "out_refund_no": f"{order_no}_refund_{int(time.time())}",
        "amount": {"refund": refund_amount, "total": total_amount, "currency": "CNY"},
        "reason": reason or "用户申请退款",
    }
    return _api_call("POST", "/v3/refund/domestic/refunds", body)
