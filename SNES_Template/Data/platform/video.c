#include <snes.h>
#include <string.h>
#include "../include/platform.h"
#include "../include/ui_text.h"
#include "../include/perspective.h"
extern u8 bg0_tiles, bg0_tiles_end, bg0_map;
extern u8 bg1_tiles, bg1_tiles_end, bg1_map, bg1_palette;
extern u8 menu_torch_tiles;
extern u8 journal_tiles, journal_tiles_end, journal_map, journal_palette;
extern u8 intro_actor0, intro_actor1, intro_actor2, intro_actor3;
extern u8 intro_actor4, intro_actor5, intro_actor6, intro_actor7;
static u8 *const intro_actors[8] = {&intro_actor0,&intro_actor1,&intro_actor2,&intro_actor3,
                                  &intro_actor4,&intro_actor5,&intro_actor6,&intro_actor7};
static SkU8 intro_pose = 0, intro_uploaded = 255;
#define SPLASH_FRAME(n) extern u8 splash_frame##n;
SPLASH_FRAME(0) SPLASH_FRAME(1) SPLASH_FRAME(2) SPLASH_FRAME(3)
SPLASH_FRAME(4) SPLASH_FRAME(5) SPLASH_FRAME(6) SPLASH_FRAME(7)
SPLASH_FRAME(8) SPLASH_FRAME(9) SPLASH_FRAME(10) SPLASH_FRAME(11)
SPLASH_FRAME(12) SPLASH_FRAME(13) SPLASH_FRAME(14) SPLASH_FRAME(15)
SPLASH_FRAME(16) SPLASH_FRAME(17) SPLASH_FRAME(18) SPLASH_FRAME(19)
SPLASH_FRAME(20) SPLASH_FRAME(21) SPLASH_FRAME(22) SPLASH_FRAME(23)
SPLASH_FRAME(24) SPLASH_FRAME(25) SPLASH_FRAME(26) SPLASH_FRAME(27)
SPLASH_FRAME(28) SPLASH_FRAME(29) SPLASH_FRAME(30) SPLASH_FRAME(31)
static u8 *const splash_frames[32] = {
    &splash_frame0, &splash_frame1, &splash_frame2, &splash_frame3,
    &splash_frame4, &splash_frame5, &splash_frame6, &splash_frame7,
    &splash_frame8, &splash_frame9, &splash_frame10, &splash_frame11,
    &splash_frame12, &splash_frame13, &splash_frame14, &splash_frame15,
    &splash_frame16, &splash_frame17, &splash_frame18, &splash_frame19,
    &splash_frame20, &splash_frame21, &splash_frame22, &splash_frame23,
    &splash_frame24, &splash_frame25, &splash_frame26, &splash_frame27,
    &splash_frame28, &splash_frame29, &splash_frame30, &splash_frame31
};
extern u8 bg2_tiles, bg2_tiles_end, bg2_map;
extern u8 bg3_tiles, bg3_tiles_end, bg3_map;
extern u8 bg4_tiles, bg4_tiles_end, bg4_map;
extern u8 bg5_tiles, bg5_tiles_end, bg5_map;
extern u8 bg2_dim, bg3_dim, bg4_dim, bg5_dim, ambient_palette;
extern u8 bg2_palette, bg3_palette, bg4_palette, bg5_palette;
extern u8 cine0_tiles, cine0_tiles_end, cine0_map, cine0_palette;
extern u8 cine1_tiles, cine1_tiles_end, cine1_map, cine1_palette;
extern u8 cine2_tiles, cine2_tiles_end, cine2_map, cine2_palette;
extern u8 sprite_tiles, sprite_tiles_end, sprite_palette, bg_palette, font_tiles, font_tiles_end;
extern u8 daycycle_notices;
extern u8 exploration_hud;
extern u8 hud_clocks, hud_numbers;
extern u8 bow_hud_maps, bow_status_maps, bow_wait_tiles;
static SkU8 bow_status_cache = 255;
extern u8 interaction0_maps, interaction1_maps, interaction2_maps, interaction3_maps;
extern u8 interaction_notice_maps;
static u8 *context_maps;
/* UI buckets live in ROM, avoiding 65C816 software division per draw. */
static const SkU8 bucket5[121] = {
    0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  3,  3,  3,  3,  3,  4,
    4,  4,  4,  4,  5,  5,  5,  5,  5,  6,  6,  6,  6,  6,  7,  7,  7,  7,  7,  8,  8,
    8,  8,  8,  9,  9,  9,  9,  9,  10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 12, 12,
    12, 12, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16,
    16, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20,
    21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 24};
static const SkU8 bucket10[61] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
                                  2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4,
                                  4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6};
