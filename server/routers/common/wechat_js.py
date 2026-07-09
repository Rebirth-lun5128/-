"""微信公众号 JS-SDK 签名生成"""
import hashlib
import random
import string
import time
import logging

import httpx
from fastapi import APIRouter, HTTPException, Query

from config import settings

logger = logging.getLogger("app.wechat_js")

router = APIRouter(prefix="/api/common/wechat", tags=["公共-微信JS-SDK"])

# 内存缓存
_cached_access_token: str = ""
_access_token_expires: float = 0
_cached_jsapi_ticket: str = ""
_jsapi_ticket_expires: float = 0


def _get_access_token() -> str:
    """获取公众号 access_token（带缓存）"""
    global _cached_access_token, _access_token_expires
    now = time.time()
    if _cached_access_token and now < _access_token_expires:
        return _cached_access_token

    if not settings.WECHAT_MP_APPID or not settings.WECHAT_MP_SECRET:
        raise HTTPException(status_code=500, detail="公众号未配置 WECHAT_MP_APPID / WECHAT_MP_SECRET")

    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": settings.WECHAT_MP_APPID,
                "secret": settings.WECHAT_MP_SECRET,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"获取access_token失败: {data.get('errmsg')}")
        _cached_access_token = data["access_token"]
        _access_token_expires = now + data.get("expires_in", 7200) - 300  # 提前5分钟过期
        logger.info("WeChat MP access_token refreshed")
        return _cached_access_token
    except httpx.RequestError:
        if _cached_access_token:
            return _cached_access_token  # 网络故障时用旧缓存
        raise HTTPException(status_code=502, detail="微信服务不可达")


def _get_jsapi_ticket() -> str:
    """获取 jsapi_ticket（带缓存）"""
    global _cached_jsapi_ticket, _jsapi_ticket_expires
    now = time.time()
    if _cached_jsapi_ticket and now < _jsapi_ticket_expires:
        return _cached_jsapi_ticket

    access_token = _get_access_token()
    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/cgi-bin/ticket/getticket",
            params={"access_token": access_token, "type": "jsapi"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise HTTPException(status_code=500, detail=f"获取jsapi_ticket失败: {data.get('errmsg')}")
        _cached_jsapi_ticket = data["ticket"]
        _jsapi_ticket_expires = now + data.get("expires_in", 7200) - 300
        logger.info("WeChat MP jsapi_ticket refreshed")
        return _cached_jsapi_ticket
    except httpx.RequestError:
        if _cached_jsapi_ticket:
            return _cached_jsapi_ticket
        raise HTTPException(status_code=502, detail="微信服务不可达")


@router.get("/js-sdk-config")
def get_js_sdk_config(url: str = Query(..., description="当前页面完整URL（不含#及之后）")):
    """
    返回微信 JS-SDK wx.config 所需的签名配置。
    前端调用示例: GET /api/common/wechat/js-sdk-config?url={encodeURIComponent(location.href.split('#')[0])}
    """
    if not settings.WECHAT_MP_APPID:
        raise HTTPException(status_code=500, detail="公众号 AppID 未配置")

    ticket = _get_jsapi_ticket()
    noncestr = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    timestamp = int(time.time())

    # 签名算法: sha1(jsapi_ticket={ticket}&noncestr={nonce}&timestamp={ts}&url={url})
    raw = f"jsapi_ticket={ticket}&noncestr={noncestr}&timestamp={timestamp}&url={url}"
    signature = hashlib.sha1(raw.encode()).hexdigest()

    logger.info("JS-SDK config generated | url=%s", url[:80])

    return {
        "appId": settings.WECHAT_MP_APPID,
        "timestamp": timestamp,
        "nonceStr": noncestr,
        "signature": signature,
    }
