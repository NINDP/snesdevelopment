#include <snes.h>
#include "../include/platform.h"
/* Channel 6 clips radial light; channel 5 shifts BG1 pixels above the flame.
   Both tables are double buffered and published together in VBlank. */
static SkU8 tables[2][VIDEO_HDMA_BYTES];
static SkU8 heat_tables[2][VIDEO_HDMA_BYTES];
static SkU8 active = 0, pending = 0, mask = 0, heat = 0;
static SkS16 old_x = -1, old_y = -1;
static SkU8 old_phase = 255, old_lamp = 255, old_enabled = 255;
static const SkS8 wave[8] = {0, 1, 2, 1, 0, -1, -2, -1};
void flashlight_prepare(const Game *g, SkU8 enabled) {
    SkU8 next, offset = 0, heat_offset = 0, row, phase;
    SkS16 left, right, shift;
    SkU16 scroll;
    SkU8 lit = g->lamp && g->oil;
    mask = enabled;
    heat = enabled && lit;
    phase = heat ? (SkU8)((g->tick >> 2) & 7) : 0;
    if (g->x == old_x && g->y == old_y && phase == old_phase && lit == old_lamp &&
        enabled == old_enabled)
        return;
    old_x = g->x;
    old_y = g->y;
    old_phase = phase;
    old_lamp = lit;
    old_enabled = enabled;
    next = active ^ 1;
    tables[next][offset++] = 24;
    tables[next][offset++] = 0;
    tables[next][offset++] = 255;
    heat_tables[next][heat_offset++] = 24;
    heat_tables[next][heat_offset++] = 0;
    heat_tables[next][heat_offset++] = 0;
    for (row = 24; row < 192; row += 4) {
        light_span(g, row, &left, &right);
        tables[next][offset++] = 4;
        tables[next][offset++] = (SkU8)left;
        tables[next][offset++] = (SkU8)right;
        shift = 0;
        if (lit && row >= g->y - 50 && row < g->y - 14)
            shift = wave[(phase + (row >> 2)) & 7];
        scroll = shift < 0 ? 512 + shift : shift;
        heat_tables[next][heat_offset++] = 4;
        heat_tables[next][heat_offset++] = (SkU8)scroll;
        heat_tables[next][heat_offset++] = (SkU8)(scroll >> 8);
    }
    tables[next][offset++] = 32;
    tables[next][offset++] = 0;
    tables[next][offset++] = 255;
    tables[next][offset] = 0;
    heat_tables[next][heat_offset++] = 32;
    heat_tables[next][heat_offset++] = 0;
    heat_tables[next][heat_offset++] = 0;
    heat_tables[next][heat_offset] = 0;
    pending = next + 1;
}
void flashlight_commit(void) {
    REG_HDMAEN = 0;
    REG_BG1HOFS = 0;
    REG_BG1HOFS = 0;
    if (!mask) {
        REG_TMW = 0;
        return;
    }
    if (pending) {
        active = pending - 1;
        pending = 0;
    }
    REG_DMAP5 = 2;
    REG_BBAD5 = 0x0d;
    REG_A1T5LH = (SkU16)heat_tables[active];
    REG_A1B5 = 0x7e;
    REG_DMAP6 = 1;
    REG_BBAD6 = 0x26;
    REG_A1T6LH = (SkU16)tables[active];
    REG_A1B6 = 0x7e;
    REG_W12SEL = 3;
    REG_W34SEL = 0;
    REG_WOBJSEL = 3;
    REG_WBGLOG = 0;
    REG_WOBJLOG = 0;
    REG_TMW = 0x11;
    REG_TSW = 0;
    REG_WH0 = 255;
    REG_WH1 = 0;
    REG_HDMAEN = heat ? (HDMA_CHANNEL5 | HDMA_CHANNEL6) : HDMA_CHANNEL6;
}
