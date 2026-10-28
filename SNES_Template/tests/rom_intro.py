#!/usr/bin/env python3
"""Play the introduction; verify large actor streaming and the live village handoff."""
import argparse
import ctypes as C
import re
from pathlib import Path
from libretro import Emulator, ROOT


def run(core,pal=False):
    e=Emulator(core,False,pal)
    symbols=(ROOT/'chernorechye.sym').read_text()
    address=int(re.search(r'^([0-9a-fA-F]{8}) oamMemory$',symbols,re.M)[1],16)-0x7e0000
    vram=e.lib.retro_get_memory_data(3)
    prefix='intro-'+('pal' if pal else 'ntsc')+'-'
    def advance():e.tap(8);e.run(12)
    try:
        e.run(190);e.tap(8);e.run(12)
        # The SDK uploads only complete non-lag frames; inspect after the draw.
        for _ in range(8):
            e.run(1)
            data=C.string_at(e.memory+address,24)
            if data[1]!=240:break
        assert [data[i*4+2] for i in range(6)]==[0,2,4,6,8,10]
        assert data[17]-data[1]==32,'Kirill does not span three 16px rows'
        assert C.string_at(vram+0xc000,1024) in [(ROOT/('assets/generated/intro-actor-%d.chr'%n)).read_bytes() for n in range(8)]
        e.capture(prefix+'gym.png')
        while e.state()['mode']==2:advance()
        assert e.state()['mode']==12
        e.buttons={7};e.wait_state(lambda s:s['x']>=400,'Running corridor',limit=600)
        e.capture(prefix+'corridor.png')
        e.wait_state(lambda s:s['x']>=478,'Descending stairs',limit=600)
        assert e.state()['mode']==12 and e.state()['y']<110,e.state()
        e.buttons=set();e.run(12);e.capture(prefix+'stairs.png');e.buttons={7}
        e.wait_state(lambda s:s['mode']==2,'Basement dialogue');e.buttons=set();e.run(12)
        while e.state()['mode']==2 and e.state()['page']<3:advance()
        assert e.state()['mode']==2 and e.state()['page']==3
        e.run(16);e.capture(prefix+'village.png')
        # This is the actual Mode7 map and scenery, not the old painted mockup.
        assert C.string_at(vram,0x8000)==(ROOT/'assets/generated/perspective0.vram').read_bytes()
        print(prefix,'PASS: 48px actor, resident poses, descending stairs, live Mode7 village')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
