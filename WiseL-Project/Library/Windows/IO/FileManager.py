# Library/IO/FileManager.py
import re

def parse_file_operations(code):
    # Парсит file.addFileRead и file.addFileWrite
    operations = []
    lines = code.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # file.addFileRead "file.txt":
        m = re.match(r'file\.addFileRead\s+"([^"]+)"\s*:', line)
        if m:
            filepath = m.group(1)
            op = {"type": "read", "path": filepath, "onRead": {}, "onError": {}}
            i += 1
            # Парсим тело блока
            while i < len(lines):
                body_line = lines[i].strip()
                if not body_line or body_line.startswith("#"):
                    i += 1
                    continue
                
                # onRead:
                if body_line == "onRead:":
                    i += 1
                    while i < len(lines):
                        prop_line = lines[i].strip()
                        if prop_line == "onError:" or prop_line.startswith("file."):
                            break
                        if "=" in prop_line:
                            k, v = prop_line.split("=", 1)
                            k, v = k.strip(), v.strip().strip('"')
                            # Editor.title = file.content
                            m2 = re.match(r'(\w+)\.(\w+)\s*=\s*file\.(\w+)', k)
                            if m2:
                                widget = m2.group(1)
                                prop = m2.group(2)
                                source = m2.group(3)
                                op["onRead"][f"{widget}.{prop}"] = source
                        i += 1
                    continue
                
                # onError:
                if body_line == "onError:":
                    i += 1
                    while i < len(lines):
                        prop_line = lines[i].strip()
                        if prop_line.startswith("file."):
                            break
                        if "=" in prop_line:
                            k, v = prop_line.split("=", 1)
                            k, v = k.strip(), v.strip().strip('"')
                            op["onError"][k] = v
                        i += 1
                    continue
                
                if body_line.startswith("file."):
                    break
                i += 1
            operations.append(op)
            continue
        
        # file.addFileWrite "file.txt":
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
                
                # content = Editor.title
                m2 = re.match(r'content\s*=\s*(\w+)\.(\w+)', body_line)
                if m2:
                    op["content"] = {"widget": m2.group(1), "prop": m2.group(2)}
                i += 1
            operations.append(op)
            continue
        
        i += 1
    
    return operations

def gen_file_read_asm(op, widget_id_map):
    code = []
    path = op["path"]
    on_read = op.get("onRead", {})
    on_error = op.get("onError", {})
    
    # Строка пути к файлу
    path_label = f"_file_path_{hash(path) & 0xFFFF}"
    
    code.extend([
        f"    ; Чтение файла: {path}",
        f"    invoke CreateFileW, {path_label}, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0",
        f"    cmp rax, INVALID_HANDLE_VALUE",
        f"    je .file_read_error",
        f"    mov r14, rax",
        f"    invoke ReadFile, r14, file_buffer, 65535, bytes_read, 0",
        f"    cmp eax, 0",
        f"    je .file_read_close",
        f"    mov rcx, [bytes_read]",
        f"    mov byte [file_buffer + rcx], 0",
    ])
    
    for target, source in on_read.items():
        m = re.match(r'(\w+)\.(\w+)', target)
        if m:
            widget_name = m.group(1)
            prop_name = m.group(2)
            
            if widget_id_map and widget_name in widget_id_map:
                wid = widget_id_map[widget_name]
            else:
                wid = widget_name
            
            if source == "content":
                if prop_name == "title":
                    code.append(f"    invoke SetWindowTextW, [hEdit_{wid}], file_buffer")
            elif source == "path":
                if prop_name == "title":
                    code.append(f"    invoke SetWindowTextW, rbx, {path_label}")
    
    code.extend([
        f"  .file_read_close:",
        f"    invoke CloseHandle, r14",
        f"    jmp .file_read_done",
        f"  .file_read_error:",
    ])
    
    # Обработка ошибок
    for k, v in on_error.items():
        pass
    
    code.append(f"  .file_read_done:")
    
    return code, [f"  {path_label} du '{path}',0"]

def gen_file_write_asm(op, widget_id_map):
    code = []
    path = op["path"]
    content = op.get("content")
    
    path_label = f"_file_path_{hash(path) & 0xFFFF}"
    
    code.extend([
        f"    ; Запись файла: {path}",
        f"    invoke CreateFileW, {path_label}, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0",
        f"    cmp rax, INVALID_HANDLE_VALUE",
        f"    je .file_write_done",
        f"    mov r14, rax",
    ])
    
    if content:
        widget_name = content.get("widget")
        prop_name = content.get("prop")
        
        if widget_id_map and widget_name in widget_id_map:
            wid = widget_id_map[widget_name]
        else:
            wid = widget_name
        
        if prop_name == "title":
            code.extend([
                f"    invoke GetWindowTextLengthW, [hEdit_{wid}]",
                f"    inc eax",
                f"    mov [bytes_read], rax",
                f"    invoke GetWindowTextW, [hEdit_{wid}], file_buffer, [bytes_read]",
                f"    invoke WriteFile, r14, file_buffer, [bytes_read], bytes_read, 0",
            ])
    
    code.extend([
        f"    invoke CloseHandle, r14",
        f"  .file_write_done:",
    ])
    
    return code, [f"  {path_label} du '{path}',0"]

def gen_file_data():
    return [
        "  file_buffer db 65536 dup(0)",
        "  bytes_read dq 0",
    ]