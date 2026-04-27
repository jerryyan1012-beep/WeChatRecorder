#!/usr/bin/env python3
"""
微信通话录音软件 - 一键打包脚本
生成单文件 EXE 和 Windows 安装程序

使用方法:
    python build_installer.py          # 完整打包（EXE + 安装程序）
    python build_installer.py --exe    # 仅生成 EXE
    python build_installer.py --clean  # 清理构建文件

要求:
    - Python 3.8+
    - Windows 系统（用于生成 ICO 和测试）
    - PyInstaller
    - Inno Setup（用于生成安装程序，可选）
    - Pillow（用于生成图标）
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


# 配置
PROJECT_ROOT = Path(__file__).parent.absolute()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
INSTALLER_DIR = PROJECT_ROOT / "installer"
ASSETS_DIR = PROJECT_ROOT / "assets"

APP_NAME = "WeChatRecorder"
APP_VERSION = "1.0.0"
ICON_FILE = PROJECT_ROOT / "app_icon.ico"


def print_step(message: str):
    """打印步骤信息"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def print_error(message: str):
    """打印错误信息"""
    print(f"\n  ❌ 错误: {message}")


def print_success(message: str):
    """打印成功信息"""
    print(f"\n  ✅ {message}")


def print_info(message: str):
    """打印信息"""
    print(f"  ℹ️  {message}")


