#!/usr/bin/env python3
"""Play the repair route and verify the secret epilogue without writing RAM."""
import argparse
import ctypes as C
import json
import struct
import textwrap
from pathlib import Path

from libretro import Emulator, ROOT
from rom_smoke import Runner


class StoryRunner(Runner):
    def __init__(self, emulator):
        super().__init__(emulator, False)
        self.observed = set()
        self.pages = json.loads((ROOT/'assets/story.json').read_text())['dialogues']
        self.ids = list(self.pages)

    def finish(self):
        for _ in range(100):
            state = self.e.state()
            if state['mode'] == 12:
                self.e.buttons = {7}
                self.e.wait_state(lambda s: s['mode'] != 12, 'Corridor exit', limit=600)
                self.e.buttons = set()
            state = self.e.state()
            if state['mode'] != 2:
                return
            name = self.ids[state['dialogue']]
            self.observed.add(name)
            if name in ('D_FINAL_WARNING', 'D_REPAIR', 'D_REMEMBER', 'D_MODERN'):
                label = 'story-'+name.lower()+'-'+('pal' if self.e.pal else 'ntsc')+'.png'
                if str(ROOT/'build'/label) not in self.shots:
                    if name == 'D_MODERN':
                        self.e.run(80)  # Wait for the cinematic fade.
                    current = self.e.state()
                    text = self.pages[name][current['page']]['text']
                    wrapped = '\n'.join(textwrap.wrap(text, 30, break_long_words=False,
                                                      break_on_hyphens=False))
                    if current['revealed'] < len(wrapped):
                        self.action()
                    self.shots.append(self.e.capture(label))
            self.action()
        raise AssertionError('Story dialogue stuck: '+str(self.e.state()))


def run(core, pal=False):
    e = Emulator(core, False, pal)
    r = StoryRunner(e)
    try:
        e.run(190); e.tap(8); r.finish(); r.light()
        r.inspect(0); r.inspect(1); r.choose(1); r.inspect(4); r.inspect(3)
        r.inspect(0); r.inspect(1); r.choose(1); r.inspect(7)
        for index in (2, 3, 4):
            r.inspect(index)
        r.inspect(5); r.inspect(0); r.inspect(1); r.inspect(5); r.inspect(6)
        r.inspect(3); r.cups(); r.inspect(4); r.choose(1)
        assert e.state()['evidence'] == 7 and e.state()['memories'] == 0
        e.tap(1); e.wait_mode(6)
        e.run(12)
        vram = e.lib.retro_get_memory_data(3)
        digit = struct.unpack('<H', C.string_at(vram+0xb800+26*64+12*2, 2))[0] & 1023
        assert digit == ord('3'), 'Written evidence counter missing from journal'
        e.tap(0); e.wait_mode(3)
        for index in range(3):
            r.rune(index)
        r.inspect(5)
        assert e.state()['dialogue'] == r.ids.index('D_FINAL_WARNING')
        before = e.state()['flags']
        e.tap(0); e.wait_mode(3)
        assert e.state()['flags'] == before, 'Cancelling a choice changed the bargain'
        r.inspect(5); r.choose(0)
        assert e.state()['mode'] == 3 and not (e.state()['flags'] & 16384)
        assert 'D_REPAIR' in r.observed, 'Failed seal did not offer repair'
        r.inspect(7); r.inspect(8); r.inspect(9)
        r.inspect(1); r.choose(0)
        r.inspect(3); r.inspect(1); r.choose(0)
        r.inspect(5); r.inspect(4); r.inspect(0); r.choose(0)
        assert e.state()['flags'] & (4 | 16 | 4096) == (4 | 16 | 4096)
        assert e.state()['rune_mask'] == 7, 'Repair discarded the sealed nodes'
        assert e.state()['memories'] == 0, 'Optional echoes were accidentally required'
        r.inspect(5)
        assert e.state()['dialogue'] == r.ids.index('D_REMEMBER')
        r.choose(0)
        assert e.state()['mode'] == 8 and e.state()['ending'] == 2
        assert {'D_MIRO_RETRY', 'D_MIRO_RELEASE', 'D_MODERN'} <= r.observed
        assert not {'D_END_STAY', 'D_END_LOST'} & r.observed
        region = 'pal' if pal else 'ntsc'
        report = {'region': region.upper(), 'frames': e.frames,
                  'rom_sha256': json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                  'checks': ['three real written witnesses', 'separate evidence counter',
                             'cancel final choice', 'failed seal preserves village',
                             'repair all three early choices', 'keep node progress',
                             'secret ending without echoes or bells', 'NovGU epilogue'],
                  'dialogues': sorted(r.observed), 'screenshots': r.shots}
        (ROOT/'build'/('story-regression-'+region+'.json')).write_text(
            json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'dialogues'}), 'PASS')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
