"""Fear trial: a Novgorod timber yard and the supplied cockroach sprite."""
import struct
from pathlib import Path
from PIL import Image, ImageDraw


def yard_background():
    from build_assets import canvas
    im, d = canvas()
    colors = [(0,0,0),(14,23,31),(27,39,49),(48,64,73),
              (37,63,55),(69,91,69),(70,55,43),(107,83,54),
              (159,119,66),(244,190,92),(54,99,109),(147,178,176),
              (47,35,39),(103,53,47),(157,83,51),(219,208,165)]
    im.putpalette([v for color in colors for v in color]+[0]*(768-48))
    d.rectangle((0,0,255,223), fill=2)
    # Layered riverbank and skyline stay below the title's three tile rows.
    d.rectangle((0,24,255,51), fill=3)
    d.ellipse((207,25,224,42), fill=11)
    d.ellipse((210,28,222,40), fill=15)
    d.ellipse((214,30,218,33), fill=11)
    for x, y in ((16,29),(39,25),(94,27),(164,26),(188,32),(243,27)):
        d.point((x,y), fill=11)
    d.line((12,36,37,35,47,37,63,37), fill=11)
    d.line((164,42,184,40,201,42), fill=2)
    d.polygon(((0,45),(27,39),(57,44),(81,39),(108,44),(147,37),
               (179,42),(213,45),(255,39),(255,62),(0,62)), fill=4)
    for x in range(0,256,11):
        y = 42 + (x*3 % 7)
        d.polygon(((x,y-7),(x-4,y+3),(x-2,y+2),(x-7,y+9),(x+7,y+9)), fill=2)
    d.polygon(((0,53),(54,49),(102,54),(88,62),(0,69)), fill=10)
    for x, y, length in ((4,55,18),(29,57,25),(8,61,21),(62,54,16)):
        d.line((x,y,x+length,y), fill=11)
    # Log homes: shingle courses, exposed log ends, carved window frames.
    for x, y, w in ((37,49,39),(165,48,37)):
        d.rectangle((x,y,x+w,y+21), fill=6, outline=1)
        for yy in range(y+2,y+21,4):
            d.line((x+1,yy,x+w-1,yy), fill=7)
            d.line((x+2,yy+2,x+w-2,yy+2), fill=12)
            d.point((x+2,yy), fill=8)
            d.point((x+w-2,yy), fill=8)
        d.polygon(((x-5,y),(x+w//2,y-15),(x+w+5,y),(x+w+3,y+3),
                   (x+w//2,y-10),(x-3,y+3)), fill=12, outline=1)
        for step in (4,8,12):
            d.line((x-3+step,y-step//2,x+w//2,y-14+step//2,
                    x+w+3-step,y-step//2), fill=13)
        d.line((x-4,y,x+w//2,y-15,x+w+4,y), fill=7)
        for wx in (x+6,x+w-14):
            d.rectangle((wx-2,y+5,wx+8,y+16), fill=1)
            d.rectangle((wx,y+7,wx+6,y+14), fill=8)
            d.line((wx+1,y+8,wx+5,y+8), fill=9)
            d.line((wx+3,y+7,wx+3,y+14), fill=6)
            d.line((wx-2,y+5,wx+3,y+3,wx+8,y+5), fill=15)
            d.line((wx-2,y+17,wx+8,y+17), fill=7)
        d.rectangle((x+w//2-3,y+10,x+w//2+3,y+21), fill=12)
    # Timber chapel, drum and cross; no modern masonry or street furniture.
    d.rectangle((108,46,147,69), fill=6, outline=1)
    for y in range(48,70,4):
        d.line((110,y,145,y), fill=7)
        d.line((110,y+2,145,y+2), fill=12)
    d.polygon(((102,47),(128,33),(153,47),(149,50),(128,39),(106,50)), fill=12, outline=1)
    for x in range(108,149,6):
        d.line((x,46,128,35), fill=13)
    d.line((103,47,128,33,152,47), fill=8)
    d.rectangle((123,30,133,37), fill=7, outline=1)
    d.polygon(((122,30),(124,26),(128,24),(132,26),(134,30)), fill=11, outline=1)
    d.line((128,16,128,25), fill=15)
    d.line((125,19,131,19), fill=15)
    d.rectangle((123,55,133,70), fill=1)
    d.arc((122,51,134,62),180,360, fill=8)
    d.rectangle((125,56,131,69), fill=8)
    d.line((128,56,128,69), fill=6)
    for x in (114,139):
        d.rectangle((x,51,x+3,56), fill=9)
    # Rough palisade with lashings, a gate and a pair of gate posts.
    d.rectangle((0,66,255,79), fill=6)
    for x in range(0,256,7):
        y = 62 + x % 3
        d.polygon(((x,y+3),(x+2,y),(x+5,y+3),(x+5,79),(x,79)), fill=7, outline=1)
        d.line((x+2,y+4,x+2,77), fill=8)
    for y in (70,76):
        d.line((0,y,255,y), fill=6, width=2)
    d.rectangle((112,65,144,79), fill=6, outline=1)
    for x in range(116,145,5):
        d.line((x,66,x,78), fill=7)
    d.line((113,77,143,66), fill=8)
    for x in (109,145):
        d.rectangle((x,61,x+3,80), fill=7, outline=1)
        d.point((x+1,63), fill=15)
    # Moss, stones and discarded timber frame a recessed playable platform.
    d.rectangle((0,80,255,199), fill=4)
    for y in range(85,200,12):
        for x in (3,10,244,251):
            d.line((x,y+3,x-2,y,x+1,y+2,x+3,y-2), fill=5)
    for x, y in ((7,93),(249,118),(4,159),(251,187),(14,193)):
        d.ellipse((x-3,y-2,x+3,y+2), fill=3, outline=1)
        d.line((x-1,y-2,x+2,y-2), fill=11)
    d.rectangle((20,79,235,199), fill=12, outline=1)
    for y in range(80,200,8):
        d.rectangle((22,y,233,y+6), fill=6)
        d.line((23,y,232,y), fill=7)
        for x in range(26,228,32):
            d.line((x,y+3,x+15,y+3), fill=12)
            d.line((x+5,y+5,x+21,y+5), fill=7)
            if (x+y) % 3 == 0:
                d.ellipse((x+15,y+1,x+21,y+4), outline=12)
        for x in (25,230):
            d.point((x,y+2), fill=1)
            d.point((x+1,y+2), fill=8)
    for x in (18,236):
        d.rectangle((x-2,78,x+2,199), fill=7, outline=1)
        d.line((x-1,80,x-1,197), fill=8)
        for y in (82,110,155,195):
            d.line((x-3,y-2,x+3,y+2), fill=6)
            d.line((x-3,y+2,x+3,y-2), fill=8)
    for row in range(3):
        for col in range(3):
            x, y = 56 + col*72, 94 + row*44
            d.ellipse((x-25,y-5,x+25,y+10), fill=12, outline=1)
            d.ellipse((x-24,y-5,x+24,y+8), fill=7, outline=8)
            d.ellipse((x-21,y-4,x+21,y+5), fill=0, outline=1)
            d.arc((x-24,y-5,x+24,y+8), 0, 180, fill=8)
            for dx in (-18,-9,9,18):
                d.line((x+dx,y+6,x+dx-1,y+8), fill=6)
    return im


def build(out, assembly, tile_image):
    from build_assets import flat_pixels
    im = yard_background()
    tiles, tilemap = tile_image(im, max_tiles=768)
    palette = im.getpalette()[:48]
    pal = struct.pack('<16H', *(palette[n]//8 + (palette[n+1]//8)*32 +
                               (palette[n+2]//8)*1024 for n in range(0,48,3)))
    im.convert('RGB').save(out/'roach-yard.png')
    for suffix, data in (('chr', tiles), ('map', tilemap), ('pal', pal)):
        (out/('roach-yard.'+suffix)).write_bytes(data)
    assembly += ['.section "roach_yard" superfree', 'roach_tiles:',
                 '.incbin "assets/generated/roach-yard.chr"', 'roach_tiles_end:',
                 'roach_map:', '.incbin "assets/generated/roach-yard.map"',
                 'roach_palette:', '.incbin "assets/generated/roach-yard.pal"', '.ends', '']

    source = Image.open(Path(__file__).resolve().parents[1]/
                        'assets/characters/fear-roach.png').convert('RGB')
    # Remove only the connected light backdrop, preserving the face and eyes.
    mask = Image.new('L', source.size)
    mask.putdata([255 if min(pixel) > 220 else 0 for pixel in flat_pixels(source)])
    ImageDraw.floodfill(mask, (0, 0), 128)
    opaque = [pixel != 128 for pixel in flat_pixels(mask)]
    reduced = source.quantize(colors=11, dither=Image.Dither.NONE)
    colors = [(0,0,0)] + [tuple(reduced.getpalette()[n:n+3]) for n in range(0,33,3)]
    colors += [(173,117,56), (226,192,119), (246,222,157), (67,40,26)]
    sheet = Image.new('P', (128,32))
    sheet.putpalette([v for color in colors for v in color]+[0]*(768-48))
    for index, color in enumerate(flat_pixels(reduced)):
        if opaque[index]:
            sheet.putpixel((7+index % source.width, index // source.width), color+1)
    hammer = ImageDraw.Draw(sheet)
    hammer.line((47,13,39,29), fill=15, width=5)
    hammer.line((47,13,39,29), fill=12, width=3)
    hammer.polygon(((41,1),(58,8),(54,20),(36,13)), fill=12, outline=15)
    hammer.line((42,3,56,9,53,17), fill=13, width=2)
    hammer.line((38,12,53,18), fill=15)
    for dx, dy in ((0,-10),(0,10),(-10,0),(10,0),(-7,-7),(7,7),(-7,7),(7,-7)):
        hammer.line((80+dx//2,16+dy//2,80+dx,16+dy), fill=14, width=2)
    sprite_tiles, _ = tile_image(sheet, dedupe=False)
    sprite_pal = struct.pack('<16H', *(r//8+(g//8)*32+(b//8)*1024 for r,g,b in colors))
    (out/'roach-actors.chr').write_bytes(sprite_tiles)
    (out/'roach-actors.pal').write_bytes(sprite_pal)
    rgba = sheet.convert('RGBA')
    alpha = Image.new('L', sheet.size)
    alpha.putdata([255 if pixel else 0 for pixel in flat_pixels(sheet)])
    rgba.putalpha(alpha)
    rgba.save(out/'roach-actors.png')
    assembly += ['.section "roach_actors" superfree', 'roach_actors:',
                 '.incbin "assets/generated/roach-actors.chr"', 'roach_actor_palette:',
                 '.incbin "assets/generated/roach-actors.pal"', '.ends', '']
