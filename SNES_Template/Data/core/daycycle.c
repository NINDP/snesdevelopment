#include "../include/game.h"
#include "../include/ui_text.h"

/* Thirty-two active seconds per world hour. Only exploration advances this
   clock; dialogue, puzzles, journal and pause are deliberately timeless. */
void daycycle_init(Game *g) {
    g->day_seconds = DAY_START_SECONDS;
    g->day_number = 1;
    g->sun_level = 16;
    g->time_phase = TIME_DAY;
    g->time_notice = 0;
}
void daycycle_second(Game *g) {
    SkU8 previous = g->time_phase;
    if (++g->day_seconds >= DAY_CYCLE_SECONDS) {
        g->day_seconds = 0;
        if (g->day_number < 999)
            ++g->day_number;
    }
    if (g->day_seconds < 160 || g->day_seconds >= 640) {
        g->time_phase = TIME_NIGHT;
        g->sun_level = 0;
    } else if (g->day_seconds < 224) {
        g->time_phase = TIME_DAWN;
        g->sun_level = (g->day_seconds - 160) >> 2;
    } else if (g->day_seconds < 576) {
        g->time_phase = TIME_DAY;
        g->sun_level = 16;
    } else {
        g->time_phase = TIME_DUSK;
        g->sun_level = 16 - ((g->day_seconds - 576) >> 2);
    }
    if (g->time_phase != previous) {
        g->time_notice = 180;
        if (g->time_phase == TIME_DUSK && g->nights < 999)
            ++g->nights;
    }
}
SkU8 game_daylight(const Game *g) {
    /* The chapel's windows are boarded. Neither it nor the crypt has sky. */
    return g->room < 2 ? g->sun_level : 0;
}
SkU8 game_visible(const Game *g, SkS16 x, SkS16 y) {
    if (x < 0 || x > 255 || y < 24 || y >= 192)
        return 0;
    if (game_daylight(g))
        return 1;
    return light_sees(g, x, y);
}
const char *game_time_name(const Game *g) {
    switch (g->time_phase) {
    case TIME_DAWN: return TXT_TIME_DAWN;
    case TIME_DAY: return TXT_TIME_DAY;
    case TIME_DUSK: return TXT_TIME_DUSK;
    default: return TXT_TIME_NIGHT;
    }
}
const char *game_time_event(const Game *g) {
    switch (g->time_phase) {
    case TIME_DAWN: return TXT_TIME_DAWN_EVENT;
    case TIME_DAY: return TXT_TIME_DAY_EVENT;
    case TIME_DUSK: return TXT_TIME_DUSK_EVENT;
    default: return TXT_TIME_NIGHT_EVENT;
    }
}
const char *game_time_hint(const Game *g) {
    if (g->room == 2)
        return TXT_TIME_CHAPEL_HINT;
    if (g->room == 3)
        return TXT_TIME_CRYPT_HINT;
    if (g->time_phase == TIME_DAY)
        return TXT_TIME_DAY_HINT;
    if (g->time_phase == TIME_DUSK)
        return TXT_TIME_DUSK_HINT;
    return TXT_TIME_DARK_HINT;
}
