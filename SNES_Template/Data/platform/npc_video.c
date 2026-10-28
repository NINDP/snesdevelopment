#include <snes.h>
#include "../include/hero.h"
#include "../include/video_layout.h"
#define NPC_FRAME(n) extern u8 npc_frame##n;
NPC_FRAME(0) NPC_FRAME(1) NPC_FRAME(2) NPC_FRAME(3) NPC_FRAME(4)
NPC_FRAME(5) NPC_FRAME(6) NPC_FRAME(7) NPC_FRAME(8) NPC_FRAME(9)
NPC_FRAME(10) NPC_FRAME(11) NPC_FRAME(12) NPC_FRAME(13) NPC_FRAME(14)
NPC_FRAME(15) NPC_FRAME(16) NPC_FRAME(17) NPC_FRAME(18) NPC_FRAME(19)
NPC_FRAME(20) NPC_FRAME(21) NPC_FRAME(22) NPC_FRAME(23) NPC_FRAME(24)
NPC_FRAME(25) NPC_FRAME(26) NPC_FRAME(27) NPC_FRAME(28) NPC_FRAME(29)
NPC_FRAME(30) NPC_FRAME(31) NPC_FRAME(32) NPC_FRAME(33) NPC_FRAME(34)
NPC_FRAME(35) NPC_FRAME(36) NPC_FRAME(37) NPC_FRAME(38) NPC_FRAME(39)
NPC_FRAME(40) NPC_FRAME(41) NPC_FRAME(42) NPC_FRAME(43) NPC_FRAME(44)

extern u8 sprite_tiles;
static u8 *const npc_frames[45] = {
&npc_frame0,&npc_frame1,&npc_frame2,&npc_frame3,&npc_frame4,&npc_frame5,&npc_frame6,&npc_frame7,&npc_frame8,&npc_frame9,&npc_frame10,&npc_frame11,&npc_frame12,&npc_frame13,&npc_frame14,&npc_frame15,&npc_frame16,&npc_frame17,&npc_frame18,&npc_frame19,&npc_frame20,&npc_frame21,&npc_frame22,&npc_frame23,&npc_frame24,&npc_frame25,&npc_frame26,&npc_frame27,&npc_frame28,&npc_frame29,&npc_frame30,&npc_frame31,&npc_frame32,&npc_frame33,&npc_frame34,&npc_frame35,&npc_frame36,&npc_frame37,&npc_frame38,&npc_frame39,&npc_frame40,&npc_frame41,&npc_frame42,&npc_frame43,&npc_frame44};
/* First/second resident per room. Empty slots still hold shared prop cells. */
static const SkU8 residents[8] = {0,9,18,9,27,36,18,9};
static SkU8 resident0, resident1, selected0, selected1, pending0, pending1;
static SkU16 pose_tick;
static SkU8 room_cache;
static SkU8 resident_x[2], resident_y[2];
static SkU8 resident_pose(const Game *g, SkU8 slot, SkU16 tick) {
    SkS16 dx, dy, ax, ay;
    SkU8 frame = (tick >> 5) & 1;
    dx = g->x - resident_x[slot]; dy = g->y - resident_y[slot];
    ax = dx < 0 ? -dx : dx; ay = dy < 0 ? -dy : dy;
    if (ax + ay < 88) {
        if (ax > ay) return (dx < 0 ? 3 : 5) + frame;
        if (dy < 0) return 7 + frame;
    }
    return (tick & 127) >= 120 ? 2 : frame;
}
void npc_enter(const Game *g) {
    SkU8 room = g->room;
    const Hotspot *h;
    resident0 = residents[room << 1];
    resident1 = residents[(room << 1) + 1];
    room_cache = room;
    pose_tick = g->tick >> 2;
    h = game_hotspot(room, room == 1 ? 1 : 0);
    resident_x[0] = h->x; resident_y[0] = h->y;
    h = game_hotspot(room, 1);
    resident_x[1] = h->x; resident_y[1] = h->y;
    selected0 = resident_pose(g, 0, g->tick);
    selected1 = resident_pose(g, 1, g->tick + 16);
    dmaCopyVram(npc_frames[resident0 + selected0], VIDEO_OBJ_TILES + 4096, 1024);
    dmaCopyVram(npc_frames[resident1 + selected1], VIDEO_OBJ_TILES + 4608, 1024);
    pending0 = pending1 = 255;
}
void npc_prepare(const Game *g) {
    SkU8 frame;
    if ((g->tick >> 2) == pose_tick) return;
    pose_tick = g->tick >> 2;
    if (!(pose_tick & 1)) {
        frame = resident_pose(g, 0, g->tick);
        if (frame != selected0) pending0 = frame;
    }
    /* Only the village and chapel have a second full-size resident. The
       other bank's shared props remain loaded without idle DMA every frame. */
    else if (room_cache == 0 || room_cache == 2) {
        frame = resident_pose(g, 1, g->tick + 16);
        if (frame != selected1) pending1 = frame;
    }
}
void npc_commit(void) {
    if (pending0 != 255) {
        dmaCopyVram(npc_frames[resident0 + pending0], VIDEO_OBJ_TILES + 4096, 1024);
        selected0 = pending0;
        pending0 = 255;
    }
    else if (pending1 != 255) {
        dmaCopyVram(npc_frames[resident1 + pending1], VIDEO_OBJ_TILES + 4608, 1024);
        selected1 = pending1;
        pending1 = 255;
    }
}
void npc_leave(void) {
    dmaCopyVram(&sprite_tiles + 8192, VIDEO_OBJ_TILES + 4096, 2048);
}
