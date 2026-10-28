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
        self.content = json.loads((ROOT/'assets/story.json').read_text())
        self.pages = self.content['dialogues']
        self.ids = list(self.pages)

    def assert_map_text(self, value, x, y):
        vram = self.e.lib.retro_get_memory_data(3)
        for row, line in enumerate(value.split('\n')):
            raw = C.string_at(vram+0xb800+(y+row)*64+x*2, len(line)*2)
            tiles = struct.unpack('<'+'H'*len(line), raw)
            expected = list(line.encode('cp1251'))
            # text_box leaves spaces as the panel's blank tile; dialogue text
            # emits the font's space tile. Both display the same whitespace.
            actual = [32 if char == 32 and (tile & 1023) in (0, 256) else tile & 1023
                      for tile, char in zip(tiles, expected)]
            assert actual == expected, \
                ('Displayed story differs from the source', self.e.state()['dialogue'], row)

    def memory_journal(self, key, label):
        self.e.tap(1); self.e.wait_mode(6)
        filename = 'story-journal-'+label+'-'+('pal' if self.e.pal else 'ntsc')+'.png'
        self.shots.append(self.e.capture(filename))
        self.assert_map_text(self.content['ui'][key], 1, 13)
        self.e.tap(0); self.e.wait_mode(3)

    def finish(self):
        for _ in range(100):
            state = self.e.state()
            if state['mode'] == 13:
                self.ambush()
                continue
            if state['mode'] == 12:
                self.e.buttons = {7}
                self.e.wait_state(lambda s: s['mode'] != 12, 'Corridor exit', limit=600)
                self.e.buttons = set()
            state = self.e.state()
            if state['mode'] != 2:
                return
            name = self.ids[state['dialogue']]
            self.observed.add(name)
            if name != 'D_RETRY':
                label = 'story-'+name.lower()+'-'+str(state['page']+1)+'-'+('pal' if self.e.pal else 'ntsc')+'.png'
                if str(ROOT/'build'/label) not in self.shots:
                    if name in ('D_MODERN', 'D_PROLOG'):
                        self.e.run(80)  # Wait for the cinematic fade.
                    current = self.e.state()
                    text = self.pages[name][current['page']]['text']
                    wrapped = '\n'.join(textwrap.wrap(text, 30, break_long_words=False,
                                                      break_on_hyphens=False))
                    if current['revealed'] < len(wrapped):
                        self.action()
                    self.shots.append(self.e.capture(label))
                    # Compare the displayed text, not merely a dialogue ID or
                    # the generated source, so a stale ROM cannot pass this check.
                    speaker = self.pages[name][current['page']]['speaker']
                    self.assert_map_text(speaker, 1, 17)
                    self.assert_map_text(wrapped, 1, 19)
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
        digit = struct.unpack('<H', C.string_at(vram+0xb800+19*64+16*2, 2))[0] & 1023
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
        r.inspect(0)
        assert e.state()['dialogue'] == r.ids.index('D_HEAD_RETURN')
        r.inspect(3); r.inspect(1); r.choose(0)
        r.inspect(5); r.inspect(4); r.inspect(0); r.choose(0)
        assert e.state()['flags'] & (4 | 16 | 4096) == (4 | 16 | 4096)
        assert e.state()['rune_mask'] == 7, 'Repair discarded the sealed nodes'
        assert e.state()['memories'] == 0, 'Optional echoes were accidentally required'
        assert not (e.state()['flags'] & 32768), 'Records restored memory before the conversation'
        r.memory_journal('J_REMEMBER', 'before-memory')
        r.inspect(5)
        assert e.state()['dialogue'] == r.ids.index('D_REMEMBER')
        assert e.state()['flags'] & 32768, 'Full memory was not recorded'
        e.capture('story-final-price-'+('pal' if pal else 'ntsc')+'.png')
        r.assert_map_text(r.content['choices'][3][1], 2, 19)
        e.tap(0); e.wait_mode(3)
        r.memory_journal('J_READY', 'after-memory')
        r.inspect(5)
        assert e.state()['dialogue'] == r.ids.index('D_FINAL_READY'), 'Memory restoration repeated after cancellation'
        r.choose(0)
        assert e.state()['mode'] == 8 and e.state()['ending'] == 2
        assert {'D_MIRO_RETRY', 'D_MIRO_RELEASE', 'D_MODERN'} <= r.observed
        assert not {'D_END_STAY', 'D_END_LOST'} & r.observed
        region = 'pal' if pal else 'ntsc'
        report = {'region': region.upper(), 'frames': e.frames,
                  'rom_sha256': json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                  'checks': ['Dobrynya opening and first conversation match the displayed text',
                             'three real written witnesses', 'separate evidence counter',
                             'cancel final choice', 'failed seal preserves village',
                             'repair all three early choices', 'keep node progress',
                             'return conversation preserves Egor decision',
                             'memory recorded only after restoration scene',
                             'memory preserved after cancelling final choice',
                             'explicit personal price of the bargain',
                             'secret ending without optional echoes or bells', 'NovGU epilogue'],
                  'dialogues': sorted(r.observed), 'screenshots': r.shots}
        (ROOT/'build'/('story-regression-'+region+'.json')).write_text(
            json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        summary = {k: v for k, v in report.items() if k not in ('dialogues', 'screenshots')}
        summary['screenshots'] = len(r.shots)
        print(json.dumps(summary), 'PASS')
    finally:
        e.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--pal', action='store_true')
    args = parser.parse_args()
    run(args.core, args.pal)
