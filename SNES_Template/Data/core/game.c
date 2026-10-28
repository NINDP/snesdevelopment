#include <string.h>
#include "../include/game.h"
#include "../include/ui_text.h"
#define HAS(g, f) (((g)->flags & (f)) == (f))
static SkS16 distance(SkS16 a, SkS16 b) {
    return a > b ? a - b : b - a;
}
static void begin_dialogue(Game *g, SkU8 id) {
    g->mode = G_DIALOGUE;
    g->dialogue = id;
    g->page = 0;
    g->revealed = 0;
    g->text_delay = 0;
    g->destination_x = g->x;
    g->destination_y = g->y;
    g->focus = SK_NONE;
    g->notice_ticks = 0;
}
static void begin_choice(Game *g, SkU8 id) {
    g->mode = G_CHOICE;
    g->choice = id;
    g->option = 0;
}
static void enter_room(Game *g, SkU8 room) {
    g->room = room;
    g->checkpoint_room = room;
    g->x = 124;
    g->y = 176;
    g->destination_x = g->x;
    g->destination_y = g->y;
    g->enemy_x = 220;
    g->enemy_y = 120;
    g->enemy_active = room == 3 || (room == 1 && game_daylight(g) < 8);
    g->direction = 0;
    g->mode = G_EXPLORE;
    g->notice = 0;
    g->echo_charge = 0;
    g->focus = SK_NONE;
    g->notice_ticks = 0;
    combat_enter(g);
}
void game_init(Game *g) {
    memset(g, 0, sizeof(*g));
    daycycle_init(g);
    combat_init(g);
    g->mode = G_SPLASH;
    g->focus = SK_NONE;
    g->oil = 120;
}
void game_new(Game *g) {
    memset(g, 0, sizeof(*g));
    daycycle_init(g);
    combat_init(g);
    g->oil = 120;
    enter_room(g, 0);
    begin_dialogue(g, D_PROLOG);
}
void game_checkpoint(Game *g) {
    enter_room(g, g->checkpoint_room);
    g->oil = 120;
    g->fear = 15;
    g->ammo = BOW_AMMO_MAX;
    g->lamp = 1;
    begin_dialogue(g, D_RETRY);
}
static SkU8 votes(const Game *g) {
    return (HAS(g, F_KIND) ? 1 : 0) + (HAS(g, F_CONFESS) ? 1 : 0) + (HAS(g, F_FREE) ? 1 : 0);
}
static void choose_ending(Game *g, SkU8 give_village) {
    /* An early mistake can be repaired; only an explicit bargain sacrifices
       the village. A failed attempt to seal returns to exploration. */
    if (!give_village && votes(g) != 3) {
        begin_dialogue(g, D_REPAIR);
        return;
    }
    if (give_village)
        g->ending = END_BAD;
    else
        g->ending = g->evidence == 7 ? END_SECRET : END_GOOD;
    g->flags |= F_SEALED;
    begin_dialogue(g,
                   g->ending == END_SECRET ? D_SECRET : (g->ending == END_GOOD ? D_GOOD : D_BAD));
}
static void finish_dialogue(Game *g) {
    SkU8 id = g->dialogue;
    g->mode = G_EXPLORE;
    switch (id) {
    case D_HEAD:
        g->flags |= F_HEAD;
        break;
    case D_EGOR:
    case D_EGOR_CAGED:
        begin_choice(g, C_EGOR);
        break;
    case D_BIRCH:
        g->flags |= F_BIRCH;
        break;
    case D_MIRO:
    case D_MIRO_RETRY:
        begin_choice(g, C_CONFESS);
        break;
    case D_FOREST:
        g->flags |= F_FOREST;
        break;
    case D_PRIEST:
        g->flags |= F_PRIEST;
        break;
    case D_TIKHON:
        g->flags |= F_TIKHON;
        break;
    case D_TOKEN:
        if (!HAS(g, F_TOKEN))
            g->wards = 3;
        g->flags |= F_TOKEN;
        break;
    case D_CHAPEL:
        g->flags |= F_CHAPEL;
        break;
    case D_REVEAL:
        g->flags |= F_REVEAL | F_HEART_TRUTH;
        begin_choice(g, C_MIRO);
        break;
    case D_MIRO_RELEASE:
        begin_choice(g, C_MIRO);
        break;
    case D_RITUAL:
    case D_RITUAL_READY:
        g->flags |= F_WITNESS;
        break;
    case D_FINAL:
    case D_FINAL_WARNING:
        begin_choice(g, C_FINAL);
        break;
    case D_GRAVE:
        g->evidence |= 1;
        break;
    case D_WITNESS:
        g->evidence |= 2;
        break;
    case D_MARK:
        g->evidence |= 4;
        break;
    case D_ECHO_HOME:
        g->memories |= 1;
        break;
    case D_ECHO_BOAT:
        g->memories |= 2;
        break;
    case D_ECHO_STONE:
        g->memories |= 4;
        break;
    case D_BELL_HINT:
        g->mode = G_BELL;
        g->option = 0;
        g->bell_step = 0;
        break;
    case D_BELL_DONE:
        g->memories |= 8;
        break;
    case D_REMEMBER:
        begin_choice(g, C_FINAL);
        break;
    case D_GOOD:
        begin_dialogue(g, D_END_STAY);
        break;
    case D_BAD:
        begin_dialogue(g, D_END_LOST);
        break;
    case D_SECRET:
        begin_dialogue(g, D_MODERN);
        break;
    case D_MODERN:
    case D_END_STAY:
    case D_END_LOST:
        g->mode = G_END;
        break;
    default:
        break;
    }
}
static void choose(Game *g) {
    switch (g->choice) {
    case C_EGOR:
        g->flags |= F_EGOR;
        g->flags &= ~F_KIND;
        if (!g->option)
            g->flags |= F_KIND;
        begin_dialogue(g, g->option ? D_LOCK : D_KIND);
        break;
    case C_CONFESS:
        g->flags |= F_MIRO;
        g->flags &= ~F_CONFESS;
        if (!g->option)
            g->flags |= F_CONFESS;
        begin_dialogue(g, g->option ? D_DENY : D_CONFESS);
        break;
    case C_MIRO:
        g->flags &= ~F_FREE;
        if (!g->option)
            g->flags |= F_FREE;
        begin_dialogue(g, g->option ? D_BIND : D_FREE);
        break;
    default:
        choose_ending(g, g->option);
        break;
    }
}
/* Solid geometry remains solid in darkness. Rectangle positions match maps. */
SkU8 game_can_walk(SkU8 room, SkS16 x, SkS16 y) {
    if (x < 12 || x > 244 || y < 32 || y > 180)
        return 0;
    /* The same authored rectangles, without constructing a temporary SkRect
       and calling through a far pointer for every footstep/arrow substep. */
    if (room == 0) {
        if (y < 63 && x >= 14 && x < 84) return 0;
        if (y < 68 && x >= 157 && x < 235) return 0;
        return 1;
    }
    if (room == 2) {
        if (y >= 53) return 1;
        if (x < 101) return 1;
        return x >= 156;
    }
    if (y >= 48) return 1;
    if (x < 106) return 1;
    return x >= 152;
}

