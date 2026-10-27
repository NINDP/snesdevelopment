"""Native pixel scenery, sized against the 32x48 actor rather than icons.

Mode7 patches the spare OBJ32..63, OBJ224..255 and OBJ320..511. NPC bodies,
hero, bow and torch keep their own authored atlas regions and palettes.
"""
import struct
from PIL import Image, ImageDraw

COLORS=[(0,0,0),(18,24,22),(25,39,29),(38,57,35),(61,78,43),
        (89,103,56),(49,34,25),(76,48,29),(109,72,39),(151,111,57),
        (180,145,82),(209,181,112),(68,73,65),(111,116,96),
        (92,128,119),(196,211,171)]

def canvas(size):
    im=Image.new('P',size,0);im.putpalette([v for c in COLORS for v in c]+[0]*720)
    return im

def house():
    im=canvas((64,64));d=ImageDraw.Draw(im)
    d.ellipse((2,55,61,63),fill=1)
    d.rectangle((7,27,57,58),fill=7,outline=1)
    d.polygon(((7,28),(39,28),(39,57),(7,57)),fill=8)
    d.polygon(((40,28),(57,29),(57,56),(40,57)),fill=6)
    for y in range(31,58,5):
        d.line((7,y,57,y),fill=6);d.line((9,y+1,37,y+1),fill=9)
        d.ellipse((5,y-2,10,y+2),fill=7,outline=6)
        d.ellipse((55,y-2,59,y+2),fill=7,outline=1)
        d.line((13+(y%3)*4,y+3,29+(y%4)*2,y+3),fill=7)
    d.polygon(((1,27),(24,4),(41,2),(63,28),(60,35),(34,30),(4,35)),fill=7,outline=1)
    d.polygon(((3,27),(25,5),(33,6),(30,27),(5,32)),fill=10)
    d.polygon(((34,6),(41,4),(60,28),(36,27)),fill=8)
    # Broken thatch bundles follow the actual two roof slopes.
    for row in range(6):
        y=9+row*4
        left=24-row*4
        for x in range(max(5,left),32,5):
            d.line((x,y,x-3,y+4),fill=11 if (x+row)%3 else 9)
        for x in range(37,42+row*3,5):d.line((x,y,x+2,y+4),fill=9)
    d.line((25,4,40,3),fill=11,width=2)
    d.line((4,33,31,28,60,33),fill=6,width=2)
    d.rectangle((12,37,25,48),fill=1)
    d.rectangle((14,39,23,45),fill=10)
    d.line((18,38,18,47),fill=7);d.line((13,43,24,43),fill=7)
    d.line((11,49,27,49),fill=9)
    d.rectangle((34,34,48,59),fill=1)
    d.rectangle((37,37,46,57),fill=6)
    for x in (39,43):d.line((x,38,x,56),fill=8)
    d.line((34,34,48,34),fill=10,width=2)
    d.point((44,47),fill=11)
    d.rectangle((31,58,51,60),fill=12);d.line((32,58,50,58),fill=13)
    return im

