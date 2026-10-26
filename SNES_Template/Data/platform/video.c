#include <snes.h>
#include <string.h>
#include "../include/platform.h"
#include "../include/ui_text.h"
extern u8 bg0_tiles, bg0_tiles_end, bg0_map;
extern u8 bg1_tiles, bg1_tiles_end, bg1_map;
extern u8 bg2_tiles, bg2_tiles_end, bg2_map;
extern u8 bg3_tiles, bg3_tiles_end, bg3_map;
extern u8 bg4_tiles, bg4_tiles_end, bg4_map;
extern u8 bg5_tiles, bg5_tiles_end, bg5_map;
extern u8 sprite_tiles, sprite_tiles_end, sprite_palette, bg_palette, font_tiles, font_tiles_end;
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
static SkU16 last_keys[10] = {65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535};
static SkS16 previous_x = 0, previous_y = 0, previous_enemy_x = 0, previous_enemy_y = 0;
static SkU8 cached_near = SK_NONE, near_direction = 255, near_lit = 255, near_room = 255;
/* Applied in VBlank; only the splash uses the SNES master brightness. */
static SkU8 brightness = 15;
static void panel(SkU8 row, SkU8 count) {
    SkU16 i, end = (SkU16)(row + count) * 32;
    if (!redraw)
        return;
    if (end > VIDEO_TEXT_ENTRIES)
        end = VIDEO_TEXT_ENTRIES;
    for (i = (SkU16)row * 32; i < end; ++i)
        text_map[i] = 256 | (7 << 10) | BG_TIL_PRIO;
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
static void first_line(SkU8 x, SkU8 y, const char *value) {
    SkU16 count = 0;
    if (!redraw)
        return;
    while (value[count] && value[count] != 10 && count < 30)
        ++count;
    text_n(x, y, value, count);
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
static void background(SkU8 id) {
    u8 *tiles = 0, *end = 0, *map = 0;
    if (current_bg == id)
        return;
    switch (id) {
    case 0:
        tiles = &bg0_tiles;
        end = &bg0_tiles_end;
        map = &bg0_map;
        break;
    case 1:
        tiles = &bg1_tiles;
        end = &bg1_tiles_end;
        map = &bg1_map;
        break;
    case 2:
        tiles = &bg2_tiles;
        end = &bg2_tiles_end;
        map = &bg2_map;
        break;
    case 3:
        tiles = &bg3_tiles;
        end = &bg3_tiles_end;
        map = &bg3_map;
        break;
    case 4:
        tiles = &bg4_tiles;
        end = &bg4_tiles_end;
        map = &bg4_map;
        break;
    default:
        tiles = &bg5_tiles;
        end = &bg5_tiles_end;
        map = &bg5_map;
        break;
    }
    setScreenOff();
    REG_HDMAEN = 0;
    bgInitTileSet(0, tiles, &bg_palette, 0, end - tiles, 32, BG_16COLORS, VIDEO_BG_TILES);
    bgInitMapSet(0, map, 2048, SC_32x32, VIDEO_BG_MAP);
    bgSetScroll(0, 0, -1);
    setPaletteColor(0, 0);
    current_bg = id;
    setScreenOn();
}
static void sprite(SkU8 id, SkS16 x, SkS16 y, SkU16 tile) {
    oamSet((SkU16)id * 4, x, y, 2, 0, 0, tile, 0);
    oamSetEx((SkU16)id * 4, OBJ_SMALL, OBJ_SHOW);
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
    setPaletteColor(29, RGB5(28, 28, 24));
    setPaletteColor(30, 0);
    setPaletteColor(31, RGB5(29, 24, 15));
}
void video_commit(void) {
    if (dirty) {
        dmaCopyVram((u8 *)text_map, VIDEO_TEXT_MAP, sizeof(text_map));
        dirty = 0;
    }
    flashlight_commit();
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
    default:
        return 0;
    }
}
static void draw_actors(const Game *g) {
    SkU8 i;
    const Hotspot *h;
    sprite(0, g->x - 8, g->y - 8,
           ((g->tick >> 3) & 1) && (g->x != previous_x || g->y != previous_y) ? 2 : 0);
    if (!(g->flags & F_CHAPEL))
        sprite(9, g->x - 5, g->y + 6, 76);
    else
        oamSetVisible(9 * 4, OBJ_HIDE);
    if (g->room == 0) {
        sprite(1, 48, 70, 6);
        sprite(2, 182, 104, 8);
    }
    if (g->room == 1)
        sprite(1, 176, 68, 4);
    if (g->room == 2) {
        sprite(1, 40, 80, 10);
        sprite(2, 190, 80, 12);
    }
    if (g->room == 3) {
        sprite(1, 184, 74, 4);
        for (i = 0; i < 3; ++i)
            if (g->rune_mask & (1 << i)) {
                h = game_hotspot(3, i + 2);
                sprite(3 + i, h->x - 8, h->y - 8, 38);
            }
    }
    if (g->enemy_active)
        sprite(8, g->enemy_x - 8, g->enemy_y - 8, 14);
    previous_x = g->x;
    previous_y = g->y;
    previous_enemy_x = g->enemy_x;
    previous_enemy_y = g->enemy_y;
}
void video_draw(const Game *g, SkU8 scope) {
    SkU8 i, bg, near, changed;
    SkU16 keys[10];
    const StoryLine *line;
    near = SK_NONE;
    if (g->mode == G_EXPLORE) {
        if (g->x != previous_x || g->y != previous_y || g->direction != near_direction ||
            (g->lamp && g->oil) != near_lit || g->room != near_room) {
            cached_near = game_nearby(g);
            near_direction = g->direction;
            near_lit = g->lamp && g->oil;
            near_room = g->room;
        }
        near = cached_near;
    }
    keys[0] = g->mode | ((SkU16)g->option << 8);
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
    for (i = 0; i < VIDEO_ACTOR_SLOTS; ++i)
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
    changed = current_bg != bg;
    background(bg);
    if (changed)
        hide();
    brightness = 15;
    if (g->mode == G_SPLASH) {
        if (g->tick < 30)
            brightness = (SkU8)(g->tick / 2);
        else if (g->tick > 120)
            brightness = (SkU8)((150 - g->tick) / 2);
    }
    /* Text stays readable, but even pause must not reveal an unlit world. */
    flashlight_prepare(g, bg >= 2);
    if (bg >= 2) {
        /* Stable actors need no repeated OAM writes; movement and UI/flag
           changes invalidate this path. Light direction has its own cache. */
        if (!redraw && !changed && g->x == previous_x && g->y == previous_y &&
            g->enemy_x == previous_enemy_x && g->enemy_y == previous_enemy_y)
            return;
        draw_actors(g);
    }
    if (g->mode == G_SPLASH) {
        text(12, 16, "NABLA");
        text(8, 19, "INTERACTIVE STORIES");
        text(8, 24, "1193 / NOVGOROD");
    } else if (g->mode == G_MENU) {
        panel(2, 6);
        text(10, 3, TXT_TITLE);
        text(4, 5, TXT_SUBTITLE);
        text(3, 7, TXT_YEAR);
        panel(19, 9);
        text(6, 20, TXT_NEW);
        text(6, 22, TXT_HELP);
        text(6, 24, TXT_CREDITS);
        text(3, 20 + g->option * 2, ">");
        text(2, 27, TXT_PRESS);
    } else if (g->mode == G_HELP || g->mode == G_CREDITS) {
        panel(2, 26);
        text(1, 3, g->mode == G_HELP ? TXT_HELP_TEXT : TXT_CREDITS_TEXT);
        text(1, 27, TXT_FINISH);
    } else if (g->mode == G_DIALOGUE) {
        text(1, 1, room_name(g->room));
        panel(16, 12);
        line = story_line(g->dialogue, g->page);
        if (line) {
            text(1, 17, line->speaker);
            text_n(1, 19, line->text, g->revealed);
        }
        text(1, 26, line && g->revealed < line->length ? TXT_MORE : TXT_CONTINUE);
        number(28, 27, g->page + 1);
    } else if (g->mode == G_EXPLORE) {
        panel(0, 3);
        text(1, 1, TXT_OIL);
        number(7, 1, (bucket5[g->oil]) * 5);
        text(14, 1, TXT_FEAR);
        number(21, 1, (bucket5[g->fear]) * 5);
        panel(24, 4);
        if (near != 255)
            text(1, 24, game_hotspot(g->room, near)->name);
        if (g->notice)
            text(1, 25, notice_text(g->notice));
        else if (!g->oil)
            text(1, 25, TXT_EMPTY);
        if (g->room == 1) {
            text(24, 24, "/");
            number(22, 24, g->forest_step);
            text(26, 24, "3");
        }
        if (g->room == 3) {
            number(17, 24, g->charge[0]);
            number(22, 24, g->charge[1]);
            number(27, 24, g->charge[2]);
        }
        first_line(1, 26, game_goal(g));
        if ((g->room == 0 && near == 5) || ((g->room == 1 || g->room == 3) && near == 8))
            number(27, 24, g->echo_charge);
        text(1, 27, TXT_EXPLORE);
    } else if (g->mode == G_CHOICE) {
        panel(11, 17);
        text(1, 12, TXT_GOAL);
        text(2, 16, choice_text(g->choice, 0));
        text(2, 19, choice_text(g->choice, 1));
        text(0, 16 + g->option * 3, ">");
        text(1, 25, TXT_CONTINUE);
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
        panel(2, 26);
        text(1, 3, TXT_JOURNAL);
        text(1, 6, TXT_GOAL);
        text(1, 8, game_goal(g));
        text(1, 12, game_journal(g));
        text(1, 18, TXT_MEMORIES);
        number(12, 18,
               (g->memories & 1 ? 1 : 0) + (g->memories & 2 ? 1 : 0) + (g->memories & 4 ? 1 : 0));
        text(16, 18, TXT_WARDS);
        number(25, 18, g->wards);
        text(1, 20, TXT_BELL_STATUS);
        number(12, 20, g->memories & 8 ? 3 : g->bell_step);
        text(1, 22, TXT_OPTIONAL);
        text(1, 23, TXT_WARD_HELP);
        text(1, 25, "Y / B / A: BACK");
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
    brightness = 15;
    redraw = 1;
    dirty = 1;
    memset(text_map, 0, sizeof(text_map));
    background(0);
    hide();
    panel(2, 26);
    text(2, 5, TXT_SCOPE);
    text(2, 7, TXT_CALIBRATE);
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
    setPaletteColor(30, RGB5(24, 25, 24));
    setPaletteColor(29, RGB5(1, 2, 3));
    memset(last_keys, 255, sizeof(last_keys));
}
