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
    ora #$28 ; Priority 2, palette 4: the torch's outer falloff also shades OBJ.
    sta.l oamMemory+3,x
    ; Scenery slots are written exactly once after perspective_clear, which
    ; resets all high bits. Most are positive-X 16px cells and need no flags.
    ; Independent combat slots can also skip the full path while their whole
    ; high-table byte is zero. A previous negative X takes the normal path,
    ; clearing its ninth bit when the sprite moves back onto the screen.
    lda 12,s
    bne perspective_obj_flags
    lda 7,s
    bne perspective_obj_flags
    rep #$20
    lda 4,s
    cmp #50
    bcc perspective_obj_done
    lsr a
    lsr a
    tax
    sep #$20
    lda.l oamMemory+512,x
    bne perspective_obj_flags
perspective_obj_done:
    rep #$20
    rtl
perspective_obj_flags:
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
-:
    lda #240
    sta.l oamMemory+1,x
    sta.l oamMemory+5,x
    sta.l oamMemory+9,x
    sta.l oamMemory+13,x
    sta.l oamMemory+17,x
    sta.l oamMemory+21,x
    sta.l oamMemory+25,x
    sta.l oamMemory+29,x
    rep #$20
    txa
    clc
    adc #32
    tax
    sep #$20
    cpx #288
    bne -
    rep #$20
    ; Slots0..71 use eighteen high-table bytes. Reset both size and ninth-X
    ; bits once per scene rebuild, instead of masking every small billboard.
    lda #0
    sta.l oamMemory+512
    sta.l oamMemory+514
    sta.l oamMemory+516
    sta.l oamMemory+518
    sta.l oamMemory+520
    sta.l oamMemory+522
    sta.l oamMemory+524
    sta.l oamMemory+526
    sta.l oamMemory+528
    rtl
 ; Fixed 32x48 hero: six 16x16 OBJ cells, palette 5, priority 2.
; One call writes twelve pairs rather than invoking the generic writer six
; times. All X positions are positive; clear only these six size/ninth bits.
hero_draw:
    lda 4,s
    asl a
    asl a
    tax
    lda.l hero_oam_template+0
    sta.l oamMemory+0,x
    lda.l hero_oam_template+2
    sta.l oamMemory+2,x
    lda.l hero_oam_template+4
    sta.l oamMemory+4,x
    lda.l hero_oam_template+6
    sta.l oamMemory+6,x
    lda.l hero_oam_template+8
    sta.l oamMemory+8,x
    lda.l hero_oam_template+10
    sta.l oamMemory+10,x
    lda.l hero_oam_template+12
    sta.l oamMemory+12,x
    lda.l hero_oam_template+14
    sta.l oamMemory+14,x
    lda.l hero_oam_template+16
    sta.l oamMemory+16,x
    lda.l hero_oam_template+18
    sta.l oamMemory+18,x
    lda.l hero_oam_template+20
    sta.l oamMemory+20,x
    lda.l hero_oam_template+22
    sta.l oamMemory+22,x
    lda 4,s
    and #3
    tax
    sep #$20
    lda.l hero_high_first,x
    sta.b tcc__r0
    lda.l hero_high_second,x
    sta.b tcc__r0h
    lda.l hero_high_third,x
    sta.b tcc__r1
    rep #$20
    lda 4,s
    lsr a
    lsr a
    tax
    sep #$20
    lda.l oamMemory+512,x
    and.b tcc__r0
    sta.l oamMemory+512,x
    lda.l oamMemory+513,x
    and.b tcc__r0h
    sta.l oamMemory+513,x
    lda.l oamMemory+514,x
    and.b tcc__r1
    sta.l oamMemory+514,x
    rep #$20
    rtl
; Slots52..59: halo32, two torch cells and five independently aged embers.
; X indexes a bank-contained4096B ROM table; all destination addresses fixed.
torch_oam_draw:
    lda 4,s
    tax
    lda.l torch_oam_frames+0,x
    sta.l oamMemory+208
    lda.l torch_oam_frames+2,x
    sta.l oamMemory+210
    lda.l torch_oam_frames+4,x
    sta.l oamMemory+212
    lda.l torch_oam_frames+6,x
    sta.l oamMemory+214
    lda.l torch_oam_frames+8,x
    sta.l oamMemory+216
    lda.l torch_oam_frames+10,x
    sta.l oamMemory+218
    lda.l torch_oam_frames+12,x
    sta.l oamMemory+220
    lda.l torch_oam_frames+14,x
    sta.l oamMemory+222
    lda.l torch_oam_frames+16,x
    sta.l oamMemory+224
    lda.l torch_oam_frames+18,x
    sta.l oamMemory+226
    lda.l torch_oam_frames+20,x
    sta.l oamMemory+228
    lda.l torch_oam_frames+22,x
    sta.l oamMemory+230
    lda.l torch_oam_frames+24,x
    sta.l oamMemory+232
    lda.l torch_oam_frames+26,x
    sta.l oamMemory+234
    lda.l torch_oam_frames+28,x
    sta.l oamMemory+236
    lda.l torch_oam_frames+30,x
    sta.l oamMemory+238
    sep #$20
    lda #2
    sta.l oamMemory+525
    lda #0
    sta.l oamMemory+526
    rep #$20
    rtl
torch_oam_hide:
    sep #$20
    lda #240
    sta.l oamMemory+209
    sta.l oamMemory+213
    sta.l oamMemory+217
    sta.l oamMemory+221
    sta.l oamMemory+225
    sta.l oamMemory+229
    sta.l oamMemory+233
    sta.l oamMemory+237
    rep #$20
    rtl
hero_oam_template:
    .db 112,116,0,$2a,128,116,2,$2a
    .db 112,132,4,$2a,128,132,6,$2a
    .db 112,148,8,$2a,128,148,10,$2a
hero_high_first: .db $00,$03,$0f,$3f
hero_high_second: .db $f0,$c0,$00,$00
hero_high_third: .db $ff,$ff,$ff,$fc
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
