# Windows 安装使用指南

> **微信通话录音软件 - Windows 平台完整安装指南**

## 📋 目录

1. [快速开始](#快速开始)
2. [系统要求](#系统要求)
3. [安装方法](#安装方法)
4. [使用方法](#使用方法)
5. [故障排除](#故障排除)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 方式一：一键运行（推荐）

1. 双击运行 `run_windows.bat`
2. 首次运行会自动安装依赖（需要几分钟）
3. 安装完成后自动启动程序

### 方式二：使用安装程序

1. 下载 `WeChatRecorder_Setup.exe`
2. 双击安装
3. 从开始菜单或桌面快捷方式启动

---

## 💻 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 (64位) |
| 内存 | 至少 4GB RAM |
| 磁盘空间 | 至少 500MB 可用空间 |
| Python | 3.8 或更高版本（一键安装包已包含）|
| 微信 | 微信桌面版（Windows 版）|

---

## 📦 安装方法

### 方法一：使用预编译版本（最简单）

1. **下载程序**
   - 从 Releases 页面下载 `WeChatRecorder.exe`
   - 或下载 `WeChatRecorder_Setup.exe` 安装程序

2. **运行程序**
   - 单文件版：双击 `WeChatRecorder.exe`
   - 安装版：运行安装程序，然后从桌面快捷方式启动

### 方法二：使用一键运行脚本

1. **下载源码**
   ```bash
   # 使用 git 克隆
   git clone https://github.com/yourusername/wechat-recorder.git
   
   # 或下载 ZIP 压缩包并解压
   ```

2. **运行脚本**
   - 进入项目文件夹
   - 双击 `run_windows.bat`
   - 首次运行会自动：
     - 检查 Python 环境
     - 创建虚拟环境
     - 安装所有依赖
     - 启动程序

### 方法三：手动安装

如果你希望完全手动控制安装过程：

1. **安装 Python**
   - 访问 https://www.python.org/downloads/
   - 下载 Python 3.9 或更高版本
   - **重要**：安装时勾选 "Add Python to PATH"

2. **创建虚拟环境**
   ```cmd
   cd wechat-recorder
   python -m venv venv
   ```

3. **激活虚拟环境**
   ```cmd
   venv\Scripts\activate.bat
   ```

4. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   ```

5. **运行程序**
   ```cmd
   python main_gui.py
   ```

### 方法四：使用环境初始化脚本

运行自动设置脚本：

```cmd
python setup_windows.py
```

此脚本会自动：
- 检查/安装 Python
- 创建虚拟环境
- 安装依赖
- 检查音频设备
- 创建桌面快捷方式

---

## 🎮 使用方法

### 启动程序

- 双击 `run_windows.bat`
- 或双击桌面快捷方式（如果已创建）

### 基本操作

1. **开始录音**
   - 点击"开始录音"按钮
   - 或启用"自动检测并录制微信通话"

2. **停止录音**
   - 点击"停止录音"按钮
   - 录音文件自动保存到 `recordings` 文件夹

3. **查看录音**
   - 点击"打开录音文件夹"按钮
   - 或在文件资源管理器中打开 `recordings` 文件夹

### 自动录音模式

1. 勾选"自动检测并录制微信通话"
2. 当微信通话开始时，软件自动开始录音
3. 通话结束时，自动保存录音文件
4. 系统托盘会显示通知

### 设置选项

- **输出格式**: WAV (无损) 或 MP3 (需要 FFmpeg)
- **采样率**: 44100 Hz (推荐) / 48000 Hz / 22050 Hz

---

## 🔧 故障排除

### 问题 1：双击 run_windows.bat 闪退

**可能原因**：
- Python 未安装或未添加到 PATH
- 系统权限问题

**解决方法**：
1. 右键点击 `run_windows.bat` → "以管理员身份运行"
2. 或先运行 `python setup_windows.py` 检查环境
3. 检查 Python 是否安装：
   ```cmd
   python --version
   ```

### 问题 2：提示 "未找到 Python"

**解决方法**：
1. 下载并安装 Python 3.9+：
   - 官网：https://www.python.org/downloads/
   - **必须勾选** "Add Python to PATH"

2. 或使用自动安装：
   ```cmd
   python setup_windows.py
   # 选择自动安装 Python
   ```

### 问题 3：依赖安装失败

**可能原因**：网络问题或 pip 版本过旧

**解决方法**：
1. 升级 pip：
   ```cmd
   python -m pip install --upgrade pip
   ```

2. 使用国内镜像：
   ```cmd
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 手动安装依赖：
   ```cmd
   pip install PyQt6 numpy psutil sounddevice comtypes
   ```

### 问题 4：录音没有声音

**检查清单**：

1. **Windows 隐私设置**
   - 设置 → 隐私 → 麦克风
   - 允许应用访问麦克风
   - 允许桌面应用访问麦克风

2. **音频设备**
   - 确保扬声器/耳机正常工作
   - 检查音量不为零
   - 确认默认播放设备正确

3. **WASAPI 支持**
   - Windows 10/11 默认支持 WASAPI Loopback
   - 如果仍有问题，尝试更新声卡驱动

### 问题 5：无法检测微信通话

**可能原因**：
- 微信未运行
- 微信版本不兼容
- 窗口标题检测失败

**解决方法**：
1. 确保微信正在运行
2. 手动开始/停止录音
3. 检查微信版本是否为官方桌面版

### 问题 6：PyQt6 导入错误

**错误信息**：`ImportError: DLL load failed`

**解决方法**：
1. 重新安装 PyQt6：
   ```cmd
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
   pip install PyQt6
   ```

2. 安装 Visual C++ Redistributable：
   - 下载：https://aka.ms/vs/17/release/vc_redist.x64.exe

### 问题 7：sounddevice 初始化失败

**错误信息**：`PortAudioError: Error querying device`

**解决方法**：
1. 重新安装 sounddevice：
   ```cmd
   pip uninstall sounddevice
   pip install sounddevice
   ```

2. 检查音频驱动：
   - 更新声卡驱动
   - 确保有活动的音频设备

### 问题 8：程序启动缓慢

**原因**：单文件 EXE 需要解压

**解决方法**：
- 使用 `--onedir` 模式打包（目录形式，启动更快）
- 或直接使用源码运行

---

## ❓ 常见问题

### Q: 录音文件保存在哪里？

A: 默认保存在程序目录下的 `recordings` 文件夹中：
```
wechat-recorder/
├── recordings/
│   ├── wechat_call_20240115_143022.wav
│   └── ...
```

### Q: 如何转换为 MP3 格式？

A: 需要安装 FFmpeg：
1. 下载 FFmpeg：https://ffmpeg.org/download.html
2. 解压并添加到系统 PATH
3. 在软件中选择 MP3 格式

或使用在线转换工具。

### Q: 录音文件太大怎么办？

A: WAV 格式为无损音频，文件较大。建议：
- 转换为 MP3 格式（压缩率约 10:1）
- 定期清理旧录音文件
- 使用外部存储保存录音

### Q: 支持哪些 Windows 版本？

A: 支持 Windows 10 和 Windows 11 的 64 位版本。
Windows 7/8 可能可以运行，但不保证兼容性。

### Q: 可以录制其他应用的音频吗？

A: 可以。本软件使用 WASAPI Loopback 录制系统音频，
可以录制任何通过扬声器播放的声音。

### Q: 如何卸载？

A: 
- 便携版：直接删除文件夹即可
- 安装版：使用 Windows 的"添加或删除程序"
- 源码版：删除项目文件夹和虚拟环境

### Q: 录音有杂音/音质不好？

A:
1. 检查音频线连接
2. 更新声卡驱动
3. 提高采样率到 48000 Hz
4. 关闭其他占用音频的程序

---

## 📞 获取帮助

如果以上方法无法解决问题：

1. 查看程序日志（在界面下方的日志区域）
2. 提交 Issue 到 GitHub 仓库
3. 联系开发者

---

## 📝 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持 Windows 一键运行
- 自动检测微信通话
- 支持 WAV/MP3 格式

---

## ⚖️ 法律声明

- 录音前请征得对方同意
- 遵守当地法律法规
- 本软件仅供个人合法使用
- 开发者不对滥用行为负责
