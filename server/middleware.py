"""
请求日志中间件：记录每个请求的方法、路径、耗时和状态码
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        status = response.status_code
        method = request.method
        path = request.url.path

        if status >= 500:
            logger.error("%s %s | %d | %.3fs | %s", method, path, status, elapsed, request_id)
        elif status >= 400:
            logger.warning("%s %s | %d | %.3fs | %s", method, path, status, elapsed, request_id)
        else:
            logger.info("%s %s | %d | %.3fs | %s", method, path, status, elapsed, request_id)

        response.headers["X-Request-ID"] = request_id
        return response
