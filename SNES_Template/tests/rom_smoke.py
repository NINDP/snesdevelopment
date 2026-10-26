#!/usr/bin/env python3
"""Complete the real ROM through controller events. Never write game RAM."""
import argparse,json
from pathlib import Path
import numpy as np
from libretro import Emulator,ROOT
HOTSPOTS=[[(56,78),(190,112),(116,158),(232,152),(32,146)],[(64,96),(184,76),(28,144),(116,60),(208,144),(232,102),(128,166),(80,158)],[(48,88),(198,88),(126,158),(128,66),(228,170),(36,150),(84,124)],[(192,82),(56,84),(48,130),(128,130),(208,130),(128,66),(24,170),(232,170)]]
HOTSPOTS[0].append((94,104))
HOTSPOTS[1].extend([(168,116),(12,40)])
HOTSPOTS[2].extend([(172,144),(224,48)])
HOTSPOTS[3].append((84,96))
class Runner:
    def __init__(self,e,scope):
        self.e=e;self.scope=scope;self.shots=[];self.prefix=''
    def capture(self,name):
        self.shots.append(self.e.capture(self.prefix+name+'.png'))
    def action(self,x=128,y=112):
        self.e.gun_tap(2,x,y) if self.scope else self.e.tap(8)
    def finish(self):
        for _ in range(80):
            if self.e.state()['mode']==12:
                self.e.buttons={7}
                self.e.wait_state(lambda s:s['mode']!=12,'Corridor exit',limit=600)
                self.e.buttons=set()
            if self.e.state()['mode']!=2:return
            self.action()
        raise AssertionError('Dialogue stuck: '+str(self.e.state()))
    def light(self):
        if not self.e.state()['lamp']:
            self.e.gun_tap(3,128,112) if self.scope else self.e.tap(9)
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
            self.e.gun_tap(2,x,y)
            for _ in range(650):
                s=self.e.state()
                if s['room']!=room or s['mode']!=3:return
                if abs(s['x']-x)<=1 and abs(s['y']-y)<=1:break
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
            self.e.gun_tap(4,x,y);self.e.x=x;self.e.y=y;self.e.gun={2}
        for _ in range(180):
            self.e.run(1)
            if self.e.state()['echo_charge']==45:break
        else:raise AssertionError('Echo never visible: '+str(self.e.state()))
        self.e.gun=set();self.e.run(8)
        if self.scope:self.e.gun_tap(4,x,y)
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
            self.e.gun_tap(4,x,y) # toggle TURBO: keep still while directing the lamp
            self.e.x=x;self.e.y=y;self.e.gun={2}
        for _ in range(180):
            self.e.run(1)
            if self.e.state()['rune_mask']&(1<<index):break
            if self.e.state()['charge'+str(index)]>=60:break
        self.e.gun=set();self.e.run(8)
        if self.scope:self.e.gun_tap(4,x,y)
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
    # The footer border starts on scanline 191 because BG3 scrolls by -1.
    r.capture('lamp-off');off=np.array(e.frame)[24:191]
    assert np.max(off)==0,'Lamp OFF must hide the world'
    r.light();r.capture('lamp-on');on=np.array(e.frame)[24:191]
    lit=np.max(on,axis=2)>64
    assert 100<np.count_nonzero(lit)<lit.size//2,'Radial torch clipping missing'
    assert np.count_nonzero(np.any(on>0,axis=2))>np.count_nonzero(lit),'Ambient silhouettes missing'
    r.capture('torch-motion-a');first=np.array(e.frame).copy();position=e.state()
    e.run(8);r.capture('torch-motion-b');second=np.array(e.frame)
    assert (e.state()['x'],e.state()['y'])==(position['x'],position['y'])
    x,y=position['x'],position['y']
    # Heat must move background pixels away from the ember sprites.
    heat_a=first[y-48:y-20,x-40:x-16]
    heat_b=second[y-48:y-20,x-40:x-16]
    assert np.count_nonzero(heat_a!=heat_b)>8,'Torch heat shimmer is static'
    assert np.count_nonzero(first[y-54:y+2,x-8:x+24]!=second[y-54:y+2,x-8:x+24])>4,'Flame/embers are static'
    r.inspect(0);r.inspect(1);r.choose(0 if ending!='bad' else 1)
    if ending=='secret':
        r.inspect(4);r.echo(5,1)
    r.inspect(3);assert e.state()['room']==1,e.state();r.capture('forest')
    r.inspect(0);r.inspect(1);r.choose(0 if ending!='bad' else 1)
    if ending=='secret':
        r.inspect(7);r.echo(8,2)
    if not scope:
        r.inspect(4);assert e.state()['forest_step']==0
    for index in (2,3,4):r.inspect(index)
    assert e.state()['flags']&64,e.state()
    r.inspect(5);assert e.state()['room']==2;r.capture('chapel')
    r.inspect(0);r.inspect(1)
    if ending=='secret':r.inspect(5)
    r.inspect(6)
    if ending=='secret':r.bells()
    r.inspect(3);r.cups();assert e.state()['flags']&1024
    r.inspect(4);assert e.state()['mode']==4
    r.capture('revelation');r.choose(0 if ending!='bad' else 1);r.capture('dungeon')
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
    r.inspect(5);r.choose(0);assert e.state()['mode']==8,e.state()
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
