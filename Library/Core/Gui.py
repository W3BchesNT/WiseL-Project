# Library/Core/Gui.py
# Парсер GUI WiseL — окна, виджеты, события, меню, Canvas, хуки, таймеры
import re
import Values
import Hooks
import Timer as TimerParser
import Canvas


# AST узлы
class ASTNode: pass

class WindowDecl(ASTNode):
    # window w: + props
    def __init__(self, name, props=None):
        self.name = name
        self.props = props or {}

class WidgetDecl(ASTNode):
    # name.addFluentButton/Label/Canvas: + props + commands
    def __init__(self, name, wtype, props=None, commands=None):
        self.name = name
        self.wtype = wtype
        self.props = props or {}
        self.commands = commands or []

class EventDecl(ASTNode):
    # name.addFunction(onClick): + actions
    def __init__(self, widget, event, actions):
        self.widget = widget
        self.event = event
        self.actions = actions

class ShowWindow(ASTNode):
    # w.show()
    def __init__(self, name):
        self.name = name

class MenuDecl(ASTNode):
    # menu File "Файл": + items
    def __init__(self, name, label, items):
        self.name = name
        self.label = label
        self.items = items

class MenuItem(ASTNode):
    # item "Выход", cmdExit
    def __init__(self, label, action):
        self.label = label
        self.action = action


WIDGET_TYPES = {
    "addFluentButton": "fluent_btn",
    "addFluentLabel": "fluent_label",
    "addFluentTextbox": "fluent_textbox",
    "addFluentImageView": "fluent_image",
    "addFluentCanvas": "fluent_canvas",
}


# Парсер 3 — присваивания: width = 800, title = "WiseL", x = 10
def parse_props(lines, start_i):
    props = {}
    i = start_i
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        if "=" in line and not line.startswith(("if ", "for ", "window ", "menu ", "item ", "asm", "call ", "separator", "init ", "onPaint:", "Hook:", "key.", "Timer ")):
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"')
            props[k] = v
            i += 1
        else:
            break
    return props, i


