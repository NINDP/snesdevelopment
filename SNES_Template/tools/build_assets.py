#!/usr/bin/env python3
"""Build SNES backgrounds, actors, radial torch sprites and CP1251 UI tiles."""
from pathlib import Path
import struct,math,random
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/generated'
PALETTE=[(0,0,0),(9,16,27),(20,30,43),(35,46,56),(53,67,64),(76,89,70),
(107,115,86),(152,153,112),(203,180,114),(249,218,145),(49,107,111),
(83,165,154),(71,34,50),(133,57,67),(248,104,16),(224,224,198)]
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
    d.line((x-10,y+9,x-3,y+1),fill=5)
    d.line((x+4,y+14,x+12,y+19),fill=3)
    d.line((x-13,y+18,x-6,y+13),fill=6)
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
        d.line((xx+1,y+15,xx+10,y+15),fill=9)
    d.rectangle((x+w-14,y-16,x+w-8,y-5),fill=3,outline=1)
    d.line((x+1,y+h-1,x+w-1,y+h-1),fill=6)
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
def title(frame=0):
    """Main menu: moonlit medieval Chernorechye, chapel and torch."""
    im, d = canvas()
    colors = [
        (4, 5, 10),      # 0 deep shadow
        (11, 12, 24),    # 1 night sky
        (19, 20, 35),    # 2 farther sky
        (29, 28, 44),    # 3 hills
        (41, 40, 53),    # 4 far wood
        (56, 52, 61),    # 5 weathered wood
        (76, 65, 63),    # 6 stones
        (108, 88, 77),   # 7 warm contour
        (156, 117, 75),  # 8 bronze
        (207, 152, 83),  # 9 amber
        (244, 193, 104), # 10 fire
        (255, 226, 150), # 11 fire core
        (90, 89, 112),   # 12 mist
        (47, 54, 69),    # 13 pine
        (24, 29, 40),    # 14 forest
        (212, 207, 184), # 15 moon
    ]
    im.putpalette([v for color in colors for v in color] + [0] * (768 - 48))
    d.rectangle((0, 0, 255, 223), fill=1)

    # Unlit night sky with sparse, hand-dithered stars.
    d.rectangle((0, 0, 255, 92), fill=2)
    d.polygon([(0, 64), (44, 62), (94, 69), (146, 58), (200, 71), (255, 59), (255, 112), (0, 112)], fill=1)
    rng = random.Random(1193)
    for _ in range(28):
        x, y = rng.randrange(8, 248), rng.randrange(9, 73)
        if not (x < 196 and y > 19):
            d.point((x, y), fill=12 if _ % 3 else 7)
    # A hard-edged moon: no gradients and no expensive effects.
    d.ellipse((203, 24, 241, 62), fill=12)
    d.ellipse((207, 27, 237, 57), fill=15)
    d.ellipse((215, 33, 225, 41), fill=12)
    d.point((228, 48), fill=12)
    d.line((203, 62, 240, 62), fill=3)

    # Layered hills and trees behind the chapel.
    d.polygon([(0, 111), (36, 90), (72, 105), (112, 87), (154, 103), (195, 91), (255, 105), (255, 194), (0, 194)], fill=3)
    d.polygon([(0, 137), (38, 112), (77, 127), (123, 108), (160, 131), (203, 112), (255, 127), (255, 202), (0, 202)], fill=14)
    for x, y, r in [(6, 115, 22), (28, 123, 20), (162, 130, 18), (174, 120, 23), (249, 129, 18)]:
        d.rectangle((x-2, y, x+2, y+r+20), fill=0)
        for row, span in ((-30, 4), (-21, 9), (-12, 13), (0, 16)):
            d.polygon([(x, y+row-10), (x-span, y+row+11), (x+span, y+row+11)], fill=13 if x < 170 else 14)
        d.line((x, y-33, x, y+8), fill=4)

    # Timber chapel with wooden cupola and Orthodox cross.
    d.polygon([(175, 114), (215, 85), (255, 114)], fill=0)
    d.polygon([(179, 115), (215, 92), (250, 115)], fill=5)
    for x in range(183, 252, 9):
        d.line((x, 113, 215, 93), fill=4)
    d.rectangle((187, 115, 245, 188), fill=4)
    for y in range(121, 187, 11):
        d.line((188, y, 244, y), fill=6)
    for x in (194, 203, 229, 239):
        d.line((x, 117, x, 188), fill=3)
    d.rectangle((210, 137, 225, 181), fill=0)
    d.rectangle((213, 140, 222, 174), fill=9)
    d.rectangle((216, 142, 220, 172), fill=10)
    d.line((217, 139, 217, 175), fill=0)
    d.line((210, 155, 225, 155), fill=0)
    d.polygon([(205, 88), (215, 76), (225, 88)], fill=5)
    d.rectangle((212, 76, 218, 91), fill=4)
    d.line((215, 63, 215, 81), fill=8, width=2)
    d.line((209, 69, 221, 69), fill=8, width=2)
    d.line((211, 76, 219, 74), fill=8)

    # Stairway leading down; strong perspective with only a few shapes.
    d.polygon([(189, 180), (245, 180), (255, 223), (153, 223)], fill=0)
    for j in range(6):
        y = 181 + j*j + 2*j
        if y > 218: break
        left = 189 - (y - 180)//2
        right = 245 + (y - 180)//3
        d.line((max(0, left), y, min(255, right), y), fill=6 if j%2==0 else 4, width=2)
    d.line((190, 181, 163, 223), fill=6)
    d.line((245, 181, 254, 223), fill=6)

    # Lone wanderer at the entrance, holding a torch.
    d.ellipse((194, 164, 201, 172), fill=0)
    d.polygon([(194, 172), (201, 172), (207, 195), (187, 195)], fill=0)
    d.line((193, 193, 191, 201), fill=0, width=3)
    d.line((201, 193, 205, 200), fill=0, width=3)
    d.line((192, 178, 182, 173), fill=0, width=3)
    d.line((182, 177, 180, 160), fill=7, width=2)
    lean = (0, 1, 2, 1, -1, -2, -1, 1)[frame & 7]
    tip = (149, 147, 148, 150, 148, 147, 149, 148)[frame & 7]
    d.polygon([(180+lean, tip), (179+lean, 153), (176, 157),
               (178, 162), (183, 162), (186, 157), (183, 153)], fill=9)
    d.polygon([(181+lean, tip+3), (178, 157), (180, 161),
               (183, 160), (184, 156)], fill=10)
    d.polygon([(181+lean//2, 154), (179, 158), (181, 161),
               (183, 158)], fill=11)
    # Three embers rise, drift and cool over a sixteen-frame cycle.
    drift = (0, 0, 1, 1, 2, 1, 0, -1)
    for ember in range(3):
        age = (frame + ember*5) & 15
        if age < 13:
            x = 180 + drift[(age+ember*2) & 7] + ember - 1
            y = 153 - age*2
            d.point((x, y), fill=10 if age < 4 else (9 if age < 9 else 8))
            if age < 3:
                d.point((x, y+1), fill=9)

    # Menu slab: fixed dark field for clear Cyrillic overlay text.
    d.rectangle((14, 88, 174, 178), fill=0)
    d.rectangle((16, 90, 172, 176), outline=6)
    d.line((17, 90, 53, 90), fill=8)
    d.line((17, 175, 52, 175), fill=8)
    d.rectangle((17, 101, 19, 164), fill=4)
    for y in (112, 136, 160):
        d.line((36, y, 161, y), fill=3)
    # Simple rune ornaments in empty corners.
    for x, y in ((20, 92), (168, 92), (20, 174), (168, 174)):
        d.point((x, y), fill=10)
    # Top/bottom framing, separated from text region.
    d.line((13, 16, 104, 16), fill=5)
    d.line((112, 16, 162, 16), fill=5)
    d.rectangle((10, 14, 12, 18), fill=8)
    d.rectangle((162, 14, 164, 18), fill=8)
    d.rectangle((0, 198, 255, 223), fill=0)
    d.line((12, 198, 244, 198), fill=6)
    d.line((12, 199, 80, 199), fill=8)
    d.rectangle((242, 197, 244, 200), fill=8)
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
    im,d=canvas(128,256)
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
    # Full-height boatbuilder: four facings, two steps, two 16x16 OBJ parts.
    for facing in range(4):
        for step in range(2):
            x=(facing*2+step)*16; y=48
            d.ellipse((x+3,y+23,x+13,y+27),fill=1)
            d.rectangle((x+5,y+19,x+7,y+26-step),fill=3)
            d.rectangle((x+9,y+19,x+11,y+25+step),fill=3)
            d.line((x+4,y+27-step,x+7,y+27-step),fill=6)
            d.line((x+9,y+26+step,x+12,y+26+step),fill=6)
            d.polygon([(x+5,y+8),(x+11,y+8),(x+13,y+19),
                       (x+3,y+19)],fill=5,outline=1)
            d.line((x+4,y+14,x+12,y+14),fill=7)
            d.rectangle((x+5,y+3,x+10,y+8),fill=8)
            d.rectangle((x+4,y+1,x+11,y+4),fill=3)
            if facing!=0:
                d.point((x+(9 if facing==1 else 6),y+5),fill=1)
                d.line((x+6,y+8,x+10,y+8),fill=3)
            else:
                d.rectangle((x+5,y+4,x+10,y+7),fill=3)
            d.line((x+3,y+10,x+2,y+17),fill=7)
            d.line((x+12,y+10,x+13,y+17),fill=8)
            d.line((x+13,y+10,x+14,y+20),fill=6)
    # Import Kirill and the animated coin from the first game, keeping its alpha.
    fixed=Image.new('P',(1,1)); fixed.putpalette(im.getpalette())
    source=ROOT/'assets/cinematics'
    for n,name in enumerate(('SceneTwoPlayerIdle.png','SceneTwoMainCharacterRunRight1.png')):
        actor=Image.open(source/name).convert('RGBA').resize((16,32),Image.Resampling.NEAREST)
        indexed=actor.convert('RGB').quantize(palette=fixed,dither=Image.Dither.NONE)
        im.paste(indexed,(n*16,96),actor.getchannel('A'))
    for n in range(7):
        actor=Image.open(source/('SceneTwoMainCharacterRunRight%d.png'%(n+1))).convert('RGBA')
        actor=actor.resize((16,32),Image.Resampling.NEAREST)
        im.paste(actor.convert('RGB').quantize(palette=fixed,dither=Image.Dither.NONE),
                 (n*16,192),actor.getchannel('A'))
    for n in range(4):
        coin=Image.open(source/('HudCoinSpin%d.png'%(n+1))).convert('RGBA')
        coin=coin.resize((16,16),Image.Resampling.NEAREST)
        im.paste(coin.convert('RGB').quantize(palette=fixed,dither=Image.Dither.NONE),
                 (n*16,32),coin.getchannel('A'))
    # Four hand-authored flame frames and three tiny ember sprites.
    for frame in range(4):
        x=frame*16; y=80
        lean=(0,1,-1,1)[frame]
        d.line((x+7,y+8,x+9,y+15),fill=6,width=2)
        d.line((x+7,y+9,x+10,y+9),fill=7)
        d.polygon([(x+7+lean,y),(x+5,y+5),(x+3,y+8),(x+5,y+11),
                   (x+10,y+11),(x+12,y+7),(x+9,y+3)],fill=14)
        d.polygon([(x+7+lean,y+3),(x+5,y+8),(x+7,y+11),
                   (x+10,y+9)],fill=9)
        d.line((x+7,y+7,x+8,y+10),fill=15)
    for frame,color in enumerate((15,9,14)):
        x=64+frame*16
        d.point((x+7,84),fill=color)
        if frame<2:d.point((x+8,85),fill=9)
        if frame==0:d.point((x+7,85),fill=15)
    d.line((119,86,121,95),fill=6,width=2)
    d.line((118,87,122,87),fill=7)
    # A tall dissolving silhouette for the gym shot.
    d.ellipse((36,97,43,104),fill=2)
    d.polygon([(36,105),(43,105),(47,124),(33,124)],fill=1,outline=2)
    # Villagers and a full-height enemy occupy the second half of OBJ VRAM.
    for n,coat in enumerate((6,12,10,3,4,1)):
        x=n*16; y=128
        if n==5:
            d.ellipse((x+4,y+1,x+11,y+8),fill=2)
            d.polygon([(x+4,y+9),(x+11,y+9),(x+15,y+28),
                       (x+8,y+25),(x+1,y+28)],fill=1,outline=2)
            d.point((x+6,y+5),fill=11);d.point((x+10,y+5),fill=11)
            continue
        d.ellipse((x+3,y+25,x+13,y+28),fill=1)
        d.rectangle((x+5,y+21,x+7,y+26),fill=3)
        d.rectangle((x+10,y+21,x+12,y+26),fill=3)
        d.polygon([(x+4,y+10),(x+11,y+10),(x+14,y+23),
                   (x+2,y+23)],fill=coat,outline=1)
        d.line((x+6,y+11,x+6,y+20),fill=5 if n!=2 else 11)
        d.rectangle((x+5,y+4,x+11,y+10),fill=8 if n!=2 else 15)
        d.rectangle((x+4,y+2,x+11,y+4),fill=7 if n==0 else (15 if n==2 else 3))
        d.point((x+6,y+6),fill=1);d.point((x+10,y+6),fill=1)
        if n in (0,4):d.line((x+6,y+10,x+10,y+11),fill=3)
        if n==3:
            d.line((x+9,y+13,x+9,y+18),fill=8)
            d.line((x+7,y+15,x+11,y+15),fill=8)
    # Upright Mode 7 scenery uses the previously empty atlas strip at y=160.
    d.rectangle((0,160,127,191),fill=0)
    # Each object is authored in its own cell: branches cannot overwrite a
    # neighbouring tile, an NPC above, or Kirill's animation below this strip.
    pine,pd=canvas(32,32)
    pd.ellipse((3,27,28,31),fill=1)
    pd.polygon([(13,18),(18,18),(19,29),(17,31),(12,30)],fill=3)
    pd.line((14,22,14,29),fill=6)
    pd.line((17,23,17,29),fill=2)
    for points in (
        [(16,0),(11,8),(13,7),(7,14),(10,13),(4,20),(8,19),
         (0,27),(7,26),(4,29),(13,28),(18,28),(27,29),(24,26),
         (31,27),(24,19),(27,20),(21,13),(24,14),(19,7),(21,8)],
    ):
        pd.polygon(points,fill=4,outline=1)
    # Broad dark undersides and broken lighter clusters give the canopy depth.
    pd.line((10,13,14,12,17,13,21,12),fill=2)
    pd.line((5,20,11,19,16,21,23,19),fill=2)
    pd.line((6,26,12,25,17,27,24,25),fill=2)
    for points in (((15,4),(13,8),(16,7)),((12,10),(9,14),(14,12)),
                   ((17,12),(20,15),(16,14)),((9,17),(6,21),(12,19)),
                   ((14,20),(10,24),(16,22)),((6,24),(3,27),(10,25)),
                   ((20,21),(24,24),(19,23))):
        pd.polygon(points,fill=5)
    for x,y in ((15,4),(12,10),(9,17),(6,24),(14,20)):
        pd.line((x,y,x-1,y+2),fill=6)
    im.paste(pine,(0,160))
    # Tile 324: a carved wooden marker, also used for the forest signs.
    marker,md=canvas(16,16)
    md.line((7,10,7,15),fill=3,width=3)
    md.line((6,12,6,15),fill=5)
    md.polygon([(2,2),(12,1),(14,3),(13,11),(2,12),(1,10)],fill=5,outline=1)
    md.line((3,3,11,2),fill=7)
    md.line((3,5,3,10),fill=4)
    md.line((11,4,11,9),fill=3)
    md.line((5,9,7,5,9,9),fill=8)
    md.line((6,8,8,8),fill=7)
    md.point((12,3),fill=3)
    im.paste(marker,(32,160))
    # Tile 326: curled birch bark, kept entirely inside its 16x16 tile.
    note,nd=canvas(16,16)
    nd.polygon([(3,2),(12,1),(14,3),(12,12),(4,14),(1,12)],fill=7,outline=3)
    nd.line((3,2,11,1),fill=8)
    nd.line((2,4,3,11,5,12),fill=6)
    nd.line((12,3,11,10,12,12),fill=5)
    nd.line((5,5,10,4),fill=4)
    nd.line((5,7,8,7),fill=3)
    nd.line((5,9,9,8),fill=4)
    nd.line((3,12,5,13,10,12),fill=8)
    nd.point((9,10),fill=5)
    im.paste(note,(48,160))
    # The lower cell retains a worn rune stone for future scenery placements.
    stone,sd=canvas(16,16)
    sd.ellipse((1,12,14,15),fill=1)
    sd.polygon([(4,1),(10,0),(13,3),(14,12),(10,14),(2,13),(1,5)],fill=3,outline=1)
    sd.line((4,2,9,1,11,3),fill=6)
    sd.line((3,3,2,10,4,12),fill=5)
    sd.line((11,5,12,10,10,12),fill=2)
    sd.line((5,10,7,4,10,10,5,10),fill=8)
    sd.line((4,5,5,6),fill=2)
    sd.point((10,3),fill=4)
    im.paste(stone,(48,176))
    # Tile 328: a log house with a heavy thatched roof and recessed doorway.
    hut,hd=canvas(32,32)
    hd.ellipse((1,27,30,31),fill=1)
    hd.rectangle((3,12,28,29),fill=4,outline=1)
    hd.polygon([(4,13),(15,13),(15,28),(4,28)],fill=5)
    for yy in (15,19,23,27):
        hd.line((4,yy,27,yy),fill=3)
        hd.line((5,yy+1,26,yy+1),fill=6 if yy==19 else 5)
        hd.point((4,yy-1),fill=6)
        hd.point((27,yy+1),fill=2)
    hd.line((5,18,11,18),fill=4)
    hd.line((22,26,26,26),fill=3)
    hd.polygon([(1,14),(15,1),(18,1),(31,14),(30,17),(16,13),(2,17)],fill=5,outline=1)
    hd.polygon([(2,14),(15,2),(16,4),(14,12),(4,15)],fill=6)
    hd.polygon([(16,4),(18,2),(29,14),(20,12)],fill=4)
    for x,y in ((5,13),(8,11),(11,8),(14,5),(18,5),(21,8),(24,11),(27,14)):
        hd.line((x,y,x-1 if x<16 else x+1,y+2),fill=7 if x<16 else 5)
    hd.line((3,15,12,12,16,12,29,15),fill=3)
    hd.line((14,2,18,2),fill=7)
    # Small amber window and deep door have distinct silhouettes at distance.
    hd.rectangle((6,18,12,23),fill=1)
    hd.rectangle((7,19,11,21),fill=8)
    hd.point((7,19),fill=9)
    hd.line((9,19,9,22),fill=3)
    hd.line((6,24,13,24),fill=6)
    hd.rectangle((17,19,24,30),fill=1)
    hd.line((17,18,24,18),fill=6)
    hd.rectangle((19,20,23,29),fill=3)
    hd.line((20,21,20,29),fill=4)
    hd.point((22,25),fill=7)
    hd.line((16,30,25,30),fill=5)
    im.paste(hut,(64,160))
    # Tile 332 is the visible oil jar; its neck must also survive the near LOD.
    jar,jd=canvas(16,16)
    jd.ellipse((2,12,13,15),fill=1)
    jd.polygon([(5,4),(10,4),(13,7),(12,12),(10,14),(5,14),(3,12),(2,8)],fill=5,outline=1)
    jd.polygon([(4,7),(6,5),(7,5),(6,12),(5,12)],fill=7)
    jd.line((10,7,11,10,10,12),fill=4)
    jd.line((4,12,6,13,10,13),fill=6)
    jd.rectangle((5,1,10,4),fill=6,outline=1)
    jd.line((6,1,9,1),fill=8)
    jd.line((6,3,9,3),fill=3)
    jd.line((4,8,11,8),fill=4)
    jd.point((5,7),fill=8)
    im.paste(jar,(96,160))
    # Smaller depth variants are prefiltered once, never scaled by the CPU.
    for n,box in enumerate([(0,160,32,192),(64,160,96,192),(96,160,112,176)]+
                           [(n*16,128,n*16+16,160) for n in range(5)]):
        small=im.crop(box).resize((16,16),Image.Resampling.NEAREST)
        im.paste(small,(n*16,224))
    return im
def torch_table():
    (ROOT/'Data/content').mkdir(parents=True,exist_ok=True)
    widths=[math.isqrt(64*64-y*y) for y in range(65)]
    text=['/* Generated radial torch: 64 pixel radius. */',
          '#include "../include/game.h"',
          'const SkU8 torch_width[TORCH_RADIUS + 1] = {'+
          ','.join(str(x) for x in widths)+'};']
    (ROOT/'Data/content/beam.c').write_text('\n'.join(text)+'\n')

def planar(tile,bpp):
    result=bytearray()
    for pair in range(bpp//2):
        for y in range(8):
            for plane in (pair*2,pair*2+1):
                result.append(sum(((tile[y*8+x]>>plane)&1)<<(7-x) for x in range(8)))
    return bytes(result)

def tile_image(im,dedupe=True,bpp=4,max_tiles=512,palette_tiles=False):
    pixels=list(flat_pixels(im)); w,h=im.size
    tiles=[]; index={}; tilemap=[0]*(1024*max(1,w//256))
    for ty in range(h//8):
        for tx in range(w//8):
            tile=tuple(pixels[(ty*8+y)*w+tx*8+x] for y in range(8) for x in range(8))
            palette=0
            if palette_tiles:
                banks={pixel>>4 for pixel in tile if pixel}
                if len(banks)>1: raise ValueError('An 8x8 tile mixes palette banks')
                palette=next(iter(banks),0)
                tile=tuple(pixel&15 for pixel in tile)
            if not dedupe or tile not in index:
                index[tile]=len(tiles); tiles.append(tile)
            tilemap[(tx//32)*1024+ty*32+tx%32]=index[tile]|(palette<<10)
    if dedupe and len(tiles)>max_tiles: raise ValueError('BG exceeds tile budget: '+str(len(tiles)))
    return b''.join(planar(t,bpp) for t in tiles),struct.pack('<%dH'%len(tilemap),*tilemap)

def menu_torch(tiles, tilemap, assembly):
    # Ten private BG tiles keep animated pixels out of shared/deduplicated tiles.
    # Runtime uploads only this 16x40 patch (320 bytes) during VBlank.
    frames = [tile_image(title(frame).crop((176, 128, 192, 168)), False)[0]
              for frame in range(16)]
    first_tile = len(tiles)//32
    if first_tile + 10 > 768:
        raise ValueError('Menu torch exceeds the background tile budget')
    entries = list(struct.unpack('<1024H', tilemap))
    for row in range(5):
        for column in range(2):
            entries[(16+row)*32 + 22+column] = first_tile + row*2 + column
    (OUT/'menu-torch.chr').write_bytes(b''.join(frames))
    assembly += ['.section "menu_torch" superfree', 'menu_torch_tiles:',
                 '.incbin "assets/generated/menu-torch.chr"', '.ends', '']
    return tiles + frames[0], struct.pack('<1024H', *entries)

def main():
    from build_cinematics import scenes, world_scenes
    OUT.mkdir(parents=True,exist_ok=True)
    assembly=['; Generated by tools/build_assets.py.','.include "hdr.asm"','']
    backgrounds=[splash(),title(),*world_scenes()]
    for i,im in enumerate(backgrounds):
        name='bg%d'%i; tiles,tilemap=tile_image(im,max_tiles=768,palette_tiles=i>=2)
        if i == 1:
            tiles, tilemap = menu_torch(tiles, tilemap, assembly)
        (OUT/(name+'.chr')).write_bytes(tiles); (OUT/(name+'.map')).write_bytes(tilemap)
        im.convert('RGB').save(OUT/(name+'.png'))
        assembly += ['.section "%s" superfree'%name, name+'_tiles:',
                     '.incbin "assets/generated/%s.chr"'%name,name+'_tiles_end:',
                     name+'_map:', '.incbin "assets/generated/%s.map"'%name]
        if i>=1:
            pal=im.getpalette()[:384]
            colors=struct.pack('<128H',*(pal[n]//8+(pal[n+1]//8)*32+(pal[n+2]//8)*1024
                                        for n in range(0,384,3)))
            (OUT/(name+'.pal')).write_bytes(colors)
            assembly += [name+'_palette:','.incbin "assets/generated/%s.pal"'%name]
        assembly += ['.ends','']
        print(name,len(tiles)//32,'tiles')
        if i>=2:
            dim_banks={0:2,3:5,4:6}
            dimmap=struct.pack('<1024H',*((x&1023)|(dim_banks[(x>>10)&7]<<10)
                                          for x in struct.unpack('<1024H',tilemap)))
            (OUT/(name+'.dimmap')).write_bytes(dimmap)
            assembly+=['.section "%s_dim" superfree'%name,name+'_dim:',
                       '.incbin "assets/generated/%s.dimmap"'%name,'.ends','']
    for i,im in enumerate(scenes()):
        name='cine%d'%i; tiles,tilemap=tile_image(im,max_tiles=1024 if i==0 else 768,palette_tiles=True)
        if i==0:
            # Reserve a whole LoROM bank so DMA never crosses a bank boundary.
            tiles=tiles.ljust(32768,b'\0')
        pal=im.getpalette()[:384]
        palette=struct.pack('<128H',*(pal[n]//8+(pal[n+1]//8)*32+(pal[n+2]//8)*1024
                                     for n in range(0,384,3)))
        for extension,payload in (('chr',tiles),('map',tilemap),('pal',palette)):
            (OUT/(name+'.'+extension)).write_bytes(payload)
        im.convert('RGB').save(OUT/(name+'.png'))
        assembly+=['.section "%s" superfree'%name,name+'_tiles:',
                   '.incbin "assets/generated/%s.chr"'%name,name+'_tiles_end:',
                   '.ends', '.section "%s_map" superfree'%name, name+'_map:','.incbin "assets/generated/%s.map"'%name,
                   name+'_palette:','.incbin "assets/generated/%s.pal"'%name,'.ends','']
        print(name,len(tiles)//32,'tiles')
    from build_perspective import build as build_perspective
    build_perspective(OUT,assembly,[v for c in PALETTE for v in c]+[0]*(768-48))
    palette=struct.pack('<16H',*[r//8+(g//8)*32+(b//8)*1024 for r,g,b in PALETTE])
    (OUT/'palette.pal').write_bytes(palette)
    ambient=struct.pack('<16H',*[max(0,r//32)+(max(0,g//32))*32+(max(0,b//24))*1024
                                 for r,g,b in PALETTE])
    (OUT/'ambient.pal').write_bytes(ambient)
    sheet=atlas()
    # Bow OBJ64..95 displaces the silver token; keep it in an unused cell.
    sheet.paste(sheet.crop((0,32,16,48)),(0,240))
    crawler=ImageDraw.Draw(sheet)
    crawler.ellipse((17,251,30,255),fill=1)
    crawler.polygon(((19,247),(22,243),(27,244),(30,247),(28,252),(21,252)),fill=2,outline=3)
    for x in (20,24,28):
        crawler.line((x,249,x-3,251,x-4,254),fill=3)
        crawler.line((x,248,x+2,245,x+1,242),fill=4)
        crawler.line((x-1,247,x+1,248),fill=6)
    crawler.polygon(((25,247),(29,246),(31,249),(28,252),(25,251)),fill=1,outline=2)
    crawler.point((27,248),fill=11);crawler.point((30,249),fill=11)
    crawler.line((27,251,29,251),fill=15)
    tiles,_=tile_image(sheet,False)
    (OUT/'sprites.chr').write_bytes(tiles); sheet.convert('RGB').save(OUT/'sprites.png')
    from build_npcs import build as build_npcs
    npc_far=build_npcs(OUT,assembly,sheet)
    from build_backdrop import build as build_backdrop
    build_backdrop(OUT,assembly)
    from build_scenery import build as build_scenery
    build_scenery(OUT,assembly,sheet,npc_far)
    torch=sheet.crop((0,80,128,96))
    rgba=torch.convert('RGBA')
    mask=Image.new('L',torch.size)
    mask.putdata([255 if pixel else 0 for pixel in flat_pixels(torch)])
    rgba.putalpha(mask)
    rgba.save(OUT/'torch-sheet.png')
    from build_hero import build as build_hero
    build_hero(OUT,assembly)
    from build_bow import build as build_bow
    build_bow(OUT,assembly)
    from build_interactions import build as build_interactions
    build_interactions(OUT,assembly)
    from build_daycycle import build as build_daycycle
    build_daycycle(OUT,assembly)
    from build_torch import build as build_torch
    build_torch(OUT,assembly)
    # Original bitmap CP1251 font: every stroke lands on the 8x8 pixel grid.
    # Color 1 = ink, 2 = panel; IDs stay compatible with all narrative text.
    from build_font import font_tiles
    fonttiles=font_tiles(planar)
    fonttiles.append(planar([2]*64,2)) # tile 256: panel; do not overwrite Cyrillic я
    # A bright optical target on the normal dark UI. The gun still sees a
    # white area around the exact (128,112) aiming point on a physical CRT.
    cross=Image.new('L',(16,16),1); cd=ImageDraw.Draw(cross)
    cd.rectangle((0,0,15,15),outline=3)
    cd.line((1,8,14,8),fill=2); cd.line((8,1,8,14),fill=2)
    cd.rectangle((5,5,11,11),outline=2)
    for ty,tx in ((0,0),(0,1),(1,0),(1,1)):
        fonttiles.append(planar(list(flat_pixels(cross.crop((tx*8,ty*8,tx*8+8,ty*8+8)))),2))
    # Tiles 261..268: gold panel borders; 269/270: filled/empty HUD segments.
    for kind in range(10):
        tile=Image.new('L',(8,8),2); td=ImageDraw.Draw(tile)
        if kind in (0,4,5): td.line((0,1,7,1),fill=3)
        if kind in (1,6,7): td.line((0,6,7,6),fill=3)
        if kind in (2,4,6): td.line((1,0,1,7),fill=3)
        if kind in (3,5,7): td.line((6,0,6,7),fill=3)
        if kind>=8:
            td.rectangle((1,2,6,5),outline=3,fill=3 if kind==8 else 2)
        fonttiles.append(planar(list(flat_pixels(tile)),2))
    (OUT/'font.chr').write_bytes(b''.join(fonttiles))
    assembly += ['.section "sprites" superfree','sprite_tiles:',
                 '.incbin "assets/generated/sprites.chr"','sprite_tiles_end:',
                 'sprite_palette:', '.incbin "assets/generated/palette.pal"','.ends','',
                 '.section "font" superfree','font_tiles:',
                 '.incbin "assets/generated/font.chr"','font_tiles_end:',
                 'bg_palette:','.incbin "assets/generated/palette.pal"','.ends','']
    assembly+=['.section "ambient_palette" superfree','ambient_palette:',
               '.incbin "assets/generated/ambient.pal"','.ends','']
    (ROOT/'Data/content/assets.asm').write_text('\n'.join(assembly))

if __name__=='__main__':
    torch_table()
    main()
