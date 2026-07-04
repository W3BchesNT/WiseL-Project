# Library/Core/Fluent.py
"""База Fluent: стили, пропсы, создание виджетов, генерация .data"""
import re

ALL_PROPS = {
    "title":        {"key": "text",       "type": "str",   "default": "Button"},
    "x":            {"key": "x",          "type": "int",   "default": 0},
    "y":            {"key": "y",          "type": "int",   "default": 0},
    "width":        {"key": "w",          "type": "int",   "default": 100},
    "height":       {"key": "h",          "type": "int",   "default": 30},
    "background":   {"key": "bg",         "type": "color", "default": "#2D2D2D"},
    "font_color":   {"key": "font_color", "type": "color", "default": "#FFFFFF"},
    "border_color": {"key": "border_color","type": "color", "default": "#3F3F46"},
    "font_size":    {"key": "font_size",  "type": "int",   "default": 14},
    "placeholder":  {"key": "placeholder","type": "str",   "default": ""},
    "scrollbar":    {"key": "scrollbar",  "type": "str",   "default": "no"},
    "anchor_right": {"key": "anchor_right", "type": "str", "default": "false"},
    "anchor_bottom": {"key": "anchor_bottom", "type": "str", "default": "false"},
    "margin_right": {"key": "margin_r", "type": "int", "default": 10},
    "margin_bottom": {"key": "margin_b", "type": "int", "default": 10},
    "gravity":      {"key": "gravity",   "type": "str",   "default": "center"},
    "src":          {"key": "src",        "type": "str",   "default": ""},
    "scale_type":   {"key": "scale_type", "type": "str",   "default": "fit"},
}

WIDGET_TYPES = {
    "fluent_btn": {
        "props":   ["title", "x", "y", "width", "height", "background", "font_color", "border_color", "gravity"],
        "events":  ["onHover", "onClick"],
        "state":   True,
    },
    "fluent_label": {
        "props":   ["title", "x", "y", "width", "height", "font_color", "font_size", "gravity"],
        "events":  [],
        "state":   False,
        "def":     {"font_color": "#000000"},
    },
    "fluent_editline": {
        "props":   ["title", "x", "y", "width", "height", "background", "font_color", "border_color", "font_size", "placeholder"],
        "events":  [],
        "state":   False,
        "def":     {"font_size": 14, "width": 200},
    },
    "fluent_textbox": {
        "props":   ["title", "x", "y", "width", "height", "background", "font_color", "border_color", "font_size", "placeholder", "scrollbar"],
        "events":  [],
        "state":   False,
        "def":     {"font_size": 14, "width": 200, "height": 100, "title": ""},
    },
    "fluent_image": {
        "props":   ["x", "y", "width", "height", "src", "scale_type", "background", "border_color", "anchor_right", "anchor_bottom", "margin_right", "margin_bottom"],
        "events":  ["onClick"],
        "state":   False,
        "def":     {"width": 100, "height": 100},
    },
    "fluent_canvas": {
        "props":   ["x", "y", "width", "height", "background"],
        "events":  [],
        "state":   False,
        "def":     {"width": 200, "height": 200, "background": "#FFFFFF"},
    },
}

EVENT_PREFIX = {None: "", "onHover": "hover_", "onClick": "click_", "onFocus": "focus_", "onBlur": "blur_"}
STYLES = {}

def hex_to_bgr(hex_color):
    c = hex_color.replace("#", "").replace('"', "").strip()
    if len(c) == 6:
        return f"0x00{c[4:6]}{c[2:4]}{c[0:2]}"
    return f"0x00{c}"

def data_section():
    return ["WiseInit64"]

def _to_int(val):
    try: return int(val)
    except (ValueError, TypeError): return val

def _utf16(text):
    chars = []
    for c in str(text):
        chars.append(f"0x{ord(c):04X}")
    chars.append("0")
    return ", ".join(chars)

