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
extern u8 scenery_tiles, scenery_low_tiles, scenery_compact_tiles;
extern u8 chapel_scenery_tiles, chapel_compact_tiles;
extern u8 daylight_scenery_palettes;
extern u8 npc_palette;
extern u8 backdrop0_tiles, backdrop0_map, backdrop1_tiles, backdrop1_map, backdrop_palettes;
void npc_enter(const Game *g);
void npc_prepare(const Game *g);
void npc_commit(void);
void npc_leave(void);
#define TORCH_PHASE(n) \
    extern u8 perspective_light##n; \
    extern u8 perspective_glow##n##_224, perspective_glow##n##_128, perspective_glow##n##_88; \
    extern u8 perspective_glow##n##_64, perspective_glow##n##_16, perspective_glow##n##_48; \
    extern u8 perspective_glow##n##_176, perspective_glow##n##_192;
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
    &perspective_glow##n##_16, &perspective_glow##n##_48, &perspective_glow##n##_176, &perspective_glow##n##_192
static u8 *const light_tables[20] = {
    &perspective_light0, &perspective_light1, &perspective_light2, &perspective_light3,
    &perspective_light4, &perspective_light5, &perspective_light6, &perspective_light7,
    &perspective_light8, &perspective_light9, &perspective_light10, &perspective_light11,
    &perspective_light12, &perspective_light13, &perspective_light14, &perspective_light15,
    &perspective_light16, &perspective_light17, &perspective_light18, &perspective_light19};
/* Flat arrays stay in ROM with 816-tcc, instead of initialized WRAM. */
static u8 *const glow_tables[160] = {
    GLOW_PHASE(0), GLOW_PHASE(1), GLOW_PHASE(2), GLOW_PHASE(3),
    GLOW_PHASE(4), GLOW_PHASE(5), GLOW_PHASE(6), GLOW_PHASE(7),
    GLOW_PHASE(8), GLOW_PHASE(9), GLOW_PHASE(10), GLOW_PHASE(11),
    GLOW_PHASE(12), GLOW_PHASE(13), GLOW_PHASE(14), GLOW_PHASE(15),
    GLOW_PHASE(16), GLOW_PHASE(17), GLOW_PHASE(18), GLOW_PHASE(19)};
static dmaMemory scale_source, light_source, layers_source, mode_source, glow_source, sky_source;
static SkU8 mode_table[2][9], layer_table[2][9];
static SkU8 parallax_table[13];
static SkU8 active_overlay = 0, pending_overlay = 0;
static SkU8 old_cut = 255, old_lit = 255, old_phase = 255, phase;
static SkU8 sky, old_sky = 255, previous_sky = 255, palette_sky = 255;
static SkU8 published_sky = 255, published_lit = 255;
static u8 *sky_palettes;
SkU16 camera_world_x, camera_world_y;
static SkU8 lit, force_objects = 1, previous_bow = 255;
static SkS16 previous_x = -1, previous_y = -1;
static SkS16 cull_left, cull_right;
static SkS16 enemy_x_cache[COMBAT_ENEMIES], enemy_y_cache[COMBAT_ENEMIES];
static SkU8 enemy_state_cache[COMBAT_ENEMIES];
static SkU8 warning_visible[COMBAT_ENEMIES];
static SkU16 arrow_tiles[COMBAT_ARROWS];
static SkU8 arrow_life_cache[COMBAT_ARROWS], marker_visible = 0;
static SkU8 combat_visible = 0;
static SkU8 enemy_slots_cache = 0, projectiles_visible = 0;
static SkU8 shove_visible = 0, hurt_visible = 0;
static SkU8 slots, moving;
/* Read-only regression counter: publishing PPU state must finish in VBlank. */
SkU16 video_late_commits = 0;
SkU8 sprite_bands[11], sprite_band_limit;
static SkU8 critical_plan[26];
/* At most six houses/NPCs are planned per room. Keep coordinates by that
   compact slot; the per-object byte stores slot<<2 plus the two-bit LOD. */
static SkS16 critical_x[6], critical_y[6];

