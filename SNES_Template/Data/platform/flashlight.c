#include <snes.h>
#include "../include/platform.h"
/* HDMA channel 6 writes WH0/WH1. Never modify the table being displayed. */
static SkU8 tables[2][VIDEO_HDMA_BYTES];
static SkU8 active = 0, pending = 0, mask = 0;
static SkS16 old_x = -1, old_y = -1;
static SkU8 old_direction = 255, old_lamp = 255, old_enabled = 255;
void flashlight_prepare(const Game *g, SkU8 enabled) {
    SkU8 next, offset = 0, row;
    SkS16 left, right;
    SkU8 lit = g->lamp && g->oil;
    mask = enabled;
    if (g->x == old_x && g->y == old_y && g->direction == old_direction && lit == old_lamp &&
        enabled == old_enabled)
        return;
    old_x = g->x;
    old_y = g->y;
    old_direction = g->direction;
    old_lamp = lit;
    old_enabled = enabled;
    next = active ^ 1;
    tables[next][offset++] = 24;
    tables[next][offset++] = 0;
    tables[next][offset++] = 255;
    for (row = 24; row < 192; row += 4) {
        light_span(g, row, &left, &right);
        tables[next][offset++] = 4;
        tables[next][offset++] = (SkU8)left;
        tables[next][offset++] = (SkU8)right;
    }
    tables[next][offset++] = 32;
    tables[next][offset++] = 0;
    tables[next][offset++] = 255;
    tables[next][offset] = 0;
    pending = next + 1;
}
void flashlight_commit(void) {
    if (!mask) {
        REG_HDMAEN = 0;
        REG_TMW = 0;
        return;
    }
    if (pending) {
        active = pending - 1;
        pending = 0;
    }
    REG_HDMAEN = 0;
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
    REG_HDMAEN = HDMA_CHANNEL6;
}
