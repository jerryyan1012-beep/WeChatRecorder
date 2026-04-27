#!/usr/bin/env python3
"""
简单的图标生成脚本 - 不依赖外部库
使用纯 Python 生成 BMP 然后转换为 ICO
"""
import os
import struct


def create_bmp_data(width, height, pixels):
    """创建 BMP 图像数据"""
    # BMP 文件头
    row_size = (width * 4 + 3) & ~3  # 每行字节数，4字节对齐
    image_size = row_size * height
    header_size = 54
    file_size = header_size + image_size
    
    # BMP 头
    header = bytearray(header_size)
    header[0:2] = b'BM'  # 签名
    struct.pack_into('<I', header, 2, file_size)  # 文件大小
    struct.pack_into('<HH', header, 6, 0, 0)  # 保留
    struct.pack_into('<I', header, 10, header_size)  # 数据偏移
    struct.pack_into('<I', header, 14, 40)  # DIB 头大小
    struct.pack_into('<i', header, 18, width)  # 宽度
    struct.pack_into('<i', header, 22, -height)  # 高度（负值表示从上到下）
    struct.pack_into('<H', header, 26, 1)  # 平面数
    struct.pack_into('<H', header, 28, 32)  # 位深度（32位RGBA）
    struct.pack_into('<I', header, 30, 0)  # 压缩方式
    struct.pack_into('<I', header, 34, image_size)  # 图像大小
    struct.pack_into('<i', header, 38, 2835)  # 水平分辨率
    struct.pack_into('<i', header, 42, 2835)  # 垂直分辨率
    struct.pack_into('<I', header, 46, 0)  # 颜色数
    struct.pack_into('<I', header, 50, 0)  # 重要颜色数
    
    # 图像数据（BGRA 格式，从下到上）
    image_data = bytearray(image_size)
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            offset = (height - 1 - y) * row_size + x * 4
            image_data[offset:offset+4] = bytes([b, g, r, a])
    
    return bytes(header) + bytes(image_data)


def create_ico_file(output_path, sizes=[16, 32, 48, 64, 128, 256]):
    """创建 ICO 文件"""
    
    def draw_icon(size):
        """绘制图标"""
        pixels = []
        scale = size / 256.0
        margin = int(8 * scale)
        
        for y in range(size):
            for x in range(size):
                # 默认透明
                r, g, b, a = 0, 0, 0, 0
                
                # 背景渐变（绿色）
                if margin <= x < size - margin and margin <= y < size - margin:
                    progress = (y - margin) / max(1, size - 2 * margin)
                    r = int(76 - 20 * progress)
                    g = int(175 - 30 * progress)
                    b = int(80 - 20 * progress)
                    a = 255
                
                # 圆角裁剪
                corner_r = int(40 * scale)
                # 简单处理：四个角透明
                if (x < margin + corner_r and y < margin + corner_r) or \
                   (x >= size - margin - corner_r and y < margin + corner_r) or \
                   (x < margin + corner_r and y >= size - margin - corner_r) or \
                   (x >= size - margin - corner_r and y >= size - margin - corner_r):
                    # 检查是否在圆角内
                    if x < margin + corner_r:
                        cx = margin + corner_r
                    else:
                        cx = size - margin - corner_r - 1
                    if y < margin + corner_r:
                        cy = margin + corner_r
                    else:
                        cy = size - margin - corner_r - 1
                    dx = x - cx
                    dy = y - cy
                    if dx * dx + dy * dy > corner_r * corner_r:
                        r, g, b, a = 0, 0, 0, 0
                
                # 麦克风图标（白色圆形）
                center_x = size // 2
                center_y = size // 2
                mic_radius = int(60 * scale)
                mic_y_offset = int(-10 * scale)
                
                dx = x - center_x
                dy = y - (center_y + mic_y_offset)
                if dx * dx + dy * dy < mic_radius * mic_radius:
                    r, g, b, a = 255, 255, 255, 230
                
                # 红点（右上角）
                dot_radius = int(20 * scale)
                dot_x = size - margin - int(30 * scale)
                dot_y = margin + int(30 * scale)
                dx = x - dot_x
                dy = y - dot_y
                if dx * dx + dy * dy < dot_radius * dot_radius:
                    r, g, b, a = 255, 50, 50, 255
                
                pixels.append((r, g, b, a))
        
        return pixels
    
    # ICO 文件头
    ico_header = bytearray(6)
    ico_header[0] = 0  # 保留
    ico_header[1] = 0  # 保留
    ico_header[2] = 1  # 图标类型（1=ICO）
    struct.pack_into('<H', ico_header, 4, len(sizes))  # 图像数量
    
    # 图像目录
    directory = bytearray()
    image_data_list = []
    offset = 6 + len(sizes) * 16
    
    for size in sizes:
        pixels = draw_icon(size)
        bmp_data = create_bmp_data(size, size * 2, pixels)  # 高度*2用于XOR和AND掩码
        
        # 目录项
        entry = bytearray(16)
        entry[0] = size if size < 256 else 0  # 宽度
        entry[1] = size if size < 256 else 0  # 高度
        entry[2] = 0  # 颜色数（0=真彩色）
        entry[3] = 0  # 保留
        entry[4:6] = struct.pack('<H', 1)  # 颜色平面
        entry[6:8] = struct.pack('<H', 32)  # 位深度
        entry[8:12] = struct.pack('<I', len(bmp_data))  # 数据大小
        entry[12:16] = struct.pack('<I', offset)  # 数据偏移
        
        directory.extend(entry)
        image_data_list.append(bmp_data)
        offset += len(bmp_data)
    
    # 写入文件
    with open(output_path, 'wb') as f:
        f.write(ico_header)
        f.write(directory)
        for data in image_data_list:
            f.write(data)
    
    print(f"图标已生成: {output_path}")


if __name__ == "__main__":
    create_ico_file("app_icon.ico")
