"""Five native 32x48 villagers, authored poses and bank-safe idle strips.

Two resident actors share OBJ256..319. Unused cells in their strips hold
the shade, woodpile and barrel, so extra detail needs no additional VRAM.
"""
import struct
from PIL import Image, ImageDraw, ImageFont
from build_scenery import encode, small_asset

COLORS=[(0,0,0),(20,18,20),(40,37,44),(58,39,30),
        (95,62,42),(130,84,51),(170,116,66),(213,165,97),
        (221,203,170),(243,224,190),(146,47,41),(39,49,63),
        (164,105,78),(208,146,108),(244,185,139),(161,158,148)]
NAMES=('dobryn','egor','miroslava','avdey','tikhon')
LABELS=('Добрын · староста','Егор · охотник','Мирослава','Авдей','Тихон')

def canvas(size=(32,48)):
    im=Image.new('P',size,0);im.putpalette([v for c in COLORS for v in c]+[0]*720)
    return im

_imported_frames=None

def actor(role,phase=0):
    global _imported_frames
    if _imported_frames is None:
        from pathlib import Path
        from import_npc_reference import load_reference
        source=Path(__file__).resolve().parents[1]/'assets/characters/villagers-reference.png'
        _imported_frames=load_reference(source,COLORS)
    return _imported_frames[role][phase].copy()

def shade(phase):
    im=canvas((16,32));d=ImageDraw.Draw(im)
    sway=1 if phase==1 else 0
    d.ellipse((2,27,14,31),fill=1)
    d.polygon(((6,1),(10,0),(13,5),(11,10),(12,16),(15,24),
               (12,28),(10,23),(9,31),(7,26),(4,30),(4,21),(1,25),
               (0,20),(3,12),(5,9),(3,6)),fill=1,outline=2)
    d.polygon(((5,11),(10,10),(12,18),(10,24),(7,20),(4,24)),fill=2)
    d.line((6,13,8,15,10,13),fill=11)
    d.line((6,17,9,18,10,16),fill=3)
    d.line((4,12,2,18,1,21+sway),fill=3)
    d.line((11,11,13,17,14,21-sway),fill=3)
    d.line((1,21+sway,0,24),fill=10)
    d.line((14,21-sway,15,23),fill=10)
    d.line((5,5,7,6),fill=10);d.line((9,5,11,4),fill=10)
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
    sheet=canvas((5*32,9*48));far=canvas((80,16))
    for role,name in enumerate(NAMES):
        assembly+=['.section "npc_'+name+'" superfree']
        for phase in range(9):
            im=actor(role,phase);payload=strip(im,legacy,phase)
            # Last resident's padding is decorative and uses scenery palette7.
            if role in (1,4):
                payload.paste(small_asset('woodpile'),(96,0));payload.paste(small_asset('barrel'),(112,0))
            filename='npc-%s-%d.chr'%(name,phase)
            (out/filename).write_bytes(encode(payload))
            assembly+=['npc_frame%d:'%(role*9+phase),'.incbin "assets/generated/'+filename+'"']
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
    print('NPCs: five 32x48 actors, breathing and blink; 46080 ROM bytes / 2048 OBJ bytes; supplied sheet, four facings')
    return far
