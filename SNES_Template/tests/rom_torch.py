#!/usr/bin/env python3
"""Check held torch, particle motion and darkness through controller input."""
import argparse
import ctypes as C
import json
import re
from pathlib import Path

import numpy as np
from libretro import Emulator, ROOT
from rom_smoke import Runner, TORCH_CENTERS


def run(core, pal=False):
    e=Emulator(core,False,pal)
    r=Runner(e,False)
    region='pal' if pal else 'ntsc'
    symbols=(ROOT/'chernorechye.sym').read_text()
    match=re.search(r'^([0-9a-fA-F]{8}) oamMemory$',symbols,re.M)
    assert match,'OAM shadow probe missing'
    address=int(match[1],16)-0x7e0000
    assert 0<=address<0x20000-544
    vram=e.lib.retro_get_memory_data(3)
    assert vram
    slot_address=int(re.search(r'^([0-9a-fA-F]{8}) torch_slot$',symbols,re.M)[1],16)-0x7e0000
    def oam():
        slot=int.from_bytes(C.string_at(e.memory+slot_address,2),'little')
        return C.string_at(e.memory+address+slot*4,16)
    def frame():
        e.want_frame=True;e.run(1);e.want_frame=False
        assert e.frame is not None
        return e.frame.copy()
    images=[];records=[]
    try:
        e.run(190);e.tap(8);r.finish();r.light()
        # The boarded chapel is dark at every hour; keep this strict darkness
        # and skin-palette regression independent of the outdoor solar cycle.
        r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
        r.inspect(0);r.inspect(1);r.choose(0)
        for index in (2,3,4):r.inspect(index)
        r.inspect(5)
        assert e.state()['room']==2
        for facing,key in enumerate((4,7,5,6)):
            e.buttons={11,key}
            e.wait_state(lambda s:s['direction']==facing*2,'Torch facing')
            e.run(12);e.buttons=set();e.run(12)
            stopped=(e.state()['x'],e.state()['y'])
            cx,cy=TORCH_CENTERS[facing]
            poses=set();trails=set();skin_frames=0
            for tick in range(40):
                image=frame();data=oam()
                resident=b"".join(C.string_at(vram+0xcc00+row*512,64) for row in range(8))
                atlas=(ROOT/"assets/generated/torch.chr").read_bytes()
                assert resident in [atlas[i*512:(i+1)*512] for i in range(8)]
                poses.add(resident)
                for cell in range(4):
                    tx,ty,tile,attr=data[cell*4:cell*4+4]
                    assert (tx+8,ty+40-cell*16)==(cx,cy),(facing,data)
                    assert tile==96+cell*32 and attr==0x2c
                pixels=np.asarray(image)
                hand=pixels[cy+16:cy+19,cx-1:cx+2].astype(np.int16)
                # Skin from the hero's palette is distinct from wood/flame.
                if np.any(np.max(np.abs(hand-np.array([172,114,74])),axis=2)<=5):
                    skin_frames+=1
                sparks=pixels[max(0,cy-40):cy-17,cx-12:cx+13]
                warm=(sparks[:,:,0]>100)&(sparks[:,:,0]>sparks[:,:,1]*1.25)&(sparks[:,:,1]>20)
                trails.add(warm.tobytes())
                r.check_darkness('torch-'+str(facing),e.state())
                if tick%4==0:images.append(image)
            assert (e.state()['x'],e.state()['y'])==stopped
            assert len(poses)==8,('Particles repeat or freeze',facing,len(poses))
            assert len(trails)>=6,('Rising sparks missing from PPU',facing,len(trails))
            assert skin_frames>=35,('Torch does not meet the hand',facing,skin_frames)
            records.append({'facing':facing,'streamed_poses':len(poses),
                            'visible_spark_states':len(trails),'hand_frames':skin_frames})
        e.tap(3);e.wait_mode(7);e.run(12)
        stopped_oam=oam();clock=e.state()['tick']
        e.run(90)
        assert oam()==stopped_oam and e.state()['tick']==clock,'Paused fire keeps animating'
        e.tap(3);e.wait_mode(3);e.tap(9);e.run(12)
        frame();r.check_darkness('torch-off',e.state())
        assert all(oam()[offset]==240 for offset in range(1,16,4)),'Unlit particles remain in OAM'
        e.tap(3);e.wait_mode(7)
        e.tap(5);e.tap(5);e.tap(8);e.wait_mode(1);e.run(12)
        atlas=(ROOT/'assets/generated/sprites.chr').read_bytes()
        assert C.string_at(vram+0xc000,1024)==atlas[:1024],'Hero overwrote the next prologue'
        assert C.string_at(vram+0xc000+3072,4096)==atlas[3072:7168],'Torch overwrote Kirill/legacy sprites'
        path=ROOT/'build'/('torch-runtime-'+region+'.gif')
        images[0].save(path,save_all=True,append_images=images[1:],duration=90,loop=0)
        report={'region':region.upper(),'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'checks':['four hand anchors','joined torch cells','rising/fading sparks',
                          'black outside moving light','frozen paused particles','hidden unlit particles',
                          'legacy graphics restored after returning to menu'],
                'facings':records,'gif':str(path)}
        (ROOT/'build'/('torch-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--pal',action='store_true')
    args=parser.parse_args();run(args.core,args.pal)
