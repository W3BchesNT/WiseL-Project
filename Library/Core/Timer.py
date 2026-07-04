# Library/Core/Timer.py
"""Парсер таймеров WiseL — с поддержкой if"""
import re


class TimerDecl:
    def __init__(self, name, interval, actions):
        self.name = name
        self.interval = interval
        self.actions = actions


class TimerAction:
    def __init__(self, obj_name, prop, op, value):
        self.obj_name = obj_name
        self.prop = prop
        self.op = op
        self.value = value


class IfBlock:
    def __init__(self, left_obj, left_prop, op, right_obj, right_prop, body):
        self.left_obj = left_obj
        self.left_prop = left_prop
        self.op = op
        self.right_obj = right_obj
        self.right_prop = right_prop
        self.body = body


def parse_timer(lines, start_i):
    i = start_i
    timers = []
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        m = re.match(r'Timer\s+(\w+)\((\d+)\)\s*:', line)
        if m:
            name = m.group(1)
            interval = int(m.group(2))
            actions = []
            i += 1
            actions, i = parse_actions(lines, i)
            timers.append(TimerDecl(name, interval, actions))
            continue
        else:
            break
    
    return timers, i


def parse_actions(lines, start_i):
    """Парсит список действий (включая вложенные if)"""
    actions = []
    i = start_i
    
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        
        # if obj.prop == obj.prop:
        m_if = re.match(r'if\s+(\w+)\.(\w+)\s*(==|!=)\s*(\w+)\.(\w+)\s*:', line)
        if m_if:
            left_obj = m_if.group(1)
            left_prop = m_if.group(2)
            op = m_if.group(3)
            right_obj = m_if.group(4)
            right_prop = m_if.group(5)
            i += 1
            body, i = parse_actions(lines, i)
            actions.append(IfBlock(left_obj, left_prop, op, right_obj, right_prop, body))
            continue
        
        # obj.prop = random MIN MAX
        m_rand = re.match(r'(\w+)\.(\w+)\s*=\s*random\s+(-?\d+)\s+(-?\d+)', line)
        if m_rand:
            obj_name = m_rand.group(1)
            prop = m_rand.group(2)
            min_val = m_rand.group(3)
            max_val = m_rand.group(4)
            actions.append(TimerAction(obj_name, prop, 'random', f"{min_val} {max_val}"))
            i += 1
            continue
        
        # obj.prop = obj.prop +/- value
        m2 = re.match(r'(\w+)\.(\w+)\s*=\s*\1\.\2\s*([+\-])\s*(\d+)', line.replace(' ', ''))
        if m2:
            obj_name = m2.group(1)
            prop = m2.group(2)
            op = m2.group(3)
            value = int(m2.group(4))
            actions.append(TimerAction(obj_name, prop, op, value))
            i += 1
            continue
        
        # obj.prop = value
        m3 = re.match(r'(\w+)\.(\w+)\s*=\s*(\d+)', line.replace(' ', ''))
        if m3:
            obj_name = m3.group(1)
            prop = m3.group(2)
            value = int(m3.group(3))
            actions.append(TimerAction(obj_name, prop, '=', value))
            i += 1
            continue
        
        break
    
    return actions, i