#include "../include/game.h"
/* Gameplay and PPU use the same four-scanline bands. No floats or raycasting. */
void light_span(const Game *g, SkS16 y, SkS16 *left, SkS16 *right) {
    SkS16 row, a, b;
    const SkS16 *span;
    *left = 255;
    *right = 0;
    /* Separate guards avoid a short-circuit miscompile in 816-tcc. */
    if (!g->lamp)
        return;
    if (!g->oil)
        return;
    /* Visible scanlines are nonnegative. The first span is empty in all
       directions, so rejecting a negative numerator preserves old clipping. */
    row = (y & ~3) + 98 - g->y;
    if (row < 0)
        return;
    row = (SkU16)row >> 2;
    if (row >= 49)
        return;
    span = beam_spans[g->direction & 7][row];
    a = span[0];
    b = span[1];
    if (a > b)
        return;
    a += g->x;
    b += g->x;
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
