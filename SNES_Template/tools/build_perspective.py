"""Native Mode 7 ground, ROM HDMA and matching billboard projection tables."""
import math, struct
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
HORIZON=32
ANCHOR=164
FOCAL=128
ORIGIN=384

def ground(room, palette):
    name=('village','forest','chapel','cellar')[room]
    source=Image.open(ROOT/'assets/cinematics'/(name+'.png')).convert('RGB').resize((256,224),Image.Resampling.LANCZOS)
    x,y=((104,136),(96,144),(96,104),(144,144))[room]
    pattern=source.crop((x,y,x+32,y+32))
    im=Image.new('RGB',(256,224))
    for yy in range(0,224,32):
        for xx in range(0,256,32):im.paste(pattern,(xx,yy))
    d=ImageDraw.Draw(im)
    colors=[tuple(palette[i:i+3]) for i in range(0,48,3)]
    if room==0:
        d.rectangle((88,0,151,72),fill=colors[10])
        for y in range(0,72,8):d.line((90,y,148,y),fill=colors[3])
        for box in ((16,32,79,63),(160,32,231,63)):d.rectangle(box,fill=colors[1])
        d.rectangle((112,64,135,79),fill=colors[5])
    if room==1:
        d.rectangle((0,0,39,128),fill=colors[10])
        for y in range(0,128,8):d.line((0,y,38,y),fill=colors[3])
        d.rectangle((16,136,47,151),fill=colors[5])
        for x in range(16,48,8):d.line((x,136,x,151),fill=colors[3])
    if room==2:
        d.rectangle((104,32,151,47),fill=colors[1])
        d.rectangle((104,56,151,71),fill=colors[5])
        d.rectangle((216,160,239,183),fill=colors[1])
    if room==3:
        for x in (40,120,200):d.rectangle((x,120,x+15,135),fill=colors[4],outline=colors[6])
        d.rectangle((112,48,143,79),fill=colors[1])
    reduced=im.quantize(colors=123,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    result=Image.new('P',im.size)
    full_palette=[0]*768
    local=reduced.getpalette()
    remap=[value+1 if value+1<28 else value+5 for value in range(123)]
    for old,new in enumerate(remap):full_palette[new*3:new*3+3]=local[old*3:old*3+3]
    full_palette[29*3:32*3]=[224,224,192,8,16,24,232,192,120]
    result.putpalette(full_palette)
    result.putdata([remap[value] for value in reduced.getdata()])
    return result

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
    scale=bytearray();window=bytearray()
    for y in range(224):
        value=round(FOCAL*256/max(1,y-HORIZON))
        # 8.8 signed coefficients must remain in range above the hidden horizon.
        value=min(value,32767)
        scale += bytes((1,))+struct.pack('<H',value)
        if y<48:
            a,b=255,0
        else:
            world_dy=FOCAL*(y-ANCHOR)/(y-HORIZON)
            radial_y=world_dy+10
            half=math.sqrt(max(0,64**2-radial_y**2))*(y-HORIZON)/FOCAL if abs(radial_y)<=64 else 0
            a,b=(max(0,math.ceil(128-half)),min(255,math.floor(128+half))) if half else (255,0)
        window += bytes((1,a,b))
    scale.append(0);window.append(0)
    (out/'perspective-scale.hdma').write_bytes(scale)
    (out/'perspective-light.hdma').write_bytes(window)
    assembly += ['.section "perspective_tables" superfree','perspective_scale:',
        '.incbin "assets/generated/perspective-scale.hdma"','perspective_light:',
        '.incbin "assets/generated/perspective-light.hdma"',
        'perspective_fog:', '.db 48,0,16,2,16,4,16,7,16,10,16,13,96,15,0','.ends','']
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
    content=['/* Generated Mode 7 camera. Edit tools/build_perspective.py. */','#include "../include/perspective.h"']
    for kind,name,values in [('SkU8','perspective_y',ys),('SkU8','perspective_size',scales),
                             ('SkS16','perspective_pick_y',invy),('SkU16','perspective_pick_scale',invscale)]:
        content.append('const '+kind+' '+name+'['+str(len(values))+'] = {'+','.join(map(str,values))+'};')
    import json
    rooms=json.loads((ROOT/'assets/story.json').read_text())['rooms']
    props=[[(256,0),(258,0),(332,2),(328,3),(324,2),(38,2)],
           [(326,2),(260,0),(324,2),(324,2),(160,2),(328,3),(332,2),(324,2),(38,2),(328,3)],
           [(262,0),(264,0),(332,2),(328,3),(328,3),(326,2),(64,2),(326,2),(328,3)],
           [(260,0),(328,3),(38,2),(38,2),(38,2),(328,3),(332,2),(328,3),(38,2)]]
    decor=[[(48,62,328,3),(196,67,328,3)],
           [(x,y+20,320,1) for x,y in [(70,37),(116,36),(166,35),(221,40),(27,74),(150,106),(44,172),(213,174),(244,154)]],
           [(28,68,328,3),(224,68,328,3),(28,120,328,3),(224,120,328,3)],
           [(20,44,324,3),(80,44,324,3),(176,44,324,3),(232,44,324,3)]]
    counts=[]
    for room in range(4):
        objects=[(x,y,*props[room][i]) for i,(x,y,_) in enumerate(rooms[room]['hotspots'])]+decor[room]
        objects.sort(key=lambda obj:obj[1],reverse=True)
        counts.append(len(objects))
        content.append('static const PerspectiveObject objects%d[] = {'%room+','.join('{%d,%d,%d,%d}'%obj for obj in objects)+'};')
    content.append('const PerspectiveObject *const perspective_objects[4] = {objects0,objects1,objects2,objects3};')
    content.append('const SkU8 perspective_counts[4] = {'+','.join(map(str,counts))+'};')
    (ROOT/'Data/content/perspective.c').write_text('\n'.join(content)+'\n')
