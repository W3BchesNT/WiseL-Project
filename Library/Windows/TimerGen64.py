# Library/Windows/TimerGen64.py
"""Генератор ASM для таймеров — с поддержкой if и random"""
import os, sys, re
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path: sys.path.insert(0, CORE_PATH)
import Timer as TimerParser


def generate_data(timers, auto_start_all=False):
    lines = []
    for timer in timers:
        running = 1 if auto_start_all else 0
        lines += [
            f"  timer_{timer.name}_running dd {running}",
            f"  timer_{timer.name}_last dd 0",
            f"  timer_{timer.name}_interval dd {timer.interval}",
        ]
    return lines


def generate_init(timers):
    return []


def _gen_action(action):
    code = []
    obj_name = action.obj_name
    prop = action.prop
    op = action.op
    value = action.value
    
    if op == 'random':
        parts = str(value).split()
        min_val = int(parts[0])
        max_val = int(parts[1])
        step = int(parts[2]) if len(parts) > 2 else 1
        count = (max_val - min_val) // step + 1
        code += [
            f"    invoke GetTickCount",
            f"    xor edx, edx",
            f"    mov ecx, {count}",
            f"    div ecx",
            f"    imul edx, {step}",
            f"    add edx, {min_val}",
            f"    mov [obj_{obj_name}_{prop}], edx",
        ]
    
    elif op == '+':
        code += [
            f"    mov eax, [obj_{obj_name}_{prop}]",
            f"    add eax, {value}",
            f"    mov [obj_{obj_name}_{prop}], eax",
        ]
    elif op == '-':
        code += [
            f"    mov eax, [obj_{obj_name}_{prop}]",
            f"    sub eax, {value}",
            f"    mov [obj_{obj_name}_{prop}], eax",
        ]
    elif op == '=':
        code += [
            f"    mov dword [obj_{obj_name}_{prop}], {value}",
        ]
    
    return code


def _gen_if(if_block, label_prefix):
    code = []
    jmp_map = {'==': 'jne', '!=': 'je'}
    jmp = jmp_map.get(if_block.op, 'jne')
    
    code += [
        f"    mov eax, [obj_{if_block.left_obj}_{if_block.left_prop}]",
        f"    cmp eax, [obj_{if_block.right_obj}_{if_block.right_prop}]",
        f"    {jmp} .skip_{label_prefix}",
    ]
    
    for act in if_block.body:
        if isinstance(act, TimerParser.TimerAction):
            code += _gen_action(act)
        elif isinstance(act, TimerParser.IfBlock):
            code += _gen_if(act, label_prefix + "_n")
    
    code.append(f"  .skip_{label_prefix}:")
    return code


def generate_timer_handler(timers):
    code = []
    if not timers:
        return code
    
    code += [
        f"    invoke GetTickCount",
        f"    mov r15, rax",
    ]
    
    for timer in timers:
        code += [
            f"    cmp dword [timer_{timer.name}_running], 1",
            f"    jne .skip_timer_{timer.name}",
            f"    mov eax, r15d",
            f"    sub eax, [timer_{timer.name}_last]",
            f"    cmp eax, [timer_{timer.name}_interval]",
            f"    jl .skip_timer_{timer.name}",
            f"    mov [timer_{timer.name}_last], r15d",
        ]
        
        for idx, item in enumerate(timer.actions):
            if isinstance(item, TimerParser.TimerAction):
                code += _gen_action(item)
            elif isinstance(item, TimerParser.IfBlock):
                code += _gen_if(item, f"{timer.name}_{idx}")
        
        code.append(f"  .skip_timer_{timer.name}:")
    
    code.append(f"    invoke InvalidateRect, rbx, 0, 0")
    return code


def generate_dispatch_check():
    return []


def generate_cleanup(timers):
    return []