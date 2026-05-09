"""
核心录音模块 - 使用 WASAPI Loopback 录制系统音频 + 麦克风输入
同时录制双方声音：麦克风（我方）+ 系统回环（对方）
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
    """
    音频录制器 - 同时录制麦克风和系统声音
    
    微信通话录音原理:
    - 对方声音: 通过 WASAPI Loopback 录制系统输出（扬声器/耳机）
    - 我方声音: 通过麦克风输入录制
    - 最终混合成双声道立体声文件（左声道=对方，右声道=我方）
    """
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 channels: int = 2,
                 chunk_duration: float = 0.1,
                 output_dir: str = "recordings"):
        """
        初始化录音器
        
        Args:
            sample_rate: 采样率 (Hz)
            channels: 声道数 (最终输出立体声的声道数)
            chunk_duration: 每次读取音频块的时长 (秒)
            output_dir: 录音文件保存目录
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration)
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 录音状态 - 使用 Event 确保线程安全
        self.is_recording = False
        self.is_paused = False
        self._stop_event = threading.Event()  # 用于线程安全退出
        
        # 两个音频流的帧数据
        self.system_frames = []  # 系统声音帧 (对方)
        self.mic_frames = []     # 麦克风声音帧 (我方)
        self.frames_lock = threading.Lock()  # 保护帧数据的锁
        
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
        
        # 设备信息
        self.system_device = None  # 系统输出设备 (Loopback)
        self.mic_device = None     # 麦克风输入设备
        
    def _get_audio_devices(self):
        """
        获取音频设备 - 在 Windows 上使用 WASAPI Loopback 模式
        
        Returns:
            (system_device, mic_device) 系统输出设备和麦克风设备
        """
        try:
            print(f"[_get_audio_devices] 开始查询音频设备...")
            print(f"[_get_audio_devices] sounddevice 版本: {sd.__version__}")
            
            # 检查 PortAudio 是否可用
            try:
                devices = sd.query_devices()
            except Exception as e:
                print(f"[_get_audio_devices] 错误: 无法查询音频设备")
                print(f"  详情: {e}")
                print(f"  可能原因: PortAudio 库未正确加载")
                print(f"  建议: 检查是否安装了音频驱动，或尝试重新启动程序")
                raise RuntimeError(f"音频库未正确加载，请检查系统音频驱动: {e}")
            
            hostapis = sd.query_hostapis()
            
            print(f"[_get_audio_devices] 可用设备数: {len(devices)}")
            
            # 找到 WASAPI hostapi 的索引
            wasapi_index = None
            for i, api in enumerate(hostapis):
                api_name = api.get('name', '')
                if 'wasapi' in api_name.lower() or api_name == 'Windows WASAPI':
                    wasapi_index = i
                    print(f"[_get_audio_devices] 找到 WASAPI: index={i}")
                    break
            
            system_device = None
            mic_device = None
            
            # Windows 平台：使用 WASAPI Loopback
            if os.name == 'nt':
                print(f"[_get_audio_devices] Windows 平台，尝试使用 WASAPI Loopback...")
                
                # 获取默认输出设备 (扬声器/耳机)
                try:
                    default_output = sd.query_devices(kind='output')
                    if default_output:
                        system_device = default_output
                        print(f"[_get_audio_devices] 系统输出设备: {system_device.get('name', 'Unknown')} (ID={system_device['index']})")
                        print(f"  - 将使用 WASAPI Loopback 模式录制此设备")
                except Exception as e:
                    print(f"[_get_audio_devices] 获取默认输出设备失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 获取默认输入设备 (麦克风)
                try:
                    default_input = sd.query_devices(kind='input')
                    if default_input:
                        mic_device = default_input
                        print(f"[_get_audio_devices] 麦克风设备: {mic_device.get('name', 'Unknown')} (ID={mic_device['index']})")
                except Exception as e:
                    print(f"[_get_audio_devices] 获取麦克风失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 非 Windows 平台或找不到 WASAPI
            if not system_device:
                print(f"[_get_audio_devices] 非 Windows 平台，尝试使用默认输入...")
                try:
                    default_input = sd.query_devices(kind='input')
                    if default_input:
                        system_device = default_input
                        print(f"[_get_audio_devices] 使用默认输入: {system_device.get('name', 'Unknown')}")
                except Exception as e:
                    print(f"[_get_audio_devices] 失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not mic_device:
                print(f"[_get_audio_devices] 未找到麦克风，将只录制系统声音")
            
            return system_device, mic_device
            
        except Exception as e:
            raise RuntimeError(f"获取音频设备失败: {e}")
    
    def _record_audio(self):
        """录音线程主函数 - 同时录制系统声音和麦克风"""
        system_stream = None
        mic_stream = None
        
        print(f"[_record_audio] 录音线程已启动")
        print(f"[_record_audio] 录音状态: is_recording={self.is_recording}")
        
        try:
            # 获取设备
            print(f"[_record_audio] 正在获取音频设备...")
            system_device, mic_device = self._get_audio_devices()
            
            if not system_device:
                print(f"[_record_audio] 错误: 未找到系统音频设备")
                raise RuntimeError("未找到系统音频设备")
            
            print(f"[_record_audio] 设备获取成功")
            
            # 检查是否是 Windows 平台
            is_windows = os.name == 'nt'
            
            # ===== 系统声音录制 (对方声音) =====
            system_id = system_device['index']
            print(f"[_record_audio] 系统设备: {system_device.get('name', 'Unknown')} (ID={system_id})")
            
            # 系统声音回调
            def system_callback(indata, frames, time_info, status):
                try:
                    if status and str(status) not in ['input overflow', '']:
                        print(f"[系统音频] 状态: {status}")
                    
                    if self.is_recording and not self.is_paused:
                        # 转换为 int16 并存储
                        audio_data = (indata * 32767).astype(np.int16)
                        with self.frames_lock:
                            self.system_frames.append(audio_data.copy())
                except Exception as e:
                    error_msg = f"[系统音频] 回调错误: {str(e)}"
                    print(error_msg)
            
            # 打开系统音频流
            print(f"[_record_audio] 打开系统音频流...")
            system_channels = min(2, system_device.get('max_input_channels', 2))
            
            # Windows 平台: 使用 WASAPI Loopback 模式
            if is_windows:
                print(f"[_record_audio] 使用 WASAPI Loopback 模式录制系统输出")
                try:
                    import sounddevice as sd_module
                    # 尝试使用 WASAPI Loopback 模式
                    system_stream = sd.InputStream(
                        device=system_id,
                        channels=system_channels,
                        samplerate=self.sample_rate,
                        dtype=np.float32,
                        blocksize=self.chunk_size,
                        callback=system_callback,
                        extra_settings=sd_module.WasapiSettings(loopback=True)
                    )
                except Exception as e:
                    print(f"[_record_audio] WASAPI Loopback 失败: {e}")
                    print(f"[_record_audio] 回退到标准模式...")
                    system_stream = sd.InputStream(
                        device=system_id,
                        channels=system_channels,
                        samplerate=self.sample_rate,
                        dtype=np.float32,
                        blocksize=self.chunk_size,
                        callback=system_callback
                    )
            else:
                # 非 Windows 平台
                system_stream = sd.InputStream(
                    device=system_id,
                    channels=system_channels,
                    samplerate=self.sample_rate,
                    dtype=np.float32,
                    blocksize=self.chunk_size,
                    callback=system_callback
                )
            
            system_stream.start()
            print(f"[_record_audio] 系统音频流已启动: 声道={system_channels}")
            
            # ===== 麦克风录制 (我方声音) =====
            if mic_device:
                mic_id = mic_device['index']
                print(f"[_record_audio] 麦克风设备: {mic_device.get('name', 'Unknown')} (ID={mic_id})")
                
                def mic_callback(indata, frames, time_info, status):
                    try:
                        if status and str(status) not in ['input overflow', '']:
                            print(f"[麦克风] 状态: {status}")
                        
                        if self.is_recording and not self.is_paused:
                            audio_data = (indata * 32767).astype(np.int16)
                            with self.frames_lock:
                                self.mic_frames.append(audio_data.copy())
                    except Exception as e:
                        error_msg = f"[麦克风] 回调错误: {str(e)}"
                        print(error_msg)
                
                print(f"[_record_audio] 打开麦克风流...")
                mic_channels = min(1, mic_device.get('max_input_channels', 1))  # 麦克风通常单声道
                mic_stream = sd.InputStream(
                    device=mic_id,
                    channels=mic_channels,
                    samplerate=self.sample_rate,
                    dtype=np.float32,
                    blocksize=self.chunk_size,
                    callback=mic_callback
                )
                mic_stream.start()
                print(f"[_record_audio] 麦克风流已启动: 声道={mic_channels}")
            else:
                print(f"[_record_audio] 没有麦克风，将只录制系统声音")
            
            self._notify_status("recording")
            
            # 主循环 - 使用 Event 等待更高效
            loop_count = 0
            last_system_count = 0
            last_mic_count = 0
            
            while not self._stop_event.is_set():
                loop_count += 1
                
                # 每 10 秒输出一次统计
                if loop_count % 100 == 0:
                    system_new = len(self.system_frames) - last_system_count
                    mic_new = len(self.mic_frames) - last_mic_count
                    print(f"[_record_audio] 录音中... 系统帧={len(self.system_frames)}(+{system_new}), 麦克风帧={len(self.mic_frames)}(+{mic_new})")
                    last_system_count = len(self.system_frames)
                    last_mic_count = len(self.mic_frames)
                
                if not self.is_paused:
                    elapsed = time.time() - self.start_time - self.total_pause_duration
                    if self.on_duration_update:
                        self.on_duration_update(elapsed)
                
                # 使用 Event 等待，支持立即退出
                self._stop_event.wait(0.1)
            
            print(f"[_record_audio] 录音结束，总循环次数={loop_count}")
            print(f"[_record_audio] 系统帧数: {len(self.system_frames)}, 麦克风帧数: {len(self.mic_frames)}")
            
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
            # 关闭音频流
            if system_stream is not None:
                try:
                    print("[_record_audio] 关闭系统音频流...")
                    system_stream.stop()
                    system_stream.close()
                    print("[_record_audio] 系统音频流已关闭")
                except Exception as e:
                    print(f"[_record_audio] 关闭系统流时出错: {e}")
            
            if mic_stream is not None:
                try:
                    print("[_record_audio] 关闭麦克风流...")
                    mic_stream.stop()
                    mic_stream.close()
                    print("[_record_audio] 麦克风流已关闭")
                except Exception as e:
                    print(f"[_record_audio] 关闭麦克风流时出错: {e}")
    
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
        self.system_frames = []
        self.mic_frames = []
        self.is_recording = True
        self.is_paused = False
        self._stop_event.clear()  # 清除停止信号
        self.start_time = time.time()
        self.total_pause_duration = 0.0
        
        print(f"录音文件路径: {self.current_filepath}")
        
        # 启动录音线程
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # 等待线程初始化（最多2秒）
        # 如果线程内部发生异常，is_recording 会被设为 False
        wait_count = 0
        max_wait = 20  # 2秒 (20 * 0.1s)
        startup_failed = False
        while wait_count < max_wait:
            if not self.is_recording:
                startup_failed = True
                break
            time.sleep(0.1)
            wait_count += 1
        
        if startup_failed:
            # 启动失败，清理线程引用避免资源泄漏
            print("录音线程启动失败，正在清理...")
            self._stop_event.set()  # 发出停止信号
            if self.recording_thread and self.recording_thread.is_alive():
                try:
                    self.recording_thread.join(timeout=1.0)
                except:
                    pass
            self.recording_thread = None
            self.is_recording = False
            raise RuntimeError("录音线程启动失败，请查看黑底控制台输出确认音频设备是否可用")
        
        print(f"录音线程已启动")
        
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
            self._notify_status("已停止")
            raise RuntimeError("没有正在进行的录音")
        
        # 发出停止信号 - 线程安全
        self._stop_event.set()
        self.is_recording = False
        
        # 等待录音线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
            if self.recording_thread.is_alive():
                print("警告: 录音线程未能在超时时间内结束")
        
        # 清理线程引用
        self.recording_thread = None
        
        # 保存录音文件
        saved = False
        if self.system_frames or self.mic_frames:
            try:
                print(f"正在保存录音...")
                print(f"  系统声音帧数: {len(self.system_frames)}")
                print(f"  麦克风帧数: {len(self.mic_frames)}")
                self._save_wav()
                saved = True
            except Exception as e:
                print(f"保存录音文件失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("警告: 没有采集到任何音频数据")
        
        # 清理帧数据释放内存
        print(f"[stop_recording] 清理帧数据...")
        self.system_frames = []
        self.mic_frames = []
        import gc
        gc.collect()
        
        # 重置状态变量
        self.start_time = None
        self.pause_start_time = None
        self.total_pause_duration = 0.0
        self.is_paused = False
        
        self._notify_status("stopped")
        
        if not saved:
            raise RuntimeError("录音保存失败：没有采集到任何音频数据或保存出错")
        
        return self.current_filepath
    
    def _save_wav(self):
        """
        保存为 WAV 文件 - 将系统声音和麦克风混合成双声道
        
        声道分配:
        - 左声道: 系统声音 (对方声音)
        - 右声道: 麦克风 (我方声音)
        """
        # 在锁内获取帧数据副本
        with self.frames_lock:
            system_frames_copy = self.system_frames.copy()
            mic_frames_copy = self.mic_frames.copy()
        
        if not system_frames_copy and not mic_frames_copy:
            return
        
        try:
            # 合并帧数据
            if system_frames_copy:
                system_data = np.concatenate(system_frames_copy, axis=0)
                # 如果是双声道，转换为单声道 (取平均)
                if len(system_data.shape) > 1 and system_data.shape[1] > 1:
                    system_data = np.mean(system_data, axis=1, keepdims=True)
            else:
                system_data = None
            
            if mic_frames_copy:
                mic_data = np.concatenate(mic_frames_copy, axis=0)
                # 如果是双声道，转换为单声道
                if len(mic_data.shape) > 1 and mic_data.shape[1] > 1:
                    mic_data = np.mean(mic_data, axis=1, keepdims=True)
            else:
                mic_data = None
            
            # 确定最终长度（取较长的）
            if system_data is not None and mic_data is not None:
                max_len = max(len(system_data), len(mic_data))
                # 填充较短的数组
                if len(system_data) < max_len:
                    padding = np.zeros((max_len - len(system_data), 1), dtype=np.int16)
                    system_data = np.concatenate([system_data, padding], axis=0)
                if len(mic_data) < max_len:
                    padding = np.zeros((max_len - len(mic_data), 1), dtype=np.int16)
                    mic_data = np.concatenate([mic_data, padding], axis=0)
                
                # 组合成双声道: [左声道(系统), 右声道(麦克风)]
                stereo_data = np.concatenate([system_data, mic_data], axis=1)
                
            elif system_data is not None:
                # 只有系统声音，复制成双声道
                stereo_data = np.concatenate([system_data, system_data], axis=1)
                
            elif mic_data is not None:
                # 只有麦克风，复制成双声道
                stereo_data = np.concatenate([mic_data, mic_data], axis=1)
            else:
                raise RuntimeError("没有音频数据可保存")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.current_filepath) or '.', exist_ok=True)
            
            # 保存为 WAV
            with wave.open(self.current_filepath, 'wb') as wf:
                wf.setnchannels(2)  # 双声道立体声
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(stereo_data.astype(np.int16).tobytes())
            
            print(f"录音已保存: {self.current_filepath}")
            print(f"文件大小: {os.path.getsize(self.current_filepath) / 1024:.1f} KB")
            print(f"格式: 双声道立体声 (左=对方, 右=我方)")
            
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
            
            return len(found_processes) > 0
        except Exception as e:
            print(f"检查进程失败: {e}")
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
