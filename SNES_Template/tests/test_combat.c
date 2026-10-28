#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "game.h"
#include "perspective.h"

static const SkInput idle = {0};

static void ticks(Game *g, unsigned count, SkU16 held) {
    SkInput in = idle;
    in.held = held;
    while (count--)
        game_tick(g, &in);
}

static void press(Game *g, SkU16 key) {
    SkInput in = idle;
    in.pressed = in.held = key;
    game_tick(g, &in);
}

static void arena(Game *g, SkU8 room) {
    game_new(g);
    g->mode = G_EXPLORE;
    g->room = g->checkpoint_room = room;
    g->day_seconds = 660;
    g->time_phase = TIME_NIGHT;
    g->sun_level = 0;
    g->lamp = 1;
    g->x = g->destination_x = 128;
    g->y = g->destination_y = 170;
    g->ward_timer = 200;
    combat_enter(g);
}

static void draw(Game *g, unsigned count) {
    SkInput in = idle;
    in.pressed = SK_ACTION;
    in.held = SK_ACTION;
    game_tick(g, &in);
    if (count > 1)
        ticks(g, count - 1, SK_ACTION);
}

static unsigned flying(const Game *g) {
    unsigned i, count = 0;
    for (i = 0; i < COMBAT_ARROWS; ++i)
        count += g->arrows[i].life && g->arrows[i].damage;
    return count;
}

static void test_layout(void) {
    assert(sizeof(Game) == 154);
    assert(offsetof(Game, day_seconds) == 52);
    assert(offsetof(Game, nights) == 60);
    assert(offsetof(Game, enemies) == 76);
    assert(offsetof(Game, arrows) == 124);
    assert(offsetof(Game, notice_ticks) == 148 && offsetof(Game, hit_stop) == 152);
    assert(sizeof(Enemy) == 12 && sizeof(Arrow) == 8);
}

static void test_nights_and_capacity(void) {
    Game g;
    unsigned night, expected, index, actual;
    arena(&g, 1);
    g.nights = 0;
    for (night = 1; night <= 7; ++night) {
        g.day_seconds = 575;
        g.time_phase = TIME_DAY;
        daycycle_second(&g);
        assert(g.nights == night);
        expected = night > 4 ? 4 : night;
        assert(combat_tier(&g) == expected - 1);
        g.sun_level = 0;
        assert(combat_capacity(&g) == expected);
        g.room = 3;
        assert(combat_capacity(&g) == expected);
        combat_enter(&g);
        actual = 0;
        for (index = 0; index < COMBAT_ENEMIES; ++index)
            actual += g.enemies[index].hp != 0;
        assert(actual == expected);
        if (night >= 3)
            assert(g.enemies[1].kind && g.enemies[1].hp == 2);
        g.room = 0;
        assert(combat_capacity(&g) == expected - 1);
        g.room = 2;
        assert(combat_capacity(&g) == 0);
        g.room = 1;
        g.sun_level = 16;
        assert(combat_capacity(&g) == 0);
        daycycle_second(&g);
        assert(g.nights == night); /* One escalation per dusk. */
    }
    g.nights = 65535;
    g.day_seconds = 575;
    g.time_phase = TIME_DAY;
    daycycle_second(&g);
    assert(g.nights == 65535);
    g.day_seconds = 767;
    g.time_phase = TIME_NIGHT;
    daycycle_second(&g);
    assert(g.nights == 65535); /* Midnight does not add a second escalation. */
}

static void test_later_nights_move_faster(void) {
    Game first, later;
    unsigned i;
    arena(&first, 3);
    first.nights = 1;
    first.ward_timer = 0;
    first.lamp = 0;
    combat_enter(&first);
    later = first;
    later.nights = 4;
    combat_enter(&later);
    for (i = 0; i < 80; ++i) {
        combat_tick(&first, &idle);
        combat_tick(&later, &idle);
    }
    assert(later.enemies[0].x < first.enemies[0].x);
    assert(later.enemies[0].y > first.enemies[0].y);
}

