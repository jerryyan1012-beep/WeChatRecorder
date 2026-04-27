; Inno Setup 安装脚本 - 微信通话录音软件
; 需要安装 Inno Setup: https://jrsoftware.org/isinfo.php

#define MyAppName "微信通话录音软件"
#define MyAppNameEn "WeChatRecorder"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "WeChat Recorder Team"
#define MyAppURL "https://github.com/yourusername/wechat-recorder"
#define MyAppExeName "WeChatRecorder.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".wcr"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; 应用信息
AppId={{8A3F2B1C-5D7E-4F6A-9B0C-1D2E3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppNameEn}
; 安装程序设置
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
DisableProgramGroupPage=no
; 压缩设置
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 输出设置
OutputDir=..\installer\output
OutputBaseFilename=WeChatRecorder_Setup_v{#MyAppVersion}
SetupIconFile=..\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; 版本信息
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} 安装程序
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
; 权限
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; 用户可选任务
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startmenuicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
; 主程序
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 图标文件
Source: "..\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; 许可证
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
; 说明文档
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
; 运行时依赖 - 如果 PyInstaller 没有打包进去的话
; 注意：PyInstaller 单文件模式通常已经包含所有依赖

[Dirs]
; 创建录音文件夹
Name: "{app}\recordings"; Permissions: users-modify

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: startmenuicon
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Tasks: startmenuicon
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon
; 启动菜单快捷方式（Windows 8+）
Name: "{userstartmenu}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: quicklaunchicon

[Run]
; 安装完成后可选运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时保留录音文件，但询问用户
Type: filesandordirs; Name: "{app}\temp"

[Code]
// 安装前检查
function InitializeSetup(): Boolean;
begin
  // 检查 Windows 版本（需要 Windows 10 或更高）
  if not IsWindows10OrGreater() then
  begin
    MsgBox('本软件需要 Windows 10 或更高版本。', mbError, MB_OK);
    Result := false;
  end else
    Result := true;
end;

// 卸载前提示
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  ResultCode := MsgBox('卸载程序将删除软件文件，但会保留您的录音文件。' + #13#10 + #13#10 +
                       '录音文件位于: ' + ExpandConstant('{app}\recordings') + #13#10 + #13#10 +
                       '确定要继续卸载吗？', mbConfirmation, MB_YESNO);
  Result := (ResultCode = IDYES);
end;

// 安装完成后显示信息
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 创建录音文件夹
    if not DirExists(ExpandConstant('{app}\recordings')) then
      CreateDir(ExpandConstant('{app}\recordings'));
  end;
end;

// 检查是否为 Windows 10 或更高版本
function IsWindows10OrGreater(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  Result := (Version.Major >= 10);
end;
