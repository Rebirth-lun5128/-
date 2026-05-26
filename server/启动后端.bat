@echo off
chcp 65001 >nul
title 外卖平台后端 API (端口 8000)
cd /d "%~dp0"

echo ========================================
echo   外卖平台 - 开发环境后端
echo   用户/商家/骑手/管理 四个小程序共用此服务
echo ========================================
echo.

where py >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python。请先安装 Python 3.10+ 并勾选 Add to PATH
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [0/4] 结束占用 8000 端口的旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo.

echo [1/4] 检查依赖...
py -3 -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 初始化测试数据（首次运行会创建数据库和账号）...
py -3 seed.py
echo.

echo [3/4] 启动服务...
echo.
echo   地址: http://localhost:8000
echo   文档: http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo   【重要】请保持本窗口打开，关闭窗口 = 停止后端
echo   按 Ctrl+C 可停止服务
echo ========================================
echo.

py -3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