static void test_crawlers_push_through_fire(void) {
    Game shadow, crawler, unlit;
    unsigned i, lit_windup = 80, dark_windup = 80;
    arena(&shadow, 3);
    shadow.nights = 4;
    shadow.ward_timer = 0;
    combat_enter(&shadow);
    shadow.enemies[0].x = 148;
    shadow.enemies[0].y = 170;
    shadow.enemies[0].attack = shadow.enemies[0].step = 0;
    shadow.enemies[0].kind = 0;
    crawler = shadow;
    crawler.enemies[0].kind = 1;
    crawler.enemies[0].hp = 2;
    unlit = crawler;
    unlit.lamp = 0;
    assert(light_sees(&shadow, 148, 170));
    for (i = 0; i < 80; ++i) {
        game_tick(&shadow, &idle);
        game_tick(&crawler, &idle);
        game_tick(&unlit, &idle);
        if (crawler.enemies[0].state == ENEMY_WINDUP && lit_windup == 80) lit_windup = i;
        if (unlit.enemies[0].state == ENEMY_WINDUP && dark_windup == 80) dark_windup = i;
    }
    assert(shadow.enemies[0].x >= 148 && !shadow.fear);
    assert(crawler.enemies[0].x < 148 && crawler.fear > 0);
    assert(lit_windup >= dark_windup && lit_windup < 80);
}

static void test_dawn_clears_defeated_actors(void) {
    Game g;
    unsigned i;
    arena(&g, 1);
    g.nights = 4;
    g.enemy_active = 0;
    memset(g.enemies, 0, sizeof(g.enemies));
    g.enemies[0].hit = 12;
    g.enemies[0].respawn = 600;
    g.day_seconds = 192;
    g.time_phase = TIME_DAWN;
    g.sun_level = 8;
    combat_tick(&g, &idle);
    for (i = 0; i < COMBAT_ENEMIES; ++i)
        assert(!g.enemies[i].hp && !g.enemies[i].hit && !g.enemies[i].respawn);
    g.day_seconds = 640;
    g.time_phase = TIME_NIGHT;
    g.sun_level = 0;
    combat_tick(&g, &idle);
    for (i = 0; i < COMBAT_ENEMIES; ++i)
        assert(g.enemies[i].hp);
}

static void test_draw_ammo_and_cooldown(void) {
    Game g;
    SkS16 x, y;
    arena(&g, 2);
    assert(g.ammo == BOW_AMMO_MAX && !g.bow_mode);
    press(&g, SK_TURN_LEFT);
    assert(g.bow_mode);
    x = g.x;
    y = g.y;
    ticks(&g, 5, SK_ACTION | SK_RIGHT);
    assert(g.x == x && g.y == y && g.bow_draw > 0);
    ticks(&g, 1, 0);
    assert(g.ammo == BOW_AMMO_MAX && !flying(&g));
    draw(&g, BOW_DRAW_TICKS + 30);
    assert(g.bow_draw == BOW_DRAW_TICKS && g.ammo == BOW_AMMO_MAX);
    ticks(&g, 1, 0);
    assert(g.ammo == BOW_AMMO_MAX - 1 && flying(&g) == 1 && g.bow_cooldown);
    draw(&g, 6);
    ticks(&g, 1, 0);
    assert(g.ammo == BOW_AMMO_MAX - 1); /* Cooldown rejects a rapid second shot. */
    ticks(&g, 80, 0);
    assert(!g.bow_cooldown && !flying(&g));
    g.ammo = 0;
    draw(&g, BOW_DRAW_TICKS);
    ticks(&g, 1, 0);
    assert(!flying(&g) && !g.ammo);
    press(&g, SK_TURN_LEFT);
    assert(!g.bow_mode && !g.bow_draw);
}

static void test_projectile_damage(void) {
    Game g;
    unsigned i;
    arena(&g, 3);
    g.enemies[0].x = 128;
    g.enemies[0].y = 120;
    g.enemies[0].hp = 2;
    g.enemies[0].respawn = 0;
    g.direction = 0;
    press(&g, SK_TURN_LEFT);
    draw(&g, BOW_DRAW_TICKS);
    ticks(&g, 1, 0);
    assert(g.ammo == BOW_AMMO_MAX - 1 && flying(&g));
    for (i = 0; i < 60 && !g.kills; ++i)
        ticks(&g, 1, 0);
    assert(g.kills == 1 && !g.enemies[0].hp && g.enemies[0].respawn);
    assert(!flying(&g));
    /* A defeated creature stays dead for a real interval. */
    ticks(&g, 60, 0);
    assert(!g.enemies[0].hp && g.enemies[0].respawn);
}

