"""Tile-authored, top-down materials for the native Mode 7 ground plane.

All variation is chosen at build time. Reusable 32-pixel swatches keep the
cartridge's 256-character budget predictable without baking perspective,
lights, or upright scenery into the floor.
"""
import random

from PIL import Image, ImageDraw

SIZE = (256, 224)
UI_COLORS = (224, 224, 192, 8, 16, 24, 232, 192, 120)
COLORS = [
    (0, 0, 0),
    # Wet soil, compacted earth, fine gravel.
    (30, 25, 22), (40, 33, 27), (49, 40, 31), (59, 48, 35),
    (69, 56, 40), (79, 65, 47), (91, 76, 56),
    # Moss and lichen. No bright green under the torch.
    (27, 33, 24), (36, 43, 29), (46, 52, 33), (58, 62, 40),
    # River silt, deep water, reflected ripples.
    (20, 29, 29), (27, 38, 37), (34, 47, 44), (43, 56, 49),
    # Worn wood, exposed grain and end cuts.
    (33, 27, 23), (47, 36, 27), (62, 47, 32), (77, 58, 39),
    (92, 72, 49), (107, 85, 59),
    # Slate and old limestone. Soft edges rather than a white grid.
    (31, 34, 32), (43, 46, 41), (55, 58, 50), (67, 68, 57),
    (79, 79, 65), (91, 89, 72), (40, 43, 35),
    # Slots 29..31 belong to the Mode 1 text overlay.
    (228, 205, 166), (0, 0, 0), (148, 109, 76),
    # Faded cloth and quiet ceremonial markings.
    (46, 28, 25), (61, 35, 28), (77, 46, 33), (90, 60, 39),
]
COLORS += [(20,35,24),(27,45,28),(37,55,31),(48,67,35),(61,78,42),(73,87,48),
           (50,40,28),(62,50,34),(75,62,42),(88,73,51),(31,29,24),(41,36,27),
           (63,62,49),(80,77,60),(98,89,66),(14,28,33),(21,38,43),(29,48,51),
           (43,61,60),(45,30,21),(59,42,25),(77,56,32)]


