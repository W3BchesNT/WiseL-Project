; ============================================================
; win64.inc — WiseL Runtime
; ============================================================

macro AppData {
    msg MSG
    ps PAINTSTRUCT
    rct RECT
    border_rect RECT
    buf_rect RECT
    win_width dd 0
    win_height dd 0
    sys_win_count dq 1
}

macro InitBuffer bg_color {
    invoke GetDC, rbx
    mov r15, rax
    invoke CreateCompatibleDC, r15
    mov [mem_dc], rax
    invoke CreateCompatibleBitmap, r15, 2000, 2000
    mov [mem_bmp], rax
    invoke SelectObject, [mem_dc], rax
    mov [old_bmp], rax
    invoke CreateSolidBrush, bg_color
    mov r13, rax
    mov [buf_rect.left], 0
    mov [buf_rect.top], 0
    mov [buf_rect.right], 2000
    mov [buf_rect.bottom], 2000
    lea rdx, [buf_rect]
    invoke FillRect, [mem_dc], rdx, r13
    invoke DeleteObject, r13
    invoke ReleaseDC, rbx, r15
}

macro DestroyBuffer {
    invoke SelectObject, [mem_dc], [old_bmp]
    invoke DeleteObject, [mem_bmp]
    invoke DeleteDC, [mem_dc]
}

macro AppInit {
    sub rsp, 8
    and rsp, -16
    sub rsp, 32
}

macro MessageLoop _msg {
  .poll:
    lea   rcx, [_msg]
    invoke GetMessage, rcx, 0, 0, 0
    test  eax, eax
    jz    .done
    lea   rcx, [_msg]
    invoke TranslateMessage, rcx
    lea   rcx, [_msg]
    invoke DispatchMessage, rcx
    jmp   .poll
  .done:
}
macro MessageLoopGDI _msg {
  .poll:
    lea   rcx, [_msg]
    invoke GetMessage, rcx, 0, 0, 0
    test  eax, eax
    jz    exit
    lea   rcx, [_msg]
    invoke TranslateMessage, rcx
    lea   rcx, [_msg]
    invoke DispatchMessage, rcx
    jmp   .poll
  exit:
    invoke CoUninitialize
}

macro WindowProc name {
    proc WindowProc_#name hwnd, wmsg, wparam, lparam
        push rbx rsi rdi r14 r12 r13
        mov rbx, rcx
}

macro EndWindowProc {
    .finish:
        pop r13 r12 r14 rdi rsi rbx
        ret
    endp
}

macro On msg, handler {
    cmp edx, msg
    je handler
}

macro OnPaint {
    lea rdx, [ps]
    invoke BeginPaint, rbx, rdx
    lea rdx, [ps]
    invoke EndPaint, rbx, rdx
    xor eax, eax
    jmp .finish
}

macro OnPaintBuf {
    lea rdx, [ps]
    invoke BeginPaint, rbx, rdx
    mov r12, rax
    invoke BitBlt, r12, 0, 0, [win_width], [win_height], [mem_dc], 0, 0, SRCCOPY
    lea rdx, [ps]
    invoke EndPaint, rbx, rdx
    xor eax, eax
    jmp .finish
}

macro OnDestroy {
    invoke PostQuitMessage, 0
    xor eax, eax
    jmp .finish
}

macro EnableDarkMode {
    dark_mode_true dd 1
    mov dword [dark_mode_true], 1
    lea r8, [dark_mode_true]
    invoke DwmSetWindowAttribute, rbx, 20, r8, 4
}

macro GetMousePos {
    mov rdx, r14
    movzx eax, dx
    shr rdx, 16
    movzx edx, dx
}

macro ProcessCommandFile {
    invoke GetCommandLineW
    mov rsi, rax
    cmp word [rsi], '"'
    je .pcf_skip_quoted
  .pcf_skip_unquoted:
    cmp word [rsi], ' '
    je .pcf_found_arg
    cmp word [rsi], 0
    je .pcf_done
    add rsi, 2
    jmp .pcf_skip_unquoted
  .pcf_skip_quoted:
    add rsi, 2
    cmp word [rsi], '"'
    jne .pcf_skip_quoted
    add rsi, 2
  .pcf_found_arg:
    cmp word [rsi], ' '
    jne .pcf_copy
    add rsi, 2
    jmp .pcf_found_arg
  .pcf_copy:
    lea rdi, [cmd_line_buffer]
    mov rcx, 8192
  .pcf_loop:
    mov ax, [rsi]
    cmp ax, 0
    je .pcf_open
    cmp ax, '\"'
    je .pcf_open
    mov [rdi], ax
    add rsi, 2
    add rdi, 2
    dec rcx
    jnz .pcf_loop
  .pcf_open:
    mov word [rdi], 0
    invoke CreateFileW, cmd_line_buffer, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, INVALID_HANDLE_VALUE
    je .pcf_done
    mov r14, rax
    invoke ReadFile, r14, _file_buffer, 8191, _bytes_read, 0
    cmp eax, 0
    je .pcf_close
    mov rcx, [_bytes_read]
    mov byte [_file_buffer + rcx], 0
    invoke MultiByteToWideChar, 65001, 0, _file_buffer, -1, _wide_buffer, 8192
  .pcf_close:
    invoke CloseHandle, r14
  .pcf_done:
}

