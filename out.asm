format PE64 GUI 5.0
entry start
include 'win64w.inc'
include 'Compiler/Macros/WinX64/win64.inc'
include 'Compiler/Macros/WinX64/vector.inc'
include 'Compiler/Macros/WinX64/hooks.inc'

section '.data' data readable writeable
WiseInit64
sys_win_count dq 1
  file_bytes_read dq 0
  file_handle dq 0
  _fpath_288 du 'test.txt',0
  _class_w du 'Class_w',0
  _title_w du 0x0046, 0x0069, 0x006C, 0x0065, 0x0020, 0x0054, 0x0065, 0x0073, 0x0074, 0
  wc_w WNDCLASS
  hwnd_w dq 0
  win_bg_w dd 0x001E1E1E
  hEdit_myEdit dq 0
  edit_brush_myEdit dq 0
  edit_rect_myEdit RECT 10, 10, 490, 210
  edit_bg_myEdit dd 0x002D2D2D
  edit_font_myEdit dd 0x00CCCCCC
  edit_font_size_myEdit dd 14
  _event_text_myEdit du 256 dup(0)
  _btn_text_btnLoad dw 0x004C, 0x006F, 0x0061, 0x0064, 0, 64 dup(0)
  btn_rect_btnLoad RECT 10, 230, 110, 260
  btn_state_btnLoad dd 0
  btn_gravity_btnLoad dd 37
  btn_bg_btnLoad dd 0x00D47800
  btn_font_btnLoad dd 0x00FFFFFF
  btn_border_btnLoad dd 0x00D47800
  btn_bg_hover_btnLoad dd 0x00D47800
  btn_font_hover_btnLoad dd 0x00FFFFFF
  btn_border_hover_btnLoad dd 0x00D47800
  btn_bg_click_btnLoad dd 0x00D47800
  btn_font_click_btnLoad dd 0x00FFFFFF
  btn_border_click_btnLoad dd 0x00D47800
  _btn_text_btnSave dw 0x0053, 0x0061, 0x0076, 0x0065, 0, 64 dup(0)
  btn_rect_btnSave RECT 120, 230, 220, 260
  btn_state_btnSave dd 0
  btn_gravity_btnSave dd 37
  btn_bg_btnSave dd 0x00008000
  btn_font_btnSave dd 0x00FFFFFF
  btn_border_btnSave dd 0x00008000
  btn_bg_hover_btnSave dd 0x00008000
  btn_font_hover_btnSave dd 0x00FFFFFF
  btn_border_hover_btnSave dd 0x00008000
  btn_bg_click_btnSave dd 0x00008000
  btn_font_click_btnSave dd 0x00FFFFFF
  btn_border_click_btnSave dd 0x00008000

section '.bss' readable writeable
  file_buffer db 1048576 dup (?)
  file_wide_buffer du 524288 dup (?)

section '.code' code readable executable
start:
    sub rsp, 8
    and rsp, -16
    sub rsp, 32
    xor ecx, ecx
    call [CoInitialize]
    lea rcx, [gdiplusToken]
    lea rdx, [gdiplusInput]
    xor r8, r8
    call [GdiplusStartup]
    mov [wc_w.style], CS_HREDRAW or CS_VREDRAW
    mov [wc_w.lpfnWndProc], WindowProc_w
    invoke GetModuleHandle, 0
    mov [wc_w.hInstance], rax
    invoke LoadIcon, 0, IDI_APPLICATION
    mov [wc_w.hIcon], rax
    invoke LoadCursor, 0, IDC_ARROW
    mov [wc_w.hCursor], rax
    invoke CreateSolidBrush, [win_bg_w]
    mov [wc_w.hbrBackground], rax
    mov [wc_w.lpszClassName], _class_w
    lea rcx, [wc_w]
    invoke RegisterClass, rcx
    test eax, eax
    jz exit_app
    invoke CreateWindowExW, 0, _class_w, _title_w, WS_OVERLAPPEDWINDOW or WS_VISIBLE or WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT, 520, 310, 0, 0, [wc_w.hInstance], 0
    test rax, rax
    jz exit_app
    mov [hwnd_w], rax
    mov [win_width], 520
    mov [win_height], 310
  .game_loop:
    lea rcx, [msg]
    invoke PeekMessage, rcx, 0, 0, 0, 1
    test eax, eax
    jnz .process_msg
    invoke WaitMessage
    jmp .game_loop
  .process_msg:
    cmp [msg.message], 18
    je exit_app
    lea rcx, [msg]
    invoke TranslateMessage, rcx
    lea rcx, [msg]
    invoke DispatchMessage, rcx
    jmp .game_loop
  exit_app:
    invoke CoUninitialize
    mov rcx, [msg.wParam]
    invoke ExitProcess, rcx
