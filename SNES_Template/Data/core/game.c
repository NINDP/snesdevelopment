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
}
void game_init(Game *g) {
    memset(g, 0, sizeof(*g));
    daycycle_init(g);
    g->mode = G_SPLASH;
    g->oil = 120;
}
void game_new(Game *g) {
    memset(g, 0, sizeof(*g));
    daycycle_init(g);
    g->oil = 120;
    enter_room(g, 0);
    begin_dialogue(g, D_PROLOG);
}
void game_checkpoint(Game *g) {
    enter_room(g, g->checkpoint_room);
    g->oil = 120;
    g->fear = 15;
    g->lamp = 1;
    begin_dialogue(g, D_RETRY);
}
static SkU8 votes(const Game *g) {
    return (HAS(g, F_KIND) ? 1 : 0) + (HAS(g, F_CONFESS) ? 1 : 0) + (HAS(g, F_FREE) ? 1 : 0);
}
static void choose_ending(Game *g, SkU8 give_village) {
    if (give_village || votes(g) != 3)
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
        begin_choice(g, C_EGOR);
        break;
    case D_BIRCH:
        g->flags |= F_BIRCH;
        break;
    case D_MIRO:
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
    case D_RITUAL:
        g->flags |= F_WITNESS;
        break;
    case D_FINAL:
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
    case D_BAD:
    case D_SECRET:
        begin_dialogue(g, D_MODERN);
        break;
    case D_MODERN:
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
        if (!g->option)
            g->flags |= F_KIND;
        begin_dialogue(g, g->option ? D_LOCK : D_KIND);
        break;
    case C_CONFESS:
        g->flags |= F_MIRO;
        if (!g->option)
            g->flags |= F_CONFESS;
        begin_dialogue(g, g->option ? D_DENY : D_CONFESS);
        break;
    case C_MIRO:
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
    SkRect obstacle;
    if (x < 12 || x > 244 || y < 32 || y > 180)
        return 0;
    if (room == 0) {
        obstacle.x = 14;
        obstacle.y = 30;
        obstacle.w = 70;
        obstacle.h = 33;
        if (sk_contains(&obstacle, x, y))
            return 0;
        obstacle.x = 157;
        obstacle.y = 30;
        obstacle.w = 78;
        obstacle.h = 38;
    } else if (room == 2) {
        obstacle.x = 101;
        obstacle.y = 29;
        obstacle.w = 55;
        obstacle.h = 24;
    } else {
        obstacle.x = 106;
        obstacle.y = 28;
        obstacle.w = 46;
        obstacle.h = 20;
    }
    return !sk_contains(&obstacle, x, y);
}
SkU8 game_nearby(const Game *g) {
    SkU8 i, best = SK_NONE;
    SkS16 d, minimum = 42;
    const Hotspot *h;
    for (i = 0; i < game_hotspot_count(g->room); ++i) {
        h = game_hotspot(g->room, i);
        d = distance(g->x, h->x) + distance(g->y, h->y);
        if (d >= minimum)
            continue;
        if (!game_visible(g, h->x, h->y))
            continue;
        best = i;
        minimum = d;
    }
    return best;
}
static void refill(Game *g) {
    g->oil = 120;
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
}
static void interact(Game *g, SkU8 id) {
    if (id == SK_NONE) {
        if (!game_daylight(g) && (!g->lamp || !g->oil))
            begin_dialogue(g, D_NO_LIGHT);
        return;
    }
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
        if (id == 1 && !HAS(g, F_MIRO))
            begin_dialogue(g, D_MIRO);
        if (id >= 2 && id <= 4) {
            if (!HAS(g, F_BIRCH)) {
                g->notice = 3;
                return;
            }
            if (HAS(g, F_FOREST))
                return;
            if (id - 2 == g->forest_step)
                ++g->forest_step;
            else {
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
                g->notice = 3;
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
                g->notice = 4;
        }
        if (id == 4) {
            if (HAS(g, F_CHAPEL)) {
                enter_room(g, 3);
                if (!HAS(g, F_REVEAL))
                    begin_dialogue(g, D_REVEAL);
            } else
                g->notice = 4;
        }
        if (id == 5)
            begin_dialogue(g, D_MARK);
        if (id == 8)
            enter_room(g, 1);
        if (id == 7) {
            if (!HAS(g, F_TOKEN))
                g->notice = 4;
            else if (g->memories & 8)
                begin_dialogue(g, D_BELL_DONE);
            else
                begin_dialogue(g, D_BELL_HINT);
        }
        if (id == 6) {
            if (HAS(g, F_PRIEST | F_TIKHON))
                begin_dialogue(g, D_TOKEN);
            else
                g->notice = 4;
        }
    } else {
        if (id == 0 && !HAS(g, F_REVEAL))
            begin_dialogue(g, D_REVEAL);
        if (id == 1)
            g->notice = 5;
        if (id >= 2 && id <= 4) {
            if (g->charge[id - 2] >= 60) {
                g->rune_mask |= 1 << (id - 2);
            } else
                g->notice = 5;
            if (g->rune_mask == 7 && !HAS(g, F_WITNESS))
                begin_dialogue(g, D_RITUAL);
        }
        if (id == 5) {
            if (HAS(g, F_WITNESS))
                begin_dialogue(g, g->memories == 15 ? D_REMEMBER : D_FINAL);
            else
                g->notice = 5;
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
    g->enemy_active = g->room == 3 || (g->room == 1 && game_daylight(g) < 8);
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
    if (g->enemy_active && !g->ward_timer && g->tick % 8 == 0) {
        if (light_sees(g, g->enemy_x, g->enemy_y)) {
            if (g->enemy_x < 238)
                g->enemy_x += 2;
        } else {
            if (g->enemy_x < g->x)
                ++g->enemy_x;
            else if (g->enemy_x > g->x)
                --g->enemy_x;
            if (g->enemy_y < g->y)
                ++g->enemy_y;
            else if (g->enemy_y > g->y)
                --g->enemy_y;
        }
        if (distance(g->x, g->enemy_x) + distance(g->y, g->enemy_y) < 18 && g->fear < 96)
            g->fear += 4;
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
    const Hotspot *point;
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
        return;
    }
    if (in->pressed & SK_LIGHT)
        g->lamp = !g->lamp;
    if (in->pressed & SK_BACK)
        silver_ward(g);
    move_player(g, in);
    tick_environment(g);
    if (g->mode == G_EXPLORE && advance) {
        nearby = game_nearby(g);
        /* A gun click on the next destination must not activate the object
           currently beside the player. Pad A still inspects the nearest one. */
        if (in->scope && in->fire) {
            if (!in->aim_valid)
                return;
            if (nearby == SK_NONE)
                return;
            point = game_hotspot(g->room, nearby);
            if (distance(in->x, point->x) + distance(in->y, point->y) > 14)
                return;
        }
        interact(g, nearby);
    }
}
const char *game_goal(const Game *g) {
    if (g->room == 0)
        return TXT_G_HEAD;
    if (g->room == 1)
        return TXT_G_FOREST;
    if (g->room == 2)
        return TXT_G_CHAPEL;
    if (!HAS(g, F_REVEAL))
        return TXT_G_REVEAL;
    return HAS(g, F_WITNESS) ? TXT_G_FINAL : TXT_G_SEAL;
}
const char *game_journal(const Game *g) {
    if (HAS(g, F_WITNESS))
        return TXT_J_SEAL;
    if (HAS(g, F_REVEAL))
        return TXT_J_TRUTH;
    if (HAS(g, F_TOKEN))
        return TXT_J_SILVER;
    if (HAS(g, F_BIRCH))
        return TXT_J_FOREST;
    if (HAS(g, F_EGOR))
        return TXT_J_EGOR;
    return TXT_J_EMPTY;
}
