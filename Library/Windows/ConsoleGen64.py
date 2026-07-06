# Library/Windows/ConsoleGen64.py
import os, sys
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path: sys.path.insert(0, CORE_PATH)
import Console, Values


def _gen_block(ast_block, counters, all_vars, strings_data):
    data_lines, code_lines = [], []
    for node in ast_block:
        if isinstance(node, Console.Print):
            idx = counters["print"]; counters["print"] += 1
            if not node.value:
                data_lines.append(f"crlf_print_{idx} db 13,10")
                code_lines.append(f"    invoke WriteFile, rbx, crlf_print_{idx}, 2, bytes_read, 0")
            elif node.value.lstrip("-").isdigit():
                code_lines += _print_number(node.value)
                code_lines.append(_print_crlf())
            else:
                t = node.value.replace("'", "''")
                data_lines += [f"str_print_{idx} db '{t}',13,10", f"str_print_{idx}_len = $ - str_print_{idx}"]
                code_lines.append(f"    invoke WriteFile, rbx, str_print_{idx}, str_print_{idx}_len, bytes_read, 0")
        elif isinstance(node, dict) and node.get("type") == "print_var":
            name = node["name"]
            code_lines += [
                f"    mov rax, [var_{name}]",
                f"    lea rdi, [_itoa_buf]",
                f"    call _itoa",
                f"    mov r8, rax",
                f"    invoke WriteFile, rbx, _itoa_buf, r8, bytes_read, 0",
                f"    invoke WriteFile, rbx, crlf, 2, bytes_read, 0",
            ]
        elif isinstance(node, Console.Pause):
            idx = counters["pause"]; counters["pause"] += 1
            data_lines.append(f"pause_buf_{idx} db 1 dup(0)")
            code_lines.append(f"    invoke ReadConsoleA, rsi, pause_buf_{idx}, 1, bytes_read, 0")
        elif isinstance(node, Console.RawAsm):
            for line in node.lines:
                s = line.strip()
                if s and not s.startswith("#"):
                    code_lines.append(f"    {s}")
    return data_lines, code_lines


def _gen_expr(target, expr):
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
                elif op == '*': code.append(f"    imul rax, rax, {right}")
                elif op == '/': code += [f"    xor rdx, rdx", f"    mov rcx, {right}", f"    idiv rcx"]
            else:
                if op == '+': code.append(f"    add rax, [var_{right}]")
                elif op == '-': code.append(f"    sub rax, [var_{right}]")
                elif op == '*': code.append(f"    imul rax, [var_{right}]")
                elif op == '/': code += [f"    xor rdx, rdx", f"    idiv qword [var_{right}]"]
            code.append(f"    mov [var_{target}], rax")
            break
    return code

def _print_number(value):
    return [
        f"    mov rax, {value}",
        f"    lea rdi, [_itoa_buf]",
        f"    call _itoa",
        f"    mov r8, rax",
        f"    invoke WriteFile, rbx, _itoa_buf, r8, bytes_read, 0",
    ]


