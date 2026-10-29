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
    sep #$20
    lda #240
    .rept 72 INDEX q
    sta.l oamMemory+1+q*4
    .endr
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
    lda.l torch_slot
    asl a
    asl a
    tay
    phb
    sep #$20
    lda #$7e
    pha
    plb
    rep #$20
    ; The torch shares its owner's depth group, after the six hero cells.
    ; DB=7E permits absolute,Y stores while X indexes banked ROM frames.
    .rept 8 INDEX q
    lda.l torch_oam_frames+q*2,x
    sta.w oamMemory+q*2,y
    .endr
    lda.l torch_slot
    and #3
    tax
    sep #$20
    lda.l torch_high_first,x
    sta.b tcc__r0
    lda.l torch_high_second,x
    sta.b tcc__r0h
    rep #$20
    lda.l torch_slot
    lsr a
    lsr a
    tax
    sep #$20
    lda.w oamMemory+512,x
    and.b tcc__r0
    sta.w oamMemory+512,x
    lda.w oamMemory+513,x
    and.b tcc__r0h
    sta.w oamMemory+513,x
    rep #$20
    plb
    rtl
torch_oam_hide:
    lda.l torch_slot
    asl a
    asl a
    tax
    sep #$20
    lda #240
    sta.l oamMemory+1,x
    sta.l oamMemory+5,x
    sta.l oamMemory+9,x
    sta.l oamMemory+13,x
    rep #$20
    rtl
torch_high_first: .db $00,$03,$0f,$3f
torch_high_second: .db $ff,$fc,$f0,$c0
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

; Scatter a packed 16x64 animation into the two left columns of the OBJ
; atlas. Eight 64-byte DMAs replace 512 bytes, at most once per four ticks.
.section "torch_upload" superfree
torch_upload:
    sep #$20
    lda #$80
    sta.l $2115
    lda 6,s
    sta.l $4304
    rep #$20
    lda #$1801
    sta.l $4300
    lda 4,s
    sta.l $4302
    ldx #$6600
    ldy #8
-:
    txa
    sta.l $2116
    lda #64
    sta.l $4305
    sep #$20
    lda #1
    sta.l $420b
    rep #$20
    txa
    clc
    adc #$100
    tax
    dey
    bne -
    rtl
.ends

; Conservative 16-scanline bands enforce the 34-sliver SNES limit.
; Hero uses four slivers in bands7..10; particles/projectiles/enemies have
; a separate reservation. Lower LOD is chosen before emitting an object.
.section "perspective_budget" superfree
perspective_budget_reset:
    sep #$20
    lda 4,s
    sta.l sprite_band_limit
    rep #$20
    lda #0
    sta.l sprite_bands
    sta.l sprite_bands+2
    sep #$20
    sta.l sprite_bands+4
    rep #$20
    lda #$0202
    sta.l sprite_bands+5
    lda #$0606
    sta.l sprite_bands+7
    sta.l sprite_bands+9
    rtl
perspective_lod:
    ; Every LOD touches its bottom band. If even one 16px cell cannot fit,
    ; reject once instead of retrying all three footprints in a dense scene.
    lda 6,s
    dec a
    cmp #176
    bcs lod_bottom_ready
    lsr a
    lsr a
    lsr a
    lsr a
    tax
    sep #$20
    lda.l sprite_bands,x
    clc
    adc #2
    cmp.l sprite_band_limit
    bcc lod_bottom_fits
    beq lod_bottom_fits
    rep #$20
    lda #0
    sta.b tcc__r0
    rtl
lod_bottom_fits:
    rep #$20
lod_bottom_ready:
    stz.b tcc__r3
    lda #16
    sta.b tcc__r3h
    lda #2
    sta.b tcc__r4
    lda 6,s
    sta.b tcc__r4h
    lda 4,s
    beq lod_npc
    cmp #1
    beq lod_tree
    cmp #6
    beq lod_wall
    cmp #4
    beq lod_house
    cmp #3
    beq lod_prop
    cmp #5
    beq lod_prop
    bra lod_try
lod_npc:
    lda.b tcc__r4h
    cmp #132
    bmi lod_try
    lda #48
    bra lod_medium
lod_prop:
    lda.b tcc__r4h
    cmp #140
    bmi lod_try
    lda #32
    bra lod_medium
lod_tree:
    lda.b tcc__r4h
    cmp #105
    bmi lod_try
    bra lod_tall
