# Library/Core/Random.py
"""Парсер random для WiseL — платформонезависимый"""
import re


class RandomExpr:
    def __init__(self, min_val, max_val, step=1):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step


def parse_random(expr):
    """Парсит выражение random MIN MAX или random MIN MAX STEP"""
    m = re.match(r'random\s+(-?\d+)\s+(-?\d+)(?:\s+(\d+))?', expr.strip())
    if m:
        min_val = int(m.group(1))
        max_val = int(m.group(2))
        step = int(m.group(3)) if m.group(3) else 1
        return RandomExpr(min_val, max_val, step)
    return None