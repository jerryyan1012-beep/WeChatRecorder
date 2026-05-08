"""
核心录音模块 - 使用 WASAPI Loopback 录制系统音频
"""
import threading
import wave
import os
import sys
import time
import platform
from datetime import datetime
from typing import Callable, Optional
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """音频录制器 - 捕获系统输出音频（WASAPI Loopback）"""
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 channels: int = 2,
                 chunk_duration: float = 0.1,
                 output_dir: str = "recordings"):
        """
        初始化录音器
        
        Args:
            sample_rate: 采样率 (Hz)
            channels: 声道数 (1=单声道, 2=立体声)
            chunk_duration: 每次读取音频块的时长 (秒)
            output_dir: 录音文件保存目录
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration)
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 录音状态
        self.is_recording = False
        self.is_paused = False
        self.frames = []
        self.recording_thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
        self.pause_start_time: Optional[float] = None
        self.total_pause_duration = 0.0
        
        # 回调函数
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_duration_update: Optional[Callable[[float], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # 录音文件信息
        self.current_filename: Optional[str] = None
        self.current_filepath: Optional[str] = None
        
    def _get_default_loopback_device(self) -> tuple:
        """获取默认的 WASAPI Loopback 设备
        
        Returns:
            (device_dict, channels) 设备信息和声道数
        """
        try:
            # 查询所有设备
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
            
            print(f"[_get_default_loopback_device] 可用 Host APIs: {[api.get('name') for api in hostapis]}")
            print(f"[_get_default_loopback_device] 可用设备数: {len(devices)}")
            
            # 找到 WASAPI hostapi 的索引
            wasapi_index = None
            for i, api in enumerate(hostapis):
                api_name = api.get('name', '')
                print(f"[_get_default_loopback_device] Host API {i}: {api_name}")
                if 'wasapi' in api_name.lower() or api_name == 'Windows WASAPI':
                    wasapi_index = i
                    print(f"[_get_default_loopback_device] 找到 WASAPI: index={i}")
                    break
            
            selected_device = None
            
            # Windows 平台：查找 Loopback 设备
            if os.name == 'nt' and wasapi_index is not None:
                print(f"[_get_default_loopback_device] Windows 平台，查找 Loopback 设备...")
                
                # 列出所有 WASAPI 设备
                print(f"[_get_default_loopback_device] WASAPI 设备列表:")
                for device in devices:
                    if device.get('hostapi') == wasapi_index:
                        device_name = device.get('name', '')
                        max_in = device.get('max_input_channels', 0)
                        max_out = device.get('max_output_channels', 0)
                        print(f"  - {device_name} (index={device['index']}, in={max_in}, out={max_out})")
                
                # 首先尝试找到默认输出设备的 Loopback
                try:
                    default_output = sd.query_devices(kind='output')
                    print(f"[_get_default_loopback_device] 默认输出设备: {default_output.get('name', 'Unknown')}")
                    if default_output:
                        device_index = default_output['index']
                        # 查找对应的 Loopback 设备
                        for device in devices:
                            if device.get('hostapi') == wasapi_index:
                                device_name = device.get('name', '')
                                if 'Loopback' in device_name:
                                    selected_device = device
                                    print(f"[_get_default_loopback_device] 找到 Loopback 设备: {device_name}")
                                    break
                except Exception as e:
                    print(f"[_get_default_loopback_device] 查找默认输出设备失败: {e}")
                
                # 回退：查找任何 WASAPI Loopback 设备
                if not selected_device:
                    print(f"[_get_default_loopback_device] 尝试查找任何 Loopback 设备...")
                    for device in devices:
                        if device.get('hostapi') == wasapi_index:
                            device_name = device.get('name', '')
                            if 'Loopback' in device_name:
                                selected_device = device
                                print(f"[_get_default_loopback_device] 找到 Loopback 设备(回退): {device_name}")
                                break
            
            # 非 Windows 或找不到 Loopback：使用默认输入设备
            if not selected_device:
                print(f"[_get_default_loopback_device] 使用默认输入设备...")
                default_input = sd.query_devices(kind='input')
                if default_input:
                    selected_device = default_input
                    print(f"[_get_default_loopback_device] 使用默认输入: {selected_device.get('name', 'Unknown')}")
            
            if not selected_device:
                raise RuntimeError("未找到可用的音频设备")
            
            # 获取设备支持的声道数
            device_channels = selected_device.get('max_input_channels', 2)
            # 如果设备是单声道，使用单声道；否则使用立体声
            if device_channels == 1:
                channels = 1
            else:
                channels = min(2, device_channels)  # 最多使用双声道
            
            print(f"[_get_default_loopback_device] 最终选择: {selected_device.get('name', 'Unknown')}, 声道数: {channels}")
            return selected_device, channels
            
        except Exception as e:
            raise RuntimeError(f"获取音频设备失败: {e}")
    
    def _record_audio(self):
        """录音线程主函数"""
        stream = None
        try:
            device, channels = self._get_default_loopback_device()
            device_id = device['index']
            
            # 更新声道数（使用设备支持的声道数）
            self.channels = channels
            print(f"[_record_audio] 开始录音初始化")
            print(f"[_record_audio] 设备={device.get('name', 'Unknown')}, ID={device_id}")
            print(f"[_record_audio] 采样率={self.sample_rate}, 声道数={channels}, 块大小={self.chunk_size}")
            print(f"[_record_audio] is_recording={self.is_recording}")
            
            callback_count = 0  # 使用整数而非列表，避免闭包问题
            
            def audio_callback(indata, frames, time_info, status):
                nonlocal callback_count  # 使用 nonlocal 而非列表
                try:
                    callback_count += 1
                    if status:
                        print(f"[_record_audio] 音频状态警告: {status}")
                    
                    # 打印前5次回调用于调试
                    if callback_count <= 5:
                        print(f"[_record_audio] 回调 #{callback_count}: is_recording={self.is_recording}, is_paused={self.is_paused}")
                        print(f"[_record_audio] 回调 #{callback_count}: indata shape={indata.shape}, dtype={indata.dtype}")
                    
                    if self.is_recording and not self.is_paused:
                        # 将音频数据转换为 int16
                        audio_data = (indata * 32767).astype(np.int16)
                        self.frames.append(audio_data.copy())
                        # 每100帧打印一次调试信息
                        if len(self.frames) % 100 == 0:
                            print(f"[_record_audio] 已采集 {len(self.frames)} 帧音频数据")
                except Exception as e:
                    error_msg = f"[_record_audio] 音频回调错误: {str(e)}"
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
                    if self.on_error:
                        self.on_error(error_msg)
            
            print(f"[_record_audio] 正在打开音频流...")
            # 打开音频流
            stream = sd.InputStream(
                device=device_id,
                channels=channels,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=audio_callback
            )
            stream.start()
            print(f"[_record_audio] 音频流已打开: active={stream.active}")
            self._notify_status("recording")
            
            loop_count = 0
            while self.is_recording:
                loop_count += 1
                if loop_count <= 10:  # 前10次循环打印调试信息
                    print(f"[_record_audio] 主循环 #{loop_count}: is_recording={self.is_recording}, frames={len(self.frames)}")
                elif loop_count == 11:
                    print(f"[_record_audio] 主循环继续运行中... (不再打印)")
                
                if not self.is_paused:
                    # 计算录音时长
                    elapsed = time.time() - self.start_time - self.total_pause_duration
                    if self.on_duration_update:
                        self.on_duration_update(elapsed)
                time.sleep(0.1)
            
            print(f"[_record_audio] 主循环结束，总循环次数={loop_count}, 总帧数={len(self.frames)}")
                
        except Exception as e:
            error_msg = f"[_record_audio] 录音错误: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            if self.on_error:
                self.on_error(error_msg)
            self.is_recording = False
            self._notify_status("error")
        finally:
            # 确保音频流正确关闭
            if stream is not None:
                try:
                    print("[_record_audio] 正在关闭音频流...")
                    stream.stop()
                    stream.close()
                    print("[_record_audio] 音频流已关闭")
                except Exception as e:
                    print(f"[_record_audio] 关闭音频流时出错: {e}")
    
    def _notify_status(self, status: str):
        """通知状态变更"""
        if self.on_status_change:
            self.on_status_change(status)
    
    def start_recording(self, filename: Optional[str] = None) -> str:
        """
        开始录音
        
        Args:
            filename: 自定义文件名（不含扩展名），默认使用时间戳
            
        Returns:
            录音文件的完整路径
        """
        if self.is_recording:
            raise RuntimeError("录音已在进行中")
        
        print(f"开始录音初始化...")
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wechat_call_{timestamp}"
        
        self.current_filename = f"{filename}.wav"
        self.current_filepath = os.path.join(self.output_dir, self.current_filename)
        
        # 重置状态
        self.frames = []
        self.is_recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_pause_duration = 0.0
        
        print(f"录音文件路径: {self.current_filepath}")
        print(f"is_recording 设置为: {self.is_recording}")
        
        # 启动录音线程
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True  # 设置为守护线程
        self.recording_thread.start()
        
        print(f"录音线程已启动，线程ID: {self.recording_thread.ident}")
        
        # 等待一小段时间检查线程是否还在运行
        time.sleep(0.5)
        if not self.recording_thread.is_alive():
            print("错误: 录音线程启动后立即退出")
        else:
            print(f"录音线程运行正常，is_recording={self.is_recording}")
        
        return self.current_filepath
    
    def pause_recording(self):
        """暂停录音"""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
            self._notify_status("paused")
    
    def resume_recording(self):
        """恢复录音"""
        if self.is_recording and self.is_paused:
            self.is_paused = False
            if self.pause_start_time:
                self.total_pause_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            self._notify_status("recording")
    
    def stop_recording(self) -> str:
        """
        停止录音并保存文件
        
        Returns:
            保存的文件路径
        """
        if not self.is_recording:
            print("警告: stop_recording 被调用但没有正在进行的录音")
            # 确保状态一致
            self._notify_status("stopped")
            raise RuntimeError("没有正在进行的录音")
        
        self.is_recording = False
        
        # 等待录音线程结束 - 改进线程结束处理
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)  # 增加超时时间
            if self.recording_thread.is_alive():
                # 线程仍在运行，记录警告但继续处理
                print("警告: 录音线程未能在超时时间内结束")
        
        # 清理线程引用
        self.recording_thread = None
        
        # 保存录音文件
        saved = False
        if self.frames:
            try:
                print(f"正在保存录音，帧数: {len(self.frames)}, 总采样数: {sum(len(f) for f in self.frames)}")
                self._save_wav()
                saved = True
            except Exception as e:
                print(f"保存录音文件失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("警告: 没有采集到任何音频数据")
        
        # 清理帧数据释放内存（关键修复：防止内存泄漏）
        print(f"[stop_recording] 清理帧数据，释放内存...")
        self.frames = []
        import gc
        gc.collect()
        print(f"[stop_recording] 内存已释放")
        
        # 重置其他状态变量
        self.start_time = None
        self.pause_start_time = None
        self.total_pause_duration = 0.0
        self.is_paused = False
        
        # 无论成否与否，都通知状态变更
        self._notify_status("stopped")
        
        if not saved:
            raise RuntimeError("录音保存失败：没有采集到任何音频数据或保存出错")
        
        return self.current_filepath
    
    def _save_wav(self):
        """保存为 WAV 文件"""
        if not self.frames:
            return
        
        try:
            # 合并所有音频帧
            audio_data = np.concatenate(self.frames, axis=0)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.current_filepath) or '.', exist_ok=True)
            
            # 保存为 WAV
            with wave.open(self.current_filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            print(f"录音已保存: {self.current_filepath}")
            print(f"文件大小: {os.path.getsize(self.current_filepath) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"保存录音失败: {e}")
            raise RuntimeError(f"保存录音文件失败: {e}")
    
    def get_recording_info(self) -> dict:
        """
        获取当前录音信息
        
        Returns:
            包含录音信息的字典
        """
        info = {
            'is_recording': self.is_recording,
            'is_paused': self.is_paused,
            'filename': self.current_filename,
            'filepath': self.current_filepath,
            'duration': 0.0,
            'file_size': 0
        }
        
        if self.is_recording and self.start_time:
            info['duration'] = time.time() - self.start_time - self.total_pause_duration
        
        if self.current_filepath and os.path.exists(self.current_filepath):
            info['file_size'] = os.path.getsize(self.current_filepath)
        
        return info
    
    def convert_to_mp3(self, wav_path: str, mp3_path: Optional[str] = None) -> str:
        """
        将 WAV 转换为 MP3（需要安装 ffmpeg）
        
        Args:
            wav_path: WAV 文件路径
            mp3_path: MP3 输出路径，默认为同名 .mp3
            
        Returns:
            MP3 文件路径
        """
        import subprocess
        import pathlib
        
        # 路径验证 - 防止命令注入
        wav_path_obj = pathlib.Path(wav_path).resolve()
        if not wav_path_obj.exists():
            raise RuntimeError(f"WAV 文件不存在: {wav_path}")
        if not wav_path_obj.suffix.lower() == '.wav':
            raise RuntimeError(f"文件必须是 WAV 格式: {wav_path}")
        
        # 验证路径在允许范围内（防止目录遍历）
        output_dir = pathlib.Path(self.output_dir).resolve()
        try:
            wav_path_obj.relative_to(output_dir)
        except ValueError:
            raise RuntimeError(f"WAV 文件不在允许的输出目录中: {wav_path}")
        
        if mp3_path is None:
            mp3_path = str(wav_path_obj.with_suffix('.mp3'))
        else:
            mp3_path_obj = pathlib.Path(mp3_path).resolve()
            try:
                mp3_path_obj.relative_to(output_dir)
            except ValueError:
                raise RuntimeError(f"MP3 输出路径不在允许的目录中: {mp3_path}")
            mp3_path = str(mp3_path_obj)
        
        # 使用列表传参避免命令注入
        cmd = [
            'ffmpeg', '-i', str(wav_path_obj),
            '-codec:a', 'libmp3lame',
            '-qscale:a', '2',
            '-y', mp3_path
        ]
        
        try:
            # Windows 下使用 CREATE_NO_WINDOW 标志
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    startupinfo=startupinfo,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(cmd, check=True, capture_output=True)
            
            return mp3_path
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            raise RuntimeError(f"转换 MP3 失败: {error_msg}")
        except FileNotFoundError:
            raise RuntimeError("未找到 ffmpeg，请安装 ffmpeg 并添加到系统 PATH")
        except Exception as e:
            raise RuntimeError(f"转换 MP3 失败: {e}")


class WeChatCallDetector:
    """微信通话检测器"""
    
    # 微信进程名（Windows）
    WECHAT_PROCESS_NAMES = ['WeChat.exe', 'WeChatApp.exe', 'wechat.exe']
    
    # 通话窗口标题关键词
    CALL_WINDOW_KEYWORDS = [
        '语音通话', '视频通话', 'Voice Call', 'Video Call',
        '正在通话', '通话中', 'Calling'
    ]
    
    def __init__(self, 
                 check_interval: float = 2.0,
                 on_call_start: Optional[Callable] = None,
                 on_call_end: Optional[Callable] = None):
        """
        初始化检测器
        
        Args:
            check_interval: 检测间隔（秒）
            on_call_start: 通话开始回调
            on_call_end: 通话结束回调
        """
        self.check_interval = check_interval
        self.on_call_start = on_call_start
        self.on_call_end = on_call_end
        
        self.is_running = False
        self.is_in_call = False
        self.detector_thread: Optional[threading.Thread] = None
    
    def _is_wechat_running(self) -> bool:
        """检查微信是否在运行"""
        try:
            import psutil
            found_processes = []
            for proc in psutil.process_iter(['name', 'pid']):
                proc_name = proc.info['name']
                if proc_name:
                    # 不区分大小写匹配
                    proc_name_lower = proc_name.lower()
                    for wechat_name in self.WECHAT_PROCESS_NAMES:
                        if wechat_name.lower() == proc_name_lower:
                            found_processes.append(f"{proc_name} (PID: {proc.info['pid']})")
                            return True
            
            # 调试信息：如果没有找到，打印所有进程名
            if not found_processes:
                print("调试：未找到微信进程，当前运行的进程包括:")
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and 'wechat' in proc.info['name'].lower():
                        print(f"  - {proc.info['name']}")
            else:
                print(f"找到微信进程: {found_processes}")
            
            return len(found_processes) > 0
        except Exception as e:
            print(f"检查进程失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_call_status(self) -> bool:
        """
        检查是否正在通话中
        
        Returns:
            True 表示正在通话
        """
        try:
            # Windows 平台：检查微信窗口标题
            if os.name == 'nt':
                return self._check_windows_call_status()
            else:
                # 其他平台：简化检测，仅检查进程
                return self._is_wechat_running()
        except Exception as e:
            print(f"检查通话状态失败: {e}")
            return False
    
    def _check_windows_call_status(self) -> bool:
        """Windows 平台检查通话状态"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # 枚举所有窗口
            user32 = ctypes.windll.user32
            
            call_windows = []
            
            # 正确的 EnumWindowsProc 回调类型定义
            EnumWindowsProc = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HWND,
                wintypes.LPARAM
            )
            
            def enum_windows_callback(hwnd, lparam):
                try:
                    if user32.IsWindowVisible(hwnd):
                        # 获取窗口标题
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buffer = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buffer, length + 1)
                            title = buffer.value
                            
                            # 检查是否是微信窗口且包含通话关键词
                            for keyword in self.CALL_WINDOW_KEYWORDS:
                                if keyword in title:
                                    call_windows.append(title)
                                    return False  # 找到就停止
                except Exception as e:
                    print(f"窗口枚举回调错误: {e}")
                return True
            
            callback = EnumWindowsProc(enum_windows_callback)
            user32.EnumWindows(callback, 0)
            
            return len(call_windows) > 0
            
        except Exception as e:
            print(f"Windows 窗口检测失败: {e}")
            # 回退：仅检查微信进程
            return self._is_wechat_running()
    
    def _detection_loop(self):
        """检测循环"""
        while self.is_running:
            try:
                is_calling = self._check_call_status()
                
                if is_calling and not self.is_in_call:
                    # 通话开始
                    self.is_in_call = True
                    print("检测到微信通话开始")
                    if self.on_call_start:
                        self.on_call_start()
                        
                elif not is_calling and self.is_in_call:
                    # 通话结束
                    self.is_in_call = False
                    print("检测到微信通话结束")
                    if self.on_call_end:
                        self.on_call_end()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"检测循环错误: {e}")
                time.sleep(self.check_interval)
    
    def start_detection(self):
        """开始检测"""
        if self.is_running:
            return
        
        # 先检查微信是否在运行
        wechat_running = self._is_wechat_running()
        
        self.is_running = True
        self.detector_thread = threading.Thread(target=self._detection_loop)
        self.detector_thread.daemon = True
        self.detector_thread.start()
        
        if wechat_running:
            print("微信通话检测已启动 (微信正在运行)")
        else:
            print("微信通话检测已启动 (未检测到微信进程，请确保微信已启动)")
    
    def stop_detection(self):
        """停止检测"""
        self.is_running = False
        if self.detector_thread:
            self.detector_thread.join(timeout=2.0)
        print("微信通话检测已停止")
    
    def get_status(self) -> dict:
        """获取检测器状态"""
        return {
            'is_running': self.is_running,
            'is_in_call': self.is_in_call,
            'wechat_running': self._is_wechat_running()
        }
