# Library/Core/Operators.py
"""Единый парсер выражений WiseL — платформонезависимый"""
import re


class ExprNode:
    pass


class NumberNode(ExprNode):
    def __init__(self, value):
        self.value = int(value)


class FloatNode(ExprNode):
    def __init__(self, value):
        self.value = float(value)


class StringNode(ExprNode):
    def __init__(self, value):
        self.value = value


class BoolNode(ExprNode):
    def __init__(self, value):
        self.value = value


class VarNode(ExprNode):
    def __init__(self, name):
        self.name = name


class PropertyNode(ExprNode):
    def __init__(self, obj, prop):
        self.obj = obj
        self.prop = prop


class BinOpNode(ExprNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class UnaryOpNode(ExprNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class CompareNode(ExprNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class CallNode(ExprNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class AssignNode(ExprNode):
    def __init__(self, target, value):
        self.target = target
        self.value = value


class RegexMatchNode(ExprNode):
    def __init__(self, text, pattern):
        self.text = text
        self.pattern = pattern


class RegexGroupNode(ExprNode):
    def __init__(self, group_index):
        self.group_index = group_index


class StringVarNode(ExprNode):
    def __init__(self, name):
        self.name = name


PRECEDENCE = {
    'or': 1,
    'and': 2,
    'not': 3,
    '==': 4, '!=': 4, '<': 4, '>': 4, '<=': 4, '>=': 4, 'matches': 4,
    '+': 5, '-': 5,
    '*': 6, '/': 6, '%': 6,
    '.': 8,
}


def tokenize(code):
    tokens = []
    i = 0
    while i < len(code):
        c = code[i]
        
        if c in ' \t\n\r':
            i += 1
            continue
        
        if c.isdigit() or (c == '-' and i + 1 < len(code) and code[i + 1].isdigit()):
            num = ''
            while i < len(code) and (code[i].isdigit() or code[i] == '.' or (num == '' and code[i] == '-')):
                num += code[i]
                i += 1
            if '.' in num:
                tokens.append(('FLOAT', num))
            else:
                tokens.append(('NUMBER', num))
            continue
        
        if c == '"':
            i += 1
            s = ''
            while i < len(code) and code[i] != '"':
                if code[i] == '\\':
                    i += 1
                    if code[i] == 'n': s += '\n'
                    elif code[i] == 't': s += '\t'
                    else: s += code[i]
                else:
                    s += code[i]
                i += 1
            i += 1
            tokens.append(('STRING', s))
            continue
        
        if c.isalpha() or c == '_':
            ident = ''
            while i < len(code) and (code[i].isalnum() or code[i] == '_'):
                ident += code[i]
                i += 1
            if ident in ('true', 'false'):
                tokens.append(('BOOL', ident))
            elif ident in ('and', 'or', 'not', 'matches'):
                tokens.append(('KEYWORD', ident))
            elif ident == 'regex':
                tokens.append(('REGEX', ident))
            else:
                tokens.append(('IDENT', ident))
            continue
        
        if i + 1 < len(code):
            two = code[i:i+2]
            if two in ('==', '!=', '<=', '>=', '->', '+='):
                tokens.append(('OP', two))
                i += 2
                continue
        
        if c in '+-*/%<>=()':
            tokens.append(('OP', c))
            i += 1
            continue
        
        if c == '.':
            tokens.append(('DOT', '.'))
            i += 1
            continue
        if c == ',':
            tokens.append(('COMMA', ','))
            i += 1
            continue
        if c == '=':
            tokens.append(('ASSIGN', '='))
            i += 1
            continue
        
        i += 1
    
    return tokens


class Parser:
    def __init__(self, code):
        self.tokens = tokenize(code)
        self.pos = 0
    
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def consume(self, expected_type=None, expected_value=None):
        token = self.peek()
        if token is None:
            return None
        if expected_type and token[0] != expected_type:
            return None
        if expected_value and token[1] != expected_value:
            return None
        self.pos += 1
        return token
    
    def parse(self):
        return self.parse_or()
    
    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek()[0] == 'KEYWORD' and self.peek()[1] == 'or':
            self.consume()
            right = self.parse_and()
            left = BinOpNode(left, 'or', right)
        return left
    
    def parse_and(self):
        left = self.parse_not()
        while self.peek() and self.peek()[0] == 'KEYWORD' and self.peek()[1] == 'and':
            self.consume()
            right = self.parse_not()
            left = BinOpNode(left, 'and', right)
        return left
    
    def parse_not(self):
        if self.peek() and self.peek()[0] == 'KEYWORD' and self.peek()[1] == 'not':
            self.consume()
            return UnaryOpNode('not', self.parse_compare())
        return self.parse_compare()
    
    def parse_compare(self):
        left = self.parse_addsub()
        op_token = self.peek()
        if op_token and op_token[0] == 'OP' and op_token[1] in ('==', '!=', '<', '>', '<=', '>='):
            self.consume()
            right = self.parse_addsub()
            return CompareNode(left, op_token[1], right)
        elif op_token and op_token[0] == 'KEYWORD' and op_token[1] == 'matches':
            self.consume()
            right = self.parse_addsub()
            return CompareNode(left, 'matches', right)
        return left
    
    def parse_addsub(self):
        left = self.parse_muldiv()
        while self.peek() and self.peek()[0] == 'OP' and self.peek()[1] in ('+', '-'):
            op = self.consume()[1]
            right = self.parse_muldiv()
            left = BinOpNode(left, op, right)
        return left
    
    def parse_muldiv(self):
        left = self.parse_unary()
        while self.peek() and self.peek()[0] == 'OP' and self.peek()[1] in ('*', '/', '%'):
            op = self.consume()[1]
            right = self.parse_unary()
            left = BinOpNode(left, op, right)
        return left
    
    def parse_unary(self):
        if self.peek() and self.peek()[0] == 'OP' and self.peek()[1] == '-':
            self.consume()
            return UnaryOpNode('-', self.parse_primary())
        return self.parse_primary()
    
    def parse_primary(self):
        token = self.peek()
        if token is None:
            return None
        
        if token[0] == 'NUMBER':
            self.consume()
            return NumberNode(token[1])
        if token[0] == 'FLOAT':
            self.consume()
            return FloatNode(token[1])
        
        if token[0] == 'STRING':
            self.consume()
            return StringNode(token[1])
        
        if token[0] == 'BOOL':
            self.consume()
            return BoolNode(token[1] == 'true')
        
        if token[0] == 'REGEX':
            self.consume()
            if self.peek() and self.peek()[0] == 'DOT':
                self.consume()
                if self.peek() and self.peek()[0] == 'IDENT' and self.peek()[1] == 'group':
                    self.consume()
                    self.consume('LPAREN')
                    group_num = self.parse()
                    self.consume('RPAREN')
                    return RegexGroupNode(group_num)
            return VarNode('regex')
        
        if token[0] == 'IDENT':
            ident = self.consume()[1]
            
            if self.peek() and self.peek()[0] == 'LPAREN':
                self.consume()
                args = []
                if self.peek() and self.peek()[0] != 'RPAREN':
                    args.append(self.parse())
                    while self.peek() and self.peek()[0] == 'COMMA':
                        self.consume()
                        args.append(self.parse())
                self.consume('RPAREN')
                return CallNode(ident, args)
            
            if self.peek() and self.peek()[0] == 'DOT':
                self.consume()
                prop_token = self.peek()
                if prop_token and prop_token[0] == 'IDENT':
                    prop = self.consume()[1]
                    
                    if self.peek() and self.peek()[0] == 'LPAREN':
                        self.consume()
                        args = []
                        if self.peek() and self.peek()[0] != 'RPAREN':
                            args.append(self.parse())
                            while self.peek() and self.peek()[0] == 'COMMA':
                                self.consume()
                                args.append(self.parse())
                        self.consume('RPAREN')
                        return CallNode(prop, [VarNode(ident)] + args)
                    
                    return PropertyNode(VarNode(ident), prop)
            
            return VarNode(ident)
        
        if token[0] == 'LPAREN':
            self.consume()
            expr = self.parse()
            self.consume('RPAREN')
            return expr
        
        return None


def parse(code):
    parser = Parser(code)
    return parser.parse()