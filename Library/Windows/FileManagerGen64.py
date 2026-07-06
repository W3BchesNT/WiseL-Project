# Library/Windows/FileManagerGen64.py
"""Генератор ASM для файловых операций Windows x64"""
import os, sys, re

CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

import FileManager


def gen_data():
    """Генерит общие данные для файловых операций"""
    return [
        "  file_buffer db 65536 dup(0)",
        "  file_bytes_read dq 0",
        "  file_handle dq 0",
    ]


def gen_read_code(op, widget_id_map=None):
    """Генерит ASM для чтения файла"""
    code = []
    path = op["path"]
    label = f"_file_path_{abs(hash(path)) % 10000}"

    code += [
        f"    ; Чтение файла: {path}",
        f"    invoke CreateFileW, {label}, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0",
        f"    cmp rax, INVALID_HANDLE_VALUE",
        f"    je .file_read_error_{label}",
        f"    mov [file_handle], rax",
        f"    invoke ReadFile, [file_handle], file_buffer, 65535, file_bytes_read, 0",
        f"    cmp eax, 0",
        f"    je .file_read_close_{label}",
        f"    mov rcx, [file_bytes_read]",
        f"    mov byte [file_buffer + rcx], 0",
    ]

    for target, source in op.get("onRead", {}).items():
        m = re.match(r'(\w+)\.(\w+)', target)
        if m:
            widget_name = m.group(1)
            prop_name = m.group(2)
            wid = widget_id_map.get(widget_name, widget_name) if widget_id_map else widget_name

            if source == "content" and prop_name == "title":
                code.append(f"    invoke SetWindowTextW, [hEdit_{wid}], file_buffer")

    code += [
        f"  .file_read_close_{label}:",
        f"    invoke CloseHandle, [file_handle]",
        f"    jmp .file_done_{label}",
        f"  .file_read_error_{label}:",
        f"  .file_done_{label}:",
    ]

    return code, [f"  {label} du '{path}',0"]


def gen_write_code(op, widget_id_map=None):
    """Генерит ASM для записи файла"""
    code = []
    path = op["path"]
    content = op.get("content", {})
    label = f"_file_path_{abs(hash(path)) % 10000}"

    code += [
        f"    ; Запись файла: {path}",
        f"    invoke CreateFileW, {label}, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0",
        f"    cmp rax, INVALID_HANDLE_VALUE",
        f"    je .file_write_done_{label}",
        f"    mov [file_handle], rax",
    ]

    if content:
        widget_name = content.get("widget", "")
        prop_name = content.get("prop", "")
        wid = widget_id_map.get(widget_name, widget_name) if widget_id_map else widget_name

        if prop_name == "title":
            code += [
                f"    invoke GetWindowTextLengthW, [hEdit_{wid}]",
                f"    inc eax",
                f"    mov [file_bytes_read], rax",
                f"    invoke GetWindowTextW, [hEdit_{wid}], file_buffer, [file_bytes_read]",
                f"    invoke WriteFile, [file_handle], file_buffer, [file_bytes_read], file_bytes_read, 0",
            ]

    code += [
        f"    invoke CloseHandle, [file_handle]",
        f"  .file_write_done_{label}:",
    ]

    return code, [f"  {label} du '{path}',0"]