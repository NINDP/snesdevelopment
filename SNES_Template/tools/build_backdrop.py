"""Raster-switched Mode1 panorama above the Mode7 plane, no OBJ cost."""
import math,random,struct
from PIL import Image,ImageDraw
from build_scenery import encode

COLORS=[(0,0,0),(31,46,59),(39,55,66),(49,65,72),(63,78,79),
        (65,83,78),(57,78,71),(48,69,62),(38,59,50),(31,51,41),
        (52,70,48),(89,85,61),(119,103,67),(66,64,48),(153,136,87),(80,94,73)]

def panorama(room):
    im=Image.new('P',(256,88),1);im.putpalette([v for c in COLORS for v in c]+[0]*720)
    d=ImageDraw.Draw(im);rng=random.Random(448+room)
    for y,color in ((16,2),(32,3),(48,4)):d.rectangle((0,y,255,87),fill=color)
    # Cloud banks, distant rolling land and two distinct bands of woodland.
    for x,y,w in ((8,22,56),(136,15,64),(72,33,48),(208,29,40)):
        d.line((x,y,x+w,y),fill=3,width=2);d.line((x+8,y-2,x+w-8,y-2),fill=2)
    points=[(0,64)]+[(x,48+round(5*math.sin(x/43))+rng.randrange(-2,3)) for x in range(0,273,16)]+[(256,88),(0,88)]
    d.polygon(points,fill=5)
    for band,base,color in ((0,67,6),(1,87,8)):
        for x in range(-12,272,8 if room else 12):
            height=rng.choice((12,16,20))+(4 if room else 0)
            y=base-height
            d.polygon(((x+6,y),(x,y+8),(x+2,y+8),(x-3,base-2),(x+15,base-2),(x+10,y+8),(x+12,y+8)),fill=color)
            if band:d.line((x+5,y+6,x+2,base-5),fill=9)
    if room==0:
        # Far fields and roofs remain small enough to read as another hamlet.
        d.polygon(((0,77),(76,70),(135,77),(207,72),(256,77),(256,87),(0,87)),fill=15)
        # Irregular field texture, never full-width horizontal scanline bands.
        for _ in range(90):
            x,y=rng.randrange(256),rng.randrange(77,88)
            d.point((x,y),fill=10 if rng.randrange(3) else 15)
        for x,y in ((18,69),(43,73),(160,68),(184,73),(217,70)):
            d.rectangle((x,y,x+14,y+10),fill=13)
            d.polygon(((x-3,y),(x+6,y-9),(x+17,y),(x+16,y+2),(x-2,y+2)),fill=11)
            d.line((x,y-1,x+6,y-7,x+12,y-1),fill=12)
            d.rectangle((x+4,y+4,x+6,y+6),fill=14)
            d.line((x+10,y+3,x+10,y+10),fill=9)
    return im

def build(out,assembly):
    for room in range(2):
        im=panorama(room);tiles=[bytes(32)];ids={tiles[0]:0};entries=[]
        for y in range(32):
            for x in range(32):
                tile=encode(im.crop((x*8,y*8,x*8+8,y*8+8))) if y<11 else bytes(32)
                if tile not in ids:ids[tile]=len(tiles);tiles.append(tile)
                entries.append(ids[tile]|(4<<10))
        assert len(tiles)<=192,('Backdrop exceeds spare 8 KiB VRAM',len(tiles))
        for suffix,payload in (('chr',b''.join(tiles).ljust(6144,b'\0')),('map',struct.pack('<1024H',*entries))):
            filename='backdrop%d.%s'%(room,suffix)
            (out/filename).write_bytes(payload)
            label='backdrop%d_%s'%(room,'tiles' if suffix=='chr' else 'map')
            assembly+=['.section "'+label+'" superfree',label+':','.incbin "assets/generated/'+filename+'"','.ends']
        im.convert('RGB').save(out/('backdrop%d.png'%room))
        print('Backdrop',room,len(tiles),'Mode1 tiles, three scroll depths')
    data=bytearray()
    for level in range(17):
        for r,g,b in COLORS:
            rgb=[round(c/8*level/16) for c in (r,g,b)]
            data.extend(struct.pack('<H',rgb[0]+rgb[1]*32+rgb[2]*1024))
    (out/'backdrop.pal').write_bytes(data)
    assembly+=['.section "backdrop_palette" superfree','backdrop_palettes:',
               '.incbin "assets/generated/backdrop.pal"','.ends']
