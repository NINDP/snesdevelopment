"""Authored timber chapel: native OBJ textures and a flat Mode 7 floor.

The room swaps the scenery atlas while blank; hero, residents and torch keep
their existing VRAM. Walls are upright 32x64 columns, never floor paintings.
"""
from PIL import Image, ImageDraw
from build_scenery import canvas, encode, small_asset


def cross(d, x, y, color=10, scale=1):
    d.line((x, y, x, y+12*scale), fill=color, width=scale)
    d.line((x-4*scale, y+4*scale, x+4*scale, y+4*scale), fill=color, width=scale)
    d.line((x-2*scale, y+9*scale, x+2*scale, y+8*scale), fill=color, width=scale)


def exterior():
    im=canvas((64,64));d=ImageDraw.Draw(im)
    d.ellipse((2,57,62,63),fill=1)
    d.rectangle((7,35,57,58),fill=7,outline=1)
    for y in range(37,58,4):
        d.line((7,y,57,y),fill=6);d.line((9,y+1,54,y+1),fill=9)
        for x in (6,55):d.rectangle((x,y-1,x+3,y+1),fill=8)
    d.polygon(((2,37),(18,22),(43,22),(62,37),(59,41),(30,36),(4,41)),fill=6,outline=1)
    d.polygon(((5,36),(19,24),(30,24),(28,35),(6,39)),fill=8)
    for x in range(9,29,4):d.line((x,36,x+10,25),fill=10)
    for x in range(34,55,4):d.line((x,26,x+8,36),fill=7)
    d.line((19,22,43,22),fill=11)
    d.rectangle((25,14,39,25),fill=7,outline=1)
    for x in (27,36):d.line((x,15,x,24),fill=10)
    d.rectangle((29,16,34,24),fill=1)
    d.ellipse((29,17,34,22),fill=9);d.line((28,22,35,22),fill=10)
    d.polygon(((22,14),(26,9),(30,7),(34,7),(39,10),(42,14)),fill=8,outline=1)
    d.line((25,13,31,9,37,12),fill=10)
    cross(d,32,0,11)
    for x in (11,44):
        d.rectangle((x,43,x+8,52),fill=1,outline=9)
        d.line((x+1,45,x+7,49),fill=7,width=2)
        d.line((x+1,50,x+7,46),fill=8)
    d.rectangle((25,40,39,59),fill=1,outline=9)
    for x in (28,32,36):d.line((x,42,x,57),fill=7)
    d.point((36,50),fill=11)
    d.rectangle((21,59,43,61),fill=12);d.line((22,59,42,59),fill=13)
    return im


def wall():
    im=canvas((64,64));d=ImageDraw.Draw(im)
    d.rectangle((0,0,63,63),fill=7)
    for y in range(2,61,6):
        d.rectangle((0,y,63,y+3),fill=8)
        d.line((0,y+1,63,y+1),fill=9)
        d.line((0,y+4,63,y+4),fill=6)
        for x in (7+(y%3)*4,39+(y%4)*3):
            d.line((x,y+2,x+9,y+2),fill=7)
        d.ellipse((18,y+1,21,y+3),outline=6)
    d.rectangle((0,0,63,4),fill=6);d.line((0,1,63,1),fill=10)
    for x in (0,30,61):
        d.rectangle((x,4,x+2,60),fill=6);d.line((x,5,x,58),fill=9)
    # Deep boarded window; the interior has no independent daylight source.
    d.rectangle((6,15,25,41),fill=1,outline=10)
    d.line((7,15,24,15),fill=11)
    for y in (20,29,37):
        d.line((8,y,23,y-2),fill=8,width=3)
        d.point((9,y),fill=12);d.point((22,y-2),fill=12)
    d.line((5,42,26,42),fill=9,width=2)
    # Small dark icon with a bronze frame and a hanging cloth.
    d.rectangle((39,17,55,39),fill=6,outline=10)
    d.rectangle((41,19,53,37),fill=1)
    d.ellipse((44,20,51,27),outline=9)
    d.ellipse((46,22,49,26),fill=10)
    d.polygon(((46,27),(50,27),(52,35),(43,35)),fill=8)
    d.line((40,40,54,40),fill=11)
    d.rectangle((40,41,54,47),fill=13)
    for x in (41,45,49,53):d.line((x,46,x,49),fill=10)
    d.rectangle((0,58,63,63),fill=12)
    d.line((0,58,63,58),fill=13)
    for x in (7,27,48):d.line((x,59,x,63),fill=1)
    return im


def side_wall():
    im=wall().crop((0,0,32,64));d=ImageDraw.Draw(im)
    # A long wooden settle sits against the side wall, with visible legs.
    d.rectangle((2,43,29,48),fill=6,outline=1)
    d.line((3,43,28,43),fill=10)
    for x in (4,26):d.rectangle((x,47,x+2,59),fill=7);d.point((x,48),fill=10)
    d.polygon(((1,51),(26,49),(31,53),(5,56)),fill=9,outline=6)
    d.line((4,52,25,51),fill=11)
    return im


