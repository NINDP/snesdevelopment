#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "game.h"
#include "perspective.h"
#include "ui_text.h"
static SkInput none;
static SkU8 last_epilogue = 255;
static void press(Game *g, SkU16 button) {
    SkInput in = none;
    in.pressed = button;
    in.held = button;
    game_tick(g, &in);
}
static void finish(Game *g) {
    unsigned n = 0;
    while ((g->mode == G_DIALOGUE || g->mode == G_CORRIDOR) && n++ < 400) {
        if (g->mode == G_DIALOGUE &&
            (g->dialogue == D_MODERN || g->dialogue == D_END_STAY || g->dialogue == D_END_LOST))
            last_epilogue = g->dialogue;
        press(g, g->mode == G_CORRIDOR ? SK_RIGHT : SK_ACTION);
    }
    assert(n < 400);
}
static void inspect(Game *g, SkU8 hotspot) {
    const Hotspot *h = game_hotspot(g->room, hotspot);
    g->x = h->x;
    g->y = h->y + 22;
    g->lamp = 1;
    g->oil = 120;
    g->direction = 0;
    assert(game_nearby(g) == hotspot);
    press(g, SK_ACTION);
    finish(g);
}
static void choice(Game *g, SkU8 option) {
    assert(g->mode == G_CHOICE);
    if (option)
        press(g, SK_DOWN);
    press(g, SK_ACTION);
    finish(g);
}
static void arrive_chapel(Game *g, SkU8 moral) {
    game_new(g);
    finish(g);
    inspect(g, 0);
    inspect(g, 1);
    choice(g, moral ? 0 : 1);
    inspect(g, 3);
    assert(g->room == 1);
    inspect(g, 0);
    inspect(g, 1);
    choice(g, moral ? 0 : 1);
    inspect(g, 2);
    inspect(g, 3);
    inspect(g, 4);
    assert(g->flags & F_FOREST);
    inspect(g, 5);
    assert(g->room == 2);
    inspect(g, 0);
    inspect(g, 1);
    inspect(g, 6);
    inspect(g, 3);
    assert(g->mode == G_PUZZLE);
    press(g, SK_ACTION);
    press(g, SK_DOWN);
    press(g, SK_ACTION);
    press(g, SK_DOWN);
    press(g, SK_ACTION);
    finish(g);
    assert(g->flags & F_CHAPEL);
}
static void reach_final(Game *g, SkU8 moral, SkU8 evidence) {
    unsigned i, n;
    arrive_chapel(g, moral);
    g->evidence = evidence;
    inspect(g, 4);
    choice(g, moral ? 0 : 1);
    assert(g->room == 3);
    for (i = 0; i < 3; ++i) {
        const Hotspot *h = game_hotspot(3, i + 2);
        g->x = h->x;
        g->y = h->y + 22;
        g->direction = 0;
        g->oil = 120;
        for (n = 0; n < 80; ++n)
            game_tick(g, &none);
        assert(g->charge[i] == 60);
        inspect(g, i + 2);
    }
    assert(g->flags & F_WITNESS);
    inspect(g, 5);
    assert(g->mode == G_CHOICE && g->choice == C_FINAL);
}
static void end_run(Game *g, SkU8 moral, SkU8 evidence, SkU8 final_option) {
    reach_final(g, moral, evidence);
    last_epilogue = 255;
    choice(g, final_option);
    assert(g->mode == G_END && (g->flags & F_SEALED));
    assert(last_epilogue == (g->ending == END_SECRET ? D_MODERN :
        (g->ending == END_GOOD ? D_END_STAY : D_END_LOST)));
}
static void test_light(void) {
    Game g;
    SkS16 a, b;
    unsigned dir, y;
    game_new(&g);
    g.lamp = 1;
    g.x = 128;
    g.y = 140;
    g.direction = 0;
    assert(light_sees(&g, 128, 80));
    assert(light_sees(&g, 128, 180));
    assert(light_sees(&g, 188, 132));
    assert(light_sees(&g, 68, 132));
    assert(!light_sees(&g, 194, 132));
    assert(!light_sees(&g, 10, 80));
    g.lamp = 0;
    assert(!light_sees(&g, 128, 140));
    g.lamp = 1;
    g.oil = 0;
    assert(!light_sees(&g, 128, 80));
    g.oil = 120;
    for (dir = 0; dir < 8; ++dir)
        for (y = 24; y < 192; ++y) {
            g.direction = dir;
            light_span(&g, y, &a, &b);
            assert(a >= 0 && a <= 255 && b >= 0 && b <= 255);
        }
    assert(light_direction(100, 0) == 2);
    assert(light_direction(-100, 0) == 6);
    assert(light_direction(0, -100) == 0);
    assert(light_direction(20, 20) == 3);
}
static void test_darkness_pause_and_recovery(void) {
    Game g;
    SkU16 old_tick;
    unsigned i;
    game_new(&g);
    finish(&g);
    assert(!g.lamp);
    g.day_seconds = 640;
    g.sun_level = 0;
    g.time_phase = TIME_NIGHT;
    press(&g, SK_ACTION);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_NO_LIGHT);
    finish(&g);
    old_tick = g.tick;
    press(&g, SK_PAUSE);
    assert(g.mode == G_PAUSE);
    for (i = 0; i < 600; ++i) {
        game_tick(&g, &none);
    }
    assert(g.tick == old_tick);
    press(&g, SK_PAUSE);
    g.oil = 1;
    g.seconds = 2;
    g.pulse = 59;
    g.lamp = 1;
    game_tick(&g, &none);
    assert(g.oil == 0);
    g.flags = F_HEAD;
    g.evidence = 1;
    g.fear = 96;
    game_tick(&g, &none);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_RETRY && g.oil == 120 && g.flags == F_HEAD &&
           g.evidence == 1);
    assert(!game_can_walk(0, 20, 40));
    assert(game_can_walk(0, 128, 176));
    assert(!game_can_walk(3, -1, 80));
}
static void test_puzzle_back_and_wrong_order(void) {
    Game g;
    arrive_chapel(&g, 1);
    assert(g.room == 2);
    g.flags &= ~F_CHAPEL;
    inspect(&g, 3);
    press(&g, SK_DOWN);
    press(&g, SK_ACTION);
    assert(g.chapel_step == 0 && g.notice == 6);
    press(&g, SK_BACK);
    assert(g.mode == G_EXPLORE);
    assert(game_hotspot(4, 0) == 0 && game_hotspot(0, 20) == 0 && story_line(D_COUNT, 0) == 0);
}
static void test_endings(void) {
    Game g;
    end_run(&g, 1, 0, 0);
    assert(g.ending == END_GOOD);
    end_run(&g, 1, 7, 0);
    assert(g.ending == END_SECRET);
    end_run(&g, 0, 7, 1);
    assert(g.ending == END_BAD);
    end_run(&g, 1, 7, 1);
    assert(g.ending == END_BAD);
    press(&g, SK_ACTION);
    assert(g.mode == G_MENU);
    press(&g, SK_ACTION);
    assert(g.flags == 0 && g.evidence == 0 && g.mode == G_DIALOGUE);
}
static void test_reconciliation_and_memory(void) {
    Game g;
    SkU16 before;
    reach_final(&g, 0, 7);
    assert(g.dialogue == D_FINAL_WARNING && !(g.flags & F_SEALED));
    before = g.flags;
    press(&g, SK_BACK);
    assert(g.mode == G_EXPLORE && g.flags == before);
    inspect(&g, 5);
    choice(&g, 0);
    assert(g.mode == G_EXPLORE && g.dialogue == D_REPAIR && !(g.flags & F_SEALED));
    assert(strcmp(game_goal(&g), TXT_G_REPAIR_EGOR) == 0);
    /* Repair all three decisions through their real return paths. */
    inspect(&g, 7); inspect(&g, 8); inspect(&g, 9);
    assert(g.room == 0);
    inspect(&g, 1); choice(&g, 0);
    assert(g.flags & F_KIND);
    assert(strcmp(game_goal(&g), TXT_G_REPAIR_MIRO) == 0);
    inspect(&g, 3); inspect(&g, 1); choice(&g, 0);
    assert(g.flags & F_CONFESS);
    assert(strcmp(game_goal(&g), TXT_G_REPAIR_FREE) == 0);
    inspect(&g, 5); inspect(&g, 4); inspect(&g, 0); choice(&g, 0);
    assert(g.flags & F_FREE);
    assert(!g.memories); /* Written evidence alone restores the full memory. */
    inspect(&g, 5);
    assert(g.dialogue == D_REMEMBER);
    choice(&g, 0);
    assert(g.mode == G_END && g.ending == END_SECRET);
    /* Echoes and bells cannot claim the truth without written witnesses. */
    reach_final(&g, 1, 0);
    press(&g, SK_BACK);
    g.memories = 15;
    inspect(&g, 5);
    assert(g.dialogue == D_FINAL);
    choice(&g, 0);
    assert(g.mode == G_END && g.ending == END_GOOD);
}
static void test_scope_destination(void) {
    Game g;
    SkInput in = none;
    game_new(&g);
    finish(&g);
    g.x = 56;
    g.y = 78;
    g.lamp = 1;
    g.direction = 0;
    in.scope = 1;
    in.fire = 1;
    in.aim_valid = 1;
    in.x = 236;
    in.y = 176;
    game_tick(&g, &in);
    assert(g.mode == G_EXPLORE && g.interactions == 0);
    in.x = 56;
    in.y = 78;
    in.aim_valid = 0;
    game_tick(&g, &in);
    assert(g.mode == G_EXPLORE && g.interactions == 0);
    in.aim_valid = 1;
    game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_HEAD);
}
static void test_scope_invalid_ui(void) {
    Game g;
    SkInput in = none;
    SkU8 page;
    game_init(&g);
    g.mode = G_MENU;
    in.scope = 1;
    in.fire = 1;
    /* Noise/lost optical latch must not choose menu items or skip text. */
    game_tick(&g, &in);
    assert(g.mode == G_MENU);
    in.aim_valid = 1;
    in.offscreen = 1;
    game_tick(&g, &in);
    assert(g.mode == G_MENU);
    in.offscreen = 0;
    game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE);
    page = g.page;
    g.revealed = story_line(g.dialogue, g.page)->length;
    in.aim_valid = 0;
    game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE && g.page == page);
}
static void test_scope_billboard(void) {
    Game g;
    SkInput in = none;
    SkS16 sx, sy, wx, wy;
    game_new(&g);
    finish(&g);
    g.x = g.destination_x = 56;
    g.y = g.destination_y = 100;
    g.lamp = 1;
    assert(perspective_project(&g, 56, 78, &sx, &sy));
    assert(perspective_pick_target(&g, sx, sy - 16, &wx, &wy));
    assert(wx == 56 && wy == 78);
    assert(perspective_pick_target(&g, sx + 12, sy - 40, &wx, &wy));
    assert(wx == 56 && wy == 78); /* The new 32x48 shoulder/head silhouette. */
    in.scope = in.fire = in.aim_valid = 1;
    in.x = wx;
    in.y = wy;
    game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_HEAD);
    /* Hidden silhouettes are not target boxes when the torch is out. */
    g.lamp = 0;
    g.sun_level = 0;
    assert(perspective_pick_target(&g, sx, sy - 16, &wx, &wy));
    assert(wx != 56 || wy != 78);
    /* A foreground tree crown overlaps walkable ground. Its decorative
       root at (44,192) is outside the map and must never capture a click. */
    g.room = 1;
    g.x = 44;
    g.y = 180;
    g.direction = 4;
    g.lamp = 1;
    assert(perspective_pick_target(&g, 112, 158, &wx, &wy));
    assert(perspective_pick(&g, 112, 158, &sx, &sy));
    assert(wx == sx && wy == sy);
    assert(game_can_walk(g.room, wx, wy));
}
static void test_journal_pages(void) {
    Game g;
    SkU16 second;
    game_new(&g);
    finish(&g);
    second = g.day_seconds;
    press(&g, SK_JOURNAL);
    assert(g.mode == G_JOURNAL && g.journal_page == 0);
    press(&g, SK_RIGHT);
    assert(g.mode == G_JOURNAL && g.journal_page == 1 && g.day_seconds == second);
    press(&g, SK_LEFT);
    assert(g.journal_page == 0 && g.day_seconds == second);
    press(&g, SK_BACK);
    assert(g.mode == G_EXPLORE);
    press(&g, SK_JOURNAL);
    assert(g.journal_page == 0);
}
static void test_clock_and_text(void) {
    SkClock clock = {0};
    unsigned i, ticks = 0;
    SkU8 id, page;
    for (i = 0; i < 50; ++i) {
        ticks += sk_clock_ticks(&clock, 50);
    }
    assert(ticks == 60);
    clock.accumulator = 0;
    ticks = 0;
    for (i = 0; i < 60; ++i) {
        ticks += sk_clock_ticks(&clock, 60);
    }
    assert(ticks == 60);
    for (id = 0; id < D_COUNT; ++id)
        for (page = 0; page < story_pages(id); ++page) {
            const StoryLine *line = story_line(id, page);
            assert(strlen(line->text) <= 154);
            assert(strlen(line->text) == line->length);
        }
    assert(sizeof(Game) == 154);
}

