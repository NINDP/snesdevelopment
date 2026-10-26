#include "../include/game.h"
/* Gameplay and PPU use the same four-scanline bands. No floats or raycasting. */
void light_span(const Game *g, SkS16 y, SkS16 *left, SkS16 *right) {
    SkS16 row, width, a, b;
    *left = 255;
    *right = 0;
    /* Separate guards avoid a short-circuit miscompile in 816-tcc. */
    if (!g->lamp)
        return;
    if (!g->oil)
        return;
    /* The torch illuminates a circle around the body, independent of facing.
       A ROM lookup replaces a square root in the 65C816 drawing loop. */
    row = (y & ~3) + 10 - g->y;
    if (row < 0)
        row = -row;
    if (row > TORCH_RADIUS)
        return;
    width = torch_width[row];
    a = g->x - width;
    b = g->x + width;
    if (b < 0 || a > 255)
        return;
    if (a < 0)
        a = 0;
    if (b > 255)
        b = 255;
    *left = a;
    *right = b;
}
SkU8 light_sees(const Game *g, SkS16 x, SkS16 y) {
    SkS16 a, b;
    if (y < 24 || y >= 192)
        return 0;
    light_span(g, y, &a, &b);
    return a <= b && x >= a && x <= b;
}
SkU8 light_direction(SkS16 dx, SkS16 dy) {
    SkS16 ax = dx < 0 ? -dx : dx, ay = dy < 0 ? -dy : dy;
    if (!ax && !ay)
        return 0;
    if (ax > ay * 2)
        return dx > 0 ? 2 : 6;
    if (ay > ax * 2)
        return dy > 0 ? 4 : 0;
    if (dy < 0)
        return dx > 0 ? 1 : 7;
    return dx > 0 ? 3 : 5;
}
