#ifndef SNESKIT_H
#define SNESKIT_H

/* Fixed width on 816-tcc and ordinary desktop compilers. No heap or floats. */
typedef unsigned char SkU8;
typedef signed char SkS8;
typedef unsigned short SkU16;
typedef signed short SkS16;

#define SK_WIDTH 256
#define SK_HEIGHT 224
#define SK_NONE 255

#ifdef __cplusplus
extern "C" {
#endif

enum SkButton {
    SK_LEFT = 1,
    SK_RIGHT = 2,
    SK_UP = 4,
    SK_DOWN = 8,
    SK_ACTION = 16,
    SK_RELOAD = 32,
    SK_LIGHT = 64,
    SK_PAUSE = 128,
    SK_AIM = 256,
    SK_JOURNAL = 512,
    SK_BACK = 1024,
    SK_TURN_LEFT = 2048,
    SK_SHOVE = 4096
};

typedef struct {
    SkU16 held, pressed;
    SkS16 x, y;
    SkU8 aim_valid, fire, offscreen, scope;
} SkInput;

typedef struct {
    SkU8 accumulator;
} SkClock;
typedef struct {
    SkS16 x, y, w, h;
} SkRect;
SkU8 sk_clock_ticks(SkClock *clock, SkU8 fps);
SkU8 sk_contains(const SkRect *rect, SkS16 x, SkS16 y);
#ifdef __cplusplus
}
#endif

#endif