def _rect_line(prefix, wid, w, def_w=100, def_h=30):
    x = int(w.get('x', 0)) if not isinstance(w.get('x', 0), str) else 0
    y = int(w.get('y', 0)) if not isinstance(w.get('y', 0), str) else 0
    ww = int(w.get('w', def_w)) if not isinstance(w.get('w', def_w), str) else def_w
    hh = int(w.get('h', def_h)) if not isinstance(w.get('h', def_h), str) else def_h
    return f"  {prefix}_rect_{wid} RECT {x}, {y}, {x + ww}, {y + hh}"

def set_prop(w, key, value):
    if key not in ALL_PROPS: return
    p = ALL_PROPS[key]
    rk = p["key"]
    if p["type"] == "int" and isinstance(value, str) and value.endswith("%"):
        w[rk + "_pct"] = int(value[:-1])
        w[rk] = 0
        return
    if p["type"] == "int":
        w[rk] = _to_int(value)
    elif p["type"] == "str":
        w[rk] = str(value)
    else:
        w[rk] = value

def set_event_prop(w, event, key, value):
    if key not in ALL_PROPS: return
    p = ALL_PROPS[key]
    rk = EVENT_PREFIX.get(event, "") + p["key"]
    if p["type"] == "int":
        w[rk] = _to_int(value)
    elif p["type"] == "str":
        w[rk] = str(value)
    else:
        w[rk] = value

def create_widget(wtype, name, id_map, counter):
    if name not in id_map:
        counter += 1
        id_map[name] = str(counter)
    info = WIDGET_TYPES[wtype]
    w = {"type": wtype, "id": id_map[name], "name": name}
    for pn in info["props"]:
        pi = ALL_PROPS[pn]
        default = info.get("def", {}).get(pn, pi["default"])
        w[pi["key"]] = default
    for ev in info["events"]:
        prefix = EVENT_PREFIX.get(ev, "")
        for pn in info["props"]:
            w[prefix + ALL_PROPS[pn]["key"]] = None
    return w, counter

def parse_styles(code):
    STYLES.clear()
    cur = None
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r'style\s+"(.*?)"\s*:', line)
        if m:
            cur = m.group(1)
            STYLES[cur] = {"props": {}, "hover": {}, "focus": {}, "click": {}}
            continue
        if cur and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"')
            if k.startswith("hover."):
                _add_style_prop(cur, "hover", k[6:], v)
            elif k.startswith("focus."):
                _add_style_prop(cur, "focus", k[6:], v)
            elif k.startswith("click."):
                _add_style_prop(cur, "click", k[6:], v)
            else:
                _add_style_prop(cur, "props", k, v)
            continue
        if re.match(r"(window\s+|Form\d+\.|Button\d+\.|Label\d+\.|EditLine\d+\.|TextBox\d+\.)", line):
            cur = None
    return STYLES

def _add_style_prop(style_name, section, prop_name, value):
    if prop_name not in ALL_PROPS: return
    key = ALL_PROPS[prop_name]["key"]
    STYLES[style_name][section][key] = _to_int(value) if ALL_PROPS[prop_name]["type"] == "int" else value

def apply_style(w, style_name):
    if style_name not in STYLES: return
    s = STYLES[style_name]
    for k, v in s["props"].items(): w[k] = v
    for k, v in s["hover"].items(): w["hover_" + k] = v
    for k, v in s["focus"].items(): w["focus_" + k] = v
    for k, v in s["click"].items(): w["click_" + k] = v

def finalize_props(w):
    info = WIDGET_TYPES[w["type"]]
    for ev in info["events"]:
        prefix = EVENT_PREFIX.get(ev, "")
        for pn in info["props"]:
            key = prefix + ALL_PROPS[pn]["key"]
            if key not in w or w[key] is None:
                w[key] = w.get(ALL_PROPS[pn]["key"], ALL_PROPS[pn]["default"])

