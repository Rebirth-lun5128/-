import logging
import random
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password
from config import settings
from database import get_db
from models.user import User
from ratelimit import strict_limiter
from schemas.user import LoginOut, UserOut, UserUpdate, WechatLoginIn, PhoneLoginIn, RefreshIn

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/common/auth", tags=["公共-认证"])

REFRESH_TOKEN_DAYS = 30  # refresh_token 30天有效


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def _make_login_response(user: User, db: Session) -> LoginOut:
    """生成登录响应，同时生成 refresh_token 存入用户记录"""
    user.last_login = datetime.now(timezone.utc)
    user.refresh_token = _generate_refresh_token()
    user.refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    token = create_access_token(data={"sub": user.id, "role": user.role})
    db.commit()
    return LoginOut(token=token, refresh_token=user.refresh_token, user=UserOut.model_validate(user))


@router.post("/wechat", response_model=LoginOut)
def wechat_login(body: WechatLoginIn, db: Session = Depends(get_db), _rl=Depends(strict_limiter)):
    """
    微信小程序登录 (用户端/骑手端)
    通过 wx.login code 换取 openid，自动注册
    """
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        openid = f"mock_openid_{body.code[-12:]}"
    else:
        try:
            resp = httpx.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.WECHAT_APPID,
                    "secret": settings.WECHAT_SECRET,
                    "js_code": body.code,
                    "grant_type": "authorization_code",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode", 0) != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"微信登录失败: {data.get('errmsg', '未知错误')}",
                )
            openid = data["openid"]
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="微信服务不可达")

    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        user = User(
            openid=openid,
            nickname=f"用户{random.randint(1000, 9999)}",
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("WeChat new user registered | openid=%s user_id=%d", openid[-12:], user.id)
    else:
        logger.info("WeChat login | user_id=%d", user.id)

    return _make_login_response(user, db)


@router.post("/phone", response_model=LoginOut)
def phone_login(body: PhoneLoginIn, db: Session = Depends(get_db), _rl=Depends(strict_limiter)):
    """
    手机号+密码登录 (商家端/骑手端/管理后台)
    """
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        raise HTTPException(status_code=400, detail="手机号未注册")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="密码错误")
    return _make_login_response(user, db)


@router.post("/register", response_model=LoginOut)
def phone_register(body: PhoneLoginIn, db: Session = Depends(get_db), _rl=Depends(strict_limiter)):
    """手机号注册 (商家/骑手)"""
    existing = db.query(User).filter(User.phone == body.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已注册")

    role = body.role if body.role in ("user", "merchant", "rider") else "user"
    user = User(
        openid=f"phone_{body.phone}",
        nickname=body.phone[-4:],
        phone=body.phone,
        role=role,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _make_login_response(user, db)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.put("/profile", response_model=UserOut)
def update_profile(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户资料（昵称、头像、手机号）"""
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar is not None:
        user.avatar = body.avatar
    if body.phone is not None:
        existing = db.query(User).filter(User.phone == body.phone, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="该手机号已被使用")
        user.phone = body.phone
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/account")
def delete_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """注销当前用户账号（软删除：设置 status=0）"""
    user.status = 0
    user.phone = f"deleted_{user.id}_{user.phone}"  # 释放手机号供重新注册
    db.commit()
    return {"message": "账号已注销。如有未完成订单，请联系客服处理。"}


@router.post("/refresh", response_model=LoginOut)
def refresh_token(body: RefreshIn, db: Session = Depends(get_db)):
    """
    用 refresh_token 换取新的 access_token（自动续期）
    每次 refresh 会轮换 refresh_token（旧 token 立即失效）
    """
    user = db.query(User).filter(User.refresh_token == body.refresh_token).first()
    if not user:
        raise HTTPException(status_code=401, detail="refresh_token 无效")

    # 检查过期（SQLite 不存时区，读出来是 naive datetime，需要类型安全处理）
    expires = user.refresh_token_expires
    if expires is None:
        user.refresh_token = ""
        user.refresh_token_expires = None
        db.commit()
        raise HTTPException(status_code=401, detail="refresh_token 已过期，请重新登录")
    if isinstance(expires, str):
        try:
            expires = datetime.fromisoformat(expires)
        except (ValueError, TypeError):
            user.refresh_token = ""
            user.refresh_token_expires = None
            db.commit()
            raise HTTPException(status_code=401, detail="refresh_token 格式错误，请重新登录")
    # SQLite 不存时区信息 → naive datetime → 补上 UTC
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        user.refresh_token = ""
        user.refresh_token_expires = None
        db.commit()
        raise HTTPException(status_code=401, detail="refresh_token 已过期，请重新登录")

    return _make_login_response(user, db)
