#include <snes.h>
#include "../include/platform.h"
#include "../include/perspective.h"
#include "../include/hero.h"
#include "../include/torch.h"
extern u8 perspective0_vram, perspective1_vram, perspective2_vram, perspective3_vram;
extern u8 perspective0_palette, perspective1_palette, perspective2_palette, perspective3_palette;
extern u8 perspective_scale, sprite_palette;
extern u8 daylight0_palettes, daylight1_palettes, daylight_actor_palettes;
extern u8 perspective_sky_brightness;
extern u8 bow_tiles, sprite_tiles;
#define TORCH_PHASE(n) \
    extern u8 perspective_light##n; \
    extern u8 perspective_glow##n##_224, perspective_glow##n##_128, perspective_glow##n##_88; \
    extern u8 perspective_glow##n##_64, perspective_glow##n##_16, perspective_glow##n##_48; \
    extern u8 perspective_glow##n##_200;
TORCH_PHASE(0)
TORCH_PHASE(1)
TORCH_PHASE(2)
TORCH_PHASE(3)
TORCH_PHASE(4) TORCH_PHASE(5) TORCH_PHASE(6) TORCH_PHASE(7)
TORCH_PHASE(8) TORCH_PHASE(9) TORCH_PHASE(10) TORCH_PHASE(11)
TORCH_PHASE(12) TORCH_PHASE(13) TORCH_PHASE(14) TORCH_PHASE(15)
TORCH_PHASE(16) TORCH_PHASE(17) TORCH_PHASE(18) TORCH_PHASE(19)
#define GLOW_PHASE(n) &perspective_glow##n##_224, &perspective_glow##n##_128, \
    &perspective_glow##n##_88, &perspective_glow##n##_64, \
    &perspective_glow##n##_16, &perspective_glow##n##_48, &perspective_glow##n##_200
static u8 *const light_tables[20] = {
    &perspective_light0, &perspective_light1, &perspective_light2, &perspective_light3,
    &perspective_light4, &perspective_light5, &perspective_light6, &perspective_light7,
    &perspective_light8, &perspective_light9, &perspective_light10, &perspective_light11,
    &perspective_light12, &perspective_light13, &perspective_light14, &perspective_light15,
    &perspective_light16, &perspective_light17, &perspective_light18, &perspective_light19};
/* Flat arrays stay in ROM with 816-tcc, instead of initialized WRAM. */
static u8 *const glow_tables[140] = {
    GLOW_PHASE(0), GLOW_PHASE(1), GLOW_PHASE(2), GLOW_PHASE(3),
    GLOW_PHASE(4), GLOW_PHASE(5), GLOW_PHASE(6), GLOW_PHASE(7),
    GLOW_PHASE(8), GLOW_PHASE(9), GLOW_PHASE(10), GLOW_PHASE(11),
    GLOW_PHASE(12), GLOW_PHASE(13), GLOW_PHASE(14), GLOW_PHASE(15),
    GLOW_PHASE(16), GLOW_PHASE(17), GLOW_PHASE(18), GLOW_PHASE(19)};
