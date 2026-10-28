#ifndef CHERNORECHYE_PLATFORM_H
#define CHERNORECHYE_PLATFORM_H
#include "game.h"
#include "video_layout.h"
void audio_init(void);
void audio_update(const Game *g);
void video_init(void);
void video_draw(const Game *g, SkU8 scope);
void video_commit(void);
void video_calibration(SkU8 stage, SkS16 x, SkS16 y);
void ambush_video_enter(void);
void ambush_video_leave(void);
void ambush_video_draw(const Game *g);
void ambush_video_commit(SkU8 full_ui);
void flashlight_prepare(const Game *g, SkU8 enabled);
void flashlight_commit(void);
#endif
