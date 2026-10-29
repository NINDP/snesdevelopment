#include <string.h>
#include "../include/game.h"
#include "../include/perspective.h"
#include "../include/audio.h"

/* Bounded actors and Q2 projectiles: no heap, division, or floating point. */
static const SkS8 arrow_dx[16] = {0,9,17,22,24,22,17,9,0,-9,-17,-22,-24,-22,-17,-9};
static const SkS8 arrow_dy[16] = {-24,-22,-17,-9,0,9,17,22,24,22,17,9,0,-9,-17,-22};
static const SkU8 spawn_x[4] = {220,32,224,32};
static const SkU8 spawn_y[4] = {96,64,160,160};
static const SkS8 step_x[8] = {0,1,1,1,0,-1,-1,-1};
static const SkS8 step_y[8] = {-1,-1,0,1,1,1,0,-1};
/* Q7 reciprocals, 24/n for n=16..31; used only on arrow release. */
static const SkU8 aim_scale[16] = {192,181,171,162,154,146,140,134,128,123,118,114,110,106,102,99};
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
    if (!game_can_walk(g->room, enemy->x, enemy->y)) enemy->y = 72;
    enemy->kind = index & 1;
    enemy->hp = combat_tier(g) >= 2 && enemy->kind ? 2 : 1;
    enemy->hit = 0;
    enemy->attack = 30;
    enemy->respawn = 0;
    enemy->step = index;
    enemy->state = ENEMY_HUNT;
}
void combat_init(Game *g) {
    g->ammo = BOW_AMMO_MAX;
    g->nights = 0;
    g->kills = 0;
}
void combat_enter(Game *g) {
    SkU8 i, count = combat_capacity(g);
    g->enemy_slots = count;
    memset(g->enemies, 0, sizeof(g->enemies));
    memset(g->arrows, 0, sizeof(g->arrows));
    g->bow_mode = g->bow_draw = g->bow_cooldown = g->shot_request = 0;
    g->combat_notice = g->combat_notice_ticks = 0;
    g->hurt_timer = g->shove_cooldown = 0;
    g->hit_stop = g->enemy_clock = 0;
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
/* Every displacement checks each world unit, including knockback at walls. */
static void displace(Game *g, Enemy *enemy, SkS16 dx, SkS16 dy, SkU8 distance) {
    SkS16 nx = (dx > 0) - (dx < 0), ny = (dy > 0) - (dy < 0);
    while (distance--) {
        if (nx && game_can_walk(g->room, enemy->x + nx, enemy->y)) enemy->x += nx;
        if (ny && game_can_walk(g->room, enemy->x, enemy->y + ny)) enemy->y += ny;
    }
}
static void stagger(Game *g, Enemy *enemy, SkS16 dx, SkS16 dy, SkU8 distance) {
    enemy->state = ENEMY_RECOVER;
    enemy->attack = 36;
    enemy->step = 0;
    enemy->hit = 12;
    displace(g, enemy, dx, dy, distance);
}
static void shove(Game *g) {
    SkU8 i, facing = g->direction;
    SkS16 dx, dy, forward, side;
    Enemy *enemy = g->enemies;
    if (g->shove_cooldown) return;
    g->shove_cooldown = SHOVE_COOLDOWN;
    sound_emit(S_PLAYER_SHOVE);
    g->bow_draw = g->shot_request = 0;
    for (i = 0; i < g->enemy_slots; ++i, ++enemy) {
        if (!enemy->hp) continue;
        dx = enemy->x - g->x; dy = enemy->y - g->y;
        if (magnitude(dx) + magnitude(dy) > 28) continue;
        forward = dx * step_x[facing] + dy * step_y[facing];
        side = dx * step_y[facing] - dy * step_x[facing];
        if (forward < 0 || magnitude(side) > forward + 6) continue;
        stagger(g, enemy, dx ? dx : step_x[facing], dy ? dy : step_y[facing], 12);
    }
}
/* Only a narrow cone around the pad's chosen heading can assist the aim.
   Scope retains its explicit world target. The arrow still hits geometry. */
static void assist_aim(Game *g) {
    SkU8 i;
    SkS16 dx, dy, distance, cross, forward, best = 113;
    const Enemy *enemy = g->enemies;
    for (i = 0; i < g->enemy_slots; ++i, ++enemy) {
        if (!enemy->hp) continue;
        dx = enemy->x - g->x; dy = enemy->y - g->y;
        distance = magnitude(dx) + magnitude(dy);
        if (distance >= best) continue;
        cross = dx * arrow_dy[g->bow_direction] - dy * arrow_dx[g->bow_direction];
        if (magnitude(cross) > (distance << 2)) continue;
        forward = dx * arrow_dx[g->bow_direction] + dy * arrow_dy[g->bow_direction];
        if (forward <= 0) continue;
        if (!game_visible(g, enemy->x, enemy->y)) continue;
        best = distance;
        g->aim_x = enemy->x; g->aim_y = enemy->y;
    }
}
static void shoot(Game *g) {
    SkU8 i;
    SkS16 dx, dy, longest, ax, ay;
    Arrow *arrow;
    if (g->bow_draw < BOW_MIN_DRAW || g->bow_cooldown) return;
    if (!g->ammo) { message(g, 2); sound_emit(S_UI_ERROR); return; }
    for (i = 0; i < COMBAT_ARROWS; ++i) {
        arrow = &g->arrows[i];
        if (arrow->life) continue;
        arrow->x = g->x << 2;
        arrow->y = g->y << 2;
        dx = g->aim_x - g->x; dy = g->aim_y - g->y;
        if (!dx && !dy) { dx = arrow_dx[g->bow_direction]; dy = arrow_dy[g->bow_direction]; }
        /* Normalize the actual aim with bounded shifts. Preserve the slope
           instead of rounding a Scope shot to the nearest 22.5 degrees. */
        ax = magnitude(dx); ay = magnitude(dy);
        longest = ax > ay ? ax + (ay >> 1) : ay + (ax >> 1);
        while (longest > 31) { ax >>= 1; ay >>= 1; longest >>= 1; }
        while (longest < 16) { ax *= 2; ay *= 2; longest *= 2; }
        ax = (ax * aim_scale[longest - 16]) >> 7;
        ay = (ay * aim_scale[longest - 16]) >> 7;
        if (g->bow_draw < BOW_DRAW_TICKS) { ax >>= 1; ay >>= 1; }
        dx = dx < 0 ? -ax : ax; dy = dy < 0 ? -ay : ay;
        arrow->dx = (SkS8)dx;
        arrow->dy = (SkS8)dy;
        arrow->life = g->bow_draw >= BOW_DRAW_TICKS ? 42 : 32;
        arrow->damage = g->bow_draw >= BOW_DRAW_TICKS ? 2 : 1;
        --g->ammo;
        sound_emit(g->bow_draw>=BOW_DRAW_TICKS?S_BOW_RELEASE_STRONG:S_BOW_RELEASE_WEAK);
        g->bow_cooldown = BOW_COOLDOWN;
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
    if (!g->bow_mode || g->shove_cooldown > SHOVE_COOLDOWN - 12) return;
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
        if (g->bow_draw >= BOW_MIN_DRAW) assist_aim(g);
        held = (in->held & SK_ACTION) != 0;
    }
    g->direction = ((g->bow_direction + 1) >> 1) & 7;
    if (held && !g->bow_cooldown) {
        if (!g->ammo) { if (!g->combat_notice_ticks) { message(g, 2);sound_emit(S_UI_ERROR); } return; }
        if (!g->bow_draw) sound_emit(S_BOW_DRAW);
        if (g->bow_draw < BOW_DRAW_TICKS) {
            ++g->bow_draw;
            if (g->bow_draw==BOW_DRAW_TICKS) sound_emit(S_BOW_READY);
        }
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
                sound_emit(g->room<3?S_ARROW_HIT_SURFACE_WOOD:S_ARROW_HIT_SURFACE_STONE);
                arrow->damage = 0; arrow->life = 6;
                break;
            }
            enemy = g->enemies;
            for (j = 0; j < COMBAT_ENEMIES; ++j, ++enemy) {
                if (!enemy->hp) continue;
                if (magnitude(x - enemy->x) + magnitude(y - enemy->y) > 12) continue;
                sound_emit(sound_variant(S_ARROW_HIT_ENEMY_01,2));
                enemy->hit = 12;
                g->hit_stop = 3;
                if (enemy->hp > arrow->damage) {
                    enemy->hp -= arrow->damage;
                    stagger(g, enemy, arrow->dx, arrow->dy, 4);
                }
                else {
                    sound_schedule(sound_variant(S_ENEMY_DISSOLVE_01,2),10);
                    enemy->hp = 0;
                    enemy->respawn = 1200 - (SkU16)combat_tier(g) * 180;
                    if (g->kills < 65535) ++g->kills;
                    if (!(g->kills & 1) && g->ammo < BOW_AMMO_MAX) ++g->ammo;
                    if (g->fear > 3) g->fear -= 3;
                    enemy->state = ENEMY_HUNT;
                }
                arrow->damage = 0; arrow->life = 6;
                break;
            }
            if (!arrow->damage) break;
        }
    }
}
static void enemies(Game *g) {
    SkU8 i, count, tier, interval, can_attack;
    SkS16 dx, dy, nx, ny, distance;
    Enemy *enemy = g->enemies;
    if (g->room == 2) {
        g->enemy_active = g->enemy_slots = 0;
        return;
    }
    /* The common sunlit path avoids tier/capacity calls and actor traversal. */
    if (g->room < 2 && g->sun_level >= 8) {
        if (g->enemy_active || enemy->respawn || enemy->hit)
            memset(g->enemies, 0, sizeof(g->enemies));
        g->enemy_active = 0;
        g->enemy_slots = 0;
        return;
    }
    tier = combat_tier(g);
    count = g->room == 0 ? tier : tier + 1;
    g->enemy_slots = count;
    interval = 8 - tier;
    if (!count) {
        if (g->enemy_active || enemy->hp || enemy->respawn)
            memset(g->enemies, 0, sizeof(g->enemies));
        g->enemy_active = 0;
        return;
    }
    /* Actors render at 30 Hz in dense scenes. Updating their AI every other
       logical tick avoids doing two full actor passes before the same PPU
       frame; counters and motion consume two ticks to retain real timing. */
    if (g->enemy_clock) { g->enemy_clock = 0; return; }
    g->enemy_clock = 1;
    g->enemy_active = 0;
    for (i = 0; i < count; ++i, ++enemy) {
        if (!enemy->hp) {
            if (enemy->hit) enemy->hit = enemy->hit > 2 ? enemy->hit - 2 : 0;
            if (enemy->respawn) {
                enemy->respawn = enemy->respawn > 2 ? enemy->respawn - 2 : 0;
                continue;
            }
            spawn(g, i);
        }
        g->enemy_active = 1;
        if (enemy->attack) enemy->attack = enemy->attack > 2 ? enemy->attack - 2 : 0;
        if (enemy->hit) { enemy->hit = enemy->hit > 2 ? enemy->hit - 2 : 0; continue; }
        if (g->ward_timer) continue;
        if (enemy->state == ENEMY_WINDUP) {
            if (!enemy->kind && !g->bow_mode && light_sees(g, enemy->x, enemy->y)) {
                enemy->state = ENEMY_RECOVER;
                enemy->attack = 20;
                enemy->step = 0;
                continue;
            }
            if (!enemy->attack) {
                sound_emit(S_ENEMY_LUNGE);
                enemy->state = ENEMY_LUNGE;
                enemy->attack = enemy->kind == ENEMY_CRAWLER ? 14 : 16;
            }
            continue;
        }
        if (enemy->state == ENEMY_LUNGE) {
            if (!enemy->attack) {
                enemy->state = ENEMY_RECOVER;
                enemy->attack = enemy->kind == ENEMY_CRAWLER ? 60 : 45;
                enemy->step = 0;
                continue;
            }
            /* A two-unit stride cannot cross any authored solid rectangle.
               Test one endpoint per axis instead of four terrain calls. */
            nx = (SkS16)step_x[enemy->step] * 2;
            ny = (SkS16)step_y[enemy->step] * 2;
            if (nx && game_can_walk(g->room, enemy->x + nx, enemy->y)) enemy->x += nx;
            if (ny && game_can_walk(g->room, enemy->x, enemy->y + ny)) enemy->y += ny;
            dx = g->x - enemy->x; dy = g->y - enemy->y;
            if (!g->hurt_timer && magnitude(dx) + magnitude(dy) < 14) {
                g->fear = g->fear > 100 - (4 + tier * 2) ? 100 : g->fear + 4 + tier * 2;
                sound_emit(sound_variant(S_PLAYER_HURT_01,2));
                g->hurt_timer = 45; /* A group cannot deal four hits at once. */
                g->bow_draw = g->shot_request = 0;
                enemy->state = ENEMY_RECOVER;
                enemy->attack = enemy->kind == ENEMY_CRAWLER ? 60 : 45;
                enemy->step = 0;
            }
            continue;
        }
        if (enemy->state == ENEMY_RECOVER) {
            if (enemy->attack) continue;
            enemy->state = ENEMY_HUNT;
            enemy->step = 0;
        }
        enemy->step += 2;
        if (enemy->step < interval) continue;
        enemy->step -= interval;
        dx = g->x - enemy->x; dy = g->y - enemy->y;
        distance = magnitude(dx) + magnitude(dy);
        nx = (dx > 0) - (dx < 0); ny = (dy > 0) - (dy < 0);
        /* Fire protects the immediate pool; enemies can gather at its edge. */
        if (distance < (g->bow_mode ? 20 : 32) && light_sees(g, enemy->x, enemy->y)) {
            if (!enemy->kind) { nx = -nx; ny = -ny; }
            else if (g->tick & 16) continue; /* Crawlers push through, slowly. */
        }
        /* Keep the call out of an OR expression: 816-tcc miscompiles the
           crawler's true branch of (kind || !light_sees(...)). */
        if (!enemy->attack) {
            if (distance < 26) {
                can_attack = enemy->kind;
                /* A planted torch leaves the archer exposed. The carried
                   flame still repels a shade during normal exploration. */
                if (g->bow_mode) can_attack = 1;
                if (!can_attack) can_attack = !light_sees(g, enemy->x, enemy->y);
                if (can_attack) {
                    sound_emit(enemy->kind==ENEMY_CRAWLER?S_CRAWLER_WARNING:S_SHADE_WARNING);
                    enemy->state = ENEMY_WINDUP;
                    enemy->attack = enemy->kind == ENEMY_CRAWLER ? 30 : 20;
                    enemy->step = light_direction(dx, dy);
                    continue;
                }
            }
        }
        /* Separate approach lanes keep a pair from becoming one silhouette. */
        if (distance > 40 && i) {
            dx += i & 1 ? -10 : 10;
            nx = (dx > 0) - (dx < 0);
        }
        if (nx && game_can_walk(g->room, enemy->x + nx, enemy->y)) enemy->x += nx;
        if (ny && game_can_walk(g->room, enemy->x, enemy->y + ny)) enemy->y += ny;
    }
    g->enemy_x = g->enemies[0].x;
    g->enemy_y = g->enemies[0].y;
}
void combat_tick(Game *g, const SkInput *in) {
    if (g->mode != G_EXPLORE) return;
    if (g->combat_notice_ticks) --g->combat_notice_ticks;
    if (g->bow_cooldown) --g->bow_cooldown;
    if (g->hurt_timer) --g->hurt_timer;
    if (g->shove_cooldown) --g->shove_cooldown;
    if (in->pressed & SK_SHOVE) shove(g);
    if (g->bow_mode || (in->pressed & SK_TURN_LEFT)) bow_input(g, in);
    /* Input remains live during impact emphasis; only moving combat actors
       pause, so a fresh R/L edge or a released string is never swallowed. */
    if (g->hit_stop) { --g->hit_stop; return; }
    if (g->arrows[0].life || g->arrows[1].life || g->arrows[2].life) projectiles(g);
    if (!g->hit_stop) enemies(g);
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
