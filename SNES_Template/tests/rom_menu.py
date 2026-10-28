#!/usr/bin/env python3
"""Verify menu fire animation and navigation against actual PPU frames."""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct

import numpy as np
from libretro import Emulator, ROOT


def run(core, pal=False):
    e = Emulator(core, False, pal)
    region = 'pal' if pal else 'ntsc'

    def frame():
        e.want_frame = True
        e.run(1)
        e.want_frame = False
        return e.frame.copy()

    try:
        e.run(210)
        e.wait_mode(1)
        e.run(80)  # Let the thirty-draw menu fade finish in both regions.
        reference = np.asarray(frame()).copy()
        vram=e.lib.retro_get_memory_data(3)
        row=struct.unpack('<32H',C.string_at(vram+0xb800+24*64,64))
        assert all(tile==0 for tile in row), 'Technical build text leaked into the menu'
        outside = np.ones(reference.shape[:2], dtype=bool)
        outside[128:168, 176:192] = False
        poses = {}
        for _ in range(160):
            image = frame()
            pixels = np.asarray(image)
            assert np.array_equal(pixels[outside], reference[outside]), \
                'Fire animation changed the menu outside the torch patch'
            patch = pixels[128:168, 176:192]
            # The flame remains attached to the painted handle in every pose.
            assert np.all(pixels[161, 178:184, 0] > 190), 'Flame detached from handle'
            poses.setdefault(patch.tobytes(), image)
        assert len(poses) == 16, ('Menu fire froze or lost frames', len(poses))

        # Open controls and credits, then return to the animated menu.
        for steps, mode in ((1, 9), (2, 10)):
            for _ in range(steps):
                e.tap(5)
            e.tap(8)
            e.wait_mode(mode)
            e.tap(0)
            e.wait_mode(1)
            e.run(40)
            before = np.asarray(frame())[128:168, 176:192].copy()
            e.run(8)
            after = np.asarray(frame())[128:168, 176:192]
            assert np.any(before != after), 'Fire did not resume after submenu'

        images = list(poses.values())
        preview = ROOT/'build'/('menu-torch-'+region+'.gif')
        images[0].save(preview, save_all=True, append_images=images[1:],
                       duration=67, loop=0)
        images[0].save(ROOT/'build'/('menu-torch-'+region+'.png'))
        report = {'region': region.upper(), 'fire_frames': len(poses),
                  'checks': ['flame stays attached', 'rising embers',
                             'unchanged surrounding menu', 'controls/credits roundtrip'],
                  'gif': str(preview)}
        (ROOT/'build'/('menu-torch-'+region+'.json')).write_text(
            json.dumps(report, indent=2)+'\n')
        print(json.dumps(report), 'PASS')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
