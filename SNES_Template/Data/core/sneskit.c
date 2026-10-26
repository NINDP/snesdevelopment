#include "../include/sneskit.h"

SkU8 sk_clock_ticks(SkClock *clock, SkU8 fps) {
    /* NTSC is one tick per frame. PAL adds one tick every fifth frame.
       No software division in the per-frame 65C816 path. */
    if (fps != 50)
        return 1;
    clock->accumulator += 10;
    if (clock->accumulator >= 50) {
        clock->accumulator -= 50;
        return 2;
    }
    return 1;
}

SkU8 sk_contains(const SkRect *rect, SkS16 x, SkS16 y) {
    /* Compare unsigned distances so no signed 16-bit addition can overflow. */
    return rect->w > 0 && rect->h > 0 && x >= rect->x && y >= rect->y &&
           (SkU16)((SkU16)x - (SkU16)rect->x) < (SkU16)rect->w &&
           (SkU16)((SkU16)y - (SkU16)rect->y) < (SkU16)rect->h;
}
