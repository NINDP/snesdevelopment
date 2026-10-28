"""Native 16-color torch, two transparent dither halos and five ember trails.

The 128x64 atlas replaces only OBJ96..223 during Mode7. A precomputed 4KiB
OAM animation table keeps particle motion out of the 65C816 drawing loop.
"""
from pathlib import Path
import math
import struct

from PIL import Image, ImageDraw
from build_hero import TORCH_GRIPS, FLAME_CENTERS

ROOT = Path(__file__).resolve().parents[1]
PALETTE = [
    (0, 0, 0), (30, 19, 15), (68, 36, 20), (113, 62, 28),
    (159, 97, 45), (96, 80, 58), (170, 146, 101), (78, 75, 65),
    (157, 151, 121), (176, 44, 12), (232, 80, 12), (255, 137, 22),
    (255, 193, 64), (255, 229, 135), (255, 248, 205), (108, 51, 17),
]
FACING = ('back', 'right', 'front', 'left')
GRIPS = TORCH_GRIPS
# Stem grips are at(8,26), flame cores at(8,9) inside each16x32 sprite.
FLAMES = FLAME_CENTERS
PLANTED_GRIP = (106, 162)
PLANTED_FLAME = (106, 145)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
DRIFT = (0, 0, 1, 1, 2, 1, 0, -1, -2, -1, 0, 1, 2, 2, 1, 0,
         -1, -2, -3, -2, -1, 0, 1, 2, 3, 2, 1, 0, -1, -1, 0, 1)


def canvas(size):
    im = Image.new('P', size, 0)
    im.putpalette([v for c in PALETTE for v in c] + [0]*(768-48))
    return im


