#!/usr/bin/env python3
"""Complete the real ROM through controller events. Never write game RAM."""
import argparse,json
import ctypes as C
import struct
from pathlib import Path
import numpy as np
from libretro import Emulator,ROOT
HOTSPOTS=[[(56,78),(190,112),(116,158),(232,152),(32,146)],[(64,96),(184,76),(28,144),(116,60),(208,144),(232,102),(128,166),(80,158)],[(48,88),(198,88),(126,158),(128,66),(228,170),(36,150),(84,124)],[(192,82),(56,84),(48,130),(128,130),(208,130),(128,66),(24,170),(232,170)]]
HOTSPOTS[0].append((94,104))
HOTSPOTS[1].extend([(168,116),(12,40)])
HOTSPOTS[2].extend([(172,144),(224,48)])
HOTSPOTS[3].append((84,96))
# Independent screen-space contract, deliberately not read from generated HDMA.
# The largest flicker radius is 79; two pixels cover scanline/latch rounding.
_TORCH_Y,_TORCH_X=np.ogrid[:224,:256]
TORCH_CENTERS=((119,125),(140,126),(136,127),(116,126))
def torch_center(state):
    return TORCH_CENTERS[(state['direction']>>1)&3]
def daylight(state):
    second=state['day_seconds']
    sun=0 if second<160 or second>=640 else ((second-160)//4 if second<224 else
        (16 if second<576 else 16-(second-576)//4))
    assert state['sun_level']==sun,('Stale daylight',state)
    return sun if state['room']<2 else 0
def world_cut(state):
    return 176  # Persistent clock/status dashboard occupies the bottom 48 px.
class Runner:
    def __init__(self,e,scope):
        self.e=e;self.scope=scope;self.shots=[];self.prefix=''
    def capture(self,name):
        state=self.e.state()
        self.shots.append(self.e.capture(self.prefix+name+'.png',
            allow_dark=state['mode']==3 and not (state['lamp'] and state['oil']) and not daylight(state)))
        self.check_darkness(name,self.e.state())
    def check_darkness(self,name,state):
        mode=state['mode']
        if mode==6:return  # Journal is an opaque, standalone Mode 1 page.
        if mode==3:cut=world_cut(state)
        elif mode in (2,4,5,6,7,11):
            if mode==2 and (state['dialogue']==22 or (state['dialogue']==0 and state['page']<3)):return
            if mode==7 and (state['return_mode']==12 or
                    (state['return_mode']==2 and state['dialogue'] in (0,22))):return
            cut={2:128,4:88,5:64,6:16,7:48,11:64}[mode]
        else:return
        pixels=np.asarray(self.e.frame)
        assert pixels.shape==(224,256,3),(name,pixels.shape)
        # The mode-switch scanline may already contain the first UI pixels.
        end=cut if cut==224 else cut-1
        world=pixels[:end]
        if daylight(state):
            if daylight(state)==16 and end>80:
                assert np.count_nonzero(np.any(world!=0,axis=2))>500,('Missing sunlight',name,state)
            return
        if not (state['lamp'] and state['oil']):
            assert not np.any(world),(name,'Unlit world revealed behind UI',state)
            return
        cx,cy=torch_center(state)
        outside=(_TORCH_X-cx)**2+(_TORCH_Y-cy)**2>81**2
        escaped=np.any(world!=0,axis=2)&outside[:end]
        assert not np.any(escaped),(name,'Light escaped the torch circle',
            np.argwhere(escaped)[:8].tolist(),state)
        if mode==3:
            assert np.count_nonzero(np.any(world!=0,axis=2))>150,(
                name,'Lit world is missing',state)
    def lighting_roundtrip(self,name):
        """Exercise light/UI transitions at each room entry without moving."""
        before=self.e.state()
        assert before['mode']==3 and before['lamp'] and before['oil'],before
        self.capture(name)
        self.e.gun_tap(3,128,112) if self.scope else self.e.tap(9)
        self.e.wait_state(lambda s:not s['lamp'],'Torch input after room audio load')
        assert not self.e.state()['lamp'],self.e.state()
        self.capture(name+'-lamp-off')
        self.e.tap(1);self.e.wait_mode(6)
        self.capture(name+'-dark-journal')
        self.e.tap(1);self.e.wait_mode(3)
        self.capture(name+'-dark-resume')
        self.light();self.capture(name+'-light-resume')
        after=self.e.state()
        for field in ('mode','room','x','y','interactions'):
            assert after[field]==before[field],(name,field,before,after)
    def screen_point(self,x,y):
        state=self.e.state()
        if state['mode']!=3:return x,y
        dy=y-state['y']
        sy=round(32+16896/(128-dy))
        sx=round(128+(x-state['x'])*(sy-32)/128)
        return sx,sy
    def action(self,x=128,y=112):
        if self.scope:
            sx,sy=self.screen_point(x,y)
            self.e.gun_tap(2,sx,sy)
        else:self.e.tap(8)
    def finish(self):
        for _ in range(80):
            if self.e.state()['mode']==13:
                self.ambush()
            if self.e.state()['mode']==12:
                self.e.buttons={7}
                self.e.wait_state(lambda s:s['mode']!=12,'Corridor exit',limit=600)
                self.e.buttons=set()
            if self.e.state()['mode']!=2:return
            self.action()
        raise AssertionError('Dialogue stuck: '+str(self.e.state()))
    def ambush(self):
        for _ in range(1500):
            state=self.e.state()
            if state['mode']!=13:return
            if state['ambush_phase']==4:
                self.e.run(4);continue
            if state['ambush_phase']!=1:
                if state['ambush_timer']:
                    self.e.run(state['ambush_timer']+2)
                self.action()
                continue
            alive=[fox for fox in state['enemies'] if fox['hp']]
            if not alive:
                self.e.run(4);continue
            fox=max(alive,key=lambda value:value['y'])
            radius=8 if fox['y']<112 else (12 if fox['y']<148 else 16)
            self.action(fox['x'],fox['y']-radius)
        raise AssertionError('Ambush did not finish: '+str(self.e.state()))
    def light(self):
        if not self.e.state()['lamp']:
            self.e.gun_tap(3,128,112) if self.scope else self.e.tap(9)
            self.e.wait_state(lambda s:s['lamp']==1,'Torch input')
        assert self.e.state()['lamp']==1
    def axis(self,field,target):
        for _ in range(600):
            state=self.e.state()
            if abs(state[field]-target)<=3:break
            positive=7 if field=='x' else 5
            negative=6 if field=='x' else 4
            self.e.buttons={positive if state[field]<target else negative};self.e.run(1)
        else:raise AssertionError('Movement stuck: '+str(self.e.state()))
        self.e.buttons=set();self.e.run(3)
    def walk(self,x,y):
        if self.scope:
            room=self.e.state()['room']
            for _ in range(50):
                state=self.e.state()
                if state['room']!=room or state['mode']!=3:return
                if abs(state['x']-x)<=1 and abs(state['y']-y)<=1:break
                tx=state['x']+max(-48,min(48,x-state['x']))
                ty=state['y']+max(-24,min(24,y-state['y']))
                if (tx,ty)!=(x,y):
                    for hx,hy in HOTSPOTS[room]:
                        if abs(tx-hx)+abs(ty-hy)<=20:
                            tx=max(12,min(244,tx+(20 if tx>=hx else -20)))
                sx, sy = self.screen_point(tx, ty)
                before = self.e.state()

                self.action(tx, ty)

                after = self.e.state()

                if self.scope:
                    print(
                        "SCOPE DEBUG:",
                        "position=", (before["x"], before["y"]),
                        "requested=", (tx, ty),
                        "screen=", (sx, sy),
                        "actual_destination=",
                        (after["destination_x"], after["destination_y"]),
                        flush=True
                    )
                for _ in range(60):
                    state=self.e.state()
                    if state['room']!=room or state['mode']!=3:return
                    if abs(state['x']-tx)<=2 and abs(state['y']-ty)<=2:break
                    self.e.run(1)
            else:raise AssertionError('Scope walk stuck: '+str(self.e.state()))
            self.e.run(5);return
        self.axis('y',174);self.axis('x',x);self.axis('y',y)
        self.e.buttons={11,4}
        for _ in range(60):
            self.e.run(1)
            if self.e.state()['direction']==0:break
        else:raise AssertionError('Aim input not consumed: '+str(self.e.state()))
        self.e.buttons=set();self.e.run(4)
    def inspect(self,index):
        s=self.e.state();x,y=HOTSPOTS[s['room']][index];target_y=min(y+22,179)
        if self.scope:
            room=s['room'];serial=s['interactions']
            self.walk(x,174)
            if self.e.state()['room']!=room or self.e.state()['mode']!=3:
                self.finish();return
            state=self.e.state()
            if state['interactions']!=serial and state['last_hotspot']==index:
                self.finish();return
            self.walk(x,target_y)
            if self.e.state()['room']!=room or self.e.state()['mode']!=3:
                self.finish();return
            state=self.e.state()
            if state['interactions']!=serial and state['last_hotspot']==index:
                self.finish();return
        else:self.walk(x,target_y)
        serial=self.e.state()['interactions']
        self.action(x,y)
        # Input is queued on VBlank. Wait for this event to be consumed before
        # moving toward another object, rather than assuming a host-frame delay.
        for _ in range(120):
            if self.e.state()['interactions']!=serial:break
            self.e.run(1)
        else:raise AssertionError('Inspect event not consumed: '+str(self.e.state()))
        assert self.e.state()['last_hotspot']==index,self.e.state()
        self.finish()
    def choose(self,option):
        assert self.e.state()['mode']==4,self.e.state()
        if self.scope:self.action(128,128 if option==0 else 156)
        else:
            if option:self.e.tap(5)
            self.action()
        for _ in range(120):
            if self.e.state()['mode']!=4:break
            self.e.run(1)
        else:raise AssertionError('Choice event not consumed: '+str(self.e.state()))
        self.finish()
    def echo(self,index,bit):
        x,y=HOTSPOTS[self.e.state()['room']][index]
        self.walk(x,y+22)
        if self.scope:
            sx,sy=self.screen_point(x,y)
            self.e.gun_tap(4,sx,sy);self.e.x=sx;self.e.y=sy;self.e.gun={2}
        for _ in range(180):
            self.e.run(1)
            if self.e.state()['echo_charge']==45:break
        else:raise AssertionError('Echo never visible: '+str(self.e.state()))
        self.e.gun=set();self.e.run(8)
        if self.scope:self.e.gun_tap(4,*self.screen_point(x,y))
        self.action(x,y);self.e.wait_mode(2);self.capture('echo-'+str(bit));self.finish()
        assert self.e.state()['memories']&bit,self.e.state()
    def bells(self):
        self.inspect(7);self.e.wait_mode(11)
        self.capture('bells')
        for step,(option,y) in enumerate(((0,104),(2,152),(1,128)),1):
            if self.scope:self.action(172,y)
            else:
                while self.e.state()['option']!=option:
                    wanted=(self.e.state()['option']+1)%3
                    self.e.tap(5)
                    self.e.wait_state(lambda s:s['option']==wanted,'Bell selection')
                self.action()
            self.e.wait_state(lambda s:s['bell_step']==step,'Bell order')
        self.finish();assert self.e.state()['memories']&8,self.e.state()
    def cups(self):
        self.e.wait_mode(5)
        for step,y in enumerate((104,128,152),1):
            if self.scope:self.action(128,y)
            else:
                if step>1:
                    self.e.tap(5)
                    self.e.wait_state(lambda s:s['option']==step-1,'Cup selection')
                self.action()
            self.e.wait_state(lambda s:s['chapel_step']==step,'Cup answer')
        self.finish()
    def rune(self,index):
        x,y=HOTSPOTS[3][index+2];self.walk(x,y+22)
        if self.scope:
            sx,sy=self.screen_point(x,y)
            self.e.gun_tap(4,sx,sy) # keep still while directing the lamp
            self.e.x=sx;self.e.y=sy;self.e.gun={2}
        for _ in range(180):
            self.e.run(1)
            if self.e.state()['rune_mask']&(1<<index):break
            if self.e.state()['charge'+str(index)]>=60:break
        self.e.gun=set();self.e.run(8)
        if self.scope:self.e.gun_tap(4,*self.screen_point(x,y))
        if not self.e.state()['rune_mask']&(1<<index):
            self.action(x,y)
        self.e.wait_state(lambda s:s['rune_mask']&(1<<index),'Rune seal')
        self.finish()
        assert self.e.state()['rune_mask']&(1<<index),self.e.state()
def run(core,ending,pal=False,scope=False):
    e=Emulator(core,scope,pal);r=Runner(e,scope)
    r.prefix=ending+('-scope' if scope else '-pad')+('-pal-' if pal else '-ntsc-')
    e.run(20);r.capture('nabla');e.run(170)
    assert e.state()['mode']==1;r.capture('menu')
    if scope:
        e.tap(2);e.gun_tap(2,128,112);e.gun_tap(3,128,112);r.action(64,88)
    else:
        e.tap(5);e.tap(8);e.wait_mode(9)
        r.capture('controls');e.tap(0);e.wait_mode(1);r.action()
    e.wait_mode(2)
    # Verify and capture the visual prologue through real controller events.
    pages=json.loads((ROOT/'assets/story.json').read_text())['dialogues']['D_PROLOG']
    for page in range(len(pages)):
        e.run(36)
        assert e.state()['mode']==2 and e.state()['page']==page,e.state()
        r.capture('prologue' if page==0 else 'prologue-'+str(page+1))
        for _ in range(4):
            r.action()
            if e.state()['mode']!=2 or e.state()['page']!=page:break
        else:raise AssertionError('Prologue page did not advance: '+str(e.state()))
        if page == 0:
            e.wait_mode(12)
            before=e.state()
            r.capture('corridor-start')
            start_pixels=np.array(e.frame).copy()
            e.run(24)
            assert e.state()['x']==before['x'],'Corridor must wait for movement'
            if scope:
                e.gun_tap(2,240,108)
            else:e.buttons={7}
            e.wait_state(lambda s:s['x']>=180,'Corridor movement')
            r.capture('corridor-doorway')
            e.buttons=set()
            e.tap(3);e.wait_mode(7)
            stopped=e.state()['x'];e.run(20)
            assert e.state()['x']==stopped,'Pause moved corridor player'
            e.tap(0);e.wait_mode(12)
            if not scope:e.buttons={7}
            captured_stairs=False
            for _ in range(1200):
                if e.state()['mode']!=12:break
                if scope:e.gun_tap(2,248,108)
                else:e.run(1)
                if e.state()['mode']==12 and e.state()['x']>=350 and not captured_stairs:
                    r.capture('corridor-stairs')
                    assert np.count_nonzero(start_pixels[24:124]!=np.array(e.frame)[24:124])>4000,'Camera did not scroll background'
                    captured_stairs=True
            else:raise AssertionError('Corridor exit stuck: '+str(e.state()))
            e.buttons=set();e.gun=set()
            assert captured_stairs,'Stairs were never reached'
            assert e.state()['mode']==2 and e.state()['page']==1,e.state()
    e.wait_mode(3)
    r.capture('lamp-off');off=np.array(e.frame)
    assert (np.max(off)>0 if daylight(e.state()) else np.max(off)==0),'Incorrect unlit visibility'
    r.light();r.capture('lamp-on');on=np.array(e.frame)
    assert np.count_nonzero(np.max(on[80:220],axis=2)>32)>300,'Mode 7 ground missing'
    # The daylight panorama now occupies this area. Inspect the UI plane,
    # rather than treating any bright sky pixel as an unwanted HUD label.
    header=C.string_at(e.lib.retro_get_memory_data(3)+0xb800,3*32*2)
    assert all((tile&1023)==0 for tile in struct.unpack('<96H',header)),'Permanent header returned'
    # A sunlit floor legitimately fills the bottom rows with bright pixels.
    # The torch-only scene still distinguishes a footer by its bright area.
    if not daylight(e.state()):
        assert np.count_nonzero(np.any(on[208:224]>64,axis=2))<1500,'Permanent footer returned'
    r.lighting_roundtrip('village')
    e.tap(1);e.wait_mode(6);r.capture('status')
    saved=e.state();e.run(60)
    assert e.state()['oil']==saved['oil'] and e.state()['fear']==saved['fear'],'Status must freeze simulation'
    e.tap(1);e.wait_mode(3)
    r.capture('torch-motion-a');first=np.array(e.frame).copy();position=e.state()
    e.run(8);r.capture('torch-motion-b');second=np.array(e.frame)
    assert (e.state()['x'],e.state()['y'])==(position['x'],position['y'])
    fx,fy=torch_center(position)
    assert np.count_nonzero(first[fy-36:fy+16,fx-16:fx+16]!=second[fy-36:fy+16,fx-16:fx+16])>8,'Flame/embers are static'
    r.inspect(0);r.inspect(1);r.choose(0 if ending!='bad' else 1)
    if ending=='secret':
        r.inspect(4);r.echo(5,1)
    r.inspect(3);assert e.state()['room']==1,e.state();r.lighting_roundtrip('forest')
    r.inspect(0);r.inspect(1);r.choose(0 if ending!='bad' else 1)
    if ending=='secret':
        r.inspect(7);r.echo(8,2)
    if not scope:
        r.inspect(4);assert e.state()['forest_step']==0
    for index in (2,3,4):r.inspect(index)
    assert e.state()['flags']&64,e.state()
    r.inspect(5);assert e.state()['room']==2;r.lighting_roundtrip('chapel')
    r.inspect(0);r.inspect(1)
    if ending=='secret':r.inspect(5)
    r.inspect(6)
    if ending=='secret':r.bells()
    r.inspect(3);r.cups();assert e.state()['flags']&1024
    r.inspect(4);assert e.state()['mode']==4
    r.capture('revelation');r.choose(0 if ending!='bad' else 1);r.lighting_roundtrip('dungeon')
    if ending=='secret':
        r.echo(8,4);assert e.state()['memories']==15
        e.tap(0);e.wait_state(lambda s:s['wards']==2,'Silver ward')
        r.capture('silver-ward')
    if not scope:
        e.tap(1);e.wait_mode(6);r.capture('journal');e.tap(0);e.wait_mode(3)
        e.tap(3);e.wait_mode(7)
        tick=e.state()['tick'];e.run(120)
        assert e.state()['tick']==tick;r.capture('pause');e.tap(3);e.wait_mode(3)
    for index in range(3):r.rune(index)
    assert e.state()['rune_mask']==7 and e.state()['flags']&8192
    r.inspect(5);r.choose(1 if ending=='bad' else 0);assert e.state()['mode']==8,e.state()
    assert e.state()['ending']=={'good':0,'bad':1,'secret':2}[ending],e.state()
    r.capture('ending-'+ending)
    assert e.audio_peak>0,'Silent SPC output'
    report={'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'], 'audio_peak':e.audio_peak,'audio_frames':e.audio_frames,
        'controller':'Super Scope' if scope else 'gamepad',
        'region':'PAL' if pal else 'NTSC','requested_ending':ending,
        'frames':e.frames,'state':e.state(),'screenshots':r.shots}
    suffix=('-scope' if scope else '-pad')+('-pal' if pal else '-ntsc')
    (ROOT/'build'/('rom-'+ending+suffix+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('state','screenshots')}),'PASS',e.state())
    e.close()
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--ending',choices=('good','bad','secret'),default='good')
    p.add_argument('--pal',action='store_true');p.add_argument('--scope',action='store_true')
    a=p.parse_args();run(a.core,a.ending,a.pal,a.scope)
