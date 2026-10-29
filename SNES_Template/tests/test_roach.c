#include <assert.h>
#include <stdio.h>
#include "game.h"

static SkInput none;
static void press(Game *g, SkU16 button) {
    SkInput input = none;
    input.pressed = input.held = button;
    game_tick(g, &input);
}
static void start(Game *g) {
    game_new(g);
    g->mode = G_EXPLORE;
    g->x = g->destination_x = 120;
    g->y = g->destination_y = 130;
    g->fear = 100;
    g->flags = F_HEAD;
    g->evidence = 3;
    game_tick(g, &none);
    assert(g->mode == G_ROACH && g->roach_phase == ROACH_INTRO);
    assert(g->x == 120 && g->y == 130);
    press(g, SK_ACTION);
    assert(g->roach_phase == ROACH_ACTIVE && g->roach_round == 1);
}
static void next(Game *g) {
    unsigned guard = 0;
    while (g->roach_phase == ROACH_ACTIVE && g->roach_gap && ++guard < 30)
        game_tick(g, &none);
    assert(guard < 30);
}
static void hit(Game *g) {
    next(g);
    g->roach_cursor = g->roach_hole;
    press(g, SK_ACTION);
}
static void miss(Game *g) {
    unsigned guard = 0;
    next(g);
    while (g->roach_phase == ROACH_ACTIVE && g->roach_timer && ++guard < 100)
        game_tick(g, &none);
    assert(guard < 100);
}
static void boundaries(void) {
    Game g;
    unsigned i;
    start(&g);
    g.room = g.checkpoint_room = 2;
    for (i = 0; i < 4; ++i) miss(&g);
    assert(g.roach_misses == 4 && g.roach_phase == ROACH_ACTIVE);
    for (i = 0; i < 6; ++i) hit(&g);
    assert(g.roach_phase == ROACH_WON && g.roach_hits == 6 && g.roach_round == 10);
    assert(g.seconds == 0 && g.day_seconds == DAY_START_SECONDS && g.oil == 120);
    press(&g, SK_ACTION);
    assert(g.mode == G_EXPLORE && g.fear == 25 && g.hurt_timer == 90);
    assert(g.x == 120 && g.y == 130 && g.flags == F_HEAD && g.evidence == 3);
    assert(g.room == 2 && g.checkpoint_room == 2);
    start(&g);
    for (i = 0; i < 5; ++i) miss(&g);
    assert(g.roach_phase == ROACH_LOST && g.mode == G_ROACH);
    assert(g.x == 120 && g.y == 130);
    press(&g, SK_ACTION);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_RETRY);
    assert(g.x == 124 && g.y == 176 && g.fear == 15);
    assert(g.flags == F_HEAD && g.evidence == 3);
    start(&g);
    for (i = 0; i < 10; ++i) hit(&g);
    assert(g.roach_hits == 10 && !g.roach_misses && g.roach_phase == ROACH_WON);
    start(&g);
    for (i = 0; i < 6; ++i) hit(&g);
    for (i = 0; i < 4; ++i) miss(&g);
    assert(g.roach_phase == ROACH_WON && g.roach_round == 10);
    start(&g);
    for (i = 0; i < 5; ++i) hit(&g);
    for (i = 0; i < 5; ++i) miss(&g);
    assert(g.roach_phase == ROACH_LOST && g.roach_round == 10);
    press(&g, SK_PAUSE);
    assert(g.mode == G_ROACH && g.roach_phase == ROACH_LOST);
}
static void defeat_returns_to_village(void) {
    Game g;
    SkInput gun = {0};
    unsigned room, i;
    for (room = 0; room < 4; ++room) {
        start(&g);
        g.room = g.checkpoint_room = room;
        g.ambush_done = 1;
        for (i = 0; i < 5; ++i) miss(&g);
        assert(g.mode == G_ROACH && g.room == room);
        if (room & 1) {
            gun.scope = gun.fire = gun.aim_valid = 1;
            game_tick(&g, &gun);
        } else
            press(&g, SK_ACTION);
        assert(g.mode == G_DIALOGUE && g.dialogue == D_RETRY);
        assert(g.room == 0 && g.checkpoint_room == 0);
        assert(g.x == 124 && g.y == 176 && g.fear == 15);
        assert(g.flags == F_HEAD && g.evidence == 3 && g.ambush_done == 1);
    }
}
static void input_and_pause(void) {
    Game g;
    SkInput gun = {0};
    SkU8 timer;
    unsigned i;
    start(&g);
    press(&g, SK_UP); press(&g, SK_LEFT);
    assert(g.roach_cursor == 0);
    press(&g, SK_UP | SK_LEFT);
    assert(g.roach_cursor == 0);
    press(&g, SK_DOWN); press(&g, SK_DOWN);
    press(&g, SK_RIGHT); press(&g, SK_RIGHT);
    press(&g, SK_DOWN | SK_RIGHT);
    assert(g.roach_cursor == 8);
    timer = g.roach_timer;
    press(&g, SK_PAUSE);
    for (i = 0; i < 100; ++i) game_tick(&g, &none);
    assert(g.mode == G_PAUSE && g.roach_timer == timer);
    press(&g, SK_PAUSE);
    gun.scope = gun.fire = gun.aim_valid = 1;
    gun.x = roach_x(g.roach_hole); gun.y = roach_y(g.roach_hole) - 10;
    gun.offscreen = 1;
    game_tick(&g, &gun);
    assert(!g.roach_hits);
    gun.offscreen = 0;
    gun.x = 0; gun.y = 0;
    g.roach_cursor = g.roach_hole;
    game_tick(&g, &gun);
    assert(!g.roach_hits);
    gun.x = roach_x(g.roach_hole); gun.y = roach_y(g.roach_hole) - 10;
    game_tick(&g, &gun);
    assert(g.roach_hits == 1);
    /* Repeated A edges during the hit flash cannot score the same roach. */
    press(&g, SK_ACTION);
    assert(g.roach_hits == 1);
    press(&g, SK_PAUSE); press(&g, SK_DOWN); press(&g, SK_ACTION);
    assert(g.mode == G_ROACH && g.roach_phase == ROACH_INTRO && !g.roach_hits);
}
static void threshold(void) {
    Game g;
    start(&g);
    g.mode = G_EXPLORE;
    g.fear = 96;
    game_tick(&g, &none);
    assert(g.mode == G_EXPLORE);
    g.fear = 99; g.lamp = 0; g.room = 3; g.pulse = 59;
    game_tick(&g, &none);
    assert(g.fear == 100 && g.mode == G_ROACH);
    g.mode = G_EXPLORE; g.fear = 100; g.pulse = 59; g.lamp = 1;
    game_tick(&g, &none);
    assert(g.mode == G_ROACH && g.fear == 100);
}
int main(void) {
    boundaries(); defeat_returns_to_village(); input_and_pause(); threshold();
    puts("PASS: fear threshold, 10 roaches, four misses, victory, defeat, Scope, pause");
    return 0;
}
