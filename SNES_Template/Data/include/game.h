#ifndef CHERNORECHYE_GAME_H
#define CHERNORECHYE_GAME_H
#include "sneskit.h"
enum GameMode {
    G_SPLASH,
    G_MENU,
    G_DIALOGUE,
    G_EXPLORE,
    G_CHOICE,
    G_PUZZLE,
    G_JOURNAL,
    G_PAUSE,
    G_END,
    G_HELP,
    G_CREDITS,
    G_BELL,
    G_CORRIDOR
};
enum StoryFlag {
    F_HEAD = 1,
    F_EGOR = 2,
    F_KIND = 4,
    F_BIRCH = 8,
    F_CONFESS = 16,
    F_MIRO = 32,
    F_FOREST = 64,
    F_PRIEST = 128,
    F_TIKHON = 256,
    F_TOKEN = 512,
    F_CHAPEL = 1024,
    F_REVEAL = 2048,
    F_FREE = 4096,
    F_WITNESS = 8192,
    F_SEALED = 16384,
    F_HEART_TRUTH = 32768
};
enum DialogueId {
    D_PROLOG,
    D_HEAD,
    D_EGOR,
    D_KIND,
    D_LOCK,
    D_BIRCH,
    D_MIRO,
    D_CONFESS,
    D_DENY,
    D_FOREST,
    D_PRIEST,
    D_TIKHON,
    D_TOKEN,
    D_CHAPEL,
    D_REVEAL,
    D_FREE,
    D_BIND,
    D_RITUAL,
    D_FINAL,
    D_GOOD,
    D_BAD,
    D_SECRET,
    D_MODERN,
    D_GATE,
    D_GRAVE,
    D_WITNESS,
    D_MARK,
    D_NO_LIGHT,
    D_RETRY,
    D_ECHO_HOME,
    D_ECHO_BOAT,
    D_ECHO_STONE,
    D_BELL_HINT,
    D_BELL_DONE,
    D_EGOR_RETURN,
    D_EGOR_CAGED,
    D_REMEMBER,
    D_MIRO_RETRY,
    D_MIRO_RELEASE,
    D_RITUAL_READY,
    D_FINAL_WARNING,
    D_REPAIR,
    D_END_STAY,
    D_END_LOST,
    D_COUNT
};
enum ChoiceId { C_EGOR, C_CONFESS, C_MIRO, C_FINAL };
enum EndingId { END_GOOD, END_BAD, END_SECRET };
enum TimePhase { TIME_NIGHT, TIME_DAWN, TIME_DAY, TIME_DUSK };
#define DAY_CYCLE_SECONDS 768
#define DAY_START_SECONDS 512
#define COMBAT_ENEMIES 4
#define COMBAT_ARROWS 3
#define BOW_AMMO_MAX 24
#define BOW_DRAW_TICKS 18
#define BOW_MIN_DRAW 6
#define BOW_COOLDOWN 24
#define SHOVE_COOLDOWN 60
enum EnemyKind { ENEMY_SHADE, ENEMY_CRAWLER };
enum EnemyState { ENEMY_HUNT, ENEMY_WINDUP, ENEMY_LUNGE, ENEMY_RECOVER };
typedef struct {
    SkS16 x, y;
    SkU8 hp, hit, kind, attack;
    SkU16 respawn;
    /* step stores the locked eight-way direction during windup/lunge. */
    SkU8 step, state;
} Enemy;
typedef struct {
    /* Quarter-world-unit coordinates; velocity uses the same units. */
    SkS16 x, y;
    SkS8 dx, dy;
    SkU8 life, damage;
} Arrow;
typedef struct {
    const char *speaker;
    const char *text;
    SkU8 length;
} StoryLine;
typedef struct {
    SkS16 x, y;
    const char *name;
} Hotspot;
/* Existing 52-byte state prefix is stable; the world clock follows it. */
typedef struct {
    SkU8 mode, room, dialogue, page, option, choice;
    SkU8 lamp, direction, oil, fear, forest_step, chapel_step;
    SkU8 rune_mask, evidence, ending, revealed, return_mode, journal_page;
    SkU8 checkpoint_room, notice, pulse, enemy_active, charge[3], last_hotspot;
    SkU16 flags, tick, seconds, interactions;
    SkS16 x, y, destination_x, destination_y, enemy_x, enemy_y;
    SkU8 memories, echo_charge, wards, bell_step, ward_timer, text_delay;
    SkU16 day_seconds, day_number;
    SkU8 sun_level, time_phase, time_notice;
    SkU8 enemy_slots; /* Cached population limit; uses the old padding byte. */
    SkU16 nights, kills;
    SkU8 bow_mode, bow_draw, bow_cooldown, bow_direction;
    SkU8 ammo, shot_request, combat_notice, combat_notice_ticks;
    SkS16 aim_x, aim_y;
    Enemy enemies[COMBAT_ENEMIES];
    Arrow arrows[COMBAT_ARROWS];
    SkU8 notice_ticks, focus;
    SkU8 hurt_timer, shove_cooldown;
    SkU8 hit_stop, enemy_clock;
} Game;
#define TORCH_RADIUS 64
#define CORRIDOR_START 80
#define CORRIDOR_END 488
SkS16 game_corridor_scroll(const Game *g);
extern const SkU8 torch_width[TORCH_RADIUS + 1];
void game_init(Game *g);
void game_new(Game *g);
void game_tick(Game *g, const SkInput *input);
void game_checkpoint(Game *g);
SkU8 game_nearby(const Game *g);
SkU8 game_hotspot_count(SkU8 room);
const Hotspot *game_hotspot(SkU8 room, SkU8 index);
const StoryLine *story_line(SkU8 id, SkU8 page);
SkU8 story_pages(SkU8 id);
const char *room_name(SkU8 room);
const char *game_goal(const Game *g);
const char *game_journal(const Game *g);
const char *choice_text(SkU8 id, SkU8 option);
SkU8 game_can_walk(SkU8 room, SkS16 x, SkS16 y);
void light_span(const Game *g, SkS16 y, SkS16 *left, SkS16 *right);
SkU8 light_sees(const Game *g, SkS16 x, SkS16 y);
SkU8 light_direction(SkS16 dx, SkS16 dy);
void daycycle_init(Game *g);
void daycycle_second(Game *g);
SkU8 game_daylight(const Game *g);
SkU8 game_visible(const Game *g, SkS16 x, SkS16 y);
const char *game_time_name(const Game *g);
const char *game_time_event(const Game *g);
const char *game_time_hint(const Game *g);
void combat_init(Game *g);
void combat_enter(Game *g);
void combat_tick(Game *g, const SkInput *in);
void combat_ward(Game *g);
SkU8 combat_capacity(const Game *g);
SkU8 combat_tier(const Game *g);
SkU8 combat_direction(SkS16 dx, SkS16 dy);
SkU8 combat_pick(const Game *g, SkS16 sx, SkS16 sy, SkS16 *x, SkS16 *y);
#endif
