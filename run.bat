@echo off
chcp 65001 >nul
echo ================================================
echo 果感知·智选助手 - 启动脚本
echo ================================================
echo.

echo [1/3] 请确保环境变量已设置...
echo   提示: 请先执行 set DEEPSEEK_API_KEY=你的密钥
echo   当前 DEEPSEEK_API_KEY: %DEEPSEEK_API_KEY%
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
