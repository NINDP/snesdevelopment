#!/usr/bin/env python3
"""Exercise archery and a live night creature through real controller events.

State is observed read-only. All movement, aiming, arrows and pauses go through
the ROM's normal input path; no RAM writes or emulator save-state patching.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from libretro import Emulator, ROOT
from rom_smoke import Runner, daylight


def run(core, pal=False):
    e = Emulator(core, True, pal)
    r = Runner(e, False)
    region = 'pal' if pal else 'ntsc'
    shots = []

    def capture(name):
        e.want_frame = True
        e.run(1)
        e.want_frame = False
        assert e.frame is not None
        im = e.frame.copy()
        assert im.size == (256, 224)
        s = e.state()
        cut = 200 if s['time_notice'] or s['bow_mode'] else 224
        pixels = np.asarray(im)[:cut - 1]
        if s['mode'] == 3 and not daylight(s) and s['lamp'] and s['oil']:
            cx, cy = (106, 145) if s['bow_mode'] else (
                ((119, 125), (140, 126), (136, 127), (116, 126))[(s['direction'] >> 1) & 3])
            yy, xx = np.ogrid[:len(pixels), :256]
            outside = (xx-cx)**2 + (yy-cy)**2 > 81**2
            assert not np.any(np.any(pixels, axis=2) & outside), ('Night archery reveals the world', name, s)
        im.save(ROOT / 'build' / ('combat-' + region + '-' + name + '.png'))
        shots.append((name, im))

    def alive(s):
        return [enemy for enemy in s['enemies'] if enemy['hp']]

    def frozen():
        before = copy.deepcopy(e.state())
        e.run(120)
        after = e.state()
        for field in ('arrows', 'enemies', 'ammo', 'bow_draw', 'bow_cooldown',
                      'day_seconds', 'nights', 'kills'):
            assert after[field] == before[field], ('Combat advanced on pause', field, before, after)

    try:
        e.run(190)
        e.tap(8)
        r.finish()
        assert e.state()['mode'] == 3 and e.state()['ammo'] == 24
        r.light()
        serial = e.state()['interactions']
        e.tap(10)
        assert e.state()['bow_mode']
        capture('ready')
        position = (e.state()['x'], e.state()['y'])
        e.buttons = {8, 7}
        e.run(3)  # Fewer than six logical ticks in both PAL and NTSC.
        e.buttons = set()
        e.run(8)
        assert e.state()['ammo'] == 24, 'A short cancelled draw consumed an arrow'
        assert (e.state()['x'], e.state()['y']) == position, 'Archer slid while aiming'
        e.buttons = {8, 4}
        e.wait_state(lambda s: s['bow_draw'] >= 8, 'Half-draw animation')
        capture('half-draw')
        e.wait_state(lambda s: s['bow_draw'] == 18, 'Full draw')
        capture('full-draw')
        ready, half, full = [np.asarray(dict(shots)[name])[116:164, 112:144]
                             for name in ('ready', 'half-draw', 'full-draw')]
        assert np.count_nonzero(np.any(ready != full, axis=2)) > 20, 'Bow stance never changed'
        assert np.count_nonzero(np.any(half != full, axis=2)) > 8, 'Half/full draw use one pose'
        assert e.state()['ammo'] == 24 and e.state()['interactions'] == serial
        e.buttons = set()
        e.wait_state(lambda s: s['ammo'] == 23, 'Pad release must launch one arrow')
        capture('release')
        assert any(a['life'] and a['damage'] for a in e.state()['arrows'])
        e.tap(3)
        e.wait_mode(7)
        frozen()
        capture('paused-flight')
        e.tap(3)
        e.wait_mode(3)
        e.run(90)
        assert e.state()['ammo'] == 23 and not any(a['life'] for a in e.state()['arrows'])
        e.tap(10)
        assert not e.state()['bow_mode']
        r.inspect(2)
        assert e.state()['ammo'] == 24, 'Resin vessel did not refill the quiver'
        r.inspect(0)
        r.inspect(1)
        r.choose(0)
        r.inspect(3)
        assert e.state()['room'] == 1 and not alive(e.state())
        # A safe horizontal firing lane, reached while the forest is sunlit.
        r.walk(170, 120)
        for _ in range(1600):
            s = e.state()
            assert s['mode'] == 3
            if s['day_seconds'] >= 640:
                break
            e.run(15)
        else:
            raise AssertionError(('Night never arrived', e.state()))
        assert e.state()['nights'] == 1 and len(alive(e.state())) == 1
        capture('first-night')

        # Calibrate only after the pad checks; a valid optical edge is needed
        # for Scope archery as well as for exploration.
        e.gun_tap(2, 200, 175)
        e.gun_tap(2, 128, 112)
        e.gun_tap(3, 128, 112)
        e.tap(10)
        assert e.state()['bow_mode']
        capture('night-ready')
        ammo = e.state()['ammo']
        e.gun = {2, 15}
        e.run(30)
        e.gun = set()
        e.run(30)
        assert e.state()['ammo'] == ammo and not e.state()['shot_request'], 'Offscreen Scope fired an arrow'
        target = alive(e.state())[0]
        sx, sy = r.screen_point(target['x'], target['y'])
        e.x, e.y = sx, sy - 16  # Aim at the creature's torso, not the floor.
        e.gun = {2}
        e.wait_state(lambda s: s['shot_request'] or s['bow_draw'], 'Scope shot was not queued')
        e.gun = set()
        capture('scope-draw')
        kills = e.state()['kills']
        impact_seen = False
        for _ in range(180):
            e.run(1)
            s = e.state()
            if not impact_seen and any(a['life'] and not a['damage'] for a in s['arrows']):
                capture('impact')
                impact_seen = True
            if s['kills'] > kills:
                break
        else:
            raise AssertionError(('Scope arrow did not kill the visible creature', e.state(), (sx, sy)))
        assert e.state()['ammo'] == ammo - 1
        assert not alive(e.state()) and e.state()['enemies'][0]['respawn'] > 0
        capture('creature-defeated')
        e.run(120)
        assert not alive(e.state()), 'Creature respawned immediately'

        sheet = Image.new('RGB', (768, 464), (0, 0, 0))
        draw_text = ImageDraw.Draw(sheet)
        selected = ['ready', 'half-draw', 'full-draw', 'release', 'night-ready', 'creature-defeated']
        images = dict(shots)
        for index, name in enumerate(selected):
            x = index % 3 * 256
            y = index // 3 * 232
            sheet.paste(images[name], (x, y+8))
            draw_text.text((x+4, y), name, fill=(220, 200, 150))
        sheet.save(ROOT / 'build' / ('combat-' + region + '-preview.png'))
        frames = [im for _, im in shots]
        frames[0].save(ROOT / 'build' / ('combat-' + region + '.gif'), save_all=True,
                       append_images=frames[1:], duration=550, loop=0)
        report = {'region': region.upper(),
                  'rom_sha256': json.loads((ROOT / 'build/link_manifest.json').read_text())['rom_sha256'],
                  'checks': ['cancelled draw', 'stationary bow aim', 'half/full/release poses',
                             'pad arrow', 'projectile pause', 'quiver refill', 'first night creature',
                             'planted torch darkness', 'offscreen Scope rejected',
                             'Scope torso hit', 'projectile kill', 'delayed respawn'],
                  'frames': e.frames, 'impact_seen': impact_seen, 'final_state': e.state()}
        (ROOT / 'build' / ('combat-regression-' + region + '.json')).write_text(
            json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), 'PASS')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
