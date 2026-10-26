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
    (224, 224, 192), (8, 16, 24), (232, 192, 120),
    # Faded cloth and quiet ceremonial markings.
    (46, 28, 25), (61, 35, 28), (77, 46, 33), (90, 60, 39),
]


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
    if room == 0:
        im = tile_material('soil')
        # Moss survives around the edges of the yard; foot traffic joins the
        # elder, Egor, oil supply and the forest exit through compacted earth.
        mask, d = mask_image()
        d.polygon([(0, 0), (256, 0), (256, 80), (224, 72), (208, 40),
                   (80, 40), (64, 112), (0, 120)], fill=255)
        d.rectangle((0, 184, 255, 223), fill=255)
        overlay(im, 'moss', mask)
        path = trail_mask([(52, 78), (100, 104), (120, 148), (176, 148), (248, 152)], 24)
        pd = ImageDraw.Draw(path)
        pd.line((120, 140, 168, 112, 192, 112), fill=255, width=18)
        pd.line((108, 144, 28, 146), fill=255, width=15)
        overlay(im, 'path', path)
        mask, d = mask_image()
        for box in ((16, 40, 79, 71), (160, 40, 231, 71)):
            d.rectangle(box, fill=255)
        overlay(im, 'foundation', mask)
        mask, d = mask_image()
        d.rectangle((96, 0, 143, 63), fill=255)
        overlay(im, 'water', mask)
        mask, d = mask_image()
        d.rectangle((112, 32, 127, 79), fill=255)
        overlay(im, 'bridge', mask)
    elif room == 1:
        im = tile_material('moss')
        mask, d = mask_image()
        d.polygon([(32, 224), (24, 144), (48, 104), (88, 80), (104, 32),
                   (144, 24), (184, 64), (224, 96), (248, 120), (224, 176),
                   (160, 192), (112, 224)], fill=255)
        overlay(im, 'soil', mask)
        overlay(im, 'path', trail_mask([(12, 40), (52, 112), (80, 132),
                                       (116, 60), (168, 116), (208, 144),
                                       (240, 102)], 14))
        mask, d = mask_image()
        d.polygon([(0, 0), (32, 0), (32, 96), (40, 120), (32, 152), (0, 160)], fill=255)
        overlay(im, 'water', mask)
        mask, d = mask_image()
        d.rectangle((16, 136, 47, 151), fill=255)
        overlay(im, 'bridge', mask)
        # Roots follow large tree bases, avoiding a repeating forest grid.
        d = ImageDraw.Draw(im)
        for x, y in ((150, 126),):
            d.line((x-8, y+4, x-3, y+1, x, y-6), fill=2, width=2)
            d.line((x, y-2, x+4, y+5, x+10, y+6), fill=2, width=2)
            d.line((x-7, y+3, x-2, y, x, y-5), fill=4)
    elif room == 2:
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