#ifndef SNES_TARGET
SkU8 game_nearby(const Game *g) {
    SkU8 i, best = SK_NONE, count = game_hotspot_count(g->room);
    SkU8 sun = game_daylight(g), facing = (g->direction >> 1) & 3;
    SkS16 dx, dy, ax, ay, d, minimum = 255;
    const Hotspot *h = game_hotspot(g->room, 0);
    if (!sun && !g->lamp) return SK_NONE;
    if (!sun && !g->oil) return SK_NONE;
    for (i = 0; i < count; ++i, ++h) {
        dx = h->x - g->x; dy = h->y - g->y;
        ax = dx < 0 ? -dx : dx;
        if (ax >= 56) continue;
        ay = dy < 0 ? -dy : dy;
        d = ax + ay;
        if (d >= 56) continue;
        /* A looks at the object in front of the actor. A trace at the feet
           must not steal a nearby conversation the player is facing. */
        if ((facing == 0 && dy > -8) || (facing == 1 && dx < 8) ||
            (facing == 2 && dy < 8) || (facing == 3 && dx > -8))
            d += 48;
        if (d >= minimum)
            continue;
        if (!sun && !light_sees(g, h->x, h->y))
            continue;
        best = i;
        minimum = d;
    }
    return best;
}
#endif
static SkU8 scope_nearby(const Game *g, const SkInput *in) {
    SkU8 i, best = SK_NONE, count = game_hotspot_count(g->room);
    SkS16 d, minimum = 15;
    const Hotspot *h = game_hotspot(g->room, 0);
    for (i = 0; i < count; ++i, ++h) {
        d = distance(in->x, h->x) + distance(in->y, h->y);
        if (d >= minimum) continue;
        if (distance(g->x, h->x) + distance(g->y, h->y) >= 56) continue;
        if (!game_visible(g, h->x, h->y)) continue;
        minimum = d; best = i;
    }
    return best;
}
static void refill(Game *g) {
    g->oil = 120;
    g->ammo = BOW_AMMO_MAX;
    g->notice = 1;
    g->fear = g->fear > 15 ? g->fear - 15 : 0;
}
/* Optional light traces share one charge counter across the current room. */
static SkU8 echo_index(SkU8 room) {
    if (room == 0)
        return 5;
    if (room == 1)
        return 8;
    if (room == 3)
        return 8;
    return SK_NONE;
}
static SkU8 echo_bit(SkU8 room) {
    return room == 0 ? 1 : (room == 1 ? 2 : 4);
}
static void inspect_echo(Game *g) {
    if (!(g->memories & echo_bit(g->room)) && g->echo_charge < 45) {
        g->notice = 7;
        return;
    }
    begin_dialogue(g, g->room == 0 ? D_ECHO_HOME : (g->room == 1 ? D_ECHO_BOAT : D_ECHO_STONE));
}
static void silver_ward(Game *g) {
    g->notice_ticks = 180;
    if (!HAS(g, F_TOKEN)) {
        g->notice = 10;
        return;
    }
    if (!g->wards) {
        g->notice = 9;
        return;
    }
    --g->wards;
    g->ward_timer = 90;
    g->notice = 8;
    g->fear = g->fear > 25 ? g->fear - 25 : 0;
    g->enemy_x = 238;
    g->enemy_y = 40;
    combat_ward(g);
}
static void interact(Game *g, SkU8 id) {
    if (id == SK_NONE) {
        if (!game_daylight(g) && (!g->lamp || !g->oil))
            begin_dialogue(g, D_NO_LIGHT);
        else { g->notice = 17; g->notice_ticks = 120; }
        return;
    }
    g->notice = 0;
    g->notice_ticks = 180;
    ++g->interactions;
    g->last_hotspot = id;
    if (id == echo_index(g->room)) {
        inspect_echo(g);
        return;
    }
    if (g->room == 0) {
        if (id == 0)
            begin_dialogue(g, D_HEAD);
        if (id == 1) {
            if (!HAS(g, F_EGOR))
                begin_dialogue(g, D_EGOR);
            else
                begin_dialogue(g, HAS(g, F_KIND) ? D_EGOR_RETURN : D_EGOR_CAGED);
        }
        if (id == 2)
            refill(g);
        if (id == 3) {
            if (HAS(g, F_HEAD | F_EGOR))
                enter_room(g, 1);
            else
                begin_dialogue(g, D_GATE);
        }
        if (id == 4)
            begin_dialogue(g, D_GRAVE);
    } else if (g->room == 1) {
        if (id == 0)
            begin_dialogue(g, D_BIRCH);
        if (id == 1)
            begin_dialogue(g, !HAS(g, F_MIRO) ? D_MIRO :
                (HAS(g, F_CONFESS) ? D_CONFESS : D_MIRO_RETRY));
        if (id >= 2 && id <= 4) {
            if (!HAS(g, F_BIRCH)) {
                g->notice = 3;
                return;
            }
            if (HAS(g, F_FOREST)) { g->notice = 12; return; }
            if (id - 2 == g->forest_step) {
                ++g->forest_step;
                g->notice = g->forest_step == 1 ? 13 : 14;
            } else {
                g->forest_step = 0;
                g->notice = 2;
                if (g->fear < 85)
                    g->fear += 15;
            }
            if (g->forest_step == 3)
                begin_dialogue(g, D_FOREST);
        }
        if (id == 5) {
            if (HAS(g, F_FOREST | F_MIRO))
                enter_room(g, 2);
            else
                g->notice = HAS(g, F_FOREST) ? 20 : 21;
        }
        if (id == 6)
            refill(g);
        if (id == 7)
            begin_dialogue(g, D_WITNESS);
        if (id == 9)
            enter_room(g, 0);
    } else if (g->room == 2) {
        if (id == 0)
            begin_dialogue(g, D_PRIEST);
        if (id == 1)
            begin_dialogue(g, D_TIKHON);
        if (id == 2)
            refill(g);
        if (id == 3) {
            if (HAS(g, F_TOKEN) && !HAS(g, F_CHAPEL)) {
                g->mode = G_PUZZLE;
                g->chapel_step = 0;
                g->option = 0;
            } else
                g->notice = HAS(g, F_CHAPEL) ? 16 : 4;
        }
        if (id == 4) {
            if (HAS(g, F_CHAPEL)) {
                enter_room(g, 3);
                if (!HAS(g, F_REVEAL))
                    begin_dialogue(g, D_REVEAL);
            } else
                g->notice = 18;
        }
        if (id == 5)
            begin_dialogue(g, D_MARK);
        if (id == 8)
            enter_room(g, 1);
        if (id == 7) {
            if (!HAS(g, F_TOKEN))
                g->notice = 19;
            else if (g->memories & 8)
                begin_dialogue(g, D_BELL_DONE);
            else
                begin_dialogue(g, D_BELL_HINT);
        }
        if (id == 6) {
            if (HAS(g, F_PRIEST | F_TIKHON))
                begin_dialogue(g, D_TOKEN);
            else
                g->notice = 19;
        }
    } else {
        if (id == 0)
            begin_dialogue(g, !HAS(g, F_REVEAL) ? D_REVEAL :
                (HAS(g, F_FREE) ? D_FREE : D_MIRO_RELEASE));
        if (id == 1)
            g->notice = 5;
        if (id >= 2 && id <= 4) {
            if (g->charge[id - 2] >= 60) {
                g->rune_mask |= 1 << (id - 2);
                g->notice = 15;
            } else
                g->notice = 5;
            if (g->rune_mask == 7 && !HAS(g, F_WITNESS))
                begin_dialogue(g, g->evidence == 7 && votes(g) == 3 ? D_RITUAL_READY : D_RITUAL);
        }
        if (id == 5) {
            if (HAS(g, F_WITNESS))
                begin_dialogue(g, votes(g) != 3 ? D_FINAL_WARNING :
                    (g->evidence == 7 ? D_REMEMBER : D_FINAL));
            else
                g->notice = 23;
        }
        if (id == 6)
            refill(g);
        if (id == 7)
            enter_room(g, 2);
    }
}
static void move_player(Game *g, const SkInput *in) {
    SkS16 nx = g->x, ny = g->y;
    SkU8 dir = in->held & (SK_LEFT | SK_RIGHT | SK_UP | SK_DOWN);
    if (in->held & SK_AIM) {
        if (in->scope && in->aim_valid)
            g->direction = light_direction(in->x - g->x, in->y - g->y);
        else if (dir)
            g->direction = light_direction((dir & SK_RIGHT ? 1 : 0) - (dir & SK_LEFT ? 1 : 0),
                                           (dir & SK_DOWN ? 1 : 0) - (dir & SK_UP ? 1 : 0));
        return;
    }
    if (in->pressed & SK_TURN_LEFT) {
        g->direction = (g->direction + 7) & 7;
        return;
    }
    if (in->scope && in->aim_valid && !in->offscreen) {
        g->direction = light_direction(in->x - g->x, in->y - g->y);
        if (in->fire) {
            g->destination_x = in->x;
            g->destination_y = in->y;
        }
    }
    if (dir) {
        nx += (dir & SK_RIGHT ? 1 : 0) - (dir & SK_LEFT ? 1 : 0);
        ny += (dir & SK_DOWN ? 1 : 0) - (dir & SK_UP ? 1 : 0);
        g->direction = light_direction(nx - g->x, ny - g->y);
        g->destination_x = nx;
        g->destination_y = ny;
    } else if (in->scope) {
        nx += g->destination_x > g->x ? 1 : (g->destination_x < g->x ? -1 : 0);
        ny += g->destination_y > g->y ? 1 : (g->destination_y < g->y ? -1 : 0);
    }
    if (game_can_walk(g->room, nx, g->y))
        g->x = nx;
    if (game_can_walk(g->room, g->x, ny))
        g->y = ny;
}
SkS16 game_corridor_scroll(const Game *g) {
    if (g->x < 112)
        return 0;
    return g->x > 368 ? 256 : g->x - 112;
}
static void corridor_tick(Game *g, const SkInput *in) {
    SkS16 target;
    if (in->scope && in->aim_valid && in->fire && !in->offscreen)
        g->destination_x = in->x + game_corridor_scroll(g);
    if (in->held & SK_RIGHT)
        g->destination_x = CORRIDOR_END;
    else if (in->held & SK_LEFT)
        g->destination_x = CORRIDOR_START;
    else if (!in->scope)
        g->destination_x = g->x;
    target = g->destination_x;
    if (target > g->x) {
        g->direction = 2;
        g->x += target - g->x > 1 ? 2 : 1;
    } else if (target < g->x) {
        g->direction = 6;
        g->x -= g->x - target > 1 ? 2 : 1;
    }
    if (g->x < CORRIDOR_START)
        g->x = CORRIDOR_START;
    if (g->x > CORRIDOR_END)
        g->x = CORRIDOR_END;
    g->y = g->x > 464 ? 110 - (g->x - 464) * 2 : 110;
    if (g->x == CORRIDOR_END) {
        g->mode = G_DIALOGUE;
        g->x = 124;
        g->y = 176;
        g->destination_x = g->x;
        g->destination_y = g->y;
    }
}
static void tick_environment(Game *g) {
    SkU8 i;
    const Hotspot *h;
    if (g->time_notice)
        --g->time_notice;
    if (g->notice_ticks)
        --g->notice_ticks;
    i = echo_index(g->room);
    if (i != SK_NONE) {
        h = game_hotspot(g->room, i);
        if (light_sees(g, h->x, h->y)) {
            if (g->echo_charge < 45)
                ++g->echo_charge;
        } else if (g->echo_charge)
            --g->echo_charge;
    }
    if (g->ward_timer)
        --g->ward_timer;
    if (g->room == 3 && HAS(g, F_REVEAL))
        for (i = 0; i < 3; ++i) {
            h = game_hotspot(3, i + 2);
            if (light_sees(g, h->x, h->y) && distance(g->x, h->x) + distance(g->y, h->y) > 12 &&
                !(g->rune_mask & (1 << i))) {
                if (g->charge[i] < 60)
                    ++g->charge[i];
            } else if (!(g->rune_mask & (1 << i)) && g->charge[i])
                --g->charge[i];
        }
    if (++g->pulse >= 60) {
        g->pulse = 0;
        ++g->seconds;
        daycycle_second(g);
        if (g->lamp && g->oil) {
            if (g->seconds % 3 == 0)
                --g->oil;
            if (g->fear)
                --g->fear;
        } else if (game_daylight(g) >= 8) {
            if (g->fear)
                --g->fear;
        } else if (g->fear < 98)
            g->fear += 2;
    }
    if (g->fear >= 96)
        game_checkpoint(g);
}
void game_tick(Game *g, const SkInput *in) {
    SkU8 advance = (in->pressed & SK_ACTION) ||
                   (in->scope && in->fire && in->aim_valid && !in->offscreen);
    SkU16 length;
    const StoryLine *line;
    SkU8 nearby, wanted;
    if (g->mode == G_PAUSE) {
        if (in->pressed & (SK_PAUSE | SK_BACK)) {
            g->mode = g->return_mode;
            return;
        }
        if (in->pressed & SK_UP)
            g->option = g->option ? g->option - 1 : 2;
        if (in->pressed & SK_DOWN)
            g->option = (g->option + 1) % 3;
        if (in->scope && in->aim_valid)
            g->option = in->y < 112 ? 0 : (in->y < 144 ? 1 : 2);
        if (advance) {
            if (g->option == 0)
                g->mode = g->return_mode;
            else if (g->option == 1) {
                if (g->return_mode == G_CORRIDOR) {
                    g->mode = G_CORRIDOR;
                    g->x = g->destination_x = CORRIDOR_START;
                    g->y = 110;
                } else
                    game_checkpoint(g);
            } else {
                game_init(g);
                g->mode = G_MENU;
            }
        }
        return;
    }
    if ((in->pressed & SK_PAUSE) &&
        ((g->mode >= G_DIALOGUE && g->mode <= G_JOURNAL) || g->mode == G_BELL ||
         g->mode == G_CORRIDOR)) {
        g->return_mode = g->mode;
        g->mode = G_PAUSE;
        g->bow_draw = g->shot_request = 0;
        g->option = 0;
        return;
    }
    ++g->tick;
    if (g->mode == G_CORRIDOR) {
        corridor_tick(g, in);
        return;
    }
    if (g->mode == G_SPLASH) {
        if (g->tick >= 150 || advance || (in->pressed & SK_PAUSE)) {
            g->mode = G_MENU;
            g->option = 0;
        }
        return;
    }
    if (g->mode == G_MENU) {
        if (in->pressed & SK_UP)
            g->option = g->option ? g->option - 1 : 2;
        if (in->pressed & SK_DOWN)
            g->option = (g->option + 1) % 3;
        if (in->scope && in->aim_valid)
            g->option = in->y < 104 ? 0 : (in->y < 128 ? 1 : 2);
        if (advance || (in->pressed & SK_PAUSE)) {
            if (!g->option)
                game_new(g);
            else
                g->mode = g->option == 1 ? G_HELP : G_CREDITS;
        }
        return;
    }
    if (g->mode == G_HELP || g->mode == G_CREDITS || g->mode == G_END) {
        if (advance || (in->pressed & SK_BACK)) {
            g->mode = G_MENU;
            g->option = 0;
        }
        return;
    }
    if (g->mode == G_JOURNAL) {
        if (advance || (in->pressed & (SK_JOURNAL | SK_BACK)))
            g->mode = G_EXPLORE;
        return;
    }
    if (g->mode == G_DIALOGUE) {
        line = story_line(g->dialogue, g->page);
        length = line ? line->length : 0;
        if (g->revealed < length && ++g->text_delay >= 6) {
            g->text_delay = 0;
            g->revealed += 4;
            if (g->revealed > length)
                g->revealed = (SkU8)length;
        }
        if (advance) {
            if (g->revealed < length)
                g->revealed = (SkU8)length;
            else {
                ++g->page;
                g->revealed = 0;
                g->text_delay = 0;
                if (g->dialogue == D_PROLOG && g->page == 1) {
                    g->mode = G_CORRIDOR;
                    g->x = g->destination_x = CORRIDOR_START;
                    g->y = 110;
                    g->direction = 2;
                }
                if (g->page >= story_pages(g->dialogue))
                    finish_dialogue(g);
            }
        }
        return;
    }
    if (g->mode == G_CHOICE) {
        if (in->pressed & SK_BACK) {
            g->mode = G_EXPLORE;
            return;
        }
        if (in->pressed & (SK_UP | SK_DOWN))
            g->option ^= 1;
        if (in->scope && in->aim_valid)
            g->option = in->y >= 148 ? 1 : 0;
        if (advance)
            choose(g);
        return;
    }
    if (g->mode == G_BELL) {
        if (in->pressed & SK_UP)
            g->option = g->option ? g->option - 1 : 2;
        if (in->pressed & SK_DOWN)
            g->option = (g->option + 1) % 3;
        if (in->scope && in->aim_valid)
            g->option = in->y < 120 ? 0 : (in->y < 144 ? 1 : 2);
        if (in->pressed & SK_BACK) {
            g->mode = G_EXPLORE;
            return;
        }
        if (advance) {
            wanted = 0;
            if (g->bell_step == 1)
                wanted = 2;
            if (g->bell_step == 2)
                wanted = 1;
            if (g->option == wanted)
                ++g->bell_step;
            else {
                g->bell_step = 0;
                g->notice = 11;
            }
            if (g->bell_step == 3) {
                g->notice = 0;
                begin_dialogue(g, D_BELL_DONE);
            }
        }
        return;
    }
    if (g->mode == G_PUZZLE) {
        if (in->pressed & SK_UP)
            g->option = g->option ? g->option - 1 : 2;
        if (in->pressed & SK_DOWN)
            g->option = (g->option + 1) % 3;
        if (in->scope && in->aim_valid)
            g->option = in->y < 120 ? 0 : (in->y < 144 ? 1 : 2);
        if (in->pressed & SK_BACK) {
            g->mode = G_EXPLORE;
            return;
        }
        if (advance) {
            if (g->option == g->chapel_step)
                ++g->chapel_step;
            else {
                g->chapel_step = 0;
                g->notice = 6;
            }
            if (g->chapel_step == 3)
                begin_dialogue(g, D_CHAPEL);
        }
        return;
    }
    if (g->mode != G_EXPLORE)
        return;
    if (in->pressed & SK_JOURNAL) {
        g->mode = G_JOURNAL;
        g->bow_draw = g->shot_request = 0;
        return;
    }
    if (in->pressed & SK_LIGHT)
        g->lamp = !g->lamp;
    if (in->pressed & SK_BACK)
        silver_ward(g);
    if (!g->bow_mode && !(in->pressed & SK_TURN_LEFT))
        move_player(g, in);
    else if (g->bow_mode && !(g->tick & 1) && !g->bow_draw && !g->shot_request &&
             g->bow_cooldown <= 16 && !(in->held & SK_ACTION) && !in->fire &&
             (in->held & (SK_LEFT | SK_RIGHT | SK_UP | SK_DOWN))) {
        /* Lower the string to take careful half-speed steps. Holding A
           anchors the feet and turns the same pad directions into aim. */
        move_player(g, in);
        g->bow_direction = g->direction << 1;
    }
    tick_environment(g);
    combat_tick(g, in);
    if (g->fear >= 96 && g->mode == G_EXPLORE)
        game_checkpoint(g);
    if (!g->bow_mode && g->mode == G_EXPLORE &&
        ((!(g->tick & 3) && !g->notice_ticks) || advance || (in->pressed & SK_LIGHT)))
        g->focus = game_nearby(g);
    if (g->mode == G_EXPLORE && advance && !g->bow_mode) {
        nearby = g->focus;
        /* A gun click on the next destination must not activate the object
           currently beside the player. Pad A still inspects the nearest one. */
        if (in->scope && in->fire) {
            if (!in->aim_valid)
                return;
            nearby = scope_nearby(g, in);
            if (nearby == SK_NONE) return;
        }
        interact(g, nearby);
    }
}
const char *game_goal(const Game *g) {
    if (HAS(g, F_WITNESS) && votes(g) != 3) {
        if (!HAS(g, F_KIND)) return TXT_G_REPAIR_EGOR;
        if (!HAS(g, F_CONFESS)) return TXT_G_REPAIR_MIRO;
        return TXT_G_REPAIR_FREE;
    }
    if (g->room == 0) {
        if (!HAS(g, F_HEAD)) return TXT_G_HEAD;
        return HAS(g, F_EGOR) ? TXT_G_TO_FOREST : TXT_G_EGOR;
    }
    if (g->room == 1) {
        if (!HAS(g, F_BIRCH)) return TXT_G_BIRCH;
        if (!HAS(g, F_MIRO)) return TXT_G_MIRO;
        return HAS(g, F_FOREST) ? TXT_G_TO_CHAPEL : TXT_G_FOREST;
    }
    if (g->room == 2) {
        if (!HAS(g, F_PRIEST | F_TIKHON)) return TXT_G_CHAPEL;
        if (!HAS(g, F_TOKEN)) return TXT_G_TOKEN;
        return HAS(g, F_CHAPEL) ? TXT_G_TO_HEART : TXT_G_CUPS;
    }
    if (!HAS(g, F_REVEAL))
        return TXT_G_REVEAL;
    return HAS(g, F_WITNESS) ? TXT_G_FINAL : TXT_G_SEAL;
}
const char *game_journal(const Game *g) {
    if (HAS(g, F_WITNESS)) {
        if (votes(g) != 3) return TXT_J_REPAIR;
        return g->evidence == 7 ? TXT_J_READY : TXT_J_FINAL;
    }
    if (HAS(g, F_REVEAL) && votes(g) == 3)
        return TXT_J_SEAL;
    if (HAS(g, F_REVEAL))
        return TXT_J_TRUTH;
    if (HAS(g, F_TOKEN))
        return TXT_J_SILVER;
    if (HAS(g, F_BIRCH))
        return TXT_J_FOREST;
    if (HAS(g, F_EGOR))
        return TXT_J_EGOR;
    if (HAS(g, F_HEAD))
        return TXT_J_HEAD;
    return TXT_J_EMPTY;
}