# Главный парсер
def parse(code):
    ast = []
    lines = code.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Парсер 4 — ключевые слова и пустые строки
        if not line or line.startswith(("#", "Use", "init")):
            i += 1
            continue
        
        # Парсер 1 — объявления с двоеточием: Timer moveUp(150):
        if line.startswith("Timer "):
            timer_decls, i = TimerParser.parse_timer(lines, i)
            for t in timer_decls: ast.append(t)
            continue
        
        # Парсер 1 — объявления с двоеточием: Hook:
        if line == "Hook:":
            hook_decl, i = Hooks.parse_hook(lines, i + 1)
            if hook_decl: ast.append(hook_decl)
            continue
        
        # Парсер 1 — объявления с двоеточием: menu File "Файл":
        m = re.match(r'menu\s+(\w+)\s+"([^"]*)"\s*:', line)
        if m:
            name, label = m.group(1), m.group(2)
            items = []
            i += 1
            while i < len(lines):
                iline = lines[i].strip()
                if iline == "separator":
                    items.append("separator")
                    i += 1
                elif iline.startswith("item "):
                    im = re.match(r'item\s+"([^"]*)"\s*,\s*(\w+)', iline)
                    if im:
                        items.append(MenuItem(im.group(1), im.group(2)))
                        i += 1
                    else:
                        break
                else:
                    break
            ast.append(MenuDecl(name, label, items))
            continue
        
        # Парсер 1 — объявления с двоеточием: window w:
        m = re.match(r'window\s+(\w+)\s*:', line)
        if m:
            props, i = parse_props(lines, i + 1)
            ast.append(WindowDecl(m.group(1), props))
            continue
        
        # Парсер 2 — вызовы с точкой: name.addFluentButton/Label/Canvas:
        widget_found = False
        for method, wtype in WIDGET_TYPES.items():
            m = re.match(rf'(\w+)\.{method}\s*(?:\(style:\s*"([^"]*)"\))?\s*:', line)
            if m:
                name, style_name = m.group(1), m.group(2)
                props, i = parse_props(lines, i + 1)
                if style_name: props['style'] = style_name
                
                if wtype == "fluent_canvas":
                    cmds = []
                    if i < len(lines) and lines[i].strip() == "onPaint:":
                        i += 1
                        # Парсер 5 — выражения в (): rect(), circle()
                        paint_cmds, i = Canvas.parse_canvas_commands(lines, i)
                        props['_paint_cmds'] = paint_cmds
                        cmds = [c for c in paint_cmds if not isinstance(c, dict)]
                    ast.append(WidgetDecl(name, wtype, props, cmds))
                else:
                    ast.append(WidgetDecl(name, wtype, props))
                
                widget_found = True
                break
        
        if widget_found:
            continue
        
        # Парсер 2 — вызовы с точкой: name.addFunction(onClick):
        m = re.match(r'(\w+)\.addFunction(?:\s*:\s*|\s*\((\w+)\)\s*:\s*)', line)
        if m:
            widget = m.group(1)
            event = m.group(2) if m.group(2) else "onClick"
            actions, asm_lines, file_ops = {}, [], []
            i += 1
            while i < len(lines):
                aline = lines[i].strip()
                if not aline or aline.startswith("#"):
                    i += 1
                    continue
                
                # Парсер 6 — блоки: asm { ... }
                if aline == "asm {":
                    i += 1
                    while i < len(lines):
                        if lines[i].strip().startswith('}'): break
                        asm_lines.append(lines[i]); i += 1
                    i += 1
                    continue
                
                # Парсер 2 — вызовы с точкой: file.addFileRead "test.txt":
                mf = re.match(r'file\.addFileRead\s+"([^"]+)"\s*:', aline)
                if mf:
                    op = {"type": "read", "path": mf.group(1), "target": {}}
                    i += 1
                    while i < len(lines):
                        fline = lines[i].strip()
                        if not fline or fline.startswith("#"): i += 1; continue
                        m2 = re.match(r'(\w+)\.(\w+)\s*=\s*\[file\.(\w+)\]', fline)
                        if m2:
                            op["target"] = {"widget": m2.group(1), "prop": m2.group(2), "source": m2.group(3)}
                            i += 1
                        else: break
                    file_ops.append(op)
                    continue
                
                # Парсер 2 — вызовы с точкой: file.addFileWrite "test.txt":
                mf = re.match(r'file\.addFileWrite\s+"([^"]+)"\s*:', aline)
                if mf:
                    op = {"type": "write", "path": mf.group(1), "source": {}}
                    i += 1
                    while i < len(lines):
                        fline = lines[i].strip()
                        if not fline or fline.startswith("#"): i += 1; continue
                        m2 = re.match(r'content\s*=\s*(\w+)\.(\w+)', fline)
                        if m2:
                            op["source"] = {"widget": m2.group(1), "prop": m2.group(2)}
                            i += 1
                        else: break
                    file_ops.append(op)
                    continue
                
                # Парсер 3 — присваивания: title = "Loaded!"
                if "=" in aline:
                    k, v = aline.split("=", 1)
                    actions[k.strip()] = v.strip().strip('"')
                    i += 1
                elif aline.startswith("file."):
                    actions[f"__file__{aline.strip()}"] = aline.strip()
                    i += 1
                else:
                    break
            
            if asm_lines: actions['__asm__'] = asm_lines
            if file_ops: actions['__file_ops__'] = file_ops
            ast.append(EventDecl(widget, event, actions))
            continue
        
        # Парсер 2 — вызовы с точкой: w.show()
        m = re.match(r'(\w+)\.show\s*\(\s*\)', line)
        if m:
            ast.append(ShowWindow(m.group(1)))
            i += 1
            continue
        
        i += 1
    
    return ast