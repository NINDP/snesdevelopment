#!/usr/bin/env python3
"""Budget project statics from generated assembler and actual asset sizes.

SDK RAM, CPU stack and APU driver memory are intentionally not called project
statics. WLA's overlapping logical RAM slots are not summed as physical RAM.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def hdma_rows(payload, width):
    rows=[]
    offset=0
    while offset<len(payload):
        count=payload[offset]
        offset+=1
        if not count:
            if offset!=len(payload):
                raise ValueError('Data after HDMA terminator')
            return rows
        if count&128:
            raise ValueError('Expected constant-span direct HDMA records')
        record=payload[offset:offset+width]
        if len(record)!=width:
            raise ValueError('Incomplete HDMA record')
        rows.extend([record]*count)
        offset+=width
    raise ValueError('Missing HDMA terminator')

def report():
    files = [ROOT / 'Data/gameState.asm', *sorted((ROOT / 'Data/core').glob('*.asm')),
             *sorted((ROOT / 'Data/platform').glob('*.asm'))]
    allocations = {}
    sizes = {}
    for path in files:
        entries = re.findall(r'^\s*(\S+) dsb (\d+)\s*$', path.read_text(), re.M)
        allocations[str(path.relative_to(ROOT))] = sum(int(n) for _, n in entries)
        sizes.update({name.split('{WLA_FILENAME}_')[-1]: int(n) for name, n in entries})
    expected = {'text_map': 1792, 'tables': 266, 'heat_tables': 266, 'game': 60}
    for name, size in expected.items():
        if sizes.get(name) != size:
            raise ValueError('Unexpected buffer/state size: ' + name)
    total = sum(allocations.values())
    if total > 3072:
        raise ValueError('Runtime/core static RAM exceeds the 3 KiB review budget')
    initialized_content={}
    for path in sorted((ROOT/'Data/content').glob('*.asm')):
        entries=re.findall(r'^\s*(\S+) dsb (\d+)\s*$',path.read_text(),re.M)
        count=sum(int(n) for _,n in entries)
        if count:initialized_content[str(path.relative_to(ROOT))]=count
    content_bytes=sum(initialized_content.values())
    if total+content_bytes>8192:
        raise ValueError('Runtime plus initialized content exceeds the 8 KiB WRAM review budget')
    symbols=(ROOT/'chernorechye.sym').read_text()
    for suffix in ('_tables','_heat_tables','_text_map'):
        match=re.search(r'^([0-9a-fA-F]{8}) tccs_.*'+suffix+r'$',symbols,re.M)
        if not match or int(match[1],16)>>16!=0x7e:
            raise ValueError('DMA buffer must remain in WRAM bank 7E: '+suffix)
    assets = ROOT / 'assets/generated'
    backgrounds = {p.name: p.stat().st_size for p in assets.glob('bg*.chr')}
    if len(backgrounds) != 6 or max(backgrounds.values()) > 24576:
        raise ValueError('Background tiles exceed reserved VRAM')
    maps = list(assets.glob('bg*.map'))
    if len(maps) != 6 or any(p.stat().st_size != 2048 for p in maps):
        raise ValueError('Expected six 32x32 tile maps')
    dim_maps = list(assets.glob('bg*.dimmap'))
    if len(dim_maps) != 4 or any(p.stat().st_size != 2048 for p in dim_maps):
        raise ValueError('Expected four ambient maps')
    cinematics = {p.name: p.stat().st_size for p in assets.glob('cine*.chr')}
    if len(cinematics) != 3 or cinematics.get('cine0.chr') != 32768 or any(size > (32768 if name == 'cine0.chr' else 24576)
                                    for name, size in cinematics.items()):
        raise ValueError('Cinematic tiles exceed reserved VRAM')
    import struct
    for path in [*assets.glob('cine*.map'), *assets.glob('bg[2-5].map')]:
        payload = path.read_bytes()
        expected_size = 4096 if path.name == 'cine0.map' else 2048
        if len(payload) != expected_size:
            raise ValueError('Unexpected tile map size: ' + path.name)
        entries = struct.unpack('<%dH' % (len(payload) // 2), payload)
        tile_count = path.with_suffix('.chr').stat().st_size // 32
        if any((entry & 1023) >= tile_count or ((entry >> 10) & 7) == 1 for entry in entries):
            raise ValueError('Invalid cinematic tile or reserved UI palette: ' + path.name)
        if path.with_suffix('.pal').stat().st_size != 256:
            raise ValueError('Cinematic palette must contain 128 colors')
    perspective = {p.name: p.stat().st_size for p in assets.glob('perspective[0-3].vram')}
    if len(perspective) != 4 or any(size != 32768 for size in perspective.values()):
        raise ValueError('Expected four interleaved Mode 7 banks')
    for name in perspective:
        payload = (assets / name).read_bytes()
        if max(payload[1::2]) > 127:
            raise ValueError('Mode 7 ground overlaps OBJ palette: ' + name)
    for name in ('perspective-scale.hdma',):
        payload = (assets / name).read_bytes()
        if len(payload) != 673 or payload[-1] != 0 or any(payload[i] != 1 for i in range(0,672,3)):
            raise ValueError('Expected 224 completed Mode 7 scanline records: ' + name)
    light_bytes=0
    for phase in range(16):
        path=assets/('perspective-light%d.hdma'%phase)
        payload=path.read_bytes()
        rows=hdma_rows(payload,4)
        if len(rows)!=224:
            raise ValueError('Torch windows must cover 224 rows')
        for outer_l,outer_r,inner_l,inner_r in rows:
            if inner_l<=inner_r and not outer_l<=inner_l<=inner_r<=outer_r:
                raise ValueError('Inner glow escapes the visibility window')
        light_bytes+=len(payload)
        for cut in (224,128,88,64,16,48,200):
            payload=(assets/('perspective-glow%d-%d.hdma'%(phase,cut))).read_bytes()
            rows=hdma_rows(payload,1)
            if len(rows)!=224 or any(row[0]>15 for row in rows):
                raise ValueError('Invalid torch brightness envelope')
            if any(row[0]!=15 for row in rows[cut:]):
                raise ValueError('Torch brightness must not dim the interface')
            light_bytes+=len(payload)
    font = (assets / 'font.chr').stat().st_size
    sprites = (assets / 'sprites.chr').stat().st_size
    if font > 6144 or sprites > 16384:
        raise ValueError('Font/OBJ tiles overlap a neighbouring VRAM slot')
    hero_frames=list(assets.glob('hero-*.chr'))
    if len(hero_frames)!=32 or any(path.stat().st_size!=1024 for path in hero_frames):
        raise ValueError('Expected 32 streamed 1 KiB hero frames')
    if (assets/'hero.pal').stat().st_size!=32:
        raise ValueError('Hero palette must contain 16 colors')
    hero_addresses=re.findall(r'^([0-9a-fA-F]{8}) hero_frame\d+$',symbols,re.M)
    if len(hero_addresses)!=32 or any((int(addr,16)&0x7fff)>32768-1024 for addr in hero_addresses):
        raise ValueError('Hero frame DMA must not cross a LoROM bank boundary')
    for name in ('torch.chr','torch-oam.bin'):
        if (assets/name).stat().st_size!=4096:
            raise ValueError('Expected a bank-contained 4 KiB torch payload: '+name)
    if (assets/'torch.pal').stat().st_size!=32:
        raise ValueError('Torch palette must contain 16 colors')
    for name in ('torch_tiles','torch_oam_frames'):
        match=re.search(r'^([0-9a-fA-F]{8}) '+name+'$',symbols,re.M)
        if not match or (int(match[1],16)&0x7fff)>32768-4096:
            raise ValueError('Torch DMA/animation data crosses a LoROM bank: '+name)
    samples = sum(p.stat().st_size for p in assets.glob('*.brr'))
    if samples > 4096:
        raise ValueError('BRR payload exceeds the allocated 4 KiB sample region')
    if (ROOT / 'chernorechye.sfc').read_bytes()[0x7fd5] != 0x30:
        raise ValueError('ROM must use FastROM addressing')
    result = {'project_static_bytes': total, 'project_static_limit': 3072,
              'excludes': ['SDK runtime', 'CPU stack', 'APU driver', 'initialized content (reported separately)'],
              'statics_by_module': allocations, 'buffers': expected,
              'initialized_content_by_module': initialized_content,
              'initialized_content_bytes': content_bytes,
              'total_project_wram_bytes': total+content_bytes,
              'total_project_wram_limit': 8192,
              'background_bytes': backgrounds, 'cinematic_bytes': cinematics,
              'perspective_bytes': perspective, 'torch_table_bytes': light_bytes,
              'fastrom': True, 'ambient_map_bytes': 2048, 'font_bytes': font,
              'sprite_bytes': sprites, 'hero_frame_bytes': 1024, 'hero_rom_bytes': 32768,
              'torch_obj_bytes': 4096, 'torch_oam_rom_bytes': 4096,
              'brr_payload_bytes': samples,
              'vram_actual_peak_bytes': max(max(backgrounds.values()) + 4096,
                                             max(size + (4096 if name == 'cine0.chr' else 2048)
                                                 for name, size in cinematics.items())) + font + 2048 + sprites,
              'rom_bytes': (ROOT / 'chernorechye.sfc').stat().st_size}
    (ROOT / 'build/memory.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return result

if __name__ == '__main__':
    report()
