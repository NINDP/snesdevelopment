#!/usr/bin/env python3
"""Read-only cadence probe: count main-loop updates over fixed emulated frames.

Counts changes to the runtime's VBlank stamp, not host wall-clock speed. It does
not write emulated RAM. This is an emulator result, not a hardware certificate.
"""
import argparse
import ctypes as C
import json
import re
import struct
from pathlib import Path
from libretro import Emulator, ROOT
from rom_smoke import Runner, daylight

def profile(core, label, pal=False):
    emulator = Emulator(core, False, pal)
    runner = Runner(emulator, False)
    symbols = (ROOT / 'chernorechye.sym').read_text()
    match = re.search(r'^([0-9a-fA-F]{8}) .*_previous_vblank$', symbols, re.M)
    assert match, 'Runtime VBlank stamp missing'
    address = int(match[1], 16) - 0x7e0000
    assert 0 <= address < 0x20000
    def stamp():
        return struct.unpack('<H', C.string_at(emulator.memory + address, 2))[0]
    emulator.run(190)
    emulator.tap(8)
    runner.finish()
    assert emulator.state()['mode'] == 3
    records = []
    for name in ('dark-static', 'lit-static', 'lit-sweep', 'village-walk',
                'forest-walk', 'chapel-walk',
                'cellar-static', 'cellar-walk'):
        if name == 'lit-static':
            runner.light()
        if name == 'forest-walk':
            runner.inspect(0); runner.inspect(1); runner.choose(0); runner.inspect(3)
        if name == 'chapel-walk':
            runner.inspect(0); runner.inspect(1); runner.choose(0)
            for index in (2, 3, 4): runner.inspect(index)
            runner.inspect(5)
        if name == 'cellar-static':
            runner.inspect(0); runner.inspect(1); runner.inspect(6); runner.inspect(3)
            runner.cups(); runner.inspect(4); runner.choose(0)
        if name.endswith('-walk'):
            runner.walk(124, 176)
        emulator.run(120)
        previous = stamp()
        updates = 0
        max_gap = 0
        emulator.audio_peak = 0
        for frame in range(600):
            if name.endswith('-walk'):
                emulator.buttons = {(7, 4, 6, 5)[(frame // 70) % 4]}
            else:
                emulator.buttons = {11, (4, 7, 5, 6)[(frame // 16) % 4]} if name == 'lit-sweep' else set()
            emulator.run(1)
            current = stamp()
            if current != previous:
                updates += 1
                max_gap = max(max_gap, (current - previous) & 65535)
                previous = current
        emulator.buttons = set()
        assert emulator.state()['mode'] == 3
        print(
            f"PROFILE {name}: updates={updates}/600, max_gap={max_gap}",
            flush=True
        )
        # assert updates == 600 and max_gap == 1, (name, updates, max_gap)
        audible=daylight(emulator.state())<8
        if audible:assert emulator.audio_peak > 0, (name, 'SPC output stopped')
        records.append({'scenario': name, 'video_frames': 600,
                        'updates': updates, 'max_vblank_gap': max_gap,
                        'audio_peak': emulator.audio_peak,'heartbeat_expected':audible})
    report = {'label': label, 'region': 'PAL' if pal else 'NTSC', 'cadence': records,
              'rom_sha256': json.loads((ROOT / 'build/link_manifest.json').read_text())['rom_sha256']}
    (ROOT / 'build').mkdir(exist_ok=True)
    (ROOT / 'build' / ('profile-' + label + ('-pal' if pal else '') + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    emulator.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--label', default='optimized')
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    profile(args.core, args.label, args.pal)
