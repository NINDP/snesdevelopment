; OAM shadow writes. All arguments occupy a 16-bit stack slot (816-tcc ABI).
.include "hdr.asm"
.accu 16
.index 16
.16bit
.section "perspective_oam" superfree
perspective_obj:
    lda 4,s
    asl a
    asl a
    tax
    sep #$20
    lda 6,s
    sta.l oamMemory,x
    lda 8,s
    sta.l oamMemory+1,x
    lda 10,s
    sta.l oamMemory+2,x
    lda 11,s
    ora #$20
    sta.l oamMemory+3,x
    rep #$20
    lda 4,s
    and #3
    tax
    sep #$20
    lda.l perspective_oam_clearbits,x
    sta.b tcc__r0
    lda #0
    sta.b tcc__r1
    lda 12,s
    beq +
    lda.l perspective_oam_sizes,x
    sta.b tcc__r1
+:
    lda 7,s
    and #1
    beq +
    lda.l perspective_oam_ninth,x
    ora.b tcc__r1
    sta.b tcc__r1
+:
    rep #$20
    lda 4,s
    lsr a
    lsr a
    tax
    sep #$20
    lda.l oamMemory+512,x
    and.b tcc__r0
    ora.b tcc__r1
    sta.l oamMemory+512,x
    rep #$20
    rtl
perspective_clear:
    ldx #0
    sep #$20
    lda #240
-:
    sta.l oamMemory+1,x
    inx
    inx
    inx
    inx
    cpx #240
    bne -
    rep #$20
    rtl
perspective_oam_clearbits: .db $fc,$f3,$cf,$3f
perspective_oam_sizes: .db 2,8,32,128
perspective_oam_ninth: .db 1,4,16,64
.ends

; Same projection as the host C implementation, using the CPU's 8x8 multiplier.
; The Mode 7 matrix registers remain exclusively owned by HDMA.
.section "perspective_project" superfree
perspective_project:
    lda 4,s
    sta.b tcc__r1
    lda 6,s
    sta.b tcc__r1h
    ldy #36
    lda [tcc__r1],y
    sta.b tcc__r2
    lda 10,s
    sec
    sbc.b tcc__r2
    clc
    adc #192
    cmp #231
    bcc +
    brl perspective_project_hidden
+:
    tax
    sep #$20
    lda.l perspective_size,x
    sta.b tcc__r4
    lda.l perspective_y,x
    rep #$20
    and #$ff
    sta.b tcc__r2
    lda 16,s
    sta.b tcc__r1
    lda 18,s
    sta.b tcc__r1h
    lda.b tcc__r2
    sta [tcc__r1]
    lda 4,s
    sta.b tcc__r1
    lda 6,s
    sta.b tcc__r1h
    ldy #34
    lda [tcc__r1],y
    sta.b tcc__r2
    lda 8,s
    sec
    sbc.b tcc__r2
    sta.b tcc__r3
    clc
    adc #255
    cmp #511
    bcc +
    brl perspective_project_hidden
+:
    lda.b tcc__r3
    bpl +
    eor #$ffff
    inc a
+:
    sep #$20
    sta.l $004202
    lda.b tcc__r4
    sta.l $004203
    rep #$20
    ; Set the result pointer while the hardware multiply finishes (8 cycles).
    lda 12,s
    sta.b tcc__r1
    lda 14,s
    sta.b tcc__r1h
    lda.l $004216
    ldx.b tcc__r3
    bpl +
    eor #$ffff
    inc a
+:
    .rept 6
    cmp #$8000
    ror a
    .endr
    clc
    adc #128
    sta [tcc__r1]
    clc
    adc #32
    cmp #320
    bcs perspective_project_hidden
    lda #1
    sta.b tcc__r0
    rtl
perspective_project_hidden:
    lda #0
    sta.b tcc__r0
    rtl
.ends

; World-space illumination shares the portable core's four-row circle lookup.
; It is used by enemies, memory traces, rune charges and interaction selection.
.section "torch_visibility" superfree
light_sees:
    lda 8,s
    cmp #256
    bcs torch_hidden
    lda 10,s
    cmp #24
    bcc torch_hidden
    cmp #192
    bcs torch_hidden
    lda 4,s
    sta.b tcc__r1
    lda 6,s
    sta.b tcc__r1h
    sep #$20
    ldy #6
    lda [tcc__r1],y
    beq torch_hidden_byte
    ldy #8
    lda [tcc__r1],y
    beq torch_hidden_byte
    rep #$20
    ldy #36
    lda [tcc__r1],y
    sta.b tcc__r2
    lda 10,s
    and #$fffc
    clc
    adc #10
    sec
    sbc.b tcc__r2
    bpl +
    eor #$ffff
    inc a
+:
    cmp #65
    bcs torch_hidden
    tax
    sep #$20
    lda.l torch_width,x
    rep #$20
    and #$ff
    sta.b tcc__r2
    ldy #34
    lda [tcc__r1],y
    sta.b tcc__r3
    lda 8,s
    sec
    sbc.b tcc__r3
    bpl +
    eor #$ffff
    inc a
+:
    cmp.b tcc__r2
    beq torch_visible
    bcc torch_visible
    bra torch_hidden
torch_visible:
    lda #1
    sta.b tcc__r0
    rtl
torch_hidden_byte:
    rep #$20
torch_hidden:
    lda #0
    sta.b tcc__r0
    rtl
.ends
