# Library/Windows/CanvasGen64.py
"""Генератор ASM для Canvas виджетов Windows x64"""
import os, sys
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path: sys.path.insert(0, CORE_PATH)
import Canvas


def _hex_to_bgr(hex_color):
    c = hex_color.lstrip('#')
    if len(c) == 6:
        return f"0x00{c[4:6]}{c[2:4]}{c[0:2]}"
    return "0x00FFFFFF"


def _utf16(text):
    chars = []
    for c in str(text):
        chars.append(f"0x{ord(c):04X}")
    chars.append("0")
    return ", ".join(chars)


def gen_data(widget):
    """Генерит .data для Canvas виджета"""
    lines = []
    x = int(widget.props.get('x', '0'))
    y = int(widget.props.get('y', '0'))
    w_str = widget.props.get('width', '200')
    h_str = widget.props.get('height', '200')
    w = 800 if str(w_str).endswith('%') else int(w_str)
    h = 600 if str(h_str).endswith('%') else int(h_str)
    bg = widget.props.get('background', '#FFFFFF')
    
    lines += [
        f"  canvas_rect_{widget.name} RECT {x}, {y}, {x+w}, {y+h}",
        f"  canvas_bg_{widget.name} dd {_hex_to_bgr(bg)}",
    ]
    
    for cmd in widget.commands:
        if isinstance(cmd, Canvas.RectCmd):
            lines += [
                f"  obj_{cmd.obj_id}_x dd {cmd.x}",
                f"  obj_{cmd.obj_id}_y dd {cmd.y}",
                f"  obj_{cmd.obj_id}_w dd {cmd.w}",
                f"  obj_{cmd.obj_id}_h dd {cmd.h}",
                f"  obj_{cmd.obj_id}_color dd {_hex_to_bgr(cmd.color)}",
            ]
        elif isinstance(cmd, Canvas.CircleCmd):
            lines += [
                f"  obj_{cmd.obj_id}_x dd {cmd.x}",
                f"  obj_{cmd.obj_id}_y dd {cmd.y}",
                f"  obj_{cmd.obj_id}_radius dd {cmd.radius}",
                f"  obj_{cmd.obj_id}_color dd {_hex_to_bgr(cmd.color)}",
            ]
        elif isinstance(cmd, Canvas.TextCmd):
            lines += [
                f"  obj_{cmd.obj_id}_x dd {cmd.x}",
                f"  obj_{cmd.obj_id}_y dd {cmd.y}",
                f"  obj_{cmd.obj_id}_text dw {_utf16(cmd.text)}",
                f"  obj_{cmd.obj_id}_color dd {_hex_to_bgr(cmd.color)}",
                f"  obj_{cmd.obj_id}_font_size dd {cmd.font_size}",
            ]
    
    return lines


def gen_paint(widget):
    """Генерит код отрисовки Canvas в WM_PAINT"""
    lines = []
    name = widget.name
    
    lines.append(f"    WiseFillRect [mem_dc], canvas_rect_{name}, [canvas_bg_{name}]")
    
    for cmd in widget.commands:
        if isinstance(cmd, Canvas.RectCmd):
            lines += [
                f"    WiseSetRect border_rect, [obj_{cmd.obj_id}_x], [obj_{cmd.obj_id}_y], [obj_{cmd.obj_id}_w], [obj_{cmd.obj_id}_h]",
                f"    WiseFillRect [mem_dc], border_rect, [obj_{cmd.obj_id}_color]",
            ]
        elif isinstance(cmd, Canvas.CircleCmd):
            lines += [
                f"    mov eax, [obj_{cmd.obj_id}_x]",
                f"    sub eax, [obj_{cmd.obj_id}_radius]",
                f"    mov [border_rect.left], eax",
                f"    mov eax, [obj_{cmd.obj_id}_y]",
                f"    sub eax, [obj_{cmd.obj_id}_radius]",
                f"    mov [border_rect.top], eax",
                f"    mov eax, [obj_{cmd.obj_id}_x]",
                f"    add eax, [obj_{cmd.obj_id}_radius]",
                f"    mov [border_rect.right], eax",
                f"    mov eax, [obj_{cmd.obj_id}_y]",
                f"    add eax, [obj_{cmd.obj_id}_radius]",
                f"    mov [border_rect.bottom], eax",
                f"    invoke CreateSolidBrush, [obj_{cmd.obj_id}_color]",
                f"    mov r13, rax",
                f"    invoke SelectObject, [mem_dc], r13",
                f"    mov r15, rax",
                f"    invoke Ellipse, [mem_dc], [border_rect.left], [border_rect.top], [border_rect.right], [border_rect.bottom]",
                f"    invoke SelectObject, [mem_dc], r15",
                f"    invoke DeleteObject, r13",
            ]
        elif isinstance(cmd, Canvas.TextCmd):
            lines += [
                f"    invoke CreateFont, [obj_{cmd.obj_id}_font_size], 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name",
                f"    mov r14, rax",
                f"    invoke SelectObject, [mem_dc], r14",
                f"    invoke SetTextColor, [mem_dc], [obj_{cmd.obj_id}_color]",
                f"    invoke SetBkMode, [mem_dc], 1",
                f"    WiseSetRect border_rect, [obj_{cmd.obj_id}_x], [obj_{cmd.obj_id}_y], 400, 30",
                f"    lea r8, [obj_{cmd.obj_id}_text]",
                f"    lea r9, [border_rect]",
                f"    invoke DrawTextW, [mem_dc], r8, -1, r9, 0x10",
                f"    invoke SelectObject, [mem_dc], [hFont]",
                f"    invoke DeleteObject, r14",
            ]
    
    return lines


def gen_resize(widget):
    """Генерит код ресайза Canvas в WM_SIZE"""
    lines = []
    name = widget.name
    wp = str(widget.props.get('width', '100%'))
    hp = str(widget.props.get('height', '100%'))
    
    if wp.endswith('%'):
        pct = int(wp[:-1])
        lines += [
            f"    mov eax, [win_width]",
            f"    imul eax, {pct}",
            f"    mov ecx, 100",
            f"    xor edx, edx",
            f"    div ecx",
            f"    mov [canvas_rect_{name}.right], eax",
        ]
    if hp.endswith('%'):
        pct = int(hp[:-1])
        lines += [
            f"    mov eax, [win_height]",
            f"    imul eax, {pct}",
            f"    mov ecx, 100",
            f"    xor edx, edx",
            f"    div ecx",
            f"    mov [canvas_rect_{name}.bottom], eax",
        ]
    
    return lines