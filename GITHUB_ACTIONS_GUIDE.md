# GitHub Actions 自动打包指南

本文档介绍如何使用 GitHub Actions 自动打包微信通话录音软件。

## 目录

- [触发方式](#触发方式)
- [打包输出](#打包输出)
- [使用方法](#使用方法)
- [下载结果](#下载结果)
- [创建 Release](#创建-release)
- [故障排除](#故障排除)

---

## 触发方式

### 方式一：手动触发 (推荐)

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 在左侧选择 **Build WeChatRecorder** 工作流
4. 点击 **Run workflow** 按钮
5. 填写参数（可选）：
   - **版本号**: 如 `1.0.0`（留空则使用默认版本）
   - **创建 GitHub Release**: 勾选则在打包完成后自动创建 Release
6. 点击 **Run workflow** 开始打包

### 方式二：推送标签触发

```bash
# 1. 创建新标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 2. 推送标签到 GitHub
git push origin v1.0.0
```

推送标签后，GitHub Actions 会自动开始打包，并创建对应的 Release。

---

## 打包输出

工作流会生成以下文件：

### 1. WeChatRecorder.exe (单文件绿色版)
- **说明**: 无需安装，双击即可运行
- **适用场景**: 快速体验、便携使用
- **大小**: 约 30-50 MB

### 2. WeChatRecorder_Setup.exe (安装程序)
- **说明**: 完整的 Windows 安装包
- **功能**:
  - 安装向导
  - 桌面快捷方式
  - 开始菜单快捷方式
  - 卸载程序
- **大小**: 约 30-50 MB

---

## 使用方法

### 首次设置

1. **Fork 或推送代码到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/wechat-recorder.git
   git push -u origin main
   ```

2. **确保工作流文件已提交**
   ```bash
   ls .github/workflows/build.yml
   ```

3. **授予 Actions 写入权限**（用于创建 Release）
   - 进入仓库 **Settings** → **Actions** → **General**
   - 找到 **Workflow permissions**
   - 选择 **Read and write permissions**
   - 点击 **Save**

### 执行打包

#### 手动打包

1. 进入仓库的 **Actions** 页面
2. 选择 **Build WeChatRecorder**
3. 点击 **Run workflow**
4. 等待约 5-10 分钟

#### 自动打包（推荐用于发布）

```bash
# 更新版本号
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

---

## 下载结果

### 方式一：从 Artifacts 下载

1. 进入工作流的运行详情页面
2. 滚动到页面底部的 **Artifacts** 区域
3. 下载以下文件：
   - `WeChatRecorder-EXE-v{版本号}` - 单文件版本
   - `WeChatRecorder-Setup-v{版本号}` - 安装程序
4. 解压 ZIP 文件即可使用

> **注意**: Artifacts 默认保留 30 天

### 方式二：从 Release 下载（推荐）

如果打包时选择了创建 Release：

1. 进入仓库的 **Releases** 页面
2. 找到对应的版本
3. 下载 Assets 中的文件

---

## 创建 Release

### 自动创建

推送标签时自动创建：

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 手动触发时创建

在手动运行工作流时勾选 **创建 GitHub Release** 选项。

### Release 内容

自动创建的 Release 包含：
- 版本号标题
- 详细的发布说明
- 两个可下载文件：
  - `WeChatRecorder.exe`
  - `WeChatRecorder_Setup.exe`
- 构建信息和提交哈希

---

## 工作流配置说明

### 触发条件 (on)

```yaml
on:
  workflow_dispatch:    # 手动触发
  push:
    tags:
      - 'v*'            # 推送 v 开头的标签
```

### 构建环境

- **运行器**: `windows-latest`
- **Python 版本**: 3.11
- **打包工具**: PyInstaller + Inno Setup

### 构建步骤

1. 检出代码
2. 设置 Python 环境
3. 安装依赖
4. 使用 PyInstaller 打包 EXE
5. 使用 Inno Setup 创建安装程序
6. 上传 Artifact
7. （可选）创建 GitHub Release

---

## 故障排除

### 问题：工作流运行失败

**检查清单**:
- [ ] 代码是否已推送到 GitHub？
- [ ] `.github/workflows/build.yml` 是否存在？
- [ ] `requirements.txt` 是否包含所有依赖？
- [ ] `wechat_recorder.spec` 是否存在？
- [ ] `installer/WeChatRecorder_Setup.iss` 是否存在？

### 问题：EXE 文件无法运行

**可能原因**:
- 杀毒软件拦截（PyInstaller 打包的常见问题）
- Windows 版本过低（需要 Windows 10+）
- 缺少 Visual C++ Redistributable

**解决方案**:
1. 将软件添加到杀毒软件白名单
2. 安装 Visual C++ Redistributable
3. 以管理员身份运行

### 问题：安装程序无法创建

**检查**:
- Inno Setup 是否正确安装
- `installer/WeChatRecorder_Setup.iss` 是否存在
- `dist/WeChatRecorder.exe` 是否成功生成

### 查看日志

1. 进入 Actions 页面
2. 点击失败的运行记录
3. 展开失败的步骤查看详细日志

---

## 自定义配置

### 修改 Python 版本

编辑 `.github/workflows/build.yml`:
```yaml
env:
  PYTHON_VERSION: '3.10'  # 修改为需要的版本
```

### 修改应用名称

编辑工作流文件中的 `APP_NAME`:
```yaml
env:
  APP_NAME: YourAppName
```

### 添加额外的构建步骤

在 `build.yml` 的 `steps` 部分添加自定义步骤。

---

## 安全注意事项

1. **Token 权限**: 工作流使用 `GITHUB_TOKEN` 创建 Release，无需额外配置
2. **Artifact 保留**: 默认 30 天后自动删除，重要版本请下载备份
3. **代码签名**: 当前未配置代码签名，杀毒软件可能报毒

---

## 相关文件

- `.github/workflows/build.yml` - GitHub Actions 工作流配置
- `wechat_recorder.spec` - PyInstaller 打包配置
- `installer/WeChatRecorder_Setup.iss` - Inno Setup 安装脚本
- `requirements.txt` - Python 依赖列表

---

## 参考链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyInstaller 文档](https://pyinstaller.org/)
- [Inno Setup 官网](https://jrsoftware.org/isinfo.php)
