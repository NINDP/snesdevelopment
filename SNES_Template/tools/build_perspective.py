"""Native Mode 7 ground, ROM HDMA and matching billboard projection tables."""
import math, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HORIZON=32
ANCHOR=164
FOCAL=128
ORIGIN=384
# The camera follows the player. A screen-space pool stays round instead of
# stretching the light to the horizon with the Mode 7 floor.
TORCH_RADII=(78,79,78,77)
OVERLAY_CUTS=(224,128,88,64,16,48,200)

def hdma_rows(rows):
    """Direct HDMA, coalescing identical rows. Never cross its 127-row limit."""
    result=bytearray()
    start=0
    while start<len(rows):
        end=start+1
        while end<len(rows) and rows[end]==rows[start] and end-start<127:
            end+=1
        result.append(end-start)
        result.extend(rows[start])
        start=end
    result.append(0)
    return bytes(result)

def torch_tables(out,assembly):
    from build_hero import FLAME_CENTERS
    from build_torch import PLANTED_FLAME
    centers=(*FLAME_CENTERS,PLANTED_FLAME)
    assembly+=['.section "perspective_torch" superfree']
    for table in range(20):
        radius=TORCH_RADII[table&3]
        center_x,center_y=centers[table>>2]
        windows=[]
        brightness=[]
        inner=radius-22
        for y in range(224):
            dy=y-center_y
            spans=[]
            for r in (radius,inner):
                if abs(dy)>r:
                    spans.extend((255,0))
                else:
                    width=math.isqrt(r*r-dy*dy)
                    spans.extend((center_x-width,center_x+width))
            windows.append(bytes(spans))
            # The inner window is full intensity, the outer annulus uses warm
            # half/subtract color math. A vertical envelope softens both caps.
            width=math.sqrt(max(0,radius*radius-dy*dy))
            brightness.append(round(15*min(1,width/(radius*0.84))))
        name='perspective-light%d'%table
        (out/(name+'.hdma')).write_bytes(hdma_rows(windows))
        assembly+=['perspective_light%d:'%table,
                   '.incbin "assets/generated/'+name+'.hdma"']
        for cut in OVERLAY_CUTS:
            rows=[bytes((value if y<cut else 15,)) for y,value in enumerate(brightness)]
            name='perspective-glow%d-%d'%(table,cut)
            (out/(name+'.hdma')).write_bytes(hdma_rows(rows))
            assembly+=['perspective_glow%d_%d:'%(table,cut),
                       '.incbin "assets/generated/'+name+'.hdma"']
    assembly+=['.ends','']

def ground(room, palette):
    from perspective_materials import build_ground
    return build_ground(room)

