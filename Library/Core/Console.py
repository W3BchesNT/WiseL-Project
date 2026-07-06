# Library/Core/Console.py
"""Единый парсер консольного WiseL — AST"""
import re
import Values


class ASTNode:
    pass

class Print(ASTNode):
    def __init__(self, value, is_expr=False):
        self.value = value
        self.is_expr = is_expr

class InputCmd(ASTNode):
    def __init__(self, prompt="", var_name=None):
        self.prompt = prompt
        self.var_name = var_name

class Pause(ASTNode):
    pass

class RawAsm(ASTNode):
    def __init__(self, lines):
        self.lines = lines

class ExitApp(ASTNode):
    def __init__(self, code=0):
        self.code = code

class CallFunc(ASTNode):
    def __init__(self, func, args):
        self.func = func
        self.args = args

class DllImport(ASTNode):
    def __init__(self, dll, funcs):
        self.dll = dll
        self.funcs = funcs

class ClearScreen(ASTNode):
    pass


def parse_single_line(line, value_parser):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    
    var_node = value_parser.parse_line(line)
    if var_node:
        return var_node
    
    m = re.match(r'print\s+\[(\w+)\]', line)
    if m:
        return {"type": "print_var", "name": m.group(1)}
    
    m = re.match(r'print\s+"(.*?)"', line)
    if m:
        return Print(m.group(1))
    
    m = re.match(r'print\s+(-?\d+)', line)
    if m:
        return Print(m.group(1))
    
    m = re.match(r'print\s+([a-zA-Z_]\w*)', line)
    if m:
        return {"type": "print_var", "name": m.group(1)}
    
    m = re.match(r'input\s+(\w+)', line)
    if m:
        return InputCmd(var_name=m.group(1))
    
    m = re.match(r'input\s+"(.*?)"\s*,\s*(\w+)', line)
    if m:
        return InputCmd(prompt=m.group(1), var_name=m.group(2))
    
    m = re.match(r'input\s+"(.*?)"', line)
    if m:
        return InputCmd(prompt=m.group(1))
    
    if line == "input":
        return InputCmd()
    
    if line == "pause":
        return Pause()
    
    m = re.match(r'exit\s+(\d+)', line)
    if m:
        return ExitApp(int(m.group(1)))
    
    if line == "exit":
        return ExitApp()
    
    if line in ("cls", "clear"):
        return ClearScreen()
    
    m = re.match(r'call\s+(\w+)\s*\(([^)]*)\)', line)
    if m:
        args = [a.strip() for a in m.group(2).split(",") if a.strip()]
        return CallFunc(m.group(1), args)
    
    return None


def parse_block(lines_block):
    result = []
    value_parser = Values.ValueParser()
    i = 0
    
    while i < len(lines_block):
        line = lines_block[i].strip()
        
        if not line or line.startswith("#"):
            i += 1
            continue
        
        if line == "asm {":
            asm_lines = []
            i += 1
            while i < len(lines_block):
                if lines_block[i].strip().startswith('}'):
                    break
                asm_lines.append(lines_block[i])
                i += 1
            result.append(RawAsm(asm_lines))
            i += 1
            continue
        
        node = parse_single_line(line, value_parser)
        if node:
            result.append(node)
        
        i += 1
    
    return result


def parse(code):
    ast = []
    value_parser = Values.ValueParser()
    
    lines = code.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith(("#", "Use", "init")):
            i += 1
            continue
        
        if line == "asm {":
            asm_lines = []
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('}'):
                    break
                asm_lines.append(lines[i])
                i += 1
            ast.append(RawAsm(asm_lines))
            i += 1
            continue
        
        if line.startswith('if '):
            m = re.match(r'if\s+(\w+)\s*(==|!=|>=|<=|>|<)\s*"?(-?\w+)"?\s*\{', line)
            if m:
                left = m.group(1)
                op = m.group(2)
                right = m.group(3)
                if_body_lines = []
                else_body_ast = None
                i += 1
                
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith('}'):
                        i += 1
                        break
                    if_body_lines.append(lines[i])
                    i += 1
                
                if_body_ast = parse_block(if_body_lines)
                
                if i < len(lines):
                    next_line = lines[i].strip()
                    if next_line == 'else' or next_line == 'else {':
                        if next_line == 'else {':
                            i += 1
                        else:
                            i += 1
                            if i < len(lines) and lines[i].strip() == '{':
                                i += 1
                        
                        else_body_lines = []
                        while i < len(lines):
                            s = lines[i].strip()
                            if s.startswith('}'):
                                i += 1
                                break
                            else_body_lines.append(lines[i])
                            i += 1
                        
                        else_body_ast = parse_block(else_body_lines)
                
                ast.append({
                    'type': 'if_block',
                    'left': left,
                    'op': op,
                    'right': right,
                    'body': if_body_ast,
                    'else_body': else_body_ast
                })
                continue
        
        if line.startswith('for '):
            m = re.match(r'for\s+(\w+)\s*=\s*(-?\w+)\s+to\s+(-?\w+)\s*\{', line)
            if m:
                var_name = m.group(1)
                start_val = m.group(2)
                end_val = m.group(3)
                for_body_lines = []
                i += 1
                
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith('}'):
                        i += 1
                        break
                    for_body_lines.append(lines[i])
                    i += 1
                
                for_body_ast = parse_block(for_body_lines)
                
                ast.append({
                    'type': 'for_block',
                    'var': var_name,
                    'start': start_val,
                    'end': end_val,
                    'body': for_body_ast
                })
                continue
        
        node = parse_single_line(line, value_parser)
        if node:
            ast.append(node)
            i += 1
            continue
        
        m = re.match(r'import\s+"([^"]+)"\s*:', line)
        if m:
            dll = m.group(1)
            funcs = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith((' ', '\t')):
                sig = lines[i].strip()
                if sig and not sig.startswith("#"):
                    m2 = re.match(r'(\w+)\s*\(([^)]*)\)', sig)
                    if m2:
                        funcs.append({"name": m2.group(1), "params": m2.group(2)})
                i += 1
            ast.append(DllImport(dll, funcs))
            continue
        
        i += 1
    
    return ast