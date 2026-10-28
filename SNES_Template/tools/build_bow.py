"""A bank-contained 1 KiB bow projectile atlas for 16x16 SNES OBJ cells.

The five arrow bases face N, NNE, NE, ENE, E. Mirror them horizontally and/or
vertically for sixteen directions. Top tile IDs are 64,66,68,70,72; impact
frames use 74/76 and the aiming diamond uses 78. Every bottom half is +16.
All cells use the existing hero palette, CGRAM 208..223 / OBJ palette 5.
The generic perspective_obj writer selects it when tile argument has 0x0200.
"""
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw

from build_hero import canvas, planar


def arrow(direction):
    im=canvas((16,16))
    d=ImageDraw.Draw(im)
    angle=direction*math.pi/8
    dx,dy=math.sin(angle),-math.cos(angle)
    px,py=-dy,dx
    def point(along,across=0):
        return round(7.5+dx*along+px*across),round(7.5+dy*along+py*across)
    d.line((point(-6),point(5)),fill=1,width=3)
    d.line((point(-6),point(5)),fill=10)
    d.polygon([point(7),point(2,-2),point(3),point(2,2)],fill=15,outline=11)
    d.line((point(-6,-2),point(-3),point(-6,2)),fill=14)
    d.line((point(-5,-2),point(-2),point(-5,2)),fill=11)
    return im


def impact(faded):
    im=canvas((16,16))
    d=ImageDraw.Draw(im)
    color=10 if faded else 15
    radius=6 if faded else 4
    for direction in range(8):
        angle=direction*math.pi/4
        inner=3 if faded else 1
        d.line((round(7.5+math.cos(angle)*inner),round(7.5+math.sin(angle)*inner),
                round(7.5+math.cos(angle)*radius),round(7.5+math.sin(angle)*radius)),fill=color)
    if not faded:d.rectangle((7,7,8,8),fill=15)
    return im


def marker():
    im=canvas((16,16))
    d=ImageDraw.Draw(im)
    for points in (((7,2),(4,5)),((8,2),(11,5)),((4,10),(7,13)),((11,10),(8,13))):
        d.line(points,fill=15)
    d.point((7,7),fill=14)
    d.point((8,8),fill=14)
    return im


def build(out,assembly):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    atlas=canvas((128,16))
    cells=[arrow(direction) for direction in range(5)]+[impact(False),impact(True),marker()]
    for index,im in enumerate(cells):atlas.paste(im,(index*16,0))
    data=bytearray()
    for y in range(0,16,8):
        for x in range(0,128,8):
            data.extend(planar(list(atlas.crop((x,y,x+8,y+8)).getdata())))
    assert len(data)==1024
    (out/'bow.chr').write_bytes(data)
    atlas.save(out/'bow-sheet.png',transparency=0)
    assembly+=['.section "bow_tiles" superfree','bow_tiles:',
               '.incbin "assets/generated/bow.chr"','.ends','']
    # Live bow UI is a single 192 B copy/DMA, independent of frame-time text
    # formatting. Index = ammo (0..24) + (Scope ? 25 : 0).
    maps=bytearray()
    attributes=(7<<10)|(1<<13)
    for scope in (False,True):
        for ammo in range(25):
            rows=[256|attributes]*96
            for x in range(1,31):
                rows[x]=261|attributes
                rows[64+x]=262|attributes
            for index,tile in ((0,265),(31,266),(32,263),(63,264),(64,267),(95,268)):
                rows[index]=tile|attributes
            if not ammo:
                message='НЕТ СТРЕЛ: ПОПОЛНИ У СОСУДА'
            elif scope:
                message='ЛУК %02d FIRE: ОГОНЬ R: ТОЛЧОК'%ammo
            else:
                message='ЛУК %02d A: ТЕТИВА R: ТОЛЧОК'%ammo
            encoded=message.encode('cp1251')
            assert len(encoded)<=28,(message,len(encoded))
            for index,ch in enumerate(encoded,34):rows[index]=ch|attributes
            maps.extend(struct.pack('<96H',*rows))
    assert len(maps)==9600
    (out/'bow-hud.map').write_bytes(maps)
    assembly+=['.section "bow_hud_maps" superfree','bow_hud_maps:',
               '.incbin "assets/generated/bow-hud.map"','.ends','']
    statuses=('НАТЯЖЕНИЕ [---]', 'НАТЯЖЕНИЕ [=--]', 'НАТЯЖЕНИЕ [==-]',
              'ПОЛНОЕ НАТЯЖЕНИЕ [===]', 'ПЕРЕЗАРЯДКА', 'ТОЛЧОК',
              'УДАР! НАТЯЖЕНИЕ СБИТО', 'ПОПОЛНИ СТРЕЛЫ У СОСУДА')
    status_maps=bytearray()
    for status in statuses:
        row=[256|attributes]*32
        row[0]=263|attributes;row[-1]=264|attributes
        encoded=(' '+status+' ').encode('cp1251')
        assert len(encoded)<=28
        start=(32-len(encoded))//2
        for index,ch in enumerate(encoded,start):row[index]=ch|attributes
        status_maps.extend(struct.pack('<32H',*row))
    assert len(status_maps)==512
    (out/'bow-status.map').write_bytes(status_maps)
    assembly+=['.section "bow_status_maps" superfree','bow_status_maps:',
               '.incbin "assets/generated/bow-status.map"', 'bow_wait_tiles:',
               '.dw '+','.join(str(ch|attributes) for ch in ' ЖДИ  '.encode('cp1251')),'.ends','']
    print('bow atlas',len(data),'ROM bytes, OBJ64..95, five arrow angles plus flips')
    print('bow HUD',len(maps),'ROM bytes, 50 ready-to-copy three-row panels')