def flame(frame):
    im = canvas((16, 32))
    d = ImageDraw.Draw(im)
    # Charred wood, long split shaft, cord wrap and a forged iron fire basket.
    d.polygon([(7, 13), (9, 13), (10, 30), (8, 31), (6, 30)], fill=2, outline=1)
    d.line((7, 17, 8, 30), fill=3)
    d.line((8, 18, 9, 29), fill=4)
    d.line((7, 21, 8, 22, 7, 24), fill=2)
    for y in (20, 23, 26, 29):
        d.line((7, y, 9, y-1), fill=5)
        d.point((7, y), fill=6)
    d.polygon([(4, 11), (11, 11), (11, 15), (9, 17), (6, 17), (4, 14)], fill=7, outline=1)
    d.line((5, 13, 10, 13), fill=8)
    d.line((6, 15, 9, 15), fill=5)
    d.point((5, 12), fill=14)
    # Eight asymmetrical silhouettes share a stable bright core and attachment.
    lean = (-1, 0, 1, 2, 1, 0, -1, -2)[frame]
    tip = (1, 2, 0, 1, 2, 1, 0, 1)[frame]
    d.polygon([(8+lean, tip), (10+lean, 4), (10, 6), (12, 5),
               (13, 9), (12, 12), (10, 14), (6, 14), (3, 11),
               (3, 8), (5, 5), (5, 8), (7, 5)], fill=9)
    d.polygon([(8+lean, tip+2), (9+lean, 5), (9, 7), (11, 7),
               (12, 10), (10, 13), (6, 13), (4, 10), (6, 7),
               (7, 8)], fill=10)
    d.polygon([(8+lean//2, 5), (9, 8), (11, 10), (9, 13),
               (6, 12), (5, 10), (7, 8)], fill=11)
    d.polygon([(8, 7), (9, 9), (10, 11), (8, 13), (6, 11)], fill=12)
    d.polygon([(8, 9), (9, 11), (8, 13), (7, 11)], fill=14)
    d.point((7, 10), fill=13)
    d.point((9, 12), fill=13)
    if frame & 1:
        d.point((6+lean, 3), fill=12)
    return im


def halo(phase):
    im = canvas((32, 32))
    # Sparse indexed pixels leave the world visible between the warm glow.
    # No opaque circle or rectangular background is baked into the halo.
    for y in range(32):
        for x in range(32):
            r2=(x-16)**2+(y-16)**2
            if r2>225:
                continue
            threshold = 3 if r2<49 else (2 if r2<121 else 1)
            sample=BAYER[(y+phase)&3][(x+phase*2)&3]
            if sample<threshold:
                im.putpixel((x,y),15 if r2>81 else (9 if sample else 10))
    return im


def ember(variant):
    im=canvas((16,16))
    d=ImageDraw.Draw(im)
    if variant==0:
        d.line((8,7,8,9),fill=11)
        d.point((8,7),fill=14)
        d.point((9,8),fill=12)
        d.point((7,9),fill=9)
    elif variant==1:
        d.point((8,8),fill=13)
        d.point((8,9),fill=10)
    elif variant==2:
        d.point((8,8),fill=11)
    elif variant==3:
        d.point((8,8),fill=9)
    elif variant==4:
        d.line((7,8,9,7),fill=12)
        d.point((8,7),fill=14)
    elif variant==5:
        d.point((8,8),fill=12)
        d.point((9,7),fill=10)
    elif variant==6:
        d.point((8,8),fill=10)
    else:
        d.point((8,8),fill=15)
    return im


def planar(tile):
    result=bytearray()
    for pair in range(2):
        for y in range(8):
            for plane in (pair*2,pair*2+1):
                result.append(sum(((tile[y*8+x]>>plane)&1)<<(7-x) for x in range(8)))
    return bytes(result)


def oam_frame(facing,tick,planted=False):
    gx,gy=PLANTED_GRIP if planted else GRIPS[facing]
    fx,fy=PLANTED_FLAME if planted else FLAMES[facing]
    # Four 16px cells share one narrow column: two slivers per scanline,
    # rather than a halo, flame and five overlapping 16px particle sprites.
    result=bytearray()
    for cell in range(4):
        result.extend((fx-8,fy-40+cell*16,96+cell*32,0x2c))
    result.extend(bytes((0,240,0,0))*4)
    assert len(result)==32
    return bytes(result)


def build(out,assembly):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    atlas=canvas((128,64))
    for frame in range(8):
        atlas.paste(flame(frame),(frame*16,0))
    atlas.paste(halo(0),(0,32))
    atlas.paste(halo(1),(32,32))
    for n in range(8):
        atlas.paste(ember(n),(64+(n&3)*16,32+(n//4)*16))
    frames=[]
    for phase in range(8):
        view=canvas((16,64))
        torch=flame(phase)
        view.paste(torch,(0,31))
        for n in range(5):
            age=(phase*4+n*6)&31
            if age<30:
                x=8+DRIFT[(age+n*5)&31]+(n%3)-1
                y=36-age
                ImageDraw.Draw(view).point((x,y),fill=14 if age<7 else (13 if age<15 else 11))
        frames.append(view)
    payload=b''.join(planar(list(view.crop((x,y,x+8,y+8)).getdata()))
                     for view in frames for y in range(0,64,8) for x in range(0,16,8))
    assert len(payload)==4096
    (out/'torch.chr').write_bytes(payload)
    (out/'torch.pal').write_bytes(struct.pack('<16H',*(r//8+g//8*32+b//8*1024 for r,g,b in PALETTE)))
    oam=b''.join(oam_frame(face,tick) for face in range(4) for tick in range(32))
    assert len(oam)==4096
    (out/'torch-oam.bin').write_bytes(oam)
    planted=b''.join(oam_frame(0,tick,True) for tick in range(32))
    assert len(planted)==1024
    (out/'torch-planted-oam.bin').write_bytes(planted)
    assembly+=['.section "torch_tiles" superfree','torch_tiles:',
               '.incbin "assets/generated/torch.chr"','.ends','',
               '.section "torch_palette" superfree','torch_palette:',
               '.incbin "assets/generated/torch.pal"','.ends','',
               '.section "torch_oam" superfree','torch_oam_frames:',
               '.incbin "assets/generated/torch-oam.bin"','torch_planted_oam_frames:',
               '.incbin "assets/generated/torch-planted-oam.bin"','.ends','']
    atlas.save(out/'torch-atlas.png',transparency=0)
    strip=canvas((128,64))
    for n,frame in enumerate(frames):strip.paste(frame,(n*16,0))
    strip.save(out/'torch-compact.png',transparency=0)
    # Readable animation preview, in indexed colors and exact integer pixels.
    frames=[]
    for frame in range(8):
        view=canvas((48,48))
        view.paste(halo(frame&1),(8,0))
        torch=flame(frame)
        view.paste(torch,(16,7),torch.point(lambda p:255 if p else 0,'L'))
        frames.append(view.resize((144,144),Image.Resampling.NEAREST))
    frames[0].save(out/'torch-flame.gif',save_all=True,append_images=frames[1:],
                   duration=80,loop=0,transparency=0,disposal=2)
    print('torch 8 flames, 2 dither halos, 5 ember trails; 4096 OBJ + 5120 ROM OAM bytes')


if __name__=='__main__':
    build(ROOT/'assets/generated',[])
