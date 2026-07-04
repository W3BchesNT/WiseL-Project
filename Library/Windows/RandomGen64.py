# Library/Windows/RandomGen64.py
import os, sys, re
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path: sys.path.insert(0, CORE_PATH)
import Random


def generate(obj_name, prop, expr_str):
    rand = Random.parse_random(expr_str)
    if not rand:
        return []
    
    count = (rand.max_val - rand.min_val) // rand.step + 1
    
    code = [
        f"    ; {obj_name}.{prop} = random {rand.min_val} {rand.max_val}",
        f"    invoke GetTickCount",
        f"    xor edx, edx",
        f"    mov ecx, {count}",
        f"    div ecx",
        f"    imul edx, {rand.step}",
        f"    add edx, {rand.min_val}",
        f"    mov [obj_{obj_name}_{prop}], edx",
    ]
    return code


def generate_console(var_name, expr_str):
    rand = Random.parse_random(expr_str)
    if not rand:
        return []
    
    count = (rand.max_val - rand.min_val) // rand.step + 1
    
    code = [
        f"    ; {var_name} = random {rand.min_val} {rand.max_val}",
        f"    invoke GetTickCount",
        f"    xor edx, edx",
        f"    mov ecx, {count}",
        f"    div ecx",
        f"    imul edx, {rand.step}",
        f"    add edx, {rand.min_val}",
        f"    mov [var_{var_name}], edx",
    ]
    return code