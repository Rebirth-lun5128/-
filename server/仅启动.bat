@echo off
chcp 65001 >nul
title 外卖平台后端 API (端口 8000)
cd /d "%~dp0"

echo 快速启动（跳过依赖检查和 seed）...
echo 地址: http://localhost:8000
echo 关闭本窗口即停止后端
echo.

py -3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
