#!/usr/bin/env python3
"""Verify real SPC output, torch channel control, MSU-1 and missing-track fallback."""
import argparse
import ctypes as C
import json
from pathlib import Path
import re
import tempfile
import libretro
from rom_smoke import Runner

ROOT=libretro.ROOT


def address(name):
    text=(ROOT/'chernorechye.sym').read_text()
    match=re.search(r'^([0-9a-fA-F]{8}) '+name+r'\s*$',text,re.M)
    assert match,name
    return int(match[1],16)-0x7e0000


def value(e,name):
    return C.string_at(e.memory+address(name),1)[0]


def run(core):
    reports=[]
    for mode in ('spc','msu1','missing-track'):
        with tempfile.TemporaryDirectory(prefix='chernorechye-audio-') as tmp:
            directory=Path(tmp)
            (directory/'build').mkdir()
            for name in ('chernorechye.sfc','chernorechye.sym','build/link_manifest.json'):
                (directory/name).symlink_to(ROOT/name)
            if mode!='spc':
                (directory/'chernorechye.msu').touch()
            if mode=='msu1':
                for path in (ROOT/'build/msu1').glob('*.pcm'):
                    (directory/path.name).symlink_to(path)
            libretro.ROOT=directory
            e=libretro.Emulator(core,False)
            try:
                e.run(300)
                assert e.state()['mode']==1,(mode,e.state())
                active=value(e,'audio_msu_active')
                assert active==(mode=='msu1'),(mode,active)
                if mode=='missing-track':
                    assert value(e,r'tccs_Data/platform/audio.asm_msu_failed')==1
                assert e.audio_peak>0,(mode,'silent music')
                if mode=='spc':
                    # Only real controller input. The module must survive X.
                    e.tap(8);r=Runner(e,False);r.finish();e.run(100)
                    module=value(e,r'tccs_Data/platform/audio.asm_loaded')
                    e.tap(9);e.wait_state(lambda s:s['lamp']==1,'Torch on');e.run(60)
                    assert value(e,r'tccs_Data/platform/audio.asm_loaded')==module
                    e.tap(9);e.wait_state(lambda s:s['lamp']==0,'Torch off');e.run(60)
                    assert value(e,r'tccs_Data/platform/audio.asm_loaded')==module
                    assert e.state()['tick']>0
                reports.append(dict(mode=mode,msu_active=bool(active),peak=e.audio_peak,frames=e.frames))
            finally:
                e.close();libretro.ROOT=ROOT
    (ROOT/'build/audio-runtime.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports),'PASS')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--core',type=Path,required=True)
    run(parser.parse_args().core.resolve())