macro LoadWindowIcon name {
    invoke LoadIcon, qword [wc_#name + 24], 1
    mov qword [wc_#name + 32], rax
}

macro AppIcon path {
    section '.rsrc' resource data readable
      directory RT_ICON, icons, RT_GROUP_ICON, group_icons
      resource icons, 1, LANG_NEUTRAL, icon_data
      resource group_icons, 1, LANG_NEUTRAL, main_icon
      icon main_icon, icon_data, path
}

macro CreateAppWindow name, w, h, bg {
    mov dword [wc_#name], CS_VREDRAW
    lea rax, [WindowProc_#name]
    mov qword [wc_#name + 8], rax
    invoke LoadCursor, 0, IDC_ARROW
    mov qword [wc_#name + 40], rax
    mov qword [wc_#name + 48], bg
    mov qword [wc_#name + 64], _class_#name
    lea rcx, [wc_#name]
    invoke RegisterClass, rcx
    test eax, eax
    jz .exit_app
    invoke CreateWindowExW, 0, _class_#name, _title_#name, WS_OVERLAPPEDWINDOW or WS_VISIBLE or WS_CLIPCHILDREN, \
           CW_USEDEFAULT, CW_USEDEFAULT, w, h, \
           0, 0, qword [wc_#name + 24], 0
    test rax, rax
    jz .exit_app
    mov [hwnd_#name], rax
    mov [win_width], w
    mov [win_height], h
}

macro WM_SIZE {
    mov eax, r14d
    and eax, 0xFFFF
    mov [win_width], eax
    mov eax, r14d
    shr eax, 16
    mov [win_height], eax
    invoke InvalidateRect, rbx, 0, 1
    xor eax, eax
    jmp .finish
}

macro WM_DESTROY {
    invoke PostQuitMessage, 0
    xor eax, eax
    jmp .finish
}

macro WM_PAINT {
    lea rdx, [ps]
    invoke BeginPaint, rbx, rdx
    lea rdx, [ps]
    invoke EndPaint, rbx, rdx
    xor eax, eax
    jmp .finish
}

; ═══ МЫШЬ ═══

macro if_mouse_in rect, id {
    cmp eax, [rect + 0]
    jl .mo_#id
    cmp eax, [rect + 8]
    jg .mo_#id
    cmp edx, [rect + 4]
    jl .mo_#id
    cmp edx, [rect + 12]
    jg .mo_#id
}

macro else_mouse id {
    jmp .md_#id
  .mo_#id:
}

macro end_mouse id {
  .md_#id:
}

macro DestroyGDI {
    invoke SelectObject, [mem_dc], [old_bmp]
    invoke DeleteObject, [mem_bmp]
    invoke DeleteDC, [mem_dc]
    invoke GdiplusShutdown, [gdiplusToken]
    invoke CoUninitialize
}

macro size_handler {
    mov eax, r14d
    and eax, 0xFFFF
    mov [win_width], eax
    mov eax, r14d
    shr eax, 16
    mov [win_height], eax
    invoke InvalidateRect, rbx, 0, 0
    xor eax, eax
}

macro WiseInit64 {
    msg MSG
    ps PAINTSTRUCT
    rct RECT
    border_rect RECT
    buf_rect RECT
    sys_font_name du 'Segoe UI',0
    edit_class du 'EDIT',0
    hFont dq 0
    mem_dc dq 0
    mem_bmp dq 0
    old_bmp dq 0
    win_width dd 0
    win_height dd 0
    dark_mode_true dd 1
    gdiplusToken dq 0
    gdiplusInput dq 1, 0, 0, 0
}

; win64.inc — GDI+ импорты
macro gdiplus_imports {
    import ole32, CoInitialize, 'CoInitialize', CoUninitialize, 'CoUninitialize'
    import gdiplus, GdiplusStartup, 'GdiplusStartup', GdiplusShutdown, 'GdiplusShutdown', \
           GdipLoadImageFromFile, 'GdipLoadImageFromFile', GdipCreateFromHDC, 'GdipCreateFromHDC', \
           GdipDrawImageRectI, 'GdipDrawImageRectI', GdipDisposeImage, 'GdipDisposeImage', \
           GdipDeleteGraphics, 'GdipDeleteGraphics', GdipGetImageWidth, 'GdipGetImageWidth', \
           GdipGetImageHeight, 'GdipGetImageHeight'
}

macro dwm_imports {
    import dwmapi, DwmSetWindowAttribute, 'DwmSetWindowAttribute'
}

macro DestroyBase {
    invoke SelectObject, [mem_dc], [old_bmp]
    invoke DeleteObject, [mem_bmp]
    invoke DeleteDC, [mem_dc]
}

macro PaintBegin bg_color {
    lea rdx, [ps]
    invoke BeginPaint, rbx, rdx
    mov r12, rax
    mov [buf_rect.left], 0
    mov [buf_rect.top], 0
    mov [buf_rect.right], 2000
    mov [buf_rect.bottom], 2000
    invoke CreateSolidBrush, bg_color
    mov r15, rax
    lea rdx, [buf_rect]
    invoke FillRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    invoke SelectObject, [mem_dc], [hFont]
    invoke SetBkMode, [mem_dc], 1
}

macro PaintEnd {
    invoke BitBlt, r12, 0, 0, [win_width], [win_height], [mem_dc], 0, 0, SRCCOPY
    lea rdx, [ps]
    invoke EndPaint, rbx, rdx
    xor eax, eax
    jmp .finish
}