# 微信通话录音软件

一款简单易用的 Windows 微信通话录音工具，支持自动检测通话、录制双方声音、导出 WAV/MP3 格式。

## 功能特点

- 🎙️ **自动检测** - 智能检测微信通话开始/结束
- 🔊 **双声道录音** - 同时录制双方声音
- 📁 **多种格式** - 支持 WAV 和 MP3 输出
- 🖥️ **简洁界面** - 直观的 GUI，易于操作
- 🔔 **系统托盘** - 后台运行，不打扰工作
- ⚙️ **自动录音** - 可选通话自动开始录音

## 系统要求

- Windows 10/11 (64位)
- 微信桌面版
- 麦克风/扬声器正常工作

## 🚀 快速开始（Windows）

### 方式一：一键运行（推荐）

1. 下载项目源码
2. 双击 `run_windows.bat`
3. 首次运行自动安装依赖，之后直接使用

### 方式二：环境检查 + 自动设置

```bash
# 1. 检查系统环境
python check_windows.py

# 2. 自动设置环境（安装依赖、创建快捷方式）
python setup_windows.py

# 3. 运行程序
python main_gui.py
```

### 方式三：便携版（无需安装 Python）

1. 下载 `WeChatRecorder_Portable.zip`
2. 解压到任意位置
3. 双击 `启动微信录音软件.bat`

### 方式四：使用预编译 EXE

1. 下载 `WeChatRecorder.exe` 或 `WeChatRecorder_Setup.exe`
2. 双击运行（单文件版）或安装后运行

## 详细安装方法

### 方法一：一键运行脚本

适合大多数用户，自动处理所有依赖：

```bash
# 下载项目后，直接运行
run_windows.bat
```

首次运行会：
- 检查 Python 环境
- 创建虚拟环境
- 自动安装所有依赖
- 启动程序

### 方法二：从源码运行

适合开发者或需要自定义的用户：

```bash
# 1. 克隆/下载项目
cd wechat-recorder

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate.bat  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main_gui.py
```

### 方法三：自行打包

```bash
# 安装依赖
pip install -r requirements.txt

# 打包为单文件 EXE
python build.py

# 或打包为目录（启动更快）
python build.py --onedir

# 创建安装程序（需要 NSIS）
python build.py --installer

# 创建便携版（嵌入式 Python）
python create_portable.py
```

## 使用说明

### 基本操作

1. **启动软件** - 运行 `WeChatRecorder.exe`
2. **开始录音** - 点击"开始录音"按钮
3. **停止录音** - 点击"停止录音"按钮
4. **查看录音** - 点击"打开录音文件夹"

### 自动录音模式

1. 勾选"自动检测并录制微信通话"
2. 当微信通话开始时，软件自动开始录音
3. 通话结束时，自动保存录音文件
4. 系统托盘会显示通知

### 设置选项

- **输出格式**: WAV (无损) 或 MP3 (需要 FFmpeg)
- **采样率**: 44100 Hz (推荐) / 48000 Hz / 22050 Hz

## 录音文件位置

录音文件默认保存在软件目录下的 `recordings/` 文件夹中：

```
wechat-recorder/
├── recordings/
│   ├── wechat_call_20240115_143022.wav
│   ├── wechat_call_20240115_145511.wav
│   └── ...
```

## 技术原理

### 音频捕获

使用 **WASAPI Loopback** 技术捕获系统输出音频：

- 无需虚拟声卡
- 直接录制扬声器输出
- 包含双方通话声音

### 通话检测

- 检测微信进程运行状态
- 分析微信窗口标题
- 识别通话关键词（"语音通话"、"视频通话"等）

## 常见问题

### Q: 录音没有声音？

A: 请检查：
1. Windows 隐私设置中允许应用访问麦克风
2. 扬声器/耳机已连接并正常工作
3. 微信通话音量不为零

### Q: 如何转换为 MP3？

A: 需要安装 FFmpeg：
1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 添加到系统 PATH
3. 在软件中选择 MP3 格式

### Q: 自动检测不准确？

A: 自动检测基于窗口标题分析，可能受以下因素影响：
- 微信版本更新
- 系统语言设置
- 窗口管理器干扰

建议手动控制录音以确保可靠性。

### Q: 录音文件太大？

A: WAV 格式为无损音频，文件较大。如需减小体积：
1. 转换为 MP3 格式
2. 降低采样率（不推荐，可能影响音质）

## 注意事项

⚠️ **法律声明**

- 录音前请征得对方同意
- 遵守当地法律法规
- 本软件仅供个人合法使用
- 开发者不对滥用行为负责

## 技术栈

- **GUI**: PyQt6
- **音频捕获**: sounddevice + WASAPI Loopback
- **进程检测**: psutil
- **打包**: PyInstaller

## 项目结构

```
wechat-recorder/
├── main_gui.py              # GUI 主程序
├── audio_recorder.py        # 音频录制模块
├── build.py                 # 打包脚本
├── build_windows.bat        # Windows 打包脚本
├── create_portable.py       # 便携版创建脚本
├── run_windows.bat          # Windows 一键运行脚本 ⭐
├── setup_windows.py         # Windows 环境设置脚本 ⭐
├── check_windows.py         # Windows 环境检查脚本 ⭐
├── WINDOWS_SETUP.md         # Windows 详细安装指南 ⭐
├── requirements.txt         # 依赖列表
├── README.md                # 使用说明
└── recordings/              # 录音文件目录
```

## Windows 用户专属文件

| 文件 | 用途 |
|------|------|
| `run_windows.bat` | **一键运行** - 双击即可运行，自动处理依赖 |
| `setup_windows.py` | **环境设置** - 检查并自动配置运行环境 |
| `check_windows.py` | **环境检查** - 检查系统是否满足要求 |
| `create_portable.py` | **创建便携版** - 生成无需 Python 的便携版本 |
| `WINDOWS_SETUP.md` | **详细指南** - 完整的安装使用说明 |

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 支持手动/自动录音
- 支持 WAV/MP3 格式
- 系统托盘支持

## 许可证

MIT License - 详见 LICENSE 文件

## 联系方式

如有问题或建议，欢迎提交 Issue。
