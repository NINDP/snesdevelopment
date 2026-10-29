#include "../include/audio.h"
#define QUEUE 12
static SkU8 ids[QUEUE], delays[QUEUE], count, variant, stride;
SkU8 sound_priority(SkU8 id) {
    if (id>=S_STEP_GROUND_01 && id<=S_STEP_WOOD_03) return 0;
    if (id>=S_UI_CANCEL && id<=S_UI_MOVE) return 1;
    if (id==S_BIRD_CALL || id==S_WOOD_CREAK || id==S_WATER_DRIP || id==S_PLAYER_HEARTBEAT || id==S_BLACK_HEART_PULSE) return 2;
    if (id==S_PLAYER_DEFEAT || id==S_PLAYER_HURT_01 || id==S_PLAYER_HURT_02 ||
        id==S_SHADE_WARNING || id==S_CRAWLER_WARNING || id==S_FOX_WARNING_01 || id==S_FOX_WARNING_02) return 7;
    if (id==S_BOW_RELEASE_WEAK || id==S_BOW_RELEASE_STRONG) return 6;
    return 4;
}
void sound_reset(void) { count = stride = 0; }
SkU8 sound_variant(SkU8 first, SkU8 alternatives) {
    if (++variant >= alternatives) variant = 0;
    return first + variant;
}
void sound_schedule(SkU8 id, SkU8 delay) {
    SkU8 i;
    if (id >= S_COUNT) return;
    for (i=0;i<count;++i) if (ids[i]==id && delays[i]==delay) return;
    if (count == QUEUE) {
        for (i=0;i<count;++i) if (sound_priority(ids[i])<sound_priority(id)) break;
        if (i==count) return;
        ids[i]=id;delays[i]=delay;return;
    }
    ids[count]=id; delays[count++]=delay;
}
void sound_emit(SkU8 id) { sound_schedule(id, 0); }
void sound_step(SkU8 ticks) {
    SkU8 i;
    for (i=0;i<count;++i) delays[i]=delays[i]>ticks?delays[i]-ticks:0;
}
SkU8 sound_take(void) {
    SkU8 i, result, best=S_NONE;
    for (i=0;i<count;++i) if (!delays[i] &&
        (best==S_NONE || sound_priority(ids[i])>sound_priority(ids[best]))) best=i;
    if (best!=S_NONE) {
        i=best;result=ids[i];
        --count;
        for (;i<count;++i) { ids[i]=ids[i+1];delays[i]=delays[i+1]; }
        return result;
    }
    return S_NONE;
}
void sound_walk(SkU8 material, SkU8 distance) {
    static const SkU8 first[4]={S_STEP_GROUND_01,S_STEP_WOOD_01,S_STEP_STONE_01,S_STEP_UNIVERSITY_01};
    stride+=distance;
    if (stride>=15) { stride=0;sound_emit(sound_variant(first[material],3)); }
}
SkU8 sound_material(const Game *g) {
    if (g->mode==G_CORRIDOR || (g->mode==G_DIALOGUE && g->dialogue==D_PROLOG && g->page<2)) return 3;
    if (g->room==3) return 2;
    if (g->room==2) return (g->x<16 || g->x>239 || (g->x>163 && g->x<181 && g->y>139 && g->y<149))?2:1;
    if (g->room==0 && g->x>88 && g->x<147 && g->y>112 && g->y<148) return 1;
    return 0;
}
SkU8 sound_profile(const Game *g) {
    SkU8 mode=g->mode;
    if (mode==G_PAUSE) mode=g->return_mode;
    if (mode==G_SPLASH || mode==G_MENU || mode==G_HELP || mode==G_CREDITS) return AP_TITLE;
    if (mode==G_CORRIDOR) return AP_UNIVERSITY;
    if (mode==G_AMBUSH) return AP_AMBUSH;
    if (mode==G_END || (mode==G_DIALOGUE && (g->dialogue==D_GOOD || g->dialogue==D_END_STAY))) return AP_ENDING_GUARDIAN+g->ending;
    if (mode==G_DIALOGUE) {
        if (g->dialogue==D_BAD || g->dialogue==D_END_LOST) return AP_ENDING_SILENT;
        if (g->dialogue==D_SECRET || g->dialogue==D_MODERN) return AP_ENDING_WITNESSES;
        if (g->dialogue==D_PROLOG) return g->page<1?AP_UNIVERSITY:(g->page==1?AP_BASEMENT:(g->page==2?AP_ARRIVAL:AP_VILLAGE_DAY));
        if (g->dialogue==D_FINAL || g->dialogue==D_FINAL_READY || g->dialogue==D_FINAL_WARNING || g->dialogue==D_REMEMBER) return AP_FINAL;
    }
    if (mode==G_CHOICE && g->choice==C_FINAL) return AP_FINAL;
    if (g->room==0) return game_daylight(g)<8?AP_VILLAGE_NIGHT:AP_VILLAGE_DAY;
    if (g->room==1) return game_daylight(g)<8?AP_FOREST_NIGHT:AP_FOREST_DAY;
    return g->room==2?AP_CHAPEL:AP_CRYPT;
}
void sound_story(SkU8 id, SkU8 page) {
    /* Cancel sounds belonging to the page the player has already left. */
    sound_reset();
    switch (id) {
    case D_PROLOG:
        if (!page) sound_emit(S_COIN_RING_01);
        if (page==1) { sound_emit(S_COIN_RING_02);sound_schedule(S_COIN_ANSWER,40);sound_schedule(S_DOOR_HANDLE_OPEN,100); }
        if (page==2) sound_emit(S_WORLD_CROSSING_ENTRY);
        break;
    case D_KIND: if (!page) sound_emit(S_ROPE_LOOSEN);break;
    case D_LOCK: if (!page) sound_emit(S_DOOR_HANDLE_CLOSE);break;
    case D_TOKEN: if (!page) { sound_emit(S_COIN_RING_02);sound_schedule(S_COIN_ANSWER,38); }break;
    case D_FOREST: if (!page) { sound_emit(S_MAGIC_TOUCH_LIGHT);sound_schedule(S_FOREST_PATH_OPEN,34); }break;
    case D_CHAPEL: if (!page) { sound_emit(S_MAGIC_TOUCH_LIGHT);sound_schedule(S_STONE_SLAB,30); }break;
    case D_REVEAL: if (page==1) sound_emit(S_COIN_ANSWER);break;
    case D_ECHO_HOME: if (!page) sound_emit(S_MEMORY_REVEAL);break;
    case D_ECHO_BOAT:
        if (!page) { sound_emit(S_BOAT_CREAK);sound_schedule(S_ROPE_STRAIN,42);sound_schedule(S_RIVER_SPLASH_01,86); }
        else { sound_emit(S_ROPE_CUT);sound_schedule(S_RIVER_SPLASH_02,28);sound_schedule(S_MEMORY_CRY,70); }
        break;
    case D_ECHO_STONE:
        if (!page) { sound_emit(S_BLACK_HEART_PULSE);sound_schedule(S_MEMORY_TAKEN,42); }
        else sound_emit(S_COIN_ANSWER);
        break;
    case D_BELL_DONE: if (!page) sound_emit(S_MEMORY_REVEAL);break;
    case D_RITUAL: case D_RITUAL_READY: if (!page) sound_emit(S_RITUAL_READY);break;
    case D_REMEMBER: if (page==2) sound_emit(S_MEMORY_RESTORED);break;
    case D_GOOD: if (!page) sound_emit(S_HEART_SEALED);break;
    case D_BAD: if (!page) sound_emit(S_MEMORY_TAKEN);break;
    case D_SECRET:
        if (!page) sound_emit(S_HEART_SEALED);
        if (page==2) { sound_emit(S_COIN_RING_01);sound_schedule(S_WORLD_CROSSING_RETURN,38); }
        break;
    case D_RETRY: if (!page) sound_emit(S_PLAYER_DEFEAT);break;
    case D_NO_LIGHT: if (!page) sound_emit(S_UI_ERROR);break;
    default: break;
    }
}