def resolve_pct(w, win_w, win_h):
    for key in list(w.keys()):
        if key.endswith("_pct"):
            bk = key[:-4]
            pct = w[key]
            if bk in ("x","w","click_x","click_w","hover_x","hover_w","focus_x","focus_w"):
                w[bk] = (pct * win_w) // 100
            elif bk in ("y","h","click_y","click_h","hover_y","hover_h","focus_y","focus_h"):
                w[bk] = (pct * win_h) // 100
            del w[key]

def _input_data(w, prefix, def_h):
    wid = w["id"]
    return [
        f"  hEdit_{wid} dq 0",
        f"  edit_brush_{wid} dq 0",
        _rect_line(prefix, wid, w, 200, def_h),
        f"  {prefix}_bg_{wid} dd {hex_to_bgr(w.get('bg','#2D2D2D'))}",
        f"  {prefix}_font_{wid} dd {hex_to_bgr(w.get('font_color','#FFFFFF'))}",
        f"  {prefix}_border_{wid} dd {hex_to_bgr(w.get('border_color','#3F3F46'))}",
        f"  {prefix}_font_size_{wid} dd {w.get('font_size',14)}",
    ]

def widget_data(w):
    wid = w["id"]
    x = int(w.get('x', 0)) if not isinstance(w.get('x', 0), str) else 0
    y = int(w.get('y', 0)) if not isinstance(w.get('y', 0), str) else 0
    ww = int(w.get('w', 100)) if not isinstance(w.get('w', 100), str) else 100
    hh = int(w.get('h', 30)) if not isinstance(w.get('h', 30), str) else 30
    text = str(w.get("text", "Button"))
    gravity = w.get("gravity", "left")
    gravity_map = {"left": "0x10", "center": "37", "right": "0x12"}
    gravity_flag = gravity_map.get(gravity, "0x10")
    
    lines = [
        f"  _btn_text_{wid} dw {_utf16(text)}",
        _rect_line("btn", wid, w),
        f"  btn_state_{wid} dd 0",
        f"  btn_gravity_{wid} dd {gravity_flag}",
    ]
    for pfx in ["", "hover_", "click_"]:
        p = pfx if pfx else ""
        lines += [
            f"  btn_bg_{p}{wid} dd {hex_to_bgr(w.get(pfx+'bg', w.get('bg','#2D2D2D')))}",
            f"  btn_font_{p}{wid} dd {hex_to_bgr(w.get(pfx+'font_color', w.get('font_color','#FFFFFF')))}",
            f"  btn_border_{p}{wid} dd {hex_to_bgr(w.get(pfx+'border_color', w.get('border_color','#3F3F46')))}",
        ]
    lines.append(f"  btn_rect_hover_{wid} RECT {x}, {y}, {x + ww}, {y + hh}")
    click_text = str(w.get('click_text', text))
    lines.append(f"  _btn_text_click_{wid} dw {_utf16(click_text)}")
    cx = int(w.get('click_x', x)) if not isinstance(w.get('click_x', x), str) else x
    cy = int(w.get('click_y', y)) if not isinstance(w.get('click_y', y), str) else y
    cw = int(w.get('click_w', ww)) if not isinstance(w.get('click_w', ww), str) else ww
    ch = int(w.get('click_h', hh)) if not isinstance(w.get('click_h', hh), str) else hh
    lines.append(f"  btn_rect_click_{wid} RECT {cx}, {cy}, {cx + cw}, {cy + ch}")
    return lines

def label_data(w):
    wid = w["id"]
    gravity = w.get("gravity", "left")
    gravity_map = {"left": "0x10", "center": "37", "right": "0x12"}
    gravity_flag = gravity_map.get(gravity, "0x10")
    
    lines = [
        f"  _label_text_{wid} dw {_utf16(w.get('text','Label'))}",
        _rect_line("label", wid, w, 300),
        f"  label_font_{wid} dd {hex_to_bgr(w.get('font_color','#000000'))}",
        f"  label_font_size_{wid} dd {w.get('font_size',14)}",
        f"  label_gravity_{wid} dd {gravity_flag}",
    ]
    return lines

