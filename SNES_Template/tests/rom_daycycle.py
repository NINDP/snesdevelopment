#!/usr/bin/env python3
"""Observe a complete solar cycle through real input; never change game RAM."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from libretro import Emulator, ROOT
from rom_smoke import Runner, daylight


def run(core,pal=False):
    e=Emulator(core,False,pal);r=Runner(e,False)
    region='pal' if pal else 'ntsc'
    r.prefix='daycycle-'+region+'-'
    shots=[];levels=[]
    def capture(name):
        r.capture(name);shots.append((name,e.frame.copy()))
    def until(day,second):
        for _ in range(1800):
            s=e.state()
            assert s['mode']==3,('World clock left exploration',s)
            if (s['day_number'],s['day_seconds'])>=(day,second):return
            e.run(30)
        raise AssertionError(('Clock stopped',e.state(),day,second))
    def frozen(button,mode):
        e.tap(button);e.wait_mode(mode)
        before=e.state();e.run(180);after=e.state()
        for field in ('day_seconds','day_number','sun_level','time_phase','oil','fear'):
            assert before[field]==after[field],('Time advanced behind UI',mode,field)
        capture('journal' if mode==6 else 'pause')
        e.tap(button);e.wait_mode(3)
    try:
        e.run(190);e.tap(8);r.finish()
        assert e.state()['day_seconds']==512 and not e.state()['lamp']
        capture('day-unlit')
        pixels=np.asarray(e.frame)
        assert np.count_nonzero(np.any(pixels[60:190,:48],axis=2))>500,'Daylight still clips to torch'
        frozen(1,6);frozen(3,7)
        until(1,576);capture('dusk-warning')
        assert e.state()['time_notice']>0 and e.state()['time_phase']==3
        for second in (580,592,608,624,636):
            until(1,second);capture('dusk-'+str(second))
            levels.append((e.state()['sun_level'],np.mean(np.asarray(e.frame)[65:190,:48])))
        assert all(a[1]>=b[1] for a,b in zip(levels,levels[1:])),('Sunset brightened',levels)
        until(1,640);capture('night-unlit')
        assert not daylight(e.state())
        r.light();capture('night-torch')
        e.audio_peak=0;e.run(180)
        assert e.audio_peak>0,'Night heartbeat/chime is silent'
        until(2,0);capture('midnight')
        until(2,160);capture('dawn-warning')
        assert e.state()['time_phase']==1 and e.state()['time_notice']>0
        for second in (164,180,196,212):
            until(2,second);capture('dawn-'+str(second))
        until(2,224);capture('day-returned')
        assert e.state()['oil']>0 and e.state()['sun_level']==16
        e.tap(9);assert not e.state()['lamp']
        until(2,512);capture('full-cycle')
        assert e.state()['day_number']==2 and e.state()['day_seconds']>=512
        # Reach the chapel through ordinary quest actions while the sun is up.
        r.inspect(2);r.light();r.inspect(0);r.inspect(1);r.choose(0);r.inspect(3)
        assert e.state()['room']==1 and not e.state()['enemy_active'],'Daytime forest shadow is awake'
        r.inspect(0);r.inspect(1);r.choose(0)
        for index in (2,3,4):r.inspect(index)
        r.inspect(5);assert e.state()['room']==2 and e.state()['sun_level']>0
        e.tap(9);capture('chapel-unlit-at-day')
        assert not np.any(np.asarray(e.frame)[:176]),'Sunlight leaked into boarded chapel'
        r.light();capture('chapel-torch-at-day')
        sheet=Image.new('RGB',(768,464),(0,0,0));d=ImageDraw.Draw(sheet)
        selected=['day-unlit','dusk-608','night-torch','dawn-180','day-returned','chapel-torch-at-day']
        lookup=dict(shots)
        for index,name in enumerate(selected):
            x=(index%3)*256;y=(index//3)*232
            sheet.paste(lookup[name],(x,y+8));d.text((x+4,y),name,fill=(220,200,150))
        sheet.save(ROOT/'build'/('daycycle-'+region+'-preview.png'))
        images=[im for _,im in shots if im.size==(256,224)]
        images[0].save(ROOT/'build'/('daycycle-'+region+'.gif'),save_all=True,
                       append_images=images[1:],duration=650,loop=0)
        report={'region':region.upper(),'rom_sha256':json.loads((ROOT/'build/link_manifest.json').read_text())['rom_sha256'],
                'checks':['full 768-second solar cycle','day counter rollover','daylight without torch',
                          'monotonic sunset','strict night darkness','night torch','dawn/day return',
                          'paused journal and pause clock','daytime forest retreat','dark indoor at daytime'],
                'frames':e.frames,'sunset_levels':levels,'final_state':e.state()}
        (ROOT/'build'/('daycycle-regression-'+region+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),'PASS')
    finally:e.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--pal',action='store_true')
    a=p.parse_args();run(a.core,a.pal)
