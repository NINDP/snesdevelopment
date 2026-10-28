#!/usr/bin/env python3
"""Observe four successive dusks, then fight the real fourth-night population.

The chapel serves as a refuge while normal exploration advances the clock.
Oil is replenished by interacting with its vessel; RAM is never changed.
The four-creature movement budget is at least 30 updates per 60 video frames,
with no gap above two VBlanks. Logical time must still advance at 60 Hz.
"""
import argparse
import ctypes as C
import json
import re
import struct
from pathlib import Path

import numpy as np

from libretro import Emulator, ROOT
from rom_smoke import Runner, world_cut


def run(core, pal=False, allow_cadence_drops=False):
    e = Emulator(core, True, pal)
    r = Runner(e, False)
    region = 'pal' if pal else 'ntsc'
    symbols = (ROOT / 'chernorechye.sym').read_text()

    def address(name):
        match = re.search(r'^([0-9a-fA-F]{8}) .*' + re.escape(name) + r'$', symbols, re.M)
        assert match, ('Missing read-only probe', name)
        value = int(match[1], 16) - 0x7e0000
        assert 0 <= value < 0x20000
        return value

    stamp_address = address('_previous_vblank')
    oam_address = address('oamMemory')

    def stamp():
        return struct.unpack('<H', C.string_at(e.memory + stamp_address, 2))[0]

    def capture(name):
        e.want_frame = True
        e.run(1)
        e.want_frame = False
        assert e.frame is not None and e.frame.size == (256, 224)
        s = e.state()
        if s['mode'] == 3 and s['room'] == 1 and s['sun_level'] == 0:
            pixels = np.asarray(e.frame)
            cut = world_cut(s)
            cy = 145 if s['bow_mode'] else ((125, 126, 127, 126)[(s['direction'] >> 1) & 3])
            cx = 106 if s['bow_mode'] else ((119, 140, 136, 116)[(s['direction'] >> 1) & 3])
            yy, xx = np.ogrid[:cut-1, :256]
            escaped = np.any(pixels[:cut-1], axis=2) & ((xx-cx)**2 + (yy-cy)**2 > 81**2)
            assert not np.any(escaped), ('Fourth-night light leaked', name, s)
        e.frame.save(ROOT / 'build' / ('survival-' + region + '-' + name + '.png'))

    def alive():
        return [enemy for enemy in e.state()['enemies'] if enemy['hp']]

    try:
        e.run(190)
        e.tap(8)
        r.finish()
        r.light()
        r.inspect(0)
        r.inspect(1)
        r.choose(0)
        r.inspect(3)
        r.inspect(0)
        r.inspect(1)
        r.choose(0)
        for index in (2, 3, 4):
            r.inspect(index)
        r.inspect(5)
        assert e.state()['room'] == 2
        r.inspect(2)
        capture('refuge')
        dusks = []
        previous_night = 0
        refills = 1
        # Fifty world minutes can fit between probes; a dusk cannot be skipped.
        for _ in range(20000):
            s = e.state()
            assert s['mode'] == 3 and s['room'] == 2, ('Refuge stopped exploration', s)
            assert not alive(), ('Nechist entered the refuge', s)
            if s['nights'] != previous_night:
                assert s['nights'] == previous_night + 1, ('Night count jumped', s)
                previous_night = s['nights']
                dusks.append({'night': s['nights'], 'world_day': s['day_number'],
                              'second': s['day_seconds'], 'frame': e.frames})
                print(region, 'dusk', s['nights'], 'frame', e.frames, flush=True)
                capture('dusk-' + str(s['nights']))
            if s['nights'] == 4 and s['day_seconds'] >= 640:
                break
            if s['oil'] < 40:
                # The player remains beside the vessel between refills.
                before = s['interactions']
                r.action()
                e.wait_state(lambda x: x['interactions'] > before, 'Refuge vessel interaction')
                assert e.state()['ammo'] == 24 and e.state()['oil'] > 110
                refills += 1
            e.run(300)
        else:
            raise AssertionError(('Four dusks never arrived', e.state()))
        assert [x['night'] for x in dusks] == [1, 2, 3, 4]
        assert e.state()['day_number'] == 4
        # Establish optical calibration while still sheltered.
        e.gun_tap(2, 200, 175)
        e.gun_tap(2, 128, 112)
        e.gun_tap(3, 128, 112)
        r.inspect(8)
        assert e.state()['room'] == 1 and e.state()['nights'] == 4
        assert len(alive()) == 4
        assert sorted(enemy['hp'] for enemy in alive()) == [1, 1, 2, 2]
        e.run(12)
        capture('four-creatures')
        oam = C.string_at(e.memory + oam_address, 544)
        slots = (56, 60, 62, 64)
        assert all(oam[slot*4+1] != 240 for slot in slots), 'A fourth-night actor is missing from OAM'

        # A fullscreen journal must hide every combat slot, including the
        # fourth creature beyond the legacy 64-slot cinematic actor range.
        vram=e.lib.retro_get_memory_data(3)
        world_tiles=C.string_at(vram,0xa000)
        e.tap(1);e.wait_mode(6);e.run(20)
        journal=(ROOT/'assets/generated/journal.chr').read_bytes()
        assert C.string_at(vram,len(journal))==journal,'Fourth-night journal artwork missing'
        oam=C.string_at(e.memory+oam_address,544)
        assert all(oam[n*4+1]==240 for n in range(128)),'Combat actor leaked onto the journal'
        capture('journal-fourth-night')
        e.tap(1);e.wait_mode(3);e.run(20)
        assert C.string_at(vram,0xa000)==world_tiles,'Journal return damaged the world'

        previous = stamp()
        updates = max_gap = 0
        clock_before = e.state()
        fear_before = clock_before['fear']
        e.audio_peak = 0
        max_population = 0
        for frame in range(600):
            # Later-night crawlers can breach fire. Circle the clearing while
            # measuring normal survival movement instead of idling to death.
            e.buttons = {(7, 4, 6, 5)[(frame // 70) % 4]}
            e.run(1)
            s = e.state()
            assert s['mode'] == 3, ('Fourth-night population caused an immediate checkpoint', s)
            max_population = max(max_population, len([x for x in s['enemies'] if x['hp']]))
            current = stamp()
            if current != previous:
                updates += 1
                max_gap = max(max_gap, (current-previous) & 65535)
                previous = current
        e.buttons = set()
        assert max_population == 4 and len(alive()) == 4
        assert e.audio_peak > 0, 'Fourth-night SPC output stopped'
        clock_after = e.state()
        logical_ticks = (clock_after['tick'] - clock_before['tick']) & 65535
        expected_ticks = 720 if pal else 600
        elapsed_seconds = (clock_after['day_seconds'] - clock_before['day_seconds']) % 768
        assert abs(logical_ticks - expected_ticks) <= 4, ('Survival clock slowed', logical_ticks, expected_ticks)
        assert abs(elapsed_seconds - (12 if pal else 10)) <= 1, ('World time slowed', elapsed_seconds)
        capture('surrounded')
        cadence = {'video_frames': 600, 'updates': updates, 'max_vblank_gap': max_gap,
                   'minimum_updates': 300, 'maximum_vblank_gap': 2,
                   'logical_ticks': logical_ticks, 'expected_logical_ticks': expected_ticks,
                   'world_elapsed_seconds': elapsed_seconds,
                   'max_population': max_population, 'audio_peak': e.audio_peak,
                   'fear_before': fear_before, 'fear_after': e.state()['fear']}
        diagnostic = {'rom_sha256': json.loads((ROOT / 'build/link_manifest.json').read_text())['rom_sha256'],
                      'region': region.upper(), 'cadence': cadence}
        (ROOT / 'build' / ('survival-cadence-' + region + '.json')).write_text(
            json.dumps(diagnostic, indent=2)+'\n')
        print(json.dumps(diagnostic), flush=True)

        # Releasing a valid Scope click must finish drawing and release an
        # arrow while later-night crawlers press through the fire.
        r.walk(128, 174)
        e.wait_state(lambda s: not s['shove_cooldown'], 'Shove recovery before enemy check')
        telegraph = e.wait_state(
            lambda s: any(x['hp'] and x['kind'] and x['state'] == 1 for x in s['enemies']),
            'Crawler never telegraphed an attack', limit=600)
        target_index = next(i for i, x in enumerate(telegraph['enemies'])
                            if x['hp'] and x['kind'] and x['state'] == 1)
        target = telegraph['enemies'][target_index]
        capture('crawler-windup')
        oam = C.string_at(e.memory + oam_address, 544)
        assert oam[(72+target_index)*4+1] != 240, 'Windup warning is absent from OAM'
        dx, dy = target['x']-telegraph['x'], target['y']-telegraph['y']
        facing = set()
        if abs(dx)*2 >= abs(dy) and dx:
            facing.add(7 if dx > 0 else 6)
        if abs(dy)*2 >= abs(dx) and dy:
            facing.add(5 if dy > 0 else 4)
        before_ammo = e.state()['ammo']
        e.buttons = facing | {11}
        e.wait_state(lambda s: s['shove_cooldown'] and
                     s['enemies'][target_index]['state'] == 3 and
                     s['enemies'][target_index]['hit'], 'R did not interrupt the crawler', limit=8)
        e.buttons = set()
        assert e.state()['ammo'] == before_ammo and e.state()['enemies'][target_index]['hp'] == target['hp']
        capture('crawler-interrupted')
        e.tap(10)
        start_kills = e.state()['kills']
        shots = interruptions = 0
        for _ in range(60):
            targets = alive()
            if not targets:
                break
            assert shots < 12, ('Too many missed arrows', e.state())
            e.wait_state(lambda s: not s['bow_cooldown'], 'Bow cooldown')
            visible = []
            for target in targets:
                sx, sy = r.screen_point(target['x'], target['y'])
                sy -= 8 if target['kind'] else 16
                if (0 <= sx < 256 and 0 <= sy < 224 and
                        (sx-106)**2 + (sy-145)**2 <= 75**2):
                    visible.append((target['kind'], sx, sy))
            if not visible:
                e.run(10)
                continue
            _, e.x, e.y = max(visible)
            before_ammo = e.state()['ammo']
            before_hurt = e.state()['hurt_timer']
            e.gun = {2}
            e.wait_state(lambda s: s['shot_request'] or s['bow_draw'] or s['hurt_timer'] > before_hurt,
                         'Fourth-night Scope draw')
            e.gun = set()
            # Every second kill can recover an arrow in the same tick, so a
            # point-blank shot need not lower the final ammo counter.
            outcome = e.wait_state(lambda s: s['bow_cooldown'] > 0 or
                                   (s['hurt_timer'] and not s['shot_request'] and not s['bow_draw']),
                                   'Fourth-night arrow or interrupted draw', limit=60)
            if not outcome['bow_cooldown']:
                interruptions += 1
                assert interruptions <= 8, ('Archer cannot recover from incoming attacks', outcome)
                assert outcome['ammo'] >= before_ammo, 'An interrupted draw spent an arrow'
                if not outcome['shove_cooldown']:
                    e.tap(11)
                e.run(12)
                continue
            shots += 1
            e.run(28)
            assert e.state()['mode'] == 3
        assert not alive() and e.state()['kills'] == start_kills+4, ('Four-creature battle did not finish', e.state())
        capture('cleared')
        report = {'region': region.upper(),
                  'rom_sha256': json.loads((ROOT / 'build/link_manifest.json').read_text())['rom_sha256'],
                  'checks': ['four successive dusks', 'safe chapel', 'repeated resource refill',
                             'four live actors', 'two tough crawlers', 'four OAM actors',
                             'night clipping', 'live audio', 'crawler telegraph OAM',
                             'R interrupts crawler without ammo or damage', 'four projectile kills'],
                  'dusks': dusks, 'refills': refills, 'frames': e.frames, 'shots': shots,
                  'interrupted_draws': interruptions,
                  'cadence': cadence, 'final_state': e.state()}
        (ROOT / 'build' / ('survival-regression-' + region + '.json')).write_text(
            json.dumps(report, indent=2)+'\n')
        print(json.dumps(report), flush=True)
        if not allow_cadence_drops:
            assert updates >= 300 and max_gap <= 2, ('Fourth-night cadence', cadence)
        print('PASS: four-night survival', region, flush=True)
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    parser.add_argument('--allow-cadence-drops', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal, args.allow_cadence_drops)
