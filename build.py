"""
打包脚本 - 使用 PyInstaller 生成可执行文件
"""
import os
import sys
import subprocess
import shutil


def clean_build():
    """清理构建目录"""
    dirs_to_remove = ['build', 'dist', '__pycache__', '.pytest_cache']
    files_to_remove = ['*.spec', '*.pyc']
    
    print("清理构建目录...")
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  删除 {dir_name}/")
    
    import glob
    for pattern in files_to_remove:
        for file in glob.glob(pattern):
            os.remove(file)
            print(f"  删除 {file}")


def build_exe(one_file=True, console=False):
    """
    构建可执行文件
    
    Args:
        one_file: True=单文件模式, False=单目录模式
        console: True=显示控制台窗口, False=仅 GUI
    """
    print("\n开始打包...")
    
    # 基本参数
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--name', 'WeChatRecorder',
    ]
    
    # 单文件或单目录
    if one_file:
        cmd.append('--onefile')
    else:
        cmd.append('--onedir')
    
    # 是否显示控制台
    if console:
        cmd.append('--console')
    else:
        cmd.append('--windowed')
    
    # 隐藏导入
    hidden_imports = [
        'pyaudio',
        'sounddevice',
        'numpy',
        'psutil',
        'comtypes',
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # 数据文件
    cmd.extend(['--add-data', 'recordings;recordings'])
    
    # 图标（如果有的话）
    if os.path.exists('icon.ico'):
        cmd.extend(['--icon', 'icon.ico'])
    
    # 主脚本
    cmd.append('main_gui.py')
    
    # 执行打包
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 打包成功!")
        print(f"输出目录: {os.path.abspath('dist')}")
    else:
        print("\n❌ 打包失败!")
        sys.exit(1)


def create_installer():
    """创建安装程序（需要 NSIS）"""
    print("\n创建安装程序...")
    
    nsis_script = """
; NSIS 安装脚本
Name "微信通话录音软件"
OutFile "WeChatRecorder_Setup.exe"
InstallDir "$PROGRAMFILES\\WeChatRecorder"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    File /r "dist\\WeChatRecorder\\*"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\WeChatRecorder"
    CreateShortcut "$SMPROGRAMS\\WeChatRecorder\\WeChatRecorder.lnk" "$INSTDIR\\WeChatRecorder.exe"
    CreateShortcut "$SMPROGRAMS\\WeChatRecorder\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    ; 创建桌面快捷方式
    CreateShortcut "$DESKTOP\\WeChatRecorder.lnk" "$INSTDIR\\WeChatRecorder.exe"
    
    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\WeChatRecorder\\*"
    RMDir "$SMPROGRAMS\\WeChatRecorder"
    Delete "$DESKTOP\\WeChatRecorder.lnk"
SectionEnd
"""
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    # 检查 NSIS 是否安装
    nsis_path = r"C:\Program Files (x86)\NSIS\makensis.exe"
    if not os.path.exists(nsis_path):
        nsis_path = "makensis"
    
    result = subprocess.run([nsis_path, 'installer.nsi'])
    
    if result.returncode == 0:
        print("✅ 安装程序创建成功!")
    else:
        print("❌ 安装程序创建失败（可能需要安装 NSIS）")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='微信通话录音软件打包脚本')
    parser.add_argument('--clean', action='store_true', help='清理构建目录')
    parser.add_argument('--onedir', action='store_true', help='单目录模式（默认单文件）')
    parser.add_argument('--console', action='store_true', help='显示控制台窗口')
    parser.add_argument('--installer', action='store_true', help='创建安装程序')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        return
    
    # 清理旧构建
    clean_build()
    
    # 构建
    build_exe(one_file=not args.onedir, console=args.console)
    
    # 创建安装程序
    if args.installer:
        create_installer()
    
    print("\n" + "="*50)
    print("构建完成!")
    print("="*50)
    print(f"输出位置: {os.path.abspath('dist')}")
    print("\n使用说明:")
    print("1. 将 dist/WeChatRecorder.exe 复制到目标电脑")
    print("2. 双击运行即可")
    print("3. 录音文件将保存在 recordings/ 目录")


if __name__ == '__main__':
    main()
