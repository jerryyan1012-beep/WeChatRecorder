@echo off
chcp 65001 >nul
title 微信通话录音软件 - 一键运行
echo.
echo ============================================
echo   微信通话录音软件 - Windows 一键运行脚本
echo   WeChat Recorder v1.0.0
echo ============================================
echo.

REM 设置工作目录为脚本所在目录
cd /d "%~dp0"

REM 检查 Python 是否已安装
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未检测到 Python！
    echo.
    echo 请选择以下方式之一安装 Python：
    echo.
    echo 方式1 - 自动下载安装（推荐）：
    echo   运行 setup_windows.py 脚本：
    echo   python setup_windows.py
echo.
    echo 方式2 - 手动安装：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载 Python 3.9 或更高版本
    echo   3. 安装时勾选 "Add Python to PATH"
    echo   4. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo     已检测到: %PYTHON_VERSION%

REM 检查 Python 版本是否 >= 3.8
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 版本过低，需要 3.8 或更高版本
    pause
    exit /b 1
)
echo     Python 版本检查通过

REM 检查并创建虚拟环境
echo.
echo [2/4] 检查虚拟环境...
if not exist "venv" (
    echo     创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo     虚拟环境创建完成
) else (
    echo     虚拟环境已存在
)

REM 激活虚拟环境
call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)
echo     虚拟环境已激活

REM 检查并安装依赖
echo.
echo [3/4] 检查依赖...
set NEED_INSTALL=0

REM 检查关键依赖是否已安装
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1
python -c "import sounddevice" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1
python -c "import numpy" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1
python -c "import psutil" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

if %NEED_INSTALL%==1 (
    echo     正在安装依赖（首次运行需要几分钟）...
    echo     请耐心等待...
    echo.
    
    REM 升级 pip
    python -m pip install --upgrade pip -q
    
    REM 安装依赖
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo.
        echo [错误] 安装依赖失败，尝试完整输出模式安装...
        echo.
        pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [错误] 依赖安装失败，请检查网络连接
            pause
            exit /b 1
        )
    )
    echo     依赖安装完成
) else (
    echo     所有依赖已安装
)

REM 创建录音目录
echo.
echo [4/4] 初始化...
if not exist "recordings" (
    mkdir recordings
    echo     创建录音目录
)

REM 检查 Windows 音频设备
echo     检查音频设备...
python -c "import sounddevice as sd; devices = sd.query_devices(); loopback_found = any('Loopback' in str(d) or d.get('hostapi') == 3 for d in devices); print('    音频设备检查' + ('通过' if loopback_found else '完成（将使用默认设备）'))" 2>nul

echo.
echo ============================================
echo   启动程序...
echo ============================================
echo.
echo 提示：
echo   - 录音文件将保存在 recordings 文件夹中
echo   - 首次使用请确保微信正在运行
echo   - 如遇问题请查看 WINDOWS_SETUP.md
echo.

REM 运行程序
python main_gui.py

REM 捕获退出码
set EXIT_CODE=%errorlevel%

REM 退出虚拟环境
call venv\Scripts\deactivate.bat >nul 2>&1

echo.
if %EXIT_CODE%==0 (
    echo 程序正常退出
) else (
    echo 程序异常退出，错误码: %EXIT_CODE%
    echo 如遇问题，请查看 WINDOWS_SETUP.md 中的故障排除部分
)
echo.
pause
