@echo off
chcp 65001 >nul
title 微信通话录音软件 - Windows 打包脚本
echo.
echo ============================================
echo   微信通话录音软件 - Windows 一键打包脚本
echo   WeChat Recorder Build Script v1.0.0
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)
echo     依赖检查完成

echo.
echo [2/5] 生成图标...
python create_icon.py
if errorlevel 1 (
    echo [警告] 图标生成失败，将使用默认图标
)
echo     图标生成完成

echo.
echo [3/5] 打包 EXE...
python -m PyInstaller --name WeChatRecorder --onefile --windowed --noconfirm --clean ^
    --icon app_icon.ico ^
    --version-file version_info.txt ^
    --add-data "app_icon.ico;." ^
    --hidden-import PyQt6.sip ^
    --hidden-import numpy ^
    --hidden-import sounddevice ^
    --hidden-import psutil ^
    --exclude-module matplotlib ^
    --exclude-module tkinter ^
    --exclude-module unittest ^
    main_gui.py

if errorlevel 1 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)
echo     EXE 打包完成

echo.
echo [4/5] 检查输出...
if not exist "dist\WeChatRecorder.exe" (
    echo [错误] 未找到生成的 EXE 文件
    pause
    exit /b 1
)
echo     EXE 文件已生成

REM 获取文件大小
for %%I in (dist\WeChatRecorder.exe) do (
    set size=%%~zI
)
echo     文件大小: %size% 字节

echo.
echo [5/5] 创建安装程序...
echo     检查 Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if exist "C:\Program Files\Inno Setup 5\ISCC.exe" set ISCC="C:\Program Files\Inno Setup 5\ISCC.exe"

if defined ISCC (
    echo     找到 Inno Setup: %ISCC%
    %ISCC% installer\WeChatRecorder_Setup.iss
    if errorlevel 1 (
        echo [警告] 安装程序创建失败
    ) else (
        echo     安装程序创建完成
        if exist "installer\output\WeChatRecorder_Setup_v1.0.0.exe" (
            copy /Y "installer\output\WeChatRecorder_Setup_v1.0.0.exe" "installer\WeChatRecorder_Setup.exe" >nul
        )
    )
) else (
    echo [警告] 未找到 Inno Setup，跳过安装程序创建
    echo     请从 https://jrsoftware.org/isinfo.php 下载安装
)

echo.
echo ============================================
echo   打包完成！
echo ============================================
echo.
echo 输出文件:
echo   - dist\WeChatRecorder.exe (单文件版本)
if exist "installer\WeChatRecorder_Setup.exe" (
echo   - installer\WeChatRecorder_Setup.exe (安装程序)
)
echo.
pause
