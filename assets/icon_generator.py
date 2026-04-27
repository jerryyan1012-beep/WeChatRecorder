"""
应用图标生成器 - 生成 ICO 格式的 Windows 图标
"""
import os
from PIL import Image, ImageDraw, ImageFont


def create_wechat_recorder_icon(output_path="app_icon.ico"):
    """
    创建微信录音软件的图标
    使用渐变背景和麦克风图案
    """
    # 创建不同尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # 创建图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 计算缩放比例
        scale = size / 256.0
        
        # 绘制渐变背景（圆角矩形）
        margin = int(8 * scale)
        corner_radius = int(40 * scale)
        
        # 创建渐变效果
        for y in range(margin, size - margin):
            progress = (y - margin) / (size - 2 * margin)
            # 从绿色到深绿色的渐变
            r = int(76 - 20 * progress)
            g = int(175 - 30 * progress)
            b = int(80 - 20 * progress)
            draw.line(
                [(margin, y), (size - margin, y)],
                fill=(r, g, b, 255),
                width=1
            )
        
        # 绘制圆角矩形边框
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=corner_radius,
            outline=(255, 255, 255, 100),
            width=max(1, int(4 * scale))
        )
        
        # 绘制麦克风图标
        center_x = size // 2
        center_y = size // 2
        
        # 麦克风主体（圆形）
        mic_radius = int(60 * scale)
        mic_y_offset = int(-10 * scale)
        draw.ellipse(
            [center_x - mic_radius, center_y - mic_radius + mic_y_offset,
             center_x + mic_radius, center_y + mic_radius + mic_y_offset],
            fill=(255, 255, 255, 230),
            outline=(200, 200, 200, 255),
            width=max(1, int(3 * scale))
        )
        
        # 麦克风网格线
        line_color = (180, 180, 180, 200)
        grid_spacing = int(20 * scale)
        for i in range(-2, 3):
            x = center_x + i * grid_spacing
            draw.line(
                [(x, center_y - mic_radius + mic_y_offset + int(10*scale)),
                 (x, center_y + mic_radius + mic_y_offset - int(10*scale))],
                fill=line_color,
                width=max(1, int(2 * scale))
            )
        
        # 麦克风支架（底部弧线）
        arc_y = center_y + mic_radius + mic_y_offset + int(15 * scale)
        draw.arc(
            [center_x - mic_radius, arc_y - int(20*scale),
             center_x + mic_radius, arc_y + int(20*scale)],
            start=0, end=180,
            fill=(255, 255, 255, 230),
            width=max(2, int(6 * scale))
        )
        
        # 支架竖线
        draw.line(
            [(center_x, arc_y),
             (center_x, arc_y + int(30 * scale))],
            fill=(255, 255, 255, 230),
            width=max(2, int(6 * scale))
        )
        
        # 底座
        base_width = int(40 * scale)
        base_height = int(8 * scale)
        draw.rounded_rectangle(
            [center_x - base_width, arc_y + int(25 * scale),
             center_x + base_width, arc_y + int(35 * scale)],
            radius=int(4 * scale),
            fill=(255, 255, 255, 230)
        )
        
        # 添加录音指示红点（右上角）
        dot_radius = int(20 * scale)
        dot_x = size - margin - int(30 * scale)
        dot_y = margin + int(30 * scale)
        draw.ellipse(
            [dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius],
            fill=(255, 50, 50, 255),
            outline=(255, 255, 255, 200),
            width=max(1, int(3 * scale))
        )
        
        images.append(img)
    
    # 保存为 ICO 文件
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    
    print(f"图标已生成: {output_path}")
    return output_path


def create_png_icons(output_dir="assets"):
    """生成 PNG 格式的图标（用于其他用途）"""
    os.makedirs(output_dir, exist_ok=True)
    
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        # 创建图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        scale = size / 256.0
        margin = int(8 * scale)
        corner_radius = int(40 * scale)
        
        # 渐变背景
        for y in range(margin, size - margin):
            progress = (y - margin) / (size - 2 * margin)
            r = int(76 - 20 * progress)
            g = int(175 - 30 * progress)
            b = int(80 - 20 * progress)
            draw.line(
                [(margin, y), (size - margin, y)],
                fill=(r, g, b, 255),
                width=1
            )
        
        # 边框
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=corner_radius,
            outline=(255, 255, 255, 100),
            width=max(1, int(4 * scale))
        )
        
        # 麦克风图标
        center_x = size // 2
        center_y = size // 2
        mic_radius = int(60 * scale)
        mic_y_offset = int(-10 * scale)
        
        draw.ellipse(
            [center_x - mic_radius, center_y - mic_radius + mic_y_offset,
             center_x + mic_radius, center_y + mic_radius + mic_y_offset],
            fill=(255, 255, 255, 230),
            outline=(200, 200, 200, 255),
            width=max(1, int(3 * scale))
        )
        
        # 网格线
        line_color = (180, 180, 180, 200)
        grid_spacing = int(20 * scale)
        for i in range(-2, 3):
            x = center_x + i * grid_spacing
            draw.line(
                [(x, center_y - mic_radius + mic_y_offset + int(10*scale)),
                 (x, center_y + mic_radius + mic_y_offset - int(10*scale))],
                fill=line_color,
                width=max(1, int(2 * scale))
            )
        
        # 支架
        arc_y = center_y + mic_radius + mic_y_offset + int(15 * scale)
        draw.arc(
            [center_x - mic_radius, arc_y - int(20*scale),
             center_x + mic_radius, arc_y + int(20*scale)],
            start=0, end=180,
            fill=(255, 255, 255, 230),
            width=max(2, int(6 * scale))
        )
        
        draw.line(
            [(center_x, arc_y),
             (center_x, arc_y + int(30 * scale))],
            fill=(255, 255, 255, 230),
            width=max(2, int(6 * scale))
        )
        
        base_width = int(40 * scale)
        draw.rounded_rectangle(
            [center_x - base_width, arc_y + int(25 * scale),
             center_x + base_width, arc_y + int(35 * scale)],
            radius=int(4 * scale),
            fill=(255, 255, 255, 230)
        )
        
        # 红点
        dot_radius = int(20 * scale)
        dot_x = size - margin - int(30 * scale)
        dot_y = margin + int(30 * scale)
        draw.ellipse(
            [dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius],
            fill=(255, 50, 50, 255),
            outline=(255, 255, 255, 200),
            width=max(1, int(3 * scale))
        )
        
        # 保存
        output_path = os.path.join(output_dir, f"icon_{size}x{size}.png")
        img.save(output_path)
        print(f"生成: {output_path}")


if __name__ == "__main__":
    # 生成 ICO 文件
    create_wechat_recorder_icon("app_icon.ico")
    
    # 生成 PNG 图标
    create_png_icons("assets/icons")
    
    print("\n所有图标生成完成!")