def build(out, assembly, palette):
    for room in range(4):
        im=ground(room,palette)
        tiles=[bytes(64)]; ids={tiles[0]:0}; indices=[]
        for y in range(0,224,8):
            for x in range(0,256,8):
                tile=im.crop((x,y,x+8,y+8)).tobytes()
                if tile not in ids:ids[tile]=len(tiles);tiles.append(tile)
                indices.append(ids[tile])
        if len(tiles)>256:raise ValueError('Mode 7 exceeds 256 characters')
        tilemap=bytearray(16384)
        # Extend ground beyond collision boundaries, avoiding a visible square island.
        for y in range(128):
            for x in range(128):tilemap[y*128+x]=indices[(y%4)*32+8+x%4]
        for y in range(28):tilemap[(y+48)*128+48:(y+48)*128+80]=bytes(indices[y*32:y*32+32])
        pixels=b''.join(tiles).ljust(16384,b'\0')
        interleaved=bytearray(32768)
        interleaved[0::2]=tilemap;interleaved[1::2]=pixels
        name='perspective%d'%room
        (out/(name+'.vram')).write_bytes(interleaved)
        im.convert('RGB').save(out/(name+'.png'))
        pal=im.getpalette()[:384]
        (out/(name+'.pal')).write_bytes(struct.pack('<128H',*(pal[i]//8+pal[i+1]//8*32+pal[i+2]//8*1024 for i in range(0,384,3))))
        assembly += ['.section "'+name+'" superfree',name+'_vram:',
                     '.incbin "assets/generated/'+name+'.vram"','.ends','']
        print(name,len(tiles),'Mode 7 characters')
    for room in range(4):
        name='perspective%d'%room
        assembly += ['.section "'+name+'_palette" superfree',name+'_palette:',
                     '.incbin "assets/generated/'+name+'.pal"','.ends','']
    # One pair of coefficients per scanline, read directly by HDMA from ROM.
    scale=bytearray()
    for y in range(224):
        value=round(FOCAL*256/max(1,y-HORIZON))
        # 8.8 signed coefficients must remain in range above the hidden horizon.
        value=min(value,32767)
        scale += bytes((1,))+struct.pack('<H',value)
    scale.append(0)
    (out/'perspective-scale.hdma').write_bytes(scale)
    assembly += ['.section "perspective_tables" superfree','perspective_scale:',
        '.incbin "assets/generated/perspective-scale.hdma"','.ends','']
    torch_tables(out,assembly)
    # dy -192..48: screen projection without any per-frame division or float.
    ys=[];scales=[]
    for dy in range(-192,49):
        sy=round(HORIZON+FOCAL*(ANCHOR-HORIZON)/(FOCAL-dy))
        ys.append(min(255,sy));scales.append(round((sy-HORIZON)*64/FOCAL))
    # Inverse picking for the visible floor, screen rows 48..223.
    invy=[];invscale=[]
    for y in range(48,224):
        invy.append(round(FOCAL*(y-ANCHOR)/(y-HORIZON)))
        invscale.append(round(FOCAL*64/(y-HORIZON)))
    from build_hero import FLAME_CENTERS
    content=['/* Generated Mode 7 camera. Edit tools/build_perspective.py. */','#include "../include/perspective.h"',
             'const SkU8 perspective_light_x[4] = {'+','.join(str(p[0]) for p in FLAME_CENTERS)+'};',
             'const SkU8 perspective_light_y[4] = {'+','.join(str(p[1]) for p in FLAME_CENTERS)+'};']
    for kind,name,values in [('SkU8','perspective_y',ys),('SkU8','perspective_size',scales),
                             ('SkS16','perspective_pick_y',invy),('SkU16','perspective_pick_scale',invscale)]:
        content.append('const '+kind+' '+name+'['+str(len(values))+'] = {'+','.join(map(str,values))+'};')
    import json
    rooms=json.loads((ROOT/'assets/story.json').read_text())['rooms']
    props=[[(256,0),(258,0),(332,2),(328,3),(324,2),(38,2)],
           [(326,2),(260,0),(324,2),(324,2),(358,2),(328,3),(332,2),(324,2),(38,2),(328,3)],
           [(262,0),(264,0),(332,2),(328,3),(328,3),(326,2),(480,2),(326,2),(328,3)],
           [(260,0),(328,3),(38,2),(38,2),(38,2),(328,3),(332,2),(328,3),(38,2)]]
    decor=[[(48,62,328,3),(196,67,328,3)],
           [(x,y+20,320,1) for x,y in [(70,37),(116,36),(166,35),(221,40),(27,74),(150,106),(44,172),(213,174),(244,154)]],
           [(28,68,328,3),(224,68,328,3),(28,120,328,3),(224,120,328,3)],
           [(20,44,324,3),(80,44,324,3),(176,44,324,3),(232,44,324,3)]]
    counts=[]
    for room in range(4):
        objects=[(x,y,*props[room][i]) for i,(x,y,_) in enumerate(rooms[room]['hotspots'])]
        # Decorative crowns must not replace the floor's movement target.
        objects += [(x,y,tile,kind|0x80) for x,y,tile,kind in decor[room]]
        objects.sort(key=lambda obj:obj[1],reverse=True)
        if sum(2 if (obj[3]&0x7f)==0 else 1 for obj in objects)+6>50:
            raise ValueError('Scenery/hero overlap enemy and torch OBJ slots')
        counts.append(len(objects))
        content.append('static const PerspectiveObject objects%d[] = {'%room+','.join('{%d,%d,%d,%d}'%obj for obj in objects)+'};')
    content.append('const PerspectiveObject *const perspective_objects[4] = {objects0,objects1,objects2,objects3};')
    content.append('const SkU8 perspective_counts[4] = {'+','.join(map(str,counts))+'};')
    (ROOT/'Data/content/perspective.c').write_text('\n'.join(content)+'\n')
