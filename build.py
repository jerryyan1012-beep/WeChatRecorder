"""
构建脚本 - 生成带有版本信息和图标的 Windows EXE
"""
import os
import sys
import subprocess
import argparse


def create_icon():
    """创建应用程序图标"""
    try:
        from PIL import Image, ImageDraw
        
        # 创建图标目录
        os.makedirs('assets', exist_ok=True)
        
        # 创建 256x256 图标
        size = 256
        img = Image.new('RGBA', (size, size), color=(59, 130, 246, 255))
        draw = ImageDraw.Draw(img)
        
        # 绘制简单的麦克风图标
        mic_color = (255, 255, 255, 255)
        center_x, center_y = size // 2, size // 2
        
        # 麦克风头
        head_radius = 50
        draw.ellipse([center_x - head_radius, center_y - 60 - head_radius,
                      center_x + head_radius, center_y - 60 + head_radius], 
                     fill=mic_color)
        
        # 麦克风身体
        body_width, body_height = 40, 70
        draw.rounded_rectangle([center_x - body_width//2, center_y - 60,
                                center_x + body_width//2, center_y + 20],
                               radius=10, fill=mic_color)
        
        # 底座
        base_width, base_height = 80, 15
        draw.rounded_rectangle([center_x - base_width//2, center_y + 50,
                                center_x + base_width//2, center_y + 50 + base_height],
                               radius=5, fill=mic_color)
        
        # 连接线
        draw.rectangle([center_x - 8, center_y + 20, center_x + 8, center_y + 50], fill=mic_color)
        
        # 保存为多尺寸图标
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        icon_images = []
        
        for icon_size in icon_sizes:
            icon_img = img.resize(icon_size, Image.Resampling.LANCZOS)
            icon_images.append(icon_img)
        
        # 保存 ICO 文件
        ico_path = 'assets/icon.ico'
        icon_images[0].save(ico_path, format='ICO', sizes=[(s[0], s[1]) for s in icon_sizes])
        
        print(f"✓ 图标已创建: {ico_path}")
        return ico_path
        
    except ImportError:
        print("⚠️ 未安装 Pillow，跳过图标创建")
        return None
    except Exception as e:
        print(f"⚠️ 图标创建失败: {e}")
        return None


def build_exe(onefile=True, windowed=True, console=False):
    """构建 EXE 文件"""
    
    # 确保资源目录存在
    os.makedirs('assets', exist_ok=True)
    
    # 创建图标（如果不存在）
    icon_path = 'assets/icon.ico'
    if not os.path.exists(icon_path):
        icon_path = create_icon()
    
    # 构建 PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--name', 'WeChatRecorder',
        '--clean',
    ]
    
    if onefile:
        cmd.append('--onefile')
    else:
        cmd.append('--onedir')
    
    if windowed:
        cmd.append('--windowed')
    
    if console:
        cmd.append('--console')
    
    # 添加图标
    if icon_path and os.path.exists(icon_path):
        cmd.extend(['--icon', icon_path])
        print(f"使用图标: {icon_path}")
    
    # 添加版本信息
    version_file = 'assets/version_info.txt'
    if os.path.exists(version_file):
        cmd.extend(['--version-file', version_file])
        print(f"使用版本信息: {version_file}")
    
    # 添加 PyQt6 依赖
    cmd.extend([
        '--collect-all', 'PyQt6',
        '--collect-all', 'PyQt6-Qt6',
        '--collect-all', 'sounddevice',
        '--collect-all', 'numpy',
        '--hidden-import', 'sounddevice',
        '--hidden-import', 'numpy',
        '--hidden-import', '_sounddevice_data',
        '--hidden-import', '_sounddevice',
    ])
    
    # 主程序
    cmd.append('main_gui.py')
    
    print(f"\n构建命令: {' '.join(cmd)}\n")
    
    # 执行构建
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 构建成功!")
        exe_path = os.path.join('dist', 'WeChatRecorder.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"   输出: {exe_path}")
            print(f"   大小: {size:.1f} MB")
    else:
        print("\n❌ 构建失败")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description='构建 WeChatRecorder EXE')
    parser.add_argument('--onedir', action='store_true', help='使用目录模式而非单文件')
    parser.add_argument('--console', action='store_true', help='显示控制台窗口')
    
    args = parser.parse_args()
    
    print("🔧 WeChatRecorder 构建脚本")
    print("=" * 50)
    
    success = build_exe(
        onefile=not args.onedir,
        windowed=not args.console,
        console=args.console
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
