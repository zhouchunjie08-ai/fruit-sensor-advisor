@echo off
chcp 65001 >nul
echo ================================================
echo 果感知·智选助手 - 启动脚本
echo ================================================
echo.

echo [1/3] 设置环境变量...
set DEEPSEEK_API_KEY=sk-a648b2d898ba49babbe21a2b93053f5d
set BING_API_KEY=
echo   DEEPSEEK_API_KEY: 已设置
echo   BING_API_KEY: %BING_API_KEY%
echo.

echo [2/3] 安装依赖...
cd /d "%~dp0backend"
pip install flask flask-cors requests openai -q
echo.

echo [3/3] 启动后端服务...
echo.
echo 服务地址: http://localhost:5000
echo 前端页面: 打开 frontend/index.html
echo.
echo 按 Ctrl+C 停止服务
echo ================================================

python app.py

pause
