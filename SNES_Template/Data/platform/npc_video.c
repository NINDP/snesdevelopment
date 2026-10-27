#include <snes.h>
#include "../include/hero.h"
#include "../include/video_layout.h"
#define NPC_FRAME(n) extern u8 npc_frame##n;
NPC_FRAME(0) NPC_FRAME(1) NPC_FRAME(2) NPC_FRAME(3) NPC_FRAME(4)
NPC_FRAME(5) NPC_FRAME(6) NPC_FRAME(7) NPC_FRAME(8) NPC_FRAME(9)
NPC_FRAME(10) NPC_FRAME(11) NPC_FRAME(12) NPC_FRAME(13) NPC_FRAME(14)
extern u8 sprite_tiles;
static u8 *const npc_frames[15] = {
    &npc_frame0,&npc_frame1,&npc_frame2,&npc_frame3,&npc_frame4,
    &npc_frame5,&npc_frame6,&npc_frame7,&npc_frame8,&npc_frame9,
    &npc_frame10,&npc_frame11,&npc_frame12,&npc_frame13,&npc_frame14};
/* First/second resident per room. Empty slots still hold shared prop cells. */
static const SkU8 residents[8] = {0,3,6,3,9,12,6,3};
static SkU8 resident0, resident1, selected0, selected1, pending0, pending1;
void npc_enter(const Game *g) {
    SkU8 room = g->room;
    SkU16 tick = g->tick;
    resident0 = residents[room << 1];
    resident1 = residents[(room << 1) + 1];
    selected0 = (tick & 127) >= 124 ? 2 : ((tick >> 5) & 1);
    tick += 16;
    selected1 = (tick & 127) >= 124 ? 2 : ((tick >> 5) & 1);
    dmaCopyVram(npc_frames[resident0 + selected0], VIDEO_OBJ_TILES + 4096, 1024);
    dmaCopyVram(npc_frames[resident1 + selected1], VIDEO_OBJ_TILES + 4608, 1024);
    pending0 = pending1 = 255;
}
void npc_prepare(const Game *g) {
    SkU16 tick = g->tick;
    SkU8 frame = (tick & 127) >= 124 ? 2 : ((tick >> 5) & 1);
    if (frame != selected0) pending0 = frame;
    tick += 16;
    frame = (tick & 127) >= 124 ? 2 : ((tick >> 5) & 1);
    if (frame != selected1) pending1 = frame;
}
void npc_commit(void) {
    if (pending0 != 255) {
        dmaCopyVram(npc_frames[resident0 + pending0], VIDEO_OBJ_TILES + 4096, 1024);
        selected0 = pending0;
        pending0 = 255;
    }
    if (pending1 != 255) {
        dmaCopyVram(npc_frames[resident1 + pending1], VIDEO_OBJ_TILES + 4608, 1024);
        selected1 = pending1;
        pending1 = 255;
    }
}
void npc_leave(void) {
    dmaCopyVram(&sprite_tiles + 8192, VIDEO_OBJ_TILES + 4096, 2048);
}
