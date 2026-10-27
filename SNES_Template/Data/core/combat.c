#include <string.h>
#include "../include/game.h"
#include "../include/perspective.h"

/* Bounded actors and Q2 projectiles: no heap, division, or floating point. */
static const SkS8 arrow_dx[16] = {0,9,17,22,24,22,17,9,0,-9,-17,-22,-24,-22,-17,-9};
static const SkS8 arrow_dy[16] = {-24,-22,-17,-9,0,9,17,22,24,22,17,9,0,-9,-17,-22};
static const SkU8 spawn_x[4] = {220,32,224,32};
static const SkU8 spawn_y[4] = {96,64,160,160};
#define magnitude(value) ((value) < 0 ? -(value) : (value))
static void message(Game *g, SkU8 id) {
    g->combat_notice = id;
    g->combat_notice_ticks = 120;
}
SkU8 combat_tier(const Game *g) {
    if (g->nights > 3) return 3;
    return g->nights ? (SkU8)g->nights - 1 : 0;
}
SkU8 combat_capacity(const Game *g) {
    SkU8 tier = combat_tier(g);
    if (g->room == 2) return 0; /* The boarded chapel is a refuge. */
    if (g->room < 2 && game_daylight(g) >= 8) return 0;
    if (g->room == 0) return tier;
    return tier + 1;
}
SkU8 combat_direction(SkS16 dx, SkS16 dy) {
    SkS16 ax = magnitude(dx), ay = magnitude(dy);
    SkU8 angle;
    if (!ax && !ay) return 0;
    if (ax * 5 <= ay) angle = 0;
    else if (ay * 5 <= ax) angle = 4;
    else if (ax * 3 < ay * 2) angle = 1;
    else if (ay * 3 < ax * 2) angle = 3;
    else angle = 2;
    if (dy >= 0) return dx >= 0 ? 8 - angle : 8 + angle;
    return dx >= 0 ? angle : ((16 - angle) & 15);
}
static void spawn(Game *g, SkU8 index) {
    Enemy *enemy = &g->enemies[index];
    enemy->x = spawn_x[index];
    enemy->y = spawn_y[index];
    /* A returning player never receives an actor directly on their body. */
    if (magnitude(enemy->x - g->x) + magnitude(enemy->y - g->y) < 48) {
        enemy->x = g->x < 128 ? 232 : 24;
        enemy->y = g->y < 112 ? 164 : 64;
    }
    enemy->kind = index & 1;
    enemy->hp = combat_tier(g) >= 2 && enemy->kind ? 2 : 1;
    enemy->hit = 0;
    enemy->attack = 30;
    enemy->respawn = 0;
    enemy->step = index;
}
void combat_init(Game *g) {
    g->ammo = BOW_AMMO_MAX;
    g->nights = 0;
    g->kills = 0;
}
void combat_enter(Game *g) {
    SkU8 i, count = combat_capacity(g);
    memset(g->enemies, 0, sizeof(g->enemies));
    memset(g->arrows, 0, sizeof(g->arrows));
    g->bow_mode = g->bow_draw = g->bow_cooldown = g->shot_request = 0;
    g->combat_notice = g->combat_notice_ticks = 0;
    g->enemy_active = count != 0;
    for (i = 0; i < count; ++i) spawn(g, i);
}
void combat_ward(Game *g) {
    SkU8 i, hp;
    for (i = 0; i < COMBAT_ENEMIES; ++i)
        if (g->enemies[i].hp) {
            hp = g->enemies[i].hp;
            spawn(g, i);
            g->enemies[i].hp = hp;
            g->enemies[i].hit = 30;
        }
    g->enemy_x = g->enemies[0].x;
    g->enemy_y = g->enemies[0].y;
}
static void shoot(Game *g) {
    SkU8 i;
    Arrow *arrow;
    if (g->bow_draw < 6 || g->bow_cooldown) return;
    if (!g->ammo) { message(g, 2); return; }
    for (i = 0; i < COMBAT_ARROWS; ++i) {
        arrow = &g->arrows[i];
        if (arrow->life) continue;
        arrow->x = g->x << 2;
        arrow->y = g->y << 2;
        arrow->dx = arrow_dx[g->bow_direction];
        arrow->dy = arrow_dy[g->bow_direction];
        arrow->life = 42;
        arrow->damage = g->bow_draw >= BOW_DRAW_TICKS ? 2 : 1;
        --g->ammo;
        g->bow_cooldown = 24;
        return;
    }
}
static void bow_input(Game *g, const SkInput *in) {
    SkU8 dir, held, optical;
    if (in->pressed & SK_TURN_LEFT) {
        g->bow_mode ^= 1;
        g->bow_draw = g->shot_request = 0;
        g->destination_x = g->x;
        g->destination_y = g->y;
        g->bow_direction = g->direction << 1;
        message(g, g->bow_mode ? 1 : 0);
    }
    if (!g->bow_mode) return;
    dir = in->held & (SK_LEFT | SK_RIGHT | SK_UP | SK_DOWN);
    optical = in->scope && (in->fire || g->shot_request ||
              (!g->bow_draw && !(in->held & SK_ACTION) && !dir));
    if (optical) {
        if (in->aim_valid && !in->offscreen) {
            g->aim_x = in->x;
            g->aim_y = in->y;
            if (in->x != g->x || in->y != g->y)
                g->bow_direction = combat_direction(in->x - g->x, in->y - g->y);
            if (in->fire && !g->bow_cooldown) g->shot_request = 1;
        } else if (!g->bow_cooldown && (in->offscreen || in->fire)) {
            /* Optical coordinates arrive only on trigger edges. Idle
               packets retain the queued aim; an explicit bad shot cancels. */
            g->shot_request = g->bow_draw = 0;
        }
        held = g->shot_request;
    } else {
        g->shot_request = 0;
        if (dir) g->bow_direction = combat_direction(
            (dir & SK_RIGHT ? 1 : 0) - (dir & SK_LEFT ? 1 : 0),
            (dir & SK_DOWN ? 1 : 0) - (dir & SK_UP ? 1 : 0));
        g->aim_x = g->x + (SkS16)arrow_dx[g->bow_direction] * 2;
        g->aim_y = g->y + (SkS16)arrow_dy[g->bow_direction] * 2;
        held = (in->held & SK_ACTION) != 0;
    }
    g->direction = ((g->bow_direction + 1) >> 1) & 7;
    if (held && !g->bow_cooldown) {
        if (!g->ammo) { if (!g->combat_notice_ticks) message(g, 2); return; }
        if (g->bow_draw < BOW_DRAW_TICKS) ++g->bow_draw;
        if (optical && g->bow_draw >= BOW_DRAW_TICKS) {
            shoot(g);
            g->shot_request = g->bow_draw = 0;
        }
    } else if (!held && g->bow_draw) {
        shoot(g);
        g->bow_draw = 0;
    }
}
static void projectiles(Game *g) {
    SkU8 i, j, part;
    SkS16 x, y;
    Arrow *arrow;
    Enemy *enemy;
    for (i = 0; i < COMBAT_ARROWS; ++i) {
        arrow = &g->arrows[i];
        if (!arrow->life) continue;
        --arrow->life;
        if (!arrow->damage) continue;
        /* Two swept substeps keep fast arrows from tunnelling through walls
           or a narrow enemy, even for diagonal shots. */
        for (part = 0; part < 2; ++part) {
            arrow->x += part ? arrow->dx - (arrow->dx >> 1) : arrow->dx >> 1;
            arrow->y += part ? arrow->dy - (arrow->dy >> 1) : arrow->dy >> 1;
            x = arrow->x >> 2;
            y = arrow->y >> 2;
            if (!game_can_walk(g->room, x, y)) {
                arrow->damage = 0; arrow->life = 6;
                break;
            }
            enemy = g->enemies;
            for (j = 0; j < COMBAT_ENEMIES; ++j, ++enemy) {
                if (!enemy->hp) continue;
                if (magnitude(x - enemy->x) + magnitude(y - enemy->y) > 12) continue;
                enemy->hit = 12;
                if (enemy->hp > arrow->damage) enemy->hp -= arrow->damage;
                else {
                    enemy->hp = 0;
                    enemy->respawn = 1200 - (SkU16)combat_tier(g) * 180;
                    if (g->kills < 65535) ++g->kills;
                    if (!(g->kills & 1) && g->ammo < BOW_AMMO_MAX) ++g->ammo;
                    if (g->fear > 3) g->fear -= 3;
                }
                arrow->damage = 0; arrow->life = 6;
                break;
            }
            if (!arrow->damage) break;
        }
    }
}
static void enemies(Game *g) {
    SkU8 i, count, tier, interval;
    SkS16 dx, dy, nx, ny;
    Enemy *enemy = g->enemies;
    /* The common sunlit path avoids tier/capacity calls and actor traversal. */
    if (g->room < 2 && g->sun_level >= 8) {
        if (g->enemy_active || enemy->respawn || enemy->hit)
            memset(g->enemies, 0, sizeof(g->enemies));
        g->enemy_active = 0;
        return;
    }
    count = combat_capacity(g);
    tier = combat_tier(g);
    interval = 8 - tier;
    if (!count) {
        if (g->enemy_active || enemy->hp || enemy->respawn)
            memset(g->enemies, 0, sizeof(g->enemies));
        g->enemy_active = 0;
        return;
    }
    g->enemy_active = 0;
    for (i = 0; i < count; ++i, ++enemy) {
        if (!enemy->hp) {
            if (enemy->hit) --enemy->hit;
            if (enemy->respawn) { --enemy->respawn; continue; }
            spawn(g, i);
        }
        g->enemy_active = 1;
        if (enemy->attack) --enemy->attack;
        if (enemy->hit) { --enemy->hit; continue; }
        if (g->ward_timer) continue;
        if (++enemy->step < interval) continue;
        enemy->step = 0;
        dx = g->x - enemy->x; dy = g->y - enemy->y;
        nx = (dx > 0) - (dx < 0); ny = (dy > 0) - (dy < 0);
        /* Fire protects the immediate pool; enemies can gather at its edge. */
        if (magnitude(dx) + magnitude(dy) < 32 && light_sees(g, enemy->x, enemy->y)) {
            if (!enemy->kind) { nx = -nx; ny = -ny; }
            else if (g->tick & 16) continue; /* Crawlers push through, slowly. */
        }
        if (game_can_walk(g->room, enemy->x + nx, enemy->y)) enemy->x += nx;
        if (game_can_walk(g->room, enemy->x, enemy->y + ny)) enemy->y += ny;
        if (!enemy->attack && magnitude(dx) + magnitude(dy) < 18) {
            g->fear += 4 + tier * 2;
            enemy->attack = 45;
        }
    }
    g->enemy_x = g->enemies[0].x;
    g->enemy_y = g->enemies[0].y;
}
void combat_tick(Game *g, const SkInput *in) {
    if (g->mode != G_EXPLORE) return;
    if (g->combat_notice_ticks) --g->combat_notice_ticks;
    if (g->bow_cooldown) --g->bow_cooldown;
    if (g->bow_mode || (in->pressed & SK_TURN_LEFT)) bow_input(g, in);
    if (g->arrows[0].life || g->arrows[1].life || g->arrows[2].life) projectiles(g);
    enemies(g);
}
SkU8 combat_pick(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y) {
    SkU8 i, facing = (g->direction >> 1) & 3;
    SkS16 ox, oy, dx, dy;
    dx = sx - (g->bow_mode ? 106 : perspective_light_x[facing]);
    dy = sy - (g->bow_mode ? 145 : perspective_light_y[facing]);
    if (!game_daylight(g)) {
        if (!g->lamp || !g->oil) return 0;
        if (dx < -77 || dx > 77 || dy < -77 || dy > 77 || dx * dx + dy * dy > 77 * 77) return 0;
    }
    for (i = 0; i < COMBAT_ENEMIES; ++i) {
        if (!g->enemies[i].hp) continue;
        if (!perspective_project(g, g->enemies[i].x, g->enemies[i].y, &ox, &oy)) continue;
        if (sx >= ox - 8 && sx < ox + 8 &&
            sy >= oy - (g->enemies[i].kind ? 16 : 32) && sy < oy) {
            *x = g->enemies[i].x; *y = g->enemies[i].y;
            return 1;
        }
    }
    return 0;
}
