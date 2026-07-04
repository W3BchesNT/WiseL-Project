# Library/Windows/ValuesGen64.py
import os, sys

CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

import Values


def gen_data(variables):
    lines = []
    
    for name, info in variables.items():
        vtype = info['type']
        value = info['value']
        
        if vtype == 'string':
            text = str(value).replace("'", "''")
            lines.append(f"  str_{name} db '{text}',0")
            lines.append(f"  var_{name} dq str_{name}")
        
        elif vtype == 'int':
            val = value if isinstance(value, int) else 0
            lines.append(f"  var_{name} dq {val}")
        
        elif vtype == 'bool':
            val = 1 if value in (True, 1, 'true', 'True') else 0
            lines.append(f"  var_{name} dq {val}")
    
    return lines


def gen_decl(node):
    code = []
    
    if node.vtype == 'int' and isinstance(node.value, Values.VarExpr):
        code.append(f"    ; int {node.name} = {node.value.value}")
        code += _gen_expr_assign(node.name, node.value.value)
    elif node.vtype == 'int':
        code.append(f"    ; int {node.name} = {node.value}")
    elif node.vtype == 'string':
        code.append(f"    ; string {node.name} = \"{node.value}\"")
    elif node.vtype == 'bool':
        code.append(f"    ; bool {node.name} = {node.value}")
    
    return code


def gen_assign(node):
    code = []
    
    if isinstance(node.value, Values.VarExpr):
        code.append(f"    ; {node.name} = {node.value.value}")
        code += _gen_expr_assign(node.name, node.value.value)
    elif isinstance(node.value, int):
        code.append(f"    ; {node.name} = {node.value}")
        code.append(f"    mov qword [var_{node.name}], {node.value}")
    elif isinstance(node.value, str):
        code.append(f"    ; {node.name} = \"{node.value}\"")
    
    return code


def gen_print_var(name, var_info):
    code = []
    
    if var_info.get('type') == 'string':
        code.extend([
            f"    ; print string [{name}]",
            f"    invoke lstrlenA, [var_{name}]",
            f"    invoke WriteFile, rbx, [var_{name}], rax, bytes_read, 0",
            f"    invoke WriteFile, rbx, crlf, 2, bytes_read, 0",
        ])
    else:
        code.extend([
            f"    ; print [{name}]",
            f"    sub rsp, 40",
            f"    lea rcx, [buf_print_var]",
            f"    lea rdx, [num_fmt]",
            f"    mov r8, [var_{name}]",
            f"    call [crt_sprintf]",
            f"    add rsp, 40",
            f"    invoke WriteFile, rbx, buf_print_var, 32, bytes_read, 0",
            f"    invoke WriteFile, rbx, crlf, 2, bytes_read, 0",
        ])
    
    return code


def _gen_expr_assign(target, expr):
    code = []
    
    for op in ['+', '-', '*', '/']:
        if op in expr:
            left, right = expr.split(op, 1)
            left, right = left.strip(), right.strip()
            
            if left.isdigit() or (left.startswith('-') and left[1:].isdigit()):
                code.append(f"    mov rax, {left}")
            else:
                code.append(f"    mov rax, [var_{left}]")
            
            if right.isdigit() or (right.startswith('-') and right[1:].isdigit()):
                if op == '+': code.append(f"    add rax, {right}")
                elif op == '-': code.append(f"    sub rax, {right}")
                elif op == '*': code.append(f"    imul rax, {right}")
                elif op == '/':
                    code.append(f"    xor rdx, rdx")
                    code.append(f"    mov rcx, {right}")
                    code.append(f"    idiv rcx")
            else:
                if op == '+': code.append(f"    add rax, [var_{right}]")
                elif op == '-': code.append(f"    sub rax, [var_{right}]")
                elif op == '*': code.append(f"    imul rax, [var_{right}]")
                elif op == '/':
                    code.append(f"    xor rdx, rdx")
                    code.append(f"    idiv qword [var_{right}]")
            
            code.append(f"    mov [var_{target}], rax")
            break
    
    return code