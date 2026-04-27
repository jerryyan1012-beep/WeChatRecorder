#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信通话录音软件 - 便携版创建脚本
创建一个包含嵌入式 Python 的便携版本，无需用户安装 Python
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import tempfile
from pathlib import Path
from subprocess import run


class PortableBuilder:
    """便携版构建器"""
    
    # Python 嵌入式版本下载链接
    PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip"
    
    def __init__(self):
        self.project_dir = Path.cwd()
        self.build_dir = self.project_dir / "portable_build"
        self.python_dir = self.build_dir / "python"
        self.dist_dir = self.project_dir / "dist_portable"
        
    def clean(self):
        """清理构建目录"""
        print("清理构建目录...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.build_dir.mkdir(parents=True)
        self.dist_dir.mkdir(parents=True)
        print("  ✓ 清理完成")
    
    def download_python(self):
        """下载嵌入式 Python"""
        print("\n下载嵌入式 Python...")
        print(f"  来源: {self.PYTHON_EMBED_URL}")
        
        zip_path = self.build_dir / "python_embed.zip"
        
        try:
            urllib.request.urlretrieve(self.PYTHON_EMBED_URL, zip_path)
            print("  ✓ 下载完成")
            
            # 解压
            print("  解压 Python...")
            self.python_dir.mkdir()
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.python_dir)
            print("  ✓ 解压完成")
            
            # 删除 zip 文件
            zip_path.unlink()
            
        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            print("  请手动下载并解压到 portable_build/python/")
            raise
    
    def setup_python(self):
        """配置 Python 环境"""
        print("\n配置 Python 环境...")
        
        # 修改 python311._pth 文件以启用 site-packages
        pth_file = self.python_dir / "python311._pth"
        if pth_file.exists():
            content = pth_file.read_text(encoding='utf-8')
            # 取消注释 import site
            content = content.replace('#import site', 'import site')
            pth_file.write_text(content, encoding='utf-8')
            print("  ✓ 启用 site-packages")
        
        # 下载 get-pip.py
        print("  下载 pip...")
        get_pip_path = self.python_dir / "get-pip.py"
        urllib.request.urlretrieve(
            "https://bootstrap.pypa.io/get-pip.py",
            get_pip_path
        )
        print("  ✓ 下载完成")
        
        # 安装 pip
        print("  安装 pip...")
        python_exe = self.python_dir / "python.exe"
        result = run([str(python_exe), str(get_pip_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✓ pip 安装完成")
        else:
            print(f"  ✗ pip 安装失败: {result.stderr}")
            raise RuntimeError("pip 安装失败")
        
        # 删除 get-pip.py
        get_pip_path.unlink()
    
    def install_dependencies(self):
        """安装依赖"""
        print("\n安装依赖...")
        
        python_exe = self.python_dir / "python.exe"
        pip_exe = self.python_dir / "Scripts" / "pip.exe"
        
        # 升级 pip
        run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
        
        # 安装依赖
        requirements_file = self.project_dir / "requirements.txt"
        
        # 修改 requirements.txt 排除 wave（内置模块）
        deps = [
            "PyQt6>=6.4.0",
            "numpy>=1.24.0",
            "psutil>=5.9.0",
            "sounddevice>=0.4.6",
            "comtypes>=1.2.0",
        ]
        
        for dep in deps:
            print(f"  安装 {dep}...")
            result = run(
                [str(python_exe), "-m", "pip", "install", dep, "-q"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  警告: {dep} 安装失败，尝试继续...")
        
        print("  ✓ 依赖安装完成")
    
    def copy_project_files(self):
        """复制项目文件"""
        print("\n复制项目文件...")
        
        # 创建应用目录
        app_dir = self.build_dir / "app"
        app_dir.mkdir()
        
        # 复制主要文件
        files_to_copy = [
            "main_gui.py",
            "audio_recorder.py",
            "requirements.txt",
            "README.md",
            "LICENSE",
        ]
        
        for file in files_to_copy:
            src = self.project_dir / file
            if src.exists():
                shutil.copy2(src, app_dir)
                print(f"  ✓ {file}")
        
        # 复制图标
        icon_file = self.project_dir / "app_icon.ico"
        if icon_file.exists():
            shutil.copy2(icon_file, app_dir)
            print("  ✓ app_icon.ico")
        
        # 创建 recordings 目录
        (app_dir / "recordings").mkdir(exist_ok=True)
        print("  ✓ recordings/ 目录")
    
    def create_launcher(self):
        """创建启动器"""
        print("\n创建启动器...")
        
        # 创建批处理文件
        bat_content = '''@echo off
chcp 65001 >nul
title 微信通话录音软件
cd /d "%~dp0"

REM 设置路径
set "PYTHON=python\\python.exe"
set "APP=app\\main_gui.py"

echo.
echo ============================================
echo   微信通话录音软件
echo ============================================
echo.

REM 检查文件
if not exist "%PYTHON%" (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

if not exist "%APP%" (
    echo [错误] 未找到主程序
    pause
    exit /b 1
)

REM 运行程序
echo 正在启动...
"%PYTHON%" "%APP%"

if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)
'''
        
        bat_path = self.build_dir / "启动微信录音软件.bat"
        bat_path.write_text(bat_content, encoding='utf-8')
        print("  ✓ 启动微信录音软件.bat")
        
        # 创建 README
        readme_content = '''# 微信通话录音软件 - 便携版

## 使用方法

1. 双击运行 "启动微信录音软件.bat"
2. 等待程序启动
3. 开始使用

## 目录结构

- `python/` - 嵌入式 Python 环境
- `app/` - 应用程序文件
- `app/recordings/` - 录音文件保存位置

## 注意事项

- 无需安装 Python，所有依赖已包含
- 录音文件保存在 app/recordings/ 目录
- 可直接复制到 U 盘在其他电脑上使用

## 系统要求

- Windows 10/11 (64位)
- 至少 500MB 可用空间
- 麦克风/扬声器正常工作

## 故障排除

如果程序无法启动：
1. 确保 Windows 是 64 位版本
2. 检查是否有杀毒软件拦截
3. 尝试以管理员身份运行
'''
        
        readme_path = self.build_dir / "README.txt"
        readme_path.write_text(readme_content, encoding='utf-8')
        print("  ✓ README.txt")
    
    def package(self):
        """打包为 ZIP"""
        print("\n打包便携版...")
        
        zip_path = self.dist_dir / "WeChatRecorder_Portable.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.build_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)
        
        # 计算文件大小
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ 打包完成: {zip_path}")
        print(f"  文件大小: {size_mb:.1f} MB")
        
        return zip_path
    
    def build(self):
        """完整构建流程"""
        print("="*50)
        print("  微信通话录音软件 - 便携版构建")
        print("="*50)
        
        try:
            self.clean()
            self.download_python()
            self.setup_python()
            self.install_dependencies()
            self.copy_project_files()
            self.create_launcher()
            zip_path = self.package()
            
            print("\n" + "="*50)
            print("  构建成功!")
            print("="*50)
            print(f"\n输出文件: {zip_path}")
            print(f"\n使用方法:")
            print("  1. 解压 ZIP 文件到任意位置")
            print("  2. 双击 '启动微信录音软件.bat'")
            print("  3. 无需安装 Python，即开即用")
            
        except Exception as e:
            print(f"\n  ✗ 构建失败: {e}")
            raise


def main():
    """主函数"""
    if os.name != 'nt':
        print("错误: 便携版仅支持 Windows 系统")
        sys.exit(1)
    
    builder = PortableBuilder()
    builder.build()
    
    print("\n按回车键退出...")
    input()


if __name__ == "__main__":
    main()
