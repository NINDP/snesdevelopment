#include <assert.h>
#include <stdio.h>
#include "game.h"

static SkInput idle;
static void tick(Game *g, SkU16 pressed) {
    SkInput in = idle;
    in.held = in.pressed = pressed;
    game_tick(g, &in);
}
static void start(Game *g) {
    game_new(g);
    g->room = g->checkpoint_room = 1;
    g->flags = F_HEAD | F_EGOR | F_FOREST | F_MIRO;
    g->evidence = 3;
    ambush_begin(g);
    while (g->ambush_timer) tick(g, 0);
    tick(g, SK_ACTION);
    assert(g->ambush_phase == AMBUSH_ACTIVE);
}
static void controls(void) {
    Game g;
    SkInput in = idle;
    SkU16 flags, clock;
    unsigned i;
    start(&g);
    flags = g.flags;
    in.scope = in.aim_valid = 1;
    in.x = 220; in.y = 60; in.pressed = SK_LIGHT;
    game_tick(&g, &in);
    assert(g.destination_x == 220 && g.y == AMBUSH_PLAYER_Y && g.lamp == 0);
    for (i = 0; i < 30; ++i) tick(&g, SK_UP);
    assert(g.x > 128 && g.y == AMBUSH_PLAYER_Y);
    clock = g.ambush_clock;
    tick(&g, SK_PAUSE);
    for (i = 0; i < 80; ++i) tick(&g, 0);
    assert(g.mode == G_PAUSE && g.ambush_clock == clock);
    tick(&g, SK_BACK);
    assert(g.mode == G_AMBUSH);
    in.pressed = 0; in.fire = 1; in.aim_valid = 0;
    game_tick(&g, &in);
    assert(!g.arrows[0].life && !g.bow_cooldown);
    in.aim_valid = 1; in.offscreen = 1;
    game_tick(&g, &in);
    assert(!g.arrows[0].life);
    in.offscreen = 0; in.x = 120; in.y = 100;
    game_tick(&g, &in);
    assert(g.arrows[0].life && g.arrows[0].dy < 0 && g.bow_cooldown);
    game_checkpoint(&g);
    assert(g.mode == G_AMBUSH && g.ambush_phase == AMBUSH_INTRO);
    assert(g.flags == flags && g.evidence == 3 && !g.ambush_done);
}
static void campaign_transition(void) {
    Game g;
    unsigned i;
    start(&g);
    for (i = 0; i < 5000 && g.mode == G_AMBUSH; ++i)
        tick(&g, SK_ACTION);
    assert(i < 5000 && g.ambush_done && g.ambush_defeated == AMBUSH_FOX_COUNT);
    assert(g.room == 2 && g.mode == G_EXPLORE && g.evidence == 3);
    assert((g.flags & (F_FOREST | F_MIRO)) == (F_FOREST | F_MIRO));
    assert(g.y == 176 && !g.bow_mode && !g.arrows[0].life);
}
static void failure_retry(void) {
    Game g;
    SkInput in = idle;
    unsigned i;
    start(&g);
    /* Walk into each telegraphed lane; no artificial damage or state writes. */
    for (i = 0; i < 7000 && (g.ambush_phase == AMBUSH_ACTIVE || g.ambush_phase == AMBUSH_BREATHER); ++i) {
        unsigned j;
        in.scope = in.aim_valid = 1;
        in.pressed = SK_LIGHT;
        in.x = g.x; in.y = 180;
        for (j = 0; j < 4; ++j)
            if (g.enemies[j].hp && g.enemies[j].y > 145) {
                in.x = g.enemies[j].x;
                break;
            }
        game_tick(&g, &in);
    }
    assert(g.ambush_phase == AMBUSH_FAILED && !g.ambush_health && !g.ambush_done);
    while (g.ambush_timer) tick(&g, 0);
    tick(&g, SK_ACTION);
    assert(g.ambush_phase == AMBUSH_ACTIVE && g.ambush_health == 3);
    assert(g.evidence == 3 && !g.ambush_defeated);
}
static void queued_trigger_and_dodge(void) {
    Game g;
    SkInput in = idle;
    unsigned i, target=0;
    SkS16 locked, previous;
    SkU8 health;
    start(&g);
    g.bow_cooldown=5;
    in.scope=in.aim_valid=in.fire=1;in.x=12;in.y=90;
    game_tick(&g,&in);
    assert(g.shot_request && !g.arrows[0].life);
    in.fire=0;
    for(i=0;i<5;++i)game_tick(&g,&in);
    assert(g.arrows[0].life && !g.shot_request);
    /* A new encounter, then dodge an actual committed attack. */
    start(&g);
    for(i=0;i<1000;++i) {
        unsigned j;
        tick(&g,0);
        for(j=0;j<4;++j)
            if(g.enemies[j].hp && g.enemies[j].state==FOX_WINDUP) { target=j;break; }
        if(j<4)break;
    }
    assert(i<1000);
    locked=(SkS16)g.enemies[target].respawn;health=g.ambush_health;
    in=idle;in.scope=in.aim_valid=1;in.x=locked<128?232:24;
    in.pressed=SK_LIGHT;
    game_tick(&g,&in);in.pressed=0;
    for(i=0;i<150 && g.enemies[target].state!=FOX_RETREAT;++i) {
        assert((SkS16)g.enemies[target].respawn==locked);
        game_tick(&g,&in);
    }
    assert(i<150 && g.ambush_health==health);
    assert(g.enemies[target].x==locked); /* Flankers reach the announced lane. */
    previous=g.enemies[target].y;
    for(i=0;i<45;++i) {
        game_tick(&g,&in);
        assert(g.enemies[target].y==previous-2);
        previous=g.enemies[target].y;
    }
    assert(g.enemies[target].hp && g.ambush_defeated==0);
    for(i=0;i<30 && g.ambush_defeated==0;++i)game_tick(&g,&in);
    assert(g.ambush_defeated==1 && g.kills==0);
}
static void wave_breather_and_feint(void) {
    Game g;
    SkInput in=idle;
    unsigned i,j;
    SkU8 feint=0,flank=0;
    start(&g);
    for(i=0;i<2000 && g.ambush_wave==0;++i)tick(&g,SK_ACTION);
    assert(g.ambush_wave==1 && g.ambush_defeated==3 && g.ambush_phase==AMBUSH_BREATHER);
    for(i=0;i<100;++i)tick(&g,0);
    assert(g.ambush_phase==AMBUSH_BREATHER && g.ambush_spawned==3);
    in.scope=in.aim_valid=1;in.pressed=SK_LIGHT;in.x=24;in.y=195;
    game_tick(&g,&in);in.pressed=0;
    for(i=0;i<900 && !feint;++i) {
        game_tick(&g,&in);
        for(j=0;j<4;++j) {
            if(g.enemies[j].hp && g.enemies[j].kind==1)flank=1;
            if(g.enemies[j].hp && g.enemies[j].state==FOX_FEINT)feint=1;
        }
    }
    assert(flank && feint && g.ambush_wave==1);
}
int main(void) {
    controls(); campaign_transition(); failure_retry(); queued_trigger_and_dodge(); wave_breather_and_feint();
    puts("PASS: horizontal Scope controls, optical validity, arrows, waves, pause, retry and chapel transition");
    return 0;
}
