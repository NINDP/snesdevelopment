#include <snes.h>
#include "../include/platform.h"
#include "../include/audio.h"
extern u8 audio_bank_0, audio_stream_table;
extern const SkU8 audio_modules[], audio_music_tracks[], audio_durations[];
extern const SkU8 audio_resident_lookup[];
extern const SkU16 audio_residents[];
extern void audio_boot(void);
extern void audio_set_volume(SkU8 channel, SkU8 volume);
static SkU8 loaded=255, resident_table, resident_count, stream_busy, stream_priority;
static SkU8 msu_present, msu_track=255, msu_pending, msu_failed;
static SkU16 audio_stamp;
static SkU16 resident_lookup;
static SkU8 previous_lit=255;
/* Exported counters make emulator verification independent of hearing/UI. */
SkU8 audio_last_sound=255, audio_last_profile=255, audio_msu_active;
SkU16 audio_play_count;
#define MSU_STATUS (*(vuint8 *)0x2000)
#define MSU_ID1 (*(vuint8 *)0x2002)
#define MSU_ID2 (*(vuint8 *)0x2003)
#define MSU_ID3 (*(vuint8 *)0x2004)
#define MSU_ID4 (*(vuint8 *)0x2005)
#define MSU_ID5 (*(vuint8 *)0x2006)
#define MSU_ID6 (*(vuint8 *)0x2007)
#define MSU_TRACK_LO (*(vuint8 *)0x2004)
#define MSU_TRACK_HI (*(vuint8 *)0x2005)
#define MSU_VOLUME (*(vuint8 *)0x2006)
#define MSU_CONTROL (*(vuint8 *)0x2007)
static void music_track(SkU8 track) {
    if (!msu_present || msu_failed) return;
    if (track!=msu_track) {
        MSU_CONTROL=0;
        MSU_VOLUME=0;
        msu_track=track;
        msu_pending=track!=0;
        if (track) { MSU_TRACK_LO=track;MSU_TRACK_HI=0; }
    }
    if (msu_pending && !(MSU_STATUS & 0x40)) {
        msu_pending=0;
        if (MSU_STATUS & 8) { msu_failed=1;audio_msu_active=0;loaded=255; }
        else { MSU_VOLUME=145;MSU_CONTROL=3;audio_msu_active=1; }
    }
}
void audio_init(void) {
    stream_busy=stream_priority=msu_pending=msu_failed=audio_msu_active=0;
    audio_play_count=0;
    sound_reset();
    audio_boot();
    spcAllocateSoundRegion(16);
    spcSetBank(&audio_bank_0);
    spcSetSoundTableEntry((brrsamples *)&audio_stream_table);
    msu_present=MSU_ID1=='S' && MSU_ID2=='-' && MSU_ID3=='M' &&
        MSU_ID4=='S' && MSU_ID5=='U' && MSU_ID6=='1';
    audio_stamp=snes_vblank_count;
}
void audio_update(const Game *g) {
    SkU8 profile, lit=g->lamp && g->oil, module, material, i, id, level;
    SkU16 delta=snes_vblank_count-audio_stamp;
    profile=sound_profile(g);
    audio_stamp=snes_vblank_count;
    if (delta>255) delta=255;
    sound_step((SkU8)delta);
    stream_busy=stream_busy>delta?stream_busy-delta:0;
    music_track(audio_music_tracks[profile]);
    module=audio_modules[(SkU16)profile*4+(msu_present && !msu_failed?1:0)];
    if (module!=loaded) {
        /* Transfers occur only at scene changes; gameplay effects use
           sixteen resident samples and a separate bounded stream region. */
        /* spcLoad drains its FIFO through the SDK's internal RTS path.
           The public spcFlush in 4.6.0 returns incorrectly with queued data. */
        spcLoad(module);
        material=profile==AP_UNIVERSITY || profile==AP_BASEMENT?3:(g->room==3?2:(g->room==2?1:0));
        resident_table=(material*2+(profile==AP_AMBUSH?1:0))*16;
        if (profile==AP_TITLE) resident_table=128;
        resident_lookup=(SkU16)(resident_table>>4)*S_COUNT;
        resident_count=profile==AP_TITLE?5:16;
        for (i=0;i<resident_count;++i) spcLoadEffect(audio_residents[resident_table+i]);
        spcPlay(0);
        loaded=module;stream_busy=0;
        previous_lit=255;
        audio_last_profile=profile;
    }
    if (previous_lit!=lit && ((profile>=AP_VILLAGE_DAY && profile<=AP_CRYPT) || profile==AP_FINAL)) {
        audio_set_volume(msu_present && !msu_failed?1:2,lit?64:0);
        previous_lit=lit;
    }
    id=sound_take();
    if (id!=S_NONE) {
        level=sound_priority(id);
        if (stream_busy && level<=stream_priority) {
            /* Quiet steps/UI never queue up behind a long story effect. */
            if (level>=4) sound_schedule(id,stream_busy);
        } else {
            i=audio_resident_lookup[resident_lookup+id];
            if (i<resident_count && !stream_busy) {
                spcEffect(1,i,((level==0?4:(level>=7?11:8))<<4)+8);
            } else {
                spcPlaySound(id);
                stream_busy=audio_durations[id];
                stream_priority=level;
            }
            audio_last_sound=id;++audio_play_count;
        }
    }
    spcProcess();
}
