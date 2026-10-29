; Modified for Chernorechye: extended SPC bootstrap and channel-volume FIFO command.
;----------------------------------------------------------------------
;
;	SNESMod from CA65 to WLA DX! By KungFuFurby.
;	Original SNESMod by mukunda
;	Conversion Started: 3/9/12, Last update: 3/9/12 Reason: First attempt.
;	Adapted by Alekmaul for pvsneslib
;
;	This software is provided 'as-is', without any express or implied
;	warranty.  In no event will the authors be held liable for any
;	damages arising from the use of this software.
;
;	Permission is granted to anyone to use this software for any
;	purpose, including commercial applications, and to alter it and
;	redistribute it freely, subject to the following restrictions:
;
;	1.	The origin of this software must not be misrepresented; you
;		must not claim that you wrote the original software. If you use
;		this software in a product, an acknowledgment in the product
;		documentation would be appreciated but is not required.
;	2.	Altered source versions must be plainly marked as such, and
;		must not be misrepresented as being the original software.
;	3.	This notice may not be removed or altered from any source
;		distribution.
;
;----------------------------------------------------------------------

;----------------------------------------------------------------------

.include "hdr.asm"
.define REG_NMI_TIMEN $4200
.define REG_APUIO0 $2140
.define REG_APUIO1 $2141
.define REG_APUIO2 $2142
.define REG_APUIO3 $2143
.define SPC_BOOT $400
.BASE $80
.section "chernorechye_spc_boot" superfree
.index 16
.accu 16
audio_boot:
	php               
	sei
	phb               
	sep #$20
    lda #$0
	sta REG_NMI_TIMEN 
    pha
	plb 			; change bank address to 0

-:	ldx	REG_APUIO0	; wait for 'ready signal from SPC
	cpx	#0BBAAh		;
	bne	-		;--------------------------------------
	stx	REG_APUIO1	; start transfer:
	ldx	#SPC_BOOT	; port1 = !0
	stx	REG_APUIO2	; port2,3 = transfer address
	lda	#$CC		; port0 = 0CCh
	sta	REG_APUIO0	;--------------------------------------
-:	cmp	REG_APUIO0	; wait for SPC
	bne	-		;
;----------------------------------------------------------------------
; ready to transfer
;----------------------------------------------------------------------
	lda.l	audio_spc_binary	; read first byte
	xba			;
	lda	#0		;
	ldx	#1		;
	bra	audio_sb_start	;
;----------------------------------------------------------------------
; transfer data
;----------------------------------------------------------------------
audio_sb_send:
;----------------------------------------------------------------------
	xba			; swap DATA into A
	lda.l	audio_spc_binary, x; read next byte
	inx			; swap DATA into B
	xba			;--------------------------------------
-:	cmp	REG_APUIO0	; wait for SPC
	bne	-		;--------------------------------------
	ina			; increment counter (port0 data)
;----------------------------------------------------------------------
audio_sb_start:
;----------------------------------------------------------------------
	rep	#$20		; write port0+port1 data
	sta	REG_APUIO0	;
	sep	#$20		;--------------------------------------
	cpx	#audio_spc_binary_end-audio_spc_binary	; loop until all bytes transferred
	bcc	audio_sb_send				;
;----------------------------------------------------------------------
; all bytes transferred
;----------------------------------------------------------------------
-:	cmp	REG_APUIO0	; wait for SPC
	bne	-		;--------------------------------------
	ina			; add 2 or so...
	ina			;--------------------------------------
				; mask data so invalid 80h message won't get sent
	stz	REG_APUIO1	; port1=0
	ldx	#SPC_BOOT	; port2,3 = entry point
	stx	REG_APUIO2	;
	sta	REG_APUIO0	; write P0 data
				;--------------------------------------
-:	cmp	REG_APUIO0	; final sync
	bne	-		;--------------------------------------
	stz	REG_APUIO0

	stz.w spc_v		; reset V
	stz.w spc_q		; reset Q
	stz.w spc_fwrite	; reset command fifo
	stz.w spc_fread	;
	stz.w spc_sfx_next	;

	stz.w spc_pr+0
	stz.w spc_pr+1
	stz.w spc_pr+2
	stz.w spc_pr+3

	stz.w spc_ptr+0
	stz.w spc_ptr+1
	stz.w spc_ptr+2
	stz.w spc_bank

	stz spc1+0
	stz spc1+1
	stz spc2+0
	stz spc2+1


	stz.w digi_src+0
	stz.w digi_src+1
	stz.w digi_src+2
	stz.w digi_src2+0
	stz.w digi_src2+1
	stz.w digi_src2+2

	stz.w SoundTable+0
	stz.w SoundTable+1
	stz.w SoundTable+2

	stz.w spc_sfx_next

	stz.w digi_init
	stz.w digi_pitch
	stz.w digi_vp
	stz.w digi_remain+0
	stz.w digi_remain+1
	stz.w digi_active
	stz.w digi_copyrate

	ldx #$0
	lda #$0
-:	sta.w spc_fifo,x
	inx
	cpx #$ff
	bne -

;----------------------------------------------------------------------
; driver installation successful
;----------------------------------------------------------------------
	plb
	cli
	plp
	rtl			; return


.ends
.section "chernorechye_spc_channel" superfree
; void audio_set_volume(u8 channel, u8 volume), using the normal SDK FIFO.
audio_set_volume:
    php
    sei
    phb
    sep #$20
    lda #0
    pha
    plb
    sep #$10
    ldx.w spc_fwrite
    lda #$0c
    sta.w spc_fifo,x
    inx
    lda 6,s
    sta.w spc_fifo,x
    inx
    lda 7,s
    sta.w spc_fifo,x
    inx
    stx spc_fwrite
    rep #$10
    plb
    plp
    rtl
.ends
.section "chernorechye_spc_binary" superfree
audio_spc_binary:
.incbin "assets/generated/audio/spc700.bin"
audio_spc_binary_end:
.ends