def outdoor_tile(kind,variant,edge=0):
    """A small texture vocabulary plus reusable shoreline/path autotiles."""
    rng=random.Random(703+variant*97+sum(map(ord,kind)))
    im=indexed((8,8));d=ImageDraw.Draw(im)
    if kind in ('grass','forest'):
        im.paste(37 if kind=='grass' else 36,(0,0,8,8))
        for _ in range(3):
            x,y=rng.randrange(1,7),rng.randrange(1,7)
            d.line((x,y+1,x+1,y-1),fill=38)
            d.point((x+2,y+1),fill=39 if kind=='grass' else 37)
        if kind=='forest':
            d.line((1,5,3,6,4,5),fill=55);d.point((3,5),fill=56)
            if variant==1:d.line((5,1,6,2),fill=57)
    elif kind in ('path','earth','mud','gravel'):
        base={'path':43,'earth':3,'mud':46,'gravel':24}[kind]
        im.paste(base,(0,0,8,8))
        for _ in range(3):
            x,y=rng.randrange(6),rng.randrange(8)
            d.line((x,y,x+2,y),fill=base-1 if kind!='mud' else 47)
        if kind in ('path','gravel') and variant==3:
            d.line((3,3,4,3),fill=49);d.point((4,4),fill=48)
        if kind=='gravel':d.line((0,7,7,7),fill=23);d.line((7,0,7,6),fill=23)
    elif kind=='water':
        im.paste(51,(0,0,8,8));d.line((1,2,5,2),fill=52)
        if variant==1:d.line((3,5,7,4),fill=53)
    elif kind=='bridge':
        im.paste(18,(0,0,8,8));d.line((0,7,7,7),fill=16);d.line((0,0,7,0),fill=20)
        d.line((2,3,5,3,6,4),fill=17);d.point((1,2),fill=21);d.point((6,5),fill=16)
    elif kind=='crops':
        im.paste(3,(0,0,8,8))
        d.line((0,2,7,2),fill=2);d.line((0,6,7,6),fill=2)
        for x,y in ((1,1),(5,1),(3,5),(7,5)):
            d.line((x,y+1,x,y-1),fill=40);d.line((x-1,y,x+1,y),fill=41)
    elif kind in ('bracken','roots','leaves','flowers'):
        im.paste(37 if kind=='flowers' else 36,(0,0,8,8))
        if kind=='roots':
            d.line((0,3,3,4,5,6,7,6),fill=55,width=2)
            d.line((1,3,4,4,6,6),fill=56);d.line((3,4,5,1,7,0),fill=55)
        elif kind=='bracken':
            for x,y in ((2,3),(6,6)):
                d.line((x,y+2,x,y-2),fill=39)
                d.line((x-2,y-1,x,y+1,x+2,y-1),fill=40)
                d.point((x-1,y-2),fill=41)
        elif kind=='leaves':
            for x,y in ((1,2),(5,1),(3,6),(7,5)):
                d.line((x,y,x+1,y+1),fill=56 if variant&1 else 57)
                d.point((x+1,y),fill=55)
        else:
            for x,y in ((2,3),(6,5)):
                d.point((x,y),fill=15);d.point((x,y+1),fill=41)
    elif kind=='tracks':
        im.paste(43,(0,0,8,8))
        d.line((1,0,1,7),fill=42);d.line((6,0,6,7),fill=42)
        if variant&1:d.line((2,3,3,3),fill=46)
    elif kind=='logs':
        im.paste(3,(0,0,8,8))
        for y in (1,5):
            d.line((0,y,7,y),fill=17,width=3);d.line((0,y-1,7,y-1),fill=21)
            d.line((1,y,5,y),fill=19)
    elif kind=='cobbles':
        im.paste(23,(0,0,8,8))
        for box in ((1,0,6,3),(-2,5,2,7),(4,5,8,7)):
            d.rounded_rectangle(box,1,fill=25,outline=24)
            d.point((box[0]+1,box[1]),fill=27)
    elif kind=='ruin':
        im.paste(36,(0,0,8,8))
        d.polygon(((1,2),(5,1),(7,4),(5,6),(1,6)),fill=24,outline=23)
        d.line((2,2,5,2),fill=26);d.line((1,7,3,7),fill=39)
    elif kind=='embers':
        im.paste(2,(0,0,8,8));d.line((1,2,6,5),fill=16,width=2)
        d.line((2,5,6,1),fill=17,width=2);d.point((3,3),fill=33)
    else:raise ValueError(kind)
    if edge:
        bank=46 if kind=='water' else (37 if kind=='path' else 36)
        for side,bit in enumerate((1,2,4,8)):
            if not edge&bit:continue
            for p in range(8):
                depth=1+(p in (0,3,6))
                for q in range(depth):
                    x,y=((p,q),(7-q,p),(p,7-q),(q,p))[side]
                    d.point((x,y),fill=bank)
    return im


