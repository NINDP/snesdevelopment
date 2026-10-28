#!/usr/bin/env python3
"""Repeated UI exits must preserve VRAM and finish PPU updates in VBlank."""
import argparse
import ctypes as C
import re
import struct
import sys
from pathlib import Path

import numpy as np

from libretro import Emulator, ROOT
from rom_smoke import Runner


def run(core, pal=False):
    e = Emulator(core, False, pal)
    r = Runner(e, False)
    region = 'pal' if pal else 'ntsc'
    symbols = (ROOT/'chernorechye.sym').read_text()
    late_address = int(re.search(r'^([0-9a-fA-F]{8}) video_late_commits$', symbols, re.M)[1], 16)-0x7e0000
    vram = e.lib.retro_get_memory_data(3)

    def clock():
        payload = C.string_at(vram + 0xb800 + 23*64 + 25*2, 10)
        return ''.join(chr(value & 255) for value in struct.unpack('<5H', payload))

    def capture(name):
        e.capture('hud-'+region+'-'+name+'.png')

    try:
        e.run(190); e.tap(8); r.finish(); e.run(20)
        original = C.string_at(vram, 0xa000)
        start_time = clock()
        assert re.fullmatch(r'\d\d:\d\d', start_time), ('Missing HUD clock', start_time)
        e.run(100)
        assert clock() != start_time, 'HUD clock did not advance'
        capture('explore')
        for repeat in range(12):
            for button, mode in ((1, 6), (3, 7)):
                e.tap(button); e.wait_mode(mode); e.run(12)
                before = e.state()['day_seconds']
                e.run(70)
                assert e.state()['day_seconds'] == before, 'World clock advanced behind UI'
                if repeat == 0 and mode == 6:
                    assert C.string_at(vram, (ROOT/'assets/generated/journal.chr').stat().st_size) == (ROOT/'assets/generated/journal.chr').read_bytes(), 'Journal artwork was replaced'
                    capture('journal')
                    e.tap(7); e.run(16)
                    assert e.state()['journal_page'] == 1, 'Full notes page did not open'
                    capture('notes')
                    e.tap(6); e.run(16)
                    assert e.state()['journal_page'] == 0, 'Overview page did not return'
                e.tap(button); e.wait_mode(3); e.run(12)
                assert C.string_at(vram, 0xa000) == original, ('UI exit corrupted world VRAM', repeat, mode)
        capture('after-24-exits')
        r.light(); e.tap(10); e.run(30)
        capture('bow')
        # Compare actual first and last glyph rows: the old mode boundary
        # erased the top of the status. BG3's -1 scroll places row 25 at y=199.
        e.want_frame = True; e.run(1); e.want_frame = False
        pixels = np.asarray(e.frame)
        entries = struct.unpack('<32H', C.string_at(vram + 0xb800 + 25*64, 64))
        sys.path.insert(0, str(ROOT/'tools'))
        from build_font import glyph_pixels
        expected = np.concatenate([np.asarray(glyph_pixels(bytes([entry & 255]).decode('cp1251'))).reshape(8,8) == 1
                                   if (entry & 1023) < 256 else np.zeros((8,8), dtype=bool)
                                   for entry in entries], axis=1)
        actual = pixels[199:207].max(axis=2) > 180
        assert np.array_equal(actual[:,8:248], expected[:,8:248]), 'Bow status glyphs clipped or displaced'
        e.buttons = {8}; e.run(36); e.buttons = set(); e.run(24)
        capture('shot')
        for button in (7, 5, 6, 4):
            e.buttons = {button}; e.run(90)
        e.buttons = set(); e.run(20)
        late = struct.unpack('<H', C.string_at(e.memory+late_address, 2))[0]
        assert late == 0, ('PPU update escaped VBlank', late)
        assert C.string_at(vram, 0xa000) == original, 'Walk or tooltip damaged world VRAM'
        print(region.upper(), 'PASS: live clock, 24 UI exits, intact VRAM, full glyphs, zero late PPU commits')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
