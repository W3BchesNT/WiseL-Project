# Library/Core/Canvas.py
"""Парсер Canvas для WiseL — платформонезависимый"""
import re


class CanvasDecl:
    def __init__(self, name, props=None, commands=None):
        self.name = name
        self.props = props or {}
        self.commands = commands or []


class CanvasCommand:
    pass


class RectCmd(CanvasCommand):
    def __init__(self, obj_id, x, y, w, h, color):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color


class CircleCmd(CanvasCommand):
    def __init__(self, obj_id, x, y, radius, color):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color


class TextCmd(CanvasCommand):
    def __init__(self, obj_id, x, y, text, color, font_size=14):
        self.obj_id = obj_id
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font_size = font_size


def parse_canvas_commands(lines, start_i):
    """Парсит команды внутри onPaint: блока"""
    cmds = []
    i = start_i
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        # rect(id, x, y, w, h, "#color")
        m = re.match(r'rect\((\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*"([^"]+)"\)', line)
        if m:
            obj_id = m.group(1)
            x, y, w, h = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            color = m.group(6)
            cmds.append(RectCmd(obj_id, x, y, w, h, color))
            i += 1
            continue
        
        # circle(id, x, y, radius, "#color")
        m = re.match(r'circle\((\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*"([^"]+)"\)', line)
        if m:
            obj_id = m.group(1)
            x, y = int(m.group(2)), int(m.group(3))
            radius = int(m.group(4))
            color = m.group(5)
            cmds.append(CircleCmd(obj_id, x, y, radius, color))
            i += 1
            continue
        
        # text(id, x, y, "text", "#color")
        m = re.match(r'text\((\w+),\s*(\d+),\s*(\d+),\s*"([^"]+)",\s*"([^"]+)"\)', line)
        if m:
            obj_id = m.group(1)
            x, y = int(m.group(2)), int(m.group(3))
            text = m.group(4)
            color = m.group(5)
            cmds.append(TextCmd(obj_id, x, y, text, color))
            i += 1
            continue
        
        # text(id, x, y, "text", "#color", font_size)
        m = re.match(r'text\((\w+),\s*(\d+),\s*(\d+),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)\)', line)
        if m:
            obj_id = m.group(1)
            x, y = int(m.group(2)), int(m.group(3))
            text = m.group(4)
            color = m.group(5)
            font_size = int(m.group(6))
            cmds.append(TextCmd(obj_id, x, y, text, color, font_size))
            i += 1
            continue
        
        # fps_max = "144"
        m = re.match(r'fps_max\s*=\s*"(\d+)"', line)
        if m:
            cmds.append({'type': 'fps_max', 'value': m.group(1)})
            i += 1
            continue
        
        break
    
    return cmds, i