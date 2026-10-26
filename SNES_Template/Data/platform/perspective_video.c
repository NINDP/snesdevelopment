#include <snes.h>
#include "../include/platform.h"
#include "../include/perspective.h"
extern u8 perspective0_vram, perspective1_vram, perspective2_vram, perspective3_vram;
extern u8 perspective0_palette, perspective1_palette, perspective2_palette, perspective3_palette;
extern u8 perspective_scale, perspective_light, perspective_fog;
static dmaMemory scale_source, light_source, layers_source, mode_source, fog_source;
static SkU8 mode_table[2][7], layer_table[2][9];
static SkU8 active_overlay = 0, pending_overlay = 0;
static SkU8 overlay_cut = 224, old_cut = 255, old_lit = 255;
static SkU16 camera_world_x, camera_world_y;
static SkU8 lit, force_objects = 1;
static SkS16 previous_x = -1, previous_y = -1, previous_enemy_x = -1, previous_enemy_y = -1;
static SkU8 slots, moving;
/* Fixed 16-bit ABI for the short 65C816 OAM writers. */
void perspective_obj(SkU16 slot, SkS16 x, SkS16 y, SkU16 tile, SkU16 large);
void perspective_clear(void);
#define obj perspective_obj
static void player(const Game *g) {
    SkU8 facing = g->direction < 2 ? 0 : (g->direction < 4 ? 1 : (g->direction < 6 ? 2 : 3));
    SkU16 tile = 96 + facing * 4;
    if (moving && ((g->tick >> 3) & 1))
        tile += 2;
    obj(slots++, 120, 132, tile, 0);
    obj(slots++, 120, 148, tile + 32, 0);
}
void perspective_enter(SkU8 room) {
    u8 *source, *palette;
    REG_HDMAEN = 0;
    switch (room) {
    case 0: source = &perspective0_vram; palette = &perspective0_palette; break;
    case 1: source = &perspective1_vram; palette = &perspective1_palette; break;
    case 2: source = &perspective2_vram; palette = &perspective2_palette; break;
    default: source = &perspective3_vram; palette = &perspective3_palette; break;
    }
    setScreenOff();
    dmaCopyVram(source, 0, 32768);
    dmaCopyCGram(palette, 0, 256);
    setMode7(0x80);
    REG_M7B = 0; REG_M7B = 0;
    REG_M7C = 0; REG_M7C = 0;
    REG_TS = 0;
    REG_TMW = 0;
    REG_TSW = 0;
    REG_W12SEL = 0;
    REG_WOBJSEL = 0x20; /* Color window 1, no sprite clipping. */
    REG_WOBJLOG = 0;
    REG_CGWSEL = 0x20; /* Suppress subtraction inside the torch window. */
    REG_CGADSUB = 0x81;
    REG_COLDATA = 0xe1;
    setPaletteColor(0, RGB5(1, 2, 3));
    scale_source.mem.p = &perspective_scale;
    light_source.mem.p = &perspective_light;
    layers_source.mem.p = layer_table[0];
    mode_source.mem.p = mode_table[0];
    active_overlay = 0;
    pending_overlay = 0;
    fog_source.mem.p = &perspective_fog;
    old_cut = 255;
    force_objects = 1;
    setScreenOn();
}
void perspective_leave(void) {
    REG_HDMAEN = 0;
    REG_CGWSEL = 0;
    REG_CGADSUB = 0;
    REG_COLDATA = 0xe0;
    REG_WOBJSEL = 0;
    setMode(BG_MODE1, BG3_MODE1_PRIORITY_HIGH);
}
void perspective_draw(const Game *g) {
    SkU8 i, count, kind, inserted = 0;
    SkU16 tile;
    SkS16 sx, sy, player_y;
    const PerspectiveObject *object;
    camera_world_x = PERSPECTIVE_ORIGIN + g->x;
    camera_world_y = PERSPECTIVE_ORIGIN + g->y;
    lit = g->lamp && g->oil;
    moving = previous_x != g->x || previous_y != g->y;
    if (force_objects || moving || g->enemy_x != previous_enemy_x || g->enemy_y != previous_enemy_y) {
        perspective_clear();
        slots = 0;
        count = perspective_counts[g->room];
        object = perspective_objects[g->room];
        player_y = g->y;
        for (i = 0; i < count; ++i, ++object) {
            if (!inserted && object->y < player_y) {
                player(g);
                inserted = 1;
            }
            if (object->y < player_y - 112)
                continue;
            if (!perspective_project(g, object->x, object->y, &sx, &sy))
                continue;
            kind = object->kind;
            tile = object->tile;
            if (kind == 0) {
                if (sy < 140)
                    obj(slots++, sx - 8, sy - 16, 454 + tile - 256, 0);
                else {
                    obj(slots++, sx - 8, sy - 32, tile, 0);
                    obj(slots++, sx - 8, sy - 16, tile + 32, 0);
                }
            } else if (kind == 1) {
                if (sy < 134)
                    obj(slots++, sx - 8, sy - 16, 448, 0);
                else
                    obj(slots++, sx - 16, sy - 32, 320, 1);
            } else if (kind == 3) {
                if (sy < 140)
                    obj(slots++, sx - 8, sy - 16, 450, 0);
                else
                    obj(slots++, sx - 16, sy - 32, tile, 1);
            } else
                obj(slots++, sx - 8, sy - 16, tile, 0);
        }
        if (!inserted)
            player(g);
        if (g->enemy_active && perspective_project(g, g->enemy_x, g->enemy_y, &sx, &sy)) {
            obj(slots++, sx - 8, sy - 32, 266, 0);
            obj(slots++, sx - 8, sy - 16, 298, 0);
        }
        previous_x = g->x;
        previous_y = g->y;
        previous_enemy_x = g->enemy_x;
        previous_enemy_y = g->enemy_y;
        force_objects = 0;
    }
    obj(60, 130, 134, lit ? 160 + ((g->tick >> 2) & 3) * 2 : 174, 0);
    obj(61, 128 + ((g->tick >> 2) & 3), 128 - (g->tick & 15), lit ? 168 : 0, 0);
}
void perspective_overlay(SkU8 cut) {
    SkU8 i = 0, floor = lit ? 0x11 : 0, next = active_overlay ^ 1;
    overlay_cut = cut;
    if (cut == old_cut && lit == old_lit)
        return;
    old_cut = cut;
    old_lit = lit;
    if (cut >= 127) {
        mode_table[next][i++] = 127; mode_table[next][i++] = 7;
        mode_table[next][i++] = cut - 127; mode_table[next][i++] = 7;
    } else {
        mode_table[next][i++] = cut; mode_table[next][i++] = 7;
    }
    mode_table[next][i++] = 1; mode_table[next][i++] = 9; mode_table[next][i] = 0;
    i = 0;
    layer_table[next][i++] = cut < 48 ? cut : 48; layer_table[next][i++] = 0;
    if (cut > 48) {
        if (cut - 48 > 127) {
            layer_table[next][i++] = 127; layer_table[next][i++] = floor;
            layer_table[next][i++] = cut - 175; layer_table[next][i++] = floor;
        } else {
            layer_table[next][i++] = cut - 48; layer_table[next][i++] = floor;
        }
    }
    layer_table[next][i++] = 1; layer_table[next][i++] = 4; layer_table[next][i] = 0;
    pending_overlay = next + 1;
}
void perspective_commit(void) {
    SkU16 hofs = camera_world_x - 128, vofs = camera_world_y - PERSPECTIVE_ANCHOR;
    REG_HDMAEN = 0;
    if (pending_overlay) {
        active_overlay = pending_overlay - 1;
        mode_source.mem.p = mode_table[active_overlay];
        layers_source.mem.p = layer_table[active_overlay];
        pending_overlay = 0;
    }
    REG_BGMODE = BG_MODE7;
    REG_M7X = camera_world_x; REG_M7X = camera_world_x >> 8;
    REG_M7Y = camera_world_y; REG_M7Y = camera_world_y >> 8;
    REG_M7HOFS = hofs; REG_M7HOFS = hofs >> 8;
    REG_M7VOFS = vofs; REG_M7VOFS = vofs >> 8;
    REG_DMAP1 = 0; REG_BBAD1 = 0x05;
    REG_A1T1LH = mode_source.mem.c.addr; REG_A1B1 = mode_source.mem.c.bank;
    REG_DMAP3 = 2; REG_BBAD3 = 0x1b;
    REG_A1T3LH = scale_source.mem.c.addr; REG_A1B3 = scale_source.mem.c.bank;
    REG_DMAP4 = 2; REG_BBAD4 = 0x1e;
    REG_A1T4LH = scale_source.mem.c.addr; REG_A1B4 = scale_source.mem.c.bank;
    REG_DMAP2 = 0; REG_BBAD2 = 0x2c;
    REG_A1T2LH = layers_source.mem.c.addr; REG_A1B2 = layers_source.mem.c.bank;
    REG_DMAP6 = 1; REG_BBAD6 = 0x26;
    REG_A1T6LH = light_source.mem.c.addr; REG_A1B6 = light_source.mem.c.bank;
    REG_DMAP5 = 0; REG_BBAD5 = 0;
    REG_A1T5LH = fog_source.mem.c.addr; REG_A1B5 = fog_source.mem.c.bank;
    REG_HDMAEN = lit && overlay_cut == 224 ? 0x7e : 0x5e;
    REG_INIDISP = lit || overlay_cut < 224 ? 15 : 0;
}
