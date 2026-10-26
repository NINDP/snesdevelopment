#ifndef CHERNORECHYE_PERSPECTIVE_H
#define CHERNORECHYE_PERSPECTIVE_H
#include "game.h"
#define PERSPECTIVE_ORIGIN 384
#define PERSPECTIVE_ANCHOR 164
#define PERSPECTIVE_DECOR 0x80
typedef struct { SkS16 x, y; SkU16 tile; SkU8 kind; } PerspectiveObject;
extern const PerspectiveObject *const perspective_objects[4];
extern const SkU8 perspective_counts[4];
extern const SkU8 perspective_light_x[4], perspective_light_y[4];
extern const SkU8 perspective_y[241], perspective_size[241];
extern const SkS16 perspective_pick_y[176];
extern const SkU16 perspective_pick_scale[176];
SkU8 perspective_project(const Game *g, SkS16 x, SkS16 y, SkS16 *sx, SkS16 *sy);
SkU8 perspective_pick(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y);
SkU8 perspective_pick_target(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y);
void perspective_enter(SkU8 room);
void perspective_draw(const Game *g);
void perspective_commit(void);
void perspective_overlay(SkU8 cut);
void perspective_leave(void);
#endif
