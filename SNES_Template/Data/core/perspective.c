#include "../include/perspective.h"
#ifndef SNES_TARGET
SkU8 perspective_project(const Game *g, SkS16 x, SkS16 y, SkS16 *sx, SkS16 *sy) {
    SkS16 dy = y - g->y, dx = x - g->x;
    SkU16 index;
    if (dy < -192 || dy > 38 || dx < -255 || dx > 255)
        return 0;
    index = dy + 192;
    *sy = perspective_y[index];
    *sx = 128 + ((dx * perspective_size[index]) >> 6);
    return *sx >= -32 && *sx <= 287;
}
#endif
SkU8 perspective_pick(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y) {
    SkU8 index;
    if (sx < 0 || sx > 255 || sy < 96 || sy > 223)
        return 0;
    index = sy - 48;
    *x = g->x + (((sx - 128) * (SkS16)perspective_pick_scale[index]) >> 6);
    *y = g->y + perspective_pick_y[index];
    return *x >= 0 && *x <= 255 && *y >= 24 && *y < 192;
}
