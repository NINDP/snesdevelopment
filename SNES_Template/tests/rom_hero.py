#!/usr/bin/env python3
"""Verify Vsevolod's real ROM animation through controller input only.

Frame identities are read-only probes. The actual 1 KiB OBJ VRAM payload,
not the frame variable alone, must change for every pose. Screenshots and
the GIF come from the emulator's PPU output; no game RAM is modified.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

from libretro import Emulator, ROOT
from rom_smoke import Runner


FACES = (
    ('back', 0, 4, (128, 174)),
    ('right', 1, 7, (24, 174)),
    ('front', 2, 5, (128, 44)),
    ('left', 3, 6, (232, 174)),
)
HERO_BOX = (112, 116, 144, 164)
# This part of the head is clear of the animated flame and remains inside
# the fully lit centre, so an idle pixel change cannot be torch flicker.
HEAD_BOX = (120, 118, 136, 132)


def run(core, pal=False):
    e = Emulator(core, False, pal)
    r = Runner(e, False)
    region = 'pal' if pal else 'ntsc'
    prefix = 'hero-runtime-' + region + '-'
    output = ROOT / 'build'
    output.mkdir(exist_ok=True)
    symbols = (ROOT / 'chernorechye.sym').read_text()
    match = re.search(r'^([0-9a-fA-F]{8}) tccs_\S+_selected_frame$', symbols, re.M)
    assert match, 'Hero animation frame probe is missing'
    frame_address = int(match[1], 16) - 0x7e0000
    assert 0 <= frame_address < 0x20000, 'Hero frame probe is not in WRAM'
    vram = e.lib.retro_get_memory_data(3)
    assert vram, 'Core does not expose video RAM for the read-only probe'

    def frame_id():
        return C.string_at(e.memory + frame_address, 1)[0]

    def vram_hash():
        return hashlib.sha256(C.string_at(vram + 0xc000, 1024)).hexdigest()

    def step(buttons):
        e.buttons = set(buttons)
        e.want_frame = True
        e.run(1)
        e.want_frame = False
        assert e.frame is not None
        assert e.state()['mode'] == 3, e.state()
        return frame_id(), vram_hash(), e.frame.copy()

    def position():
        state = e.state()
        return state['x'], state['y']

    def turn(key, facing):
        stopped = position()
        old = vram_hash()
        e.buttons = {11, key}  # R holds position while the arrow changes facing.
        e.wait_state(lambda state: state['direction'] == facing * 2,
                     'Stationary facing change', limit=90)
        e.run(8)
        e.buttons = set()
        e.run(8)
        assert position() == stopped, ('Turning moved the hero', stopped, e.state())
        assert frame_id() // 8 == facing, ('Facing did not reach OBJ VRAM', e.state(), frame_id())
        return old, vram_hash()

    records = []
    walking_images = []
    contact = Image.new('RGB', (32 * 6, 48 * 4), (0, 0, 0))
    idle_heads = []
    try:
        e.run(190)
        e.tap(8)
        r.finish()
        e.wait_mode(3)
        r.light()

        for row, (name, facing, key, start) in enumerate(FACES):
            r.walk(*start)
            e.run(12)
            stopped = position()
            old_hash, turned_hash = turn(key, facing)
            # Runner.walk leaves the hero facing back; force a distinct prior
            # facing for that one case so the turn assertion is meaningful.
            if facing == 0:
                turn(7, 1)
                old_hash, turned_hash = turn(key, facing)
            assert turned_hash != old_hash, ('Idle turn did not update VRAM', name)
            assert position() == stopped

            idle = {}
            previous = None
            for _ in range(82):
                selected, payload_hash, image = step(set())
                assert selected in (facing * 8, facing * 8 + 1), (name, selected)
                if selected == previous:
                    if selected in idle:
                        assert idle[selected]['vram_sha256'] == payload_hash, (
                            'One idle frame has unstable VRAM', name, selected)
                    else:
                        path = output / (prefix + name + '-idle-' + str(selected % 8) + '.png')
                        image.save(path)
                        idle[selected] = {'vram_sha256': payload_hash,
                                          'head_sha256': hashlib.sha256(image.crop(HEAD_BOX).tobytes()).hexdigest(),
                                          'screenshot': str(path)}
                previous = selected
            assert position() == stopped, ('Idle animation moved the hero', name)
            assert len(idle) == 2, ('Missing idle pose', name, sorted(idle))
            assert len({record['vram_sha256'] for record in idle.values()}) == 2, (
                'Idle frame selector changes but OBJ data does not', name)
            assert len({record['head_sha256'] for record in idle.values()}) == 2, (
                'Idle animation is not visible in the PPU head pixels', name)
            idle_heads.append(idle[facing * 8]['head_sha256'])

            walking = {}
            previous = None
            start_position = position()
            # Six gait poses hold for six logical ticks each. Fifty-four video
            # frames cover the full cycle in both regions and stay inside the
            # walkable village corridor for the start positions above.
            for _ in range(54):
                selected, payload_hash, image = step({key})
                local_frame = selected - facing * 8
                if 2 <= local_frame < 8 and selected == previous:
                    if selected in walking:
                        assert walking[selected]['vram_sha256'] == payload_hash, (
                            'One gait frame has unstable VRAM', name, selected)
                    else:
                        path = output / (prefix + name + '-walk-' + str(local_frame - 2) + '.png')
                        image.save(path)
                        walking[selected] = {'vram_sha256': payload_hash, 'screenshot': str(path)}
                        walking_images.append(image)
                        contact.paste(image.crop(HERO_BOX), ((local_frame - 2) * 32, row * 48))
                previous = selected
            e.buttons = set()
            e.run(12)
            assert position() != start_position, ('Walking did not move the hero', name)
            assert len(walking) == 6, ('Missing walking pose', name, sorted(walking))
            assert len({record['vram_sha256'] for record in walking.values()}) == 6, (
                'Walking selector changes but OBJ payloads repeat', name)
            records.append({'facing': name, 'idle': idle, 'walking': walking,
                            'stationary_turn_updates_vram': True})

        assert len(set(idle_heads)) == 4, 'The four facings do not look distinct in PPU output'
        e.tap(3)
        e.wait_mode(7)
        e.run(12)
        frozen_tick = e.state()['tick']
        frozen_frame = frame_id()
        frozen_hash = vram_hash()
        for _ in range(120):
            e.run(1)
            assert e.state()['tick'] == frozen_tick, 'Pause advanced the animation clock'
            assert frame_id() == frozen_frame, 'Pause advanced the selected hero frame'
            assert vram_hash() == frozen_hash, 'Hero OBJ data changed while paused'
        r.capture(prefix + 'pause')
        e.tap(3)
        e.wait_mode(3)
        e.run(12)
        assert frame_id() < 32

        gif = output / ('hero-walk-' + region + '.gif')
        walking_images[0].save(gif, save_all=True, append_images=walking_images[1:],
                               duration=100, loop=0, optimize=False)
        contact.resize((768, 768), Image.Resampling.NEAREST).save(
            output / (prefix + 'walk-sheet.png'))
        report = {
            'rom_sha256': json.loads((output / 'link_manifest.json').read_text())['rom_sha256'],
            'region': 'PAL' if pal else 'NTSC',
            'frames': e.frames,
            'facings': records,
            'checks': ['four visible facings', 'six distinct walking VRAM payloads per facing',
                       'two visible idle poses per facing', 'stationary facing changes',
                       'paused clock/frame/OBJ VRAM remain stable'],
            'walk_gif': str(gif),
        }
        (output / ('hero-regression-' + region + '.json')).write_text(
            json.dumps(report, indent=2) + '\n')
        print(json.dumps({'region': report['region'], 'frames': e.frames,
                          'facings': 4, 'walking_poses': 24, 'idle_poses': 8,
                          'paused_vram_stable': True, 'rom_sha256': report['rom_sha256']}), 'PASS')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
