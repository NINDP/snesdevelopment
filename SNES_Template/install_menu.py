#!/usr/bin/env python3
"""Install the Chernorechye SNES main-menu visual redesign.
Run from SNES_Template: python3 install_menu.py
"""
from pathlib import Path
import re

ROOT = Path.cwd()
if not (ROOT / 'Data/platform/video.c').is_file():
    raise SystemExit('Run this script from the SNES_Template directory.')

ASSETS = ROOT / 'tools/build_assets.py'
VIDEO = ROOT / 'Data/platform/video.c'

NEW_TITLE = 'def title():\n    """Main menu: moonlit medieval Chernorechye, chapel and torch."""\n    im, d = canvas()\n    colors = [\n        (4, 5, 10),      # 0 deep shadow\n        (11, 12, 24),    # 1 night sky\n        (19, 20, 35),    # 2 farther sky\n        (29, 28, 44),    # 3 hills\n        (41, 40, 53),    # 4 far wood\n        (56, 52, 61),    # 5 weathered wood\n        (76, 65, 63),    # 6 stones\n        (108, 88, 77),   # 7 warm contour\n        (156, 117, 75),  # 8 bronze\n        (207, 152, 83),  # 9 amber\n        (244, 193, 104), # 10 fire\n        (255, 226, 150), # 11 fire core\n        (90, 89, 112),   # 12 mist\n        (47, 54, 69),    # 13 pine\n        (24, 29, 40),    # 14 forest\n        (212, 207, 184), # 15 moon\n    ]\n    im.putpalette([v for color in colors for v in color] + [0] * (768 - 48))\n    d.rectangle((0, 0, 255, 223), fill=1)\n\n    # Unlit night sky with sparse, hand-dithered stars.\n    d.rectangle((0, 0, 255, 92), fill=2)\n    d.polygon([(0, 64), (44, 62), (94, 69), (146, 58), (200, 71), (255, 59), (255, 112), (0, 112)], fill=1)\n    rng = random.Random(1193)\n    for _ in range(28):\n        x, y = rng.randrange(8, 248), rng.randrange(9, 73)\n        if not (x < 196 and y > 19):\n            d.point((x, y), fill=12 if _ % 3 else 7)\n    # A hard-edged moon: no gradients and no expensive effects.\n    d.ellipse((203, 24, 241, 62), fill=12)\n    d.ellipse((207, 27, 237, 57), fill=15)\n    d.ellipse((215, 33, 225, 41), fill=12)\n    d.point((228, 48), fill=12)\n    d.line((203, 62, 240, 62), fill=3)\n\n    # Layered hills and trees behind the chapel.\n    d.polygon([(0, 111), (36, 90), (72, 105), (112, 87), (154, 103), (195, 91), (255, 105), (255, 194), (0, 194)], fill=3)\n    d.polygon([(0, 137), (38, 112), (77, 127), (123, 108), (160, 131), (203, 112), (255, 127), (255, 202), (0, 202)], fill=14)\n    for x, y, r in [(6, 115, 22), (28, 123, 20), (162, 130, 18), (174, 120, 23), (249, 129, 18)]:\n        d.rectangle((x-2, y, x+2, y+r+20), fill=0)\n        for row, span in ((-30, 4), (-21, 9), (-12, 13), (0, 16)):\n            d.polygon([(x, y+row-10), (x-span, y+row+11), (x+span, y+row+11)], fill=13 if x < 170 else 14)\n        d.line((x, y-33, x, y+8), fill=4)\n\n    # Timber chapel with wooden cupola and Orthodox cross.\n    d.polygon([(175, 114), (215, 85), (255, 114)], fill=0)\n    d.polygon([(179, 115), (215, 92), (250, 115)], fill=5)\n    for x in range(183, 252, 9):\n        d.line((x, 113, 215, 93), fill=4)\n    d.rectangle((187, 115, 245, 188), fill=4)\n    for y in range(121, 187, 11):\n        d.line((188, y, 244, y), fill=6)\n    for x in (194, 203, 229, 239):\n        d.line((x, 117, x, 188), fill=3)\n    d.rectangle((210, 137, 225, 181), fill=0)\n    d.rectangle((213, 140, 222, 174), fill=9)\n    d.rectangle((216, 142, 220, 172), fill=10)\n    d.line((217, 139, 217, 175), fill=0)\n    d.line((210, 155, 225, 155), fill=0)\n    d.polygon([(205, 88), (215, 76), (225, 88)], fill=5)\n    d.rectangle((212, 76, 218, 91), fill=4)\n    d.line((215, 63, 215, 81), fill=8, width=2)\n    d.line((209, 69, 221, 69), fill=8, width=2)\n    d.line((211, 76, 219, 74), fill=8)\n\n    # Stairway leading down; strong perspective with only a few shapes.\n    d.polygon([(189, 180), (245, 180), (255, 223), (153, 223)], fill=0)\n    for j in range(6):\n        y = 181 + j*j + 2*j\n        if y > 218: break\n        left = 189 - (y - 180)//2\n        right = 245 + (y - 180)//3\n        d.line((max(0, left), y, min(255, right), y), fill=6 if j%2==0 else 4, width=2)\n    d.line((190, 181, 163, 223), fill=6)\n    d.line((245, 181, 254, 223), fill=6)\n\n    # Lone wanderer at the entrance, holding a torch.\n    d.ellipse((194, 164, 201, 172), fill=0)\n    d.polygon([(194, 172), (201, 172), (207, 195), (187, 195)], fill=0)\n    d.line((193, 193, 191, 201), fill=0, width=3)\n    d.line((201, 193, 205, 200), fill=0, width=3)\n    d.line((192, 178, 182, 173), fill=0, width=3)\n    d.line((182, 177, 180, 160), fill=7, width=2)\n    d.polygon([(180, 149), (176, 157), (178, 162), (183, 162), (186, 157)], fill=9)\n    d.polygon([(181, 152), (179, 157), (182, 161), (184, 157)], fill=11)\n    for x, y in ((175, 150), (187, 147), (190, 154)):\n        d.point((x,y), fill=9)\n\n    # Menu slab: fixed dark field for clear Cyrillic overlay text.\n    d.rectangle((14, 88, 174, 178), fill=0)\n    d.rectangle((16, 90, 172, 176), outline=6)\n    d.line((17, 90, 53, 90), fill=8)\n    d.line((17, 175, 52, 175), fill=8)\n    d.rectangle((17, 101, 19, 164), fill=4)\n    for y in (112, 136, 160):\n        d.line((36, y, 161, y), fill=3)\n    # Simple rune ornaments in empty corners.\n    for x, y in ((20, 92), (168, 92), (20, 174), (168, 174)):\n        d.point((x, y), fill=10)\n    # Top/bottom framing, separated from text region.\n    d.line((13, 16, 104, 16), fill=5)\n    d.line((112, 16, 162, 16), fill=5)\n    d.rectangle((10, 14, 12, 18), fill=8)\n    d.rectangle((162, 14, 164, 18), fill=8)\n    d.rectangle((0, 198, 255, 223), fill=0)\n    d.line((12, 198, 244, 198), fill=6)\n    d.line((12, 199, 80, 199), fill=8)\n    d.rectangle((242, 197, 244, 200), fill=8)\n    return im'
OLD_MENU = '} else if (g->mode == G_MENU) {\n        text(3, 3, TXT_TITLE);\n        text(3, 5, TXT_SUBTITLE);\n        text(3, 7, TXT_YEAR);\n        text(4, 11, TXT_NEW);\n        text(4, 14, TXT_HELP);\n        text(4, 17, TXT_CREDITS);\n        text(2, 11 + g->option * 3, ">");\n        text(3, 25, TXT_PRESS);\n    } else if (g->mode == G_HELP || g->mode == G_CREDITS) {'
NEW_MENU = '} else if (g->mode == G_MENU) {\n        /* Night of Chernorechye: menu positions align with the painted slab. */\n        text(3, 3, TXT_TITLE);\n        text(3, 5, TXT_SUBTITLE);\n        text(3, 8, TXT_YEAR);\n        text(5, 12, TXT_NEW);\n        text(5, 15, TXT_HELP);\n        text(5, 18, TXT_CREDITS);\n        text(3, 12 + g->option * 3, ">");\n        text(3, 26, TXT_PRESS);\n    } else if (g->mode == G_HELP || g->mode == G_CREDITS) {'

