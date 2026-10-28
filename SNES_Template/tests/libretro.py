#!/usr/bin/env python3
"""Exercise the real ROM through a Snes9x libretro core, without a desktop.

Reads exported debug symbol addresses, sends controller input, and records actual
PPU frames. It never writes game RAM or skips combat by patching memory.
Usage: python3 tests/rom_smoke.py --core /path/to/snes9x_libretro.so [--scope]
"""
import argparse
import hashlib
import ctypes as C
import json
import re
import struct
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ENV=C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p)
VIDEO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t)
AUDIO=C.CFUNCTYPE(None,C.c_int16,C.c_int16)
BATCH=C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
POLL=C.CFUNCTYPE(None)
STATE=C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint)

class GameInfo(C.Structure):
    _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]

class Variable(C.Structure):
    _fields_=[('key',C.c_char_p),('value',C.c_char_p)]

class Emulator:
    def __init__(self,core,scope,pal=False):
        self.lib=C.CDLL(str(core.resolve()))
        self.buttons=set(); self.gun=set(); self.x=128; self.y=112
        self.fmt=2; self.frame=None; self.want_frame=False
        self.audio_peak=0; self.audio_frames=0
        self.directory=str(ROOT).encode()
        self.pal=pal
        self.callbacks=[ENV(self.environment),VIDEO(self.video),AUDIO(lambda l,r:None),
                        BATCH(self.audio_batch),POLL(lambda:None),STATE(self.input)]
        for name,callback in zip(('environment','video_refresh','audio_sample',
                                 'audio_sample_batch','input_poll','input_state'),self.callbacks):
            function=getattr(self.lib,'retro_set_'+name)
            function.argtypes=[type(callback)]; function(callback)
        self.lib.retro_init()
        self.lib.retro_load_game.argtypes=[C.POINTER(GameInfo)]
        self.lib.retro_load_game.restype=C.c_bool
        self.buffer=C.create_string_buffer((ROOT/'chernorechye.sfc').read_bytes())
        info=GameInfo(str(ROOT/'chernorechye.sfc').encode(),C.cast(self.buffer,C.c_void_p),len(self.buffer)-1,None)
        assert self.lib.retro_load_game(C.byref(info)),'ROM loading failed'
        self.lib.retro_set_controller_port_device(0,1)
        self.lib.retro_set_controller_port_device(1,260 if scope else 1)
        self.lib.retro_get_memory_data.argtypes=[C.c_uint]
        self.lib.retro_get_memory_data.restype=C.c_void_p
        self.memory=self.lib.retro_get_memory_data(2)
        symbols=(ROOT/'chernorechye.sym').read_text()
        manifest=json.loads((ROOT/'build/link_manifest.json').read_text())
        assert hashlib.sha256((ROOT/'chernorechye.sfc').read_bytes()).hexdigest()==manifest['rom_sha256'],'ROM/symbol manifest mismatch'
        assert hashlib.sha256(symbols.encode()).hexdigest()==manifest['symbols_sha256'],'Stale symbols'
        self.symbols={}
        for line in symbols.splitlines():
            match=re.match(r'([0-9a-fA-F]{8}) (.*)',line)
            if match:
                name=match[2].rsplit('_',1)[-1]
                self.symbols[name]=int(match[1],16)-0x7e0000
        self.game_addr=self.symbols['game']
        self.frames=0

    def environment(self,cmd,data):
        cmd &= 0xffff
        if cmd==10:
            self.fmt=C.cast(data,C.POINTER(C.c_int))[0]; return True
        if cmd in (9,30,31):
            C.cast(data,C.POINTER(C.c_char_p))[0]=self.directory; return True
        if cmd==3:
            C.cast(data,C.POINTER(C.c_bool))[0]=True; return True
        if cmd==17:
            C.cast(data,C.POINTER(C.c_bool))[0]=False; return True
        if cmd==15:
            var=C.cast(data,C.POINTER(Variable)).contents
            if var.key==b'snes9x_superscope_crosshair':
                var.value=b'0'; return True
            if var.key==b'snes9x_region':
                var.value=b'pal' if self.pal else b'ntsc'; return True
            return False
        if cmd==39:
            C.cast(data,C.POINTER(C.c_uint))[0]=0; return True
        return cmd in (1,6,8,11,16,18,32,34,35,36,37,51)

    def input(self,port,device,index,key):
        if port==0 and device==1:
            if key==256: return sum(1<<x for x in self.buttons)
            return int(key in self.buttons)
        if port==1 and device==4:
            if key==13: return int(self.x*65534/255-32767)
            if key==14: return int(self.y*65534/223-32767)
            return int(key in self.gun)
        return 0

    def video(self,data,width,height,pitch):
        if not data or not self.want_frame: return
        raw=C.string_at(data,pitch*height)
        if self.fmt==1:
            arr=np.frombuffer(raw,dtype=np.uint8).reshape(height,pitch)[:,:width*4].reshape(height,width,4)
            self.frame=Image.fromarray(arr[:,:,[2,1,0]].copy())
        else:
            arr=np.frombuffer(raw,dtype='<u2').reshape(height,pitch//2)[:,:width]
            if self.fmt==2:
                rgb=np.stack(((arr>>11)*255//31,((arr>>5)&63)*255//63,(arr&31)*255//31),axis=2)
            else:
                rgb=np.stack((((arr>>10)&31)*255//31,((arr>>5)&31)*255//31,(arr&31)*255//31),axis=2)
            self.frame=Image.fromarray(rgb.astype(np.uint8))

    def audio_batch(self,data,n):
        if data and n:
            raw=np.frombuffer(C.string_at(data,n*4),dtype='<i2').astype(np.int32)
            self.audio_peak=max(self.audio_peak,int(np.max(np.abs(raw))))
            self.audio_frames+=n
        return n

    def run(self,n=1):
        for _ in range(n): self.lib.retro_run(); self.frames+=1

    def tap(self,key):
        # Allow a complete main-loop/input-queue pass on both edges, including
        # frames spent uploading a background or rebuilding torch HDMA tables.
        self.buttons={key}; self.run(8); self.buttons=set(); self.run(8)

    def gun_tap(self,key,x=None,y=None):
        if x is not None: self.x=x
        if y is not None: self.y=y
        self.gun={key}; self.run(12); self.gun=set(); self.run(12)

    def state(self):
        raw=C.string_at(self.memory+self.game_addr,154)
        keys=('mode','room','dialogue','page','option','choice','lamp','direction','oil','fear','forest_step','chapel_step','rune_mask','evidence','ending','revealed','return_mode','journal_page','checkpoint_room','notice','pulse','enemy_active','charge0','charge1','charge2','last_hotspot')
        result=dict(zip(keys,raw[:26]))
        for i,key in enumerate(('flags','tick','seconds','interactions','x','y','destination_x','destination_y','enemy_x','enemy_y')):
            result[key]=struct.unpack_from('<H' if i<4 else '<h',raw,26+i*2)[0]
        result.update(zip(("memories","echo_charge","wards","bell_step","ward_timer"),raw[46:51]))
        result['day_seconds'],result['day_number']=struct.unpack_from('<HH',raw,52)
        result['enemy_slots']=raw[59]
        result['notice_ticks'],result['focus']=raw[148:150]
        result['hurt_timer'],result['shove_cooldown']=raw[150:152]
        result['hit_stop']=raw[152]
        result.update(zip(('sun_level','time_phase','time_notice'),raw[56:59]))
        result['nights'],result['kills']=struct.unpack_from('<HH',raw,60)
        result.update(zip(('bow_mode','bow_draw','bow_cooldown','bow_direction',
                           'ammo','shot_request','combat_notice','combat_notice_ticks'),raw[64:72]))
        result['aim_x'],result['aim_y']=struct.unpack_from('<hh',raw,72)
        result['enemies']=[]
        for index in range(4):
            values=struct.unpack_from('<hhBBBBHBB',raw,76+index*12)
            result['enemies'].append(dict(zip(('x','y','hp','hit','kind','attack',
                                               'respawn','step','state'),values)))
        result['arrows']=[]
        for index in range(3):
            values=struct.unpack_from('<hhbbBB',raw,124+index*8)
            result['arrows'].append(dict(zip(('x','y','dx','dy','life','damage'),values)))
        return result

    def wait_state(self,predicate,label,limit=120):
        for _ in range(limit):
            state=self.state()
            if predicate(state):return state
            self.run(1)
        raise AssertionError(label+': '+str(self.state()))

    def wait_mode(self,mode):
        return self.wait_state(lambda s:s['mode']==mode,'Expected mode '+str(mode))

    def capture(self,name,allow_dark=False):
        self.want_frame=True; self.run(12); self.want_frame=False
        assert self.frame is not None
        path=ROOT/'build'/name; self.frame.save(path)
        assert allow_dark or np.max(np.array(self.frame))>0,'Empty PPU frame'
        return str(path)

    def close(self): self.lib.retro_unload_game(); self.lib.retro_deinit()
