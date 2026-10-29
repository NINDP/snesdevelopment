#ifndef CHERNORECHYE_AUDIO_H
#define CHERNORECHYE_AUDIO_H
#include "game.h"
#include "audio_ids.h"
SkU8 sound_priority(SkU8 id);
void sound_reset(void);
void sound_emit(SkU8 id);
void sound_schedule(SkU8 id, SkU8 delay);
void sound_step(SkU8 ticks);
SkU8 sound_take(void);
void sound_story(SkU8 dialogue, SkU8 page);
void sound_walk(SkU8 material, SkU8 distance);
SkU8 sound_variant(SkU8 first, SkU8 count);
SkU8 sound_profile(const Game *g);
SkU8 sound_material(const Game *g);
#endif
