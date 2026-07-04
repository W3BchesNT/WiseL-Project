# Library/Windows/GuiGen64.py — Генератор ASM для GUI Windows x64
import os, sys, ctypes, re
from ctypes import wintypes

CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Core')
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

import Gui
import Hooks
import HooksGen64
import Timer as TimerParser
import TimerGen64
import CanvasGen64


def _hex_to_bgr(hex_color):
    c = hex_color.lstrip('#')
    if len(c) == 6:
        return f"0x00{c[4:6]}{c[2:4]}{c[0:2]}"
    return "0x00FFFFFF"


def _get_short_path(long_path):
    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    GetShortPathNameW.restype = wintypes.DWORD
    buf = ctypes.create_unicode_buffer(512)
    return buf.value if GetShortPathNameW(long_path, buf, 512) else long_path


def _utf16(text):
    return ", ".join([f"0x{ord(c):04X}" for c in str(text)] + ["0"])


def generate(ast):
    data_lines = [
        "WiseInit64",
        "sys_win_count dq 1",
        "  fps_counter dd 0",
        "  fps_last_tick dd 0",
        "  fps_current dd 0",
        "  fps_buf dw 16 dup(0)",
        "  fps_perf_freq dq 0",
        "  fps_perf_start dq 0",
        "  fps_perf_end dq 0",
        "  fps_target_ms dd 0",
    ]
    code_lines = []
    windows = []
    widgets = []
    events = []
    menus = []
    hook = None
    timers = []
    global_menu_id = 5000

    has_fps_label = False
    fps_label_name = ""
    fps_max = 0

    for node in ast:
        if isinstance(node, TimerParser.TimerDecl):
            timers.append(node)
            data_lines += TimerGen64.generate_data([node])

        elif isinstance(node, Hooks.HookDecl):
            hook = node

        elif isinstance(node, Gui.MenuDecl):
            menus.append(node)
            for item in node.items:
                if isinstance(item, Gui.MenuItem):
                    data_lines.append(f"  menu_text_{item.action} du {_utf16(item.label)}")
            data_lines.append(f"  menu_label_{node.name} du {_utf16(node.label)}")

        elif isinstance(node, Gui.WindowDecl):
            windows.append(node)
            bg = _hex_to_bgr(node.props.get('background', '#FFFFFF'))
            title = node.props.get('title', 'Wise Window')
            data_lines += [
                f"  _class_{node.name} du 'Class_{node.name}',0",
                f"  _title_{node.name} du {_utf16(title)}",
                f"  wc_{node.name} WNDCLASS",
                f"  hwnd_{node.name} dq 0",
                f"  win_bg_{node.name} dd {bg}",
            ]

        elif isinstance(node, Gui.WidgetDecl):
            widgets.append(node)

            if node.wtype == "fluent_btn":
                x = int(node.props.get('x', 0))
                y = int(node.props.get('y', 0))
                w = int(node.props.get('width', 100))
                h = int(node.props.get('height', 30))
                title = node.props.get('title', 'Button')
                bg = node.props.get('background', '#0078D4')
                fg = node.props.get('font_color', '#FFFFFF')
                border = node.props.get('border_color', bg)
                hover_bg = node.props.get('hover.background', bg)
                hover_fg = node.props.get('hover.font_color', fg)
                hover_border = node.props.get('hover.border_color', border)
                click_bg = node.props.get('click.background', bg)
                click_fg = node.props.get('click.font_color', fg)
                click_border = node.props.get('click.border_color', border)
                gravity = node.props.get('gravity', 'center')
                grav_flag = "37" if gravity == "center" else ("0x12" if gravity == "right" else "0x10")

                data_lines += [
                    f"  _btn_text_{node.name} dw {_utf16(title)}",
                    f"  btn_rect_{node.name} RECT {x}, {y}, {x + w}, {y + h}",
                    f"  btn_state_{node.name} dd 0",
                    f"  btn_gravity_{node.name} dd {grav_flag}",
                    f"  btn_bg_{node.name} dd {_hex_to_bgr(bg)}",
                    f"  btn_font_{node.name} dd {_hex_to_bgr(fg)}",
                    f"  btn_border_{node.name} dd {_hex_to_bgr(border)}",
                    f"  btn_bg_hover_{node.name} dd {_hex_to_bgr(hover_bg)}",
                    f"  btn_font_hover_{node.name} dd {_hex_to_bgr(hover_fg)}",
                    f"  btn_border_hover_{node.name} dd {_hex_to_bgr(hover_border)}",
                    f"  btn_bg_click_{node.name} dd {_hex_to_bgr(click_bg)}",
                    f"  btn_font_click_{node.name} dd {_hex_to_bgr(click_fg)}",
                    f"  btn_border_click_{node.name} dd {_hex_to_bgr(click_border)}",
                ]

            elif node.wtype == "fluent_label":
                x = int(node.props.get('x', 0))
                y = int(node.props.get('y', 0))
                w = int(node.props.get('width', 300))
                h = int(node.props.get('height', 30))
                title = node.props.get('title', 'Label')

                if title == '_showrenderfps':
                    has_fps_label = True
                    fps_label_name = node.name
                    data_lines.append(f"  _label_text_{node.name} dw 'F','P','S',':',' ','0',0,0,0,0,0,0,0,0,0,0")
                else:
                    data_lines.append(f"  _label_text_{node.name} dw {_utf16(title)}")

                fg = node.props.get('font_color', '#000000')
                fs = node.props.get('font_size', '14')
                gravity = node.props.get('gravity', 'left')
                grav_flag = "37" if gravity == "center" else ("0x12" if gravity == "right" else "0x10")

                data_lines += [
                    f"  label_rect_{node.name} RECT {x}, {y}, {x + w}, {y + h}",
                    f"  label_font_{node.name} dd {_hex_to_bgr(fg)}",
                    f"  label_font_size_{node.name} dd {fs}",
                    f"  label_gravity_{node.name} dd {grav_flag}",
                ]

            elif node.wtype in ("fluent_editline", "fluent_textbox"):
                x = int(node.props.get('x', 0))
                y = int(node.props.get('y', 0))
                w_str = str(node.props.get('width', '200'))
                h_str = str(node.props.get('height', '30'))
                w = 800 if w_str.endswith('%') else int(w_str)
                h = 600 if h_str.endswith('%') else int(h_str)
                title = node.props.get('title', '')
                bg = node.props.get('background', '#FFFFFF')
                fg = node.props.get('font_color', '#000000')
                fs = node.props.get('font_size', '14')
                style_val = "ES_MULTILINE or ES_AUTOVSCROLL or WS_VSCROLL" if node.wtype == "fluent_textbox" else "ES_AUTOHSCROLL"

                data_lines += [
                    f"  hEdit_{node.name} dq 0",
                    f"  edit_brush_{node.name} dq 0",
                    f"  edit_rect_{node.name} RECT {x}, {y}, {x + w}, {y + h}",
                    f"  edit_bg_{node.name} dd {_hex_to_bgr(bg)}",
                    f"  edit_font_{node.name} dd {_hex_to_bgr(fg)}",
                    f"  edit_font_size_{node.name} dd {fs}",
                ]
                if title:
                    data_lines.append(f"  _init_text_{node.name} du {_utf16(title)}")

            elif node.wtype == "fluent_canvas":
                if 'fps_max' in node.props:
                    fps_max = int(node.props['fps_max'])
                data_lines += CanvasGen64.gen_data(node)

        elif isinstance(node, Gui.EventDecl):
            events.append(node)

    if not windows:
        return "; No windows defined"

    win = windows[0]
    w_str = win.props.get('width', '400')
    h_str = win.props.get('height', '300')
    w = int(w_str) if not str(w_str).endswith('%') else 800
    h = int(h_str) if not str(h_str).endswith('%') else 600
    toolbar = win.props.get('toolbar', 'light')

    has_icon = win.props.get('icon', '') != ''
    icon_full_path = ''
    if has_icon:
        sd = os.path.dirname(os.path.abspath(__file__))
        pd = os.path.dirname(os.path.dirname(sd))
        for attempt in [
            os.path.join(pd, win.props['icon']),
            os.path.join(sd, '..', '..', win.props['icon']),
            win.props['icon']
        ]:
            if os.path.exists(attempt):
                icon_full_path = attempt
                break
        if not icon_full_path:
            icon_full_path = win.props['icon']

    has_btns = any(w.wtype == "fluent_btn" for w in widgets)
    has_edits = any(w.wtype in ("fluent_editline", "fluent_textbox") for w in widgets)
    has_menu = len(menus) > 0
    has_hook = hook is not None and len(hook.bindings) > 0
    has_timer = len(timers) > 0

    if has_menu:
        data_lines.append(f"  hMenu_{win.name} dq 0")
        for menu in menus:
            data_lines.append(f"  hSubMenu_{win.name}_{menu.name} dq 0")

    code_lines += [
        "start:",
        "    sub rsp, 8", "    and rsp, -16", "    sub rsp, 32",
        "    xor ecx, ecx", "    call [CoInitialize]",
        "    lea rcx, [gdiplusToken]", "    lea rdx, [gdiplusInput]",
        "    xor r8, r8", "    call [GdiplusStartup]",
    ]

    if fps_max > 0:
        code_lines += [
            f"    invoke QueryPerformanceFrequency, fps_perf_freq",
            f"    mov dword [fps_target_ms], {1000 // fps_max}",
        ]

    code_lines += [
        f"    mov [wc_{win.name}.style], CS_HREDRAW or CS_VREDRAW",
        f"    mov [wc_{win.name}.lpfnWndProc], WindowProc_{win.name}",
        f"    invoke GetModuleHandle, 0", f"    mov [wc_{win.name}.hInstance], rax",
    ]

    if has_icon:
        code_lines += [
            f"    invoke LoadIcon, [wc_{win.name}.hInstance], 1",
            f"    mov [wc_{win.name}.hIcon], rax",
        ]
    else:
        code_lines += [
            f"    invoke LoadIcon, 0, IDI_APPLICATION",
            f"    mov [wc_{win.name}.hIcon], rax",
        ]

    code_lines += [
        f"    invoke LoadCursor, 0, IDC_ARROW", f"    mov [wc_{win.name}.hCursor], rax",
        f"    invoke CreateSolidBrush, [win_bg_{win.name}]", f"    mov [wc_{win.name}.hbrBackground], rax",
        f"    mov [wc_{win.name}.lpszClassName], _class_{win.name}",
        f"    lea rcx, [wc_{win.name}]", f"    invoke RegisterClass, rcx",
        f"    test eax, eax", f"    jz exit_app",
        f"    invoke CreateWindowExW, 0, _class_{win.name}, _title_{win.name}, WS_OVERLAPPEDWINDOW or WS_VISIBLE or WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT, {w}, {h}, 0, 0, [wc_{win.name}.hInstance], 0",
        f"    test rax, rax", f"    jz exit_app",
        f"    mov [hwnd_{win.name}], rax", f"    mov [win_width], {w}", f"    mov [win_height], {h}",
    ]

    if fps_max > 0:
        code_lines += [
            f"  .game_loop:",
            f"    invoke QueryPerformanceCounter, fps_perf_start",
            f"    invoke InvalidateRect, [hwnd_{win.name}], 0, 0",
            f"    lea rcx, [msg]",
            f"    invoke PeekMessage, rcx, 0, 0, 0, 1",
            f"    test eax, eax",
            f"    jz .do_sleep",
            f"    cmp [msg.message], 18",
            f"    je exit_app",
            f"    lea rcx, [msg]",
            f"    invoke TranslateMessage, rcx",
            f"    lea rcx, [msg]",
            f"    invoke DispatchMessage, rcx",
            f"  .do_sleep:",
            f"    invoke QueryPerformanceCounter, fps_perf_end",
            f"    mov rax, [fps_perf_end]",
            f"    sub rax, [fps_perf_start]",
            f"    imul rax, 1000",
            f"    xor edx, edx",
            f"    div qword [fps_perf_freq]",
            f"    mov ecx, [fps_target_ms]",
            f"    sub ecx, eax",
            f"    cmp ecx, 0",
            f"    jle .game_loop",
            f"    invoke Sleep, ecx",
            f"    jmp .game_loop",
            f"  exit_app:",
        ]
    else:
        code_lines += [
            f"  .game_loop:",
            f"    invoke InvalidateRect, [hwnd_{win.name}], 0, 0",
            f"    lea rcx, [msg]",
            f"    invoke PeekMessage, rcx, 0, 0, 0, 1",
            f"    test eax, eax",
            f"    jz .game_loop",
            f"    cmp [msg.message], 18",
            f"    je exit_app",
            f"    lea rcx, [msg]",
            f"    invoke TranslateMessage, rcx",
            f"    lea rcx, [msg]",
            f"    invoke DispatchMessage, rcx",
            f"    jmp .game_loop",
            f"  exit_app:",
        ]

    code_lines += [
        f"    invoke CoUninitialize",
        f"    mov rcx, [msg.wParam]",
        f"    invoke ExitProcess, rcx",
    ]

    code_lines += [f"proc WindowProc_{win.name} hwnd, wmsg, wparam, lparam"]

    disp_lines = [
        f"    push rbx rsi rdi r14 r12 r13",
        f"    mov rbx, rcx", f"    mov rsi, rdx", f"    mov rdi, r8", f"    mov r14, r9",
        f"    cmp edx, 1", f"    je .wm_create",
        f"    cmp edx, 5", f"    je .wm_size",
        f"    cmp edx, 15", f"    je .wm_paint",
    ]

    if has_edits:
        disp_lines += [f"    cmp edx, WM_CTLCOLOREDIT", f"    je .wm_ctlcoloredit"]
    if has_btns:
        disp_lines += [
            f"    cmp edx, 512", f"    je .wm_mousemove",
            f"    cmp edx, 513", f"    je .wm_lbuttondown",
        ]
    if has_menu:
        disp_lines += [f"    cmp edx, 273", f"    je .wm_command"]
    if has_hook:
        disp_lines += HooksGen64.generate_dispatch_check()

    disp_lines += [
        f"    cmp edx, WM_DESTROY", f"    je .wm_destroy",
        f"    pop r13 r12 r14 rdi rsi rbx",
        f"    invoke DefWindowProc, rcx, rdx, r8, r9",
        f"    ret",
    ]
    code_lines += disp_lines

    # WM_CREATE
    code_lines.append(f"  .wm_create:")
    if toolbar == "dark":
        code_lines += [
            f"    mov dword [dark_mode_true], 1",
            f"    lea r8, [dark_mode_true]",
            f"    invoke DwmSetWindowAttribute, rbx, 20, r8, 4",
        ]
    code_lines += [
        f"    invoke CreateFont, 16, 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name",
        f"    mov [hFont], rax",
    ]

    if has_menu:
        code_lines += [
            f"    invoke CreateMenu",
            f"    mov [hMenu_{win.name}], rax",
        ]
        for menu in menus:
            code_lines += [
                f"    invoke CreatePopupMenu",
                f"    mov [hSubMenu_{win.name}_{menu.name}], rax",
                f"    mov r15, rax",
            ]
            for item in menu.items:
                if item == "separator":
                    code_lines.append(f"    invoke AppendMenuW, r15, 2048, 0, 0")
                elif isinstance(item, Gui.MenuItem):
                    code_lines.append(f"    invoke AppendMenuW, r15, 0, {global_menu_id}, menu_text_{item.action}")
                    global_menu_id += 1
            code_lines.append(f"    invoke AppendMenuW, [hMenu_{win.name}], 16, r15, menu_label_{menu.name}")
        code_lines.append(f"    invoke SetMenu, rbx, [hMenu_{win.name}]")

    eid = 2000
    for wgt in widgets:
        if wgt.wtype in ("fluent_editline", "fluent_textbox"):
            name = wgt.name
            x = int(wgt.props.get('x', 0))
            y = int(wgt.props.get('y', 0))
            ww_str = str(wgt.props.get('width', '200'))
            wh_str = str(wgt.props.get('height', '30'))
            ww = 800 if str(ww_str).endswith('%') else int(ww_str)
            wh = 600 if str(wh_str).endswith('%') else int(wh_str)
            style_val = "ES_MULTILINE or ES_AUTOVSCROLL or WS_VSCROLL" if wgt.wtype == "fluent_textbox" else "ES_AUTOHSCROLL"

            code_lines += [
                f"    invoke CreateSolidBrush, [edit_bg_{name}]",
                f"    mov [edit_brush_{name}], rax",
                f"    invoke CreateWindowExW, 0, edit_class, 0, WS_CHILD or WS_VISIBLE or {style_val}, {x}, {y}, {ww}, {wh}, rbx, {eid}, [wc_{win.name}.hInstance], 0",
                f"    mov [hEdit_{name}], rax",
                f"    invoke SendMessageW, rax, WM_SETFONT, [hFont], 1",
            ]
            if wgt.props.get('title', ''):
                code_lines.append(f"    invoke SetWindowTextW, [hEdit_{name}], _init_text_{name}")
            eid += 1

    code_lines += [
        f"    InitBuffer [win_bg_{win.name}]",
        f"    invoke InvalidateRect, rbx, 0, 1",
        f"    xor eax, eax",
        f"    jmp .finish",
    ]

    # WM_COMMAND
    if has_menu:
        code_lines.append(f"  .wm_command:")
        menu_id = 5000
        for menu in menus:
            for item in menu.items:
                if isinstance(item, Gui.MenuItem):
                    code_lines += [
                        f"    cmp r8d, {menu_id}",
                        f"    jne .skip_menu_{menu_id}",
                    ]
                    for evt in events:
                        if evt.widget == item.action and evt.event == "onClick":
                            if '__asm__' in evt.actions:
                                for asm_line in evt.actions['__asm__']:
                                    code_lines.append(f"    {asm_line.strip()}")
                    code_lines += [
                        f"    invoke InvalidateRect, rbx, 0, 1",
                        f"    jmp .finish",
                        f"  .skip_menu_{menu_id}:",
                    ]
                    menu_id += 1
        code_lines.append(f"    jmp .finish")

    # WM_CTLCOLOREDIT
    if has_edits:
        code_lines.append(f"  .wm_ctlcoloredit:")
        for wgt in widgets:
            if wgt.wtype in ("fluent_editline", "fluent_textbox"):
                name = wgt.name
                code_lines += [
                    f"    cmp r14, [hEdit_{name}]",
                    f"    jne .ne_{name}",
                    f"    invoke SetTextColor, rdi, [edit_font_{name}]",
                    f"    invoke SetBkColor, rdi, [edit_bg_{name}]",
                    f"    mov rax, [edit_brush_{name}]",
                    f"    jmp .finish",
                    f"  .ne_{name}:",
                ]
        code_lines += [
            f"    pop r13 r12 r14 rdi rsi rbx",
            f"    invoke DefWindowProc, rcx, rdx, r8, r9",
            f"    ret",
        ]

    # WM_SIZE
    code_lines += [f"  .wm_size:", f"    size_handler"]
    for wgt in widgets:
        if wgt.wtype in ("fluent_textbox", "fluent_editline"):
            name = wgt.name
            wp = str(wgt.props.get('width', '100%'))
            hp = str(wgt.props.get('height', '100%'))
            if wp.endswith('%'):
                pct = int(wp[:-1])
                code_lines += [
                    f"    mov eax, [win_width]",
                    f"    imul eax, {pct}",
                    f"    mov ecx, 100",
                    f"    xor edx, edx",
                    f"    div ecx",
                    f"    mov [edit_rect_{name}.right], eax",
                ]
            if hp.endswith('%'):
                pct = int(hp[:-1])
                code_lines += [
                    f"    mov eax, [win_height]",
                    f"    imul eax, {pct}",
                    f"    mov ecx, 100",
                    f"    xor edx, edx",
                    f"    div ecx",
                    f"    mov [edit_rect_{name}.bottom], eax",
                ]
            if wp.endswith('%') or hp.endswith('%'):
                code_lines += [
                    f"    invoke SetWindowPos, [hEdit_{name}], 0, 0, 0, [edit_rect_{name}.right], [edit_rect_{name}.bottom], 0x4",
                ]
        elif wgt.wtype == "fluent_canvas":
            code_lines += CanvasGen64.gen_resize(wgt)
    code_lines.append(f"    jmp .finish")

    # WM_KEYDOWN
    if has_hook:
        code_lines += HooksGen64.generate_keydown_handler(hook)

    # WM_PAINT
    code_lines.append(f"  .wm_paint:")

    code_lines += [
        f"    inc dword [fps_counter]",
        f"    invoke GetTickCount",
        f"    mov ecx, eax",
        f"    sub ecx, [fps_last_tick]",
        f"    cmp ecx, 1000",
        f"    jl .fps_skip",
        f"    mov [fps_last_tick], eax",
        f"    mov eax, [fps_counter]",
        f"    mov [fps_current], eax",
        f"    mov dword [fps_counter], 0",
        f"    mov eax, [fps_current]",
        f"    lea rdi, [fps_buf]",
        f"    call fps_itoa",
    ]

    if has_fps_label:
        code_lines += [
            f"    lea rsi, [fps_buf]",
            f"    lea rdi, [_label_text_{fps_label_name} + 10]",
            f"    mov ecx, 5",
            f"  .fps_clr:",
            f"    mov word [rdi], ' '",
            f"    add rdi, 2",
            f"    loop .fps_clr",
            f"    lea rsi, [fps_buf]",
            f"    lea rdi, [_label_text_{fps_label_name} + 10]",
            f"  .fps_cpy:",
            f"    mov ax, [rsi]",
            f"    test ax, ax",
            f"    jz .fps_end",
            f"    mov [rdi], ax",
            f"    add rsi, 2",
            f"    add rdi, 2",
            f"    jmp .fps_cpy",
            f"  .fps_end:",
        ]

    code_lines.append(f"  .fps_skip:")

    if has_timer:
        code_lines += TimerGen64.generate_timer_handler(timers)

    code_lines.append(f"    PaintBegin [win_bg_{win.name}]")

    for wgt in widgets:
        if wgt.wtype == "fluent_btn":
            name = wgt.name
            code_lines += [
                f"    cmp [btn_state_{name}], 2",
                f"    jne .nc_{name}",
                f"    WiseFillRect [mem_dc], btn_rect_{name}, [btn_bg_click_{name}]",
                f"    WiseDrawText [mem_dc], _btn_text_{name}, btn_rect_{name}, [btn_gravity_{name}], [btn_font_click_{name}]",
                f"    invoke CreateSolidBrush, [btn_border_click_{name}]",
                f"    mov r15, rax",
                f"    lea rdx, [btn_rect_{name}]",
                f"    invoke FrameRect, [mem_dc], rdx, r15",
                f"    invoke DeleteObject, r15",
                f"    jmp .fd_{name}",
                f"  .nc_{name}:",
                f"    cmp [btn_state_{name}], 1",
                f"    jne .nh_{name}",
                f"    WiseFillRect [mem_dc], btn_rect_{name}, [btn_bg_hover_{name}]",
                f"    WiseDrawText [mem_dc], _btn_text_{name}, btn_rect_{name}, [btn_gravity_{name}], [btn_font_hover_{name}]",
                f"    invoke CreateSolidBrush, [btn_border_hover_{name}]",
                f"    mov r15, rax",
                f"    lea rdx, [btn_rect_{name}]",
                f"    invoke FrameRect, [mem_dc], rdx, r15",
                f"    invoke DeleteObject, r15",
                f"    jmp .fd_{name}",
                f"  .nh_{name}:",
                f"    WiseFillRect [mem_dc], btn_rect_{name}, [btn_bg_{name}]",
                f"    WiseDrawText [mem_dc], _btn_text_{name}, btn_rect_{name}, [btn_gravity_{name}], [btn_font_{name}]",
                f"    invoke CreateSolidBrush, [btn_border_{name}]",
                f"    mov r15, rax",
                f"    lea rdx, [btn_rect_{name}]",
                f"    invoke FrameRect, [mem_dc], rdx, r15",
                f"    invoke DeleteObject, r15",
                f"  .fd_{name}:",
            ]

        elif wgt.wtype == "fluent_label":
            name = wgt.name
            code_lines += [
                f"    invoke CreateFontW, [label_font_size_{name}], 0, 0, 0, 400, 0, 0, 0, 204, 0, 0, 5, 0, sys_font_name",
                f"    mov r14, rax",
                f"    invoke SelectObject, [mem_dc], r14",
                f"    WiseDrawText [mem_dc], _label_text_{name}, label_rect_{name}, [label_gravity_{name}], [label_font_{name}]",
                f"    invoke SelectObject, [mem_dc], [hFont]",
                f"    invoke DeleteObject, r14",
            ]

        elif wgt.wtype == "fluent_canvas":
            code_lines += CanvasGen64.gen_paint(wgt)

    code_lines.append(f"    PaintEnd")

    # WM_MOUSEMOVE
    if has_btns:
        code_lines += [f"  .wm_mousemove:", f"    GetMousePos"]
        for wgt in widgets:
            if wgt.wtype == "fluent_btn":
                name = wgt.name
                code_lines += [
                    f"    if_mouse_in btn_rect_{name}, {name}",
                    f"    cmp [btn_state_{name}], 1",
                    f"    je .nr_{name}",
                    f"    mov [btn_state_{name}], 1",
                    f"    invoke InvalidateRect, rbx, 0, 0",
                    f"    jmp .md_{name}",
                    f"    else_mouse {name}",
                    f"    cmp [btn_state_{name}], 0",
                    f"    je .nr_{name}",
                    f"    mov [btn_state_{name}], 0",
                    f"    invoke InvalidateRect, rbx, 0, 0",
                    f"    end_mouse {name}",
                    f"  .nr_{name}:",
                ]
        code_lines += [
            f"    invoke SetCursor, [wc_{win.name}.hCursor]",
            f"    jmp .finish",
        ]

    # WM_LBUTTONDOWN
    if has_btns:
        code_lines += [f"  .wm_lbuttondown:", f"    GetMousePos"]
        for wgt in widgets:
            if wgt.wtype == "fluent_btn":
                name = wgt.name
                has_evt = any(e.widget == name and e.event == "onClick" for e in events)
                code_lines += [f"    if_mouse_in btn_rect_{name}, cl_{name}"]
                if has_evt:
                    code_lines.append(f"    mov [btn_state_{name}], 2")
                    for evt in events:
                        if evt.widget == name and evt.event == "onClick":
                            if '__asm__' in evt.actions:
                                for asm_line in evt.actions['__asm__']:
                                    code_lines.append(f"    {asm_line.strip()}")
                    code_lines.append(f"    invoke InvalidateRect, rbx, 0, 1")
                code_lines += [
                    f"    jmp .mc_{name}",
                    f"    else_mouse cl_{name}",
                    f"    end_mouse cl_{name}",
                    f"  .mc_{name}:",
                ]
        code_lines.append(f"    jmp .finish")

    # WM_DESTROY
    code_lines += [
        f"  .wm_destroy:",
        f"    DestroyGDI",
    ]
    for wgt in widgets:
        if wgt.wtype in ("fluent_editline", "fluent_textbox"):
            code_lines.append(f"    invoke DeleteObject, [edit_brush_{wgt.name}]")
    code_lines += [
        f"    dec qword [sys_win_count]",
        f"    cmp qword [sys_win_count], 0",
        f"    jne .skip_quit",
        f"    invoke PostQuitMessage, 0",
        f"  .skip_quit:",
        f"    xor eax, eax",
        f"  .finish:",
        f"    pop r13 r12 r14 rdi rsi rbx",
        f"    ret",
        f"endp",
    ]

    code_lines += [
        "fps_itoa:",
        "    push rbx rcx rdx",
        "    mov ebx, 10",
        "    xor ecx, ecx",
        "    cmp eax, 0",
        "    jne .itoa_push",
        "    mov word [rdi], '0'",
        "    mov word [rdi+2], 0",
        "    pop rdx rcx rbx",
        "    ret",
        "  .itoa_push:",
        "    xor edx, edx",
        "    div ebx",
        "    add dl, '0'",
        "    push rdx",
        "    inc ecx",
        "    test eax, eax",
        "    jnz .itoa_push",
        "  .itoa_pop:",
        "    pop rax",
        "    mov [rdi], ax",
        "    add rdi, 2",
        "    loop .itoa_pop",
        "    mov word [rdi], 0",
        "    pop rdx rcx rbx",
        "    ret",
    ]

    icon_section = ""
    if has_icon:
        sp = _get_short_path(icon_full_path).replace('\\', '/') if os.path.exists(icon_full_path) else icon_full_path.replace('\\', '/')
        icon_section = f"""
section '.rsrc' resource data readable
  directory RT_ICON, icons, RT_GROUP_ICON, group_icons
  resource icons, 1, LANG_NEUTRAL, icon_data
  resource group_icons, 1, LANG_NEUTRAL, main_icon
  icon main_icon, icon_data, '{sp}'
"""

    return f"""format PE64 GUI 5.0
entry start
include 'win64w.inc'
include 'Compiler/Macros/WinX64/win64.inc'
include 'Compiler/Macros/WinX64/vector.inc'
include 'Compiler/Macros/WinX64/hooks.inc'

section '.data' data readable writeable
{chr(10).join(data_lines)}

section '.code' code readable executable
{chr(10).join(code_lines)}

section '.idata' import data readable writeable
  library kernel32, 'KERNEL32.DLL', user32, 'USER32.DLL', gdi32, 'GDI32.DLL', dwmapi, 'DWMAPI.DLL', ole32, 'OLE32.DLL', gdiplus, 'GDIPLUS.DLL'
  include 'api/kernel32.inc'
  include 'api/user32.inc'
  include 'api/gdi32.inc'
  import dwmapi, DwmSetWindowAttribute, 'DwmSetWindowAttribute'
  import ole32, CoInitialize, 'CoInitialize', CoUninitialize, 'CoUninitialize'
  import gdiplus, GdiplusStartup, 'GdiplusStartup', GdiplusShutdown, 'GdiplusShutdown'
{icon_section}
"""