# Library/Core/Values.py
"""Единый реестр переменных WiseL — AST"""
import re


class ASTNode:
    pass


class VarDecl(ASTNode):
    def __init__(self, name, vtype, value=None):
        self.name = name
        self.vtype = vtype
        self.value = value


class VarAssign(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class VarExpr(ASTNode):
    def __init__(self, value):
        self.value = value


class ValueParser:
    def __init__(self):
        self.variables = {}
    
    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        
        m = re.match(r'int\s+(\w+)\s*=\s*(.+)', line)
        if m:
            return self._parse_int_decl(m.group(1), m.group(2).strip())
        
        m = re.match(r'string\s+(\w+)\s*=\s*"(.*?)"', line)
        if m:
            name, value = m.group(1), m.group(2)
            self.variables[name] = {'type': 'string', 'value': value}
            return VarDecl(name, 'string', value)
        
        m = re.match(r'string\s+(\w+)', line)
        if m:
            name = m.group(1)
            self.variables[name] = {'type': 'string', 'value': ''}
            return VarDecl(name, 'string', '')
        
        m = re.match(r'bool\s+(\w+)\s*=\s*(true|false|True|False)', line)
        if m:
            name = m.group(1)
            value = 1 if m.group(2).lower() == 'true' else 0
            self.variables[name] = {'type': 'bool', 'value': value}
            return VarDecl(name, 'bool', value)
        
        m = re.match(r'(\w+)\s*=\s*(.+)', line)
        if m:
            return self._parse_assign(m.group(1), m.group(2).strip())
        
        return None
    
    def _parse_int_decl(self, name, value_str):
        if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
            val = int(value_str)
            self.variables[name] = {'type': 'int', 'value': val}
            return VarDecl(name, 'int', val)
        if any(op in value_str for op in ['+', '-', '*', '/']):
            self.variables[name] = {'type': 'int', 'value': 0}
            return VarDecl(name, 'int', VarExpr(value_str))
        self.variables[name] = {'type': 'int', 'value': 0}
        return VarDecl(name, 'int', VarExpr(value_str))
    
    def _parse_assign(self, name, value_str):
        if name not in self.variables:
            return None
        vtype = self.variables[name]['type']
        if vtype == 'int':
            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                val = int(value_str)
                self.variables[name]['value'] = val
                return VarAssign(name, val)
            else:
                self.variables[name]['value'] = 0
                return VarAssign(name, VarExpr(value_str))
        elif vtype == 'string':
            m = re.match(r'"(.*?)"', value_str)
            if m:
                val = m.group(1)
                self.variables[name]['value'] = val
                return VarAssign(name, val)
        elif vtype == 'bool':
            if value_str.lower() in ('true', 'false'):
                val = 1 if value_str.lower() == 'true' else 0
                self.variables[name]['value'] = val
                return VarAssign(name, val)
        return None
    
    def get_var(self, name):
        return self.variables.get(name)
    
    def get_all_vars(self):
        return self.variables