proc WindowProc_w hwnd, wmsg, wparam, lparam
    push rbx rsi rdi r14 r12 r13
    mov rbx, rcx
    mov rsi, rdx
    mov rdi, r8
    mov r14, r9
    cmp edx, 1
    je .wm_create
    cmp edx, 5
    je .wm_size
    cmp edx, 15
    je .wm_paint
    cmp edx, WM_CTLCOLOREDIT
    je .wm_ctlcoloredit
    cmp edx, 512
    je .wm_mousemove
    cmp edx, 513
    je .wm_lbuttondown
    cmp edx, WM_DESTROY
    je .wm_destroy
    pop r13 r12 r14 rdi rsi rbx
    invoke DefWindowProc, rcx, rdx, r8, r9
    ret
  .wm_create:
    mov dword [dark_mode_true], 1
    lea r8, [dark_mode_true]
    invoke DwmSetWindowAttribute, rbx, 20, r8, 4
    invoke CreateFont, 16, 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name
    mov [hFont], rax
    invoke CreateSolidBrush, [edit_bg_myEdit]
    mov [edit_brush_myEdit], rax
    invoke CreateWindowExW, 0, edit_class, 0, WS_CHILD or WS_VISIBLE or ES_MULTILINE or ES_AUTOVSCROLL or WS_VSCROLL, 10, 10, 480, 200, rbx, 2000, [wc_w.hInstance], 0
    mov [hEdit_myEdit], rax
    invoke SendMessageW, rax, WM_SETFONT, [hFont], 1
    InitBuffer [win_bg_w]
    invoke InvalidateRect, rbx, 0, 1
    xor eax, eax
    jmp .finish
  .wm_ctlcoloredit:
    cmp r14, [hEdit_myEdit]
    jne .ne_myEdit
    invoke SetTextColor, rdi, [edit_font_myEdit]
    invoke SetBkColor, rdi, [edit_bg_myEdit]
    mov rax, [edit_brush_myEdit]
    jmp .finish
  .ne_myEdit:
    pop r13 r12 r14 rdi rsi rbx
    invoke DefWindowProc, rcx, rdx, r8, r9
    ret
  .wm_size:
    size_handler
    jmp .finish
  .wm_paint:
    PaintBegin [win_bg_w]
    cmp [btn_state_btnLoad], 2
    jne .nc_btnLoad
    WiseFillRect [mem_dc], btn_rect_btnLoad, [btn_bg_click_btnLoad]
    WiseDrawText [mem_dc], _btn_text_btnLoad, btn_rect_btnLoad, [btn_gravity_btnLoad], [btn_font_click_btnLoad]
    invoke CreateSolidBrush, [btn_border_click_btnLoad]
    mov r15, rax
    lea rdx, [btn_rect_btnLoad]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_btnLoad
  .nc_btnLoad:
    cmp [btn_state_btnLoad], 1
    jne .nh_btnLoad
    WiseFillRect [mem_dc], btn_rect_btnLoad, [btn_bg_hover_btnLoad]
    WiseDrawText [mem_dc], _btn_text_btnLoad, btn_rect_btnLoad, [btn_gravity_btnLoad], [btn_font_hover_btnLoad]
    invoke CreateSolidBrush, [btn_border_hover_btnLoad]
    mov r15, rax
    lea rdx, [btn_rect_btnLoad]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_btnLoad
  .nh_btnLoad:
    WiseFillRect [mem_dc], btn_rect_btnLoad, [btn_bg_btnLoad]
    WiseDrawText [mem_dc], _btn_text_btnLoad, btn_rect_btnLoad, [btn_gravity_btnLoad], [btn_font_btnLoad]
    invoke CreateSolidBrush, [btn_border_btnLoad]
    mov r15, rax
    lea rdx, [btn_rect_btnLoad]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
  .fd_btnLoad:
    cmp [btn_state_btnSave], 2
    jne .nc_btnSave
    WiseFillRect [mem_dc], btn_rect_btnSave, [btn_bg_click_btnSave]
    WiseDrawText [mem_dc], _btn_text_btnSave, btn_rect_btnSave, [btn_gravity_btnSave], [btn_font_click_btnSave]
    invoke CreateSolidBrush, [btn_border_click_btnSave]
    mov r15, rax
    lea rdx, [btn_rect_btnSave]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_btnSave
  .nc_btnSave:
    cmp [btn_state_btnSave], 1
    jne .nh_btnSave
    WiseFillRect [mem_dc], btn_rect_btnSave, [btn_bg_hover_btnSave]
    WiseDrawText [mem_dc], _btn_text_btnSave, btn_rect_btnSave, [btn_gravity_btnSave], [btn_font_hover_btnSave]
    invoke CreateSolidBrush, [btn_border_hover_btnSave]
    mov r15, rax
    lea rdx, [btn_rect_btnSave]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_btnSave
  .nh_btnSave:
    WiseFillRect [mem_dc], btn_rect_btnSave, [btn_bg_btnSave]
    WiseDrawText [mem_dc], _btn_text_btnSave, btn_rect_btnSave, [btn_gravity_btnSave], [btn_font_btnSave]
    invoke CreateSolidBrush, [btn_border_btnSave]
    mov r15, rax
    lea rdx, [btn_rect_btnSave]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
  .fd_btnSave:
    PaintEnd
  .wm_mousemove:
    GetMousePos
  cmp eax, [btn_rect_btnLoad.left]
  jl .skip_hover_btnLoad
  cmp eax, [btn_rect_btnLoad.right]
  jg .skip_hover_btnLoad
  cmp edx, [btn_rect_btnLoad.top]
  jl .skip_hover_btnLoad
  cmp edx, [btn_rect_btnLoad.bottom]
  jg .skip_hover_btnLoad
    cmp [btn_state_btnLoad], 1
    je .hover_done_btnLoad
    mov [btn_state_btnLoad], 1
    invoke InvalidateRect, rbx, 0, 0
    jmp .hover_done_btnLoad
  .skip_hover_btnLoad:
    cmp [btn_state_btnLoad], 0
    je .hover_done_btnLoad
    mov [btn_state_btnLoad], 0
    invoke InvalidateRect, rbx, 0, 0
  .hover_done_btnLoad:
  cmp eax, [btn_rect_btnSave.left]
  jl .skip_hover_btnSave
  cmp eax, [btn_rect_btnSave.right]
  jg .skip_hover_btnSave
  cmp edx, [btn_rect_btnSave.top]
  jl .skip_hover_btnSave
  cmp edx, [btn_rect_btnSave.bottom]
  jg .skip_hover_btnSave
    cmp [btn_state_btnSave], 1
    je .hover_done_btnSave
    mov [btn_state_btnSave], 1
    invoke InvalidateRect, rbx, 0, 0
    jmp .hover_done_btnSave
  .skip_hover_btnSave:
    cmp [btn_state_btnSave], 0
    je .hover_done_btnSave
    mov [btn_state_btnSave], 0
    invoke InvalidateRect, rbx, 0, 0
  .hover_done_btnSave:
    invoke SetCursor, [wc_w.hCursor]
    jmp .finish
  .wm_lbuttondown:
    GetMousePos
  cmp eax, [btn_rect_btnLoad.left]
  jl .skip_click_btnLoad
  cmp eax, [btn_rect_btnLoad.right]
  jg .skip_click_btnLoad
  cmp edx, [btn_rect_btnLoad.top]
  jl .skip_click_btnLoad
  cmp edx, [btn_rect_btnLoad.bottom]
  jg .skip_click_btnLoad
    mov [btn_state_btnLoad], 2
    invoke CreateFileW, _fpath_288, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, INVALID_HANDLE_VALUE
    je .file_done_btnLoad__fpath_288_0
    mov [file_handle], rax
    invoke ReadFile, [file_handle], file_buffer, 1048575, file_bytes_read, 0
    mov rcx, [file_bytes_read]
    mov byte [file_buffer + rcx], 0
    invoke CloseHandle, [file_handle]
    invoke MultiByteToWideChar, 65001, 0, file_buffer, -1, file_wide_buffer, 524288
    invoke SetWindowTextW, [hEdit_myEdit], file_wide_buffer
  .file_done_btnLoad__fpath_288_0:
    lea rdi, [_btn_text_btnLoad]
    mov ecx, 64
    xor eax, eax
  .clear_title_btnLoad:
    mov word [rdi], ax
    add rdi, 2
    loop .clear_title_btnLoad
    lea rdi, [_btn_text_btnLoad]
    mov word [rdi], 0x0050
    add rdi, 2
    mov word [rdi], 0x0072
    add rdi, 2
    mov word [rdi], 0x0065
    add rdi, 2
    mov word [rdi], 0x0073
    add rdi, 2
    mov word [rdi], 0x0073
    add rdi, 2
    mov word [rdi], 0x0065
    add rdi, 2
    mov word [rdi], 0x0064
    add rdi, 2
    invoke InvalidateRect, rbx, 0, 1
  .skip_click_btnLoad:
  cmp eax, [btn_rect_btnSave.left]
  jl .skip_click_btnSave
  cmp eax, [btn_rect_btnSave.right]
  jg .skip_click_btnSave
  cmp edx, [btn_rect_btnSave.top]
  jl .skip_click_btnSave
  cmp edx, [btn_rect_btnSave.bottom]
  jg .skip_click_btnSave
    mov [btn_state_btnSave], 2
    invoke CreateFileW, _fpath_288, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, INVALID_HANDLE_VALUE
    je .file_done_btnSave__fpath_288_0
    mov [file_handle], rax
    invoke GetWindowTextW, [hEdit_myEdit], file_wide_buffer, 524288
    invoke WideCharToMultiByte, 65001, 0, file_wide_buffer, -1, file_buffer, 1048576, 0, 0
    invoke lstrlenA, file_buffer
    mov [file_bytes_read], rax
    invoke WriteFile, [file_handle], file_buffer, [file_bytes_read], file_bytes_read, 0
    invoke CloseHandle, [file_handle]
  .file_done_btnSave__fpath_288_0:
    lea rdi, [_btn_text_btnSave]
    mov ecx, 64
    xor eax, eax
  .clear_title_btnSave:
    mov word [rdi], ax
    add rdi, 2
    loop .clear_title_btnSave
    lea rdi, [_btn_text_btnSave]
    mov word [rdi], 0x0050
    add rdi, 2
    mov word [rdi], 0x0072
    add rdi, 2
    mov word [rdi], 0x0065
    add rdi, 2
    mov word [rdi], 0x0073
    add rdi, 2
    mov word [rdi], 0x0073
    add rdi, 2
    mov word [rdi], 0x0065
    add rdi, 2
    mov word [rdi], 0x0064
    add rdi, 2
    invoke InvalidateRect, rbx, 0, 1
  .skip_click_btnSave:
    jmp .finish
  .wm_destroy:
    DestroyGDI
    invoke DeleteObject, [edit_brush_myEdit]
    dec qword [sys_win_count]
    cmp qword [sys_win_count], 0
    jne .skip_quit
    invoke PostQuitMessage, 0
  .skip_quit:
    xor eax, eax
  .finish:
    pop r13 r12 r14 rdi rsi rbx
    ret
endp

section '.idata' import data readable writeable
  library kernel32, 'KERNEL32.DLL', user32, 'USER32.DLL', gdi32, 'GDI32.DLL', dwmapi, 'DWMAPI.DLL', ole32, 'OLE32.DLL', gdiplus, 'GDIPLUS.DLL'
  include 'api/kernel32.inc'
  include 'api/user32.inc'
  include 'api/gdi32.inc'
  import dwmapi, DwmSetWindowAttribute, 'DwmSetWindowAttribute'
  import ole32, CoInitialize, 'CoInitialize', CoUninitialize, 'CoUninitialize'
  import gdiplus, GdiplusStartup, 'GdiplusStartup', GdiplusShutdown, 'GdiplusShutdown'

