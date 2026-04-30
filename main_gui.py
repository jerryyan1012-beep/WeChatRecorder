"""
微信通话录音软件 - GUI 界面
使用 PyQt6 构建
"""
import sys
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import platform

# 获取应用程序根目录（处理 PyInstaller 打包后的路径）
def get_app_root():
    """获取应用程序根目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的路径
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox, QTextEdit,
    QGroupBox, QStatusBar, QFileDialog, QMessageBox, QProgressBar,
    QSystemTrayIcon, QMenu, QStyle
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QFont

from audio_recorder import AudioRecorder, WeChatCallDetector


class RecordingThread(QThread):
    """录音工作线程"""
    duration_updated = pyqtSignal(float)
    status_changed = pyqtSignal(str)
    
    def __init__(self, recorder: AudioRecorder):
        super().__init__()
        self.recorder = recorder
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置回调函数"""
        self.recorder.on_duration_update = self._on_duration_update
        self.recorder.on_status_change = self._on_status_change
    
    def _on_duration_update(self, duration: float):
        self.duration_updated.emit(duration)
    
    def _on_status_change(self, status: str):
        self.status_changed.emit(status)
    
    def run(self):
        """线程运行 - 等待录音完成"""
        # 等待录音器完成录音
        while self.recorder.is_recording:
            self.msleep(100)  # 使用 QThread 的 msleep 避免阻塞 GUI
        
        # 确保最终状态被更新
        self.status_changed.emit("stopped")