static dmaMemory scale_source, light_source, layers_source, mode_source, glow_source;
static SkU8 mode_table[2][7], layer_table[2][9];
static SkU8 active_overlay = 0, pending_overlay = 0;
static SkU8 old_cut = 255, old_lit = 255, old_phase = 255, phase;
static SkU8 sky, old_sky = 255, previous_sky = 255, palette_sky = 255;
static u8 *sky_palettes;
static SkU16 camera_world_x, camera_world_y;
static SkU8 lit, force_objects = 1, previous_facing = 255;
static SkS16 previous_x = -1, previous_y = -1;
static SkS16 cull_left, cull_right;
static SkS16 enemy_x_cache[COMBAT_ENEMIES], enemy_y_cache[COMBAT_ENEMIES];
static SkU8 enemy_state_cache[COMBAT_ENEMIES];
static SkU16 arrow_tiles[COMBAT_ARROWS];
static SkU8 arrow_life_cache[COMBAT_ARROWS], marker_visible = 0;
static SkU8 combat_visible = 0;
static SkU8 slots, moving;
/* Fixed 16-bit ABI for the short 65C816 OAM writers. */
void perspective_obj(SkU16 slot, SkS16 x, SkS16 y, SkU16 tile, SkU16 large);
void perspective_clear(void);
#define obj perspective_obj
static void player(void) {
    hero_draw(slots);
    slots += 6;
}
static void combat_draw(const Game *g, SkU8 force) {
    const Enemy *enemy;
    const Arrow *arrow;
    SkU8 i, slot, state, direction, angle;
    SkS16 sx, sy;
    SkU16 tile;
    if (!g->enemy_active && !g->bow_mode &&
        !g->arrows[0].life && !g->arrows[1].life && !g->arrows[2].life &&
        !g->enemies[0].hit && !g->enemies[1].hit && !g->enemies[2].hit && !g->enemies[3].hit) {
        /* Daytime exploration needs no actor traversal. Run the loop once
           when the last combat sprite disappears to clear its cached slot. */
        if (!combat_visible)
            return;
        combat_visible = 0;
    } else
        combat_visible = 1;
    enemy = g->enemies;
    for (i = 0; i < COMBAT_ENEMIES; ++i, ++enemy) {
        state = enemy->hp ? enemy->kind + 1 : (enemy->hit ? 3 : 0);
        if (enemy->hit && (g->tick & 2))
            state = 0;
        /* A scenery rebuild has already hidden every combat slot. Never
           spend twelve generic OAM calls rewriting hidden daytime actors. */
        if (!state) {
            if (!force && enemy_state_cache[i]) {
                slot = i ? 58 + (i << 1) : 50;
                obj(slot, 0, 240, 0, 0);
                obj(slot + 1, 0, 240, 0, 0);
            }
            enemy_state_cache[i] = 0;
            continue;
        }
        if (!force && state == enemy_state_cache[i] && enemy->x == enemy_x_cache[i] &&
            enemy->y == enemy_y_cache[i])
            continue;
        enemy_x_cache[i] = enemy->x;
        enemy_y_cache[i] = enemy->y;
        enemy_state_cache[i] = state;
        /* Keep the original shade slots for old captures and give new actors
           independent fixed slots so movement never rebuilds the scenery. */
        slot = i ? 58 + (i << 1) : 50;
        if (!perspective_project(g, enemy->x, enemy->y, &sx, &sy)) {
            obj(slot, 0, 240, 0, 0);
            obj(slot + 1, 0, 240, 0, 0);
        } else if (state == 1) {
            obj(slot, sx - 8, sy - 32, 266, 0);
            obj(slot + 1, sx - 8, sy - 16, 298, 0);
        } else {
            tile = state == 2 ? 482 : (BOW_IMPACT_TILE | 0x0200);
            obj(slot, sx - 8, sy - 16, tile, 0);
            obj(slot + 1, 0, 240, 0, 0);
        }
    }
    arrow = g->arrows;
    for (i = 0; i < COMBAT_ARROWS; ++i, ++arrow) {
        if (arrow->life && arrow->damage && (arrow->life > arrow_life_cache[i] || !arrow_life_cache[i])) {
            direction = combat_direction(arrow->dx, arrow->dy);
            angle = direction <= 4 ? direction : (direction <= 8 ? 8 - direction :
                    (direction <= 12 ? direction - 8 : 16 - direction));
            tile = (BOW_ARROW_TILE + (angle << 1)) | 0x0200;
            if (direction > 8)
                tile |= 0x4000;
            if (direction > 4 && direction < 12)
                tile |= 0x8000;
            arrow_tiles[i] = tile;
        }
        if (arrow->life && perspective_project(g, arrow->x >> 2, arrow->y >> 2, &sx, &sy)) {
            tile = arrow->damage ? arrow_tiles[i] :
                   ((BOW_IMPACT_TILE + (arrow->life < 4 ? 2 : 0)) | 0x0200);
            obj(68 + i, sx - 8, sy - 30, tile, 0);
        } else if (!force && arrow_life_cache[i])
            obj(68 + i, 0, 240, 0, 0);
        arrow_life_cache[i] = arrow->life;
    }
    if (g->bow_mode && perspective_project(g, g->aim_x, g->aim_y, &sx, &sy)) {
        obj(71, sx - 8, sy - 26, BOW_MARKER_TILE | 0x0200, 0);
        marker_visible = 1;
    } else if (force || marker_visible) {
        if (!force)
            obj(71, 0, 240, 0, 0);
        marker_visible = 0;
    }
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
    sky_palettes = room == 0 ? &daylight0_palettes :
                   (room == 1 ? &daylight1_palettes : palette);
    palette_sky = 255;
    setScreenOff();
    dmaCopyVram(source, 0, 32768);
    dmaCopyCGram(palette, 0, 256);
    /* OBJ palettes 4..7 participate in color math; palette 0 stays available
       to the Mode 1 introduction. Both copies use the same authored colors. */
    dmaCopyCGram(&sprite_palette, 192, 32);
    hero_enter();
    torch_enter();
    dmaCopyVram(&bow_tiles, VIDEO_OBJ_TILES + 1024, BOW_TILE_BYTES);
    setMode7(0x80);
    REG_M7B = 0; REG_M7B = 0;
    REG_M7C = 0; REG_M7C = 0;
    REG_TS = 0;
    REG_TM = 0;
    REG_TMW = 0x11;
    REG_TSW = 0;
    REG_W12SEL = 3; /* Hide BG1 outside window 1. */
    REG_W34SEL = 0; /* Text is never clipped. */
    REG_WBGLOG = 0;
    REG_WOBJSEL = 0x83; /* OBJ outside W1; color math outside inner W2. */
    REG_WOBJLOG = 0;
    REG_CGWSEL = 0x20;
    REG_CGADSUB = 0xd1; /* Half/subtract on BG1 and OBJ, never BG3/backdrop. */
    REG_COLDATA = 0x21;
    REG_COLDATA = 0x43;
    REG_COLDATA = 0x85;
    REG_WH0 = 255; REG_WH1 = 0;
    REG_WH2 = 255; REG_WH3 = 0;
    setPaletteColor(0, 0);
    scale_source.mem.p = &perspective_scale;
    light_source.mem.p = light_tables[0];
    layers_source.mem.p = layer_table[0];
    mode_source.mem.p = mode_table[0];
    active_overlay = 0;
    pending_overlay = 0;
    glow_source.mem.p = glow_tables[0];
    old_cut = 255;
    old_sky = 255;
    force_objects = 1;
    setScreenOn();
}
void perspective_leave(void) {
    setScreenOff();
    REG_HDMAEN = 0;
    perspective_clear();
    hero_leave();
    torch_leave();
    dmaCopyVram(&sprite_tiles + 2048, VIDEO_OBJ_TILES + 1024, BOW_TILE_BYTES);
    REG_TMW = 0;
    REG_TSW = 0;
    REG_W12SEL = 0;
    REG_W34SEL = 0;
    REG_WBGLOG = 0;
    REG_WOBJLOG = 0;
    REG_CGWSEL = 0;
    REG_CGADSUB = 0;
    REG_COLDATA = 0xe0;
    REG_WOBJSEL = 0;
    REG_TS = 0;
    setMode(BG_MODE1, BG3_MODE1_PRIORITY_HIGH);
}
void perspective_draw(const Game *g) {
    SkU8 i, count, kind, inserted = 0, objects_changed;
    SkU16 tile;
    SkS16 sx, sy, player_y;
    const PerspectiveObject *object;
    camera_world_x = PERSPECTIVE_ORIGIN + g->x;
    camera_world_y = PERSPECTIVE_ORIGIN + g->y;
    lit = g->lamp && g->oil;
    sky = game_daylight(g);
    phase = (g->bow_mode ? 16 : ((g->direction & 6) << 1)) | ((g->tick >> 3) & 3);
    moving = previous_x != g->x || previous_y != g->y;
    hero_prepare(g, moving);
    objects_changed = force_objects || moving || (phase >> 2) != previous_facing || sky != previous_sky;
    if (objects_changed) {
        perspective_clear();
        slots = 0;
        count = perspective_counts[g->room];
        object = perspective_objects[g->room];
        player_y = g->y;
        if ((phase >> 2) != previous_facing || sky != previous_sky) {
            cull_left = sky ? -32 : (g->bow_mode ? TORCH_PLANTED_X : perspective_light_x[phase >> 2]) - 96;
            cull_right = sky ? 287 : cull_left + 192;
        }
        for (i = 0; i < count; ++i, ++object) {
            if (!inserted && object->y < player_y) {
                player();
                inserted = 1;
            }
            if (object->y < player_y - 112)
                continue;
            if (!perspective_project(g, object->x, object->y, &sx, &sy))
                continue;
            /* Even the widest (32 px) billboard cannot touch the light here.
               Keep partial silhouettes at the edge; PPU windows clip pixels. */
            if (sx < cull_left || sx > cull_right)
                continue;
            kind = object->kind & 0x7f;
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
            player();
        previous_x = g->x;
        previous_y = g->y;
        previous_facing = phase >> 2;
        previous_sky = sky;
        force_objects = 0;
    }
    /* Avoid even the combat function's stack frame and cold actor probes on
       a sunlit walk. Existing arrows and fading enemies keep it scheduled. */
    if (g->enemy_active || g->bow_mode || combat_visible)
        combat_draw(g, objects_changed);
    torch_draw(g);
}
void perspective_overlay(SkU8 cut) {
    SkU8 i = 0, floor = (lit || sky) ? 0x11 : 0, next = active_overlay ^ 1, glow = 0;
    if (cut == old_cut && lit == old_lit && phase == old_phase && sky == old_sky)
        return;
    switch (cut) {
    case 128: glow = 1; break;
    case 88: glow = 2; break;
    case 64: glow = 3; break;
    case 16: glow = 4; break;
    case 48: glow = 5; break;
    case 200: glow = 6; break;
    }
    light_source.mem.p = light_tables[phase];
    glow_source.mem.p = sky ? &perspective_sky_brightness : glow_tables[(phase << 3) - phase + glow];
    old_phase = phase;
    if (cut == old_cut && lit == old_lit && sky == old_sky)
        return;
    old_cut = cut;
    old_lit = lit;
    old_sky = sky;
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
    SkU8 shade;
    REG_HDMAEN = 0;
    hero_commit();
    if (sky != palette_sky) {
        dmaCopyCGram(sky_palettes + ((SkU16)sky << 8), 0, 256);
        dmaCopyCGram(&daylight_actor_palettes + ((SkU16)sky << 6), 192, 64);
        palette_sky = sky;
    }
    REG_TMW = sky ? 0 : 0x11;
    REG_WOBJSEL = sky ? 0x23 : 0x83;
    REG_CGWSEL = sky && !lit ? 0 : 0x20;
    REG_CGADSUB = sky ? 0x91 : 0xd1;
    if (sky) {
        shade = 16 - sky;
        REG_COLDATA = 0x20 | shade;
        REG_COLDATA = 0x40 | shade;
        REG_COLDATA = 0x80 | shade;
    } else {
        REG_COLDATA = 0x21;
        REG_COLDATA = 0x43;
        REG_COLDATA = 0x85;
    }
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
    /* A single four-register transfer publishes both concentric windows. */
    REG_DMAP6 = 4; REG_BBAD6 = 0x26;
    REG_A1T6LH = light_source.mem.c.addr; REG_A1B6 = light_source.mem.c.bank;
    REG_DMAP5 = 0; REG_BBAD5 = 0;
    REG_A1T5LH = glow_source.mem.c.addr; REG_A1B5 = glow_source.mem.c.bank;
    REG_TM = 0;
    REG_WH0 = 255; REG_WH1 = 0;
    REG_WH2 = 255; REG_WH3 = 0;
    REG_HDMAEN = 0x7e; /* Windows also mask the world above dialogue panels. */
    REG_INIDISP = 15;
}
