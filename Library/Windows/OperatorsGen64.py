# Library/Windows/OperatorsGen64.py
"""Генератор ASM x64 для выражений WiseL"""
import os, sys
CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)
import Operators


class ASMGen:
    def __init__(self, var_prefix="var_", obj_prefix="obj_"):
        self.var_prefix = var_prefix
        self.obj_prefix = obj_prefix
        self.code = []
        self.data = []
        self.label_counter = 0
        self.string_counter = 0
        self.result_reg = "eax"
    
    def new_label(self, prefix="L"):
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"
    
    def new_string_label(self):
        self.string_counter += 1
        return f"_str_{self.string_counter}"
    
    def generate(self, node):
        self.code = []
        self.label_counter = 0
        self._gen_node(node)
        return self.code, self.data
    
    def _gen_node(self, node):
        if node is None:
            return
        
        if isinstance(node, Operators.NumberNode):
            self.code.append(f"    mov {self.result_reg}, {node.value}")
        
        elif isinstance(node, Operators.FloatNode):
            self.code.append(f"    mov {self.result_reg}, __float__({node.value})")
        
        elif isinstance(node, Operators.StringNode):
            label = self.new_string_label()
            escaped = node.value.replace("'", "''")
            self.data.append(f"  {label} db '{escaped}',0")
            self.code.append(f"    lea {self.result_reg}, [{label}]")
        
        elif isinstance(node, Operators.BoolNode):
            self.code.append(f"    mov {self.result_reg}, {1 if node.value else 0}")
        
        elif isinstance(node, Operators.VarNode):
            if node.name in ('true', 'false'):
                self.code.append(f"    mov {self.result_reg}, {1 if node.name == 'true' else 0}")
            else:
                self.code.append(f"    mov {self.result_reg}, [{self.var_prefix}{node.name}]")
        
        elif isinstance(node, Operators.StringVarNode):
            self.code.append(f"    lea {self.result_reg}, [{self.var_prefix}{node.name}]")
        
        elif isinstance(node, Operators.PropertyNode):
            obj_name = node.obj.name if isinstance(node.obj, Operators.VarNode) else "unknown"
            self.code.append(f"    mov {self.result_reg}, [{self.obj_prefix}{obj_name}_{node.prop}]")
        
        elif isinstance(node, Operators.UnaryOpNode):
            self._gen_node(node.operand)
            if node.op == '-':
                self.code.append(f"    neg {self.result_reg}")
            elif node.op == 'not':
                self.code.append(f"    xor {self.result_reg}, 1")
        
        elif isinstance(node, Operators.BinOpNode):
            if node.op in ('and', 'or'):
                self._gen_logical(node)
            elif node.op == '+' and self._is_string_op(node):
                self._gen_string_concat(node)
            else:
                self._gen_arithmetic(node)
        
        elif isinstance(node, Operators.CompareNode):
            self._gen_compare(node)
        
        elif isinstance(node, Operators.CallNode):
            self._gen_call(node)
        
        elif isinstance(node, Operators.AssignNode):
            self._gen_node(node.value)
            if isinstance(node.target, Operators.VarNode):
                self.code.append(f"    mov [{self.var_prefix}{node.target.name}], {self.result_reg}")
            elif isinstance(node.target, Operators.PropertyNode):
                obj_name = node.target.obj.name
                self.code.append(f"    mov [{self.obj_prefix}{obj_name}_{node.target.prop}], {self.result_reg}")
            elif isinstance(node.target, Operators.StringVarNode):
                self.code.append(f"    mov [{self.var_prefix}{node.target.name}], {self.result_reg}")
    
    def _is_string_op(self, node):
        return isinstance(node.left, (Operators.StringNode, Operators.StringVarNode)) or \
               isinstance(node.right, (Operators.StringNode, Operators.StringVarNode))
    
    def _gen_string_concat(self, node):
        label = self.new_label("strcat")
        self.data.append(f"  {label}_buf db 65536 dup(0)")
        
        self.code.append(f"    lea rdi, [{label}_buf]")
        
        # Копируем левую строку
        self._gen_node(node.left)
        self.code.append(f"    push rax")
        self.code.append(f"    pop rsi")
        self.code.append(f"    cmp rsi, 0")
        self.code.append(f"    je .skip_left_{label}")
        self.code.append(f"  .copy_left_{label}:")
        self.code.append(f"    mov al, [rsi]")
        self.code.append(f"    test al, al")
        self.code.append(f"    jz .skip_left_{label}")
        self.code.append(f"    mov [rdi], al")
        self.code.append(f"    inc rsi")
        self.code.append(f"    inc rdi")
        self.code.append(f"    jmp .copy_left_{label}")
        self.code.append(f"  .skip_left_{label}:")
        
        # Копируем правую строку
        self._gen_node(node.right)
        self.code.append(f"    push rax")
        self.code.append(f"    pop rsi")
        self.code.append(f"    cmp rsi, 0")
        self.code.append(f"    je .skip_right_{label}")
        self.code.append(f"  .copy_right_{label}:")
        self.code.append(f"    mov al, [rsi]")
        self.code.append(f"    test al, al")
        self.code.append(f"    jz .skip_right_{label}")
        self.code.append(f"    mov [rdi], al")
        self.code.append(f"    inc rsi")
        self.code.append(f"    inc rdi")
        self.code.append(f"    jmp .copy_right_{label}")
        self.code.append(f"  .skip_right_{label}:")
        
        self.code.append(f"    mov byte [rdi], 0")
        self.code.append(f"    lea {self.result_reg}, [{label}_buf]")
    
    def _gen_arithmetic(self, node):
        self._gen_node(node.left)
        self.code.append(f"    push rax")
        old_result = self.result_reg
        self.result_reg = "ecx" if old_result == "eax" else "eax"
        self._gen_node(node.right)
        self.result_reg = old_result
        
        if node.op == '+':
            self.code.append(f"    pop rcx")
            self.code.append(f"    add eax, ecx")
        elif node.op == '-':
            self.code.append(f"    pop rcx")
            self.code.append(f"    sub ecx, eax")
            self.code.append(f"    mov eax, ecx")
        elif node.op == '*':
            self.code.append(f"    pop rcx")
            self.code.append(f"    imul eax, ecx")
        elif node.op == '/':
            self.code.append(f"    pop rcx")
            self.code.append(f"    xor edx, edx")
            self.code.append(f"    idiv ecx")
        elif node.op == '%':
            self.code.append(f"    pop rcx")
            self.code.append(f"    xor edx, edx")
            self.code.append(f"    idiv ecx")
            self.code.append(f"    mov eax, edx")
    
    def _gen_logical(self, node):
        label_true = self.new_label("log_true")
        label_end = self.new_label("log_end")
        
        self._gen_node(node.left)
        self.code.append(f"    cmp eax, 0")
        
        if node.op == 'and':
            self.code.append(f"    je {label_end}")
        elif node.op == 'or':
            self.code.append(f"    jne {label_true}")
        
        self._gen_node(node.right)
        self.code.append(f"    cmp eax, 0")
        
        if node.op == 'and':
            self.code.append(f"    je {label_end}")
        elif node.op == 'or':
            self.code.append(f"    je {label_end}")
        
        self.code.append(f"  {label_true}:")
        self.code.append(f"    mov eax, 1")
        self.code.append(f"  {label_end}:")
    
    def _gen_compare(self, node):
        label_true = self.new_label("cmp_true")
        label_end = self.new_label("cmp_end")
        
        self._gen_node(node.left)
        self.code.append(f"    push rax")
        self._gen_node(node.right)
        self.code.append(f"    pop rcx")
        self.code.append(f"    cmp ecx, eax")
        
        jmp_map = {
            '==': 'je', '!=': 'jne', '<': 'jl', '>': 'jg',
            '<=': 'jle', '>=': 'jge', 'matches': 'je',
        }
        jmp = jmp_map.get(node.op, 'je')
        
        self.code.append(f"    {jmp} {label_true}")
        self.code.append(f"    mov eax, 0")
        self.code.append(f"    jmp {label_end}")
        self.code.append(f"  {label_true}:")
        self.code.append(f"    mov eax, 1")
        self.code.append(f"  {label_end}:")
    
    def _gen_call(self, node):
        if node.name == 'random':
            self._gen_node(node.args[0])
            self.code.append(f"    push rax")
            self._gen_node(node.args[1])
            self.code.append(f"    pop rcx")
            self.code.append(f"    sub eax, ecx")
            self.code.append(f"    inc eax")
            self.code.append(f"    push rax")
            self.code.append(f"    invoke GetTickCount")
            self.code.append(f"    xor edx, edx")
            self.code.append(f"    pop rcx")
            self.code.append(f"    div ecx")
            self.code.append(f"    add edx, ecx")
        elif node.name == 'length':
            self._gen_node(node.args[0])
            self.code.append(f"    invoke lstrlenA, eax")
        elif node.name == 'toUpperCase':
            self._gen_node(node.args[0])
            self.code.append(f"    invoke CharUpperA, eax")
        elif node.name == 'toLowerCase':
            self._gen_node(node.args[0])
            self.code.append(f"    invoke CharLowerA, eax")


def parse_and_generate(code, var_prefix="var_", obj_prefix="obj_"):
    ast = Operators.parse(code)
    if ast is None:
        return [], []
    gen = ASMGen(var_prefix, obj_prefix)
    return gen.generate(ast)