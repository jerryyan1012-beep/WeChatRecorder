#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信通话录音软件 - Windows 环境检查脚本
检查系统是否满足运行要求
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def print_header(text):
    """打印标题"""
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50)


def print_check(name, status, message=""):
    """打印检查结果"""
    symbol = "✓" if status else "✗"
    color = "32" if status else "31"  # 绿色或红色
    print(f"  \033[{color}m[{symbol}] {name}\033[0m")
    if message:
        print(f"      {message}")


def check_os():
    """检查操作系统"""
    print_header("系统信息")
    
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    
    print(f"  操作系统: {system} {release}")
    print(f"  版本号: {version}")
    print(f"  架构: {machine}")
    
    # 检查是否是 Windows
    is_windows = system == "Windows"
    is_64bit = machine in ["AMD64", "x86_64"]
    
    print_check("Windows 系统", is_windows)
    print_check("64位系统", is_64bit)
    
    if not is_windows:
        print("\n  警告: 此软件主要为 Windows 设计")
    
    return is_windows and is_64bit


def check_python():
    """检查 Python 环境"""
    print_header("Python 环境")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"  Python 版本: {version_str}")
    print(f"  Python 路径: {sys.executable}")
    
    is_valid = version >= (3, 8)
    print_check("Python >= 3.8", is_valid, 
                f"当前: {version_str}" if is_valid else f"需要升级 (当前: {version_str})")
    
    return is_valid


def check_dependencies():
    """检查依赖"""
    print_header("依赖检查")
    
    dependencies = {
        "PyQt6": "GUI 框架",
        "numpy": "数值计算",
        "sounddevice": "音频设备",
        "psutil": "进程管理",
        "comtypes": "COM 接口",
    }
    
    all_ok = True
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print_check(f"{dep} ({desc})", True)
        except ImportError:
            print_check(f"{dep} ({desc})", False, "未安装")
            all_ok = False
    
    return all_ok


def check_audio():
    """检查音频设备"""
    print_header("音频设备")
    
    try:
        import sounddevice as sd
        
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        
        print(f"  发现 {len(devices)} 个音频设备")
        
        # 检查 WASAPI
        has_wasapi = any('wasapi' in api.get('name', '').lower() for api in hostapis)
        print_check("WASAPI 支持", has_wasapi)
        
        # 查找 Loopback 设备
        loopback_found = False
        for device in devices:
            name = str(device.get('name', ''))
            if 'Loopback' in name:
                loopback_found = True
                print(f"      - {name}")
        
        print_check("Loopback 设备", loopback_found, 
                    "找到" if loopback_found else "未找到（将使用默认设备）")
        
        return True
        
    except Exception as e:
        print_check("音频检查", False, str(e))
        return False


def check_wechat():
    """检查微信"""
    print_header("微信检查")
    
    try:
        import psutil
        
        wechat_names = ['WeChat.exe', 'WeChatApp.exe', 'wechat.exe']
        wechat_running = False
        
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in wechat_names:
                wechat_running = True
                break
        
        print_check("微信运行状态", wechat_running,
                    "正在运行" if wechat_running else "未运行（请先启动微信）")
        
        return True
        
    except Exception as e:
        print_check("微信检查", False, str(e))
        return False


def check_permissions():
    """检查权限"""
    print_header("权限检查")
    
    # 检查录音目录写入权限
    recordings_path = Path("recordings")
    try:
        recordings_path.mkdir(exist_ok=True)
        test_file = recordings_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        print_check("录音目录写入权限", True)
        can_write = True
    except Exception as e:
        print_check("录音目录写入权限", False, str(e))
        can_write = False
    
    # 检查管理员权限
    is_admin = False
    if os.name == 'nt':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            pass
    
    print_check("管理员权限", is_admin,
                "已获取" if is_admin else "普通用户（通常足够）")
    
    return can_write


def print_summary(results):
    """打印总结"""
    print_header("检查结果总结")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "通过" if passed else "失败"
        color = "32" if passed else "31"
        print(f"  \033[{color}m{check}: {status}\033[0m")
    
    print()
    if all_passed:
        print("  \033[32m✓ 所有检查通过！系统可以正常运行软件。\033[0m")
        print("\n  运行方式:")
        print("    1. 双击 run_windows.bat")
        print("    2. 或执行: python main_gui.py")
    else:
        print("  \033[31m✗ 部分检查未通过，请根据上方提示修复问题。\033[0m")
        print("\n  建议:")
        if not results.get("依赖"):
            print("    - 运行: pip install -r requirements.txt")
        if not results.get("Python"):
            print("    - 升级 Python 到 3.8 或更高版本")
        print("    - 查看 WINDOWS_SETUP.md 获取详细帮助")


def main():
    """主函数"""
    print("\n" + "="*50)
    print("  微信通话录音软件 - 环境检查工具")
    print("="*50)
    
    results = {
        "操作系统": check_os(),
        "Python": check_python(),
        "依赖": check_dependencies(),
        "音频设备": check_audio(),
        "微信": check_wechat(),
        "权限": check_permissions(),
    }
    
    print_summary(results)
    
    print("\n" + "="*50)
    print("  检查完成")
    print("="*50)
    
    # 等待用户按键
    print("\n按回车键退出...")
    input()


if __name__ == "__main__":
    main()