def memorial_table():
    im=canvas((32,32));d=ImageDraw.Draw(im)
    d.ellipse((1,27,30,31),fill=1)
    for x in (5,25):d.rectangle((x,17,x+2,29),fill=6);d.line((x,18,x,27),fill=9)
    d.polygon(((1,12),(25,10),(31,15),(6,18)),fill=10,outline=6)
    d.polygon(((3,16),(29,14),(28,25),(5,27)),fill=13,outline=12)
    d.line((5,25,27,23),fill=15)
    for x in (7,11,15,19,23):d.line((x,25,x,28),fill=10)
    # Three cups tie the art to the existing three-part memorial puzzle.
    for x in (9,16,23):
        d.ellipse((x-2,12,x+2,15),fill=8,outline=11)
        d.point((x,13),fill=1)
    cross(d,16,0,10)
    return im


def bells():
    im=canvas((32,32));d=ImageDraw.Draw(im)
    for x in (2,27):d.rectangle((x,3,x+2,30),fill=6);d.line((x,4,x,29),fill=9)
    d.rectangle((1,2,30,5),fill=8,outline=6);d.line((2,2,29,2),fill=11)
    for x,top,bottom in ((8,9,21),(16,8,24),(24,10,20)):
        d.line((x,5,x,top),fill=13)
        d.polygon(((x-2,top),(x+2,top),(x+3,bottom-2),(x+4,bottom),
                   (x-4,bottom),(x-3,bottom-2)),fill=8,outline=6)
        d.line((x-2,top+2,x-2,bottom-2),fill=10)
        d.line((x-3,bottom-1,x+3,bottom-1),fill=11)
        d.line((x,bottom+1,x,bottom+4),fill=13)
    return im


def candle():
    im=canvas((16,16));d=ImageDraw.Draw(im)
    d.ellipse((2,13,13,15),fill=1)
    d.line((8,6,8,13),fill=9,width=2);d.line((4,13,12,13),fill=10)
    for x,y in ((4,6),(8,3),(12,6)):
        d.line((x,y+1,x,9),fill=11);d.point((x,y),fill=10)
        d.point((x,y-1),fill=15)
    d.line((4,9,12,9),fill=9)
    return im


def door():
    im=canvas((16,16));d=ImageDraw.Draw(im)
    d.rectangle((1,0,14,15),fill=6,outline=12)
    d.rectangle((4,2,11,15),fill=1)
    for x in (5,8,11):d.line((x,3,x,14),fill=7)
    for y in (5,12):d.line((4,y,11,y),fill=12)
    d.point((10,9),fill=11)
    return im


def pack_quad(destination, image, x=0):
    size=image.width//2
    for n in range(4):
        xx=(n&1)*size;yy=(n>>1)*size
        destination.paste(image.crop((xx,yy,xx+size,yy+size)),(x+n*size,0))


def publish(out, assembly, name, im):
    (out/(name+'.chr')).write_bytes(encode(im))
    im.save(out/(name+'.png'),transparency=0)
    label=name.replace('-','_')+'_tiles'
    assembly+=['.section "'+label+'" superfree',label+':',
               '.incbin "assets/generated/'+name+'.chr"','.ends']


def build(out, assembly):
    # The exterior stays an authoring reference. In-game the chapel is first
    # visible in the clearing's distant BG2 panorama, beyond Miroslava's forest.
    exterior_image=exterior()
    sheet=canvas((128,96));compact=canvas((128,16))
    timber=wall();side=side_wall();table=memorial_table();rack=bells()
    pack_quad(sheet,timber)
    sheet.paste(side.crop((0,0,32,32)),(0,32))
    sheet.paste(side.crop((0,32,32,64)),(32,32))
    sheet.paste(timber.crop((0,0,32,64)).resize((32,32),Image.Resampling.NEAREST),(64,32))
    sheet.paste(table,(96,32))
    pack_quad(compact,timber.resize((32,32),Image.Resampling.NEAREST))
    pack_quad(compact,rack,64)
    small=[side.resize((16,16),Image.Resampling.NEAREST),
           timber.resize((16,16),Image.Resampling.NEAREST),
           small_asset('jar'),candle(),small_asset('light'),small_asset('rod'),
           small_asset('note'),small_asset('barrel'),
           Image.open(out/'scenery.png').crop((0,80,16,96)),
           Image.open(out/'scenery.png').crop((16,80,32,96)),
           small_asset('grave'),door(),table.resize((16,16),Image.Resampling.NEAREST),
           small_asset('basket'),small_asset('rock'),rack.resize((16,16),Image.Resampling.NEAREST)]
    for n,im in enumerate(small):sheet.paste(im,((n%8)*16,64+(n//8)*16))
    publish(out,assembly,'chapel-scenery',sheet)
    publish(out,assembly,'chapel-compact',compact)
    for name,im in (('chapel-exterior-native',exterior_image),('chapel-wall-native',timber),
                    ('chapel-side-native',side),('chapel-table-native',table),('chapel-bells-native',rack)):
        im.save(out/(name+'.png'),transparency=0)
    print('Chapel interior: timber walls, boarded windows, icons, settles, cups and bell rack; 7168 ROM bytes')