static void test_optional_systems(void) {
    Game g;
    const Hotspot *h;
    unsigned i;
    SkU16 saved;
    game_new(&g);
    finish(&g);
    h = game_hotspot(0, 5);
    g.x = h->x;
    g.y = h->y + 22;
    g.lamp = 1;
    g.direction = 0;
    press(&g, SK_ACTION);
    assert(g.mode == G_EXPLORE && g.notice == 7);
    for (i = 0; i < 50; ++i)
        game_tick(&g, &none);
    assert(g.echo_charge == 45);
    press(&g, SK_ACTION);
    finish(&g);
    assert(g.memories == 1);
    g.lamp = 0;
    for (i = 0; i < 50; ++i)
        game_tick(&g, &none);
    assert(g.echo_charge == 0);
    press(&g, SK_BACK);
    assert(g.notice == 10);
    arrive_chapel(&g, 1);
    assert(g.wards == 3);
    g.fear = 40;
    press(&g, SK_BACK);
    assert(g.wards == 2 && g.fear <= 15 && g.ward_timer);
    inspect(&g, 6);
    assert(g.wards == 2); /* Re-reading the token cannot refill wards. */
    inspect(&g, 7);
    assert(g.mode == G_BELL);
    press(&g, SK_DOWN);
    press(&g, SK_ACTION);
    assert(g.bell_step == 0 && g.notice == 11);
    press(&g, SK_UP);
    press(&g, SK_ACTION);
    assert(g.bell_step == 1);
    press(&g, SK_PAUSE);
    saved = g.tick;
    for (i = 0; i < 100; ++i)
        game_tick(&g, &none);
    assert(g.tick == saved);
    press(&g, SK_BACK);
    assert(g.mode == G_BELL);
    /* Pause owns option; select the next bell explicitly after resuming. */
    g.option = 2;
    press(&g, SK_ACTION);
    g.option = 1;
    press(&g, SK_ACTION);
    finish(&g);
    assert(g.memories & 8);
    g.memories = 15;
    game_checkpoint(&g);
    finish(&g);
    assert(g.memories == 15 && g.wards == 2);
    g.wards = 0;
    press(&g, SK_BACK);
    assert(g.notice == 9);
    inspect(&g, 8);
    assert(g.room == 1);
    inspect(&g, 9);
    assert(g.room == 0);
}

