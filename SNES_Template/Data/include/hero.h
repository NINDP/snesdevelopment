#ifndef CHERNORECHYE_HERO_H
#define CHERNORECHYE_HERO_H
#include "game.h"
/* Mode 7 only. Calls to enter/leave run under forced blank; commit in VBlank. */
#define HERO_FRAME_BYTES 1024
#define HERO_FRAME_COUNT 32
#define HERO_BOW_FRAME_COUNT 16
#define BOW_TILE_BYTES 1024
#define BOW_ARROW_TILE 64
#define BOW_IMPACT_TILE 74
#define BOW_MARKER_TILE 78
enum HeroGripField { HERO_LEFT_X, HERO_LEFT_Y, HERO_RIGHT_X, HERO_RIGHT_Y };
/* Frame-major attachment coordinates; four fields per selected pose. */
extern const SkU8 hero_grips[HERO_FRAME_COUNT * 4];
void hero_enter(void);
void hero_leave(void);
void hero_prepare(const Game *g, SkU8 moving);
void hero_commit(void);
void hero_draw(SkU16 first_slot);
#endif
