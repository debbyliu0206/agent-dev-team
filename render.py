import json
import glob
import os
import math
from PIL import Image, ImageDraw, ImageFont

def render_excalidraw(filepath):
    print(f"Rendering {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    elements = data.get('elements', [])
    if not elements:
        print(f"No elements in {filepath}")
        return
        
    # Calculate extents
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for el in elements:
        x, y = el.get('x', 0), el.get('y', 0)
        w, h = el.get('width', 0), el.get('height', 0)
        
        # for arrows, we might need to look at points
        if el.get('type') == 'arrow':
            points = el.get('points', [])
            for pt in points:
                px = x + pt[0]
                py = y + pt[1]
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)
        else:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

    padding = 50
    if min_x == float('inf'):
        min_x, min_y, max_x, max_y = 0, 0, 800, 600

    width = int(max_x - min_x + 2 * padding)
    height = int(max_y - min_y + 2 * padding)
    
    # Ensure min dimensions
    width = max(width, 100)
    height = max(height, 100)
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a truetype font, else use default
    try:
        # typical windows font
        default_font_name = "arial.ttf"
        font_large = ImageFont.truetype(default_font_name, 20)
    except IOError:
        font_large = ImageFont.load_default()
        
    def get_font(size):
        try:
            return ImageFont.truetype("arial.ttf", int(size))
        except:
            return font_large
            
    # Draw elements
    for el in elements:
        t = el.get('type')
        x = el.get('x', 0) - min_x + padding
        y = el.get('y', 0) - min_y + padding
        w = el.get('width', 0)
        h = el.get('height', 0)
        bg_color = el.get('backgroundColor', 'transparent')
        if bg_color == 'transparent':
            bg_color = None
        stroke_color = el.get('strokeColor', 'black')
        
        if t == 'rectangle':
            # Draw filled rounded rect
            draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=bg_color, outline=stroke_color, width=2)
        elif t == 'text':
            text = el.get('text', '')
            font_size = el.get('fontSize', 20)
            fnt = get_font(font_size)
            draw.text((x, y), text, fill=stroke_color, font=fnt)
        elif t == 'arrow':
            points = el.get('points', [])
            if not points:
                continue
            # draw lines
            abs_points = [(x + pt[0] - min_x + padding, y + pt[1] - min_y + padding) for pt in points]
            draw.line(abs_points, fill=stroke_color, width=2)
            
            # Draw arrowhead at the end (last point)
            if len(abs_points) >= 2:
                p1 = abs_points[-2]
                p2 = abs_points[-1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                angle = math.atan2(dy, dx)
                arrow_len = 15
                arrow_angle = math.pi / 6
                left_x = p2[0] - arrow_len * math.cos(angle - arrow_angle)
                left_y = p2[1] - arrow_len * math.sin(angle - arrow_angle)
                right_x = p2[0] - arrow_len * math.cos(angle + arrow_angle)
                right_y = p2[1] - arrow_len * math.sin(angle + arrow_angle)
                draw.polygon([p2, (left_x, left_y), (right_x, right_y)], fill=stroke_color)
                
    out_path = filepath.replace('.excalidraw', '.jpg')
    img.save(out_path, 'JPEG', quality=95)
    print(f"Saved {out_path}")

def main():
    files = glob.glob('docs/diagrams/*.excalidraw')
    for f in files:
        render_excalidraw(f)

if __name__ == '__main__':
    main()
