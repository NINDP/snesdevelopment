#include "../include/game.h"

SkS16 roach_x(SkU8 hole) { return 56 + (hole % 3) * 72; }
SkS16 roach_y(SkU8 hole) { return 94 + (hole / 3) * 44; }

void roach_begin(Game *g) {
    g->mode = G_ROACH;
    g->fear = 100;
    g->roach_phase = ROACH_INTRO;
    g->roach_round = g->roach_hits = g->roach_misses = 0;
    g->roach_hole = SK_NONE;
    g->roach_cursor = 4;
    g->roach_timer = g->roach_gap = g->roach_flash = 0;
    g->roach_seed = g->tick ^ (g->seconds << 3) ^ 0x5a71;
    g->bow_draw = g->shot_request = 0;
    g->destination_x = g->x;
    g->destination_y = g->y;
}

static void spawn(Game *g) {
    SkU8 previous = g->roach_hole;
    /* A private deterministic stream never changes the world's simulation. */
    g->roach_seed = (SkU16)(g->roach_seed * 25173U + 13849U);
    g->roach_hole = (g->roach_seed >> 8) % 9;
    if (g->roach_hole == previous)
        g->roach_hole = (g->roach_hole + 1) % 9;
    g->roach_timer = 90 - g->roach_round * 3;
    ++g->roach_round;
}

static void resolve(Game *g, SkU8 hit) {
    if (hit) {
        ++g->roach_hits;
        g->roach_flash = 14;
    } else
        ++g->roach_misses;
    g->roach_timer = 0;
    g->roach_gap = 24;
    if (g->roach_misses > ROACH_MAX_MISSES)
        g->roach_phase = ROACH_LOST;
    else if (g->roach_round == ROACH_TOTAL)
        g->roach_phase = ROACH_WON;
}

void roach_tick(Game *g, const SkInput *in) {
    SkU8 i, action = (in->pressed & SK_ACTION) != 0;
    SkU8 gun = in->scope && in->fire && in->aim_valid && !in->offscreen;
    if (g->roach_flash)
        --g->roach_flash;
    if (g->roach_phase == ROACH_INTRO) {
        if (action || gun) {
            g->roach_phase = ROACH_ACTIVE;
            spawn(g);
        }
        return;
    }
    if (g->roach_phase == ROACH_WON || g->roach_phase == ROACH_LOST) {
        if (action || gun) {
            if (g->roach_phase == ROACH_LOST) {
                g->checkpoint_room = 0;
                game_checkpoint(g);
            } else {
                g->fear = 25;
                g->hurt_timer = 90;
                g->mode = G_EXPLORE;
            }
        }
        return;
    }
    if ((in->pressed & SK_LEFT) && g->roach_cursor % 3)
        --g->roach_cursor;
    if ((in->pressed & SK_RIGHT) && g->roach_cursor % 3 < 2)
        ++g->roach_cursor;
    if ((in->pressed & SK_UP) && g->roach_cursor >= 3)
        g->roach_cursor -= 3;
    if ((in->pressed & SK_DOWN) && g->roach_cursor < 6)
        g->roach_cursor += 3;
    if (in->scope && in->aim_valid && !in->offscreen) {
        for (i = 0; i < 9; ++i)
            if (in->x >= roach_x(i) - 24 && in->x < roach_x(i) + 24 &&
                in->y >= roach_y(i) - 32 && in->y < roach_y(i) + 8) {
                g->roach_cursor = i;
                break;
            }
        /* Empty space cannot reuse the last hovered hole for a gun hit. */
        if (i == 9)
            gun = 0;
    }
    if (g->roach_gap) {
        if (!--g->roach_gap)
            spawn(g);
        return;
    }
    if ((action || gun) && g->roach_cursor == g->roach_hole) {
        resolve(g, 1);
        return;
    }
    if (g->roach_timer && !--g->roach_timer)
        resolve(g, 0);
}