static void test_partial_damage_and_enemy_pick(void) {
    Game g;
    SkS16 sx, sy, wx, wy;
    unsigned i;
    arena(&g, 3);
    g.enemies[0].x = 128;
    g.enemies[0].y = 120;
    g.enemies[0].hp = 2;
    g.enemies[0].respawn = 0;
    g.direction = 0;
    press(&g, SK_TURN_LEFT);
    assert(perspective_project(&g, 128, 120, &sx, &sy));
    assert(combat_pick(&g, sx, sy - 16, &wx, &wy) && wx == 128 && wy == 120);
    g.lamp = 0;
    assert(!combat_pick(&g, sx, sy - 16, &wx, &wy));
    g.lamp = 1;
    draw(&g, 6);
    ticks(&g, 1, 0);
    for (i = 0; i < 20 && g.enemies[0].hp == 2; ++i)
        ticks(&g, 1, 0);
    assert(g.enemies[0].hp == 1 && !g.kills);
    assert(combat_direction(0, -100) == 0);
    assert(combat_direction(100, 0) == 4);
    assert(combat_direction(0, 100) == 8);
    assert(combat_direction(-100, 0) == 12);
    assert(combat_direction(100, -100) == 2);
    assert(combat_direction(-100, -100) == 14);
}

static void test_ward_preserves_wounds(void) {
    Game g;
    arena(&g, 3);
    g.nights = 3;
    combat_enter(&g);
    assert(g.enemies[1].hp == 2);
    g.enemies[1].hp = 1;
    g.enemies[1].x = g.x + 2;
    g.enemies[1].y = g.y;
    g.enemies[2].hp = 0;
    g.enemies[2].respawn = 500;
    combat_ward(&g);
    assert(g.enemies[1].hp == 1 && g.enemies[1].hit);
    assert(g.enemies[1].x != g.x + 2 || g.enemies[1].y != g.y);
    assert(!g.enemies[2].hp && g.enemies[2].respawn == 500);
}

static void test_walls_and_npc_safety(void) {
    Game g;
    SkU16 flags, interactions;
    unsigned i;
    arena(&g, 0);
    g.nights = 2;
    combat_enter(&g);
    g.x = g.destination_x = 48;
    g.y = g.destination_y = 90;
    g.direction = 0;
    g.enemies[0].x = 48;
    g.enemies[0].y = 40;
    g.enemies[0].hp = 1;
    press(&g, SK_TURN_LEFT);
    draw(&g, BOW_DRAW_TICKS);
    ticks(&g, 1, 0);
    for (i = 0; i < 60; ++i)
        ticks(&g, 1, 0);
    assert(!g.kills && g.enemies[0].hp == 1); /* The solid building stops the arrow. */
    arena(&g, 0);
    g.x = g.destination_x = 56;
    g.y = g.destination_y = 112;
    flags = g.flags;
    interactions = g.interactions;
    press(&g, SK_TURN_LEFT);
    draw(&g, BOW_DRAW_TICKS);
    ticks(&g, 60, 0);
    assert(g.mode == G_EXPLORE && g.flags == flags && g.interactions == interactions);
    press(&g, SK_TURN_LEFT);
    g.ammo = 1;
    g.x = g.destination_x = 116;
    g.y = g.destination_y = 180;
    press(&g, SK_ACTION);
    assert(g.ammo == BOW_AMMO_MAX);
}

