# 微信通话录音软件 - 打包说明

## 概述

本文档说明如何将微信通话录音软件打包为 Windows 可执行文件和安装程序。

## 打包输出

打包完成后，将生成以下文件：

### 1. 单文件可执行程序
- **路径**: `dist/WeChatRecorder.exe`
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

### 开发环境（打包用）
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB 可用空间

### 运行环境（用户使用）
- **操作系统**: Windows 10/11 (64位)
- **运行内存**: 至少 2GB RAM
- **磁盘空间**: 至少 100MB 可用空间
- **依赖**: 无需额外安装 Python 或依赖库

## 打包方法

### 方法一：使用一键打包脚本（推荐）

在 Windows 上双击运行或命令行执行：

```batch
build_windows.bat
```

此脚本会自动：
1. 检查并安装依赖
2. 生成应用图标
3. 使用 PyInstaller 打包 EXE
4. 使用 Inno Setup 创建安装程序（如果已安装）

### 方法二：使用 Python 打包脚本

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行打包脚本
python build_installer.py
```

### 方法三：手动分步打包

#### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

#### 步骤 2: 生成图标

```bash
python create_icon.py
```

#### 步骤 3: 打包 EXE

```bash
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
```

#### 步骤 4: 创建安装程序

1. 下载并安装 Inno Setup: https://jrsoftware.org/isinfo.php
2. 打开 `installer/WeChatRecorder_Setup.iss`
3. 点击 Build → Compile
4. 或使用命令行：

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\WeChatRecorder_Setup.iss
```

## 打包配置文件说明

### PyInstaller 配置

**文件**: `wechat_recorder.spec`

主要配置项：
- `APP_NAME`: 应用名称
- `APP_VERSION`: 版本号
- `icon_path`: 图标路径
- `hidden_imports`: 隐式导入的模块
- `excludes`: 排除的模块（减小体积）

### 版本信息

**文件**: `version_info.txt`

包含 Windows 可执行文件的版本信息：
- 公司名称
- 产品名称
- 文件版本
- 版权信息

### Inno Setup 配置

**文件**: `installer/WeChatRecorder_Setup.iss`

主要功能：
- 安装向导界面
- 桌面/开始菜单快捷方式
- 卸载支持
- 多语言支持（简体中文、英文）

## 文件结构

打包后的项目结构：

```
wechat-recorder/
├── app_icon.ico                    # 应用图标
├── version_info.txt                # 版本信息
├── wechat_recorder.spec            # PyInstaller 配置
├── build_windows.bat               # Windows 一键打包脚本
├── build_installer.py              # Python 打包脚本
├── create_icon.py                  # 图标生成脚本
├── requirements.txt                # 依赖列表
├── BUILD.md                        # 本文件
├── dist/                           # 输出目录
│   └── WeChatRecorder.exe          # 单文件可执行程序
├── installer/                      # 安装程序目录
│   ├── WeChatRecorder_Setup.iss    # Inno Setup 脚本
│   ├── WeChatRecorder_Setup.exe    # 生成的安装程序
│   └── output/                     # 编译输出
│       └── WeChatRecorder_Setup_v1.0.0.exe
└── build/                          # 临时构建文件
```

## 安装程序功能

### 安装向导
- 欢迎页面
- 许可协议
- 安装路径选择
- 快捷方式选项
- 安装进度
- 完成页面

### 快捷方式
- 桌面快捷方式（可选）
- 开始菜单快捷方式
- 快速启动栏快捷方式（Windows 7/8）

### 卸载功能
- 控制面板卸载
- 保留用户录音文件
- 清理注册表项

## 常见问题

### Q: 打包后的 EXE 文件很大？

A: 这是正常的。PyInstaller 会将 Python 解释器和所有依赖库打包进去。
- 单文件 EXE 通常在 30-50MB 左右
- 使用 UPX 压缩可以减小约 20-30% 体积
- 可以通过排除不需要的模块来减小体积

### Q: 杀毒软件报毒？

A: 这是 PyInstaller 打包的常见问题：
1. 将软件添加到杀毒软件白名单
2. 使用代码签名证书签名 EXE（需要购买证书）
3. 向杀毒软件厂商提交误报申诉
4. 建议用户从可信来源下载

### Q: 在某些电脑上无法运行？

A: 可能的原因：
1. Windows 版本过低（需要 Windows 10+）
2. 缺少 Visual C++ Redistributable
3. 权限问题（尝试以管理员身份运行）
4. 杀毒软件拦截

### Q: 如何更新版本号？

A: 修改以下文件中的版本号：
1. `build_installer.py` - 脚本中的 APP_VERSION
2. `version_info.txt` - Windows 版本信息
3. `installer/WeChatRecorder_Setup.iss` - 安装程序版本
4. `build_windows.bat` - 批处理脚本中的版本

### Q: 如何自定义安装程序？

A: 编辑 `installer/WeChatRecorder_Setup.iss`：
- 修改 `DefaultDirName` 更改默认安装路径
- 修改 `OutputBaseFilename` 更改输出文件名
- 添加 `[Registry]` 段写入注册表
- 添加 `[Run]` 段安装后运行程序

## 技术细节

### PyInstaller 参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包为单文件 |
| `--windowed` | 隐藏控制台窗口（GUI 应用） |
| `--icon` | 指定应用图标 |
| `--version-file` | 指定版本信息文件 |
| `--add-data` | 添加数据文件 |
| `--hidden-import` | 显式导入模块 |
| `--exclude-module` | 排除不需要的模块 |
| `--upx-dir` | 指定 UPX 压缩工具路径 |

### Inno Setup 功能

- 支持 Windows 10/11
- 自动创建快捷方式
- 完整的卸载支持
- 多语言界面
- 安装前系统检查
- 自定义安装路径
- 安装进度显示

## 发布检查清单

在发布前，请确认：

- [ ] EXE 文件可以正常运行
- [ ] 安装程序可以正常安装
- [ ] 卸载程序可以正常卸载
- [ ] 桌面快捷方式可以正常创建
- [ ] 开始菜单快捷方式可以正常创建
- [ ] 录音功能正常工作
- [ ] 自动检测功能正常工作
- [ ] 版本信息正确显示
- [ ] 图标正确显示

## 联系支持

如有问题，请查看 README.md 或提交 Issue。

---

**版本**: 1.0.0  
**最后更新**: 2024-01-15
