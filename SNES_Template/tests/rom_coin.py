#!/usr/bin/env python3
"""Record the actual coin chase and check motion/rolling/scene continuity."""
import argparse,ctypes as C,json,re
from pathlib import Path
from libretro import Emulator,ROOT


def run(core,pal=False):
    e=Emulator(core,False,pal);region='pal' if pal else 'ntsc'
    symbols=(ROOT/'chernorechye.sym').read_text();address=int(re.search(r'^([0-9a-fA-F]{8}) oamMemory$',symbols,re.M)[1],16)-0x7e0000
    frames=[];coins=set();positions=[];poses=set();vram=e.lib.retro_get_memory_data(3)
    def shot():
        e.want_frame=True;e.run(1);e.want_frame=False
        frames.append(e.frame.copy())
    try:
        e.run(190);e.buttons={8};e.wait_mode(2);e.buttons=set()
        for _ in range(160):
            shot();state=e.state();data=C.string_at(e.memory+address+32,4)
            if data[1]==240:continue # incomplete CPU-side draw, not published OAM
            x,y,tile,_=data;coins.add(tile)
            scroll=max(0,min(256,state['x']-112))
            positions.append((state['x'],x+8+scroll))
            assert x+8>min(112,state['x'])+20,'Coin is not leading Kirill'
            assert 93<=y<=95,'Coin is not rolling along the floor'
            poses.add(C.string_at(vram+0xc000,1024))
        assert len(coins)==4 and len(poses)>=6,(coins,len(poses))
        assert max(x for x,_ in positions)-min(x for x,_ in positions)>80
        assert max(x for _,x in positions)-min(x for _,x in positions)>60
        e.wait_state(lambda s:s['tick']>=132,'Opening chase completion')
        before=e.state()['x']
        for _ in range(4):
            if e.state()['mode']==12:break
            e.tap(8)
        assert e.state()['mode']==12 and e.state()['x']==before,'Scene change teleported Kirill'
        e.buttons={7}
        for _ in range(110):shot()
        e.buttons=set()
        frames[0].save(ROOT/'build'/('coin-chase-'+region+'.gif'),save_all=True,append_images=frames[1::2],duration=40,loop=0)
        report={'region':region,'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'rolling_frames':len(coins),'actor_poses':len(poses),'continuous_transition':True}
        (ROOT/'build'/('coin-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',required=True,type=Path);p.add_argument('--pal',action='store_true');a=p.parse_args();run(a.core,a.pal)
