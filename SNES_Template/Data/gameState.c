
#include <snes.h>
#include "include/platform.h"
#include "include/scope_input.h"
#include "include/perspective.h"

static Game game;
static SkInput frame_input;
static SkU8 draw_pending;
static SkClock clock;
static ScopePacket packet;
static SkU8 calibration = 0, scope_ready = 0, calibration_wait_release = 0;
static SkU16 previous_vblank = 0;

static void map_button(SkInput *in, SkU16 pad, SkU16 edge, SkU16 key, SkU16 action) {
    if (pad & key)
        in->held |= action;
    if (edge & key)
        in->pressed |= action;
}

static SkInput read_input(void) {
    SkInput in;
    SkU16 pad = scope_pad_buttons(), edge = packet.pad_pressed;

    in.held = 0;
    in.pressed = 0;
    in.x = game.x;
    in.y = game.y;
    in.aim_valid = 0;
    in.fire = 0;
    in.offscreen = 0;
    in.scope = 0;

    map_button(&in, pad, edge, KEY_LEFT, SK_LEFT);
    map_button(&in, pad, edge, KEY_RIGHT, SK_RIGHT);
    map_button(&in, pad, edge, KEY_UP, SK_UP);
    map_button(&in, pad, edge, KEY_DOWN, SK_DOWN);
    map_button(&in, pad, edge, KEY_A, SK_ACTION);
    map_button(&in, pad, edge, KEY_B, SK_BACK);
    map_button(&in, pad, edge, KEY_X, SK_LIGHT);
    map_button(&in, pad, edge, KEY_Y, SK_JOURNAL);
    map_button(&in, pad, edge, KEY_R, SK_AIM);
    map_button(&in, pad, edge, KEY_L, SK_TURN_LEFT);
    map_button(&in, pad, edge, KEY_START, SK_PAUSE);

    /* The first gun click opens an explicit calibration target. */
    if (packet.connected && !scope_ready &&
        (packet.buttons & (SSC_FIRE | SSC_CURSOR))) {
        calibration = 1;
        calibration_wait_release = 1;
        packet.buttons = 0;
        packet.valid = 0;
        return in;
    }

    if (packet.connected && scope_ready) {
        in.scope = 1;
        in.x = packet.raw_x + scope_centerh;
        in.y = packet.raw_y + scope_centerv;
        in.offscreen = (packet.flags & SSC_OFFSCREEN) != 0;

        in.aim_valid =
            packet.valid && !packet.flags &&
            in.x >= 0 && in.x < 256 &&
            in.y >= 0 && in.y < 224;

        in.fire = (packet.buttons & SSC_FIRE) != 0;

        if (packet.buttons & SSC_TURBO)
            in.held |= SK_AIM;
        if (packet.buttons & SSC_CURSOR)
            in.pressed |= SK_LIGHT;
        if (packet.buttons & SSC_PAUSE)
            in.pressed |= SK_PAUSE;
    }

    /* Coordinate conversion is handled in GameUpdate. */

    if ((edge & KEY_SELECT) && packet.connected) {
        calibration = 1;
        scope_ready = 0;
        calibration_wait_release = 1;
    }

    return in;
}

static void calibrate(void) {
    video_calibration(
        calibration,
        packet.raw_x + scope_centerh,
        packet.raw_y + scope_centerv
    );

    flashlight_prepare(&game, 0);

    if (calibration_wait_release) {
        /* Drain already published gun edges before arming the target. */
        if (!(scope_held_buttons() & (SSC_FIRE | SSC_CURSOR)) &&
            !scope_packets_pending())
            calibration_wait_release = 0;
    } else {
        if (calibration == 1 &&
            (packet.buttons & SSC_FIRE) &&
            packet.valid && !packet.flags) {

            scope_centerh = 128 - packet.raw_x;
            scope_centerv = 112 - packet.raw_y;
            calibration = 2;

        } else if (calibration == 2 &&
                   (packet.buttons & SSC_CURSOR)) {

            calibration = 0;
            scope_ready = 1;
        }
    }

    if (packet.pad_pressed & KEY_B) {
        calibration = 1;
        scope_ready = 0;
        calibration_wait_release = 1;
    }

    if (!packet.connected || (packet.pad_pressed & KEY_START)) {
        calibration = 0;
        scope_ready = 0;
        calibration_wait_release = 0;
    }

    if (!calibration) {
        setPaletteColor(29, RGB5(28, 28, 24));
        setPaletteColor(30, RGB5(1, 2, 3));
    }
}

/* Template lifecycle: one input/update pass and one draw pass per VBlank. */

void GameStart(void) {
    game_init(&game);
    clock.accumulator = 0;
    audio_init();
    video_init();
    detectSuperScope();
    nmiSet(scope_capture_vblank);
    setScreenOn();
}

void GameUpdate(void) {
    SkU16 delta;
    SkU8 elapsed, ticks, i, j;

    /* Separate world coordinates avoid aliasing input structure fields. */
    SkS16 world_x, world_y;
    SkU8 valid;

    draw_pending = 0;

    WaitForVBlank();
    video_commit();
    scope_take_packet(&packet);

    delta = snes_vblank_count - previous_vblank;
    previous_vblank = snes_vblank_count;
    elapsed = delta > 4 ? 4 : (SkU8)delta;

    /* Service the audio stream before simulation. */
    audio_update(&game);

    if (calibration) {
        calibrate();
        return;
    }

    frame_input = read_input();

    if (calibration) {
        calibrate();
        return;
    }

    /*
     * Super Scope coordinate conversion.
     *
     * Convert screen-space aiming coordinates into
     * world-space coordinates before game_tick().
     */
    if (game.mode == G_EXPLORE &&
        frame_input.scope &&
        frame_input.aim_valid) {

        world_x = frame_input.x;
        world_y = frame_input.y;
        valid = 0;

        if (game.bow_mode) {
            valid = combat_pick(
                &game,
                frame_input.x,
                frame_input.y,
                &world_x,
                &world_y
            );

            if (!valid) {
                valid = perspective_pick(
                    &game,
                    frame_input.x,
                    frame_input.y,
                    &world_x,
                    &world_y
                );
            }
        } else {
            valid = perspective_pick_target(
                &game,
                frame_input.x,
                frame_input.y,
                &world_x,
                &world_y
            );
        }

        frame_input.aim_valid = valid;

        if (valid) {
            frame_input.x = world_x;
            frame_input.y = world_y;
        }
    }

    for (j = 0; j < elapsed; ++j) {
        ticks = sk_clock_ticks(&clock, snes_fps);

        for (i = 0; i < ticks; ++i) {
            game_tick(&game, &frame_input);
            frame_input.pressed = 0;
            frame_input.fire = 0;
        }
    }

    draw_pending = 1;
}

void GameDraw(void) {
    if (!draw_pending)
        return;

    video_draw(&game, frame_input.scope);
}

void GameEnd(void) {
    REG_HDMAEN = 0;
    REG_TMW = 0;
}
