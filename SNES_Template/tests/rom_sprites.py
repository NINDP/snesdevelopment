#!/usr/bin/env python3
"""Read OAM during real input routes; every world scanline must fit SNES OBJ limits."""
import argparse
import ctypes as C
import json
import re
from libretro import Emulator, ROOT
from rom_smoke import Runner


def run(core, pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    symbols=(ROOT/'chernorechye.sym').read_text()
    address=int(re.search(r'^([0-9a-fA-F]{8}) oamMemory$',symbols,re.M)[1],16)-0x7e0000
    original=e.run
    checked=0;max_tiles=0;max_objects=0;shots=0
    def advance(n=1):
        nonlocal checked,max_tiles,max_objects,shots
        for _ in range(n):
            original(1)
            state=e.state()
            if state['mode']!=3:continue
            data=C.string_at(e.memory+address,544)
            counts=[0]*176;tiles=[0]*176
            for obj in range(128):
                x,y,_,_=data[obj*4:obj*4+4]
                high=(data[512+obj//4]>>((obj%4)*2))&3
                if high&1:x-=256
                size=32 if high&2 else 16
                if x>=256 or x+size<=0:continue
                for row in range(size):
                    sy=(y+row)&255
                    if sy<176:
                        counts[sy]+=1;tiles[sy]+=size//8
            assert max(counts)<=32,('OBJ range overflow',state,max(counts))
            assert max(tiles)<=34,('OBJ tile overflow',state,max(tiles))
            max_tiles=max(max_tiles,max(tiles));max_objects=max(max_objects,max(counts));checked+=1
            shots+=int(any(a['life'] for a in state['arrows']))
    e.run=advance
    try:
        e.run(190);e.tap(8);r.finish();r.light()
        for x,y in ((124,97),(72,110),(190,110),(124,145)):
            r.walk(x,y)
            for key in (4,7,5,6):
                e.buttons={11,key};e.run(4);e.buttons=set();e.run(40)
        r.walk(124,97);e.capture('sprites-budget-village.png')
        e.tap(10)
        for key in (4,7,5,6):
            e.buttons={8,key};e.run(38);e.buttons=set();e.run(24)
        e.tap(10)
        r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
        r.walk(170,120)
        e.run(1400)
        e.capture('sprites-budget-night.png')
        assert checked>1500 and shots>10,(checked,shots)
        report={'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'region':'PAL' if pal else 'NTSC','checked_world_frames':checked,
                'maximum_tiles_per_scanline':max_tiles,'maximum_objects_per_scanline':max_objects,
                'frames_with_arrows':shots}
        (ROOT/'build'/('sprite-budget-'+('pal' if pal else 'ntsc')+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',required=True,type=__import__('pathlib').Path);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
