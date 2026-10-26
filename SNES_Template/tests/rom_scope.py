#!/usr/bin/env python3
"""Super Scope regressions through controller events, with read-only RAM probes."""
import argparse
import ctypes as C
import json
import re
from pathlib import Path

from libretro import Emulator, ROOT
from rom_smoke import Runner


def run(core, pal=False):
    e = Emulator(core, True, pal)
    r = Runner(e, True)
    symbols = (ROOT / 'chernorechye.sym').read_text()

    def byte(name):
        match = re.search(r'^([0-9a-fA-F]{8}) tccs_\S+_' + re.escape(name) + r'$', symbols, re.M)
        assert match, 'Missing runtime probe: ' + name
        address = int(match[1], 16) - 0x7e0000
        assert 0 <= address < 0x20000
        return C.string_at(e.memory + address, 1)[0]

    def held():
        match = re.search(r'^([0-9a-fA-F]{8}) tccs_\S+_held_scope$', symbols, re.M)
        assert match, 'Missing Scope switch probe'
        address = int(match[1], 16) - 0x7e0000
        return int.from_bytes(C.string_at(e.memory + address, 2), 'little')

    e.run(190)
    assert e.state()['mode'] == 1 and byte('calibration') == 0
    # Deliberately leave TURBO on while the very first off-centre shot is held.
    # It should show the target, never use that menu click as calibration data.
    if not held() & 0x2000:
        e.gun_tap(4)
    e.x, e.y = 200, 175
    e.gun = {2}
    e.run(30)
    assert held() & 0x2000
    assert byte('calibration') == 1 and byte('scope_ready') == 0
    e.gun = set()
    e.run(12)
    e.gun_tap(2, 128, 112)
    assert byte('calibration') == 2 and byte('scope_ready') == 0
    e.gun_tap(3, 128, 112)
    assert byte('calibration') == 0 and byte('scope_ready') == 1
    if held() & 0x2000:
        e.gun_tap(4)

    # Snes9x reports a changed TURBO position on the next FIRE.
    # Use an offscreen shot: it must update the switch without activating UI.
    e.x, e.y = 64, 88
    e.gun = {2, 15}
    e.run(12)
    e.gun = set()
    e.run(12)
    assert not held() & 0x2000
    assert e.state()['mode'] == 1
    r.action(64, 88)
    r.finish()
    assert e.state()['mode'] == 3
    r.light()

    # Set a destination beyond one gun tap, then use the switch without FIRE.
    # Waiting on idle input used to drop TURBO and resume the old destination.
    state = e.state()
    r.action(min(220, state['x'] + 36), state['y'])
    state = e.state()
    assert state['destination_x'] != state['x'], state
    destination = (state['destination_x'], state['destination_y'])
    e.gun = {4}
    e.run(1)
    e.gun = {2}
    e.run(12)
    e.gun = set()
    e.run(12)
    assert held() & 0x2000
    stopped = (e.state()['x'], e.state()['y'])
    e.run(60)
    assert (e.state()['x'], e.state()['y']) == stopped, 'TURBO lost on idle frames'
    e.gun = {4}
    e.run(1)
    e.gun = set()
    e.gun_tap(2, *r.screen_point(*destination))
    e.run(60)
    assert (e.state()['x'], e.state()['y']) != stopped, 'TURBO did not release movement'

    # Approach with the pad, then shoot the NPC's torso rather than its feet.
    pad = Runner(e, False)
    pad.walk(56, 100)
    sx, sy = r.screen_point(56, 78)
    serial = e.state()['interactions']
    e.gun_tap(2, sx, sy - 16)
    e.wait_mode(2)
    state = e.state()
    assert state['dialogue'] == 1 and state['last_hotspot'] == 0, state
    assert state['interactions'] == serial + 1
    e.run(120)
    page = e.state()['page']
    e.gun = {2, 15}
    e.run(12)
    e.gun = set()
    e.run(12)
    assert e.state()['page'] == page, 'Offscreen FIRE skipped dialogue'

    report = {
        'region': 'PAL' if pal else 'NTSC',
        'rom_sha256': json.loads((ROOT / 'build/link_manifest.json').read_text())['rom_sha256'],
        'checks': ['first-click calibration', 'held trigger release gate',
                   'offscreen menu shot', 'persistent TURBO switch',
                   'TURBO release', 'NPC torso hit', 'offscreen dialogue shot'],
        'frames': e.frames,
    }
    (ROOT / 'build' / ('scope-regression-' + ('pal' if pal else 'ntsc') + '.json')).write_text(
        json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), 'PASS')
    e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
