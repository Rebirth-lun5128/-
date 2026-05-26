"""
WebSocket 连接管理器
管理各角色的实时连接，支持按用户/角色推送消息
"""
import asyncio
import json
from typing import Dict, Set, Optional

from fastapi import WebSocket


class ConnectionManager:
    """管理 WebSocket 连接，按 user_id 和 role 分组"""

    def __init__(self):
        self._user_conns: Dict[int, WebSocket] = {}
        self._role_users: Dict[str, Set[int]] = {
            "user": set(), "merchant": set(), "rider": set(), "admin": set(),
        }

    async def connect(self, ws: WebSocket, user_id: int, role: str):
        await ws.accept()
        if user_id in self._user_conns:
            old = self._user_conns[user_id]
            try:
                await old.close(code=4001, reason="new_connection")
            except Exception:
                pass
        self._user_conns[user_id] = ws
        role_set = self._role_users.get(role)
        if role_set is not None:
            role_set.add(user_id)

    def disconnect(self, user_id: int, role: str):
        self._user_conns.pop(user_id, None)
        role_set = self._role_users.get(role)
        if role_set:
            role_set.discard(user_id)

    async def send_to_user(self, user_id: int, data: dict) -> bool:
        ws = self._user_conns.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
                return True
            except Exception:
                return False
        return False

    async def send_to_role(self, role: str, data: dict):
        for user_id in list(self._role_users.get(role, set())):
            await self.send_to_user(user_id, data)

    async def push_order_event(
        self,
        event: str,
        order: dict,
        *,
        user_id: Optional[int] = None,
        merchant_user_id: Optional[int] = None,
        rider_user_id: Optional[int] = None,
        broadcast_role: Optional[str] = None,
    ):
        """推送订单事件给指定角色或广播到某个角色"""
        msg = {"event": event, "order": order}
        if user_id:
            await self.send_to_user(user_id, msg)
        if merchant_user_id:
            await self.send_to_user(merchant_user_id, msg)
        if rider_user_id:
            await self.send_to_user(rider_user_id, msg)
        if broadcast_role:
            await self.send_to_role(broadcast_role, msg)

    # ---- 同步包装 (供同步路由调用) ----

    def push_order_event_sync(
        self,
        event: str,
        order: dict,
        *,
        user_id: Optional[int] = None,
        merchant_user_id: Optional[int] = None,
        rider_user_id: Optional[int] = None,
        broadcast_role: Optional[str] = None,
    ):
        """push_order_event 的同步版本"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.ensure_future(
                self.push_order_event(
                    event, order,
                    user_id=user_id, merchant_user_id=merchant_user_id,
                    rider_user_id=rider_user_id, broadcast_role=broadcast_role,
                )
            )
        else:
            loop.run_until_complete(
                self.push_order_event(
                    event, order,
                    user_id=user_id, merchant_user_id=merchant_user_id,
                    rider_user_id=rider_user_id, broadcast_role=broadcast_role,
                )
            )


manager = ConnectionManager()
