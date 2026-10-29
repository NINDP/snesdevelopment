#!/usr/bin/env python3
"""Play the real Mode 7 clearing with optical Scope packets, without RAM edits."""
import argparse
import ctypes as C
import json
import re
from pathlib import Path
import numpy as np
from libretro import Emulator, ROOT
from rom_smoke import Runner

class ManualRunner(Runner):
    def ambush(self):
        pass

def enter(e):
    r=ManualRunner(e,True)
    e.run(190)
    e.tap(2);e.gun_tap(2,128,112);e.gun_tap(3,128,112)
    r.action(64,88);r.finish();r.light()
    r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
    r.inspect(0);r.inspect(1);r.choose(0)
    for index in (2,3,4):r.inspect(index)
    r.inspect(5)
    assert e.state()['mode']==13 and e.state()['room']==1
    return r

def run(core,pal=False):
    e=Emulator(core,True,pal);region='pal' if pal else 'ntsc'
    images=[]
    clip=[];recording=False
    run_frames=e.run
    def recorded_run(n=1):
        for _ in range(n):
            capture=recording and e.frames%4==0
            if capture:e.want_frame=True
            run_frames(1)
            if capture:
                clip.append(e.frame.copy())
                e.want_frame=False
    e.run=recorded_run
    def frame(name=None):
        e.want_frame=True;e.run(1);e.want_frame=False
        image=e.frame.copy();images.append(image)
        if name:image.save(ROOT/'build'/('ambush-'+region+'-'+name+'.png'))
        return np.asarray(image)
    try:
        r=enter(e)
        frame('intro')
        before=e.state()
        e.wait_state(lambda s:s['ambush_timer']==0,'Ambush intro and audio bank ready')
        e.gun_tap(2,128,112)
        e.wait_state(lambda s:s['ambush_phase']==1,'Start ambush')
        assert e.state()['ambush_phase']==1
        first=frame('ready')
        def hero_visible(pixels,x):
            crop=pixels[154:202,max(0,x-16):min(256,x+16)].astype(int)
            return int(np.count_nonzero((crop[:,:,0]>crop[:,:,1]+7)&
                                        (crop[:,:,1]>crop[:,:,2]+5)))
        assert hero_visible(first,e.state()['x'])>40, 'Hero OAM exists but the PPU does not show it'
        late_match=re.search(r'^([0-9a-fA-F]{8}) video_late_commits$',
                             (ROOT/'chernorechye.sym').read_text(),re.M)
        late_address=int(late_match[1],16)-0x7e0000
        def late():return int.from_bytes(C.string_at(e.memory+late_address,2),'little')
        late_before=late()
        address=int(re.search(r'^([0-9a-fA-F]{8}) oamMemory$',
                             (ROOT/'chernorechye.sym').read_text(),re.M)[1],16)-0x7e0000
        shadow=C.string_at(e.memory+address,544)
        assert shadow[1]==154 and shadow[5]==shadow[9]==186, 'Bottom-lane hero is missing'
        assert shadow[512]&2, 'Hero upper body is not a 32x32 sprite'
        vram=e.lib.retro_get_memory_data(3)
        assert C.string_at(vram,32768)==(ROOT/'assets/generated/ambush-ground.vram').read_bytes(), 'Native Mode 7 map missing'
        ground=first[96:204,24:232].astype(float)
        luma=ground@np.array([0.2126,0.7152,0.0722])
        assert 65<float(luma.mean())<170, ('Night palette is too dark or washed out',luma.mean())
        assert float(np.mean(luma<25))<0.04, 'A dark torch mask covers the arena'
        assert float(np.mean(luma>215))<0.04, 'Arena has been whitened'
        widths=[]
        for y in (98,140):
            row=first[y].astype(int)
            ids=np.flatnonzero(((row[:,0]>100)&(row[:,1]>110)&(row[:,2]>115))[64:192])
            widths.append(int(ids[-1]-ids[0]+1) if len(ids) else 0)
        assert widths[1]>widths[0]+8, ('Ground does not narrow toward the horizon',widths)
        e.gun_tap(3,220,194)
        e.wait_state(lambda s:s['x']>=210,'Horizontal Scope step',limit=180)
        moved=frame('moving')
        assert e.state()['y']==202 and e.state()['lamp']==before['lamp']
        assert np.count_nonzero(first[100:140,64:192]!=moved[100:140,64:192])>1000, 'Mode 7 camera does not move'
        e.buttons={4};e.run(16);e.buttons=set()
        assert e.state()['y']==202, 'Vertical input escaped the bottom lane'
        e.gun_tap(6);e.wait_mode(7)
        saved=e.state();e.run(60)
        assert e.state()['ambush_clock']==saved['ambush_clock']
        e.gun_tap(6);e.wait_mode(13)
        # The lower HUD is not a shooting target, even when its optical packet is valid.
        e.gun_tap(2,250,220)
        assert not e.state()['bow_cooldown']
        e.gun_tap(3,128,196)
        e.wait_state(lambda s:abs(s['x']-128)<=2,'Return to centre',limit=180)
        # Exercise a complete announced attack, dodge and visible retreat.
        e.wait_state(lambda s:any(f['hp'] and f['state']==1 for f in s['enemies']),
                     'First announced attack',limit=900)
        state=e.state()
        first_fox=next(i for i,f in enumerate(state['enemies']) if f['hp'] and f['state']==1)
        locked=state['enemies'][first_fox]['respawn']
        kills=state['kills'];health=state['ambush_health']
        recording=True
        frame('windup')
        e.gun_tap(3,232 if locked<128 else 24,196)
        e.wait_state(lambda s:s['enemies'][first_fox]['state']==2 and
                     s['enemies'][first_fox]['y']>=174,'Committed charge',limit=180)
        assert e.state()['enemies'][first_fox]['respawn']==locked,'Charge follows the player'
        charge=frame('charge')
        fox=e.state()['enemies'][first_fox]
        crop=charge[max(88,fox['y']-48):fox['y']+2,
                    max(0,fox['x']-36):min(256,fox['x']+36)].astype(int)
        assert np.count_nonzero((crop[:,:,0]>140)&(crop[:,:,0]>crop[:,:,1]*1.2)&
                                (crop[:,:,1]>crop[:,:,2]*1.2))>70, 'Charging fox is invisible in the PPU frame'
        assert hero_visible(charge,e.state()['x'])>40, 'Hero disappears while dodging'
        e.wait_state(lambda s:s['enemies'][first_fox]['state']==3,'Fox retreat',limit=120)
        retreat_clock=e.state()['ambush_clock']
        frame('retreat')
        e.wait_state(lambda s:s['ambush_defeated']>=1,'Repelled scout leaves the clearing',limit=180)
        assert e.state()['ambush_clock']-retreat_clock>=45,'Fox teleported away'
        assert e.state()['kills']==kills and e.state()['ambush_health']==health
        recording=False
        waves=set();max_foxes=0;shots=0
        for _ in range(1800):
            state=e.state()
            assert state['mode']==13 and state['y']==202
            if state['ambush_phase']==2:break
            if state['ambush_phase']==4:
                e.run(4);continue
            assert state['ambush_phase']==1,('Pack defeated the Scope player',state)
            waves.add(state['ambush_wave'])
            alive=[fox for fox in state['enemies'] if fox['hp']]
            max_foxes=max(max_foxes,len(alive))
            if alive:
                fox=max(alive,key=lambda f:f['y'])
                radius=8 if fox['y']<112 else (12 if fox['y']<148 else 16)
                e.gun_tap(2,fox['x'],fox['y']-radius)
                shots+=1
                if shots%2==0:frame('combat' if shots==2 else None)
            else:e.run(4)
        else:raise AssertionError('Waves never ended')
        assert e.state()['ambush_defeated']==12 and waves=={0,1,2}
        assert e.state()['kills']-kills>=10,'Scope did not hit the rest of the pack'
        assert e.state()['ambush_clock']>=1000,'Waves collapsed into a short spawn rush'
        late_commits=(late()-late_before)&65535
        assert late_commits==0,('Fox animation DMA ran beyond VBlank',late_commits)
        assert e.state()['day_seconds']==before['day_seconds']
        frame('clear')
        e.run(32);e.gun_tap(2,128,112);e.wait_mode(3)
        assert e.state()['room']==2 and e.state()['ambush_done']==1
        assert e.state()['evidence']==before['evidence'] and e.state()['flags']==before['flags']
        assert e.state()['y']==176 and not e.state()['bow_mode']
        r.inspect(8);assert e.state()['room']==1
        r.inspect(5);assert e.state()['room']==2 and e.state()['mode']==3
        gif=ROOT/'build'/('ambush-'+region+'.gif')
        images[0].save(gif,save_all=True,append_images=images[1:],duration=100,loop=0)
        dodge_gif=ROOT/'build'/('ambush-'+region+'-dodge.gif')
        clip[0].save(dodge_gif,save_all=True,append_images=clip[1:],
                     duration=80 if pal else 67,loop=0)
        report={'region':region.upper(),'controller':'Super Scope','shots':shots,'max_foxes':max_foxes,
                'ground_luma_mean':round(float(luma.mean()),1),'perspective_path_widths':widths,
                'late_commits':late_commits,
                'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'checks':['native interleaved Mode 7 VRAM','perspective and camera shift',
                          'moonlit palette without white veil','horizontal Cursor motion',
                          'announced fixed-lane attack','visible retreat after dodge',
                          'Scope arrows through three distinct waves','pause freezes the pack',
                          'chapel transition and no replay on return'],
                'gif':str(gif),'dodge_gif':str(dodge_gif)}
        (ROOT/'build'/('ambush-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--core',type=Path,required=True);parser.add_argument('--pal',action='store_true')
    args=parser.parse_args();run(args.core,args.pal)
