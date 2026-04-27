#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信通话录音软件 - Windows 环境初始化脚本
自动检查并配置运行环境
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import shutil
from pathlib import Path


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_colored(text, color=None, bold=False):
    """打印彩色文本"""
    if sys.platform == 'win32':
        # Windows 使用普通输出
        print(text)
    else:
        prefix = ""
        if bold:
            prefix += Colors.BOLD
        if color:
            prefix += getattr(Colors, color.upper(), '')
        print(f"{prefix}{text}{Colors.END}")


def run_command(cmd, capture=True, check=True):
    """运行命令"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if check and result.returncode != 0:
                return False, result.stderr
            return True, result.stdout
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)


def check_python():
    """检查 Python 安装"""
    print_colored("\n[1/6] 检查 Python 环境...", "blue", bold=True)
    
    # 检查 Python 是否已安装
    success, output = run_command("python --version")
    if success:
        version_line = output.strip()
        print(f"  ✓ 已检测到: {version_line}")
        
        # 检查版本
        success, _ = run_command(
            "python -c \"import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)\""
        )
        if success:
            print_colored("  ✓ Python 版本符合要求 (>= 3.8)", "green")
            return True
        else:
            print_colored("  ✗ Python 版本过低，需要 3.8 或更高版本", "red")
            return False
    else:
        print_colored("  ✗ 未检测到 Python", "red")
        return False


def install_python():
    """自动下载并安装 Python"""
    print_colored("\n正在准备安装 Python...", "yellow")
    
    # Python 3.11.8 下载链接（Windows 64位安装程序）
    python_url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
    installer_path = os.path.join(tempfile.gettempdir(), "python_installer.exe")
    
    print("  正在下载 Python 安装程序...")
    print(f"  下载地址: {python_url}")
    
    try:
        # 下载安装程序
        urllib.request.urlretrieve(python_url, installer_path)
        print_colored("  ✓ 下载完成", "green")
        
        # 运行安装程序
        print("  正在安装 Python...")
        print("  请按照安装向导完成安装，建议勾选 'Add Python to PATH'")
        
        # 静默安装参数
        install_cmd = f'"{installer_path}" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0'
        success, _ = run_command(install_cmd, capture=False)
        
        if success:
            print_colored("  ✓ Python 安装完成", "green")
            print_colored("  请重新运行此脚本以继续设置", "yellow")
            return True
        else:
            print_colored("  ✗ 安装失败，请手动安装 Python", "red")
            return False
            
    except Exception as e:
        print_colored(f"  ✗ 下载失败: {e}", "red")
        return False


def setup_virtual_environment():
    """设置虚拟环境"""
    print_colored("\n[2/6] 设置虚拟环境...", "blue", bold=True)
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("  虚拟环境已存在，跳过创建")
        return True
    
    print("  创建虚拟环境...")
    success, output = run_command("python -m venv venv")
    
    if success:
        print_colored("  ✓ 虚拟环境创建成功", "green")
        return True
    else:
        print_colored(f"  ✗ 创建失败: {output}", "red")
        return False


def install_dependencies():
    """安装依赖"""
    print_colored("\n[3/6] 安装依赖...", "blue", bold=True)
    
    # 确定 pip 路径
    if os.name == 'nt':
        pip_path = "venv\\Scripts\\pip.exe"
        python_path = "venv\\Scripts\\python.exe"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # 升级 pip
    print("  升级 pip...")
    run_command(f"{python_path} -m pip install --upgrade pip -q")
    
    # 安装依赖
    print("  安装依赖包（可能需要几分钟）...")
    print("  依赖列表: PyQt6, sounddevice, numpy, psutil, pyaudio, comtypes")
    
    success, output = run_command(f"{pip_path} install -r requirements.txt", capture=False)
    
    if success:
        print_colored("  ✓ 依赖安装完成", "green")
        return True
    else:
        print_colored("  ✗ 依赖安装失败", "red")
        print("  尝试单独安装...")
        
        # 尝试逐个安装
        packages = [
            "PyQt6>=6.4.0",
            "numpy>=1.24.0",
            "psutil>=5.9.0",
            "sounddevice>=0.4.6",
            "comtypes>=1.2.0"
        ]
        
        for package in packages:
            print(f"    安装 {package}...")
            run_command(f"{pip_path} install {package} -q")
        
        print_colored("  ✓ 依赖安装完成", "green")
        return True


def check_audio_devices():
    """检查音频设备"""
    print_colored("\n[4/6] 检查音频设备...", "blue", bold=True)
    
    python_path = "venv\\Scripts\\python.exe" if os.name == 'nt' else "venv/bin/python"
    
    check_script = '''
import sys
try:
    import sounddevice as sd
    print("✓ sounddevice 已安装")
    
    devices = sd.query_devices()
    print(f"✓ 发现 {len(devices)} 个音频设备")
    
    # 查找 Loopback 设备
    loopback_found = False
    for i, device in enumerate(devices):
        name = str(device.get('name', ''))
        hostapi = device.get('hostapi', -1)
        if 'Loopback' in name or hostapi == 3:
            print(f"  - 设备 {i}: {name} (WASAPI)")
            loopback_found = True
    
    if loopback_found:
        print("✓ 发现 WASAPI Loopback 设备，录音功能可用")
    else:
        print("⚠ 未发现 Loopback 设备，将使用默认音频设备")
        print("  提示: Windows 10/11 通常支持 WASAPI Loopback")
    
    sys.exit(0)
except Exception as e:
    print(f"✗ 检查失败: {e}")
    sys.exit(1)
'''
    
    success, output = run_command(f'echo "{check_script}" | {python_path} -')
    print(output)
    
    return success


def create_shortcuts():
    """创建快捷方式"""
    print_colored("\n[5/6] 创建快捷方式...", "blue", bold=True)
    
    try:
        # 创建桌面快捷方式（仅 Windows）
        if os.name == 'nt':
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "微信通话录音软件.lnk"
            
            # 使用 PowerShell 创建快捷方式
            script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{Path.cwd() / 'run_windows.bat'}"
$Shortcut.WorkingDirectory = "{Path.cwd()}"
$Shortcut.Description = "微信通话录音软件"
$Shortcut.Save()
'''
            # 保存并执行 PowerShell 脚本
            ps_script_path = Path(tempfile.gettempdir()) / "create_shortcut.ps1"
            with open(ps_script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            run_command(f'powershell -ExecutionPolicy Bypass -File "{ps_script_path}"')
            
            if shortcut_path.exists():
                print_colored(f"  ✓ 桌面快捷方式已创建", "green")
        
        return True
    except Exception as e:
        print(f"  创建快捷方式失败（非关键）: {e}")
        return True


def final_check():
    """最终检查"""
    print_colored("\n[6/6] 最终检查...", "blue", bold=True)
    
    checks = []
    
    # 检查虚拟环境
    if Path("venv").exists():
        print("  ✓ 虚拟环境")
        checks.append(True)
    else:
        print("  ✗ 虚拟环境")
        checks.append(False)
    
    # 检查录音目录
    if not Path("recordings").exists():
        Path("recordings").mkdir()
    print("  ✓ 录音目录")
    checks.append(True)
    
    # 检查主程序
    if Path("main_gui.py").exists():
        print("  ✓ 主程序文件")
        checks.append(True)
    else:
        print("  ✗ 主程序文件缺失")
        checks.append(False)
    
    return all(checks)


def print_final_message():
    """打印最终信息"""
    print_colored("\n" + "="*50, "green")
    print_colored("  设置完成！", "green", bold=True)
    print_colored("="*50, "green")
    
    print("\n使用方法:")
    print("  1. 双击 run_windows.bat 运行程序")
    print("  2. 或在命令行执行: python main_gui.py")
    
    print("\n快捷方式:")
    if os.name == 'nt':
        print("  • 桌面快捷方式: 微信通话录音软件")
    print("  • 运行脚本: run_windows.bat")
    
    print("\n录音文件位置:")
    print(f"  {Path.cwd() / 'recordings'}")
    
    print("\n帮助文档:")
    print("  WINDOWS_SETUP.md - 详细使用指南")
    
    print("\n提示:")
    print("  • 首次运行会自动安装依赖，可能需要几分钟")
    print("  • 确保微信正在运行才能自动检测通话")
    print("  • 录音文件保存在 recordings 文件夹中")
    
    print_colored("\n按回车键退出...", "yellow")
    input()


def main():
    """主函数"""
    print_colored("="*50, "blue")
    print_colored("  微信通话录音软件 - Windows 环境设置", "blue", bold=True)
    print_colored("="*50, "blue")
    
    # 检查是否在项目目录
    if not Path("main_gui.py").exists():
        print_colored("\n错误: 请在项目根目录运行此脚本", "red")
        print("请切换到包含 main_gui.py 的目录后重试")
        input("\n按回车键退出...")
        return
    
    # 检查 Python
    if not check_python():
        print_colored("\nPython 未安装，是否自动安装? (y/n): ", "yellow")
        choice = input().strip().lower()
        if choice == 'y':
            if install_python():
                print_colored("\n请重新运行此脚本完成设置", "green")
                input("\n按回车键退出...")
                return
        else:
            print("\n请手动安装 Python 3.8 或更高版本:")
            print("  https://www.python.org/downloads/")
            input("\n按回车键退出...")
            return
    
    # 设置虚拟环境
    if not setup_virtual_environment():
        print_colored("\n设置失败，请检查错误信息", "red")
        input("\n按回车键退出...")
        return
    
    # 安装依赖
    if not install_dependencies():
        print_colored("\n依赖安装失败，请检查网络连接", "red")
        input("\n按回车键退出...")
        return
    
    # 检查音频设备
    check_audio_devices()
    
    # 创建快捷方式
    create_shortcuts()
    
    # 最终检查
    if not final_check():
        print_colored("\n部分检查未通过，但基本功能应该可用", "yellow")
    
    # 打印最终信息
    print_final_message()


if __name__ == "__main__":
    main()