static void test_scope_and_freeze(void) {
    Game g;
    SkInput in = idle;
    SkU8 ammo;
    Arrow arrows[COMBAT_ARROWS];
    Enemy enemies[COMBAT_ENEMIES];
    unsigned i;
    arena(&g, 2);
    press(&g, SK_TURN_LEFT);
    in.scope = in.fire = 1;
    in.x = 128;
    in.y = 80;
    for (i = 0; i < 30; ++i)
        game_tick(&g, &in);
    assert(!g.bow_draw && !g.shot_request && g.ammo == BOW_AMMO_MAX);
    in.aim_valid = 1;
    in.offscreen = 1;
    for (i = 0; i < 30; ++i)
        game_tick(&g, &in);
    assert(!g.bow_draw && !g.shot_request && g.ammo == BOW_AMMO_MAX);
    in.offscreen = 0;
    game_tick(&g, &in);
    in.fire = 0;
    in.aim_valid = 0; /* An idle Scope packet has no fresh optical latch. */
    for (i = 0; i < BOW_DRAW_TICKS + 2; ++i)
        game_tick(&g, &in);
    assert(g.ammo == BOW_AMMO_MAX - 1 && flying(&g));
    memcpy(arrows, g.arrows, sizeof(arrows));
    memcpy(enemies, g.enemies, sizeof(enemies));
    ammo = g.ammo;
    press(&g, SK_PAUSE);
    ticks(&g, 120, SK_ACTION);
    assert(g.ammo == ammo && !memcmp(arrows, g.arrows, sizeof(arrows)) &&
           !memcmp(enemies, g.enemies, sizeof(enemies)));
    press(&g, SK_PAUSE);
    press(&g, SK_JOURNAL);
    memcpy(arrows, g.arrows, sizeof(arrows));
    ticks(&g, 120, SK_ACTION);
    assert(g.ammo == ammo && !memcmp(arrows, g.arrows, sizeof(arrows)));
    g.mode = G_EXPLORE;
    g.ammo = 1;
    g.nights = 3;
    game_checkpoint(&g);
    assert(g.ammo == BOW_AMMO_MAX && g.nights == 3 && !g.bow_mode && !flying(&g));
}

static void test_pad_bow_with_scope_connected(void) {
    Game g;
    SkInput in = idle;
    unsigned i;
    arena(&g, 2);
    press(&g, SK_TURN_LEFT);
    in.scope = 1;
    in.held = SK_ACTION;
    for (i = 0; i < BOW_DRAW_TICKS; ++i)
        game_tick(&g, &in);
    assert(g.bow_draw == BOW_DRAW_TICKS && g.ammo == BOW_AMMO_MAX);
    in.held = 0;
    game_tick(&g, &in);
    assert(g.ammo == BOW_AMMO_MAX - 1 && flying(&g));
}

static void test_telegraphed_attack_and_dodge(void) {
    Game hit, dodge;
    unsigned i;
    arena(&hit, 3);
    hit.ward_timer = hit.lamp = 0;
    hit.enemies[0].x = hit.x;
    hit.enemies[0].y = hit.y - 24;
    hit.enemies[0].attack = hit.enemies[0].step = 0;
    for (i = 0; i < 8; ++i) combat_tick(&hit, &idle);
    assert(hit.enemies[0].state == ENEMY_WINDUP && !hit.fear);
    dodge = hit;
    dodge.x += 48;
    for (i = 0; i < 16; ++i) {
        combat_tick(&hit, &idle);
        combat_tick(&dodge, &idle);
        assert(!hit.fear && !dodge.fear);
    }
    assert(hit.enemies[0].state == ENEMY_WINDUP);
    for (i = 0; i < 23; ++i) {
        combat_tick(&hit, &idle);
        combat_tick(&dodge, &idle);
    }
    assert(hit.fear == 4 && hit.hurt_timer);
    assert(hit.enemies[0].state == ENEMY_RECOVER);
    assert(!dodge.fear && dodge.enemies[0].x == 128);
    assert(dodge.enemies[0].state == ENEMY_RECOVER);
    /* Recovery gives a real interval to draw or walk away. */
    for (i = 0; i < 20; ++i) combat_tick(&hit, &idle);
    assert(hit.fear == 4);
}

static void test_group_damage_and_interrupt(void) {
    Game g;
    SkInput held = idle;
    unsigned i;
    arena(&g, 3);
    g.nights = 4;
    combat_enter(&g);
    g.ward_timer = g.lamp = 0;
    g.bow_mode = 1;
    g.bow_draw = BOW_DRAW_TICKS;
    g.shot_request = 1;
    for (i = 0; i < COMBAT_ENEMIES; ++i) {
        g.enemies[i].x = g.x;
        g.enemies[i].y = g.y - 2;
        g.enemies[i].state = ENEMY_LUNGE;
        g.enemies[i].step = 4;
        g.enemies[i].attack = 10;
    }
    held.held = SK_ACTION;
    combat_tick(&g, &held);
    assert(g.fear == 10 && g.hurt_timer == 45);
    assert(!g.bow_draw && !g.shot_request);
    assert(g.ammo == BOW_AMMO_MAX); /* Being hit cancels a held shot without spending ammo. */
    g.fear = 254;
    g.hurt_timer = 0;
    combat_tick(&g, &idle);
    combat_tick(&g, &idle);
    assert(g.fear == 100); /* No byte wrap near a checkpoint. */
}

