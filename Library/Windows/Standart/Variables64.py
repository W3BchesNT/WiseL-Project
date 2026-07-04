# Library/Windows/Standart/Variables64.py
"""Переменные WiseL для x64: string, int, bool"""
import re

class Variable:
    def __init__(self, name, vtype, value=None):
        self.name = name
        self.type = vtype
        self.value = value if value is not None else self._default()
    
    def _default(self):
        if self.type in ('int', 'input_int', 'runtime_int'):
            return 0
        elif self.type == 'bool':
            return 0
        return ""
    
    def asm_data(self):
        if self.type in ('int', 'input_int', 'runtime_int', 'bool'):
            return f"var_{self.name} dq {self.value}"
        else:
            return f"var_{self.name} dq 0"


def parse_variable(line, variables, commands):
    """Парсит объявление переменной. Возвращает True если обработано"""
    
    # string name = input("prompt")
    m = re.match(r'string\s+(\w+)\s*=\s*input\("(.*?)"\)', line)
    if m:
        name, prompt = m.groups()
        variables[name] = Variable(name, 'input_string')
        commands.append({"type": "sys_input", "var": name, "prompt": prompt, "is_int": False})
        return True
    
    # int name = input("prompt")
    m = re.match(r'int\s+(\w+)\s*=\s*input\("(.*?)"\)', line)
    if m:
        name, prompt = m.groups()
        variables[name] = Variable(name, 'input_int')
        commands.append({"type": "sys_input", "var": name, "prompt": prompt, "is_int": True})
        return True
    
    # string name = "value"
    m = re.match(r'string\s+(\w+)\s*=\s*"(.*?)"', line)
    if m:
        name, value = m.groups()
        variables[name] = Variable(name, 'string', value)
        return True
    
    # int name = число
    m = re.match(r'int\s+(\w+)\s*=\s*(\d+)', line)
    if m:
        name, value = m.groups()
        variables[name] = Variable(name, 'int', int(value))
        return True
    
    # bool name = true/false
    m = re.match(r'bool\s+(\w+)\s*=\s*(true|false)', line)
    if m:
        name, value = m.groups()
        variables[name] = Variable(name, 'bool', 1 if value == 'true' else 0)
        return True
    
    # int name = выражение (age + 1)
    m = re.match(r'int\s+(\w+)\s*=\s*(.+)', line)
    if m:
        var_name = m.group(1)
        expr = m.group(2).strip()
        variables[var_name] = Variable(var_name, 'runtime_int', 0)
        commands.append({"type": "set_var", "var": var_name, "expr": expr})
        return True
    
    return False