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
SkU8 perspective_pick_target(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y) {
    const PerspectiveObject *object;
    SkS16 ox, oy, dx, dy;
    SkU8 i, half, height;
    /* A player aims at a villager's body, not the tiny floor point at their
       feet. Pick the visible billboard before converting the floor. The ROM
       list is near-to-far, matching OBJ priority and the renderer's LODs. */
    i = (g->direction >> 1) & 3;
    dx = sx - perspective_light_x[i];
    dy = sy - perspective_light_y[i];
    if (game_daylight(g) || (g->lamp && g->oil && dx >= -79 && dx <= 79 && dy >= -79 && dy <= 79 &&
        dx * dx + dy * dy <= 79 * 79)) {
        object = perspective_objects[g->room];
        for (i = 0; i < perspective_counts[g->room]; ++i, ++object) {
            if (object->kind & PERSPECTIVE_DECOR)
                continue;
            if (object->y < g->y - 112)
                continue;
            if (!perspective_project(g, object->x, object->y, &ox, &oy))
                continue;
            half = 8;
            height = 16;
            if (object->kind == 0 && oy >= 140)
                height = 32;
            if ((object->kind == 1 && oy >= 134) || (object->kind == 3 && oy >= 140)) {
                half = 16;
                height = 32;
            }
            if (sx < ox - half || sx >= ox + half || sy < oy - height || sy >= oy)
                continue;
            *x = object->x;
            *y = object->y;
            return 1;
        }
    }
    return perspective_pick(g, sx, sy, x, y);
}