assets = ASSETS.read_text(encoding='utf-8')
pattern = r'(?ms)^def title\(\):\n.*?(?=^def splash\(\):)'
replacement = NEW_TITLE + '\n\n'
updated_assets, count = re.subn(pattern, lambda _: replacement, assets)
if count != 1:
    raise SystemExit('Cannot find exactly one title() before splash() in build_assets.py')

video = VIDEO.read_text(encoding='utf-8')
if OLD_MENU in video:
    updated_video = video.replace(OLD_MENU, NEW_MENU, 1)
elif NEW_MENU in video:
    updated_video = video
else:
    raise SystemExit('Cannot find original G_MENU block in Data/platform/video.c; no files changed')

if assets != updated_assets:
    ASSETS.with_name(ASSETS.name + '.menu-backup').write_text(assets, encoding='utf-8')
    ASSETS.write_text(updated_assets, encoding='utf-8')
if video != updated_video:
    VIDEO.with_name(VIDEO.name + '.menu-backup').write_text(video, encoding='utf-8')
    VIDEO.write_text(updated_video, encoding='utf-8')

print('Menu changed. Backups: *.menu-backup')
print('Next: python3 tools/build_assets.py')
print('Then: export PVSNESLIB_HOME="$PWD/third_party/pvsneslib" && make')
