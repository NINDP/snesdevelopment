#!/usr/bin/env python3
"""Play into the chapel and verify the room's textures, walls and exits in PPU.

Only controller input and read-only memory inspection; no state/RAM patches.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from libretro import Emulator, ROOT
from rom_smoke import Runner


def preview(shots, path):
    selected=(('exterior','Фасад часовни'),('entry','Вход'),('sanctuary','Поминальный стол'),
              ('west-wall','Бревенчатая стена'),('bell-rack','Три колокола'),('cellar-stairs','Спуск в подземелье'))
    font=ImageFont.truetype(next(str(p) for p in (
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/System/Library/Fonts/Supplemental/Arial.ttf')) if p.exists()),13)
    sheet=Image.new('RGB',(768,496),(12,17,15));draw=ImageDraw.Draw(sheet)
    for n,(name,label) in enumerate(selected):
        x=n%3*256;y=n//3*248
        draw.text((x+8,y+4),label,font=font,fill=(220,205,157));sheet.paste(shots[name],(x,y+24))
    sheet.save(path)


def run(core, pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    region='pal' if pal else 'ntsc';r.prefix='chapel-'+region+'-'
    shots=[];wall_checks=0
    source=(ROOT/'Data/content/perspective.c').read_text()
    ys=list(map(int,re.search(r'perspective_y\[241\] = \{([^}]+)',source)[1].split(',')))
    scales=list(map(int,re.search(r'perspective_size\[241\] = \{([^}]+)',source)[1].split(',')))
    vram=e.lib.retro_get_memory_data(3)
    def textures(prefix):
        for suffix,offset,size in (('',0xe800,6144),('-compact',0xdc00,1024)):
            name=prefix+suffix+'.chr'
            assert C.string_at(vram+offset,size)==(ROOT/'assets/generated'/name).read_bytes(),('Wrong chapel textures',name)
    def capture(name):
        r.capture(name);shots.append((name,e.frame.copy()))
    def walls():
        nonlocal wall_checks
        # Every visible column must survive the per-scanline admission budget.
        # Near columns are two large cells with an exact vertical seam.
        state=e.state();index=192-state['y'];sy=ys[index];expected=set()
        for n,x in enumerate(range(32,225,32)):
            sx=128+((x-state['x'])*scales[index]>>6)
            if not 18<=sx<=238:continue
            if sy>=126:
                tile=320 if n%2==0 else 324
                expected.add((sx-16,sy-64,tile,32))
                expected.add((sx-16,sy-32,tile+8,32))
            elif sy>=98:expected.add((sx-16,sy-32,392,32))
            else:expected.add((sx-8,sy-16,450,16))
        for _ in range(4):
            e.run(1);data=C.string_at(e.memory+e.symbols['oamMemory'],544)
            actual=set()
            for n in range(54):
                off=n*4;tile=data[off+2]+((data[off+3]&1)<<8)
                if data[off+1]==240 or ((data[off+3]>>1)&7)!=7:continue
                flags=data[512+n//4]>>((n%4)*2)
                actual.add((data[off]-(256 if flags&1 else 0),data[off+1],tile,32 if flags&2 else 16))
            if expected and expected<=actual:
                wall_checks+=len(expected)//(2 if sy>=126 else 1);return
        raise AssertionError(('Missing upright chapel walls',expected-actual,e.state()))
    try:
        e.run(190);e.tap(8);r.finish();r.light()
        r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
        r.inspect(0);r.inspect(1);r.choose(0)
        for index in (2,3,4):r.inspect(index)
        r.walk(220,112);textures('chapel-approach');capture('exterior')
        r.inspect(5)
        assert e.state()['room']==2 and e.state()['mode']==3
        def interior_textures():
            for name,offset,size in (('chapel-scenery.chr',0xe800,6144),('chapel-compact.chr',0xdc00,1024)):
                assert C.string_at(vram+offset,size)==(ROOT/'assets/generated'/name).read_bytes(),('Interior atlas missing',name)
            assert C.string_at(vram,32768)==(ROOT/'assets/generated/perspective2.vram').read_bytes(),'Chapel Mode 7 floor missing'
        interior_textures();r.lighting_roundtrip('entry');capture('entry')
        for name,x,y in (('aisle',128,120),('sanctuary',128,88),('west-wall',80,44),
                         ('east-wall',176,44),('bell-rack',172,162),('cellar-stairs',224,174)):
            r.walk(x,y);e.run(12);capture(name)
            if name in ('sanctuary','west-wall','east-wall'):walls()
        # Journal/paused Mode 1 screens must restore this room's atlas.
        for key,mode in ((1,6),(3,7)):
            e.tap(key);e.wait_mode(mode);e.tap(key);e.wait_mode(3);e.run(12)
            interior_textures();capture('resume-'+str(mode))
        r.inspect(0);r.inspect(1);r.inspect(5);r.inspect(6)
        r.bells()
        r.inspect(3);r.cups();r.inspect(4);r.choose(0)
        assert e.state()['room']==3
        textures('scenery');capture('cellar')
        r.inspect(7);assert e.state()['room']==2
        interior_textures();capture('return-from-cellar')
        r.inspect(8);assert e.state()['room']==1
        textures('chapel-approach');capture('return-to-forest')
        preview(dict(shots),ROOT/'build'/('chapel-'+region+'-preview.png'))
        report={'region':region.upper(),'rom_sha256':hashlib.sha256((ROOT/'chernorechye.sfc').read_bytes()).hexdigest(),
                'frames':e.frames,'wall_columns_checked':wall_checks,'screenshots':len(shots),
                'checks':['exterior atlas','Mode 7 floor','upright two-cell timber walls',
                          'room-specific atlas after journal/pause','torch darkness',
                          'residents, records, silver, bells and cups','cellar and forest round trips']}
        (ROOT/'build'/('chapel-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--pal',action='store_true');args=parser.parse_args()
    run(args.core,args.pal)