static void test_radial_torch(void) {
    Game g;
    SkS16 a, b, expected_left, expected_right;
    int x, y, scanline, dx, dy, half, direction;
    game_new(&g);
    g.lamp = 1;
    for (x = 12; x <= 244; x += 116)
        for (y = 32; y <= 180; ++y)
            for (scanline = 24; scanline < 192; ++scanline) {
                g.x = x;
                g.y = y;
                dy = (scanline & ~3) + 10 - y;
                expected_left = 255;
                expected_right = 0;
                if (dy >= -64 && dy <= 64) {
                    half = 0;
                    while ((half + 1) * (half + 1) + dy * dy <= 64 * 64)
                        ++half;
                    expected_left = x - half < 0 ? 0 : x - half;
                    expected_right = x + half > 255 ? 255 : x + half;
                }
                light_span(&g, scanline, &a, &b);
                assert(a == expected_left && b == expected_right);
                for (direction = 0; direction < 8; ++direction) {
                    g.direction = direction;
                    for (dx = -65; dx <= 65; dx += 13)
                        assert(light_sees(&g, x + dx, scanline) ==
                               (x + dx >= 0 && x + dx <= 255 &&
                                dx * dx + dy * dy <= 64 * 64));
                }
            }
}

static void test_corridor(void) {
    Game g;
    SkInput in = none;
    unsigned i;
    game_new(&g);
    press(&g, SK_ACTION);
    press(&g, SK_ACTION);
    assert(g.mode == G_CORRIDOR && g.x == CORRIDOR_START && g.page == 1);
    for (i = 0; i < 30; ++i)
        press(&g, SK_ACTION);
    assert(g.x == CORRIDOR_START && g.mode == G_CORRIDOR);
    in.held = SK_RIGHT;
    for (i = 0; i < 100; ++i)
        game_tick(&g, &in);
    assert(g.x == 280 && game_corridor_scroll(&g) == 168);
    assert(g.oil == 120 && g.fear == 0);
    press(&g, SK_PAUSE);
    game_tick(&g, &in);
    assert(g.mode == G_PAUSE && g.x == 280);
    press(&g, SK_BACK);
    in.held = SK_LEFT;
    for (i = 0; i < 120; ++i)
        game_tick(&g, &in);
    assert(g.x == CORRIDOR_START && game_corridor_scroll(&g) == 0);
    in = none;
    in.scope = in.aim_valid = in.fire = 1;
    in.x = 221;
    game_tick(&g, &in);
    in.fire = 0;
    for (i = 0; i < 80; ++i)
        game_tick(&g, &in);
    assert(g.x == 221);
    in.held = SK_RIGHT;
    for (i = 0; i < 130; ++i)
        game_tick(&g, &in);
    assert(g.mode == G_CORRIDOR && g.y < 110 && game_corridor_scroll(&g) == 256);
    for (i = 0; i < 10; ++i)
        game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE && g.page == 1 && g.x == 124 && g.y == 176);
    finish(&g);
    assert(g.mode == G_EXPLORE && g.room == 0);
}