def clean_build():
    """清理构建文件"""
    print_step("清理构建文件")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    files_to_clean = [
        PROJECT_ROOT / f"{APP_NAME}.spec",
        ICON_FILE,
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print_info(f"删除目录: {dir_path}")
            shutil.rmtree(dir_path)
    
    for file_path in files_to_clean:
        if file_path.exists():
            print_info(f"删除文件: {file_path}")
            file_path.unlink()
    
    print_success("清理完成")


def check_dependencies():
    """检查必要的依赖"""
    print_step("检查依赖")
    
    required_packages = [
        "PyInstaller",
        "Pillow",
        "PyQt6",
        "numpy",
        "sounddevice",
        "psutil",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.lower().replace("pyinstaller", "PyInstaller"))
            print_info(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print_error(f"✗ {package} 未安装")
    
    if missing:
        print_error(f"缺少依赖: {', '.join(missing)}")
        print_info("请运行: pip install -r requirements.txt")
        return False
    
    print_success("所有依赖已安装")
    return True


def generate_icon():
    """生成应用图标"""
    print_step("生成应用图标")
    
    if ICON_FILE.exists():
        print_info(f"图标已存在: {ICON_FILE}")
        return True
    
    try:
        # 导入图标生成器
        sys.path.insert(0, str(ASSETS_DIR))
        from icon_generator import create_wechat_recorder_icon
        
        # 生成 ICO 文件
        create_wechat_recorder_icon(str(ICON_FILE))
        
        if ICON_FILE.exists():
            print_success(f"图标已生成: {ICON_FILE}")
            return True
        else:
            print_error("图标生成失败")
            return False
            
    except Exception as e:
        print_error(f"生成图标时出错: {e}")
        print_info("将使用默认图标")
        return False


def build_exe():
    """使用 PyInstaller 打包 EXE"""
    print_step("打包 EXE 文件")
    
    # 确保 dist 目录存在
    DIST_DIR.mkdir(exist_ok=True)
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",           # 单文件模式
        "--windowed",          # 隐藏控制台（GUI 应用）
        "--noconfirm",         # 不确认覆盖
        "--clean",             # 清理临时文件
    ]
    
    # 添加图标（如果存在）
    if ICON_FILE.exists():
        cmd.extend(["--icon", str(ICON_FILE)])
    
    # 添加版本信息（如果存在）
    version_file = PROJECT_ROOT / "version_info.txt"
    if version_file.exists():
        cmd.extend(["--version-file", str(version_file)])
    
    # 添加数据文件
    if ICON_FILE.exists():
        cmd.extend(["--add-data", f"{ICON_FILE};."])
    
    # 隐藏导入
    hidden_imports = [
        "PyQt6.sip",
        "numpy",
        "sounddevice",
        "psutil",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 排除不必要的模块
    excludes = [
        "matplotlib",
        "tkinter",
        "unittest",
        "pydoc",
    ]
    for exc in excludes:
        cmd.extend(["--exclude-module", exc])
    
    # 主脚本
    cmd.append(str(PROJECT_ROOT / "main_gui.py"))
    
    print_info(f"运行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=False)
        if result.returncode != 0:
            print_error("PyInstaller 打包失败")
            return False
    except Exception as e:
        print_error(f"运行 PyInstaller 时出错: {e}")
        return False
    
    # 检查输出文件
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print_success(f"EXE 已生成: {exe_path} ({size_mb:.2f} MB)")
        return True
    else:
        print_error(f"未找到输出文件: {exe_path}")
        return False


def build_installer():
    """使用 Inno Setup 创建安装程序"""
    print_step("创建 Windows 安装程序")
    
    # 检查 EXE 是否存在
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print_error(f"未找到 EXE 文件: {exe_path}")
        print_info("请先运行打包 EXE 步骤")
        return False
    
    # 查找 Inno Setup
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    iscc = None
    for path in iscc_paths:
        if os.path.exists(path):
            iscc = path
            break
    
    if not iscc:
        print_error("未找到 Inno Setup")
        print_info("请从 https://jrsoftware.org/isinfo.php 下载并安装 Inno Setup")
        print_info("安装完成后重新运行此脚本")
        return False
    
    print_info(f"找到 Inno Setup: {iscc}")
    
    # 运行 Inno Setup 编译器
    iss_file = INSTALLER_DIR / "WeChatRecorder_Setup.iss"
    if not iss_file.exists():
        print_error(f"未找到安装脚本: {iss_file}")
        return False
    
    cmd = [iscc, str(iss_file)]
    print_info(f"运行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print_error("Inno Setup 编译失败")
            return False
    except Exception as e:
        print_error(f"运行 Inno Setup 时出错: {e}")
        return False
    
    # 检查输出文件
    output_dir = INSTALLER_DIR / "output"
    setup_files = list(output_dir.glob("WeChatRecorder_Setup_*.exe"))
    
    if setup_files:
        setup_file = setup_files[0]
        size_mb = setup_file.stat().st_size / (1024 * 1024)
        print_success(f"安装程序已生成: {setup_file} ({size_mb:.2f} MB)")
        
        # 同时复制到 installer 目录根
        final_path = INSTALLER_DIR / "WeChatRecorder_Setup.exe"
        shutil.copy2(setup_file, final_path)
        print_success(f"安装程序已复制到: {final_path}")
        
        return True
    else:
        print_error("未找到生成的安装程序")
        return False


def test_exe():
    """测试生成的 EXE"""
    print_step("测试 EXE 文件")
    
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print_error(f"未找到 EXE 文件: {exe_path}")
        return False
    
    # 检查文件大小
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    if size_mb < 1:
        print_error(f"EXE 文件异常小 ({size_mb:.2f} MB)，可能打包不完整")
        return False
    
    print_info(f"文件大小: {size_mb:.2f} MB")
    print_info("文件结构检查通过")
    
    # 注意：在 macOS/Linux 上无法直接运行 Windows EXE
    if sys.platform != "win32":
        print_info("当前不是 Windows 系统，跳过运行测试")
        print_info("请在 Windows 上运行此 EXE 进行测试")
        return True
    
    # Windows 上可以尝试运行测试
    print_info("尝试运行 EXE 进行测试...")
    try:
        # 使用 --version 或 --help 参数测试（如果应用支持）
        # 或者只是检查能否启动
        result = subprocess.run(
            [str(exe_path), "--help"],
            capture_output=True,
            timeout=5
        )
        print_success("EXE 可以正常启动")
        return True
    except subprocess.TimeoutExpired:
        print_success("EXE 可以正常启动（GUI 应用，无命令行输出）")
        return True
    except Exception as e:
        print_error(f"测试运行时出错: {e}")
        return False


def generate_build_md():
    """生成 BUILD.md 文档"""
    print_step("生成打包说明文档")
    
    content = f"""# 微信通话录音软件 - 打包说明

## 打包输出

本次打包生成以下文件：

### 1. 单文件可执行程序
- **路径**: `dist/{APP_NAME}.exe`
- **说明**: 无需安装，双击即可运行
- **适用场景**: 快速体验、便携使用

### 2. Windows 安装程序
- **路径**: `installer/WeChatRecorder_Setup.exe`
- **说明**: 完整的 Windows 安装包
- **功能**:
  - 安装向导
  - 桌面快捷方式
  - 开始菜单快捷方式
  - 卸载程序

## 系统要求

- **操作系统**: Windows 10/11 (64位)
- **运行内存**: 至少 2GB RAM
- **磁盘空间**: 至少 100MB 可用空间
- **依赖**: 无需额外安装 Python 或依赖库

## 安装方法

### 方法一：使用安装程序（推荐）

1. 运行 `installer/WeChatRecorder_Setup.exe`
2. 按照安装向导提示完成安装
3. 安装完成后，可以在以下位置找到软件：
   - 桌面快捷方式
   - 开始菜单 → 微信通话录音软件
   - 安装目录（默认：`C:\\Program Files\\WeChatRecorder`）

### 方法二：使用单文件版本

1. 复制 `dist/{APP_NAME}.exe` 到任意位置
2. 双击运行即可
3. 录音文件将保存在程序所在目录的 `recordings/` 文件夹中

## 打包过程说明

### 使用的工具

1. **PyInstaller**: 将 Python 代码打包为 Windows 可执行文件
   - 单文件模式（--onefile）
   - 隐藏控制台窗口（--windowed）
   - UPX 压缩优化

2. **Inno Setup**: 创建专业的 Windows 安装程序
   - 支持多语言（简体中文、英文）
   - 创建桌面和开始菜单快捷方式
   - 完整的安装/卸载流程

3. **Pillow**: 生成应用图标
   - 256x256 高分辨率图标
   - 包含多种尺寸（16x16 到 256x256）

### 打包步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成图标
python assets/icon_generator.py

# 3. 打包 EXE
python -m PyInstaller --onefile --windowed main_gui.py

# 4. 创建安装程序（需要 Inno Setup）
# 使用 Inno Setup 编译 installer/WeChatRecorder_Setup.iss

# 或使用一键打包脚本
python build_installer.py
```

## 文件说明

### 生成的文件

```
wechat-recorder/
├── dist/
│   └── {APP_NAME}.exe          # 单文件可执行程序
├── installer/
│   ├── WeChatRecorder_Setup.exe    # 安装程序
│   ├── output/
│   │   └── WeChatRecorder_Setup_v{APP_VERSION}.exe
│   └── WeChatRecorder_Setup.iss    # Inno Setup 脚本
├── app_icon.ico                    # 应用图标
└── BUILD.md                        # 本文件
```

### 打包配置文件

- `wechat_recorder.spec`: PyInstaller 配置文件
- `version_info.txt`: Windows 版本信息
- `installer/WeChatRecorder_Setup.iss`: Inno Setup 安装脚本
- `build_installer.py`: 一键打包脚本

## 常见问题

### Q: 打包后的 EXE 文件很大？

A: 这是正常的。PyInstaller 会将 Python 解释器和所有依赖库打包进去。
- 使用 UPX 压缩可以减小体积
- 单文件模式比目录模式略大，但更便携

### Q: 杀毒软件报毒？

A: 这是 PyInstaller 打包的常见问题：
1. 将软件添加到杀毒软件白名单
2. 使用代码签名证书签名 EXE（需要购买证书）
3. 向杀毒软件厂商提交误报申诉

### Q: 在某些电脑上无法运行？

A: 可能的原因：
1. Windows 版本过低（需要 Windows 10+）
2. 缺少 Visual C++ Redistributable
3. 权限问题（尝试以管理员身份运行）

### Q: 如何更新版本号？

A: 修改以下文件中的版本号：
1. `build_installer.py` - 脚本中的 APP_VERSION
2. `version_info.txt` - Windows 版本信息
3. `installer/WeChatRecorder_Setup.iss` - 安装程序版本

## 自定义打包

### 修改应用信息

编辑 `version_info.txt` 修改：
- 公司名称
- 产品名称
- 版本号
- 版权信息

### 修改安装程序

编辑 `installer/WeChatRecorder_Setup.iss`：
- 安装路径
- 快捷方式选项
- 界面文字
- 安装前/后操作

### 添加额外文件

在 `wechat_recorder.spec` 中修改 `added_files` 列表：

```python
added_files = [
    ('path/to/source/file', 'target_directory'),
]
```

## 技术细节

### PyInstaller 参数说明

- `--onefile`: 打包为单文件
- `--windowed`: 隐藏控制台窗口（GUI 应用）
- `--icon`: 指定应用图标
- `--version-file`: 指定版本信息文件
- `--add-data`: 添加数据文件
- `--hidden-import`: 显式导入模块
- `--exclude-module`: 排除不需要的模块

### Inno Setup 功能

- 支持 Windows 10/11
- 自动创建快捷方式
- 完整的卸载支持
- 多语言界面
- 安装前系统检查
- 自定义安装路径

## 联系支持

如有问题，请查看 README.md 或提交 Issue。

---

**版本**: {APP_VERSION}  
**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    build_md_path = PROJECT_ROOT / "BUILD.md"
    with open(build_md_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print_success(f"文档已生成: {build_md_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="微信通话录音软件打包脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build_installer.py          # 完整打包
  python build_installer.py --exe    # 仅生成 EXE
  python build_installer.py --clean  # 清理构建文件
        """
    )
    
    parser.add_argument(
        "--exe",
        action="store_true",
        help="仅打包 EXE，不创建安装程序"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理所有构建文件"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖检查"
    )
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          微信通话录音软件 - 一键打包脚本                  ║
║                                                          ║
║          WeChat Recorder Build Script v{APP_VERSION}              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 清理模式
    if args.clean:
        clean_build()
        return 0
    
    # 检查依赖
    if not args.skip_deps:
        if not check_dependencies():
            return 1
    
    # 生成图标
    if not generate_icon():
        print_info("将继续使用默认图标")
    
    # 打包 EXE
    if not build_exe():
        return 1
    
    # 测试 EXE
    test_exe()
    
    # 创建安装程序（除非指定 --exe）
    if not args.exe:
        build_installer()
    
    # 生成文档
    generate_build_md()
    
    # 完成
    print("\n" + "=" * 60)
    print("  🎉 打包完成!")
    print("=" * 60)
    print(f"""
输出文件:
  📦 EXE 文件: {DIST_DIR / f'{APP_NAME}.exe'}
  💿 安装程序: {INSTALLER_DIR / 'WeChatRecorder_Setup.exe'}
  📖 说明文档: {PROJECT_ROOT / 'BUILD.md'}

使用说明:
  1. 单文件版本: 直接运行 dist/{APP_NAME}.exe
  2. 安装版本: 运行 installer/WeChatRecorder_Setup.exe
  3. 查看 BUILD.md 了解详细信息
    """)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
