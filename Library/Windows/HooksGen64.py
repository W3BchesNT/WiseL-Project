# Library/Windows/HooksGen64.py
"""Генератор ASM для хуков Windows x64"""
import os, sys, re
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path: sys.path.insert(0, CORE_PATH)
import Hooks


def generate_data(hook):
    return []


def generate_init(hook):
    return []


def generate_keydown_handler(hook):
    code = []
    if not hook or not hook.bindings:
        return code
    
    code.append(f"  .wm_keydown:")
    
    for idx, binding in enumerate(hook.bindings):
        vk_code = Hooks.KEY_MAP.get(binding.key, '00h')
        vk_int = int(vk_code.replace('h', ''), 16)
        actions = binding.actions
        modifiers = binding.modifiers
        label_id = f"{binding.key}_{idx}"
        
        for mod in modifiers:
            mod_code = Hooks.MOD_MAP.get(mod, '00h')
            code += [
                f"    invoke GetAsyncKeyState, {mod_code}",
                f"    test eax, 0x8000",
                f"    jz .skip_{label_id}",
            ]
        
        code += [
            f"    cmp r8d, {vk_int}",
            f"    jne .skip_{label_id}",
        ]
        
        # Выполняем ВСЕ действия для этой клавиши (в порядке: сначала stop, потом start, потом остальное)
        for action in actions:
            action = action.strip()
            
            if action.endswith('.stop'):
                timer_name = action.replace('.stop', '')
                code.append(f"    mov dword [timer_{timer_name}_running], 0")
            
            elif action.endswith('.start'):
                timer_name = action.replace('.start', '')
                code.append(f"    mov dword [timer_{timer_name}_running], 1")
            
            elif action in ('exit', 'quit'):
                code.append(f"    invoke PostQuitMessage, 0")
            
            elif action.startswith('asm'):
                m_asm = re.search(r'asm\s*\{([^}]+)\}', action)
                if m_asm:
                    asm_code = m_asm.group(1).strip()
                    for asm_line in asm_code.splitlines():
                        asm_line = asm_line.strip()
                        if asm_line and not asm_line.startswith('#'):
                            code.append(f"    {asm_line}")
            
            elif '+' in action:
                parts = action.replace(' ', '').split('+')
                left = parts[0].strip()
                right = parts[1].strip()
                if '.' in left:
                    obj_name, prop = left.split('.', 1)
                    code += [
                        f"    mov eax, [obj_{obj_name}_{prop}]",
                        f"    add eax, {right}",
                        f"    mov [obj_{obj_name}_{prop}], eax",
                    ]
            
            elif '-' in action and not action.strip().startswith('-'):
                parts = action.replace(' ', '').split('-')
                left = parts[0].strip()
                right = parts[1].strip()
                if '.' in left:
                    obj_name, prop = left.split('.', 1)
                    code += [
                        f"    mov eax, [obj_{obj_name}_{prop}]",
                        f"    sub eax, {right}",
                        f"    mov [obj_{obj_name}_{prop}], eax",
                    ]
            
            elif '=' in action:
                parts = action.replace(' ', '').split('=')
                left = parts[0].strip()
                right = parts[1].strip()
                if '.' in left:
                    obj_name, prop = left.split('.', 1)
                    code.append(f"    mov dword [obj_{obj_name}_{prop}], {right}")
        
        code += [
            f"    invoke InvalidateRect, rbx, 0, 0",
            f"    jmp .finish",
            f"  .skip_{label_id}:",
        ]
    
    code.append(f"    jmp .finish")
    return code


def generate_dispatch_check():
    return [
        f"    cmp edx, 256",
        f"    je .wm_keydown",
    ]


def generate_cleanup(hook):
    return []