static void test_shove_cone_cooldown_and_walls(void) {
    Game g;
    SkS16 front, back;
    arena(&g, 3);
    g.nights = 2;
    combat_enter(&g);
    g.direction = 0;
    g.bow_mode = 1;
    g.bow_draw = BOW_DRAW_TICKS;
    g.shot_request = 1;
    g.enemies[0].x = g.enemies[1].x = g.x;
    g.enemies[0].y = g.y - 20;
    g.enemies[1].y = g.y + 10;
    g.enemies[0].state = ENEMY_WINDUP;
    g.enemies[0].attack = 20;
    press(&g, SK_SHOVE);
    assert(g.shove_cooldown == SHOVE_COOLDOWN && g.ammo == BOW_AMMO_MAX);
    assert(!g.bow_draw && !g.shot_request);
    assert(g.enemies[0].y == g.y - 32 && g.enemies[0].state == ENEMY_RECOVER);
    assert(g.enemies[1].y == g.y + 10 && g.enemies[1].state == ENEMY_HUNT);
    front = g.enemies[0].y; back = g.enemies[1].y;
    press(&g, SK_SHOVE);
    assert(g.shove_cooldown == SHOVE_COOLDOWN - 1);
    assert(g.enemies[0].y == front && g.enemies[1].y == back);
    ticks(&g, SHOVE_COOLDOWN, 0);
    assert(!g.shove_cooldown);
    /* A shove cannot push an actor through the village building. */
    arena(&g, 0);
    g.nights = 2;
    combat_enter(&g);
    g.x = g.destination_x = 48;
    g.y = g.destination_y = 90;
    g.direction = 0;
    g.enemies[0].x = 48; g.enemies[0].y = 68;
    press(&g, SK_SHOVE);
    assert(g.enemies[0].y == 63 && game_can_walk(g.room, 48, 63));
}

static void test_arrow_stagger_and_precision(void) {
    Game g;
    SkInput scope = idle;
    Arrow *arrow;
    unsigned i;
    arena(&g, 3);
    g.ward_timer = 0;
    g.enemies[0].x = g.x;
    g.enemies[0].y = g.y - 20;
    g.enemies[0].hp = 2;
    g.enemies[0].state = ENEMY_LUNGE;
    g.enemies[0].attack = 10;
    g.enemies[0].step = 4;
    arrow = &g.arrows[0];
    arrow->x = g.x * 4; arrow->y = (g.y - 12) * 4;
    arrow->dx = 0; arrow->dy = -24; arrow->life = 20; arrow->damage = 1;
    combat_tick(&g, &idle);
    assert(g.enemies[0].hp == 1 && g.enemies[0].state == ENEMY_RECOVER);
    assert(g.enemies[0].y == g.y - 24 && !g.fear);
    arena(&g, 2);
    press(&g, SK_TURN_LEFT);
    scope.scope = scope.fire = scope.aim_valid = 1;
    scope.x = g.x + 21; scope.y = g.y - 80;
    combat_tick(&g, &scope);
    scope.fire = scope.aim_valid = 0;
    for (i = 1; i < BOW_DRAW_TICKS; ++i) combat_tick(&g, &scope);
    arrow = &g.arrows[0];
    assert(g.ammo == BOW_AMMO_MAX - 1 && arrow->damage == 2);
    assert(arrow->dx > 0 && arrow->dy < 0);
    assert(abs(arrow->dx * 80 + arrow->dy * 21) <= 80);
    assert(abs(arrow->dx) <= 24 && abs(arrow->dy) <= 24);
    /* Pad assistance catches a small offset, without needing a hidden lock. */
    arena(&g, 3);
    g.enemies[0].x = 136; g.enemies[0].y = 120; g.enemies[0].hp = 2;
    g.direction = 0;
    press(&g, SK_TURN_LEFT);
    draw(&g, BOW_DRAW_TICKS);
    assert(g.aim_x == 136 && g.aim_y == 120);
    ticks(&g, 30, 0);
    assert(g.kills == 1);
    arena(&g, 3);
    g.lamp = 0;
    g.enemies[0].x = 136; g.enemies[0].y = 120;
    g.direction = 0;
    press(&g, SK_TURN_LEFT);
    draw(&g, BOW_DRAW_TICKS);
    assert(g.aim_x == g.x && g.aim_y == g.y - 48);
}

