; ============================================================
; vector.inc — WiseL Graphics Primitives (Fixed)
; ============================================================

; ─── Заливка прямоугольника ─────────────
macro WiseFillRect dc, rect, color {
    invoke CreateSolidBrush, color
    mov r13, rax
    lea rdx, [rect]
    invoke FillRect, dc, rdx, r13
    invoke DeleteObject, r13
}

; ─── Обводка прямоугольника ─────────────
macro WiseFrameRect dc, rect, color, width {
    invoke CreateSolidBrush, color
    mov r15, rax
    mov eax, [rect + 0]
    mov [border_rect.left], eax
    mov eax, [rect + 4]
    mov [border_rect.top], eax
    mov eax, [rect + 8]
    mov [border_rect.right], eax
    mov eax, [rect + 12]
    mov [border_rect.bottom], eax
    mov ecx, width
  .loop_#rect:
    push rcx
    lea rdx, [border_rect]
    invoke FrameRect, dc, rdx, r15
    inc [border_rect.left]
    inc [border_rect.top]
    dec [border_rect.right]
    dec [border_rect.bottom]
    pop rcx
    loop .loop_#rect
    invoke DeleteObject, r15
}

; ─── Текст ──────────────────────────────
macro WiseDrawText dc, text, rect, gravity, color {
    invoke SetTextColor, dc, color
    invoke SetBkMode, dc, 1
    mov eax, [rect + 0]
    mov [border_rect.left], eax
    mov eax, [rect + 4]
    mov [border_rect.top], eax
    mov eax, [rect + 8]
    mov [border_rect.right], eax
    mov eax, [rect + 12]
    mov [border_rect.bottom], eax
    lea r8, [text]
    lea r9, [border_rect]
    invoke DrawText, dc, r8, -1, r9, gravity
}

; ─── Эллипс (заливка) ───────────────────
macro WiseFillEllipse dc, x, y, w, h, color {
    invoke CreateSolidBrush, color
    mov r13, rax
    invoke SelectObject, dc, r13
    mov r15, rax
    invoke Ellipse, dc, x, y, x + w, y + h
    invoke SelectObject, dc, r15
    invoke DeleteObject, r13
}

; ─── Линия ──────────────────────────────
macro WiseDrawLine dc, x1, y1, x2, y2, color, width {
    invoke CreatePen, 0, width, color
    mov r14, rax
    invoke SelectObject, dc, r14
    mov r15, rax
    invoke MoveToEx, dc, x1, y1, 0
    invoke LineTo, dc, x2, y2
    invoke SelectObject, dc, r15
    invoke DeleteObject, r14
}

; ─── Скруглённый прямоугольник ──────────
macro WiseFillRoundRect dc, rect, radius, color {
    invoke CreateSolidBrush, color
    mov r13, rax
    invoke SelectObject, dc, r13
    mov r15, rax
    invoke RoundRect, dc, [rect + 0], [rect + 4], [rect + 8], [rect + 12], radius, radius
    invoke SelectObject, dc, r15
    invoke DeleteObject, r13
}

; ─── Установка RECT из переменных ───────
macro WiseSetRect _rect, x, y, w, h {
    mov eax, x
    mov [_rect + 0], eax
    mov eax, y
    mov [_rect + 4], eax
    mov eax, x
    add eax, w
    mov [_rect + 8], eax
    mov eax, y
    add eax, h
    mov [_rect + 12], eax
}

; ─── Ресайз RECT по процентам ───────────
macro WiseResizeRectPct _rect, pct_x, pct_y, pct_w, pct_h, base_w, base_h {
    if pct_x >= 0
        mov eax, base_w
        imul eax, pct_x
        mov ecx, 100
        xor edx, edx
        div ecx
        mov [_rect + 0], eax
    end if
    if pct_y >= 0
        mov eax, base_h
        imul eax, pct_y
        mov ecx, 100
        xor edx, edx
        div ecx
        mov [_rect + 4], eax
    end if
    if pct_w >= 0
        mov eax, base_w
        imul eax, pct_w
        mov ecx, 100
        xor edx, edx
        div ecx
        mov r11d, eax
        mov eax, [_rect + 0]
        add eax, r11d
        mov [_rect + 8], eax
    end if
    if pct_h >= 0
        mov eax, base_h
        imul eax, pct_h
        mov ecx, 100
        xor edx, edx
        div ecx
        mov r11d, eax
        mov eax, [_rect + 4]
        add eax, r11d
        mov [_rect + 12], eax
    end if
}

; ─── Копирование RECT ───────────────────
macro WiseCopyRect src, dst {
    mov eax, [src + 0]
    mov [dst + 0], eax
    mov eax, [src + 4]
    mov [dst + 4], eax
    mov eax, [src + 8]
    mov [dst + 8], eax
    mov eax, [src + 12]
    mov [dst + 12], eax
}