static void test_perspective(void) {
    Game g;
    SkS16 sx, sy, wx, wy;
    int dx, dy;
    game_new(&g);
    g.x = 128;
    g.y = 128;
    for (dy = -70; dy <= 32; dy += 3)
        for (dx = -48; dx <= 48; dx += 4) {
            assert(perspective_project(&g, g.x + dx, g.y + dy, &sx, &sy));
            assert(perspective_pick(&g, sx, sy, &wx, &wy));
            assert(wx >= g.x + dx - 3 && wx <= g.x + dx + 3);
            assert(wy >= g.y + dy - 3 && wy <= g.y + dy + 3);
        }
    assert(perspective_project(&g, g.x, g.y, &sx, &sy));
    assert(sx == 128 && sy == PERSPECTIVE_ANCHOR);
    assert(!perspective_project(&g, 128, 200, &sx, &sy));
    assert(!perspective_pick(&g, 128, 60, &wx, &wy));
    assert(!perspective_pick(&g, -1, 164, &wx, &wy));
}

static void test_daycycle(void) {
    Game g;
    unsigned i, mode;
    SkU16 day, second;
    game_new(&g);
    finish(&g);
    assert(g.day_number == 1 && g.day_seconds == DAY_START_SECONDS && g.sun_level == 16);
    assert(game_visible(&g, 20, 90) && !light_sees(&g, 20, 90));
    g.fear = 20;
    for (i = 0; i < 60; ++i)
        game_tick(&g, &none);
    assert(g.day_seconds == DAY_START_SECONDS + 1 && g.fear == 19 && g.oil == 120);
    for (mode = G_DIALOGUE; mode <= G_BELL; ++mode) {
        if (mode == G_EXPLORE || mode == G_END || mode == G_HELP || mode == G_CREDITS)
            continue;
        g.mode = mode;
        second = g.day_seconds;
        for (i = 0; i < 120; ++i)
            game_tick(&g, &none);
        assert(g.day_seconds == second);
    }
    g.mode = G_EXPLORE;
    g.day_seconds = 575;
    daycycle_second(&g);
    assert(g.time_phase == TIME_DUSK && g.sun_level == 16 && g.time_notice == 180);
    for (i = 0; i < 64; ++i)
        daycycle_second(&g);
    assert(g.time_phase == TIME_NIGHT && !game_daylight(&g));
    assert(!game_visible(&g, 20, 90));
    g.room = 1;
    game_tick(&g, &none);
    assert(g.enemy_active);
    second = g.day_seconds;
    day = g.day_number;
    g.checkpoint_room = 1;
    game_checkpoint(&g);
    assert(g.day_seconds == second && g.day_number == day);
    g.day_seconds = 767;
    daycycle_second(&g);
    assert(g.day_seconds == 0 && g.day_number == day + 1);
    for (i = 0; i < 224; ++i)
        daycycle_second(&g);
    assert(g.time_phase == TIME_DAY && g.sun_level == 16);
    g.mode = G_EXPLORE;
    game_tick(&g, &none);
    assert(!g.enemy_active);
    g.room = 2;
    assert(!game_daylight(&g));
    g.room = 3;
    game_tick(&g, &none);
    assert(!game_daylight(&g) && g.enemy_active);
    /* A full solar cycle is exact; neither tick nor elapsed-second wrap
       rewinds world time or aliases the day counter. */
    second = g.day_seconds;
    day = g.day_number;
    for (i = 0; i < DAY_CYCLE_SECONDS; ++i)
        daycycle_second(&g);
    assert(g.day_seconds == second && g.day_number == day + 1);
}