def outdoor_ground(room):
    """Authored village/ford layout; textures stay flat in world space."""
    base='grass' if room==0 else 'forest'
    grid=[[base for _ in range(32)] for _ in range(28)]
    def paint(kind,mask):
        for y in range(28):
            for x in range(32):
                if not mask.getpixel((x*8+4,y*8+4)):continue
                if kind in ('bracken','roots','leaves','flowers') and grid[y][x] not in ('grass','forest'):
                    continue
                grid[y][x]=kind
    def region(kind,polygon=None,box=None):
        mask,d=mask_image()
        if polygon:d.polygon(polygon,fill=255)
        if box:d.rectangle(box,fill=255)
        paint(kind,mask)
    def trail(points,width):paint('path',trail_mask(points,width))
    if room==0:
        region('earth',polygon=[(24,76),(72,64),(108,96),(172,90),(220,116),
                               (244,156),(192,176),(96,184),(48,168),(16,128)])
        # A courtyard and two homesteads face the road; the creek is behind.
        region('gravel',box=(16,48,80,80));region('gravel',box=(160,48,232,80))
        region('water',polygon=[(96,0),(144,0),(144,40),(136,64),(120,80),(96,64)])
        region('mud',box=(88,48,104,72));region('bridge',box=(112,24,128,80))
        trail([(120,184),(120,152),(104,120),(56,80)],24)
        trail([(112,144),(160,144),(192,112)],20)
        trail([(120,152),(184,152),(248,152)],22)
        trail([(96,144),(32,144)],14)
        region('gravel',box=(136,120,160,144))
        region('mud',box=(24,136,40,160))
        # Kitchen plots, wheel ruts, stacked timber and a worn common yard.
        region('crops',box=(0,104,40,128));region('crops',box=(192,168,240,208))
        region('crops',box=(40,184,88,208))
        region('cobbles',box=(128,120,160,144))
        region('logs',box=(8,80,40,88));region('logs',box=(200,80,224,88))
        region('tracks',box=(176,128,240,144))
        region('flowers',box=(64,64,80,80));region('flowers',box=(168,64,184,80))
        region('leaves',box=(0,160,16,208));region('leaves',box=(88,32,104,48))
    else:
        region('earth',polygon=[(56,224),(40,168),(48,120),(72,104),(88,72),
                               (120,48),(176,64),(208,96),(240,128),(224,168),(168,192),(112,224)])
        region('water',polygon=[(0,64),(12,72),(24,96),(24,112),(40,136),
                               (32,160),(16,176),(8,208),(0,224)])
        region('mud',polygon=[(16,96),(32,112),(48,136),(40,160),(24,176),(16,176),(24,144)])
        trail([(128,184),(128,160),(88,144),(56,112),(64,96)],20)
        trail([(88,144),(28,144)],16)
        trail([(64,96),(88,80),(116,60)],14)
        trail([(116,60),(152,80),(184,76)],14)
        trail([(128,160),(168,136),(208,144)],16)
        trail([(168,136),(176,112),(208,112),(240,104)],16)
        trail([(56,112),(32,72),(12,40)],12)
        region('bridge',box=(16,136,56,152))
        region('gravel',box=(112,152,136,176))
        # Understorey forms beds at the tree line, with a disturbed camp at
        # the ford and pieces of an old paved approach to the chapel.
        for box in ((0,0,72,56),(208,0,256,80),(80,184,112,224),
                    (216,168,256,224),(40,72,56,96),(144,32,168,56)):
            region('bracken',box=box)
        for box in ((40,40,64,64),(208,48,232,64),(0,112,16,136),
                    (232,88,256,104),(112,192,152,208)):
            region('roots',box=box)
        for box in ((72,96,88,120),(160,152,184,176),(176,48,200,64),
                    (48,168,72,192),(120,88,144,104)):
            region('leaves',box=box)
        region('logs',box=(40,152,64,160));region('embers',box=(56,128,72,136))
        region('ruin',box=(192,112,224,128));region('ruin',box=(112,48,128,64))
    im=indexed();cache={}
    for y,row in enumerate(grid):
        for x,kind in enumerate(row):
            edge=0
            if kind in ('path','water'):
                for side,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))):
                    xx,yy=x+dx,y+dy
                    other=grid[yy][xx] if 0<=xx<32 and 0<=yy<28 else kind
                    if (kind=='water' and other!='water') or (kind=='path' and other in ('grass','forest')):
                        edge|=1<<side
            variant=(x*3+y*5+(x//4))%4
            key=(kind,variant,edge)
            if key not in cache:cache[key]=outdoor_tile(*key)
            im.paste(cache[key],(x*8,y*8))
    return im


def indexed(size=SIZE, fill=1):
    im = Image.new('P', size, fill)
    im.putpalette([value for color in COLORS for value in color] +
                  [0] * (768 - len(COLORS) * 3))
    return im


def swatch(kind):
    """Small, seamless texture vocabulary; no per-pixel white noise."""
    rng = random.Random(1193 + sum(map(ord, kind)))
    im = indexed((32, 32))
    d = ImageDraw.Draw(im)
    if kind in ('soil', 'path', 'moss'):
        base = {'soil': 3, 'path': 5, 'moss': 9}[kind]
        im.paste(base, (0, 0, 32, 32))
        # Clusters are sparse and elongated, so Mode 7 reads soil, not speckle.
        for _ in range(32):
            x, y = rng.randrange(32), rng.randrange(32)
            w, h = rng.choice((2, 3, 4)), rng.choice((1, 1, 2))
            color = rng.choice((base - 1, base, base + 1))
            for ox in (-32, 0, 32):
                for oy in (-32, 0, 32):
                    d.line((x+ox, y+oy, x+w+ox, y+oy), fill=color)
                    if h == 2:
                        d.line((x+1+ox, y+1+oy, x+w-1+ox, y+1+oy), fill=color)
        if kind != 'moss':
            for x, y in ((4, 7), (23, 20), (13, 28)):
                d.line((x, y, x+2, y), fill=4 if kind == 'soil' else 7)
                d.point((x+1, y+1), fill=2 if kind == 'soil' else 4)
        else:
            for x, y in ((3, 5), (18, 13), (25, 27)):
                d.line((x, y, x+3, y+1), fill=10)
                d.point((x+1, y-1), fill=11)
    elif kind == 'water':
        im.paste(12, (0, 0, 32, 32))
        for x, y, w in ((3, 3, 9), (19, 7, 8), (8, 15, 13), (0, 23, 5), (23, 28, 7)):
            d.line((x, y, x+w, y-1), fill=13)
            d.line((x+2, y, x+w-3, y), fill=14)
    elif kind in ('planks', 'bridge'):
        im.paste(18, (0, 0, 32, 32))
        # One grain pattern per plank, with staggered joints and tiny iron nails.
        for x in range(0, 32, 8):
            d.rectangle((x, 0, x, 31), fill=16)
            d.line((x+1, 0, x+1, 31), fill=19)
            for y in range(32):
                if (y + x) % 17 not in (0, 1, 2):
                    d.point((x+3+(y//11+x//8)%2, y), fill=17)
                if (y + x*3) % 13 < 7:
                    d.point((x+6, y), fill=19)
            joint = (x//8 * 13 + 7) % 32
            d.line((x+1, joint, x+7, joint), fill=16)
            d.line((x+2, (joint+1)%32, x+6, (joint+1)%32), fill=20)
            d.point((x+2, (joint+3)%32), fill=17)
            d.point((x+6, (joint-2)%32), fill=17)
        d.line((12, 17, 12, 20, 14, 21, 14, 18, 12, 17), fill=17)
        if kind == 'bridge':
            im = im.transpose(Image.Transpose.ROTATE_90)
    elif kind in ('slate', 'foundation'):
        im.paste(24, (0, 0, 32, 32))
        # Irregular fitted slabs, with a one-pixel bevel on the lit side.
        for ox in (-32, 0, 32):
            for oy in (-32, 0, 32):
                for points, color in (
                    ([(1, 1), (17, 1), (18, 5), (16, 14), (2, 15), (0, 12)], 25),
                    ([(20, 1), (31, 0), (33, 13), (19, 14), (20, 9)], 24),
                    ([(1, 18), (9, 17), (10, 30), (0, 32)], 24),
                    ([(12, 17), (28, 16), (31, 22), (30, 31), (13, 31), (11, 26)], 25),
                ):
                    polygon = [(x+ox, y+oy) for x, y in points]
                    d.polygon(polygon, fill=color, outline=23)
                    d.line([polygon[0], polygon[1]], fill=color+1)
        d.line((4, 4, 8, 5, 10, 4), fill=26)
        d.line((18, 27, 22, 26, 24, 28), fill=24)
        d.line((23, 4, 25, 7, 24, 10), fill=23)
        for x, y in ((5, 11), (26, 20), (16, 22)):
            d.line((x, y, x+2, y), fill=26)
        if kind == 'foundation':
            # Dirt collected between stones makes a village footing less formal.
            d.line((0, 16, 8, 15, 17, 16, 24, 14, 31, 15), fill=2)
    elif kind == 'cloth':
        im.paste(33, (0, 0, 32, 32))
        for y in range(0, 32, 4):
            d.line((0, y, 31, y), fill=32)
        for x in (2, 29):
            d.line((x, 0, x, 31), fill=35)
    else:
        raise ValueError('Unknown ground material: '+kind)
    return im


def tile_material(kind):
    patch = swatch(kind)
    im = indexed()
    for y in range(0, SIZE[1], 32):
        for x in range(0, SIZE[0], 32):
            im.paste(patch, (x, y))
    return im


def overlay(im, kind, mask):
    im.paste(tile_material(kind), (0, 0), mask)


def mask_image():
    im = Image.new('L', SIZE)
    return im, ImageDraw.Draw(im)


def trail_mask(points, width):
    mask, d = mask_image()
    d.line(points, fill=255, width=width, joint='curve')
    radius = width//2
    for x, y in points:
        d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=255)
    return mask


def build_ground(room):
    if room<2:return outdoor_ground(room)
    if room == 2:
        im = tile_material('planks')
        mask, d = mask_image()
        d.rectangle((104, 56, 151, 71), fill=255)
        d.rectangle((112, 72, 143, 143), fill=255)
        overlay(im, 'cloth', mask)
        mask, d = mask_image()
        d.rectangle((0, 0, 255, 31), fill=255)
        d.rectangle((0, 32, 15, 223), fill=255)
        d.rectangle((240, 32, 255, 223), fill=255)
        overlay(im, 'foundation', mask)
        d = ImageDraw.Draw(im)
        # A raised sanctuary, worn central runner, woven borders and a timber
        # threshold. All marks lie flat; upright walls live in the OBJ atlas.
        d.rectangle((104,32,151,55),fill=18)
        for y in (35,43,51):
            d.line((105,y,150,y),fill=21)
            d.line((105,y+1,150,y+1),fill=16)
        d.line((104,55,151,55),fill=22)
        d.line((104,56,151,56),fill=17)
        for x in (112,140):
            d.line((x,72,x,143),fill=35)
            for y in range(76,140,8):
                d.line((x+1,y,x+2,y+1,x+1,y+2),fill=34)
        for y in (84,108,132):
            d.line((124,y,128,y-4,132,y,128,y+4,124,y),fill=34)
            d.point((128,y),fill=35)
        d.rectangle((16,176,239,183),fill=17)
        d.line((16,176,239,176),fill=21)
        d.line((16,183,239,183),fill=16)
        # Hearth-like stone pads under the two candlestands and the bells.
        for x,y in ((80,78),(176,78),(172,144)):
            d.rectangle((x-8,y-4,x+7,y+3),fill=23)
            d.line((x-7,y-3,x+5,y-3),fill=25)
        # Worn threshold and descending dark stair treads at the cellar exit.
        d.rectangle((216, 160, 239, 183), fill=16)
        for y in range(162, 184, 4):
            d.line((218, y, 237, y), fill=18)
            d.line((219, y+1, 236, y+1), fill=17)
    elif room == 3:
        im = tile_material('slate')
        d = ImageDraw.Draw(im)
        # Damp in the corners, not luminous cracks or a geometric floor grid.
        for x, y in ((8, 32), (232, 32), (16, 184), (224, 184)):
            d.polygon([(x, y), (x+15, y+2), (x+12, y+10), (x+2, y+13)], fill=28)
            d.line((x+2, y+3, x+9, y+4, x+12, y+7), fill=9)
        for x in (48, 128, 208):
            d.rectangle((x-8, 120, x+7, 135), fill=23)
            d.line((x-7, 121, x+5, 121), fill=26)
            d.line((x-7, 122, x-7, 133), fill=25)
            d.line((x+6, 123, x+6, 134), fill=22)
        d.rectangle((112, 48, 143, 79), fill=22)
        d.line((113, 49, 141, 49), fill=24)
    else:
        raise ValueError('Unknown Mode 7 room')
    return im