def pine():
    im=canvas((32,64));d=ImageDraw.Draw(im)
    d.ellipse((4,59,28,63),fill=1)
    d.polygon(((13,28),(18,28),(20,60),(17,63),(11,60)),fill=6,outline=1)
    d.line((14,40,14,60),fill=8);d.line((17,45,18,59),fill=7)
    for cx,top,width,height in ((16,0,10,19),(15,10,18,23),(17,21,25,26),(15,32,31,23)):
        left=cx-width//2;right=cx+width//2;bottom=top+height
        d.polygon(((cx,top),(left+3,bottom-6),(left,bottom-1),(cx-4,bottom-3),
                   (cx,bottom),(right-3,bottom-3),(right,bottom-1)),fill=2,outline=1)
        d.polygon(((cx,top+3),(left+4,bottom-5),(cx-2,bottom-7),(cx+3,bottom-4)),fill=3)
        for yy in range(top+7,bottom-3,5):
            reach=max(2,(yy-top)*width//height//2)
            d.line((cx-reach,yy,cx-2,yy+1,cx+2,yy,cx+reach-2,yy+1),fill=4)
            if yy%2:d.line((cx-reach+2,yy-1,cx-2,yy),fill=5)
    return im

def small_asset(kind):
    im=canvas((16,16));d=ImageDraw.Draw(im)
    d.ellipse((2,12,14,15),fill=1)
    if kind=='jar':
        d.polygon(((5,3),(10,3),(13,7),(12,13),(9,15),(5,14),(2,10),(3,6)),fill=8,outline=6)
        d.line((4,7,5,12,7,13),fill=10);d.line((11,7,11,12),fill=7)
        d.rectangle((5,1,10,4),fill=9,outline=6);d.line((4,8,11,8),fill=7)
    elif kind in ('water','rod','light'):
        d.rectangle((6,9,9,15),fill=7)
        d.polygon(((2,1),(12,1),(14,3),(13,11),(2,12),(1,9)),fill=8,outline=6)
        d.line((3,2,11,2),fill=10)
        if kind=='water':
            d.line((3,6,5,4,7,6,9,4,11,6),fill=15);d.line((3,9,5,7,7,9,9,7,11,9),fill=13)
        elif kind=='rod':
            d.line((7,3,7,9),fill=15);d.line((4,4,10,4),fill=15);d.line((4,8,7,10,10,8),fill=13)
        else:
            d.ellipse((5,4,10,9),outline=15);d.line((7,2,7,3),fill=11);d.point((12,6),fill=11)
    elif kind=='note':
        d.polygon(((3,1),(13,2),(12,12),(4,14),(2,11)),fill=11,outline=8)
        for y in (4,7,10):d.line((5,y,10,y),fill=7)
        d.line((3,2,4,12),fill=10)
    elif kind=='grave':
        d.polygon(((4,1),(11,0),(13,4),(12,14),(3,14),(2,4)),fill=7,outline=6)
        d.line((5,2,10,2),fill=10);d.line((7,4,7,11),fill=13);d.line((4,6,10,6),fill=13)
    elif kind=='echo':
        d.polygon(((3,5),(8,1),(13,5),(14,12),(8,15),(2,12)),fill=12,outline=6)
        d.line((5,11,5,6,7,4,7,10,9,6,10,10,12,9),fill=14)
        d.point((7,4),fill=15)
    elif kind=='gate':
        d.rectangle((1,3,3,15),fill=7);d.rectangle((12,1,14,15),fill=7)
        d.line((1,3,13,1),fill=10,width=2);d.line((4,7,11,7),fill=8)
        d.line((7,4,10,6,7,8),fill=11)
    elif kind=='fence':
        for x in (1,8,14):d.rectangle((x,4,x+1,15),fill=7);d.point((x,3),fill=10)
        d.line((1,8,14,7),fill=9,width=2);d.line((1,12,14,11),fill=8)
    elif kind=='stump':
        d.polygon(((4,5),(12,5),(14,13),(10,15),(2,13)),fill=7,outline=6)
        d.ellipse((3,2,13,8),fill=10,outline=8);d.ellipse((5,4,10,6),outline=7)
        d.line((4,9,4,12),fill=9)
    elif kind=='fern':
        for x,y in ((1,6),(4,3),(8,1),(12,4),(15,8)):
            d.line((8,15,x,y),fill=3);d.line((x,y,x,y+3),fill=5)
    elif kind=='woodpile':
        for x,y in ((3,10),(8,10),(5,6),(11,9),(9,4)):
            d.polygon(((x-2,y),(x+2,y-3),(x+5,y-1),(x+1,y+3)),fill=7,outline=6)
            d.ellipse((x-2,y,x+2,y+4),fill=10,outline=8);d.point((x,y+2),fill=7)
    elif kind=='barrel':
        d.polygon(((4,3),(11,3),(13,7),(12,13),(9,15),(4,14),(2,10),(2,6)),fill=8,outline=6)
        d.ellipse((3,1,12,5),fill=10,outline=7)
        d.line((5,6,5,12),fill=10);d.line((9,6,9,13),fill=7)
        d.line((3,6,12,6),fill=12);d.line((3,12,12,12),fill=12)
    elif kind=='basket':
        d.arc((4,1,12,10),180,360,fill=9,width=2)
        d.polygon(((2,7),(14,7),(12,14),(4,14)),fill=9,outline=6)
        for y in (9,12):d.line((4,y,12,y),fill=7)
        for x in (5,9,12):d.line((x,8,x-1,13),fill=10)
        d.ellipse((4,5,9,9),fill=4);d.ellipse((8,5,12,8),fill=5)
    else: # Weathered rock / sealed node.
        d.polygon(((4,2),(11,1),(14,6),(12,13),(3,14),(1,8)),fill=12,outline=1)
        d.line((4,3,10,2,12,5),fill=13);d.line((5,10,7,5,10,11,5,10),fill=15)
    return im

def stone_arch():
    im=canvas((32,32));d=ImageDraw.Draw(im)
    d.polygon(((3,31),(3,10),(9,3),(22,3),(28,11),(28,31)),fill=12,outline=1)
    d.polygon(((10,30),(10,13),(14,9),(19,9),(22,14),(22,30)),fill=1)
    for y in (12,18,24,30):d.line((4,y,9,y),fill=6);d.line((23,y,27,y),fill=6)
    d.line((8,7,13,4,21,4),fill=13);d.line((4,11,4,29),fill=13)
    d.line((13,15,16,11,19,15,16,20,13,15),fill=14)
    return im

def well():
    im=canvas((32,32));d=ImageDraw.Draw(im)
    d.ellipse((3,22,29,31),fill=1)
    d.rectangle((4,17,27,26),fill=12,outline=1)
    d.ellipse((4,13,27,24),fill=13,outline=12);d.ellipse((8,16,23,21),fill=1)
    for x in (8,20):d.line((x,23,x,27),fill=6)
    for x in (5,25):d.rectangle((x,4,x+2,18),fill=7);d.line((x,4,x,16),fill=9)
    d.polygon(((1,6),(15,0),(30,6),(28,9),(15,5),(3,9)),fill=8,outline=6)
    d.line((3,6,15,1,27,6),fill=10);d.line((16,6,16,17),fill=11)
    d.rectangle((14,17,18,21),fill=8,outline=6)
    return im

def encode(im):
    data=bytearray()
    for y in range(0,im.height,8):
        for x in range(0,im.width,8):
            pixels=list(im.crop((x,y,x+8,y+8)).getdata())
            for pair in range(2):
                for yy in range(8):
                    for plane in (pair*2,pair*2+1):
                        data.append(sum(((pixels[yy*8+xx]>>plane)&1)<<(7-xx) for xx in range(8)))
    return bytes(data)

def build(out,assembly,legacy,npc_far):
    sheet=canvas((128,96));low=canvas((128,16));compact=canvas((128,16))
    hut=house();tree=pine()
    for n in range(4):
        x=(n&1)*32;y=(n>>1)*32
        sheet.paste(hut.crop((x,y,x+32,y+32)),(n*32,0))
    sheet.paste(tree.crop((0,0,32,32)),(0,32));sheet.paste(tree.crop((0,32,32,64)),(32,32))
    sheet.paste(tree.resize((32,32),Image.Resampling.NEAREST),(64,32))
    sheet.paste(stone_arch(),(96,32))
    for n,image in enumerate((hut.resize((32,32),Image.Resampling.NEAREST),well())):
        for part in range(4):
            x=(part&1)*16;y=(part>>1)*16
            compact.paste(image.crop((x,y,x+16,y+16)),((n*4+part)*16,0))
    small=[tree.resize((16,16),Image.Resampling.NEAREST),hut.resize((16,16),Image.Resampling.NEAREST),
           *[small_asset(x) for x in ('jar','water','rod','light','note','grave')],
           legacy.crop((0,240,16,256)),legacy.crop((16,240,32,256)),
           *[small_asset(x) for x in ('echo','gate','rock','stump','fern','rock')]]
    small[-1]=well().resize((16,16),Image.Resampling.NEAREST)
    for n,im in enumerate(small):sheet.paste(im,((n%8)*16,64+(n//8)*16))
    low.paste(npc_far,(0,0));low.paste(small_asset('basket'),(80,0))
    low.paste(small_asset('fence'),(96,0));low.paste(small_asset('stump'),(112,0))
    for name,im,size in (('scenery',sheet,6144),('scenery-low',low,1024),('scenery-compact',compact,1024)):
        data=encode(im);assert len(data)==size
        (out/(name+'.chr')).write_bytes(data);im.save(out/(name+'.png'),transparency=0)
        label=name.replace('-','_')+'_tiles'
        assembly+=['.section "'+label+'" superfree',label+':','.incbin "assets/generated/'+name+'.chr"','.ends']
    palette=struct.pack('<16H',*(r//8+(g//8)*32+(b//8)*1024 for r,g,b in COLORS))
    (out/'scenery.pal').write_bytes(palette)
    assembly+=['.section "scenery_palette" superfree','scenery_palette:',
               '.incbin "assets/generated/scenery.pal"','.ends']
    hut.save(out/'house-native.png',transparency=0);tree.save(out/'pine-native.png',transparency=0)
    print('Native scenery: 64x64 house, 32x64 pine, well, depth variants, 8192 OBJ bytes')
