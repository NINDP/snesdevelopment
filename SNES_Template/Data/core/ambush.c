#include <string.h>
#include "../include/game.h"
#include "../include/audio.h"

static const SkU8 lanes[8] = {42,210,84,174,58,196,112,150};
static const SkU8 wave_end[3] = {3,7,12};
#define absolute(n) ((n) < 0 ? -(n) : (n))

SkU8 ambush_fox_lod(SkS16 y) {
    if (y < 102) return 0;
    if (y < 116) return 1;
    if (y < 130) return 2;
    if (y < 144) return 3;
    if (y < 158) return 4;
    if (y < 172) return 5;
    if (y < 186) return 6;
    return 7;
}
SkU8 ambush_fox_width(SkS16 y) {
    static const SkU8 widths[8] = {16,20,24,28,36,44,52,60};
    return widths[ambush_fox_lod(y)];
}
static SkS16 clamp_x(SkS16 x) {
    if (x < 24) return 24;
    return x > 232 ? 232 : x;
}
static void step_x(Enemy *fox, SkS16 target, SkU8 speed) {
    if (fox->x < target) {
        fox->x += speed;
        if (fox->x > target) fox->x = target;
    } else if (fox->x > target) {
        fox->x -= speed;
        if (fox->x < target) fox->x = target;
    }
}
void ambush_begin(Game *g) {
    memset(g->enemies, 0, sizeof(g->enemies));
    memset(g->arrows, 0, sizeof(g->arrows));
    sound_reset();
    g->mode = G_AMBUSH;
    g->x = g->destination_x = 128;
    g->y = g->destination_y = AMBUSH_PLAYER_Y;
    g->direction = 0;
    g->ambush_phase = AMBUSH_INTRO;
    g->ambush_wave = g->ambush_spawned = g->ambush_defeated = 0;
    g->ambush_clock = g->ambush_aim_ticks = 0;
    g->ambush_health = 3;
    g->ambush_timer = 18;
    g->enemy_slots = 4;
    g->enemy_active = 0;
    g->bow_mode = 1;
    g->bow_draw = g->bow_cooldown = g->shot_request = g->hurt_timer = 0;
    g->combat_notice = g->combat_notice_ticks = g->notice_ticks = 0;
    g->focus = SK_NONE;
}
static void queue_shot(Game *g, SkS16 x, SkS16 y) {
    if (x < 8 || x > 247 || y < 72 || y > 201) return;
    g->aim_x = x; g->aim_y = y;
    g->shot_request = 1;
    g->ambush_aim_ticks = 30;
    g->combat_notice = 0;
}
static void release_shot(Game *g) {
    SkU8 i;
    SkS16 dx,dy,longest;
    Arrow *arrow;
    if (g->shot_request == 0 || g->bow_cooldown) return;
    for (i=0;i<COMBAT_ARROWS;++i) {
        arrow=&g->arrows[i];
        if (arrow->life) continue;
        dx=g->aim_x-g->x;dy=g->aim_y-164;
        longest=absolute(dx);
        if (absolute(dy)>longest) longest=absolute(dy);
        if (longest==0) { longest=1;dy=-1; }
        arrow->x=g->x*4;arrow->y=164*4;
        arrow->dx=(SkS8)(dx*40/longest);
        arrow->dy=(SkS8)(dy*40/longest);
        arrow->life=32;arrow->damage=1;
        sound_emit(S_BOW_RELEASE_STRONG);
        g->bow_cooldown=11;
        g->shot_request=0;
        return;
    }
}
static void arrows(Game *g) {
    SkU8 i,j,sub,width,height;
    SkS16 x,y,start_x,start_y;
    Arrow *arrow;
    Enemy *fox;
    for (i=0;i<COMBAT_ARROWS;++i) {
        arrow=&g->arrows[i];
        if (arrow->life==0) continue;
        --arrow->life;
        start_x=arrow->x;start_y=arrow->y;
        /* Sweep four short segments, including small distant targets. */
        for (sub=1;sub<=4;++sub) {
            x=(start_x+arrow->dx*sub/4)/4;
            y=(start_y+arrow->dy*sub/4)/4;
            for (j=0;j<4;++j) {
                fox=&g->enemies[j];
                if (fox->hp==0) continue;
                width=ambush_fox_width(fox->y);height=(width*3)>>2;
                if (absolute(x-fox->x)>width/2+2) continue;
                if (y<fox->y-height-2 || y>fox->y+2) continue;
                sound_emit(sound_variant(S_FOX_HURT_01,2));
                sound_schedule(S_FOX_DISSOLVE,10);
                fox->hp=0;fox->hit=22;
                arrow->life=0;
                ++g->ambush_defeated;++g->kills;
                g->combat_notice=1;g->ambush_aim_ticks=18;
                break;
            }
            if (arrow->life==0) break;
        }
        arrow->x=start_x+arrow->dx;arrow->y=start_y+arrow->dy;
        if (arrow->x<0 || arrow->x>1020 || arrow->y<280 || arrow->y>820)
            arrow->life=0;
    }
}
static void movement(Game *g,const SkInput *in,SkU8 valid) {
    if (valid && (in->pressed & SK_LIGHT)) g->destination_x=clamp_x(in->x);
    if (in->scope==0) {
        g->destination_x=g->x;
        if (in->held & SK_LEFT) g->destination_x=24;
        if (in->held & SK_RIGHT) g->destination_x=232;
    }
    if (g->x<g->destination_x) {
        g->x+=3;if(g->x>g->destination_x)g->x=g->destination_x;
    } else if(g->x>g->destination_x) {
        g->x-=3;if(g->x<g->destination_x)g->x=g->destination_x;
    }
    g->y=g->destination_y=AMBUSH_PLAYER_Y;
}
static void pack(Game *g) {
    SkU8 i,kind;
    SkS16 target;
    Enemy *fox;
    for(i=0;i<4;++i) {
        fox=&g->enemies[i];
        if(fox->hit)--fox->hit;
        if(fox->hp==0)continue;
        ++fox->step;
        if(fox->state==FOX_RETREAT) {
            fox->y-=2;step_x(fox,(SkS16)fox->respawn,1);
            if(fox->y<88) {
                fox->hp=0;
                ++g->ambush_defeated;
            }
            continue;
        }
        if(fox->state==FOX_WINDUP) {
            if(fox->attack)--fox->attack;
            else {
                sound_emit(S_FOX_CHARGE);
                fox->state=FOX_CHARGE;
                fox->attack=(SkU8)((absolute((SkS16)fox->respawn-fox->x)+28)/29);
                if(fox->attack==0)fox->attack=1;
            }
            continue;
        }
        if(fox->state==FOX_FEINT) {
            step_x(fox,(SkS16)fox->respawn,2);
            if(fox->attack)--fox->attack;
            else {
                sound_emit(sound_variant(S_FOX_WARNING_01,2));
                fox->state=FOX_WINDUP;
                fox->respawn=g->x;
                fox->attack=38;
            }
            continue;
        }
        if(fox->state==FOX_CHARGE) {
            fox->y+=2;
            step_x(fox,(SkS16)fox->respawn,fox->attack);
            if(fox->y>=198) {
                if(absolute(fox->x-g->x)<27 && g->hurt_timer==0) {
                    sound_emit(sound_variant(S_PLAYER_HURT_01,2));
                    --g->ambush_health;g->hurt_timer=60;
                }
                sound_emit(S_FOX_RETREAT);
                fox->state=FOX_RETREAT;
                fox->respawn=fox->x<128?24:232;
                fox->attack=0;
            }
            continue;
        }
        if(fox->attack) { --fox->attack;continue; }
        /* Scouts pause and fan out; attacks commit to one announced lane. */
        if(fox->step%3==0)++fox->y;
        if((fox->step&3)==0) {
            target=fox->kind==1?(fox->x<128?44:212):g->x;
            step_x(fox,target,1);
        }
        if(fox->y>=140) {
            kind=fox->kind;
            if(kind==2) {
                fox->state=FOX_FEINT;
                fox->respawn=clamp_x(fox->x+(fox->x<128?30:-30));
                fox->attack=20;
            } else {
                sound_emit(sound_variant(S_FOX_WARNING_01,2));
                fox->state=FOX_WINDUP;
                fox->respawn=g->x;
                fox->attack=46-g->ambush_wave*4;
            }
        }
    }
}
SkU8 ambush_tick(Game *g,const SkInput *in) {
    SkU8 i,valid=in->scope && in->aim_valid && !in->offscreen;
    SkU8 advance=(in->pressed & SK_ACTION) || (valid && in->fire);
    SkU8 wanted,alive=0,limit;
    SkS16 tx=128,ty=90,nearest=0;
    Enemy *fox;
    if(g->ambush_phase==AMBUSH_INTRO || g->ambush_phase==AMBUSH_CLEAR || g->ambush_phase==AMBUSH_FAILED) {
        if(g->ambush_timer) { --g->ambush_timer;return 0; }
        if(advance==0)return 0;
        if(g->ambush_phase==AMBUSH_CLEAR) { g->ambush_done=1;return 1; }
        if(g->ambush_phase==AMBUSH_FAILED)ambush_begin(g);
        sound_emit(S_WAVE_START);
        g->ambush_phase=AMBUSH_ACTIVE;g->ambush_timer=60;return 0;
    }
    ++g->ambush_clock;
    if(g->bow_cooldown)--g->bow_cooldown;
    if(g->hurt_timer)--g->hurt_timer;
    if(g->ambush_aim_ticks)--g->ambush_aim_ticks;
    movement(g,in,valid);
    if(g->ambush_phase==AMBUSH_BREATHER) {
        if(g->ambush_timer)--g->ambush_timer;
        else { sound_emit(S_WAVE_START);g->ambush_phase=AMBUSH_ACTIVE;g->ambush_spawned=0;g->ambush_timer=35; }
        return 0;
    }
    if(valid && in->fire)queue_shot(g,in->x,in->y);
    if(in->scope && in->offscreen)g->shot_request=0;
    if(in->scope==0 && (in->pressed & SK_ACTION)) {
        for(i=0;i<4;++i) {
            fox=&g->enemies[i];
            if(fox->hp && fox->y>nearest) {
                nearest=fox->y;tx=fox->x;ty=fox->y-((ambush_fox_width(fox->y)*3)>>3);
            }
        }
        if(nearest)queue_shot(g,tx,ty);
    }
    release_shot(g);
    for(i=0;i<4;++i)if(g->enemies[i].hp)++alive;
    wanted=g->ambush_wave+3;
    limit=g->ambush_wave==0?2:3;
    if(g->ambush_timer)--g->ambush_timer;
    else if(g->ambush_spawned<wanted && alive<limit) {
        for(i=0;i<4;++i) {
            fox=&g->enemies[i];
            if(fox->hp || fox->hit)continue;
            memset(fox,0,sizeof(*fox));
            fox->x=lanes[(g->ambush_spawned+g->ambush_wave*2)&7];
            fox->y=92;fox->hp=1;
            fox->kind=g->ambush_wave?(g->ambush_spawned+g->ambush_wave)%3:0;
            fox->attack=22;
            ++g->ambush_spawned;
            g->ambush_timer=g->ambush_wave==0?112:(g->ambush_spawned&1?55:135);
            break;
        }
    }
    arrows(g);pack(g);
    if(g->ambush_health==0) { sound_emit(S_PLAYER_DEFEAT); g->ambush_phase=AMBUSH_FAILED;g->ambush_timer=35;g->shot_request=0; }
    else if(g->ambush_defeated>=wave_end[g->ambush_wave]) {
        g->shot_request=0;
        memset(g->arrows,0,sizeof(g->arrows));
        if(++g->ambush_wave>=3) { sound_emit(S_WAVE_CLEAR_COMPLETE);g->ambush_phase=AMBUSH_CLEAR;g->ambush_timer=35; }
        else { sound_emit(S_WAVE_CLEAR_SHORT);g->ambush_phase=AMBUSH_BREATHER;g->ambush_timer=115; }
    }
    return 0;
}
