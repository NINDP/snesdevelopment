#include <snes.h>
#include "../include/hero.h"
#include "../include/video_layout.h"
extern u8 hero_palette, sprite_tiles;
#define HERO_FRAMES(n) \
    extern u8 hero_frame##n;
HERO_FRAMES(0) HERO_FRAMES(1) HERO_FRAMES(2) HERO_FRAMES(3)
HERO_FRAMES(4) HERO_FRAMES(5) HERO_FRAMES(6) HERO_FRAMES(7)
HERO_FRAMES(8) HERO_FRAMES(9) HERO_FRAMES(10) HERO_FRAMES(11)
HERO_FRAMES(12) HERO_FRAMES(13) HERO_FRAMES(14) HERO_FRAMES(15)
HERO_FRAMES(16) HERO_FRAMES(17) HERO_FRAMES(18) HERO_FRAMES(19)
HERO_FRAMES(20) HERO_FRAMES(21) HERO_FRAMES(22) HERO_FRAMES(23)
HERO_FRAMES(24) HERO_FRAMES(25) HERO_FRAMES(26) HERO_FRAMES(27)
HERO_FRAMES(28) HERO_FRAMES(29) HERO_FRAMES(30) HERO_FRAMES(31)
#define HERO_BOW_FRAMES(n) \
    extern u8 hero_bow_frame##n;
HERO_BOW_FRAMES(0) HERO_BOW_FRAMES(1) HERO_BOW_FRAMES(2) HERO_BOW_FRAMES(3)
HERO_BOW_FRAMES(4) HERO_BOW_FRAMES(5) HERO_BOW_FRAMES(6) HERO_BOW_FRAMES(7)
HERO_BOW_FRAMES(8) HERO_BOW_FRAMES(9) HERO_BOW_FRAMES(10) HERO_BOW_FRAMES(11)
HERO_BOW_FRAMES(12) HERO_BOW_FRAMES(13) HERO_BOW_FRAMES(14) HERO_BOW_FRAMES(15)
/* Flat table stays in ROM and indexes with shifts, without software multiply. */
static u8 *const frame_data[HERO_FRAME_COUNT + HERO_BOW_FRAME_COUNT] = {
    &hero_frame0, &hero_frame1, &hero_frame2, &hero_frame3,
    &hero_frame4, &hero_frame5, &hero_frame6, &hero_frame7,
    &hero_frame8, &hero_frame9, &hero_frame10, &hero_frame11,
    &hero_frame12, &hero_frame13, &hero_frame14, &hero_frame15,
    &hero_frame16, &hero_frame17, &hero_frame18, &hero_frame19,
    &hero_frame20, &hero_frame21, &hero_frame22, &hero_frame23,
    &hero_frame24, &hero_frame25, &hero_frame26, &hero_frame27,
    &hero_frame28, &hero_frame29, &hero_frame30, &hero_frame31,
    &hero_bow_frame0, &hero_bow_frame1, &hero_bow_frame2, &hero_bow_frame3,
    &hero_bow_frame4, &hero_bow_frame5, &hero_bow_frame6, &hero_bow_frame7,
    &hero_bow_frame8, &hero_bow_frame9, &hero_bow_frame10, &hero_bow_frame11,
    &hero_bow_frame12, &hero_bow_frame13, &hero_bow_frame14, &hero_bow_frame15};
static SkU8 selected_frame = 255, pending_frame = 255;
static SkU8 gait_frame = 2, gait_ticks = 0;
static SkU16 animation_tick = 0;
void hero_enter(void) {
    dmaCopyCGram(&hero_palette, 208, 32);
    selected_frame = 255;
    pending_frame = 255;
    gait_frame = 2;
    gait_ticks = 0;
    animation_tick = 0;
}
void hero_leave(void) {
    /* Restore legacy icons for a fresh playthrough's Mode 1 introduction. */
    dmaCopyVram(&sprite_tiles, VIDEO_OBJ_TILES, HERO_FRAME_BYTES);
    selected_frame = 255;
    pending_frame = 255;
}
void hero_prepare(const Game *g, SkU8 moving) {
    SkU8 facing, frame, elapsed;
    SkU16 delta = g->tick - animation_tick;
    animation_tick = g->tick;
    elapsed = delta > 4 ? 1 : (SkU8)delta;
    facing = g->direction < 2 ? 0 : (g->direction < 4 ? 1 : (g->direction < 6 ? 2 : 3));
    if (g->bow_mode) {
        /* A stationary two-handed stance: the off hand braces the grip,
           the shooting hand follows the string, then moves away on loose. */
        gait_frame = 2;
        gait_ticks = 0;
        frame = g->bow_draw >= 12 ? 2 : (g->bow_draw >= 6 ? 1 : 0);
        if (g->bow_cooldown > 16)
            frame = 3;
        frame += HERO_FRAME_COUNT + (facing << 2);
    } else if (moving) {
        gait_ticks += elapsed;
        if (gait_ticks >= 6) {
            gait_ticks -= 6;
            ++gait_frame;
            if (gait_frame >= 8)
                gait_frame = 2;
        }
        frame = gait_frame + (facing << 3);
    } else {
        gait_frame = 2;
        gait_ticks = 0;
        frame = ((g->tick >> 5) & 1) + (facing << 3);
    }
    if (frame != selected_frame)
        pending_frame = frame;
}
void hero_commit(void) {
    if (pending_frame == 255)
        return;
    /* Each facing is a separate 8 KiB LoROM section: this 1 KiB transfer
       cannot wrap its 16-bit source address. No per-frame heap or WRAM copy. */
    dmaCopyVram(frame_data[pending_frame], VIDEO_OBJ_TILES, HERO_FRAME_BYTES);
    selected_frame = pending_frame;
    pending_frame = 255;
}
