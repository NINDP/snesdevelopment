#!/usr/bin/env python3
"""Budget project statics from generated assembler and actual asset sizes.

SDK RAM, CPU stack and APU driver memory are intentionally not called project
statics. WLA's overlapping logical RAM slots are not summed as physical RAM.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def report():
    files = [ROOT / 'Data/gameState.asm', *sorted((ROOT / 'Data/core').glob('*.asm')),
             *sorted((ROOT / 'Data/platform').glob('*.asm'))]
    allocations = {}
    sizes = {}
    for path in files:
        entries = re.findall(r'^\s*(\S+) dsb (\d+)\s*$', path.read_text(), re.M)
        allocations[str(path.relative_to(ROOT))] = sum(int(n) for _, n in entries)
        sizes.update({name.split('{WLA_FILENAME}_')[-1]: int(n) for name, n in entries})
    expected = {'text_map': 1792, 'tables': 266, 'game': 52}
    for name, size in expected.items():
        if sizes.get(name) != size:
            raise ValueError('Unexpected buffer/state size: ' + name)
    total = sum(allocations.values())
    if total > 3072:
        raise ValueError('Project static RAM exceeds the 3 KiB review budget')
    symbols=(ROOT/'chernorechye.sym').read_text()
    for suffix in ('_tables','_text_map'):
        match=re.search(r'^([0-9a-fA-F]{8}) .*'+suffix+r'$',symbols,re.M)
        if not match or int(match[1],16)>>16!=0x7e:
            raise ValueError('DMA buffer must remain in WRAM bank 7E: '+suffix)
    assets = ROOT / 'assets/generated'
    backgrounds = {p.name: p.stat().st_size for p in assets.glob('bg*.chr')}
    if len(backgrounds) != 6 or max(backgrounds.values()) > 16384:
        raise ValueError('Background tiles exceed reserved VRAM')
    maps = list(assets.glob('bg*.map'))
    if len(maps) != 6 or any(p.stat().st_size != 2048 for p in maps):
        raise ValueError('Expected six 32x32 tile maps')
    font = (assets / 'font.chr').stat().st_size
    sprites = (assets / 'sprites.chr').stat().st_size
    if font > 6144 or sprites > 16384:
        raise ValueError('Font/OBJ tiles overlap a neighbouring VRAM slot')
    samples = sum(p.stat().st_size for p in assets.glob('*.brr'))
    if samples > 4096:
        raise ValueError('BRR payload exceeds the allocated 4 KiB sample region')
    result = {'project_static_bytes': total, 'project_static_limit': 3072,
              'excludes': ['SDK runtime', 'CPU stack', 'APU driver'],
              'statics_by_module': allocations, 'buffers': expected,
              'background_bytes': backgrounds, 'font_bytes': font,
              'sprite_bytes': sprites, 'brr_payload_bytes': samples,
              'vram_actual_peak_bytes': max(backgrounds.values()) + 2048 + font + 2048 + sprites,
              'rom_bytes': (ROOT / 'chernorechye.sfc').stat().st_size}
    (ROOT / 'build/memory.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return result

if __name__ == '__main__':
    report()