class WeChatRecorderGUI(QMainWindow):
    """微信通话录音软件主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信通话录音软件")
        self.setMinimumSize(600, 500)
        
        # 获取应用根目录并创建录音文件夹
        self.app_root = get_app_root()
        self.recordings_dir = os.path.join(self.app_root, "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # 初始化组件（使用正确的录音目录）
        self.recorder = AudioRecorder(output_dir=self.recordings_dir)
        self.detector = WeChatCallDetector(
            on_call_start=self._on_call_detected_start,
            on_call_end=self._on_call_detected_end
        )
        self.recording_thread = RecordingThread(self.recorder)
        
        # 连接信号
        self.recording_thread.duration_updated.connect(self._update_duration_display)
        self.recording_thread.status_changed.connect(self._update_recording_status)
        
        # 状态变量
        self.auto_record_enabled = False
        self.output_format = "WAV"
        self.recordings_list = []
        
        # 创建界面
        self._create_menu()
        self._create_central_widget()
        self._create_status_bar()
        self._create_system_tray()
        
        # 启动定时器更新界面
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(1000)  # 每秒更新一次
        
        # 启动检测器
        self.detector.start_detection()
        
        self._log_message("软件已启动，正在检测微信通话...")
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开录音文件夹", self)
        open_action.triggered.connect(self._open_recordings_folder)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 开机启动选项
        autostart_action = QAction("开机自动启动", self)
        autostart_action.setCheckable(True)
        autostart_action.triggered.connect(self._toggle_autostart)
        settings_menu.addAction(autostart_action)
        
        settings_menu.addSeparator()
        
        # 自动录音选项
        auto_record_action = QAction("自动检测通话", self)
        auto_record_action.setCheckable(True)
        auto_record_action.setChecked(self.auto_record_enabled)
        auto_record_action.triggered.connect(self._toggle_auto_record)
        settings_menu.addAction(auto_record_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_central_widget(self):
        """创建中央部件"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === 状态显示区域 ===
        status_group = QGroupBox("通话状态")
        status_layout = QHBoxLayout(status_group)
        
        self.wechat_status_label = QLabel("微信: 未运行")
        self.wechat_status_label.setStyleSheet("color: gray; font-size: 14px;")
        status_layout.addWidget(self.wechat_status_label)
        
        status_layout.addStretch()
        
        self.call_status_label = QLabel("通话: 未检测")
        self.call_status_label.setStyleSheet("color: gray; font-size: 14px;")
        status_layout.addWidget(self.call_status_label)
        
        layout.addWidget(status_group)
        
        # === 录音控制区域 ===
        control_group = QGroupBox("录音控制")
        control_layout = QVBoxLayout(control_group)
        
        # 录音信息显示
        info_layout = QHBoxLayout()
        
        self.duration_label = QLabel("时长: 00:00:00")
        self.duration_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        info_layout.addWidget(self.duration_label)
        
        info_layout.addStretch()
        
        self.file_size_label = QLabel("文件大小: 0 KB")
        self.file_size_label.setStyleSheet("font-size: 12px; color: gray;")
        info_layout.addWidget(self.file_size_label)
        
        control_layout.addLayout(info_layout)
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始录音")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_btn.clicked.connect(self._start_recording)
        buttons_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #f57c00; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.pause_btn.clicked.connect(self._pause_recording)
        self.pause_btn.setEnabled(False)
        buttons_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("停止录音")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_btn.clicked.connect(self._stop_recording)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(buttons_layout)
        
        # 自动录音选项
        auto_layout = QHBoxLayout()
        
        self.auto_record_checkbox = QCheckBox("自动检测并录制微信通话")
        self.auto_record_checkbox.setChecked(False)
        self.auto_record_checkbox.stateChanged.connect(self._toggle_auto_record)
        auto_layout.addWidget(self.auto_record_checkbox)
        
        auto_layout.addStretch()
        
        control_layout.addLayout(auto_layout)
        
        layout.addWidget(control_group)
        
        # === 设置区域 ===
        settings_group = QGroupBox("录音设置")
        settings_layout = QHBoxLayout(settings_group)
        
        # 输出格式
        settings_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["WAV", "MP3 (需要 FFmpeg)"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        settings_layout.addWidget(self.format_combo)
        
        settings_layout.addSpacing(20)
        
        # 采样率
        settings_layout.addWidget(QLabel("采样率:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["44100 Hz", "48000 Hz", "22050 Hz"])
        settings_layout.addWidget(self.sample_rate_combo)
        
        settings_layout.addStretch()
        
        # 打开文件夹按钮
        open_folder_btn = QPushButton("打开录音文件夹")
        open_folder_btn.clicked.connect(self._open_recordings_folder)
        settings_layout.addWidget(open_folder_btn)
        
        layout.addWidget(settings_group)
        
        # === 日志区域 ===
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # 限制日志行数（兼容不同 PyQt6 版本）
        try:
            self.log_text.setMaximumBlockCount(100)
        except AttributeError:
            pass
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        # 设置布局比例
        layout.setStretch(0, 1)  # 状态
        layout.setStretch(1, 2)  # 控制
        layout.setStretch(2, 1)  # 设置
        layout.setStretch(3, 3)  # 日志
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _create_system_tray(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用系统默认图标
        self.tray_icon.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        ))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()
    
    def _tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def _update_ui(self):
        """更新界面状态"""
        # 更新微信状态
        detector_status = self.detector.get_status()
        
        if detector_status['wechat_running']:
            self.wechat_status_label.setText("微信: 运行中")
            self.wechat_status_label.setStyleSheet("color: #4CAF50; font-size: 14px;")
        else:
            self.wechat_status_label.setText("微信: 未运行")
            self.wechat_status_label.setStyleSheet("color: gray; font-size: 14px;")
        
        # 更新通话状态
        if detector_status['is_in_call']:
            self.call_status_label.setText("通话: 进行中")
            self.call_status_label.setStyleSheet("color: #f44336; font-size: 14px; font-weight: bold;")
        else:
            self.call_status_label.setText("通话: 未检测")
            self.call_status_label.setStyleSheet("color: gray; font-size: 14px;")
    
    def _update_duration_display(self, duration: float):
        """更新时长显示"""
        formatted = str(timedelta(seconds=int(duration)))
        self.duration_label.setText(f"时长: {formatted}")
        
        # 更新文件大小（估算）
        # WAV: 采样率 * 声道数 * 2字节 * 时长
        sample_rate = 44100
        channels = 2
        bytes_per_sec = sample_rate * channels * 2
        size_bytes = int(bytes_per_sec * duration)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        
        if size_mb >= 1:
            self.file_size_label.setText(f"文件大小: {size_mb:.2f} MB")
        else:
            self.file_size_label.setText(f"文件大小: {size_kb:.2f} KB")
    
    def _update_recording_status(self, status: str):
        """更新录音状态"""
        if status == "recording":
            self.status_bar.showMessage("正在录音...")
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        elif status == "paused":
            self.status_bar.showMessage("录音已暂停")
            self.pause_btn.setText("继续")
        elif status == "stopped":
            self.status_bar.showMessage("录音已停止")
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setText("暂停")
            self.duration_label.setText("时长: 00:00:00")
            self.file_size_label.setText("文件大小: 0 KB")
    
    def _start_recording(self):
        """开始录音"""
        try:
            filepath = self.recorder.start_recording()
            self._log_message(f"开始录音: {os.path.basename(filepath)}")
            self._update_recording_status("recording")
            
            # 添加到录音列表
            self.recordings_list.append(filepath)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"开始录音失败: {str(e)}")
            self._log_message(f"错误: {str(e)}")
    
    def _pause_recording(self):
        """暂停/继续录音"""
        if self.recorder.is_paused:
            self.recorder.resume_recording()
            self._log_message("继续录音")
        else:
            self.recorder.pause_recording()
            self._log_message("暂停录音")
    
    def _stop_recording(self):
        """停止录音"""
        try:
            filepath = self.recorder.stop_recording()
            self._log_message(f"录音已保存: {filepath}")
            
            # 添加到录音列表并限制大小防止内存泄漏
            self.recordings_list.append(filepath)
            MAX_RECORDINGS = 1000  # 限制录音列表大小
            if len(self.recordings_list) > MAX_RECORDINGS:
                # 移除最旧的记录
                self.recordings_list = self.recordings_list[-MAX_RECORDINGS:]
                self._log_message(f"录音列表已清理，保留最近 {MAX_RECORDINGS} 条记录")
            
            # 如果需要转换为 MP3
            if "MP3" in self.format_combo.currentText():
                self._convert_to_mp3(filepath)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止录音失败: {str(e)}")
            self._log_message(f"错误: {str(e)}")
    
    def _convert_to_mp3(self, wav_path: str):
        """转换为 MP3"""
        import pathlib
        
        try:
            # 路径验证 - 防止命令注入
            wav_path_obj = pathlib.Path(wav_path).resolve()
            if not wav_path_obj.exists():
                raise RuntimeError(f"WAV 文件不存在: {wav_path}")
            if not wav_path_obj.suffix.lower() == '.wav':
                raise RuntimeError(f"文件必须是 WAV 格式: {wav_path}")
            
            mp3_path = str(wav_path_obj.with_suffix('.mp3'))
            self._log_message(f"正在转换为 MP3...")
            
            # 使用列表传参避免命令注入
            cmd = [
                'ffmpeg', '-i', str(wav_path_obj),
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',
                '-y', mp3_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self._log_message(f"MP3 转换完成: {mp3_path}")
                # 删除原始 WAV
                os.remove(wav_path)
                self._log_message("已删除原始 WAV 文件")
            else:
                self._log_message(f"MP3 转换失败: {result.stderr}")
                
        except Exception as e:
            self._log_message(f"转换 MP3 失败: {str(e)}")
    
    def _toggle_auto_record(self, state):
        """切换自动录音"""
        self.auto_record_enabled = state == Qt.CheckState.Checked.value
        if self.auto_record_enabled:
            self._log_message("自动录音已启用")
        else:
            self._log_message("自动录音已禁用")
    
    def _on_call_detected_start(self):
        """检测到通话开始"""
        self._log_message("检测到微信通话开始")
        
        if self.auto_record_enabled and not self.recorder.is_recording:
            self._start_recording()
            
            # 显示托盘通知
            self.tray_icon.showMessage(
                "微信通话录音",
                "检测到通话，开始自动录音",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    def _on_call_detected_end(self):
        """检测到通话结束"""
        self._log_message("检测到微信通话结束")
        
        if self.auto_record_enabled and self.recorder.is_recording:
            self._stop_recording()
            
            # 显示托盘通知
            self.tray_icon.showMessage(
                "微信通话录音",
                "通话结束，录音已保存",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    def _on_format_changed(self, text: str):
        """输出格式改变"""
        self.output_format = text.replace(" (需要 FFmpeg)", "")
    
    def _open_recordings_folder(self):
        """打开录音文件夹"""
        recordings_path = self.recordings_dir
        os.makedirs(recordings_path, exist_ok=True)
        
        try:
            if os.name == 'nt':
                os.startfile(recordings_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', recordings_path])
            else:  # Linux
                subprocess.run(['xdg-open', recordings_path])
        except Exception as e:
            self._log_message(f"打开文件夹失败: {e}")
            # 复制路径到剪贴板作为备选
            clipboard = QApplication.clipboard()
            clipboard.setText(recordings_path)
            self._log_message(f"文件夹路径已复制到剪贴板: {recordings_path}")
    
    def _toggle_autostart(self, checked):
        """切换开机自动启动"""
        # 这里可以实现开机启动的逻辑
        if checked:
            self._log_message("已设置开机自动启动")
        else:
            self._log_message("已取消开机自动启动")
    
    def _toggle_auto_record(self, checked):
        """切换自动录音"""
        self.auto_record_enabled = checked
        if checked:
            self._log_message("已启用自动检测通话录音")
        else:
            self._log_message("已禁用自动检测通话录音")
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 微信通话录音软件",
            """<h2>微信通话录音软件 v1.0</h2>
            <p>一款简单易用的 Windows 微信通话录音工具。</p>
            <p>功能特点：</p>
            <ul>
                <li>自动检测微信通话</li>
                <li>录制双方声音</li>
                <li>支持 WAV/MP3 格式</li>
                <li>简洁易用的界面</li>
            </ul>
            <p>注意：录音仅供个人使用，请遵守当地法律法规。</p>
            """
        )
    
    def _log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 先停止检测器
        self.detector.stop_detection()
        
        if self.recorder.is_recording:
            reply = QMessageBox.question(
                self, "确认退出",
                "正在录音中，确定要退出吗？录音将被保存。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self._stop_recording()
                    # 等待录音线程完全结束
                    if self.recording_thread and self.recording_thread.isRunning():
                        self.recording_thread.wait(3000)
                except Exception as e:
                    self._log_message(f"停止录音时出错: {e}")
                event.accept()
            else:
                # 用户取消退出，重新启动检测器
                self.detector.start_detection()
                event.ignore()
        else:
            # 确保录音线程已清理
            if self.recording_thread and self.recording_thread.isRunning():
                self.recording_thread.wait(1000)
            event.accept()


def main():
    """主函数"""
    # 启用高 DPI 支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用字体（根据系统选择合适字体）
    if os.name == 'nt':  # Windows
        font = QFont("Microsoft YaHei", 10)
    elif platform.system() == 'Darwin':  # macOS
        font = QFont("PingFang SC", 10)
    else:  # Linux
        font = QFont("Noto Sans CJK SC", 10)
    app.setFont(font)
    
    window = WeChatRecorderGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
