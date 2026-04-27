微信通话录音软件 - 安装程序
========================================

此目录用于存放 Windows 安装程序

由于当前环境是 macOS，无法直接生成 Windows 安装程序。
请在 Windows 系统上完成以下步骤：

1. 先打包 EXE 文件（参考 dist/README.txt）

2. 安装 Inno Setup：
   https://jrsoftware.org/isinfo.php

3. 编译安装脚本：
   - 打开 WeChatRecorder_Setup.iss
   - 点击 Build → Compile
   - 或使用命令行：
     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" WeChatRecorder_Setup.iss

生成的文件：
- output/WeChatRecorder_Setup_v1.0.0.exe - 安装程序
- WeChatRecorder_Setup.exe - 安装程序（复制版）

安装程序功能：
- 安装向导
- 桌面快捷方式
- 开始菜单快捷方式
- 完整卸载支持
