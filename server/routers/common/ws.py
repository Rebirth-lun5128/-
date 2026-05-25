"""WebSocket 端点 — 各角色实时连接"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from database import get_db
from models.user import User
from websocket import manager
from jose import jwt
from config import settings

router = APIRouter(prefix="/ws", tags=["公共-WebSocket"])


def _auth_ws(token: str) -> User:
    """通过 query token 鉴权，返回用户"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise ValueError
    except Exception:
        raise ValueError("无效令牌")

    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.status == 0:
            raise ValueError("用户不存在或已禁用")
        return user
    finally:
        db.close()


@router.websocket("")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    try:
        user = _auth_ws(token)
    except ValueError:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="认证失败")
        return

    await manager.connect(ws, user.id, user.role)
    try:
        while True:
            # 保持连接，接收客户端消息（心跳等）
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text('{"event":"pong"}')
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(user.id, user.role)
