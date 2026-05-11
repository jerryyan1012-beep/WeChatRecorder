# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import pyaudio
import sounddevice
import soundfile

block_cipher = None

# 获取库路径
pyaudio_dir = os.path.dirname(pyaudio.__file__)
sounddevice_dir = os.path.dirname(sounddevice.__file__)
soundfile_dir = os.path.dirname(soundfile.__file__)

print(f"PyAudio dir: {pyaudio_dir}")
print(f"Sounddevice dir: {sounddevice_dir}")
print(f"Soundfile dir: {soundfile_dir}")

# 收集二进制文件
binaries = []

# PyAudio binaries
if os.path.exists(pyaudio_dir):
    for f in os.listdir(pyaudio_dir):
        if f.endswith('.pyd') or f.endswith('.dll'):
            binaries.append((os.path.join(pyaudio_dir, f), '.'))
            print(f"Adding PyAudio binary: {f}")

# Sounddevice binaries (portaudio)
sounddevice_data = os.path.join(sounddevice_dir, '_sounddevice_data')
if os.path.exists(sounddevice_data):
    for root, dirs, files in os.walk(sounddevice_data):
        for f in files:
            if f.endswith('.dll') or f.endswith('.pyd'):
                src = os.path.join(root, f)
                rel_path = os.path.relpath(root, sounddevice_dir)
                binaries.append((src, rel_path))
                print(f"Adding Sounddevice binary: {src} -> {rel_path}")

# Soundfile binaries
if os.path.exists(soundfile_dir):
    for f in os.listdir(soundfile_dir):
        if f.endswith('.dll') or f.endswith('.pyd') or 'libsndfile' in f.lower():
            binaries.append((os.path.join(soundfile_dir, f), '.'))
            print(f"Adding Soundfile binary: {f}")

a = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[
        'pyaudio',
        'sounddevice',
        'soundfile',
        'numpy',
        'numpy.core._dtype_ctypes',
        'psutil',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WeChatRecorder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
