"""
测试脚本 - 验证录音功能
"""
import os
import sys
import time
import threading


def test_audio_devices():
    """测试音频设备"""
    print("=" * 50)
    print("测试音频设备")
    print("=" * 50)
    
    try:
        import sounddevice as sd
        
        print("\n可用音频设备:")
        devices = sd.query_devices()
        
        for i, device in enumerate(devices):
            hostapi = device.get('hostapi', -1)
            hostapi_name = sd.query_hostapis(hostapi)['name'] if hostapi >= 0 else 'Unknown'
            
            print(f"\n  [{i}] {device['name']}")
            print(f"      Host API: {hostapi_name}")
            print(f"      输入通道: {device['max_input_channels']}")
            print(f"      输出通道: {device['max_output_channels']}")
            print(f"      默认采样率: {device['default_samplerate']}")
            
            # 标记 WASAPI Loopback 设备
            if hostapi_name == 'Windows WASAPI' and 'Loopback' in device['name']:
                print(f"      >>> WASAPI Loopback 设备 <<<")
        
        # 查找默认输出设备
        try:
            default_output = sd.query_devices(kind='output')
            print(f"\n默认输出设备: [{default_output['index']}] {default_output['name']}")
        except Exception as e:
            print(f"\n获取默认输出设备失败: {e}")
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    
    return True


def test_recording(duration=5):
    """测试录音功能"""
    print("\n" + "=" * 50)
    print(f"测试录音 ({duration} 秒)")
    print("=" * 50)
    
    try:
        from audio_recorder import AudioRecorder
        
        recorder = AudioRecorder()
        
        print(f"\n开始录音，请播放一些音频...")
        filepath = recorder.start_recording("test_recording")
        print(f"录音文件: {filepath}")
        
        # 录音中显示进度
        for i in range(duration):
            time.sleep(1)
            info = recorder.get_recording_info()
            print(f"  录音中... {i+1}/{duration} 秒", end='\r')
        
        print()
        
        # 停止录音
        final_path = recorder.stop_recording()
        print(f"录音已保存: {final_path}")
        
        # 检查文件
        if os.path.exists(final_path):
            size = os.path.getsize(final_path)
            print(f"文件大小: {size / 1024:.2f} KB")
            return True
        else:
            print("错误: 文件未创建")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wechat_detection():
    """测试微信检测"""
    print("\n" + "=" * 50)
    print("测试微信检测")
    print("=" * 50)
    
    try:
        from audio_recorder import WeChatCallDetector
        
        detector = WeChatCallDetector()
        
        status = detector.get_status()
        print(f"\n微信运行状态: {'运行中' if status['wechat_running'] else '未运行'}")
        print(f"检测器状态: {'运行中' if status['is_running'] else '已停止'}")
        
        # 启动检测器
        detector.start_detection()
        
        print("\n检测器已启动，正在监听 5 秒...")
        time.sleep(5)
        
        status = detector.get_status()
        print(f"通话状态: {'通话中' if status['is_in_call'] else '未通话'}")
        
        detector.stop_detection()
        print("检测器已停止")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui():
    """测试 GUI 界面"""
    print("\n" + "=" * 50)
    print("测试 GUI 界面")
    print("=" * 50)
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("PyQt6 导入成功")
        
        # 检查是否能创建应用实例
        app = QApplication.instance()
        if app is None:
            print("可以创建 QApplication 实例")
        else:
            print("QApplication 实例已存在")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("微信通话录音软件 - 功能测试")
    print("=" * 50)
    
    results = []
    
    # 测试 1: 音频设备
    results.append(("音频设备检测", test_audio_devices()))
    
    # 测试 2: 录音功能
    results.append(("录音功能", test_recording(duration=3)))
    
    # 测试 3: 微信检测
    results.append(("微信检测", test_wechat_detection()))
    
    # 测试 4: GUI
    results.append(("GUI 界面", test_gui()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败，请检查错误信息")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
