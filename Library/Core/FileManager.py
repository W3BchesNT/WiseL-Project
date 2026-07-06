# Library/Core/FileManager.py
"""Парсер файловых операций WiseL — платформонезависимый"""
import re


class FileOperation:
    pass


class FileReadOp(FileOperation):
    def __init__(self, path, target_widget, target_prop, source="content"):
        self.path = path
        self.target_widget = target_widget
        self.target_prop = target_prop
        self.source = source


class FileWriteOp(FileOperation):
    def __init__(self, path, source_widget, source_prop):
        self.path = path
        self.source_widget = source_widget
        self.source_prop = source_prop


def parse_file_operations(code):
    operations = []
    lines = code.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # file.addFileRead "path.txt":
        m = re.match(r'file\.addFileRead\s+"([^"]+)"\s*:', line)
        if m:
            filepath = m.group(1)
            op = {"type": "read", "path": filepath, "onRead": {}}
            i += 1
            while i < len(lines):
                body_line = lines[i].strip()
                if not body_line or body_line.startswith("#"):
                    i += 1
                    continue
                if body_line.startswith("file.") or body_line.startswith("window "):
                    break
                if "=" in body_line:
                    k, v = body_line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"')
                    m2 = re.match(r'(\w+)\.(\w+)\s*=\s*file\.(\w+)', k)
                    if m2:
                        widget = m2.group(1)
                        prop = m2.group(2)
                        source = m2.group(3)
                        op["onRead"][f"{widget}.{prop}"] = source
                i += 1
            operations.append(op)
            continue

        # file.addFileWrite "path.txt":
        m = re.match(r'file\.addFileWrite\s+"([^"]+)"\s*:', line)
        if m:
            filepath = m.group(1)
            op = {"type": "write", "path": filepath, "content": None}
            i += 1
            while i < len(lines):
                body_line = lines[i].strip()
                if not body_line or body_line.startswith("#"):
                    i += 1
                    continue
                if body_line.startswith("file.") or body_line.startswith("window "):
                    break
                m2 = re.match(r'content\s*=\s*(\w+)\.(\w+)', body_line)
                if m2:
                    op["content"] = {"widget": m2.group(1), "prop": m2.group(2)}
                i += 1
            operations.append(op)
            continue

        i += 1

    return operations