static void test_interaction_feedback(void) {
    Game g;
    SkInput in = none;
    unsigned i;
    game_new(&g); finish(&g);
    /* A diagonal approach used to select the trace at the feet and put the
       visibly nearby elder just outside the interaction diamond. */
    g.x = g.destination_x = 80; g.y = g.destination_y = 100;
    g.direction = 0;
    assert(game_nearby(&g) == 0);
    press(&g, SK_ACTION);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_HEAD);
    finish(&g);
    g.room = g.checkpoint_room = 1;
    g.x = g.destination_x = 28; g.y = g.destination_y = 166;
    g.lamp = 1; g.direction = 0;
    press(&g, SK_ACTION);
    assert(g.notice == 3 && g.notice_ticks && g.mode == G_EXPLORE);
    g.flags |= F_BIRCH;
    press(&g, SK_ACTION);
    assert(g.forest_step == 1 && g.notice == 13 && g.notice_ticks == 180);
    press(&g, SK_JOURNAL);
    for (i=0;i<90;++i) game_tick(&g,&none);
    assert(g.notice_ticks == 180);
    press(&g, SK_JOURNAL);
    g.flags |= F_MIRO | F_CONFESS;
    g.x = g.destination_x = 184; g.y = g.destination_y = 98;
    press(&g, SK_ACTION);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_CONFESS);
    finish(&g);
    assert((g.flags & F_CONFESS) && g.mode == G_EXPLORE);
    /* Explicit Scope targets must not be rejected merely because an urn
       is slightly closer to the player than the clicked silver token. */
    g.room = 2; g.x = g.destination_x = 110; g.y = g.destination_y = 138;
    g.flags |= F_PRIEST | F_TIKHON;
    in.scope = in.fire = in.aim_valid = 1; in.x = 84; in.y = 124;
    game_tick(&g, &in);
    assert(g.mode == G_DIALOGUE && g.dialogue == D_TOKEN && g.last_hotspot == 6);
}

int main(void) {
    test_reconciliation_and_memory();
    test_interaction_feedback();
    test_daycycle();
    test_perspective();
    test_corridor();
    test_radial_torch();
    test_clock_and_text();
    test_journal_pages();
    test_light();
    test_darkness_pause_and_recovery();
    test_puzzle_back_and_wrong_order();
    test_endings();
    test_scope_destination();
    test_scope_invalid_ui();
    test_scope_billboard();
    test_optional_systems();
    puts("PASS: radial torch, fuel, fear, pause, recovery, puzzles, choices, all endings, restart, clocks");
    return 0;
}
