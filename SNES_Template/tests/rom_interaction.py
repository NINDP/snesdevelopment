#!/usr/bin/env python3
"""Reproduce ordinary A-button approaches, feedback and a four-room quest."""
import argparse
import json
from pathlib import Path
import numpy as np
from libretro import Emulator, ROOT
from rom_smoke import Runner, HOTSPOTS

def run(core,pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    region='pal' if pal else 'ntsc';r.prefix='interaction-'+region+'-'
    checks=[]
    def capture(name):
        r.capture(name)
        assert np.count_nonzero(np.asarray(e.frame)[192:223])>120,('Interaction panel missing',name)
    try:
        e.run(190);e.tap(8);r.finish();r.light()
        r.walk(80,100);e.run(8)
        assert e.state()['focus']==0,('Elder stolen by optional trace',e.state())
        # Compare the native selector with an independent facing-aware score
        # on real turns. This also catches signed-coordinate errors in ASM.
        for button in (7,5,6,4):
            e.buttons={11,button};e.run(12);e.buttons=set();e.run(8)
            s=e.state();candidates=[];facing=(s['direction']>>1)&3
            for index,(x,y) in enumerate(HOTSPOTS[0]):
                dx=x-s['x'];dy=y-s['y'];distance=abs(dx)+abs(dy)
                if distance>=56:continue
                front=(dy<=-8,dx>=8,dy>=8,dx<=-8)[facing]
                candidates.append((distance+(0 if front else 48),index))
            expected=min(candidates)[1] if candidates else 255
            assert s['focus']==expected,('Native target selection mismatch',s,expected)
        assert e.state()['focus']==0
        capture('elder-prompt')
        e.tap(8);assert e.state()['mode']==2 and e.state()['dialogue']==1
        r.finish();checks.append('A at diagonal approach selects the elder')
        r.inspect(1);r.choose(0);r.inspect(3)
        assert e.state()['room']==1
        r.inspect(2)
        assert e.state()['notice']==3 and e.state()['notice_ticks']>0
        capture('read-birch-first');checks.append('missing prerequisite is visible in exploration')
        r.inspect(0);r.inspect(2)
        assert e.state()['forest_step']==1 and e.state()['notice']==13
        capture('first-sign-accepted')
        r.inspect(3)
        assert e.state()['forest_step']==2 and e.state()['notice']==14
        capture('second-sign-accepted')
        r.inspect(4);assert e.state()['flags']&64
        r.inspect(1);r.choose(0);r.inspect(1)
        assert e.state()['mode']==3 and e.state()['flags']&16
        checks.append('sign progress and repeat conversations remain usable')
        r.inspect(5);assert e.state()['room']==2
        r.inspect(4)
        assert e.state()['notice']==18 and e.state()['notice_ticks']>0
        capture('fill-the-cups-first')
        r.inspect(0);r.inspect(1);r.walk(110,138);e.run(8)
        assert e.state()['focus']==6,('Urn stole the silver token focus',e.state())
        capture('silver-prompt')
        e.tap(8);assert e.state()['mode']==2 and e.state()['dialogue']==12
        r.finish();assert e.state()['flags']&512
        checks.append('A selects silver from an ordinary diagonal approach')
        r.inspect(3);r.cups();r.inspect(4);r.choose(0)
        assert e.state()['room']==3 and e.state()['mode']==3
        checks.append('pad-only route reaches all four rooms')
        report={'region':region.upper(),'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'checks':checks,'frames':e.frames,'final_state':e.state()}
        (ROOT/'build'/('interaction-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