SkU8 perspective_project_object(const PerspectiveObject *object, SkS16 *sx, SkS16 *sy);
void perspective_budget_reset(SkU16 limit);
SkU8 perspective_lod(SkU16 kind, SkS16 bottom);
SkU8 perspective_reserve(SkS16 top, SkS16 bottom, SkU16 cost);
static SkU8 previous_budget = 255;
/* Fixed 16-bit ABI for the short 65C816 OAM writers. */
void perspective_obj(SkU16 slot, SkS16 x, SkS16 y, SkU16 tile, SkU16 large);
void perspective_quad(SkU16 slot, SkS16 x, SkS16 y, SkU16 tile, SkU16 large);
void perspective_npc(SkU16 slot, SkS16 x, SkS16 y, SkU16 tile);
void perspective_clear(void);
#define obj perspective_obj
static void player(void) {
    hero_draw(slots);
    slots += 6;
    torch_slot = slots;
    slots += 4;
}
static void combat_draw(const Game *g, SkU8 force) {
    const Enemy *enemy;
    const Arrow *arrow;
    SkU8 i, slot, state, direction, angle, count;
    SkS16 sx, sy;
    SkU16 tile;
    if (!g->enemy_active && !g->bow_mode &&
        !g->arrows[0].life && !g->arrows[1].life && !g->arrows[2].life &&
        !g->enemies[0].hit && !g->enemies[1].hit && !g->enemies[2].hit && !g->enemies[3].hit &&
        !g->shove_cooldown && !g->hurt_timer) {
        /* Daytime exploration needs no actor traversal. Run the loop once
           when the last combat sprite disappears to clear its cached slot. */
        if (!combat_visible)
            return;
        combat_visible = 0;
    } else
        combat_visible = 1;
    enemy = g->enemies;
    count = g->enemy_slots > enemy_slots_cache ? g->enemy_slots : enemy_slots_cache;
    enemy_slots_cache = g->enemy_slots;
    for (i = 0; i < count; ++i, ++enemy) {
        state = enemy->hp ? enemy->kind + 1 : (enemy->hit ? 3 : 0);
        if (enemy->hp) state |= (enemy->state << 3) | ((g->tick & 16) << 1);
        if (enemy->hit && (g->tick & 2))
            state = 0;
        /* A scenery rebuild has already hidden every combat slot. Never
           spend twelve generic OAM calls rewriting hidden daytime actors. */
        if (!state) {
            if (!force && enemy_state_cache[i]) {
                slot = i ? 58 + (i << 1) : 56;
                obj(slot, 0, 240, 0, 0);
                obj(slot + 1, 0, 240, 0, 0);
            }
            if (warning_visible[i]) {
                obj(72 + i, 0, 240, 0, 0);
                warning_visible[i] = 0;
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
        slot = i ? 58 + (i << 1) : 56;
        if (!perspective_project(g, enemy->x, enemy->y, &sx, &sy)) {
            obj(slot, 0, 240, 0, 0);
            obj(slot + 1, 0, 240, 0, 0);
            if (warning_visible[i]) {
                obj(72 + i, 0, 240, 0, 0);
                warning_visible[i] = 0;
            }
        } else {
            /* Breathing, a compressed attack pose and a flashing warning
               use the resident atlas without any additional sprite DMA. */
            if (enemy->state == ENEMY_WINDUP && enemy->hp) {
                obj(72 + i, sx - 8, sy - (enemy->kind ? 32 : 48),
                    (BOW_IMPACT_TILE + ((g->tick & 16) ? 2 : 0)) | 0x0200, 0);
                warning_visible[i] = 1;
            } else if (warning_visible[i]) {
                obj(72 + i, 0, 240, 0, 0);
                warning_visible[i] = 0;
            }
            if (enemy->hp && !enemy->kind) {
                if (enemy->state == ENEMY_WINDUP) sy += 3;
                else if (g->tick & 16) --sy;
                tile = enemy->state == ENEMY_LUNGE ? 0x4000 : 0;
                obj(slot, sx - 8, sy - 32, 268 | tile, 0);
                obj(slot + 1, sx - 8, sy - 16, 270 | tile, 0);
            } else {
                tile = enemy->hp ? (482 | 0x0600 | ((g->tick & 16) ? 0x4000 : 0)) :
                    (BOW_IMPACT_TILE | 0x0200);
                obj(slot, sx - 8, sy - 16, tile, 0);
                obj(slot + 1, 0, 240, 0, 0);
            }
        }
    }
    if (projectiles_visible || g->arrows[0].life || g->arrows[1].life || g->arrows[2].life) {
    projectiles_visible = 0;
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
        if (arrow->life) projectiles_visible = 1;
    }
    }
    if (g->bow_mode && perspective_project(g, g->aim_x, g->aim_y, &sx, &sy)) {
        obj(71, sx - 8, sy - 26, BOW_MARKER_TILE | 0x0200, 0);
        marker_visible = 1;
    } else if (force || marker_visible) {
        if (!force)
            obj(71, 0, 240, 0, 0);
        marker_visible = 0;
    }
    if (g->shove_cooldown > SHOVE_COOLDOWN - 12) {
        sx = g->direction == 0 || g->direction == 4 ? 128 : (g->direction < 4 ? 148 : 108);
        sy = g->direction < 2 || g->direction > 6 ? 124 : (g->direction > 2 && g->direction < 6 ? 164 : 144);
        obj(76, sx - 8, sy - 16, BOW_IMPACT_TILE | 0x0200, 0);
        shove_visible = 1;
    } else if (shove_visible || force) {
        obj(76, 0, 240, 0, 0);
        shove_visible = 0;
    }
    if (g->hurt_timer > 32) {
        obj(77, 120, 132, (BOW_IMPACT_TILE + 2) | 0x0200, 0);
        hurt_visible = 1;
    } else if (hurt_visible || force) {
        obj(77, 0, 240, 0, 0);
        hurt_visible = 0;
    }
}
static void scene_palettes(void) {
    dmaCopyCGram(sky_palettes + ((SkU16)sky << 8), 0, 256);
    dmaCopyCGram(&daylight_actor_palettes + ((SkU16)sky << 6), 192, 64);
    dmaCopyCGram(&daylight_scenery_palettes + ((SkU16)sky << 5), 240, 32);
    dmaCopyCGram(&backdrop_palettes + ((SkU16)sky << 5), 64, 32);
    dmaCopyCGram(&backdrop_palettes + ((SkU16)sky << 5) + 16, 0, 2);
    palette_sky = sky;
}
void perspective_enter(const Game *g) {
    u8 *source, *palette;
    SkU8 room = g->room;
    REG_HDMAEN = 0;
    switch (room) {
    case 0: source = &perspective0_vram; palette = &perspective0_palette; break;
    case 1: source = &perspective1_vram; palette = &perspective1_palette; break;
    case 2: source = &perspective2_vram; palette = &perspective2_palette; break;
    default: source = &perspective3_vram; palette = &perspective3_palette; break;
    }
    sky_palettes = room == 0 ? &daylight0_palettes :
                   (room == 1 ? &daylight1_palettes : palette);
    sky = game_daylight(g);
    setScreenOff();
    dmaCopyVram(source, 0, 32768);
    dmaCopyCGram(palette, 0, 256);
    /* OBJ palettes 4..7 participate in color math; palette 0 stays available
       to the Mode 1 introduction. Both copies use the same authored colors. */
    dmaCopyCGram(&npc_palette, 192, 32);
    npc_enter(g);
    hero_enter();
    /* Seed a complete hero pose while blank. The first full UI upload may
       defer streaming, but must never expose the legacy intro OBJ cells. */
    hero_prepare(g, 0);
    hero_commit();
    torch_enter();
    dmaCopyVram(&bow_tiles, VIDEO_OBJ_TILES + 1024, BOW_TILE_BYTES);
    dmaCopyVram(&scenery_low_tiles, VIDEO_OBJ_TILES + 512, 1024);
    dmaCopyVram(room == 2 ? &chapel_compact_tiles : &scenery_compact_tiles,
                VIDEO_OBJ_TILES + 3584, 1024);
    dmaCopyVram(room == 2 ? &chapel_scenery_tiles : &scenery_tiles,
                VIDEO_OBJ_TILES + 5120, 6144);
    if (room < 2) {
        dmaCopyVram(room ? &backdrop1_tiles : &backdrop0_tiles, 0x4000, 6144);
        dmaCopyVram(room ? &backdrop1_map : &backdrop0_map, 0x4c00, 2048);
    }
    sky_source.mem.p = parallax_table;
    setMode7(0x80);
    REG_BG2SC = 0x4c;
    REG_BG12NBA = 0x40;
    REG_BG2VOFS = 0; REG_BG2VOFS = 0;
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
    /* Only DMA0 and the SDK's DMA7 are mutable during VBlank. Configure the
       six dedicated HDMA channels once; per-frame commits update sources. */
    REG_DMAP1 = 0; REG_BBAD1 = 0x05;
    REG_DMAP2 = 0; REG_BBAD2 = 0x2c;
    REG_DMAP3 = 2; REG_BBAD3 = 0x1b;
    REG_DMAP4 = 2; REG_BBAD4 = 0x1e;
    REG_DMAP5 = 0; REG_BBAD5 = 0;
    REG_DMAP6 = 4; REG_BBAD6 = 0x26;
    parallax_table[0] = 40; parallax_table[2] = 0;
    parallax_table[3] = 24; parallax_table[5] = 0;
    parallax_table[6] = 127; parallax_table[8] = 0;
    parallax_table[9] = 33; parallax_table[11] = 0; parallax_table[12] = 0;
    /* Initial UI, hero and two resident transfers can fill the next VBlank.
       Publish all daylight colors now, while the screen is forced blank. */
    scene_palettes();
    scale_source.mem.p = &perspective_scale;
    light_source.mem.p = light_tables[0];
    layers_source.mem.p = layer_table[0];
    mode_source.mem.p = mode_table[0];
    active_overlay = 0;
    pending_overlay = 0;
    glow_source.mem.p = glow_tables[0];
    old_cut = 255;
    old_sky = 255;
    published_sky = published_lit = 255;
    force_objects = 1;
    /* The first commit publishes the new OAM, text, modes and HDMA together.
       Releasing blank here exposed half-built worlds after journal exits. */
    REG_INIDISP = 0x80;
}
void perspective_leave(void) {
    setScreenOff();
    REG_HDMAEN = 0;
    /* Dedicated Mode1 screens must not inherit combat sprites 64..77. */
    oamClear(0, 0);
    hero_leave();
    npc_leave();
    torch_leave();
    dmaCopyVram(&sprite_tiles + 2048, VIDEO_OBJ_TILES + 1024, BOW_TILE_BYTES);
    dmaCopyVram(&sprite_tiles + 1024, VIDEO_OBJ_TILES + 512, 1024);
    dmaCopyVram(&sprite_tiles + 7168, VIDEO_OBJ_TILES + 3584, 1024);
    dmaCopyVram(&sprite_tiles + 10240, VIDEO_OBJ_TILES + 5120, 6144);
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
    SkU8 i, count, kind, inserted = 0, objects_changed, level, budget, critical_index;
    SkU16 tile;
    SkS16 sx, sy, player_y, object_y, far_actor_y, far_scenery_y;
    const PerspectiveObject *object;
    camera_world_x = PERSPECTIVE_ORIGIN + g->x;
    camera_world_y = PERSPECTIVE_ORIGIN + g->y;
    lit = g->lamp && g->oil;
    sky = game_daylight(g);
    phase = (g->bow_mode ? 16 : ((g->direction & 6) << 1)) | ((g->tick >> 3) & 3);
    moving = previous_x != g->x || previous_y != g->y;
    budget = 34 - (g->enemy_slots << 2);
    if (g->shove_cooldown > SHOVE_COOLDOWN - 12) budget -= 2;
    if (g->hurt_timer > 32) budget -= 2;
    hero_prepare(g, moving);
    npc_prepare(g);
    objects_changed = force_objects || moving || sky != previous_sky || budget != previous_budget || g->bow_mode != previous_bow || g->bow_mode || projectiles_visible;
    if (objects_changed) {
        perspective_clear();
        slots = 0;
        perspective_budget_reset(budget);
        previous_budget = budget;
        count = perspective_counts[g->room];
        object = perspective_objects[g->room];
        player_y = g->y;
        far_actor_y = player_y - 112;
        far_scenery_y = player_y - 180;
        /* Cover the union of every held/planted light position. Turning the
           torch changes only PPU windows, never scenery membership or LOD. */
        cull_left = sky ? -32 : (g->room == 0 ? (g->bow_mode ? -8 : 2) : (g->bow_mode ? 8 : 18));
        cull_right = sky ? 287 : (g->room == 0 ? (g->bow_mode ? 220 : 254) : (g->bow_mode ? 204 : 238));
        /* Allocate houses, then people, before optional clutter. Keep emission
           in depth order: allocation priority must not change occlusion. */
        for (i = 0; i < COMBAT_ARROWS; ++i) {
            if (g->arrows[i].life && perspective_project(g, g->arrows[i].x >> 2,
                    g->arrows[i].y >> 2, &sx, &sy))
                perspective_reserve(sy - 30, sy - 15, 2);
        }
        if (g->bow_mode && perspective_project(g, g->aim_x, g->aim_y, &sx, &sy))
            perspective_reserve(sy - 26, sy - 11, 2);
        for (critical_index = 0; critical_index < 6; ++critical_index) {
            i = perspective_critical_indices[g->room][critical_index];
            if (i == 255) break;
            critical_plan[i] = 0;
            object = perspective_objects[g->room] + i;
            kind = object->kind & 0x7f;
            if (object->y < player_y - (kind == 4 ? 180 : 112)) continue;
            if (!perspective_project_object(object, &sx, &sy)) continue;
            if (sx < cull_left || sx > cull_right) continue;
            level = perspective_lod(kind, sy);
            if (!level) continue;
            critical_plan[i] = level | (critical_index << 2);
            critical_x[critical_index] = sx;
            critical_y[critical_index] = sy;
        }
        object = perspective_objects[g->room];
        for (i = 0; i < count; ++i, ++object) {
            object_y = object->y;
            if (!inserted && object_y < player_y) {
                player();
                inserted = 1;
            }
            kind = object->kind & 0x7f;
            if (object_y < far_actor_y) {
                if (kind != 1 && kind != 4 && kind != 6) continue;
                if (object_y < far_scenery_y) continue;
            }
            if (kind == 0 || kind == 4) {
                level = critical_plan[i];
                if (!level) continue;
                critical_index = level >> 2;
                level &= 3;
                sx = critical_x[critical_index];
                sy = critical_y[critical_index];
            } else {
                if (!perspective_project_object(object, &sx, &sy)) continue;
                if (sx < cull_left || sx > cull_right) continue;
                level = perspective_lod(kind, sy);
            }
            if (!level) continue;
            --level;
            if (kind == 0) {
                tile = object->tile;
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 32 + (tile << 1), 0);
                else {
                    tile = tile == 1 || tile == 4 ? 288 : 256;
                    perspective_npc(slots, sx - 16, sy - 48, tile);
                    slots += 6;
                }
            } else if (kind == 1) {
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 448 | 0x0600, 0);
                else if (level == 1)
                    obj(slots++, sx - 16, sy - 32, 392 | 0x0600, 1);
                else {
                    /* The HUD starts at176. Do not emit cells that lie wholly
                       below it; their visible silhouette is unchanged. */
                    if (sy >= 240) continue;
                    obj(slots++, sx - 16, sy - 64, 384 | 0x0600, 1);
                    if (sy < 208)
                        obj(slots++, sx - 16, sy - 32, 388 | 0x0600, 1);
                }
            } else if (kind == 6) {
                /* Upright timber columns share world-space feet with the
                   Mode 7 foundation; two cells preserve their 32x64 height. */
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 450 | 0x0600, 0);
                else if (level == 1)
                    obj(slots++, sx - 16, sy - 32, 392 | 0x0600, 1);
                else {
                    obj(slots++, sx - 16, sy - 64, object->tile | 0x0600, 1);
                    obj(slots++, sx - 16, sy - 32, (object->tile + 8) | 0x0600, 1);
                }
            } else if (kind == 3) {
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 488 | 0x0600, 0);
                else
                    obj(slots++, sx - 16, sy - 32, object->tile | 0x0600, 1);
            } else if (kind == 4) {
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 450 | 0x0600, 0);
                else if (level == 1) {
                    perspective_quad(slots, sx - 16, sy - 32, 224 | 0x0600, 0);
                    slots += 4;
                } else {
                    perspective_quad(slots, sx - 32, sy - 64, 320 | 0x0600, 1);
                    slots += 4;
                }
            } else if (kind == 5) {
                if (!level)
                    obj(slots++, sx - 8, sy - 16, 494 | 0x0600, 0);
                else {
                    perspective_quad(slots, sx - 16, sy - 32, 232 | 0x0600, 0);
                    slots += 4;
                }
            } else
                obj(slots++, sx - 8, sy - 16, object->tile | 0x0600, 0);
        }
        if (!inserted)
            player();
        previous_x = g->x;
        previous_y = g->y;
        previous_bow = g->bow_mode;
        previous_sky = sky;
        force_objects = 0;
    }
    /* Avoid even the combat function's stack frame and cold actor probes on
       a sunlit walk. Existing arrows and fading enemies keep it scheduled. */
    if (g->enemy_active || g->bow_mode || combat_visible ||
        g->shove_cooldown > SHOVE_COOLDOWN - 12 || g->hurt_timer > 32)
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
    case 176: glow = 6; break;
    case 192: glow = 7; break;
    }
    light_source.mem.p = light_tables[phase];
    glow_source.mem.p = sky ? &perspective_sky_brightness : glow_tables[(phase << 3) + glow];
    old_phase = phase;
    if (cut == old_cut && lit == old_lit && sky == old_sky)
        return;
    old_cut = cut;
    old_lit = lit;
    old_sky = sky;
    if (sky && cut > 88) {
        mode_table[next][i++] = 88; mode_table[next][i++] = 9;
        if (cut - 88 > 127) {
            mode_table[next][i++] = 127; mode_table[next][i++] = 7;
            mode_table[next][i++] = cut - 215; mode_table[next][i++] = 7;
        } else {
            mode_table[next][i++] = cut - 88; mode_table[next][i++] = 7;
        }
    } else if (cut >= 127) {
        mode_table[next][i++] = 127; mode_table[next][i++] = 7;
        mode_table[next][i++] = cut - 127; mode_table[next][i++] = 7;
    } else {
        mode_table[next][i++] = cut; mode_table[next][i++] = sky ? 9 : 7;
    }
    mode_table[next][i++] = 1; mode_table[next][i++] = 9; mode_table[next][i] = 0;
    i = 0;
    if (sky) {
        layer_table[next][i++] = cut < 88 ? cut : 88; layer_table[next][i++] = 0x12;
        if (cut > 88) {
            if (cut - 88 > 127) {
                layer_table[next][i++] = 127; layer_table[next][i++] = floor;
                layer_table[next][i++] = cut - 215; layer_table[next][i++] = floor;
            } else {
                layer_table[next][i++] = cut - 88; layer_table[next][i++] = floor;
            }
        }
    } else {
        layer_table[next][i++] = cut < 48 ? cut : 48; layer_table[next][i++] = 0;
        if (cut > 48) {
            if (cut - 48 > 127) {
                layer_table[next][i++] = 127; layer_table[next][i++] = floor;
                layer_table[next][i++] = cut - 175; layer_table[next][i++] = floor;
            } else {
                layer_table[next][i++] = cut - 48; layer_table[next][i++] = floor;
            }
        }
    }
    layer_table[next][i++] = 1; layer_table[next][i++] = 4; layer_table[next][i] = 0;
    pending_overlay = next + 1;
}
void perspective_commit(SkU8 full_ui) {
    SkU16 hofs = camera_world_x - 128, vofs = camera_world_y - PERSPECTIVE_ANCHOR;
    SkU8 shade;
    /* A full text map consumes this blank's streaming budget. Otherwise one
       1 KiB actor upload at most; pending NPC poses carry into the next blank. */
    if (!full_ui && !hero_commit())
        npc_commit();
    if (!full_ui)
        torch_commit();
    if (!full_ui && sky != palette_sky) {
        scene_palettes();
    }
    if (sky != published_sky || lit != published_lit) {
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
        published_sky = sky;
        published_lit = lit;
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
    REG_A1T1LH = mode_source.mem.c.addr; REG_A1B1 = mode_source.mem.c.bank;
    REG_A1T3LH = scale_source.mem.c.addr; REG_A1B3 = scale_source.mem.c.bank;
    REG_A1T4LH = scale_source.mem.c.addr; REG_A1B4 = scale_source.mem.c.bank;
    REG_A1T2LH = layers_source.mem.c.addr; REG_A1B2 = layers_source.mem.c.bank;
    /* A single four-register transfer publishes both concentric windows. */
    REG_A1T6LH = light_source.mem.c.addr; REG_A1B6 = light_source.mem.c.bank;
    REG_A1T5LH = glow_source.mem.c.addr; REG_A1B5 = glow_source.mem.c.bank;
    parallax_table[1] = (camera_world_x - PERSPECTIVE_ORIGIN) >> 4;
    parallax_table[4] = (camera_world_x - PERSPECTIVE_ORIGIN) >> 3;
    parallax_table[7] = (camera_world_x - PERSPECTIVE_ORIGIN) >> 2;
    parallax_table[10] = parallax_table[7];
    /* PVSnesLib's NMI owns DMA7 for OAM. Never enable HDMA on that channel:
       Mesen/hardware can corrupt sprites even if we restore it after NMI.
       DMA0 is available between commits and is disabled before text uploads. */
    REG_DMAP0 = 2; REG_BBAD0 = 0x0f;
    REG_A1T0LH = sky_source.mem.c.addr; REG_A1B0 = sky_source.mem.c.bank;
    REG_TM = 0;
    REG_WH0 = 255; REG_WH1 = 0;
    REG_WH2 = 255; REG_WH3 = 0;
    REG_HDMAEN = sky ? 0x7f : 0x7e;
    REG_INIDISP = 15;
    if (!(REG_HVBJOY & 0x80))
        ++video_late_commits;
}
