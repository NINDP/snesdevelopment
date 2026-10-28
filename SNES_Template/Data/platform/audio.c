#include <snes.h>
#include "../include/platform.h"
extern u8 heartbeat_sound, heartbeat_sound_end;
extern u8 latch_sound, latch_sound_end;
extern u8 seal_sound, seal_sound_end;
extern u8 chime_sound, chime_sound_end;
extern u8 bow_sound, bow_sound_end, impact_sound, impact_sound_end;
extern u8 attack_sound, attack_sound_end, shove_sound, shove_sound_end, hurt_sound, hurt_sound_end;
static brrsamples sounds[9];
static SkU8 old_lamp = 0, old_room = 0, old_runes = 0, cooldown = 0;
static SkU16 previous_tick = 0;
static SkU8 old_time_phase = TIME_DAY;
static SkU8 old_bow_cooldown = 0;
static SkU8 old_hurt = 0, old_shove = 0, old_impact = 0;
static SkU8 old_attack_mask = 0, old_draw = 0;
static SkU16 old_kills = 0;
void audio_init(void) {
    spcBoot();
    spcAllocateSoundRegion(16);
    spcSetSoundEntry(5, 8, 1, &heartbeat_sound_end - &heartbeat_sound, &heartbeat_sound,
                     &sounds[0]);
    spcSetSoundEntry(6, 8, 4, &latch_sound_end - &latch_sound, &latch_sound, &sounds[1]);
    spcSetSoundEntry(7, 8, 4, &seal_sound_end - &seal_sound, &seal_sound, &sounds[2]);
    spcSetSoundEntry(6, 8, 1, &chime_sound_end - &chime_sound, &chime_sound, &sounds[3]);
    spcSetSoundEntry(7, 8, 1, &bow_sound_end - &bow_sound, &bow_sound, &sounds[4]);
    spcSetSoundEntry(7, 8, 1, &impact_sound_end - &impact_sound, &impact_sound, &sounds[5]);
    spcSetSoundEntry(6, 8, 1, &attack_sound_end - &attack_sound, &attack_sound, &sounds[6]);
    spcSetSoundEntry(7, 8, 1, &shove_sound_end - &shove_sound, &shove_sound, &sounds[7]);
    spcSetSoundEntry(7, 8, 1, &hurt_sound_end - &hurt_sound, &hurt_sound, &sounds[8]);
    /* Explicit origin: heartbeat=0, latch=1, seal=2, time chime=3. */
    spcSetSoundTableEntry(&sounds[0]);
}
void audio_update(const Game *g) {
    SkU8 i, impact = 0, attack_mask = 0, bit = 1;
    if (g->arrows[0].life || g->arrows[1].life || g->arrows[2].life)
        for (i = 0; i < COMBAT_ARROWS; ++i)
            if (g->arrows[i].life && !g->arrows[i].damage) impact = 1;
    if (g->enemy_active)
        for (i = 0; i < g->enemy_slots; ++i) {
            if (g->enemies[i].state == ENEMY_WINDUP) attack_mask |= bit;
            bit <<= 1;
        }
    if (cooldown)
        --cooldown;
    if (g->bow_cooldown > old_bow_cooldown) {
        spcPlaySound(4);
        cooldown = 18;
    } else if (g->kills > old_kills || (impact && !old_impact)) {
        spcPlaySound(5);
        cooldown = 18;
    } else if (g->hurt_timer > old_hurt) {
        spcPlaySound(8);
        cooldown = 18;
    } else if (g->shove_cooldown > old_shove) {
        spcPlaySound(7);
        cooldown = 12;
    } else if (attack_mask & ~old_attack_mask) {
        spcPlaySound(6);
        cooldown = 12;
    } else if (g->bow_draw == BOW_DRAW_TICKS && old_draw < BOW_DRAW_TICKS) {
        spcPlaySound(3);
        cooldown = 12;
    } else if (g->lamp != old_lamp) {
        spcPlaySound(1);
        cooldown = 18;
    } else if (g->room != old_room || g->rune_mask != old_runes) {
        spcPlaySound(2);
        cooldown = 30;
    } else if (g->mode == G_EXPLORE && g->time_phase != old_time_phase) {
        spcPlaySound(3);
        cooldown = 30;
    } else if (!cooldown && g->mode == G_EXPLORE && g->tick != previous_tick && !(g->seconds & 1) &&
               g->pulse < 4 && game_daylight(g) < 8) {
        spcPlaySound(0);
        cooldown = 45;
    }
    old_lamp = g->lamp;
    old_room = g->room;
    old_runes = g->rune_mask;
    previous_tick = g->tick;
    old_time_phase = g->time_phase;
    old_bow_cooldown = g->bow_cooldown;
    old_kills = g->kills;
    old_hurt = g->hurt_timer;
    old_shove = g->shove_cooldown;
    old_impact = impact;
    old_attack_mask = attack_mask;
    old_draw = g->bow_draw;
    spcProcess();
}
