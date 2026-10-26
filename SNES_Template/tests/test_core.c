#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "game.h"
static SkInput none;
static void press(Game *g, SkU16 button) {
    SkInput in = none;
    in.pressed = button;
    in.held = button;
    game_tick(g, &in);
}
static void finish(Game *g) {
    unsigned n = 0;
    while (g->mode == G_DIALOGUE && n++ < 100)
        press(g, SK_ACTION);
    assert(n < 100);
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
static void end_run(Game *g, SkU8 moral, SkU8 evidence, SkU8 final_option) {
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
    choice(g, final_option);
    assert(g->mode == G_END && (g->flags & F_SEALED));
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
    assert(!light_sees(&g, 128, 180));
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
    end_run(&g, 0, 7, 0);
    assert(g.ending == END_BAD);
    end_run(&g, 1, 7, 1);
    assert(g.ending == END_BAD);
    press(&g, SK_ACTION);
    assert(g.mode == G_MENU);
    press(&g, SK_ACTION);
    assert(g.flags == 0 && g.evidence == 0 && g.mode == G_DIALOGUE);
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
    assert(sizeof(Game) == 52);
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

static void test_beam_equivalence(void) {
    Game g;
    SkS16 a, b, left, right, row;
    unsigned x, y, line, dir;
    game_new(&g);
    g.lamp = 1;
    for (dir = 0; dir < 8; ++dir) {
        assert(beam_spans[dir][0][0] > beam_spans[dir][0][1]);
        g.direction = dir;
        for (x = 12; x <= 244; x += 116)
            for (y = 32; y <= 180; ++y)
                for (line = 24; line < 192; ++line) {
                    g.x = x;
                    g.y = y;
                    left = 255;
                    right = 0;
                    row = (((SkS16)line / 4) * 4 + 2 - g.y + 96) / 4;
                    if (row >= 0 && row < 49) {
                        a = beam_spans[dir][row][0];
                        b = beam_spans[dir][row][1];
                        if (a <= b) {
                            a += g.x;
                            b += g.x;
                            if (b >= 0 && a <= 255) {
                                left = a < 0 ? 0 : a;
                                right = b > 255 ? 255 : b;
                            }
                        }
                    }
                    light_span(&g, line, &a, &b);
                    assert(a == left && b == right);
                }
    }
}

int main(void) {
    test_beam_equivalence();
    test_clock_and_text();
    test_light();
    test_darkness_pause_and_recovery();
    test_puzzle_back_and_wrong_order();
    test_endings();
    test_scope_destination();
    test_optional_systems();
    puts("PASS: light, oil, fear, pause, recovery, puzzles, choices, all endings, restart, clocks");
    return 0;
}
