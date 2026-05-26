import asyncio
import contextlib
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import engine, Base
from logger import setup_logging
from middleware import RequestLoggingMiddleware

# 启动日志
setup_logging()
logger = logging.getLogger("app")

# 创建所有表
Base.metadata.create_all(bind=engine)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    from tasks import auto_cancel_pending_orders
    task = asyncio.create_task(auto_cancel_pending_orders())
    logger.info("Background task started: auto_cancel_pending_orders")
    yield
    task.cancel()
    logger.info("Background task stopped")

app = FastAPI(title=settings.APP_NAME, docs_url="/docs", lifespan=lifespan)

# ---- 中间件 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ---- 全局异常处理 ----
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "request_id": getattr(request.state, "request_id", "")},
    )

# ---- 路由注册 ----
from routers.common.auth import router as auth_router
from routers.common.pay import router as pay_router
from routers.common.ws import router as ws_router
from routers.common.upload import router as upload_router
from routers.user.address import router as user_address_router
from routers.user.store import router as user_store_router
from routers.user.order import router as user_order_router
from routers.user.coupon import router as user_coupon_router
from routers.merchant.shop import router as merchant_shop_router
from routers.merchant.menu import router as merchant_menu_router
from routers.merchant.order import router as merchant_order_router
from routers.rider.orders import router as rider_router
from routers.admin.dashboard import router as admin_router

app.include_router(auth_router)
app.include_router(pay_router)
app.include_router(ws_router)
app.include_router(upload_router)
app.include_router(user_address_router)
app.include_router(user_store_router)
app.include_router(user_order_router)
app.include_router(user_coupon_router)
app.include_router(merchant_shop_router)
app.include_router(merchant_menu_router)
app.include_router(merchant_order_router)
app.include_router(rider_router)
app.include_router(admin_router)

# 静态文件
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "外卖平台 API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
