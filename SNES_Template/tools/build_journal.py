"""Native 256x224 journal: parchment ink, copper ornaments and blood-red accents."""
import random
import struct

from PIL import Image, ImageDraw

COLORS = [(0,0,0),(9,13,14),(23,26,25),(43,38,32),
          (68,52,42),(105,77,56),(148,109,76),(192,153,108),
          (228,205,166),(248,224,183),(55,19,21),(108,35,33),
          (164,51,43),(209,85,51),(239,146,68),(114,108,94)]


def artwork():
    im = Image.new('P', (256,224), 0)
    im.putpalette([v for color in COLORS for v in color]+[0]*(768-48))
    d = ImageDraw.Draw(im)
    # Thin, weathered frame. The center remains completely quiet for text.
    d.rectangle((3,3,252,220), outline=4)
    d.rectangle((4,4,251,219), outline=3)
    rng = random.Random(1193)
    for _ in range(70):
        x = rng.randrange(6,250)
        d.point((x,3 if _ & 1 else 220), fill=5 if _ % 3 else 6)
    for x,y,dx,dy in ((4,4,1,1),(251,4,-1,1),(4,219,1,-1),(251,219,-1,-1)):
        d.line((x,y,x+dx*17,y), fill=6)
        d.line((x,y,x,y+dy*15), fill=5)
        d.line((x+dx*3,y+dy*2,x+dx*3,y+dy*6,x+dx*8,y+dy*6), fill=5)
        d.polygon([(x+dx*8,y),(x+dx*11,y+dy*3),(x+dx*8,y+dy*6),
                   (x+dx*5,y+dy*3)], outline=4)
        d.point((x+dx*8,y+dy*3), fill=8)

    def diamond(x,y):
        d.line((x-5,y,x+5,y),fill=4)
        d.line((x,y-5,x,y+5),fill=5)
        d.polygon([(x,y-3),(x+3,y),(x,y+3),(x-3,y)],outline=6)
        d.point((x,y),fill=8)
    diamond(128,4)
    d.line((16,47,239,47), fill=4)
    d.line((16,48,239,48), fill=2)
    diamond(128,47)
    d.line((128,55,128,82), fill=4)
    # A restrained red flourish marks the objective instead of another box.
    d.line((73,91,237,91), fill=11)
    d.line((73,92,237,92), fill=10)
    d.polygon([(236,88),(240,91),(236,94),(232,91)], outline=11)
    d.line((24,155,239,155), fill=4)
    diamond(128,155)
    d.line((128,162,128,203), fill=4)
    d.line((16,204,239,204), fill=2)

    # Open notebook with two leaves and an inked spine, 20x20 pixels.
    d.rectangle((14,18,34,36), fill=3)
    d.line((15,17,15,34,24,36,33,34,33,17),fill=6)
    d.polygon([(16,16),(23,17),(24,20),(25,17),(32,16),(32,32),
               (25,34),(24,33),(23,34),(16,32)], fill=7)
    d.line((24,20,24,33),fill=4)
    for y in (20,23,26,29):
        d.line((18,y,21,y+1),fill=4)
        d.line((27,y+1,30,y),fill=4)
    d.line((30,14,30,30),fill=8)
    from build_font import GLYPHS
    # Tall, individually drawn bitmap heading; no vector font rasterization.
    for index, ch in enumerate('ЗАПИСИ КИРИЛЛА'):
        pattern = GLYPHS[ch]
        width = len(pattern[0])
        for y in range(11):
            for x, bit in enumerate(pattern[y*len(pattern)//11]):
                if bit == '1': d.point((41+index*8+(7-width)//2+x,16+y),fill=8)

    # Torch and eye occupy a dedicated icon gutter, away from the gauges.
    d.line((21,65,21,79),fill=6,width=2)
    d.line((17,66,25,66),fill=7)
    d.polygon([(20,52),(23,57),(24,55),(26,61),(24,65),
               (18,65),(16,61),(19,57)],fill=11)
    d.polygon([(21,55),(23,60),(24,62),(21,65),(18,62)],fill=13)
    d.line((21,60,21,64),fill=8)
    d.polygon([(138,64),(145,59),(153,64),(145,69)],outline=7)
    d.ellipse((142,60,148,68),fill=6)
    d.rectangle((145,62,146,66),fill=0)
    d.line((141,56,149,56),fill=5)
    d.line((144,54,146,54),fill=5)

    # Small cross/waymark beside the objective heading.
    d.line((22,85,22,98), fill=11, width=2)
    d.line((16,90,28,90), fill=11)
    for x,y in ((22,85),(16,90),(28,90),(22,98)):
        d.polygon([(x,y-2),(x+2,y),(x,y+2),(x-2,y)],outline=12)

    def icon(kind,x,y):
        if kind == 'arrow':
            d.line((x,y+10,x+10,y),fill=7)
            d.line((x+5,y,x+10,y,x+10,y+5),fill=8)
            d.line((x,y+6,x+4,y+10),fill=6)
            d.line((x+2,y+4,x+6,y+8),fill=6)
        elif kind == 'coin':
            for yy in (y+7,y+3,y):
                d.ellipse((x,yy,x+10,yy+5),fill=6,outline=7)
                d.line((x+3,yy+2,x+7,yy+2),fill=4)
        elif kind == 'feather':
            d.polygon([(x,y+10),(x+3,y+2),(x+10,y),(x+8,y+7),(x+2,y+10)],fill=7)
            d.line((x,y+12,x+9,y+2),fill=4)
            d.point((x+5,y+5),fill=8)
        elif kind == 'cross':
            d.line((x+5,y,x+5,y+11),fill=7,width=2)
            d.line((x,y+5,x+10,y+5),fill=7)
            d.point((x+5,y+5),fill=9)
        elif kind == 'moon':
            d.ellipse((x,y,x+10,y+11),fill=7)
            d.ellipse((x+4,y-2,x+13,y+7),fill=0)
        elif kind == 'key':
            d.ellipse((x+4,y,x+10,y+6),outline=7)
            d.line((x+6,y+5,x+1,y+11),fill=7,width=2)
            d.point((x+3,y+11),fill=8)
    for row, pair in zip((158,174,190), (('arrow','coin'),('feather','cross'),('moon','key'))):
        icon(pair[0],14,row);icon(pair[1],143,row)

    # Thorn sprigs stay in the outside margin; they never cover a text cell.
    for offset,color in ((0,3),(37,4),(72,11)):
        d.line((6,203-offset,12,180-offset,7,162-offset),fill=color)
        for y in range(168-offset,199-offset,10):
            d.line((9,y,5,y-4),fill=color)
            d.point((11,y-5),fill=color)
    # A small skyline is engraved in the lower frame.
    for x,h in ((106,5),(114,7),(124,11),(133,6),(142,4)):
        d.rectangle((x,219-h,x+4,219),fill=3)
        d.polygon([(x-1,219-h),(x+2,215-h),(x+5,219-h)],fill=4)
    return im


def font_tiles(planar):
    from build_font import glyph_pixels
    result = []
    for full in (True, False):
        tile = [2]*64
        for y in range(2,7):
            for x in range(7):
                tile[y*8+x] = 3 if y in (2,6) or x in (0,6) else (1 if full else 2)
        result.append(planar(tile,2))
    for char in '0123456789:':
        source = glyph_pixels(char)
        pixels = [2]*128
        for y in range(12):
            for x in range(8):
                pixels[(y+1)*8+x] = source[(y*7//12)*8+x]
        result.extend((planar(pixels[:64],2),planar(pixels[64:],2)))
    return result


def build(out, assembly, tile_image):
    im = artwork()
    tiles, tilemap = tile_image(im, max_tiles=768)
    colors = COLORS + [(0,0,0)]*16
    for bank, ink in ((5,(137,126,108)),(6,(172,57,48)),(7,(228,205,166))):
        colors[bank*4+1] = ink
        colors[bank*4+2] = (0,0,0)
        colors[bank*4+3] = COLORS[5]
    palette = struct.pack('<32H', *(r//8+(g//8)*32+(b//8)*1024 for r,g,b in colors))
    for extension,payload in (('chr',tiles),('map',tilemap),('pal',palette)):
        (out/('journal.'+extension)).write_bytes(payload)
    im.convert('RGB').save(out/'journal.png')
    assembly += ['.section "journal_background" superfree', 'journal_tiles:',
                 '.incbin "assets/generated/journal.chr"', 'journal_tiles_end:',
                 'journal_map:', '.incbin "assets/generated/journal.map"',
                 'journal_palette:', '.incbin "assets/generated/journal.pal"', '.ends', '']
    print('journal',len(tiles)//32,'tiles')
