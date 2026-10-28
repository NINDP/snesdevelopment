"""Vsevolod's native 32x48, 16-color actor and bank-safe OBJ frame strips.

Each frame streams into OBJ characters 0..31 as six 16x16 cells. All frames
are authored at final resolution; there is no runtime scaling or quantization.
"""
from pathlib import Path
import struct

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PALETTE = [
    (0, 0, 0), (18, 17, 20), (37, 29, 27), (66, 43, 30),
    (104, 72, 43), (38, 49, 39), (61, 76, 51), (91, 105, 66),
    (122, 129, 83), (111, 98, 72), (160, 145, 106), (197, 182, 137),
    (119, 76, 49), (172, 116, 73), (211, 159, 105), (224, 209, 164),
]
FACING = ('back', 'right', 'front', 'left')
BODY_ORIGIN = (112, 116)
# Left/off hand holds the torch; the right hand is available for a sword.
LEFT_GRIPS = {'back': (7, 26), 'right': (28, 27),
              'front': (24, 28), 'left': (4, 27)}
TORCH_GRIPS = tuple((BODY_ORIGIN[0]+LEFT_GRIPS[face][0],
                    BODY_ORIGIN[1]+LEFT_GRIPS[face][1]) for face in FACING)
FLAME_CENTERS = tuple((x, y-17) for x, y in TORCH_GRIPS)
STRIDE = (-3, -2, 0, 3, 2, 0)
LIFT = (0, 1, 2, 2, 1, 0)


def hand_grips(facing, frame):
    walking = frame >= 2
    phase = frame-2 if walking else 0
    bob = (0, 1, 0, 0, 1, 0)[phase] if walking else frame
    swing = STRIDE[phase] if walking else 0
    torch_on_right = facing in ('front', 'right')
    free_x = 7+swing//2 if torch_on_right else 23-swing//2
    right = (free_x+1, (30 if torch_on_right else 31)+bob)
    left = LEFT_GRIPS[facing]
    return tuple(value+BODY_ORIGIN[index&1]
                 for index,value in enumerate((*left,*right)))


def canvas(size=(32, 48)):
    im = Image.new('P', size, 0)
    im.putpalette([v for color in PALETTE for v in color] + [0] * (768-48))
    return im


def boot(d, x, top, foot, front=True):
    # Rounded leather toe, warm seam and a separate sole are readable at 1x.
    d.polygon([(x, top), (x+5, top), (x+5, foot-3),
               (x+7 if front else x+5, foot-2),
               (x+7 if front else x+6, foot), (x-1, foot),
               (x-1, foot-2), (x, foot-4)], fill=2, outline=1)
    d.line((x+1, top+1, x+1, foot-3), fill=4)
    d.line((x+2, top+1, x+4, top+1), fill=3)
    d.line((x, foot-1, x+5, foot-1), fill=3)
    d.point((x+3, foot-3), fill=4)


def face_front(d, bob):
    y = bob
    # Dark hair frames the forehead; face and beard are distinct silhouettes.
    d.polygon([(11, 5+y), (13, 3+y), (18, 3+y), (21, 6+y),
               (21, 12+y), (19, 16+y), (13, 16+y), (10, 12+y)], fill=12, outline=1)
    d.rectangle((12, 7+y, 19, 12+y), fill=13)
    d.line((13, 7+y, 17, 7+y), fill=14)
    d.point((18, 9+y), fill=14)
    d.line((10, 6+y, 12, 4+y, 18, 4+y, 20, 6+y), fill=2, width=2)
    d.line((12, 4+y, 17, 4+y), fill=3)
    d.line((10, 7+y, 10, 11+y), fill=2)
    d.line((20, 7+y, 20, 11+y), fill=2)
    d.point((12, 9+y), fill=1)
    d.point((18, 9+y), fill=1)
    d.line((15, 10+y, 15, 12+y), fill=12)
    d.point((16, 11+y), fill=14)
    d.polygon([(11, 12+y), (13, 13+y), (14, 12+y), (17, 12+y),
               (18, 13+y), (20, 12+y), (19, 15+y),
               (16, 17+y), (13, 16+y)], fill=2)
    d.line((13, 14+y, 14, 16+y), fill=3)
    d.line((17, 14+y, 17, 16+y), fill=3)
    d.line((14, 13+y, 16, 13+y), fill=1)


