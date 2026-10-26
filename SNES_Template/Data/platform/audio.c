#include <snes.h>
#include "../include/platform.h"
extern u8 heartbeat_sound, heartbeat_sound_end;
extern u8 latch_sound, latch_sound_end;
extern u8 seal_sound, seal_sound_end;
static brrsamples sounds[3];
static SkU8 old_lamp = 0, old_room = 0, old_runes = 0, cooldown = 0;
static SkU16 previous_tick = 0;
void audio_init(void) {
    spcBoot();
    spcAllocateSoundRegion(16);
    spcSetSoundEntry(5, 8, 4, &heartbeat_sound_end - &heartbeat_sound, &heartbeat_sound,
                     &sounds[0]);
    spcSetSoundEntry(6, 8, 4, &latch_sound_end - &latch_sound, &latch_sound, &sounds[1]);
    spcSetSoundEntry(7, 8, 4, &seal_sound_end - &seal_sound, &seal_sound, &sounds[2]);
    /* Explicit origin: heartbeat=0, latch=1, seal=2. */
    spcSetSoundTableEntry(&sounds[0]);
}
void audio_update(const Game *g) {
    if (cooldown)
        --cooldown;
    if (g->lamp != old_lamp) {
        spcPlaySound(1);
        cooldown = 18;
    } else if (g->room != old_room || g->rune_mask != old_runes) {
        spcPlaySound(2);
        cooldown = 30;
    } else if (!cooldown && g->mode == G_EXPLORE && g->tick != previous_tick && !(g->seconds & 1) &&
               g->pulse < 4) {
        spcPlaySound(0);
        cooldown = 45;
    }
    old_lamp = g->lamp;
    old_room = g->room;
    old_runes = g->rune_mask;
    previous_tick = g->tick;
    spcProcess();
}
