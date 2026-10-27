"""Five native 32x48 villagers, authored poses and bank-safe idle strips.

Two resident actors share OBJ256..319. Unused cells in their strips hold
the shade, woodpile and barrel, so extra detail needs no additional VRAM.
"""
import struct
from PIL import Image, ImageDraw, ImageFont
from build_scenery import encode, small_asset

COLORS=[(0,0,0),(17,20,23),(30,34,38),(53,49,43),
        (85,57,35),(128,87,46),(165,126,72),(207,183,129),
        (40,65,67),(64,99,95),(115,52,44),(153,185,156),
        (120,77,54),(175,119,78),(216,162,111),(233,213,167)]
NAMES=('dobryn','egor','miroslava','avdey','tikhon')
LABELS=('Добрын · староста','Егор · охотник','Мирослава','Авдей','Тихон')

def canvas(size=(32,48)):
    im=Image.new('P',size,0);im.putpalette([v for c in COLORS for v in c]+[0]*720)
    return im

def actor(role,phase=0):
    im=canvas();d=ImageDraw.Draw(im)
    d.ellipse((5,43,27,47),fill=1)
    # Feet are planted through both idle poses; only the upper body breathes.
    for x in (10,20):
        d.polygon(((x,34),(x+4,34),(x+4,43),(x+6,44),(x+6,46),(x-1,46)),fill=2,outline=1)
        d.line((x,36,x,43),fill=4);d.line((x,45,x+4,45),fill=3)
    body=canvas();p=ImageDraw.Draw(body)
    if role==0: # Broad sheepskin coat, white beard, staff and clasp.
        p.polygon(((8,16),(22,16),(26,30),(24,39),(7,39),(5,28)),fill=4,outline=1)
        p.polygon(((9,18),(14,20),(13,36),(8,36)),fill=5)
        p.line((14,20,15,38),fill=7,width=2);p.line((19,20,19,37),fill=3)
        p.line((8,34,23,34),fill=2,width=2);p.rectangle((14,33,17,35),fill=6)
        p.polygon(((8,17),(12,16),(15,21),(19,16),(22,18),(19,24),(14,22)),fill=7,outline=3)
        p.line((5,22,4,30,7,32),fill=4,width=3)
        p.rectangle((5,29,8,32),fill=13);p.point((6,29),fill=14)
        p.line((27,17,27,45),fill=4,width=2);p.line((26,17,26,42),fill=6)
        p.rectangle((24,27,28,30),fill=13);p.line((24,27,27,27),fill=14)
    elif role==1: # Linen shirt, leather jerkin, red sash, slung hunting bow.
        p.arc((22,9,31,39),270,90,fill=6,width=2);p.line((27,11,27,37),fill=7)
        p.polygon(((8,17),(22,17),(24,31),(22,36),(9,36),(6,29)),fill=7,outline=1)
        p.polygon(((10,17),(14,19),(14,30),(9,32)),fill=4)
        p.polygon(((18,18),(21,17),(23,32),(17,31)),fill=5)
        p.line((15,17,15,24),fill=3);p.line((16,18,16,22),fill=15)
        p.line((8,31,23,31),fill=10,width=3);p.line((18,32,20,39),fill=10,width=2)
        p.line((7,19,5,28,10,31),fill=7,width=3)
        p.line((23,20,25,27,20,30),fill=6,width=3)
        p.rectangle((10,28,14,31),fill=13);p.line((11,28,14,28),fill=14)
        p.rectangle((18,28,21,30),fill=13)
        p.line((9,18,21,31),fill=2,width=2);p.line((10,18,22,30),fill=6)
    elif role==2: # Teal cloak, embroidered ochre skirt, braid and herb pouch.
        p.polygon(((10,17),(22,17),(25,40),(5,40)),fill=5,outline=1)
        for x in (9,14,19):p.line((x,28,x-1,38),fill=4)
        p.line((7,37,23,37),fill=7);p.line((8,39,23,39),fill=10)
        for x in (9,14,19):p.point((x,37),fill=10)
        p.polygon(((8,15),(15,18),(22,15),(26,30),(23,33),(18,24),(15,27),(8,32),(4,29)),fill=8,outline=1)
        p.line((8,18,6,28,12,24),fill=9,width=2);p.line((19,18,23,28),fill=9)
        p.line((15,19,15,26),fill=7);p.ellipse((14,19,17,22),fill=6,outline=4)
        p.rectangle((7,28,10,31),fill=13);p.rectangle((20,28,23,31),fill=13)
        p.ellipse((11,28,20,35),fill=4,outline=1);p.line((13,29,17,29),fill=6)
        for x in (13,15,18):p.line((x,29,x-1,25),fill=9);p.point((x-1,25),fill=11)
    else:
        coat=3 if role==3 else 8
        p.polygon(((9,16),(22,17),(25,40),(6,40)),fill=coat,outline=1)
        p.line((12,20,10,37),fill=4 if role==3 else 9,width=2)
        p.line((17,20,19,38),fill=2);p.line((8,32,23,32),fill=4)
        p.line((6,20,5,28,12,30),fill=coat,width=3)
        p.line((23,21,25,29,18,31),fill=coat,width=3)
        p.rectangle((10,28,14,31),fill=13);p.rectangle((17,29,21,31),fill=13)
        if role==3:
            p.line((16,18,16,29),fill=6);p.line((13,24,19,24),fill=7,width=2)
        else:
            p.rectangle((10,27,21,33),fill=4,outline=1);p.line((12,28,19,28),fill=7)
    # Individually readable faces: warm forehead, nose, cheeks and eye pixels.
    p.polygon(((11,4),(14,2),(19,3),(22,6),(21,13),(18,16),(13,15),(10,11)),fill=12,outline=1)
    p.rectangle((12,6,19,12),fill=13);p.line((13,6,18,6),fill=14)
    p.line((15,9,15,12),fill=12);p.point((16,11),fill=14)
    p.point((12,9),fill=1);p.point((19,9),fill=1)
    if role==0:
        p.polygon(((10,10),(13,12),(16,11),(19,12),(22,10),(21,16),(16,20),(11,16)),fill=7,outline=3)
        p.line((12,13,13,16,16,18),fill=15);p.line((18,13,18,16),fill=6)
        p.line((14,13,18,13),fill=3)
        p.polygon(((9,5),(11,2),(19,1),(23,5),(22,7),(10,7)),fill=3,outline=1)
        p.line((11,3,19,2),fill=5);p.line((10,6,21,6),fill=6)
    elif role==2:
        p.line((10,6,12,3,18,2,21,5,21,12),fill=4,width=2)
        p.line((12,4,18,3),fill=6);p.line((12,14,14,16,18,15),fill=12)
        p.line((20,12,22,17,21,22,23,25),fill=4,width=2)
        for y in (14,18,22):p.point((21,y),fill=6)
        p.line((10,6,21,6),fill=10);p.point((16,6),fill=7)
    elif role==1:
        p.line((10,6,11,3,18,2,21,5,21,8),fill=2,width=2)
        p.line((12,3,17,3),fill=4);p.line((13,13,17,14,20,12),fill=3)
    else:
        p.line((10,6,12,3,19,3,21,6),fill=2,width=2)
        p.polygon(((11,12),(14,13),(18,12),(20,12),(18,18),(14,17)),fill=6 if role==3 else 3)
        if role==3:p.line((12,4,18,4),fill=7)
    if phase==2: # Brief blink, not an alternating permanent closed eye.
        p.line((12,9,13,9),fill=12);p.line((18,9,19,9),fill=12)
    # The staff stays planted while coat/shoulders rise by one pixel.
    im.paste(body,(0,-1 if phase==1 else 0),body.point(lambda c:255 if c else 0,'L'))
    if role==0:
        d.line((26,32,26,45),fill=6);d.line((27,32,27,45),fill=4)
    return im

