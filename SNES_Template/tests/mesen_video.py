#!/usr/bin/env python3
"""Mesen regression: raster ownership, dialogue horizons, journal layers and DMA.

Only controller input is injected; game RAM and PPU registers remain read-only.
The headless runner disables saving Mesen settings. Lua IO is enabled only for
this process to export its report and actual PPU screenshots.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r'''
local game=@GAME@
local output=@OUTPUT@
local frame,age,journals,pauses,previous=0,0,0,0,255
local collisions,visibleDma,latePublish,night,overview,notes=0,0,0,false,false,false
local buttons={}
local spriteOverflow,maxTiles,worldSamples=0,0,0
local houseChecks,houseFailures,steady,lastX,lastY=0,0,0,-1,-1
local depthChecks,depthFailures=0,0
local horizonSamples,dialogueHorizonSamples,projectedLayerWrites=0,0,0
local journalChecks,journalLayerFailures=0,0
local prologHolds={[3]=0,[4]=0}
local depths=@DEPTHS@
local scales=@SCALES@
local function byte(offset) return emu.read(game+offset,emu.memType.snesWorkRam) end
local function screenshot(name)
 local file=assert(io.open(output..'/mesen-'..name..'.png','wb'))
 file:write(emu.takeScreenshot());file:close()
end
local function checkSprites()
 local rows={}
 for y=0,175 do rows[y]=0 end
 for n=0,127 do
  local x=emu.read(n*4,emu.memType.snesSpriteRam)
  local y=emu.read(n*4+1,emu.memType.snesSpriteRam)
  local high=(emu.read(512+math.floor(n/4),emu.memType.snesSpriteRam) >> ((n%4)*2)) & 3
  if (high & 1)~=0 then x=x-256 end
  local size=(high & 2)~=0 and 32 or 16
  if x<256 and x+size>0 then
   for row=0,size-1 do
    local sy=(y+row)%256
    if sy<176 then rows[sy]=rows[sy]+size/8 end
   end
  end
 end
 for y=0,175 do
  maxTiles=math.max(maxTiles,rows[y])
  if rows[y]>34 then spriteOverflow=spriteOverflow+1 end
 end
 worldSamples=worldSamples+1
end
local function checkHouses(x,y)
 if byte(6)~=0 and byte(8)>0 then
  local hero=-1
  for n=0,53 do
   if emu.read(n*4+2,emu.memType.snesSpriteRam)==0 and emu.read(n*4+3,emu.memType.snesSpriteRam)==0x2a and emu.read(n*4+1,emu.memType.snesSpriteRam)==116 then hero=n end
  end
  depthChecks=depthChecks+1
  if hero<0 or emu.read((hero+6)*4+2,emu.memType.snesSpriteRam)~=96 then depthFailures=depthFailures+1 end
 end
 local actual={}
 for n=0,53 do
  local ax=emu.read(n*4,emu.memType.snesSpriteRam)
  local ay=emu.read(n*4+1,emu.memType.snesSpriteRam)
  local at=emu.read(n*4+2,emu.memType.snesSpriteRam)+((emu.read(n*4+3,emu.memType.snesSpriteRam)&1)<<8)
  local high=(emu.read(512+math.floor(n/4),emu.memType.snesSpriteRam)>>((n%4)*2))&3
  if (high&1)~=0 then ax=ax-256 end
  actual[string.format('%d,%d,%d,%d',ax,ay,at,high>>1)]=true
 end
 for _,house in ipairs({{196,68},{48,64},{120,40}}) do
  local dy=house[2]-y
  if dy>=-180 and dy<=38 then
   local sy=depths[dy+193]
   local sx=128+math.floor((house[1]-x)*scales[dy+193]/64)
   if sx>=-32 and sx<=287 then
    local size=sy>=130 and 64 or (sy>=95 and 32 or 16)
    local tile=size==64 and 320 or (size==32 and 224 or 450)
    local cells=size==16 and 1 or 4
    local found=true
    for cell=0,cells-1 do
     local ax=sx-size/2+(cell%2)*size/2
     local ay=(sy-size+math.floor(cell/2)*size/2)%256
     local at=tile+cell*size/16
     local large=size==64 and 1 or 0
     local key=string.format('%d,%d,%d,%d',ax,ay,at,large)
     if not actual[key] then found=false end
    end
    houseChecks=houseChecks+1
    if not found then houseFailures=houseFailures+1 end
   end
  end
 end
end
local function dmaWrite(address,value)
 local state=emu.getState()
 local hdma=state['dmaController.hdmaChannels'] or 0
 if (value & hdma) ~= 0 then collisions=collisions+1 end
 if frame>30 and not state['ppu.forcedBlank'] and state['ppu.scanline']<225 then
  visibleDma=visibleDma+1
 end
end
local function layerWrite(address,value)
 local mode=byte(0)
 local dialogue=byte(2)
 local projected=mode==3 or (mode==2 and dialogue~=22 and (dialogue~=0 or byte(3)>=3))
 if not projected then return end
 local state=emu.getState()
 local line=state['ppu.scanline']
 local clock=state['memoryManager.hClock']
 if not state['ppu.forcedBlank'] and line>0 and line<225 and clock>88 and clock<1096 then
  projectedLayerWrites=projectedLayerWrites+1
 end
end
emu.addMemoryCallback(layerWrite,emu.callbackType.write,0x212c)
emu.addMemoryCallback(layerWrite,emu.callbackType.write,0x80212c)
-- The SDK uses DB=$80, whereas the C platform writes long bank-$00 registers.
emu.addMemoryCallback(dmaWrite,emu.callbackType.write,0x420b)
emu.addMemoryCallback(dmaWrite,emu.callbackType.write,0x80420b)
local function publish(address,value)
 if value~=0 and frame>30 and emu.getState()['ppu.scanline']<225 then
  latePublish=latePublish+1
 end
end
emu.addMemoryCallback(publish,emu.callbackType.write,0x420c)
emu.addMemoryCallback(publish,emu.callbackType.write,0x80420c)
emu.addEventCallback(function()
 frame=frame+1
 local mode=byte(0)
 if mode==3 and frame%8==0 and not emu.getState()['ppu.forcedBlank'] then checkSprites() end
 local x,y=byte(34)+byte(35)*256,byte(36)+byte(37)*256
 if x==lastX and y==lastY then steady=steady+1 else steady=0 end
 lastX,lastY=x,y
 if mode==3 and byte(1)==0 and byte(56)>0 and steady>8 and frame%8==0 and not emu.getState()['ppu.forcedBlank'] then checkHouses(x,y) end
 local scenic=mode==2 and byte(2)==0 and byte(3)>=3
 if (mode==3 or scenic) and byte(1)==0 and byte(56)==16 and steady>8 and ((mode==3 and frame%512==0) or (scenic and frame%32==0)) and not emu.getState()['ppu.forcedBlank'] then
  local name='horizon-'..frame
  screenshot(name)
  -- takeScreenshot() reads the asynchronous display decoder. Assert against
  -- the completed PPU buffer, not a potentially older displayed frame.
  local size=emu.getScreenSize()
  local pixels=emu.getScreenBuffer()
  local raw=assert(io.open(output..'/mesen-'..name..'.rgb','wb'))
  raw:write(string.pack('<I4I4',size.width,size.height))
  for n=1,#pixels do local c=pixels[n];raw:write(string.char((c>>16)&255,(c>>8)&255,c&255)) end
  raw:close()
  local file=assert(io.open(output..'/mesen-'..name..'.bin','wb'))
  file:write(string.char(x&255,(x>>8)&255,y&255,(y>>8)&255))
  for n=0,543 do file:write(string.char(emu.read(n,emu.memType.snesSpriteRam))) end
  file:close();horizonSamples=horizonSamples+1
  if scenic then dialogueHorizonSamples=dialogueHorizonSamples+1 end
 end
 local phase=frame%96
 if mode==6 and phase>=20 and phase<=64 and not emu.getState()['ppu.forcedBlank'] then
  journalChecks=journalChecks+1
  local state=emu.getState()
  if state['ppu.bgMode']~=1 or state['ppu.mainScreenLayers']~=5 then journalLayerFailures=journalLayerFailures+1 end
 end
 if mode==6 and previous~=6 then journals=journals+1 end
 if mode==7 and previous~=7 then pauses=pauses+1 end
 previous=mode
 buttons={a=false,b=false,x=false,y=false,start=false,select=false,
          l=false,r=false,up=false,down=false,left=false,right=false}
 if mode==2 and byte(2)==0 and prologHolds[byte(3)]~=nil and prologHolds[byte(3)]<144 then
  prologHolds[byte(3)]=prologHolds[byte(3)]+1
 elseif mode==1 or mode==2 then buttons.a=(frame%24)<8
 elseif mode==12 then buttons.right=true
 elseif mode==3 then
  age=age+1
  if age<20 then buttons.x=true end
  if age<220 then
   buttons.right=(age%120)<60;buttons.left=not buttons.right
  elseif y>110 then buttons.up=true
  elseif journals<12 then buttons.y=phase<8
  elseif pauses<12 then buttons.start=phase<8
  else buttons.l=(frame%256)<8 end
  local second=byte(52)+byte(53)*256
  if second>=644 and not night then night=true;screenshot('night') end
 elseif mode==6 then
  if phase==28 and not overview and not emu.getState()['ppu.forcedBlank'] then
   overview=true;screenshot('journal')
  end
  buttons.right=phase>=32 and phase<40
  if phase==60 and not notes then notes=true;screenshot('notes') end
  buttons.y=phase>=72 and phase<80
 elseif mode==7 then buttons.start=phase>=48 and phase<56
 end
 if frame==@FRAMES@ then
  screenshot('final')
  local file=assert(io.open(output..'/mesen-video.json','w'))
  file:write(string.format('{"frames":%d,"collisions":%d,"visible_dma":%d,"late_publish":%d,'..
   '"journal_checks":%d,"journal_layer_failures":%d,"projected_layer_writes":%d,"dialogue_horizon_samples":%d,"horizon_samples":%d,"torch_depth_checks":%d,"torch_depth_failures":%d,"house_checks":%d,"house_failures":%d,"sprite_overflow":%d,"maximum_tiles_per_scanline":%d,"world_samples":%d,"journal_entries":%d,"pause_entries":%d,"night":%s,"overview":%s,"notes":%s}',
   frame,collisions,visibleDma,latePublish,journalChecks,journalLayerFailures,projectedLayerWrites,dialogueHorizonSamples,horizonSamples,depthChecks,depthFailures,houseChecks,houseFailures,spriteOverflow,maxTiles,worldSamples,journals,pauses,tostring(night),tostring(overview),tostring(notes)))
  file:close()
  emu.stop(journalLayerFailures==0 and journalChecks>=100 and projectedLayerWrites==0 and dialogueHorizonSamples>=6 and horizonSamples>=3 and depthFailures==0 and depthChecks>100 and houseFailures==0 and houseChecks>100 and spriteOverflow==0 and worldSamples>100 and collisions==0 and visibleDma==0 and latePublish==0 and journals>=12 and pauses>=12 and night and notes and 0 or 1)
 end
end,emu.eventType.endFrame)
emu.addEventCallback(function() emu.setInput(buttons,0) end,emu.eventType.inputPolled)
'''


def check_horizon():
    """Compare actual PPU pixels to the authored sky; exclude actual OBJ cells."""
    import sys
    import numpy as np
    from PIL import Image
    sys.path.insert(0,str(ROOT/'tools'))
    from build_backdrop import panorama,COLORS
    palette=np.round(np.array(COLORS)/8)*255/31
    source=palette[np.asarray(panorama(0))]
    compared=corrupt=0
    for path in (ROOT/'build').glob('mesen-horizon-*.bin'):
        data=path.read_bytes();x=int.from_bytes(data[:2],'little');oam=data[4:]
        import struct
        raw=path.with_suffix('.rgb').read_bytes()
        width,height=struct.unpack_from('<II',raw)
        assert (width,height)==(256,239),('Unexpected PPU frame size',width,height)
        pixels=np.frombuffer(raw[8:],dtype=np.uint8).reshape(height,width,3)[7:231].astype(int)
        Image.fromarray(pixels.astype(np.uint8)).save(path.with_name(path.stem+'-ppu.png'))
        mask=np.ones((224,256),dtype=bool)
        for n in range(128):
            sx,sy,_,_=oam[n*4:n*4+4];high=(oam[512+n//4]>>((n%4)*2))&3
            if high&1:sx-=256
            size=32 if high&2 else 16
            if sx<256 and sx+size>0:
                mask[sy:min(224,sy+size),max(0,sx):min(256,sx+size)]=False
        # BG2 VOFS=0 exposes source row1 on visible scanline0. The last
        # parallax band starts at64 and scrolls at one quarter camera speed.
        expected=source[np.arange(65,88)[:,None],(np.arange(256)[None,:]+(x>>2))%256]
        mismatch=np.max(np.abs(pixels[64:87]-expected),axis=2)>8
        compared+=int(np.count_nonzero(mask[64:87]))
        corrupt+=int(np.count_nonzero(mismatch&mask[64:87]))
    assert compared>5000,'Insufficient actual sky pixels captured'
    assert corrupt==0,('Corrupted horizon pixels',corrupt,compared)
    return {'horizon_capture':'ppu','horizon_compared_pixels':compared,'horizon_corrupt_pixels':corrupt}


def run(mesen, frames=15000):
    symbols = (ROOT/'chernorechye.sym').read_text()
    manifest = json.loads((ROOT/'build/link_manifest.json').read_text())
    assert hashlib.sha256(symbols.encode()).hexdigest() == manifest['symbols_sha256'], 'Stale symbols'
    assert hashlib.sha256((ROOT/'chernorechye.sfc').read_bytes()).hexdigest() == manifest['rom_sha256'], 'Stale ROM'
    match = re.search(r'^([0-9a-fA-F]{8}) .*_game$', symbols, re.M)
    assert match, 'Missing game symbol'
    script = SCRIPT.replace('@GAME@', str(int(match[1], 16)-0x7e0000))
    content=(ROOT/'Data/content/perspective.c').read_text()
    for name,marker in [('perspective_y','@DEPTHS@'),('perspective_size','@SCALES@')]:
        values=re.search(name+r'\[241\] = \{([^}]+)',content)[1]
        script=script.replace(marker,'{'+values+'}')
    script = script.replace('@OUTPUT@', json.dumps(str(ROOT/'build')))
    script = script.replace('@FRAMES@', str(frames))
    output = ROOT/'build/mesen-video.json'
    output.unlink(missing_ok=True)
    for sample in (ROOT/'build').glob('mesen-horizon-*'):
        sample.unlink()
    with tempfile.TemporaryDirectory(prefix='chernorechye-mesen-') as temp:
        lua = Path(temp)/'video.lua'
        lua.write_text(script)
        with (ROOT/'build/mesen-video.log').open('w') as log:
            result = subprocess.run([str(mesen), '--testRunner', str(lua),
                                     str(ROOT/'chernorechye.sfc'), '--timeout=180',
                                     '--Debug.ScriptWindow.AllowIoOsAccess=true',
                                     '--Snes.DisableFrameSkipping=true'],
                                    stdout=log, stderr=subprocess.STDOUT, timeout=200)
    assert output.exists(), 'Mesen did not export a report; see build/mesen-video.log'
    report = json.loads(output.read_text())
    assert hashlib.sha256((ROOT/'chernorechye.sfc').read_bytes()).hexdigest() == manifest['rom_sha256'], 'ROM changed during Mesen run'
    report['rom_sha256'] = manifest['rom_sha256']
    report.update(check_horizon())
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    assert result.returncode == 0, 'Mesen detected unsafe DMA or an incomplete route'
    assert report['collisions'] == report['visible_dma'] == report['late_publish'] == 0
    assert report['journal_layer_failures'] == 0 and report['journal_checks'] >= 100
    assert report['projected_layer_writes'] == 0 and report['dialogue_horizon_samples'] >= 6
    assert report['horizon_samples'] >= 3 and report['horizon_corrupt_pixels'] == 0
    assert report['torch_depth_checks'] > 100 and report['torch_depth_failures'] == 0
    assert report['house_checks'] > 100 and report['house_failures'] == 0
    assert report['sprite_overflow'] == 0 and report['maximum_tiles_per_scanline'] <= 34
    assert report['world_samples'] > 100
    assert report['journal_entries'] >= 12 and report['pause_entries'] >= 12
    assert report['night'] and report['notes'] and report['overview']
    print('PASS: Mesen raster ownership, dialogue horizons, journal artwork/layers, DMA and night rendering')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mesen', type=Path, required=True)
    parser.add_argument('--frames', type=int, default=15000)
    args = parser.parse_args()
    run(args.mesen, args.frames)