static void test_combat_timers_freeze_and_light_interrupt(void) {
    Game g;
    SkU8 hurt, shove_ticks;
    arena(&g, 3);
    press(&g, SK_SHOVE);
    g.hurt_timer = 40;
    hurt = g.hurt_timer; shove_ticks = g.shove_cooldown;
    press(&g, SK_PAUSE);
    ticks(&g, 120, 0);
    assert(g.hurt_timer == hurt && g.shove_cooldown == shove_ticks);
    press(&g, SK_PAUSE);
    press(&g, SK_JOURNAL);
    ticks(&g, 120, 0);
    assert(g.hurt_timer == hurt && g.shove_cooldown == shove_ticks);
    arena(&g, 3);
    g.ward_timer = 0;
    g.enemies[0].x = g.x; g.enemies[0].y = g.y - 20;
    g.enemies[0].state = ENEMY_WINDUP;
    g.enemies[0].attack = 10;
    combat_tick(&g, &idle);
    assert(g.enemies[0].state == ENEMY_RECOVER && !g.fear);
}

static void test_footwork_and_impact_input(void) {
    Game g;
    SkS16 x, y;
    SkInput shove_input = idle;
    arena(&g, 2);
    press(&g, SK_TURN_LEFT);
    x = g.x; y = g.y;
    ticks(&g, 20, SK_RIGHT);
    assert(g.x == x + 10 && g.y == y && g.bow_mode);
    x = g.x;
    ticks(&g, 20, SK_ACTION | SK_LEFT);
    assert(g.x == x && g.bow_draw == BOW_DRAW_TICKS);
    assert(g.ammo == BOW_AMMO_MAX);
    /* A three-tick impact pause must not swallow a fresh defensive input. */
    g.hit_stop = 3;
    shove_input.pressed = SK_SHOVE;
    combat_tick(&g, &shove_input);
    assert(g.shove_cooldown == SHOVE_COOLDOWN && g.hit_stop == 2);
    assert(!g.bow_draw && g.ammo == BOW_AMMO_MAX);
    g.mode = G_PAUSE;
    combat_tick(&g, &idle);
    assert(g.hit_stop == 2);
}

static void test_planted_torch_exposes_the_archer(void) {
    Game g;
    unsigned i;
    SkInput held = idle;
    arena(&g, 3);
    g.ward_timer = 0;
    g.bow_mode = 1;
    g.enemies[0].kind = ENEMY_SHADE;
    g.enemies[0].x = g.x; g.enemies[0].y = g.y - 24;
    g.enemies[0].attack = g.enemies[0].step = 0;
    held.held = SK_ACTION;
    for (i = 0; i < 45; ++i) combat_tick(&g, &held);
    assert(g.hurt_timer && g.fear == 4 && g.ammo == BOW_AMMO_MAX);
}

int main(void) {
    test_layout();
    test_nights_and_capacity();
    test_later_nights_move_faster();
    test_crawlers_push_through_fire();
    test_dawn_clears_defeated_actors();
    test_draw_ammo_and_cooldown();
    test_projectile_damage();
    test_partial_damage_and_enemy_pick();
    test_ward_preserves_wounds();
    test_walls_and_npc_safety();
    test_scope_and_freeze();
    test_pad_bow_with_scope_connected();
    test_telegraphed_attack_and_dodge();
    test_group_damage_and_interrupt();
    test_shove_cone_cooldown_and_walls();
    test_arrow_stagger_and_precision();
    test_combat_timers_freeze_and_light_interrupt();
    test_footwork_and_impact_input();
    test_planted_torch_exposes_the_archer();
    puts("PASS: bow precision, stagger, telegraphs, dodge, shove, group protection, nights, Scope, pause and NPC safety");
    return 0;
}
