format PE64 GUI 5.0
entry start
include 'win64w.inc'
include 'Compiler/Macros/WinX64/win64.inc'
include 'Compiler/Macros/WinX64/vector.inc'
include 'Compiler/Macros/WinX64/hooks.inc'

section '.data' data readable writeable
WiseInit64
sys_win_count dq 1
  fps_counter dd 0
  fps_last_tick dd 0
  fps_current dd 0
  fps_buf dw 16 dup(0)
  fps_perf_freq dq 0
  fps_perf_start dq 0
  fps_perf_end dq 0
  fps_target_ms dd 0
  _class_w du 'Class_w',0
  _title_w du 0x0057, 0x0069, 0x0073, 0x0065, 0x0020, 0x0057, 0x0069, 0x006E, 0x0064, 0x006F, 0x0077, 0
  wc_w WNDCLASS
  hwnd_w dq 0
  win_bg_w dd 0x00FFFFFF
  _label_text_label dw 0x004C, 0x0061, 0x0062, 0x0065, 0x006C, 0x0020, 0x0031, 0
  label_rect_label RECT 10, 10, 310, 40
  label_font_label dd 0x00000000
  label_font_size_label dd 16
  label_gravity_label dd 0x10
  _btn_text_button dw 0x0042, 0x0075, 0x0074, 0x0074, 0x006F, 0x006E, 0x0020, 0x0031, 0
  btn_rect_button RECT 10, 40, 130, 76
  btn_state_button dd 0
  btn_gravity_button dd 37
  btn_bg_button dd 0x00D47800
  btn_font_button dd 0x00FFFFFF
  btn_border_button dd 0x00D47800
  btn_bg_hover_button dd 0x0000AA00
  btn_font_hover_button dd 0x00FFFFFF
  btn_border_hover_button dd 0x0000AA00
  btn_bg_click_button dd 0x00D47800
  btn_font_click_button dd 0x00FFFFFF
  btn_border_click_button dd 0x00D47800
  hEdit_textbox dq 0
  edit_brush_textbox dq 0
  edit_rect_textbox RECT 10, 80, 147, 116
  edit_bg_textbox dd 0x00B4B4B4
  edit_font_textbox dd 0x00000000
  edit_font_size_textbox dd 14

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
    invoke LoadIcon, [wc_w.hInstance], 1
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
    invoke CreateWindowExW, 0, _class_w, _title_w, WS_OVERLAPPEDWINDOW or WS_VISIBLE or WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT, 400, 300, 0, 0, [wc_w.hInstance], 0
    test rax, rax
    jz exit_app
    mov [hwnd_w], rax
    mov [win_width], 400
    mov [win_height], 300
  .game_loop:
    invoke InvalidateRect, [hwnd_w], 0, 0
    lea rcx, [msg]
    invoke PeekMessage, rcx, 0, 0, 0, 1
    test eax, eax
    jz .game_loop
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
    invoke CreateFont, 16, 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name
    mov [hFont], rax
    invoke CreateSolidBrush, [edit_bg_textbox]
    mov [edit_brush_textbox], rax
    invoke CreateWindowExW, 0, edit_class, 0, WS_CHILD or WS_VISIBLE or ES_MULTILINE or ES_AUTOVSCROLL or WS_VSCROLL, 10, 80, 137, 36, rbx, 2000, [wc_w.hInstance], 0
    mov [hEdit_textbox], rax
    invoke SendMessageW, rax, WM_SETFONT, [hFont], 1
    InitBuffer [win_bg_w]
    invoke InvalidateRect, rbx, 0, 1
    xor eax, eax
    jmp .finish
  .wm_ctlcoloredit:
    cmp r14, [hEdit_textbox]
    jne .ne_textbox
    invoke SetTextColor, rdi, [edit_font_textbox]
    invoke SetBkColor, rdi, [edit_bg_textbox]
    mov rax, [edit_brush_textbox]
    jmp .finish
  .ne_textbox:
    pop r13 r12 r14 rdi rsi rbx
    invoke DefWindowProc, rcx, rdx, r8, r9
    ret
  .wm_size:
    size_handler
    jmp .finish
  .wm_paint:
    inc dword [fps_counter]
    invoke GetTickCount
    mov ecx, eax
    sub ecx, [fps_last_tick]
    cmp ecx, 1000
    jl .fps_skip
    mov [fps_last_tick], eax
    mov eax, [fps_counter]
    mov [fps_current], eax
    mov dword [fps_counter], 0
    mov eax, [fps_current]
    lea rdi, [fps_buf]
    call fps_itoa
  .fps_skip:
    PaintBegin [win_bg_w]
    invoke CreateFontW, [label_font_size_label], 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name
    mov r14, rax
    invoke SelectObject, [mem_dc], r14
    WiseDrawText [mem_dc], _label_text_label, label_rect_label, [label_gravity_label], [label_font_label]
    invoke SelectObject, [mem_dc], [hFont]
    invoke DeleteObject, r14
    cmp [btn_state_button], 2
    jne .nc_button
    WiseFillRect [mem_dc], btn_rect_button, [btn_bg_click_button]
    WiseDrawText [mem_dc], _btn_text_button, btn_rect_button, [btn_gravity_button], [btn_font_click_button]
    invoke CreateSolidBrush, [btn_border_click_button]
    mov r15, rax
    lea rdx, [btn_rect_button]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_button
  .nc_button:
    cmp [btn_state_button], 1
    jne .nh_button
    WiseFillRect [mem_dc], btn_rect_button, [btn_bg_hover_button]
    WiseDrawText [mem_dc], _btn_text_button, btn_rect_button, [btn_gravity_button], [btn_font_hover_button]
    invoke CreateSolidBrush, [btn_border_hover_button]
    mov r15, rax
    lea rdx, [btn_rect_button]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
    jmp .fd_button
  .nh_button:
    WiseFillRect [mem_dc], btn_rect_button, [btn_bg_button]
    WiseDrawText [mem_dc], _btn_text_button, btn_rect_button, [btn_gravity_button], [btn_font_button]
    invoke CreateSolidBrush, [btn_border_button]
    mov r15, rax
    lea rdx, [btn_rect_button]
    invoke FrameRect, [mem_dc], rdx, r15
    invoke DeleteObject, r15
  .fd_button:
    PaintEnd
  .wm_mousemove:
    GetMousePos
    if_mouse_in btn_rect_button, button
    cmp [btn_state_button], 1
    je .nr_button
    mov [btn_state_button], 1
    invoke InvalidateRect, rbx, 0, 0
    jmp .md_button
    else_mouse button
    cmp [btn_state_button], 0
    je .nr_button
    mov [btn_state_button], 0
    invoke InvalidateRect, rbx, 0, 0
    end_mouse button
  .nr_button:
    invoke SetCursor, [wc_w.hCursor]
    jmp .finish
  .wm_lbuttondown:
    GetMousePos
    if_mouse_in btn_rect_button, cl_button
    jmp .mc_button
    else_mouse cl_button
    end_mouse cl_button
  .mc_button:
    jmp .finish
  .wm_destroy:
    DestroyGDI
    invoke DeleteObject, [edit_brush_textbox]
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
fps_itoa:
    push rbx rcx rdx
    mov ebx, 10
    xor ecx, ecx
    cmp eax, 0
    jne .itoa_push
    mov word [rdi], '0'
    mov word [rdi+2], 0
    pop rdx rcx rbx
    ret
  .itoa_push:
    xor edx, edx
    div ebx
    add dl, '0'
    push rdx
    inc ecx
    test eax, eax
    jnz .itoa_push
  .itoa_pop:
    pop rax
    mov [rdi], ax
    add rdi, 2
    loop .itoa_pop
    mov word [rdi], 0
    pop rdx rcx rbx
    ret

section '.idata' import data readable writeable
  library kernel32, 'KERNEL32.DLL', user32, 'USER32.DLL', gdi32, 'GDI32.DLL', dwmapi, 'DWMAPI.DLL', ole32, 'OLE32.DLL', gdiplus, 'GDIPLUS.DLL'
  include 'api/kernel32.inc'
  include 'api/user32.inc'
  include 'api/gdi32.inc'
  import dwmapi, DwmSetWindowAttribute, 'DwmSetWindowAttribute'
  import ole32, CoInitialize, 'CoInitialize', CoUninitialize, 'CoUninitialize'
  import gdiplus, GdiplusStartup, 'GdiplusStartup', GdiplusShutdown, 'GdiplusShutdown'

section '.rsrc' resource data readable
  directory RT_ICON, icons, RT_GROUP_ICON, group_icons
  resource icons, 1, LANG_NEUTRAL, icon_data
  resource group_icons, 1, LANG_NEUTRAL, main_icon
  icon main_icon, icon_data, 'C:/Users/17D3~1/Desktop/ALPHAD~1/res/main.ico'

