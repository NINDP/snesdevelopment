#!/usr/bin/env python3
"""Check the torch-to-logo reveal and its transition using actual PPU frames."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from libretro import Emulator, ROOT


def run(core, pal=False):
    e = Emulator(core, False, pal)
    region = 'pal' if pal else 'ntsc'
    samples = {}
    animation = []
    try:
        e.want_frame = True
        for _ in range(260):
            e.run(1)
            state = e.state()
            if state['mode'] == 1:
                break
            if state['mode'] == 0 and e.frame is not None:
                tick = state['tick']
                samples[tick] = np.asarray(e.frame).copy()
                animation.append(e.frame.copy())
        assert e.state()['mode'] == 1, 'Splash never reached the menu'

        def at(tick):
            return samples[min(samples, key=lambda value: abs(value-tick))]

        def bright(pixels):
            return (pixels.max(axis=2) > 150).sum()

        assert at(80).mean() > at(5).mean()+5, 'Fade-in failed'
        assert at(100).mean() > at(148).mean()+5, 'Fade-out failed'
        assert bright(at(65)[52:120, 88:169]) > \
               bright(at(32)[52:120, 88:169])+40, 'Logo did not grow from sparks'
        assert bright(at(50)[128:135, 80:177]) == 0, 'Caption appeared too early'
        assert bright(at(100)[128:135, 80:177]) > 80, 'Studio caption missing'
        assert bright(at(100)[152:159, 80:177]) > 50, 'Presents caption missing'
        outside = np.ones(at(40).shape[:2], dtype=bool)
        outside[34:198, 54:203] = False
        for tick in (45, 60, 75, 90, 110):
            assert np.array_equal(at(40)[outside], at(tick)[outside]), \
                'Reveal moved the surrounding landscape'
        poses = {at(tick)[175:191, 122:135].tobytes() for tick in range(35, 115)}
        assert len(poses) >= 3, 'Torch stopped flickering'
        # Lettering and both edges share the same center, to within one pixel.
        for y in (128, 152):
            columns = 80 + np.where((at(110)[y:y+7, 80:177].max(axis=2) > 150).any(axis=0))[0]
            assert abs(int(columns.min())+int(columns.max())-256) <= 1

        preview = ROOT/'build'/('nabla-animation-'+region+'.gif')
        frames = [im.resize((512, 448), Image.Resampling.NEAREST) for im in animation]
        frames[0].save(preview, save_all=True, append_images=frames[1:],
                       duration=20 if pal else 17, loop=0)
        Image.fromarray(at(110)).save(ROOT/'build'/('nabla-animation-'+region+'.png'))
        print(region.upper(), 'PASS: reveal, captions, alignment, flicker, fade, menu;', preview)
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