def image_data(w):
    wid = w["id"]
    src = w.get("src", "")
    x = int(w.get('x', 0)) if not isinstance(w.get('x', 0), str) else 0
    y = int(w.get('y', 0)) if not isinstance(w.get('y', 0), str) else 0
    ww = int(w.get('w', 100)) if not isinstance(w.get('w', 100), str) else 100
    hh = int(w.get('h', 100)) if not isinstance(w.get('h', 100), str) else 100
    scale_type = w.get("scale_type", "fit")
    
    lines = [
        f"  img_rect_{wid} RECT {x}, {y}, {x + ww}, {y + hh}",
        f"  img_loaded_{wid} dd 0",
        f"  img_src_w_{wid} dd 0",
        f"  img_src_h_{wid} dd 0",
        f"  img_scale_{wid} db '{scale_type}',0",
        f"  img_pImage_{wid} dq 0",
        f"  img_pGraph_{wid} dq 0",
        f"  img_wstr_{wid} du '{src}',0",
        f"  img_bg_{wid} dd {hex_to_bgr(w.get('bg','#2D2D2D'))}",
        f"  img_border_{wid} dd {hex_to_bgr(w.get('border_color','#3F3F46'))}",
        f"  img_cache_dc_{wid} dq 0",
        f"  img_cache_bmp_{wid} dq 0",
        f"  img_cache_old_{wid} dq 0",
        f"  img_cache_w_{wid} dd 0",
        f"  img_cache_h_{wid} dd 0",
        f"  img_black_brush_{wid} dq 0",
    ]
    return lines

def canvas_data(w):
    wid = w["id"]
    lines = [
        _rect_line("canvas", wid, w, 200, 200),
        f"  canvas_bg_{wid} dd {hex_to_bgr(w.get('bg','#FFFFFF'))}",
    ]
    return lines

# В конец Fluent.py добавить:
def gen_title(context, **kwargs):
    TITLE = {
        "window":       lambda name, value: (f"  _title_{name} du {_utf16(value)}", None),
        "menu_label":   lambda name, value: (f"  menu_label_{name} du {_utf16(value)}", None),
        "menu_text":    lambda name, value: (f"  menu_text_{name} du {_utf16(value)}", None),
        "menu_click":   lambda name, item_id, value, wid=None: (
            f"  _menu_text_{name}_{item_id} du {_utf16(value)}",
            f"    invoke SetWindowTextW, [hEdit_{wid}], _menu_text_{name}_{item_id}"
        ),
        "textbox":      lambda wid, value: (
            f"  _init_text_{wid} du {_utf16(value)}",
            f"    invoke SetWindowTextW, [hEdit_{wid}], _init_text_{wid}"
        ),
        "textbox_set":  lambda wid: (None, f"    invoke SetWindowTextW, [hEdit_{wid}], _wide_buffer"),
        "label":        lambda wid, value: (f"  _label_text_{wid} dw {_utf16(value)}", None),
        "button":       lambda wid, value: (f"  _btn_text_{wid} dw {_utf16(value)}", None),
        "cmd_title":    lambda wid, value: (f"  _cmd_title_{wid} du {_utf16(value)}", None),
        "cmd_title_set": lambda wid: (None, f"    invoke SetWindowTextW, rbx, _cmd_title_{wid}"),
        "set_text":     lambda wid: (None, f"    invoke SetWindowTextW, [hEdit_{wid}], _wide_buffer"),
    }
    
    fn = TITLE.get(context)
    if not fn:
        print(f"  [Fluent] WARNING: unknown title context '{context}'")
        return None, None
    
    import inspect
    sig = inspect.signature(fn)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    result = fn(**filtered)
    return result if isinstance(result, tuple) else (result, None)

def editline_data(w): return _input_data(w, "edit", 30)
def textbox_data(w):  return _input_data(w, "tb", 100)