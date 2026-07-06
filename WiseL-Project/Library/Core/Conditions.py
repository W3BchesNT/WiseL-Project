# Library/Core/Conditions.py
import re


class IfBlock:
    def __init__(self, left, op, right, body, else_body=None):
        self.left = left
        self.op = op
        self.right = right
        self.body = body
        self.else_body = else_body


def parse_if_block(lines, start_i, parse_fn):
    i = start_i
    line = lines[i].strip()
    
    m = re.match(r'if\s+(\w+)\s*(==|!=|>=|<=|>|<)\s*"?(-?\w+)"?\s*\{', line)
    if not m:
        return None, start_i
    
    left = m.group(1)
    op = m.group(2)
    right = m.group(3)
    
    if_body_lines = []
    else_body_lines = None
    i += 1
    depth = 1
    
    while i < len(lines) and depth > 0:
        l = lines[i]
        s = l.strip()
        if s == '{':
            depth += 1
        elif s == '}':
            depth -= 1
        if depth > 0:
            if_body_lines.append(l)
        i += 1
    
    if_body_code = '\n'.join(if_body_lines)
    if_body_ast = parse_fn(if_body_code) if parse_fn else if_body_lines
    
    else_body_ast = None
    if i < len(lines):
        next_line = lines[i].strip()
        if next_line == 'else' or next_line.startswith('} else'):
            if '{' in next_line:
                i += 1
            elif i + 1 < len(lines) and lines[i + 1].strip() == '{':
                i += 2
            else:
                i += 1
            
            if i < len(lines):
                else_body_lines = []
                depth = 1
                while i < len(lines) and depth > 0:
                    l = lines[i]
                    s = l.strip()
                    if s == '{':
                        depth += 1
                    elif s == '}':
                        depth -= 1
                    if depth > 0:
                        else_body_lines.append(l)
                    i += 1
                
                if else_body_lines:
                    else_body_code = '\n'.join(else_body_lines)
                    else_body_ast = parse_fn(else_body_code) if parse_fn else else_body_lines
    
    return IfBlock(left, op, right, if_body_ast, else_body_ast), i