lod_wall:
    lda.b tcc__r4h
    cmp #98
    bmi lod_try
lod_tall:
    cmp #126
    bmi lod_32
    lda #2
    sta.b tcc__r3
    lda #64
    sta.b tcc__r3h
    lda #4
    sta.b tcc__r4
    bra lod_try
lod_house:
    lda.b tcc__r4h
    cmp #95
    bmi lod_try
    cmp #130
    bmi lod_32
    lda #2
    sta.b tcc__r3
    lda #64
    sta.b tcc__r3h
    lda #8
    sta.b tcc__r4
    bra lod_try
lod_32:
    lda #32
lod_medium:
    sta.b tcc__r3h
    lda #1
    sta.b tcc__r3
    lda #4
    sta.b tcc__r4
lod_try:
    lda.b tcc__r4
    pha
    lda.b tcc__r4h
    dec a
    pha
    inc a
    sec
    sbc.b tcc__r3h
    pha
    jsl perspective_reserve
    pla
    pla
    pla
    lda.b tcc__r0
    bne lod_success
    lda.b tcc__r3
    beq lod_failed
    dec a
    sta.b tcc__r3
    beq lod_small
    lda #32
    sta.b tcc__r3h
    lda #4
    sta.b tcc__r4
    bra lod_try
lod_small:
    lda #16
    sta.b tcc__r3h
    lda #2
    sta.b tcc__r4
    bra lod_try
lod_success:
    lda.b tcc__r3
    inc a
    sta.b tcc__r0
lod_failed:
    rtl
perspective_reserve:
    lda 6,s
    bmi reserve_invisible
    lda 4,s
    cmp #176
    bpl reserve_invisible
    cmp #0
    bpl +
    lda #0
+:
    lsr a
    lsr a
    lsr a
    lsr a
    sta.b tcc__r1
    lda 6,s
    cmp #176
    bmi +
    lda #175
+:
    lsr a
    lsr a
    lsr a
    lsr a
    sta.b tcc__r1h
    lda 8,s
    sta.b tcc__r2
    ldx.b tcc__r1
    sep #$20
reserve_check:
    lda.l sprite_bands,x
    clc
    adc.b tcc__r2
    cmp.l sprite_band_limit
    bcc +
    beq +
    rep #$20
    lda #0
    sta.b tcc__r0
    rtl
+:
    inx
    cpx.b tcc__r1h
    bcc reserve_check
    beq reserve_check
    ldx.b tcc__r1
reserve_add:
    lda.l sprite_bands,x
    clc
    adc.b tcc__r2
    sta.l sprite_bands,x
    inx
    cpx.b tcc__r1h
    bcc reserve_add
    beq reserve_add
    rep #$20
reserve_invisible:
    lda #1
    sta.b tcc__r0
    rtl
.ends

; Four adjacent scenery cells in one ABI call. The high-table mask preserves
; neighbouring NPC/hero bits, including unaligned groups and negative X.
.section "perspective_quad" superfree
perspective_quad:
    lda 12,s
    beq quad_small
    lda #32
    sta.b tcc__r2
    lda #4
    sta.b tcc__r2h
    lda #$aa
    bra quad_size
quad_small:
    lda #16
    sta.b tcc__r2
    lda #2
    sta.b tcc__r2h
    lda #0
quad_size:
    sta.b tcc__r4h
    lda 4,s
    asl a
    asl a
    tax
    lda 6,s
    and #$ff
    sta.b tcc__r1
    lda 8,s
    xba
    and #$ff00
    sta.b tcc__r1h
    ora.b tcc__r1
    sta.l oamMemory,x
    lda 6,s
    clc
    adc.b tcc__r2
    and #$ff
    sta.b tcc__r3h
    ora.b tcc__r1h
    sta.l oamMemory+4,x
    lda 8,s
    clc
    adc.b tcc__r2
    xba
    and #$ff00
    sta.b tcc__r3
    ora.b tcc__r1
    sta.l oamMemory+8,x
    lda.b tcc__r3
    ora.b tcc__r3h
    sta.l oamMemory+12,x
    lda 10,s
    ora #$2800
    sta.l oamMemory+2,x
    clc
    adc.b tcc__r2h
    sta.l oamMemory+6,x
    clc
    adc.b tcc__r2h
    sta.l oamMemory+10,x
    clc
    adc.b tcc__r2h
    sta.l oamMemory+14,x
    lda 6,s
    and #$100
    beq +
    lda.b tcc__r4h
    ora #$11
    sta.b tcc__r4h
