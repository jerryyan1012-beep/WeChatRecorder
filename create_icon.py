#!/usr/bin/env python3
"""
简单的图标生成脚本 - 生成 ICO 文件
使用 Python 标准库
"""
import os
import struct


def create_simple_ico(output_path="app_icon.ico"):
    """
    创建一个简单的 ICO 文件
    使用纯色填充，包含多种尺寸
    """
    sizes = [16, 32, 48, 64, 128, 256]
    
    # ICO 文件头
    ico_header = struct.pack('<HHH', 0, 1, len(sizes))  # 保留, 类型(1=ICO), 数量
    
    # 为每个尺寸创建图像
    images = []
    directory = bytearray()
    data_offset = 6 + len(sizes) * 16  # 头 + 目录
    
    for size in sizes:
        # 创建 PNG 格式的图像数据（更简单）
        # 这里我们创建一个简单的 BMP 格式图像
        
        # 创建 32位 BMP (BGRA)
        row_size = ((size * 4 + 3) // 4) * 4  # 4字节对齐
        image_size = row_size * size
        
        # BMP 文件头 (14字节) + DIB 头 (40字节) = 54字节
        bmp_header = bytearray(54)
        
        # BMP 文件头
        bmp_header[0:2] = b'BM'
        struct.pack_into('<I', bmp_header, 2, 54 + image_size)  # 文件大小
        struct.pack_into('<HH', bmp_header, 6, 0, 0)  # 保留
        struct.pack_into('<I', bmp_header, 10, 54)  # 数据偏移
        
        # DIB 头 (BITMAPINFOHEADER)
        struct.pack_into('<I', bmp_header, 14, 40)  # 头大小
        struct.pack_into('<i', bmp_header, 18, size)  # 宽度
        struct.pack_into('<i', bmp_header, 22, size * 2)  # 高度（XOR + AND 掩码）
        struct.pack_into('<H', bmp_header, 26, 1)  # 平面数
        struct.pack_into('<H', bmp_header, 28, 32)  # 位深度
        struct.pack_into('<I', bmp_header, 30, 0)  # 压缩
        struct.pack_into('<I', bmp_header, 34, 0)  # 图像大小（未压缩为0）
        struct.pack_into('<i', bmp_header, 38, 0)  # X分辨率
        struct.pack_into('<i', bmp_header, 42, 0)  # Y分辨率
        struct.pack_into('<I', bmp_header, 46, 0)  # 颜色数
        struct.pack_into('<I', bmp_header, 50, 0)  # 重要颜色数
        
        # 创建图像数据（从下到上）
        image_data = bytearray(image_size * 2)  # XOR + AND 掩码
        
        scale = size / 256.0
        margin = int(16 * scale)
        
        for y in range(size):
            for x in range(size):
                # 计算像素位置（BMP 是从下到上存储）
                row = (size - 1 - y)
                offset = row * row_size + x * 4
                
                # 默认透明
                b, g, r, a = 0, 0, 0, 0
                
                # 绿色背景（圆角矩形）
                if margin <= x < size - margin and margin <= y < size - margin:
                    # 检查圆角
                    corner = int(20 * scale)
                    in_corner = False
                    
                    # 左上角
                    if x < margin + corner and y < margin + corner:
                        dx = x - (margin + corner)
                        dy = y - (margin + corner)
                        if dx * dx + dy * dy > corner * corner:
                            in_corner = True
                    # 右上角
                    elif x >= size - margin - corner and y < margin + corner:
                        dx = x - (size - margin - corner - 1)
                        dy = y - (margin + corner)
                        if dx * dx + dy * dy > corner * corner:
                            in_corner = True
                    # 左下角
                    elif x < margin + corner and y >= size - margin - corner:
                        dx = x - (margin + corner)
                        dy = y - (size - margin - corner - 1)
                        if dx * dx + dy * dy > corner * corner:
                            in_corner = True
                    # 右下角
                    elif x >= size - margin - corner and y >= size - margin - corner:
                        dx = x - (size - margin - corner - 1)
                        dy = y - (size - margin - corner - 1)
                        if dx * dx + dy * dy > corner * corner:
                            in_corner = True
                    
                    if not in_corner:
                        # 渐变绿色背景
                        progress = (y - margin) / max(1, size - 2 * margin)
                        r = int(76 - 20 * progress)
                        g = int(175 - 30 * progress)
                        b = int(80 - 20 * progress)
                        a = 255
                
                # 白色麦克风图标（中心圆形）
                cx, cy = size // 2, size // 2
                mic_r = int(40 * scale)
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy < mic_r * mic_r:
                    r, g, b, a = 255, 255, 255, 255
                
                # 红色录音点（右上角）
                dot_r = int(12 * scale)
                dot_x = size - margin - int(20 * scale)
                dot_y = margin + int(20 * scale)
                dx, dy = x - dot_x, y - dot_y
                if dx * dx + dy * dy < dot_r * dot_r:
                    r, g, b, a = 255, 50, 50, 255
                
                # 写入 BGRA
                image_data[offset:offset+4] = bytes([b, g, r, a])
        
        # 组合 BMP
        bmp_data = bytes(bmp_header) + bytes(image_data)
        
        # 添加到目录
        entry = bytearray(16)
        entry[0] = size if size < 256 else 0
        entry[1] = size if size < 256 else 0
        entry[2] = 0  # 颜色数
        entry[3] = 0  # 保留
        struct.pack_into('<H', entry, 4, 1)  # 平面
        struct.pack_into('<H', entry, 6, 32)  # 位深度
        struct.pack_into('<I', entry, 8, len(bmp_data))  # 大小
        struct.pack_into('<I', entry, 12, data_offset)  # 偏移
        
        directory.extend(entry)
        images.append(bmp_data)
        data_offset += len(bmp_data)
    
    # 写入 ICO 文件
    with open(output_path, 'wb') as f:
        f.write(ico_header)
        f.write(directory)
        for img in images:
            f.write(img)
    
    print(f"✓ 图标已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    create_simple_ico()
