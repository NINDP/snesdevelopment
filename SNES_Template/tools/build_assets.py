#!/usr/bin/env python3
"""Original pixel maps, sprites and precomputed eight-direction beam spans."""
from pathlib import Path
import struct,os,math,random
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/generated'
PALETTE=[(0,0,0),(9,16,27),(20,30,43),(35,46,56),(53,67,64),(76,89,70),
(107,115,86),(152,153,112),(203,180,114),(249,218,145),(49,107,111),
(83,165,154),(71,34,50),(133,57,67),(206,92,88),(224,224,198)]
def flat_pixels(im):
    return im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()

def canvas(w=256,h=224):
    im=Image.new('P',(w,h),0)
    im.putpalette([v for c in PALETTE for v in c]+[0]*(768-48))
    return im,ImageDraw.Draw(im)
def floor(d,material='wood'):
    d.rectangle((8,24,247,191),fill=2)
    if material=='earth':
        # Repeated sparse clusters keep the 4bpp tile budget predictable.
        for y in range(32,184,16):
            for x in range(16,240,16):
                d.point((x,y),fill=3)
                d.line((x+5,y+7,x+7,y+6),fill=4)
        return
    if material=='stone':
        for y in range(24,192,16):
            d.line((8,y,247,y),fill=1)
            for x in range(8+(8 if (y//16)%2 else 0),248,32):
                d.line((x,y,x,y+15),fill=1)
                d.line((x+2,y+2,min(x+25,247),y+2),fill=3)
        return
    for y in range(28,190,12):
        d.line((8,y,247,y),fill=1)
        for x in range(10+(y%24),247,24): d.line((x,y,x,y+11),fill=3)
def tree(d,x,y):
    d.rectangle((x-2,y+9,x+3,y+24),fill=3)
    d.polygon([(x,y-16),(x-15,y+10),(x-7,y+8),(x-20,y+20),(x+20,y+20),(x+7,y+8),(x+15,y+10)],fill=4,outline=1)
    d.line((x,y-10,x-7,y+6),fill=6)
    d.line((x+2,y+2,x+9,y+13),fill=5)
def lamp(d,x,y):
    d.rectangle((x-3,y-5,x+3,y+5),fill=7)
    d.rectangle((x-2,y-3,x+2,y+1),fill=9)
    d.line((x-5,y+6,x+5,y+6),fill=4)
def house(d,x,y,w,h):
    d.rectangle((x,y,x+w,y+h),fill=4,outline=1)
    for yy in range(y+6,y+h,5): d.line((x,yy,x+w,yy),fill=3)
    d.polygon([(x-4,y),(x+w//2,y-19),(x+w+4,y)],fill=6,outline=1)
    for xx in range(x,x+w,7): d.line((xx,y-2,x+w//2,y-17),fill=5)
    d.rectangle((x+w//2-6,y+h-18,x+w//2+6,y+h),fill=1)
    for xx in (x+8,x+w-19):
        d.rectangle((xx,y+5,xx+11,y+16),fill=8)
        d.line((xx+5,y+5,xx+5,y+16),fill=3)
def map_village():
    im,d=canvas(); floor(d,'earth'); house(d,14,33,70,31); house(d,157,34,78,33)
    d.rectangle((88,27,146,76),fill=1)
    d.line((91,27,91,76),fill=5); d.line((144,27,144,76),fill=5)
    for y in range(90,186,16):
        for x in range(100,157,9): d.line((x,y,x+5,y-1),fill=4)
    for x in range(8,249,8): d.line((x,183,x,190),fill=5)
    d.line((8,185,248,185),fill=4)
    d.rectangle((17,132,45,155),fill=3)
    d.line((31,130,31,145),fill=7); d.line((24,135,38,135),fill=7)
    d.rectangle((225,143,244,163),outline=8)
    d.rectangle((88,99,100,110),outline=10); d.line((91,108,97,101),fill=11)
    lamp(d,116,158); d.line((181,120,202,120),fill=12)
    return im
def map_forest():
    im,d=canvas(); floor(d,'earth')
    # A readable earthen path connects the three signs without lighting them.
    d.line((28,144,78,130,116,60,170,117,208,144,232,102),fill=3,width=10)
    d.rectangle((8,25,48,130),fill=10)
    for y in range(28,126,7): d.line((8,y,43,y-2),fill=11)
    for x,y in [(70,37),(116,36),(166,35),(221,40),(27,74),(150,106),(44,172),(213,174),(244,154)]: tree(d,x,y)
    d.line((44,128,44,158),fill=7,width=3); d.line((40,133,48,133),fill=8)
    d.rectangle((53,84,76,108),fill=8)
    d.line((58,88,71,91,59,96,71,100),fill=3)
    d.ellipse((20,140,36,148),outline=11); d.line((21,144,35,144),fill=11)
    d.rectangle((110,52,121,65),fill=7)
    d.line((115,52,115,62),fill=2); d.line((112,55,119,58),fill=2)
    for a in (-5,0,5): d.line((202,146+a,214,142-a),fill=5)
    d.rectangle((227,90,245,114),outline=8)
    d.rectangle((69,153,89,162),fill=6); d.line((73,156,85,159),fill=3)
    d.ellipse((161,110,175,122),outline=11); d.line((163,117,173,114),fill=10)
    d.rectangle((9,33,17,47),outline=7)
    lamp(d,128,166)
    return im
def map_chapel():
    im,d=canvas(); floor(d)
    for x in (12,240):
        d.rectangle((x,24,x+5,184),fill=6)
        for y in range(29,180,8): d.line((x,y,x+5,y),fill=3)
    d.rectangle((89,24,167,49),fill=4); d.line((94,49,162,49),fill=7)
    d.line((128,27,128,44),fill=8,width=3); d.line((120,33,136,33),fill=8,width=2)
    d.rectangle((103,57,153,73),fill=7)
    for x in (111,128,145): d.ellipse((x-4,59,x+4,66),fill=1,outline=8)
    for x in (25,216):
        for y in (62,114): d.rectangle((x,y,x+15,y+6),fill=5)
    d.ellipse((79,118,89,128),fill=8,outline=15)
    d.rectangle((26,143,47,159),fill=6); d.line((29,147,44,152),fill=3)
    d.rectangle((219,158,240,183),fill=1)
    for y in range(161,184,5): d.line((222,y,238,y),fill=4)
    d.line((153,128,191,128),fill=5,width=2)
    for x in (158,172,186):
        d.line((x,128,x,141),fill=6)
        d.ellipse((x-4,138,x+4,147),fill=8,outline=7)
    d.rectangle((216,38,232,56),outline=7)
    lamp(d,126,158)
    return im
def map_dungeon():
    im,d=canvas(); floor(d,'stone'); d.rectangle((12,25,243,47),fill=3)
    for x in range(18,238,18): d.rectangle((x,27,x+12,44),fill=1)
    d.ellipse((105,47,151,89),fill=0,outline=12,width=2)
    d.polygon([(116,53),(128,59),(140,53),(146,65),(128,83),(110,65)],fill=12)
    d.line((122,62,129,76,134,62),fill=14)
    d.ellipse((87,99,168,172),outline=4,width=2)
    for x in (48,128,208):
        d.rectangle((x-10,121,x+10,139),fill=3,outline=6)
        d.line((x-5,131,x,124,x+5,131,x-5,131),fill=8)
    d.rectangle((44,70,66,94),fill=4); d.line((49,75,59,82,49,89),fill=8)
    d.rectangle((181,70,203,94),fill=1,outline=10)
    d.rectangle((77,89,91,103),outline=10); d.line((80,100,84,92,88,100),fill=11)
    d.rectangle((223,157,241,183),fill=1); lamp(d,24,170)
    return im
def title():
    im,d=canvas(); rng=random.Random(1193)
    for _ in range(70): d.point((rng.randrange(256),rng.randrange(100)),fill=rng.choice([2,3,5]))
    d.ellipse((160,25,196,61),fill=7); d.ellipse((149,20,184,57),fill=0)
    for x in range(-16,272,23): tree(d,x,94+(x%3)*6)
    d.rectangle((0,131,255,223),fill=1)
    for y in range(138,224,9): d.line((0,y,255,y),fill=2)
    d.polygon([(71,127),(128,83),(185,127)],fill=3,outline=6)
    d.rectangle((82,128,174,168),fill=2); d.rectangle((117,136,139,168),fill=0)
    d.line((128,92,128,114),fill=8,width=2); d.line((121,99,135,99),fill=8,width=2)
    return im
def splash():
    im,d=canvas()
    d.polygon([(98,58),(158,58),(128,113)],outline=11,width=3)
    d.line((107,66,128,102,149,66),fill=8,width=2)
    d.line((101,59,153,59),fill=15); d.line((86,177,170,177),fill=3)
    for inset,color in ((0,2),(4,3)):
        d.line((74+inset,48,74+inset,119,93,119),fill=color)
        d.line((182-inset,48,182-inset,119,163,119),fill=color)
    return im
def atlas():
    im,d=canvas(128,128)
    for i,color in enumerate([10,10,11,5,12,7,3,1]):
        x=i*16
        if i==7:
            d.polygon([(x+8,1),(x+2,10),(x,15),(x+15,15),(x+13,10)],fill=2)
            d.point((x+6,5),fill=11); d.point((x+10,5),fill=11)
            continue
        d.rectangle((x+5,3,x+10,7),fill=8)
        d.rectangle((x+4,1,x+11,3),fill=3 if i<2 else 6)
        d.polygon([(x+4,7),(x+11,7),(x+13,13),(x+2,13)],fill=color)
        d.line((x+5,14,x+5,15),fill=3)
        d.line((x+10,14,x+10+(i==1),15),fill=3)
        if i<2: d.point((x+14,9),fill=9); d.point((x+14,10),fill=8)
    for i in range(8):
        x=i*16; y=16
        d.ellipse((x+3,y+3,x+12,y+12),fill=8 if i<3 else 11,outline=15)
        if i==0: d.line((x+5,y+10,x+8,y+5,x+11,y+10),fill=3)
        if i==1: d.line((x+8,y+4,x+8,y+11),fill=3); d.line((x+5,y+7,x+11,y+7),fill=3)
        if i==2: d.line((x+4,y+8,x+11,y+8),fill=3)
    d.ellipse((98,36,108,43),fill=1)
    return im
def beam_table():
    (ROOT/'Data/content').mkdir(parents=True,exist_ok=True)
    rows=[]
    for direction in range(8):
        im=Image.new('1',(241,241)); d=ImageDraw.Draw(im)
        angle=direction*math.pi/4
        vx,vy=math.sin(angle),-math.cos(angle); px,py=-vy,vx
        d.polygon([(120,120),(round(120+vx*92+px*34),round(120+vy*92+py*34)),(round(120+vx*92-px*34),round(120+vy*92-py*34))],fill=1)
        d.ellipse((110,110,130,130),fill=1)
        spans=[]
        for yy in range(-96,97,4):
            xs=[x-120 for y in range(120+yy,min(120+yy+4,241)) for x in range(241) if 0<=y<241 and im.getpixel((x,y))]
            spans.append((min(xs),max(xs)) if xs else (255,0))
        rows.append(spans)
    text=['/* Generated 8 directions x 49 four-line bands. */','#include "../include/game.h"','const SkS16 beam_spans[8][49][2] = {']
    for spans in rows: text.append('    {'+','.join('{%d,%d}'%s for s in spans)+'},')
    text.append('};')
    (ROOT/'Data/content/beam.c').write_text('\n'.join(text)+'\n')

def planar(tile,bpp):
    result=bytearray()
    for pair in range(bpp//2):
        for y in range(8):
            for plane in (pair*2,pair*2+1):
                result.append(sum(((tile[y*8+x]>>plane)&1)<<(7-x) for x in range(8)))
    return bytes(result)

def tile_image(im,dedupe=True,bpp=4):
    pixels=list(flat_pixels(im)); w,h=im.size
    tiles=[]; index={}; tilemap=[0]*1024
    for ty in range(h//8):
        for tx in range(w//8):
            tile=tuple(pixels[(ty*8+y)*w+tx*8+x] for y in range(8) for x in range(8))
            if not dedupe or tile not in index:
                index[tile]=len(tiles); tiles.append(tile)
            tilemap[ty*32+tx]=index[tile]
    if dedupe and len(tiles)>512: raise ValueError('BG exceeds reserved 512 tiles')
    return b''.join(planar(t,bpp) for t in tiles),struct.pack('<1024H',*tilemap)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assembly=['; Generated by tools/build_assets.py.','.include "hdr.asm"','']
    backgrounds=[splash(),title(),map_village(),map_forest(),map_chapel(),map_dungeon()]
    for i,im in enumerate(backgrounds):
        name='bg%d'%i; tiles,tilemap=tile_image(im)
        (OUT/(name+'.chr')).write_bytes(tiles); (OUT/(name+'.map')).write_bytes(tilemap)
        im.convert('RGB').save(OUT/(name+'.png'))
        assembly += ['.section "%s" superfree'%name, name+'_tiles:',
                     '.incbin "assets/generated/%s.chr"'%name,name+'_tiles_end:',
                     name+'_map:', '.incbin "assets/generated/%s.map"'%name,'.ends','']
        print(name,len(tiles)//32,'tiles')
    palette=struct.pack('<16H',*[r//8+(g//8)*32+(b//8)*1024 for r,g,b in PALETTE])
    (OUT/'palette.pal').write_bytes(palette)
    sheet=atlas(); tiles,_=tile_image(sheet,False)
    (OUT/'sprites.chr').write_bytes(tiles); sheet.convert('RGB').save(OUT/'sprites.png')
    # CP1251 font. Tiles are 2bpp; color 1 = ink, 2 = panel background.
    candidates=[os.environ.get('SK_FONT',''),
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                '']
    font_path=next((x for x in candidates if x and Path(x).is_file()),None)
    if not font_path: raise RuntimeError('Set SK_FONT to a monospace font with Cyrillic support')
    font=ImageFont.truetype(font_path,9)
    fonttiles=[]
    for i in range(256):
        im=Image.new('L',(8,8),0); d=ImageDraw.Draw(im)
        if i != 0:
            try: ch=bytes([i]).decode('cp1251')
            except UnicodeDecodeError: ch=''
            if i>=32: d.text((1,-2),ch,font=font,fill=255,stroke_width=0)
        pixels=[1 if p>=100 else 2 for p in flat_pixels(im)]
        if i==0: pixels=[0]*64
        fonttiles.append(planar(pixels,2))
    fonttiles.append(planar([2]*64,2)) # tile 256: panel; do not overwrite Cyrillic я
    cross=Image.new('L',(16,16),2); cd=ImageDraw.Draw(cross)
    cd.line((0,8,15,8),fill=1); cd.line((8,0,8,15),fill=1)
    cd.rectangle((4,4,12,12),outline=1)
    for ty,tx in ((0,0),(0,1),(1,0),(1,1)):
        fonttiles.append(planar(list(flat_pixels(cross.crop((tx*8,ty*8,tx*8+8,ty*8+8)))),2))
    (OUT/'font.chr').write_bytes(b''.join(fonttiles))
    assembly += ['.section "sprites" superfree','sprite_tiles:',
                 '.incbin "assets/generated/sprites.chr"','sprite_tiles_end:',
                 'sprite_palette:', '.incbin "assets/generated/palette.pal"','.ends','',
                 '.section "font" superfree','font_tiles:',
                 '.incbin "assets/generated/font.chr"','font_tiles_end:',
                 'bg_palette:','.incbin "assets/generated/palette.pal"','.ends','']
    (ROOT/'Data/content/assets.asm').write_text('\n'.join(assembly))

if __name__=='__main__':
    beam_table()
    main()