def face_back(d, bob):
    y = bob
    d.polygon([(11, 5+y), (13, 3+y), (18, 3+y), (21, 6+y),
               (21, 13+y), (18, 16+y), (12, 15+y), (10, 12+y)], fill=2, outline=1)
    d.line((12, 5+y, 17, 4+y, 19, 6+y), fill=3)
    d.line((12, 7+y, 12, 11+y), fill=3)
    d.line((17, 7+y, 18, 12+y), fill=1)
    d.line((13, 13+y, 17, 14+y), fill=3)
    d.point((10, 10+y), fill=12)
    d.point((21, 10+y), fill=12)


def face_side(d, bob, left=False):
    y = bob
    # Author the profile in a small local cell, then mirror the head alone.
    im = canvas((32, 20))
    p = ImageDraw.Draw(im)
    p.polygon([(12, 5+y), (15, 3+y), (19, 4+y), (21, 7+y),
               (21, 9+y), (23, 10+y), (21, 11+y),
               (21, 14+y), (17, 17+y), (12, 14+y), (10, 10+y)], fill=12, outline=1)
    p.polygon([(15, 7+y), (20, 7+y), (20, 10+y), (22, 10+y),
               (20, 12+y), (17, 13+y), (14, 11+y)], fill=13)
    p.line((17, 7+y, 20, 8+y), fill=14)
    p.point((21, 10+y), fill=14)
    p.line((11, 6+y, 14, 4+y, 18, 4+y, 20, 6+y), fill=2, width=2)
    p.line((12, 5+y, 17, 4+y), fill=3)
    p.rectangle((10, 8+y, 13, 12+y), fill=2)
    p.point((14, 10+y), fill=12)
    p.point((20, 9+y), fill=1)
    p.polygon([(15, 12+y), (18, 13+y), (20, 12+y),
               (21, 13+y), (19, 16+y), (16, 17+y), (13, 14+y)], fill=2)
    p.line((16, 14+y, 17, 16+y), fill=3)
    if left:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def actor(facing, frame, with_hands=True):
    im = canvas()
    d = ImageDraw.Draw(im)
    walking = frame >= 2
    phase = frame-2 if walking else 0
    bob = (0, 1, 0, 0, 1, 0)[phase] if walking else frame
    swing = STRIDE[phase] if walking else 0
    lift = LIFT[phase] if walking else 0
    # A dithered contact shadow does not form a hard rectangular base.
    d.ellipse((5, 44, 27, 47), fill=1)
    for x in (7, 11, 15, 19, 23, 27):
        d.point((x, 47), fill=0)
    front = facing == 'front'
    side = facing in ('right', 'left')
    # Boots, trouser knees and stride overlap are drawn before the coat.
    if side:
        far_x = 13-swing//2
        near_x = 15+swing
        boot(d, far_x, 34+bob, 44-lift, facing == 'right')
        boot(d, near_x, 34+bob, 46-(2-lift if walking else 0), facing == 'right')
        d.polygon([(13, 29+bob), (19, 29+bob), (far_x+4, 38), (far_x, 38)], fill=5, outline=1)
        d.polygon([(16, 29+bob), (21, 30+bob), (near_x+4, 39), (near_x, 39)], fill=6, outline=1)
        d.line((18, 32+bob, near_x+2, 38), fill=7)
    else:
        boot(d, 10+swing//2, 35+bob, 46-lift, front)
        boot(d, 18-swing//2, 35+bob, 46-(2-lift if walking else 0), front)
        d.polygon([(10, 29+bob), (16, 29+bob), (15+swing//2, 38),
                   (10+swing//2, 38)], fill=5, outline=1)
        d.polygon([(17, 29+bob), (22, 29+bob), (22-swing//2, 38),
                   (17-swing//2, 38)], fill=6, outline=1)
        d.line((12, 32+bob, 12+swing//2, 37), fill=7)
        d.line((19, 32+bob, 19-swing//2, 37), fill=7)
    # Layered wool cloak: broad shoulder, broken hem and lengthwise folds.
    d.polygon([(11, 16+bob), (19, 16+bob), (24, 20+bob),
               (23, 28+bob), (25, 34+bob), (18, 33+bob),
               (15, 35+bob), (7, 33+bob), (9, 24+bob), (8, 20+bob)], fill=6, outline=1)
    d.polygon([(10, 18+bob), (14, 18+bob), (13, 29+bob),
               (10, 32+bob), (8, 31+bob)], fill=7)
    d.polygon([(19, 18+bob), (22, 20+bob), (21, 28+bob),
               (23, 32+bob), (19, 31+bob)], fill=5)
    d.line((10, 18+bob, 13, 17+bob, 18, 17+bob), fill=8)
    d.line((9, 32+bob, 13, 33+bob), fill=8)
    d.line((15, 23+bob, 15, 31+bob), fill=5)
    d.line((18, 25+bob, 19, 32+bob), fill=7)
    if facing != 'back':
        # Open front reveals a linen tunic with a tied, stitched collar.
        d.polygon([(14, 17+bob), (18, 17+bob), (20, 28+bob),
                   (17, 31+bob), (12, 29+bob)], fill=10, outline=9)
        d.line((15, 19+bob, 14, 26+bob), fill=11)
        d.line((18, 21+bob, 18, 27+bob), fill=9)
        d.line((14, 18+bob, 16, 20+bob, 18, 18+bob), fill=11)
        d.point((16, 21+bob), fill=4)
        d.point((16, 23+bob), fill=4)
    else:
        d.line((14, 20+bob, 13, 29+bob), fill=8)
        d.line((16, 22+bob, 17, 31+bob), fill=5)
        d.line((10, 24+bob, 10, 29+bob), fill=6)
    # Leather belt and cross-body satchel strap sit above the fabric.
    d.rectangle((10, 28+bob, 22, 30+bob), fill=3)
    d.line((11, 28+bob, 21, 28+bob), fill=4)
    d.rectangle((15, 28+bob, 17, 30+bob), outline=15)
    d.line((11, 17+bob, 21, 29+bob), fill=3, width=2)
    d.line((12, 18+bob, 21, 28+bob), fill=4)
    bag_x = 8 if facing == 'left' else 20
    d.polygon([(bag_x, 28+bob), (bag_x+5, 28+bob),
               (bag_x+6, 34+bob), (bag_x+3, 36+bob), (bag_x-1, 34+bob)], fill=3, outline=1)
    d.line((bag_x, 29+bob, bag_x+4, 29+bob), fill=4)
    d.point((bag_x+3, 31+bob), fill=15)
    if with_hands:
        # Hold the same anatomical left hand in all four views. The wrist is a
        # fixed attachment point; shoulders/elbows absorb breathing and gait.
        torch_on_right = facing in ('front', 'right')
        if torch_on_right:
            free_x = 7 + (swing//2 if walking else 0)
            d.polygon([(9, 19+bob), (11, 21+bob), (free_x+3, 27+bob),
                       (free_x+3, 30+bob), (free_x, 30+bob),
                       (free_x-1, 25+bob)], fill=9, outline=1)
            d.line((8, 21+bob, free_x, 26+bob), fill=11)
            d.rectangle((free_x, 29+bob, free_x+2, 32+bob), fill=13)
            d.point((free_x, 29+bob), fill=14)
        else:
            free_x = 23 - (swing//2 if walking else 0)
            d.polygon([(21, 19+bob), (24, 20+bob), (free_x+3, 25+bob),
                       (free_x+3, 31+bob), (free_x, 32+bob),
                       (free_x-1, 26+bob)], fill=9, outline=1)
            d.line((23, 21+bob, free_x+2, 27+bob), fill=10)
            d.rectangle((free_x, 30+bob, free_x+2, 33+bob), fill=13)
            d.point((free_x+2, 30+bob), fill=14)
        grip = LEFT_GRIPS[facing]
        hx, hy = grip
        if torch_on_right:
            d.polygon([(21, 18+bob), (24, 20+bob), (hx+1, hy-5),
                       (hx+2, hy-1), (hx, hy+1), (hx-3, hy-1),
                       (21, 23+bob)], fill=9, outline=1)
            d.line((23, 20+bob, hx, hy-3), fill=11)
            d.line((hx-2, hy-2, hx+1, hy-2), fill=4)
        else:
            d.polygon([(10, 18+bob), (12, 21+bob), (hx+3, hy-3),
                       (hx+2, hy), (hx-1, hy+1), (hx-2, hy-2),
                       (8, 21+bob)], fill=9, outline=1)
            d.line((9, 20+bob, hx-1, hy-3), fill=11)
            d.line((hx-1, hy-2, hx+2, hy-2), fill=4)
        # These three pixels cover the shaft: the fingers wrap over the wood,
        # while the torch's upper and lower sections meet at the same coordinate.
        d.rectangle((hx-1, hy-1, hx+1, hy+1), fill=13)
        d.line((hx-1, hy-1, hx+1, hy-1), fill=14)
        d.point((hx+1, hy+1), fill=12)
    # Neck, collar and head are drawn last for a stable eye line.
    d.rectangle((13, 14+bob, 18, 17+bob), fill=12)
    d.line((13, 17+bob, 15, 18+bob, 18, 17+bob), fill=11)
    if facing == 'back':
        face_back(d, bob)
    elif facing == 'front':
        face_front(d, bob)
    else:
        head = face_side(d, bob, facing == 'left')
        im.paste(head, (0, 0), head.point(lambda p: 255 if p else 0, 'L'))
    return im


def planar(tile):
    payload = bytearray()
    for pair in range(2):
        for y in range(8):
            for plane in (pair*2, pair*2+1):
                payload.append(sum(((tile[y*8+x] >> plane) & 1) << (7-x) for x in range(8)))
    return bytes(payload)


def frame_strip(im):
    # Six 16x16 cells, laid out in a 128x16 OBJ strip: tile IDs 0,2,..10.
    strip = canvas((128, 16))
    for part in range(6):
        x, y = (part & 1)*16, (part//2)*16
        strip.paste(im.crop((x, y, x+16, y+16)), (part*16, 0))
    payload = bytearray()
    for y in range(0, 16, 8):
        for x in range(0, 128, 8):
            payload.extend(planar(list(strip.crop((x, y, x+8, y+8)).getdata())))
    assert len(payload) == 1024
    return bytes(payload)


def bow_actor(facing, pose):
    """Two hands, one nock and a flexing bow; the torch is planted separately.

    Poses are ready, half draw, full draw and loose. Clothing, face and feet
    come from the idle silhouette; the original held-torch arms are omitted.
    """
    side = facing in ('right', 'left')
    # Draw the left profile from the same coherent stance, then mirror the
    # complete pose so fingers, nock and string stay joined at every stage.
    im = actor('right' if side else facing, 0, with_hands=False)
    d = ImageDraw.Draw(im)
    d.polygon([(5, 18), (9, 17), (11, 29), (9, 34), (6, 32)], fill=3, outline=1)
    d.line((7, 19, 9, 31), fill=4)
    for x in (4, 7, 9):
        d.line((x, 14, x+2, 22), fill=10)
        d.line((x-1, 14, x+1, 16), fill=15)
        d.point((x+1, 13), fill=11)

    def arm(points, hand):
        d.line(points, fill=1, width=5)
        d.line(points, fill=9, width=3)
        d.line(points[:-1], fill=11)
        x, y = hand
        d.rectangle((x-1, y-1, x+1, y+1), fill=13)
        d.point((x, y-1), fill=14)

    def wood(points):
        d.line(points, fill=1, width=3)
        d.line(points, fill=4, width=2)
        d.line(points[1:-1], fill=10)

    if side:
        # Anatomical left hand braces the grip; right draws to the cheek.
        pull = (22, 18, 14, 23)[pose]
        wood([(24, 12), (27, 15), (29, 21), (29, 29), (27, 35), (24, 38)])
        d.line((24, 12, pull, 24, 24, 38), fill=11)
        if pose != 3:
            d.line((pull, 24, 31, 24), fill=10)
            d.polygon([(31, 24), (28, 22), (28, 25)], fill=15)
            d.line((pull, 24, pull+2, 22), fill=15)
            d.point((pull+1, 25), fill=11)
        arm([(20, 20), (24, 24), (28, 25)], (28, 25))
        elbow = (11, 24) if pose == 2 else (13, 26)
        arm([(12, 21), elbow, (pull, 24)], (pull, 24))
        d.line((27, 25, 29, 25), fill=3)
    elif facing == 'back':
        pull = (18, 22, 26, 17)[pose]
        wood([(2, 14), (7, 12), (12, 13), (16, 16), (20, 13), (25, 12), (29, 14)])
        d.line((2, 14, 16, pull, 29, 14), fill=11)
        if pose != 3:
            d.line((16, pull, 16, 8), fill=10)
            d.polygon([(16, 7), (14, 10), (17, 10)], fill=15)
            d.line((16, pull, 14, pull-2), fill=15)
        arm([(10, 21), (12, 19), (16, 17)], (16, 17))
        arm([(23, 21), (23, 26), (16, pull)], (16, pull))
    else:
        pull = (31, 27, 23, 32)[pose]
        wood([(2, 34), (7, 37), (11, 35), (16, 32), (21, 35), (25, 37), (29, 34)])
        d.line((2, 34, 16, pull, 29, 34), fill=11)
        if pose != 3:
            d.line((16, pull, 16, 41), fill=10)
            d.polygon([(16, 42), (14, 39), (17, 39)], fill=15)
            d.line((16, pull, 14, pull+2), fill=15)
        arm([(22, 21), (23, 27), (16, 32)], (16, 32))
        arm([(9, 21), (10, 25), (16, pull)], (16, pull))
    if facing == 'left':
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im


def build(out, assembly):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sheet = canvas((256, 192))
    grips=[]
    for direction, facing in enumerate(FACING):
        # Keep each facing's 8 KiB in its own LoROM section. A 1 KiB DMA can
        # therefore never cross the bank boundary, even after linker packing.
        assembly += ['.section "hero_%s" superfree' % facing]
        for frame in range(8):
            im = actor(facing, frame)
            assert im.size == (32, 48) and max(im.getdata()) < 16
            payload = frame_strip(im)
            name = 'hero-%s-%d.chr' % (facing, frame)
            (out / name).write_bytes(payload)
            index = direction*8+frame
            grips.append(hand_grips(facing,frame))
            assembly += ['hero_frame%d:' % index,
                         '.incbin "assets/generated/%s"' % name]
            sheet.paste(im, (frame*32, direction*48))
        assembly += ['.ends', '']
    palette = struct.pack('<16H', *(r//8+(g//8)*32+(b//8)*1024 for r, g, b in PALETTE))
    (out/'hero.pal').write_bytes(palette)
    assembly += ['.section "hero_palette" superfree', 'hero_palette:',
                 '.incbin "assets/generated/hero.pal"', '.ends', '']
    (ROOT/'Data/content/hero_grips.c').write_text(
        '/* Generated hand attachment points; edit tools/build_hero.py. */\n'
        '#include "../include/hero.h"\nconst SkU8 hero_grips[128] = {'+
        ','.join(str(value) for grip in grips for value in grip)+'};\n')
    sheet.save(out/'hero-sheet.png', transparency=0)
    # Preview all four facings together at a readable integer scale.
    frames=[]
    for frame in (2, 3, 4, 5, 6, 7):
        view=canvas((128,48))
        for direction in range(4):
            view.paste(sheet.crop((frame*32,direction*48,frame*32+32,direction*48+48)),(direction*32,0))
        frames.append(view.resize((384,144),Image.Resampling.NEAREST))
    frames[0].save(out/'hero-walk.gif',save_all=True,append_images=frames[1:],
                   duration=100,loop=0,transparency=0,disposal=2)
    bow_sheet = canvas((256,192))
    for direction, facing in enumerate(FACING):
        assembly += ['.section "hero_bow_%s" superfree' % facing]
        for pose in range(8):
            im = bow_actor(facing,min(pose,3) if pose < 4 else (3 if pose==6 else 0))
            if pose in (4,5):
                walk=actor(facing,2 if pose==4 else 5,with_hands=False)
                im.paste(walk.crop((0,35,32,48)),(0,35))
            elif pose in (6,7):
                # The feet stay planted while shoulders drive the shove or
                # recoil from a blow. All displacement is integer pixels.
                upper=im.crop((0,0,32,35))
                im.paste(0,(0,0,32,35))
                amount=2 if pose==6 else -2
                dx=amount if facing=='right' else (-amount if facing=='left' else 0)
                dy=amount if facing=='front' else (-amount if facing=='back' else 0)
                im.paste(upper,(dx,dy),upper.point(lambda p:255 if p else 0,'L'))
            name = 'bow-hero-%s-%d.chr' % (facing,pose)
            (out/name).write_bytes(frame_strip(im))
            assembly += ['hero_bow_frame%d:' % (direction*8+pose),
                         '.incbin "assets/generated/%s"' % name]
            bow_sheet.paste(im,(pose*32,direction*48))
        assembly += ['.ends','']
    bow_sheet.save(out/'hero-bow-sheet.png',transparency=0)
    bow_frames=[]
    for pose in (0,1,2,2,3,0):
        view=canvas((128,48))
        for direction in range(4):
            view.paste(bow_sheet.crop((pose*32,direction*48,pose*32+32,direction*48+48)),(direction*32,0))
        bow_frames.append(view.resize((512,192),Image.Resampling.NEAREST))
    bow_frames[0].save(out/'hero-bow.gif',save_all=True,append_images=bow_frames[1:],
                       duration=120,loop=0,transparency=0,disposal=2)
    print('hero', len(FACING)*8, 'frames, 32768 ROM bytes, 1024 streamed OBJ bytes')
    print('hero bow',32,'frames, 32768 ROM bytes; draw, footwork, shove and recoil')


if __name__ == '__main__':
    build(ROOT/'assets/generated', [])