def shade(phase):
    im=canvas((16,32));d=ImageDraw.Draw(im)
    sway=1 if phase==1 else 0
    d.ellipse((2,27,14,31),fill=1)
    d.polygon(((6,1),(10,0),(13,5),(11,10),(12,16),(15,24),
               (12,28),(10,23),(9,31),(7,26),(4,30),(4,21),(1,25),
               (0,20),(3,12),(5,9),(3,6)),fill=1,outline=2)
    d.polygon(((5,11),(10,10),(12,18),(10,24),(7,20),(4,24)),fill=2)
    d.line((6,13,8,15,10,13),fill=8)
    d.line((6,17,9,18,10,16),fill=3)
    d.line((4,12,2,18,1,21+sway),fill=3)
    d.line((11,11,13,17,14,21-sway),fill=3)
    d.line((1,21+sway,0,24),fill=11)
    d.line((14,21-sway,15,23),fill=11)
    d.line((5,5,7,6),fill=11);d.line((9,5,11,4),fill=11)
    d.point((6,5),fill=15);d.point((10,4),fill=15)
    d.line((7,8,9,8),fill=8)
    return im

def strip(im,legacy,phase):
    sheet=canvas((128,16))
    for n in range(6):sheet.paste(im.crop(((n&1)*16,(n//2)*16,(n&1)*16+16,(n//2)*16+16)),(n*16,0))
    # Both banks contain identical props; the first bank supplies the enemy,
    # the second the woodpile/barrel. All unused cells stay deterministic.
    enemy=shade(phase)
    sheet.paste(enemy.crop((0,0,16,16)),(96,0))
    sheet.paste(enemy.crop((0,16,16,32)),(112,0))
    return sheet

def build(out,assembly,legacy):
    sheet=canvas((5*32,3*48));far=canvas((80,16))
    for role,name in enumerate(NAMES):
        assembly+=['.section "npc_'+name+'" superfree']
        for phase in range(3):
            im=actor(role,phase);payload=strip(im,legacy,phase)
            # Last resident's padding is decorative and uses scenery palette7.
            if role in (1,4):
                payload.paste(small_asset('woodpile'),(96,0));payload.paste(small_asset('barrel'),(112,0))
            filename='npc-%s-%d.chr'%(name,phase)
            (out/filename).write_bytes(encode(payload))
            assembly+=['npc_frame%d:'%(role*3+phase),'.incbin "assets/generated/'+filename+'"']
            sheet.paste(im,(role*32,phase*48))
            if phase==0:far.paste(im.resize((16,16),Image.Resampling.NEAREST),(role*16,0))
        assembly+=['.ends']
    palette=struct.pack('<16H',*(r//8+(g//8)*32+(b//8)*1024 for r,g,b in COLORS))
    (out/'npc.pal').write_bytes(palette)
    assembly+=['.section "npc_palette" superfree','npc_palette:','.incbin "assets/generated/npc.pal"','.ends']
    sheet.save(out/'npc-sheet.png',transparency=0)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    preview=Image.new('RGB',(1000,280),(22,28,27));draw=ImageDraw.Draw(preview)
    for role,label in enumerate(LABELS):
        im=actor(role).convert('RGBA');im.putalpha(actor(role).point(lambda c:255 if c else 0,'L'))
        preview.paste(im.resize((128,192),Image.Resampling.NEAREST),(role*200+36,28),im.resize((128,192),Image.Resampling.NEAREST))
        draw.text((role*200+16,236),label,font=font,fill=(225,210,172))
    preview.save(out/'npc-preview.png')
    print('NPCs: five 32x48 actors, breathing and blink; 15360 ROM bytes / 2048 OBJ bytes')
    return far