+:
    lda 6,s
    clc
    adc.b tcc__r2
    and #$100
    beq +
    lda.b tcc__r4h
    ora #$44
    sta.b tcc__r4h
+:
    lda 4,s
    and #3
    asl a
    tax
    tay
    lda.l quad_masks,x
    sta.b tcc__r5
    lda.b tcc__r4h
    cpy #0
    beq quad_shifted
quad_shift:
    asl a
    dey
    bne quad_shift
quad_shifted:
    sta.b tcc__r4h
    lda 4,s
    lsr a
    lsr a
    tax
    lda.l oamMemory+512,x
    and.b tcc__r5
    ora.b tcc__r4h
    sta.l oamMemory+512,x
    rtl
quad_masks: .dw $ff00,$fc03,$f00f,$c03f
.ends

; Dynamic 32x48 resident. Called once after scene clear, so positive-X
; actors need no high-table work. Keep six cells in a single ABI call.
.section "perspective_npc" superfree
perspective_npc:
    lda 4,s
    asl a
    asl a
    tax
    lda 6,s
    and #$ff
    sta.b tcc__r0
    lda 6,s
    clc
    adc #16
    and #$ff
    sta.b tcc__r0h
    lda 8,s
    xba
    and #$ff00
    sta.b tcc__r1
    ora.b tcc__r0
    sta.l oamMemory,x
    lda.b tcc__r1
    ora.b tcc__r0h
    sta.l oamMemory+4,x
    lda.b tcc__r1
    clc
    adc #$1000
    and #$ff00
    sta.b tcc__r1
    ora.b tcc__r0
    sta.l oamMemory+8,x
    lda.b tcc__r1
    ora.b tcc__r0h
    sta.l oamMemory+12,x
    lda.b tcc__r1
    clc
    adc #$1000
    and #$ff00
    sta.b tcc__r1
    ora.b tcc__r0
    sta.l oamMemory+16,x
    lda.b tcc__r1
    ora.b tcc__r0h
    sta.l oamMemory+20,x
    lda 10,s
    ora #$2800
    sta.l oamMemory+2,x
    clc
    adc #2
    sta.l oamMemory+6,x
    clc
    adc #2
    sta.l oamMemory+10,x
    clc
    adc #2
    sta.l oamMemory+14,x
    clc
    adc #2
    sta.l oamMemory+18,x
    clc
    adc #2
    sta.l oamMemory+22,x
    lda 6,s
    and #$100
    sta.b tcc__r3
    lda 6,s
    clc
    adc #16
    and #$100
    sta.b tcc__r3h
    ora.b tcc__r3
    bne npc_high
    rtl
npc_high:
    lda 4,s
    sta.b tcc__r2
    stz.b tcc__r2h
    lda #6
    sta.b tcc__r4
npc_high_loop:
    lda.b tcc__r2h
    beq +
    lda.b tcc__r3h
    bra ++
+:
    lda.b tcc__r3
++:
    beq npc_high_next
    lda.b tcc__r2
    and #3
    tax
    sep #$20
    lda.l perspective_oam_ninth,x
    sta.b tcc__r5
    rep #$20
    lda.b tcc__r2
    lsr a
    lsr a
    tax
    sep #$20
    lda.l oamMemory+512,x
    ora.b tcc__r5
    sta.l oamMemory+512,x
    rep #$20
npc_high_next:
    inc.b tcc__r2
    lda.b tcc__r2h
    eor #1
    sta.b tcc__r2h
    dec.b tcc__r4
    bne npc_high_loop
    rtl
.ends

; Same target selection as the portable core, using authored byte coordinates.
; The context label refreshes while walking, so avoid a C table/function call
; for every candidate. r9h holds the result, r10 the best facing-aware score.
.section "interaction_focus" superfree
game_nearby:
    lda 4,s
    sta.b tcc__r1
    lda 6,s
    sta.b tcc__r1h
    lda #255
    sta.b tcc__r9h
    sta.b tcc__r10
    stz.b tcc__r9
    stz.b tcc__r5h
    ldy #34
    lda [tcc__r1],y
    sta.b tcc__r2
    ldy #36
    lda [tcc__r1],y
    sta.b tcc__r2h
    ldy #7
    lda [tcc__r1],y
    and #$ff
    lsr a
    and #3
    sta.b tcc__r5
    ldy #1
    lda [tcc__r1],y
    and #$ff
    cmp #4
    bcc +
    brl focus_done
