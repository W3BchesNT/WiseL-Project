; ============================================================
; hooks.inc — WiseL Animation & Input System
; ============================================================

; ─── VK коды клавиш ─────────────────────
VK_LEFT   = 25h
VK_UP     = 26h
VK_RIGHT  = 27h
VK_DOWN   = 28h
VK_W      = 57h
VK_A      = 41h
VK_S      = 53h
VK_D      = 44h
VK_SPACE  = 20h

; ─── Данные хуков ───────────────────────
macro HookData {
    keys            db 256 dup(0)
    last_tick       dq 0
    delta_time      dq 0
    hook_timer_id   dq 1
}

; ─── Инициализация ──────────────────────
macro HookInit {
    invoke GetTickCount
    mov [last_tick], rax
    invoke SetTimer, rbx, [hook_timer_id], 16, 0
}

; ─── Обработка клавиш ───────────────────
macro HookProcessKeys {
    test r9d, 40000000h
    jnz .key_up
    movzx eax, r8w
    mov byte [keys + eax], 1
    jmp .key_done
  .key_up:
    movzx eax, r8w
    mov byte [keys + eax], 0
  .key_done:
}

; ─── Проверка клавиши ───────────────────
macro HookIsKeyDown key {
    cmp byte [keys + key], 1
}

; ─── Таймер для Update ──────────────────
macro HookOnTimer {
    invoke GetTickCount
    mov r15, rax
    sub r15, [last_tick]
    mov [delta_time], r15
    mov [last_tick], rax
}