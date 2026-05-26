import logging
import random
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password
from config import settings
from database import get_db
from models.user import User
from ratelimit import strict_limiter
from schemas.user import LoginOut, UserOut, UserUpdate, WechatLoginIn, PhoneLoginIn

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/common/auth", tags=["公共-认证"])


def _make_login_response(user: User) -> LoginOut:
    """生成登录响应"""
    user.last_login = datetime.now(timezone.utc)
    token = create_access_token(data={"sub": user.id, "role": user.role})
    return LoginOut(token=token, user=UserOut.model_validate(user))


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

    return _make_login_response(user)


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
    return _make_login_response(user)


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
    return _make_login_response(user)


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