+:
    sta.b tcc__r0
    asl a
    asl a
    asl a
    asl a
    asl a
    sta.b tcc__r4
    tax
    lda.l interaction_points,x
    and #$ff
    sta.b tcc__r4h
    inc.b tcc__r4
    lda.b tcc__r0
    cmp #2
    bcs focus_dark
    ldy #56
    lda [tcc__r1],y
    and #$ff
    beq focus_dark
    inc.b tcc__r5h
    bra focus_loop
focus_dark:
    ldy #6
    lda [tcc__r1],y
    and #$ff
    bne +
    brl focus_done
+:
    ldy #8
    lda [tcc__r1],y
    and #$ff
    bne focus_loop
    brl focus_done
focus_loop:
    ldx.b tcc__r4
    lda.l interaction_points,x
    and #$ff
    sec
    sbc.b tcc__r2
    sta.b tcc__r3
    bpl +
    eor #$ffff
    inc a
+:
    sta.b tcc__r0h
    cmp #56
    bcc +
    brl focus_next
+:
    lda.l interaction_points+1,x
    and #$ff
    sec
    sbc.b tcc__r2h
    sta.b tcc__r3h
    bpl +
    eor #$ffff
    inc a
+:
    clc
    adc.b tcc__r0h
    cmp #56
    bcc +
    brl focus_next
+:
    sta.b tcc__r10h
    lda.b tcc__r5
    beq focus_north
    cmp #1
    beq focus_east
    cmp #2
    beq focus_south
    lda.b tcc__r3
    clc
    adc #7
    bmi focus_score
    bra focus_side
focus_north:
    lda.b tcc__r3h
    clc
    adc #7
    bmi focus_score
    bra focus_side
focus_east:
    lda.b tcc__r3
    sec
    sbc #8
    bpl focus_score
    bra focus_side
focus_south:
    lda.b tcc__r3h
    sec
    sbc #8
    bpl focus_score
focus_side:
    lda.b tcc__r10h
    clc
    adc #48
    sta.b tcc__r10h
focus_score:
    lda.b tcc__r10h
    cmp.b tcc__r10
    bcs focus_next
    lda.b tcc__r5h
    bne focus_accept
    lda.l interaction_points+1,x
    and #$fc
    clc
    adc #10
    sec
    sbc.b tcc__r2h
    bpl +
    eor #$ffff
    inc a
+:
    cmp #65
    bcs focus_next
    tax
    lda.l torch_width,x
    and #$ff
    cmp.b tcc__r0h
    bcc focus_next
focus_accept:
    lda.b tcc__r10h
    sta.b tcc__r10
    lda.b tcc__r9
    sta.b tcc__r9h
focus_next:
    inc.b tcc__r4
    inc.b tcc__r4
    inc.b tcc__r9
    lda.b tcc__r9
    cmp.b tcc__r4h
    bcs focus_done
    brl focus_loop
focus_done:
    lda.b tcc__r9h
    sta.b tcc__r0
    rtl
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

; Billboard projection reads packed ROM coordinates directly. This avoids
; loading them into the C stack and passing the camera pointer for every prop.
.section "perspective_project_object" superfree
perspective_project_object:
    lda 4,s
    sta.b tcc__r5
    lda 6,s
    sta.b tcc__r5h
    ldy #2
    lda [tcc__r5],y
    sec
    sbc.l camera_world_y
    clc
    adc #576
    cmp #231
    bcc +
    brl object_project_hidden
+:
    tax
    sep #$20
    lda.l perspective_size,x
    sta.b tcc__r4
    lda.l perspective_y,x
    rep #$20
    and #$ff
    sta.b tcc__r2
    lda 12,s
    sta.b tcc__r1
    lda 14,s
    sta.b tcc__r1h
    lda.b tcc__r2
    sta [tcc__r1]
    lda [tcc__r5]
    sec
    sbc.l camera_world_x
    clc
    adc #384
    sta.b tcc__r3
    clc
    adc #255
    cmp #511
    bcc +
    brl object_project_hidden
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
    lda 8,s
    sta.b tcc__r1
    lda 10,s
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
    bcs object_project_hidden
    lda #1
    sta.b tcc__r0
    rtl
object_project_hidden:
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