static SkU16 text_map[VIDEO_TEXT_ENTRIES];
static SkU8 current_bg = 255, dirty = 1, redraw = 1;
static SkU8 menu_torch_frame = 0, menu_torch_uploaded = 0;
static SkU8 splash_frame = 0, splash_uploaded = 0;
static SkU16 menu_torch_vram = 0;
static SkU16 last_keys[10] = {65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535};
static SkS16 previous_x = 0, previous_y = 0, previous_enemy_x = 0, previous_enemy_y = 0;
/* Applied in VBlank: splash and cinematic transitions use master brightness. */
static SkU8 brightness = 15, scene_age = 0;
static SkU16 camera_x = 0;
static SkU8 calibration_stage = 255;
static SkS16 calibration_x = -1, calibration_y = -1;
static SkU8 time_banner = 255;
static SkU8 banner_dirty = 0;
static void ui_tile(SkU8 x, SkU8 y, SkU16 tile) {
    text_map[(SkU16)y * 32 + x] = tile | (7 << 10) | BG_TIL_PRIO;
}
static void panel(SkU8 row, SkU8 count) {
    SkU16 i, end = (SkU16)(row + count) * 32;
    SkU8 x, y, bottom;
    if (!redraw)
        return;
    if (end > VIDEO_TEXT_ENTRIES)
        end = VIDEO_TEXT_ENTRIES;
    for (i = (SkU16)row * 32; i < end; ++i)
        text_map[i] = 256 | (7 << 10) | BG_TIL_PRIO;
    bottom = (SkU8)(end / 32 - 1);
    for (x = 1; x < 31; ++x) {
        ui_tile(x, row, 261);
        ui_tile(x, bottom, 262);
    }
    for (y = row + 1; y < bottom; ++y) {
        ui_tile(0, y, 263);
        ui_tile(31, y, 264);
    }
    ui_tile(0, row, 265);
    ui_tile(31, row, 266);
    ui_tile(0, bottom, 267);
    ui_tile(31, bottom, 268);
}
static void text_n(SkU8 x, SkU8 y, const char *value, SkU16 limit) {
    SkU8 start = x, ch;
    if (!redraw || !value)
        return;
    while (*value && y < 28 && limit) {
        --limit;
        ch = (SkU8)*value++;
        if (ch == 10) {
            x = start;
            ++y;
            continue;
        }
        if (x < 32)
            text_map[(SkU16)y * 32 + x] = ch | (7 << 10) | BG_TIL_PRIO;
        ++x;
    }
}
static void text(SkU8 x, SkU8 y, const char *value) {
    text_n(x, y, value, 65535);
}
static void number(SkU8 x, SkU8 y, SkU16 value) {
    char out[6], tmp;
    SkU8 i = 0, j;
    if (!redraw)
        return;
    do {
        out[i++] = '0' + value % 10;
        value /= 10;
    } while (value && i < 5);
    out[i] = 0;
    for (j = 0; j < i / 2; ++j) {
        tmp = out[j];
        out[j] = out[i - j - 1];
        out[i - j - 1] = tmp;
    }
    text(x, y, out);
}
static void draw_clock(SkU8 x, SkU8 y, const Game *g) {
    SkU8 hour = g->day_seconds >> 5;
    SkU8 minute = ((g->day_seconds & 31) * 60) >> 5, i, digit;
    char value[6];
    if (!redraw)
        return;
    value[0] = '0' + hour / 10;
    value[1] = '0' + hour % 10;
    value[2] = ':';
    value[3] = '0' + minute / 10;
    value[4] = '0' + minute % 10;
    value[5] = 0;
    for (i = 0; i < 5; ++i) {
        digit = value[i] == ':' ? 10 : value[i] - '0';
        ui_tile(x+i, y, 273 + digit*2);
        ui_tile(x+i, y+1, 274 + digit*2);
    }
}
static void tint(SkU8 x, SkU8 y, SkU8 width, SkU8 rows, SkU8 palette) {
    SkU8 dx, dy;
    SkU16 *tile;
    if (!redraw) return;
    for (dy = 0; dy < rows; ++dy)
        for (dx = 0; dx < width; ++dx) {
            tile = text_map + (SkU16)(y+dy)*32 + x+dx;
            if (*tile) *tile = (*tile & 0xe3ff) | ((SkU16)palette << 10);
        }
}
static void journal_meter(SkU8 x, SkU8 y, SkU8 amount) {
    SkU8 i, full = (amount + 19) / 20;
    if (!redraw) return;
    for (i = 0; i < 6; ++i)
        text_map[(SkU16)y*32+x+i] = (i < full ? 271 : 272) | (6 << 10) | BG_TIL_PRIO;
}
static void text_box(SkU8 x, SkU8 y, const char *value, SkU8 width, SkU8 rows, SkU8 flow) {
    SkU8 column = 0, row = 0, length, i;
    if (!redraw || !value)
        return;
    while (*value && row < rows) {
        if (*value == '\n') {
            if (flow) { ++value; if (column && column < width) ++column; continue; }
            ++value; ++row; column = 0;
            continue;
        }
        length = 0;
        while (value[length] && value[length] != ' ' && value[length] != '\n')
            ++length;
        if (length && column && column + length > width) {
            ++row; column = 0;
            if (row == rows) break;
        }
        if (!length) {
            ++value;
            if (column && column < width) ++column;
            continue;
        }
        for (i = 0; i < length; ++i) {
            if (column >= width) { ++row; column = 0; }
            if (row == rows) return;
            ui_tile(x + column++, y + row, (SkU8)*value++);
        }
    }
}
static void background(SkU8 id) {
    u8 *tiles = 0, *end = 0, *map = 0, *dim = 0, *palette = &bg_palette;
    SkU16 palette_bytes = 32, map_bytes = 2048;
    SkU8 map_size = SC_32x32;
    if (current_bg == id)
        return;
    if (current_bg >= 10 && current_bg <= 13)
        perspective_leave();
    switch (id) {
    case 14:
        tiles = &journal_tiles;
        end = &journal_tiles_end;
        map = &journal_map;
        palette = &journal_palette;
        palette_bytes = 64;
        break;
    case 0:
        tiles = &bg0_tiles;
        end = &bg0_tiles_end;
        map = &bg0_map;
        /* Studio card and menu use the same night/bronze palette. */
        palette = &bg1_palette;
        palette_bytes = 256;
        splash_frame = splash_uploaded = 0;
        break;
    case 1:
        tiles = &bg1_tiles;
        end = &bg1_tiles_end;
        map = &bg1_map;
        palette = &bg1_palette;
        palette_bytes = 256;
        /* The last ten background tiles belong exclusively to the flame. */
        menu_torch_vram = VIDEO_BG_TILES +
            ((&bg1_tiles_end - &bg1_tiles - VIDEO_MENU_TORCH_BYTES) >> 1);
        menu_torch_frame = menu_torch_uploaded = 0;
        break;
    case 2:
        tiles = &bg2_tiles;
        end = &bg2_tiles_end;
        map = &bg2_map;
        dim = &bg2_dim;
        palette = &bg2_palette;
        palette_bytes = 256;
        break;
    case 3:
        tiles = &bg3_tiles;
        end = &bg3_tiles_end;
        map = &bg3_map;
        dim = &bg3_dim;
        palette = &bg3_palette;
        palette_bytes = 256;
        break;
    case 4:
        tiles = &bg4_tiles;
        end = &bg4_tiles_end;
        map = &bg4_map;
        dim = &bg4_dim;
        palette = &bg4_palette;
        palette_bytes = 256;
        break;
    case 6:
        map_bytes = 4096;
        map_size = SC_64x32;
        tiles = &cine0_tiles;
        end = &cine0_tiles; /* A full LoROM bank has no 16-bit end pointer. */
        map = &cine0_map;
        palette = &cine0_palette;
        palette_bytes = 256;
        break;
    case 7:
        tiles = &cine1_tiles;
        end = &cine1_tiles_end;
        map = &cine1_map;
        palette = &cine1_palette;
        palette_bytes = 256;
        break;
    case 8:
        tiles = &cine2_tiles;
        end = &cine2_tiles_end;
        map = &cine2_map;
        palette = &cine2_palette;
        palette_bytes = 256;
        break;
    case 9:
        tiles = &bg2_tiles;
        end = &bg2_tiles_end;
        map = &bg2_map;
        palette = &bg2_palette;
        palette_bytes = 256;
        break;
    default:
        tiles = &bg5_tiles;
        end = &bg5_tiles_end;
        map = &bg5_map;
        dim = &bg5_dim;
        palette = &bg5_palette;
        palette_bytes = 256;
        break;
    }
    setScreenOff();
    REG_HDMAEN = 0;
    if (id == 6) {
        dmaCopyVram(&intro_actor0, VIDEO_OBJ_TILES, 1024);
        dmaCopyCGram(&sprite_palette, 128, 32);
        intro_uploaded = intro_pose = 0;
    }
    bgInitTileSet(0, tiles, palette, 0, id == 6 ? 32768 : end - tiles, palette_bytes,
                  BG_16COLORS, VIDEO_BG_TILES);
    bgInitMapSet(0, map, map_bytes, map_size, VIDEO_BG_MAP);
    bgSetScroll(0, 0, -1);
    bgSetDisable(1);
    if (dim) {
        bgSetGfxPtr(1, VIDEO_BG_TILES);
        bgInitMapSet(1, dim, 2048, SC_32x32, VIDEO_AMBIENT_MAP);
        bgSetScroll(1, 0, -1);
    }
    setPaletteColor(0, 0);
    if (id != 14) {
        setPaletteColor(29, RGB5(28, 28, 24));
        setPaletteColor(30, RGB5(1, 2, 3));
        setPaletteColor(31, RGB5(29, 24, 15));
    } else {
        setMode(BG_MODE1, BG3_MODE1_PRIORITY_HIGH);
        REG_TM = 0x05; /* Journal artwork + text only; no leftover actors. */
    }
    setPaletteColor(142, RGB5(31, 13, 2));
    current_bg = id;
    scene_age = 0;
    /* Keep the first card dark while the initial draw prepares its reveal. */
    if (id == 14)
        REG_INIDISP = 0x80; /* Publish the complete journal text before reveal. */
    else if (id == 0)
        REG_INIDISP = 0;
    else
        setScreenOn();
}
static void sprite(SkU8 id, SkS16 x, SkS16 y, SkU16 tile) {
    oamSet((SkU16)id * 4, x, y, 2, 0, 0, tile, 0);
    oamSetEx((SkU16)id * 4, OBJ_SMALL, OBJ_SHOW);
}
static void actor(SkU8 top, SkU8 bottom, SkS16 x, SkS16 y, SkU16 tile) {
    sprite(top, x, y, tile);
    sprite(bottom, x, y + 16, tile + 32);
}
static void hide(void) {
    SkU8 i;
    for (i = 0; i < VIDEO_ACTOR_SLOTS; ++i)
        oamSetVisible((SkU16)i * 4, OBJ_HIDE);
}
void video_init(void) {
    setScreenOff();
    /* Initialize all PPU map rows, including the four rows omitted from DMA. */
    dmaClearVram();
    oamClear(0, 0);
    dmaCopyVram(&font_tiles, VIDEO_FONT_TILES, &font_tiles_end - &font_tiles);
    bgSetGfxPtr(2, VIDEO_FONT_TILES);
    bgSetMapPtr(2, VIDEO_TEXT_MAP, SC_32x32);
    bgSetScroll(2, 0, -1);
    oamInitGfxSet(&sprite_tiles, &sprite_tiles_end - &sprite_tiles, &sprite_palette, 32, 0,
                  VIDEO_OBJ_TILES, OBJ_SIZE16_L32);
    setMode(BG_MODE1, BG3_MODE1_PRIORITY_HIGH);
    bgSetDisable(1);
    bgSetEnable(0);
    bgSetEnable(2);
    dmaCopyCGram(&ambient_palette, 32, 32);
    setPaletteColor(29, RGB5(28, 28, 24));
    setPaletteColor(30, RGB5(1, 2, 3));
    setPaletteColor(31, RGB5(29, 24, 15));
}
void video_commit(void) {
    SkU8 full_ui = dirty && !banner_dirty;
    /* DMA0 is also the outdoor parallax HDMA channel. Stop HDMA before any
       normal transfer, then perspective_commit publishes the next frame. */
    REG_HDMAEN = 0;
    if (current_bg == 0 && splash_frame != splash_uploaded) {
        dmaCopyVram(splash_frames[splash_frame], VIDEO_BG_MAP, 2048);
        splash_uploaded = splash_frame;
    }
    if (current_bg == 1 && menu_torch_frame != menu_torch_uploaded) {
        dmaCopyVram(&menu_torch_tiles + (SkU16)menu_torch_frame * VIDEO_MENU_TORCH_BYTES,
                    menu_torch_vram, VIDEO_MENU_TORCH_BYTES);
        menu_torch_uploaded = menu_torch_frame;
    }
    if (current_bg == 6 && !full_ui && intro_pose != intro_uploaded) {
        dmaCopyVram(intro_actors[intro_pose], VIDEO_OBJ_TILES, 1024);
        intro_uploaded = intro_pose;
    }
    if (dirty) {
        if (banner_dirty)
            dmaCopyVram((u8 *)text_map + 23 * 64, VIDEO_TEXT_MAP + 23 * 32, 4 * 64);
        else
            dmaCopyVram((u8 *)text_map, VIDEO_TEXT_MAP, sizeof(text_map));
        dirty = 0;
        banner_dirty = 0;
    }
    if (current_bg >= 10 && current_bg <= 13) {
        perspective_commit(full_ui);
        return;
    }
    flashlight_commit();
    if (current_bg == 6)
        bgSetScroll(0, camera_x, -1);
    REG_INIDISP = brightness;
}
static const char *notice_text(SkU8 notice) {
    switch (notice) {
    case 1:
        return TXT_OIL_OK;
    case 2:
        return TXT_WRONG;
    case 3:
        return TXT_FOREST_NEED;
    case 4:
        return TXT_CHAPEL_NEED;
    case 5:
        return TXT_CHARGE;
    case 6:
        return TXT_PUZZLE_WRONG;
    case 7:
        return TXT_ECHO_WAIT;
    case 8:
        return TXT_WARD_OK;
    case 9:
        return TXT_WARD_EMPTY;
    case 10:
        return TXT_WARD_NEED;
    case 11:
        return TXT_BELL_WRONG;
    case 12: return TXT_FOREST_DONE;
    case 13: return TXT_SIGN_ONE;
    case 14: return TXT_SIGN_TWO;
    case 15: return TXT_RUNE_DONE;
    case 16: return TXT_TABLE_DONE;
    case 17: return TXT_APPROACH;
    case 18: return TXT_TABLE_NEED;
    case 19: return TXT_TOKEN_NEED;
    case 20: return TXT_MIRO_NEED;
    case 21: return TXT_SIGN_ORDER;
    case 22: return TXT_RUNE_WAIT;
    case 23: return TXT_RUNES_NEED;
    default:
        return 0;
    }
}
static void draw_actors(const Game *g) {
    SkU8 i, facing;
    SkU16 tile;
    const Hotspot *h;
    facing = g->direction < 2 ? 0 : (g->direction < 4 ? 1 : (g->direction < 6 ? 2 : 3));
    tile = 96 + facing * 4;
    if (((g->tick >> 3) & 1) && (g->x != previous_x || g->y != previous_y))
        tile += 2;
    sprite(0, g->x - 8, g->y - 20, tile);
    sprite(10, g->x - 8, g->y - 4, tile + 32);
    if (!(g->flags & F_CHAPEL))
        sprite(9, g->x - 5, g->y + 6, 76);
    else
        oamSetVisible(9 * 4, OBJ_HIDE);
    if (g->room == 0) {
        actor(1, 6, 48, 58, 256);
        actor(2, 7, 182, 92, 258);
    }
    if (g->room == 1)
        actor(1, 6, 176, 56, 260);
    if (g->room == 2) {
        actor(1, 6, 40, 68, 262);
        actor(2, 7, 190, 68, 264);
    }
    if (g->room == 3) {
        actor(1, 6, 184, 62, 260);
        for (i = 0; i < 3; ++i)
            if (g->rune_mask & (1 << i)) {
                h = game_hotspot(3, i + 2);
                sprite(3 + i, h->x - 8, h->y - 8, 38);
            }
    }
    if (g->enemy_active)
        actor(8, 11, g->enemy_x - 8, g->enemy_y - 20, 266);
    previous_x = g->x;
    previous_y = g->y;
    previous_enemy_x = g->enemy_x;
    previous_enemy_y = g->enemy_y;
}
static void draw_kirill(SkS16 x, SkS16 y, SkU8 flip) {
    SkU8 i, column;
    for (i = 0; i < 6; ++i) {
        column = flip ? 1-(i&1) : (i&1);
        oamSet(i*4, x-16+column*16, y-48+(i>>1)*16, 2, flip, 0, i*2, 0);
        oamSetEx(i*4, OBJ_SMALL, OBJ_SHOW);
    }
}
static void draw_coin(SkS16 x, SkS16 feet, SkU16 roll) {
    /* A coin rolls on its rim: the face keeps its outline while the stamped
       mark rotates. One-pixel hops follow the uneven floor. */
    sprite(8, x - 8, feet - 15 - ((roll & 7) == 3), 64 + ((roll >> 2) & 3) * 2);
}
static void draw_corridor(const Game *g) {
    SkS16 scroll = game_corridor_scroll(g);
    intro_pose = g->x == previous_x ? 0 : 1 + (g->tick / 6) % 7;
    hide();
    camera_x = scroll;
    draw_kirill(g->x-scroll, g->y, g->direction == 6);
    if (g->x < CORRIDOR_END - 12)
        draw_coin(g->x + 26 - scroll, g->y, g->x - CORRIDOR_START);
    previous_x = g->x;
}
static void draw_cinematic(const Game *g) {
    hide();
    if (g->dialogue != D_PROLOG)
        return;
    if (g->page == 0) {
        SkU16 roll = g->tick < 104 ? g->tick : 104;
        camera_x = game_corridor_scroll(g);
        intro_pose = g->x > CORRIDOR_START && g->tick < 128 ? 1 + (g->tick / 6) % 7 : 0;
        draw_kirill(g->x - camera_x, 110, 0);
        draw_coin(CORRIDOR_START + 26 + roll - camera_x, 110, roll);
    }
}
static void draw_torch(const Game *g) {
    static const SkS8 drift[8] = {0, 1, 2, 1, 0, -1, -2, -1};
    SkU8 i, age, lit = g->lamp && g->oil;
    SkS16 x = g->x + 2, y = g->y - 18;
    sprite(12, x, y, lit ? 160 + ((g->tick >> 2) & 3) * 2 : 174);
    for (i = 0; i < 5; ++i) {
        age = (SkU8)((g->tick + i * 6) & 31);
        if (!lit || age > 28) {
            oamSetVisible((SkU16)(13 + i) * 4, OBJ_HIDE);
            continue;
        }
        sprite(13 + i, x + drift[(age >> 2) & 7] * 2 - 2 + (i & 1) * 3,
               y - age - 4, age < 10 ? 168 : (age < 20 ? 170 : 172));
    }
}
void video_draw(const Game *g, SkU8 scope) {
    SkU8 i, bg, near, changed, world, cinematic, corridor, projected, cut, bow_status, status_changed;
    SkU16 keys[10];
    const StoryLine *line;
    calibration_stage = 255;
    if (g->mode == G_EXPLORE) {
        if (current_bg != 10 + g->room) {
            hide();
            perspective_enter(g);
            current_bg = 10 + g->room;
            memset(last_keys, 255, sizeof(last_keys));
            time_banner = 255;
        }
        if (time_banner == 255) {
            context_maps = g->room == 0 ? &interaction0_maps :
                (g->room == 1 ? &interaction1_maps : (g->room == 2 ? &interaction2_maps : &interaction3_maps));
        }
        perspective_draw(g);
        i = g->notice_ticks && g->notice ? 160 + g->notice :
            (g->time_notice ? g->time_phase : (g->bow_mode ? 32 + g->ammo + (scope ? 25 : 0) :
            (g->focus != SK_NONE ? 96 + (g->room << 4) + g->focus : 254)));
        bow_status = 0;
        if (g->bow_mode) {
            bow_status = !g->ammo ? 7 : (g->hurt_timer > 32 ? 6 :
            (g->shove_cooldown > SHOVE_COOLDOWN - 12 ? 5 : (g->bow_cooldown ? 4 :
            (g->bow_draw >= BOW_DRAW_TICKS ? 3 : (g->bow_draw >= 12 ? 2 :
            (g->bow_draw >= BOW_MIN_DRAW ? 1 : 0))))));
            if (g->shove_cooldown) bow_status |= 128;
        }
        status_changed = time_banner == 255 || last_keys[0] != (g->oil | ((SkU16)g->fear << 8)) ||
                         last_keys[1] != g->day_seconds;
        if (i != time_banner || status_changed ||
            (g->bow_mode && i >= 32 && i < 82 && bow_status != bow_status_cache)) {
            banner_dirty = !dirty && time_banner != 255;
            if (time_banner == 255) {
                memset(text_map, 0, sizeof(text_map));
                memcpy(text_map + 22 * 32, &exploration_hud, 6 * 64);
            } else
                memcpy(text_map + 25 * 32, &exploration_hud + 3 * 64, 2 * 64);
            time_banner = i;
            dirty = 1;
            redraw = 1;
            if (status_changed) {
                memcpy(text_map + 23 * 32, &exploration_hud + 64, 64);
                last_keys[0] = g->oil | ((SkU16)g->fear << 8);
                last_keys[1] = g->day_seconds;
                memcpy(text_map + 23 * 32 + 8, &hud_numbers + (SkU16)g->oil * 6, 6);
                memcpy(text_map + 23 * 32 + 19, &hud_numbers + (SkU16)g->fear * 6, 6);
                memcpy(text_map + 23 * 32 + 25, &hud_clocks + g->day_seconds * 10, 10);
            }
            if (i >= 160 && i < 192)
                memcpy(text_map + 25 * 32, &interaction_notice_maps + ((SkU16)g->notice << 8) + 64, 2 * 64);
            else if (i >= 96 && i < 160)
                memcpy(text_map + 25 * 32, context_maps + ((SkU16)g->focus << 8) + 64, 2 * 64);
            else if (g->time_notice)
                memcpy(text_map + 25 * 32, &daycycle_notices + (SkU16)g->time_phase * 192 + 64, 64);
            else if (g->bow_mode) {
                memcpy(text_map + 25 * 32, &bow_status_maps + ((SkU16)(bow_status & 7) << 6), 64);
                memcpy(text_map + 26 * 32, &bow_hud_maps + (SkU16)(i - 32) * 192 + 64, 64);
                if (g->ammo && g->shove_cooldown)
                    memcpy(text_map + 26 * 32 + (scope ? 24 : 22), &bow_wait_tiles, 12);
            }
            bow_status_cache = bow_status;
        }
        perspective_overlay(176);
        return;
    }
    time_banner = 255;
    projected = (g->mode >= G_DIALOGUE && g->mode <= G_PAUSE) || g->mode == G_BELL;
    if (g->mode == G_JOURNAL)
        projected = 0;
    if (g->mode == G_DIALOGUE && ((g->dialogue == D_PROLOG && g->page < 3) || g->dialogue == D_MODERN))
        projected = 0;
    if (g->mode == G_PAUSE && g->return_mode == G_CORRIDOR)
        projected = 0;
    if (g->mode == G_PAUSE && g->return_mode == G_DIALOGUE &&
        ((g->dialogue == D_PROLOG && g->page < 3) || g->dialogue == D_MODERN))
        projected = 0;
    near = SK_NONE;
    keys[0] = g->mode | ((SkU16)(g->mode == G_JOURNAL ? g->journal_page : g->option) << 8);
    keys[1] = g->dialogue | ((SkU16)g->page << 8);
    keys[2] = g->revealed | ((SkU16)g->room << 8);
    keys[3] = (bucket5[g->oil]) | ((SkU16)(bucket5[g->fear]) << 5) | ((SkU16)g->lamp << 11);
    keys[4] = g->notice | ((SkU16)near << 8);
    keys[5] = g->rune_mask | ((SkU16)g->chapel_step << 4) | ((SkU16)g->forest_step << 6) |
              ((SkU16)(bucket10[g->charge[0]]) << 8) | ((SkU16)(bucket10[g->charge[1]]) << 11);
    keys[6] = bucket10[g->charge[2]];
    keys[7] = g->flags;
    keys[8] = g->memories | ((SkU16)g->wards << 8);
    keys[9] = (bucket5[g->echo_charge]) | ((SkU16)g->bell_step << 8);
    redraw = 0;
    for (i = 0; i < 10; ++i)
        if (keys[i] != last_keys[i])
            redraw = 1;
    if (redraw) {
        memcpy(last_keys, keys, sizeof(keys));
        memset(text_map, 0, sizeof(text_map));
        dirty = 1;
    }
    bg = g->room + 2;
    if (g->mode == G_SPLASH)
        bg = 0;
    if (g->mode == G_MENU || g->mode == G_HELP || g->mode == G_CREDITS || g->mode == G_END)
        bg = 1;
    if (g->mode == G_JOURNAL)
        bg = 14;
    corridor = g->mode == G_CORRIDOR ||
               (g->mode == G_PAUSE && g->return_mode == G_CORRIDOR);
    cinematic = g->mode == G_DIALOGUE && ((g->dialogue == D_PROLOG && g->page < 3) || g->dialogue == D_MODERN);
    if (cinematic)
        bg = g->dialogue == D_MODERN ? 7 : (g->page < 3 ? 6 + g->page : 9);
    if (g->mode == G_PAUSE && g->return_mode == G_DIALOGUE && g->dialogue == D_MODERN)
        bg = 7;
    if (corridor)
        bg = 6;
    world = bg >= 2 && bg <= 5;
    changed = current_bg != bg;
    if (projected) {
        if (current_bg != 10 + g->room) {
            hide();
            perspective_enter(g);
            current_bg = 10 + g->room;
        }
        cut = g->mode == G_DIALOGUE ? 128 : (g->mode == G_CHOICE ? 88 : 64);
        if (g->mode == G_JOURNAL)
            cut = 16;
        if (g->mode == G_PAUSE)
            cut = 48;
        perspective_draw(g);
        perspective_overlay(cut);
        world = 0;
        changed = 0;
    } else
        background(bg);
    if (changed) {
        hide();
        camera_x = 0;
    }
    brightness = 15;
    if (scene_age < 30)
        ++scene_age;
    if ((cinematic || g->mode == G_MENU) && scene_age < 30)
        brightness = scene_age >> 1;
    if (g->mode == G_SPLASH) {
        if (g->tick < 30)
            brightness = (SkU8)(g->tick / 2);
        else if (g->tick > 120)
            brightness = (SkU8)((150 - g->tick) / 2);
    }
    /* Text stays readable, but even pause must not reveal an unlit world. */
    if (!projected) {
        flashlight_prepare(g, world);
        if (g->mode != G_JOURNAL) {
            if (world && g->lamp && g->oil)
                bgSetEnable(1);
            else
                bgSetDisable(1);
        }
    }
    /* Perspective HDMA owns TM for the entire raster, including dialogues.
       Calling the SDK's BG toggle here publishes its stale Mode1 layer mask
       during active display and can expose the Mode7 plane as 4bpp tiles. */
    if (cinematic)
        draw_cinematic(g);
    if (corridor)
        draw_corridor(g);
    if (world) {
        draw_torch(g);
        /* Stable actors need no repeated OAM writes; movement and UI/flag
           changes invalidate this path. Light direction has its own cache. */
        if (!redraw && !changed && g->x == previous_x && g->y == previous_y &&
            g->enemy_x == previous_enemy_x && g->enemy_y == previous_enemy_y)
            return;
        draw_actors(g);
    }
    if (g->mode == G_SPLASH) {
        /* Captions are centered in the animation itself, after the sparks. */
        splash_frame = g->tick < 96 ? g->tick / 3 : 28 + ((g->tick >> 2) & 3);
    } else if (g->mode == G_MENU) {
        /* Night of Chernorechye: menu positions align with the painted slab. */
        menu_torch_frame = (g->tick >> 2) & 15;
        text(3, 3, TXT_TITLE);
        text(3, 5, TXT_SUBTITLE);
        text(3, 8, TXT_YEAR);
        text(5, 12, TXT_NEW);
        text(5, 15, TXT_HELP);
        text(5, 18, TXT_CREDITS);
        text(3, 12 + g->option * 3, ">");
        text(3, 26, TXT_PRESS);
    } else if (g->mode == G_HELP || g->mode == G_CREDITS) {
        panel(2, 26);
        text(1, 3, g->mode == G_HELP ? TXT_HELP_TEXT : TXT_CREDITS_TEXT);
        text(1, 27, TXT_FINISH);
    } else if (g->mode == G_DIALOGUE) {
        if (cinematic) {
            text(1, 1, g->dialogue == D_MODERN ? TXT_PROLOG_CELLAR : (g->page == 0 ? TXT_PROLOG_GYM
                                   : (g->page == 1 ? TXT_PROLOG_CELLAR : TXT_PROLOG_PAST)));
        } else
            text(1, 1, room_name(g->room));
        panel(16, 12);
        line = story_line(g->dialogue, g->page);
        if (line) {
            text(1, 17, line->speaker);
            text_n(1, 19, line->text, g->revealed);
        }
        text(1, 26, line && g->revealed < line->length ? TXT_MORE : TXT_CONTINUE);
        number(28, 27, g->page + 1);
    } else if (g->mode == G_CORRIDOR) {
        text(1, 1, TXT_PROLOG_CORRIDOR);
        panel(23, 5);
        text(2, 24, TXT_CORRIDOR_WALK);
        text(2, 26, TXT_CORRIDOR_HINT);
    } else if (g->mode == G_CHOICE) {
        panel(11, 17);
        text(1, 12, TXT_GOAL);
        text(2, 16, choice_text(g->choice, 0));
        text(2, 19, choice_text(g->choice, 1));
        text(0, 16 + g->option * 3, ">");
        text(1, 25, TXT_CHOOSE_HINT);
    } else if (g->mode == G_BELL) {
        panel(8, 20);
        text(1, 9, TXT_BELL_TITLE);
        number(28, 10, g->bell_step + 1);
        text(4, 13, TXT_BELL_LEFT);
        text(4, 16, TXT_BELL_MIDDLE);
        text(4, 19, TXT_BELL_RIGHT);
        text(1, 13 + g->option * 3, ">");
        text(1, 23, TXT_BELL_HINT);
        if (g->notice == 11)
            text(1, 25, TXT_BELL_WRONG);
    } else if (g->mode == G_PUZZLE) {
        panel(8, 20);
        text(1, 9, TXT_PUZZLE);
        number(28, 9, g->chapel_step + 1);
        text(5, 13, TXT_MEMORY);
        text(5, 16, TXT_NAME);
        text(5, 19, TXT_LIGHT);
        text(2, 13 + g->option * 3, ">");
        text(1, 23, TXT_PUZZLE_HINT);
        if (g->notice == 6)
            text(1, 25, TXT_PUZZLE_WRONG);
    } else if (g->mode == G_JOURNAL) {
        /* A dedicated Mode 1 page keeps the journal independent of the
           world renderer and gives every group its own space and palette. */
        draw_clock(25, 2, g);
        text(5, 4, TXT_WORLD_DAY);
        number(11, 4, g->day_number);
        tint(11, 4, 3, 1, 6);
        text(30 - strlen(game_time_name(g)), 4, game_time_name(g));
        text(5, 7, TXT_OIL);
        text(21, 7, TXT_FEAR);
        journal_meter(5, 9, g->oil);
        journal_meter(21, 9, g->fear);
        number(12, 9, g->oil);
        number(28, 9, g->fear);
        text(21, 2, g->journal_page ? "2/2" : "1/2");
        tint(21, 2, 3, 1, 5);
        text(5, 11, g->journal_page ? TXT_NOTES_SHORT : TXT_GOAL);
        tint(5, 11, 6, 1, 6);
        if (g->journal_page) {
            text_box(5, 12, game_journal(g), 25, 7, 1);
        } else {
            text_box(5, 12, game_goal(g), 25, 4, 0);
            text_box(5, 17, game_journal(g), 25, 2, 1);
            tint(5, 17, 25, 2, 5);
            text(30, 18, ">");
            tint(30, 18, 1, 1, 6);
        }
        text(4, 20, TXT_ARROWS);
        number(13, 20, g->ammo);
        text(20, 20, TXT_WARDS);
        number(28, 20, g->wards);
        text(4, 22, TXT_MEMORIES);
        number(13, 22,
               (g->memories & 1 ? 1 : 0) + (g->memories & 2 ? 1 : 0) + (g->memories & 4 ? 1 : 0));
        text(14, 22, "/3");
        text(20, 22, g->room == 3 ? TXT_NODES : (g->room == 1 ? TXT_SIGNS : TXT_BELL_STATUS));
        number(28, 22, g->room == 3 ?
               (g->rune_mask & 1 ? 1 : 0) + (g->rune_mask & 2 ? 1 : 0) + (g->rune_mask & 4 ? 1 : 0) :
               (g->room == 1 ? g->forest_step : (g->memories & 8 ? 3 : g->bell_step)));
        text(29, 22, "/3");
        text(4, 24, TXT_NIGHTS);
        number(13, 24, g->nights);
        text(20, 24, TXT_KILLS);
        number(28, 24, g->kills);
        text(2, 26, "<>");
        text(6, 26, TXT_EVIDENCE_SHORT);
        number(12, 26, (g->evidence & 1 ? 1 : 0) + (g->evidence & 2 ? 1 : 0) +
                       (g->evidence & 4 ? 1 : 0));
        text(13, 26, "/3");
        text(23, 26, "B");
        tint(23, 26, 1, 1, 6);
        text(25, 26, TXT_BACK_SHORT);
    } else if (g->mode == G_PAUSE) {
        panel(6, 22);
        text(1, 7, TXT_PAUSE);
        text(2, 12, TXT_RESUME);
        text(2, 16, TXT_CHECKPOINT);
        text(2, 20, TXT_MENU);
        text(0, 12 + g->option * 4, ">");
    } else if (g->mode == G_END) {
        panel(8, 20);
        text(1, 10,
             g->ending == END_SECRET ? TXT_END_SECRET
                                     : (g->ending == END_GOOD ? TXT_END_GOOD : TXT_END_BAD));
        text(1, 14, "NABLA");
        text(1, 17, TXT_TITLE);
        text(1, 20, "1193 > NOVGU");
        text(1, 25, TXT_FINISH);
    }
    (void)scope;
}
void video_calibration(SkU8 stage, SkS16 x, SkS16 y) {
    SkU8 row, column;
    /* Optical packets can arrive every frame with TURBO held. A stable target
       needs no repeated full UI rebuild or 1792-byte upload on those frames. */
    if (stage == calibration_stage && x == calibration_x && y == calibration_y && current_bg == 0)
        return;
    calibration_stage = stage;
    calibration_x = x;
    calibration_y = y;
    brightness = 15;
    redraw = 1;
    dirty = 1;
    memset(text_map, 0, sizeof(text_map));
    background(0);
    hide();
    panel(2, 26);
    text(2, 5, TXT_SCOPE);
    text(2, 7, TXT_CALIBRATE);
    /* Unused DEL glyph 127 is solid white: a 32x32 optical patch around
       the 16x16 crosshair gives a real CRT Scope enough light to latch. */
    for (row = 12; row < 16; ++row)
        for (column = 14; column < 18; ++column)
            ui_tile(column, row, 127);
    text_map[13 * 32 + 15] = 257 | (7 << 10) | BG_TIL_PRIO;
    text_map[13 * 32 + 16] = 258 | (7 << 10) | BG_TIL_PRIO;
    text_map[14 * 32 + 15] = 259 | (7 << 10) | BG_TIL_PRIO;
    text_map[14 * 32 + 16] = 260 | (7 << 10) | BG_TIL_PRIO;
    if (stage == 2) {
        text(1, 21, TXT_CALIBRATE2);
        text(1, 24, TXT_CALIBRATE3);
        if (x >= 0 && x < 256 && y >= 0 && y < 224)
            text(x / 8, y / 8, "+");
    }
    REG_HDMAEN = 0;
    REG_TMW = 0;
    /* Keep instructions readable on the same dark panel as the rest of the
       UI. Only the optical target is bright, centered at (128,112). */
    setPaletteColor(30, RGB5(1, 2, 3));
    setPaletteColor(29, RGB5(29, 29, 26));
    memset(last_keys, 255, sizeof(last_keys));
}
