#!/usr/bin/env python3
"""Visible houses keep their distance-based size through animation and UI exits."""
import argparse
import ctypes as C
import json
import re
from pathlib import Path
from libretro import Emulator, ROOT
from rom_smoke import Runner


def run(core,pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    source=(ROOT/'Data/content/perspective.c').read_text()
    ys=list(map(int,re.search(r'perspective_y\[241\] = \{([^}]+)',source)[1].split(',')))
    scales=list(map(int,re.search(r'perspective_size\[241\] = \{([^}]+)',source)[1].split(',')))
    symbols=(ROOT/'chernorechye.sym').read_text()
    addr=int(re.search(r'^([0-9a-fA-F]{8}) oamMemory$',symbols,re.M)[1],16)-0x7e0000
    slot_addr=int(re.search(r'^([0-9a-fA-F]{8}) torch_slot$',symbols,re.M)[1],16)-0x7e0000
    checks=0
    vram=e.lib.retro_get_memory_data(3)
    scenery=None
    def check():
        nonlocal checks
        s=e.state();expected=[]
        for x,y in ((196,68),(48,64),(120,40)):
            dy=y-s['y']
            if not -180<=dy<=38:continue
            sy=ys[dy+192];sx=128+((x-s['x'])*scales[dy+192]>>6)
            if not -32<=sx<=287:continue
            size=64 if sy>=130 else (32 if sy>=95 else 16)
            base={16:450,32:224,64:320}[size]
            for cell in range(1 if size==16 else 4):
                step=size//2
                expected.append((sx-size//2+(cell&1)*step,
                                 (sy-size+(cell>>1)*step)&255,
                                 base+cell*(size//16),int(size==64)))
        # OAM shadow can be mid-build at an arbitrary CPU sample. Demand a
        # complete result within four frames, rather than accepting a subset.
        for _ in range(4):
            e.run(1);data=C.string_at(e.memory+addr,544);actual=set()
            for n in range(54):
                x,y,t,a=data[n*4:n*4+4]
                if (data[512+n//4]>>((n%4)*2))&1:x-=256
                actual.add((x,y,t+((a&1)<<8),(data[512+n//4]>>((n%4)*2+1))&1))
            if all(item in actual for item in expected):break
        else:raise AssertionError(('House disappeared or shrank',s,expected,actual))
        assert C.string_at(vram+0xdc00,1024)+C.string_at(vram+0xe800,6144)==scenery, 'Animated effects corrupted scenery VRAM'
        torch_slot=int.from_bytes(C.string_at(e.memory+slot_addr,2),'little')
        hero_slots=[n for n in range(54) if data[n*4+2]==0 and data[n*4+3]==0x2a and data[n*4+1]==116]
        assert hero_slots and torch_slot==hero_slots[0]+6, 'Torch is outside its owner depth group'
        assert torch_slot+3<56, 'Torch overlaps the first enemy'
        checks+=1
    try:
        e.run(190);e.tap(8);r.finish();r.light();e.run(12)
        scenery=C.string_at(vram+0xdc00,1024)+C.string_at(vram+0xe800,6144)
        for y in (176,150,124,110,97,80,60):
            r.walk(124,y);e.run(12)
            for key in (4,7,5,6):
                e.buttons={11,key};e.run(3);e.buttons=set();e.run(12)
                for _ in range(8):check()
            for key,mode in ((1,6),(3,7)):
                e.tap(key);e.wait_mode(mode);e.tap(key);e.wait_mode(3);e.run(12);check()
            e.tap(10);e.run(12);check()
            e.buttons={8,4};e.run(30);e.buttons=set()
            for _ in range(24):check()
            e.tap(10);e.run(12);check()
            if y==110:e.capture('houses-fixed-'+('pal' if pal else 'ntsc')+'.png')
        report={'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'region':'PAL' if pal else 'NTSC','house_geometry_checks':checks,'missing_or_shrunken_houses':0,'torch_depth_checks':checks}
        (ROOT/'build'/('houses-regression-'+('pal' if pal else 'ntsc')+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
