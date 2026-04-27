# Windows Defender 误报解决方案

## 问题
WeChatRecorder.exe 被 Windows Defender 拦截，这是常见的误报现象。

## 原因
PyInstaller 打包的 EXE 文件容易被杀毒软件误报为病毒/木马。

## 解决方案

### 方法 1：添加排除项（推荐）

1. 打开 **Windows 安全中心**
2. 点击 **病毒和威胁防护**
3. 点击 **管理设置**
4. 找到 **排除项**，点击 **添加或删除排除项**
5. 点击 **添加排除项** → **文件夹**
6. 选择 WeChatRecorder.exe 所在的文件夹

### 方法 2：临时关闭实时保护

1. 打开 **Windows 安全中心**
2. 点击 **病毒和威胁防护**
3. 点击 **管理设置**
4. 关闭 **实时保护**（临时）
5. 运行 WeChatRecorder.exe
6. 重新开启实时保护

### 方法 3：使用源码运行（最安全）

如果不信任 EXE，可以直接使用 Python 源码运行：

```batch
# 1. 安装 Python 3.11
# 2. 打开命令提示符
cd WeChatRecorder
pip install -r requirements.txt
python main_gui.py
```

## 验证文件安全性

你可以将 EXE 文件上传到以下网站进行病毒扫描：
- https://www.virustotal.com/

## 说明

本软件是开源的，所有代码都在 GitHub 上可见：
https://github.com/jerryyan1012-beep/WeChatRecorder

如果不放心，建议使用方法 3 直接运行源码。