def generate(ast):
    data_lines, code_lines = [], []
    counters = {"print": 0, "input": 0, "pause": 0, "for": 0}
    needs_lstrlen = False
    needs_lstrcmp = False
    strings_data = []
    str_counter = 0
    
    kernel32_extra = []
    user32_extra = []
    other_dlls = {}
    
    for node in ast:
        if isinstance(node, Console.DllImport):
            dll_name = node.dll.lower().replace('.dll', '')
            for func in node.funcs:
                if dll_name == 'kernel32':
                    if func['name'] not in kernel32_extra:
                        kernel32_extra.append(func['name'])
                elif dll_name == 'user32':
                    if func['name'] not in user32_extra:
                        user32_extra.append(func['name'])
                else:
                    if node.dll not in other_dlls:
                        other_dlls[node.dll] = []
                    if func['name'] not in other_dlls[node.dll]:
                        other_dlls[node.dll].append(func['name'])
    
    code_lines += [
        "start:",
        "    sub rsp, 8", "    and rsp, -16", "    sub rsp, 32",
        "    invoke SetConsoleOutputCP, 65001",
        "    invoke GetStdHandle, -11", "    mov rbx, rax",
        "    invoke GetStdHandle, -10", "    mov rsi, rax",
    ]
    data_lines += [
        "bytes_read dq 0",
        "_itoa_buf db 32 dup(0)",
        "crlf db 13,10",
    ]
    
    all_vars = {}
    for node in ast:
        if isinstance(node, Values.VarDecl):
            all_vars[node.name] = {'type': node.vtype, 'value': node.value if isinstance(node.value, (int, str)) else 0}
        elif isinstance(node, dict) and node.get('type') == 'for_block':
            var_name = node['var']
            start_val = node['start']
            s = int(start_val) if (start_val.isdigit() or (start_val.startswith('-') and start_val[1:].isdigit())) else 0
            all_vars[var_name] = {'type': 'int', 'value': s}
    
    for name, info in all_vars.items():
        vtype = info['type']
        value = info['value']
        if vtype == 'string':
            text = str(value).replace("'", "''")
            data_lines.append(f"  str_{name} db '{text}',0")
            data_lines.append(f"  var_{name} dq str_{name}")
        elif vtype in ('int', 'bool'):
            val = value if isinstance(value, int) else (1 if value in (True, 1, 'true', 'True') else 0)
            data_lines.append(f"  var_{name} dq {val}")
    
    for node in ast:
        if isinstance(node, Values.VarDecl):
            if node.vtype == 'int' and isinstance(node.value, Values.VarExpr):
                code_lines += _gen_expr(node.name, node.value.value)
        
        elif isinstance(node, Values.VarAssign):
            name = node.name
            value = node.value
            if isinstance(value, Values.VarExpr):
                code_lines += _gen_expr(name, value.value)
            elif isinstance(value, int):
                code_lines.append(f"    mov qword [var_{name}], {value}")
        
        elif isinstance(node, dict) and node.get('type') == 'for_block':
            cid = counters["for"]; counters["for"] += 1
            var_name = node['var']
            start_val = node['start']
            end_val = node['end']
            
            if not start_val.isdigit() and not (start_val.startswith('-') and start_val[1:].isdigit()):
                code_lines.append(f"    mov rax, [var_{start_val}]")
                code_lines.append(f"    mov [var_{var_name}], rax")
            else:
                code_lines.append(f"    mov qword [var_{var_name}], {start_val}")
            
            code_lines.append(f"  .loop_{cid}:")
            
            if end_val.isdigit() or (end_val.startswith('-') and end_val[1:].isdigit()):
                code_lines.append(f"    cmp qword [var_{var_name}], {end_val}")
            else:
                code_lines.append(f"    mov rax, [var_{end_val}]")
                code_lines.append(f"    cmp qword [var_{var_name}], rax")
            
            code_lines.append(f"    jg .end_{cid}")
            
            if node['body']:
                inner_data, inner_code = _gen_block(node['body'], counters, all_vars, strings_data)
                data_lines += inner_data
                code_lines += inner_code
            
            code_lines += [
                f"    inc qword [var_{var_name}]",
                f"    jmp .loop_{cid}",
                f"  .end_{cid}:",
            ]
        
        elif isinstance(node, dict) and node.get('type') == 'if_block':
            cid = counters["print"]; counters["print"] += 1
            left = node['left']
            op = node['op']
            right = node['right']
            
            if right.isdigit() or (right.startswith('-') and right[1:].isdigit()):
                code_lines.append(f"    mov rax, [var_{left}]")
                code_lines.append(f"    cmp rax, {right}")
            else:
                needs_lstrcmp = True
                data_lines.append(f"  str_cmp_{cid} db '{right}',0")
                code_lines += [
                    f"    invoke lstrcmpiA, [var_{left}], str_cmp_{cid}",
                    f"    cmp eax, 0",
                ]
            
            jmp_map = {
                '==': f'jne .else_{cid}',
                '!=': f'je .else_{cid}',
                '>':  f'jle .else_{cid}',
                '<':  f'jge .else_{cid}',
                '>=': f'jl .else_{cid}',
                '<=': f'jg .else_{cid}',
            }
            code_lines.append(f"    {jmp_map[op]}")
            
            if node['body']:
                inner_data, inner_code = _gen_block(node['body'], counters, all_vars, strings_data)
                data_lines += inner_data
                code_lines += inner_code
            
            code_lines.append(f"    jmp .endif_{cid}")
            code_lines.append(f"  .else_{cid}:")
            
            if node['else_body'] is not None and len(node['else_body']) > 0:
                inner_data, inner_code = _gen_block(node['else_body'], counters, all_vars, strings_data)
                data_lines += inner_data
                code_lines += inner_code
            
            code_lines.append(f"  .endif_{cid}:")
        
        elif isinstance(node, dict) and node.get("type") == "print_var":
            name = node["name"]
            vi = all_vars.get(name, {'type': 'int', 'value': 0})
            if vi.get('type') == 'string':
                code_lines += [
                    f"    invoke lstrlenA, [var_{name}]",
                    f"    invoke WriteFile, rbx, [var_{name}], rax, bytes_read, 0",
                ]
            else:
                code_lines += _print_number(f"[var_{name}]")
            code_lines.append(_print_crlf())
        
        elif isinstance(node, Console.Print):
            idx = counters["print"]; counters["print"] += 1
            if not node.value:
                data_lines.append(f"crlf_print_{idx} db 13,10")
                code_lines.append(f"    invoke WriteFile, rbx, crlf_print_{idx}, 2, bytes_read, 0")
            elif node.value.lstrip("-").isdigit():
                code_lines += _print_number(node.value)
                code_lines.append(_print_crlf())
            else:
                t = node.value.replace("'", "''")
                data_lines += [f"str_print_{idx} db '{t}',13,10", f"str_print_{idx}_len = $ - str_print_{idx}"]
                code_lines.append(f"    invoke WriteFile, rbx, str_print_{idx}, str_print_{idx}_len, bytes_read, 0")
        
        elif isinstance(node, Console.InputCmd):
            idx = counters["input"]; counters["input"] += 1
            
            if node.prompt:
                t = node.prompt.replace("'", "''")
                data_lines += [f"prompt_input_{idx} db '{t}',0", f"prompt_input_{idx}_len = $ - prompt_input_{idx} - 1"]
                code_lines.append(f"    invoke WriteFile, rbx, prompt_input_{idx}, prompt_input_{idx}_len, bytes_read, 0")
            
            data_lines.append(f"buf_input_{idx} db 256 dup(0)")
            code_lines.append(f"    invoke ReadConsoleA, rsi, buf_input_{idx}, 255, bytes_read, 0")
            
            if node.var_name:
                code_lines += [
                    f"    mov rcx, [bytes_read]",
                    f"    sub rcx, 2",
                    f"    mov byte [buf_input_{idx} + rcx], 0",
                ]
                data_lines.append(f"  var_{node.var_name} dq buf_input_{idx}")
                all_vars[node.var_name] = {'type': 'string', 'value': ''}
        
        elif isinstance(node, Console.Pause):
            idx = counters["pause"]; counters["pause"] += 1
            data_lines.append(f"pause_buf_{idx} db 1 dup(0)")
            code_lines.append(f"    invoke ReadConsoleA, rsi, pause_buf_{idx}, 1, bytes_read, 0")
        
        elif isinstance(node, Console.RawAsm):
            for line in node.lines:
                s = line.strip()
                if s and not s.startswith("#"):
                    code_lines.append(f"    {s}")
        
        elif isinstance(node, Console.ExitApp):
            code_lines.append(f"    invoke ExitProcess, {node.code}")
        
        elif isinstance(node, Console.CallFunc):
            args = []
            for arg in node.args:
                if arg.startswith('"') and arg.endswith('"'):
                    str_text = arg[1:-1]
                    label = f"_str_{str_counter}"
                    str_counter += 1
                    strings_data.append(f"  {label} db '{str_text}',0")
                    args.append(label)
                elif arg.startswith('[') and arg.endswith(']'):
                    var_name = arg[1:-1]
                    args.append(f"[var_{var_name}]")
                else:
                    args.append(arg)
            code_lines.append(f"    invoke {node.func}, {', '.join(args)}")
        
        elif isinstance(node, Console.DllImport):
            pass
        
        elif isinstance(node, Console.ClearScreen):
            data_lines.append("cls_cmd db 'cls',0")
            code_lines.append("    invoke system, cls_cmd")
    
    if not any(isinstance(n, Console.ExitApp) for n in ast):
        code_lines.append("    invoke ExitProcess, 0")
    
    data_lines += strings_data
    
    kernel32_funcs = ['ExitProcess', 'GetStdHandle', 'WriteFile', 'ReadConsoleA', 'SetConsoleOutputCP', 'Sleep']
    if needs_lstrlen: kernel32_funcs.append('lstrlenA')
    if needs_lstrcmp: kernel32_funcs.append('lstrcmpiA')
    for f in kernel32_extra:
        if f not in kernel32_funcs:
            kernel32_funcs.append(f)
    
    user32_funcs = ['MessageBoxA']
    for f in user32_extra:
        if f not in user32_funcs:
            user32_funcs.append(f)
    
    idata_lines = []
    idata_lines.append("  library kernel32, 'KERNEL32.DLL', msvcrt, 'msvcrt.dll', user32, 'user32.dll'")
    for dll in other_dlls:
        dll_short = dll.replace('.dll', '')
        idata_lines.append(f"  library {dll_short}, '{dll}'")
    
    k32_imports = ', '.join([f"{f}, '{f}'" for f in kernel32_funcs])
    idata_lines.append(f"  import kernel32, {k32_imports}")
    idata_lines.append("  import msvcrt, system, 'system'")
    u32_imports = ', '.join([f"{f}, '{f}'" for f in user32_funcs])
    idata_lines.append(f"  import user32, {u32_imports}")
    
    for dll, funcs in other_dlls.items():
        dll_short = dll.replace('.dll', '')
        dll_imports = ', '.join([f"{f}, '{f}'" for f in funcs])
        idata_lines.append(f"  import {dll_short}, {dll_imports}")
    
    return f"""format PE64 CONSOLE
entry start
include 'win64a.inc'

section '.data' data readable writeable
{chr(10).join(data_lines)}

section '.code' code readable executable
{chr(10).join(code_lines)}

_itoa:
    push rbx rcx rdx rsi rdi
    mov rbx, 10
    xor rcx, rcx
    mov rsi, rdi
    cmp rax, 0
    jge .pos
    neg rax
    mov byte [rdi], '-'
    inc rdi
    inc rsi
.pos:
    xor rdx, rdx
    div rbx
    add dl, '0'
    push rdx
    inc rcx
    test rax, rax
    jnz .pos
    mov rdi, rsi
.store:
    pop rax
    stosb
    loop .store
    mov byte [rdi], 0
    mov rax, rdi
    sub rax, rsi
    pop rdi rsi rdx rcx rbx
    ret

section '.idata' import data readable writeable
{chr(10).join(idata_lines)}
"""