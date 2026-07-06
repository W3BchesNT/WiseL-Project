# Library/Core/Hooks.py — полный фикс
"""Единый парсер хуков WiseL — платформонезависимый"""
import re


class HookDecl:
    def __init__(self, bindings):
        self.bindings = bindings


class KeyBinding:
    def __init__(self, key, actions, modifiers=None):
        self.key = key
        self.actions = actions  # список строк действий
        self.modifiers = modifiers or []


KEY_MAP = {
    'a': '41h', 'b': '42h', 'c': '43h', 'd': '44h', 'e': '45h',
    'f': '46h', 'g': '47h', 'h': '48h', 'i': '49h', 'j': '4Ah',
    'k': '4Bh', 'l': '4Ch', 'm': '4Dh', 'n': '4Eh', 'o': '4Fh',
    'p': '50h', 'q': '51h', 'r': '52h', 's': '53h', 't': '54h',
    'u': '55h', 'v': '56h', 'w': '57h', 'x': '58h', 'y': '59h', 'z': '5Ah',
    '0': '30h', '1': '31h', '2': '32h', '3': '33h', '4': '34h',
    '5': '35h', '6': '36h', '7': '37h', '8': '38h', '9': '39h',
    'f1': '70h', 'f2': '71h', 'f3': '72h', 'f4': '73h',
    'f5': '74h', 'f6': '75h', 'f7': '76h', 'f8': '77h',
    'f9': '78h', 'f10': '79h', 'f11': '7Ah', 'f12': '7Bh',
    'space': '20h', 'enter': '0Dh', 'esc': '1Bh',
    'tab': '09h', 'caps': '14h', 'backspace': '08h',
    'left': '25h', 'up': '26h', 'right': '27h', 'down': '28h',
    'shift': '10h', 'ctrl': '11h', 'alt': '12h',
    'insert': '2Dh', 'delete': '2Eh', 'home': '24h', 'end': '23h',
    'pageup': '21h', 'pagedown': '22h',
    'numpad0': '60h', 'numpad1': '61h', 'numpad2': '62h',
    'numpad3': '63h', 'numpad4': '64h', 'numpad5': '65h',
    'numpad6': '66h', 'numpad7': '67h', 'numpad8': '68h', 'numpad9': '69h',
    'numpad_add': '6Bh', 'numpad_sub': '6Dh', 'numpad_mul': '6Ah', 'numpad_div': '6Fh',
    'minus': 'BDh', 'plus': 'BBh', 'comma': 'BCh', 'dot': 'BEh',
    'slash': 'BFh', 'backslash': 'DCh', 'semicolon': 'BAh',
    'quote': 'DEh', 'bracket_open': 'DBh', 'bracket_close': 'DDh',
}

MOD_MAP = {
    'ctrl': '11h', 'shift': '10h', 'alt': '12h',
}


def parse_hook(lines, start_i):
    i = start_i
    bindings = []
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        m = re.match(r'key\.func\((\w+)\)\s*:', line)
        if m:
            i += 1
            while i < len(lines):
                bline = lines[i].strip()
                if not bline or bline.startswith("#"):
                    i += 1
                    continue
                
                # key.w = expression (одиночное действие)
                m2 = re.match(r'key\.([a-zA-Z0-9_+]+)\s*=\s*(.+)', bline)
                if m2:
                    key_combo = m2.group(1).lower()
                    action = m2.group(2).strip()
                    
                    modifiers = []
                    key_name = key_combo
                    for mod in ['ctrl', 'shift', 'alt']:
                        if mod + '+' in key_combo:
                            modifiers.append(mod)
                            key_combo = key_combo.replace(mod + '+', '')
                    key_name = key_combo.strip()
                    
                    if key_name in KEY_MAP:
                        bindings.append(KeyBinding(key_name, [action], modifiers))
                    i += 1
                    continue
                
                # key.w: (блок действий)
                m3 = re.match(r'key\.([a-zA-Z0-9_+]+)\s*:', bline)
                if m3:
                    key_combo = m3.group(1).lower()
                    modifiers = []
                    key_name = key_combo
                    for mod in ['ctrl', 'shift', 'alt']:
                        if mod + '+' in key_combo:
                            modifiers.append(mod)
                            key_combo = key_combo.replace(mod + '+', '')
                    key_name = key_combo.strip()
                    
                    if key_name in KEY_MAP:
                        actions = []
                        i += 1
                        while i < len(lines):
                            aline = lines[i].strip()
                            if not aline or aline.startswith("#"):
                                i += 1
                                continue
                            if re.match(r'(key\.|menu\s+|window\s+|\w+\.addFluent|\w+\.addFunction|\w+\.show|Hook:)', aline):
                                break
                            actions.append(aline)
                            i += 1
                        bindings.append(KeyBinding(key_name, actions, modifiers))
                    continue
                
                if re.match(r'(menu\s+|window\s+|\w+\.addFluent|\w+\.addFunction|\w+\.show|Hook:)', bline):
                    break
                
                break
            continue
        else:
            break
    
    return HookDecl(bindings), i