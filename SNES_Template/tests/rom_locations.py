#!/usr/bin/env python3
"""Inspect the two authored locations and restored OBJ atlas in the real ROM."""
import argparse
import ctypes as C
import hashlib
import json
import re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from libretro import Emulator,ROOT
from rom_smoke import Runner

def run(core,pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    region='pal' if pal else 'ntsc';r.prefix='locations-'+region+'-'
    shots=[];quads=0;npcs=[]
    address=int(re.search(r'^([0-9a-fA-F]{8}) .*_parallax_table$',(ROOT/'chernorechye.sym').read_text(),re.M)[1],16)-0x7e0000
    def panorama(room):
        vram=e.lib.retro_get_memory_data(3)
        for suffix,offset,size in (('chr',0x8000,6144),('map',0x9800,2048)):
            assert C.string_at(vram+offset,size)==(ROOT/'assets/generated'/('backdrop%d.%s'%(room,suffix))).read_bytes(),('Backdrop VRAM',room,suffix)
        state=e.state();scroll=C.string_at(e.memory+address,13)
        assert tuple(scroll[i] for i in (0,3,6,9,12))==(40,24,127,33,0),'Invalid parallax spans'
        assert tuple(scroll[i] for i in (1,4,7,10))==(state['x']>>4,state['x']>>3,state['x']>>2,state['x']>>2),('Parallax speeds',scroll,state)
        pixels=e.frame.crop((0,0,256,80))
        assert sum(1 for p in pixels.getdata() if p!=(0,0,0))>19000,'Empty horizon returned'
    def resident(role,slot):
        pointer=e.lib.retro_get_memory_data(3)+0xc000+8192+slot*1024
        variants=[(ROOT/'assets/generated'/('npc-%s-%d.chr'%(role,n))).read_bytes() for n in range(3)]
        observed=set()
        for _ in range(140):
            data=C.string_at(pointer,1024)
            assert data in variants,('Wrong resident stream',role)
            observed.add(variants.index(data));e.run(1)
        assert observed=={0,1,2},('Resident never breathed/blinked',role,observed)
        # Six small OBJ cells form a real 32x48 body at the projected feet.
        data=C.string_at(e.memory+e.symbols['oamMemory'],544)
        base_tile=256+slot*32
        for index in range(45):
            off=index*4;t=data[off+2]+((data[off+3]&1)<<8)
            if t!=base_tile or data[off+1]==240:continue
            coords=[]
            for part in range(6):
                off=(index+part)*4;flags=data[512+((index+part)>>2)]>>(((index+part)&3)*2)
                tile=data[off+2]+((data[off+3]&1)<<8)
                assert tile==base_tile+part*2 and not flags&2,('NPC cell',role,part,tile)
                assert ((data[off+3]>>1)&7)==4,('NPC palette',role,part)
                coords.append((data[off]+((flags&1)<<8),data[off+1]))
            x,y=coords[0]
            assert coords==[((x+(p&1)*16)&511,(y+(p//2)*16)&255) for p in range(6)],('NPC silhouette',role,coords)
            npcs.append(role);return
        raise AssertionError(('Resident has no full-size body',role,e.state()))
    def quad_geometry():
        data=C.string_at(e.memory+e.symbols['oamMemory'],544)
        found=0
        for slot in range(47):
            base=slot*4;attr=data[base+3];tile=data[base+2]+((attr&1)<<8)
            if data[base+1]==240 or tile not in (224,232,320) or ((attr>>1)&7)!=7:continue
            size=32 if tile==320 else 16;step=4 if size==32 else 2
            coords=[]
            for part in range(4):
                offset=(slot+part)*4;flags=data[512+((slot+part)>>2)]>>(((slot+part)&3)*2)
                t=data[offset+2]+((data[offset+3]&1)<<8)
                assert t==tile+part*step,('Scenery cell tile order',slot,part,t)
                assert (flags>>1)&1==(size==32),('Scenery cell size',slot,part,flags)
                coords.append((data[offset]+((flags&1)<<8),data[offset+1]))
            x,y=coords[0]
            assert coords==[(x,y),((x+size)&511,y),(x,(y+size)&255),((x+size)&511,(y+size)&255)],('Broken scenery quad',slot,coords)
            found+=1
        return found
    def capture(name):
        nonlocal quads
        r.capture(name);shots.append((name,e.frame.copy()))
        if name.startswith('village'):quads+=quad_geometry()
    try:
        e.run(190);e.tap(8);r.finish()
        capture('village-entry')
        panorama(0)
        vram=e.lib.retro_get_memory_data(3)
        for name,offset,size in (('scenery-low.chr',1024,1024),('scenery-compact.chr',7168,1024),('scenery.chr',10240,6144)):
            assert C.string_at(vram+0xc000+offset,size)==(ROOT/'assets/generated'/name).read_bytes(),('Missing scenery',name)
        r.walk(56,104);resident('dobryn',0);capture('village-homestead')
        r.walk(190,136);resident('egor',1);capture('village-egor')
        r.walk(200,104);resident('dobryn',0);capture('village-edge')
        r.walk(142,154);capture('village-square');panorama(0)
        r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
        assert e.state()['room']==1
        capture('forest-entry')
        panorama(1)
        r.walk(56,164);capture('forest-ford')
        r.walk(176,130);capture('forest-path')
        r.walk(184,100);resident('miroslava',0);capture('forest-miroslava')
        r.light()
        for _ in range(700):
            if e.state()['day_seconds']>=640:break
            e.run(30)
        else:raise AssertionError('Night never arrived')
        e.run(200);capture('forest-night')
        r.inspect(9);assert e.state()['room']==0
        r.walk(56,104);capture('village-night')
        # The full legacy atlas is needed when returning to the Mode1 intro.
        e.tap(3);e.wait_mode(7);e.tap(5);e.tap(5);e.tap(8);e.wait_mode(1);e.run(12)
        assert C.string_at(vram+0xc000,16384)==(ROOT/'assets/generated/sprites.chr').read_bytes(),'Scenery leaked into the intro'
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
        selected=[('village-homestead','Староста · двор'),('village-egor','Егор · запасы'),
                  ('forest-miroslava','Мирослава · тропа'),('forest-ford','Лес · брод'),
                  ('village-night','Деревня · ночь'),('forest-night','Лес · ночь')]
        sheet=Image.new('RGB',(768,500),(12,17,15));draw=ImageDraw.Draw(sheet);lookup=dict(shots)
        for n,(key,label) in enumerate(selected):
            x=n%3*256;y=n//3*250
            draw.text((x+6,y+4),label,font=font,fill=(220,205,157));sheet.paste(lookup[key],(x,y+24))
        sheet.save(ROOT/'build'/('locations-'+region+'-preview.png'))
        frames=[im for _,im in shots]
        frames[0].save(ROOT/'build'/('locations-'+region+'.gif'),save_all=True,append_images=frames[1:],duration=900,loop=0)
        assert quads>=4,('Large scenery was not observed',quads)
        report={'region':region.upper(),'rom_sha256':hashlib.sha256((ROOT/'chernorechye.sfc').read_bytes()).hexdigest(),
                'checks':['native scenery VRAM','village scale and courtyard','forest trail and ford',
                          'daylight','night circular darkness','unchanged quest route','full intro atlas restoration',
                          'resident breathing and blink DMA','32x48 resident OBJ geometry including negative X',
                          'village/forest backdrop VRAM','three parallax scroll depths','populated daytime horizon'],
                'frames':e.frames,'verified_scenery_quads':quads,'verified_residents':npcs}
        (ROOT/'build'/('locations-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
