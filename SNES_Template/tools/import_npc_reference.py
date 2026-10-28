"""Convert the project's supplied character sheet into native SNES frames.

This is asset import, not a runtime image operation: the original PNG remains
intact in assets/characters. All game pixels use a shared 15-color OBJ palette.
"""
from collections import deque

import numpy as np
from PIL import Image

CENTERS = ((109, 241), (421, 545), (727, 848), (1025, 1152), (1330, 1456))
ROWS = ((268, 431), (448, 617), (633, 803), (814, 991))


def cut_sprite(source, center, row):
    top, bottom = row
    crop = source.crop((center-57, top, center+57, bottom)).convert('RGB')
    pixels = np.asarray(crop)
    # Remove only dark background reachable from the cell's perimeter. Dark
    # outlines and the priest's black coat remain solid inside the silhouette.
    background = pixels.max(axis=2) <= 28
    height, width = background.shape
    outside = np.zeros((height, width), dtype=bool)
    pending = deque()
    for x in range(width):
        pending.extend(((x, 0), (x, height-1)))
    for y in range(height):
        pending.extend(((0, y), (width-1, y)))
    while pending:
        x, y = pending.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        if outside[y, x] or not background[y, x]:
            continue
        outside[y, x] = True
        pending.extend(((x-1, y), (x+1, y), (x, y-1), (x, y+1)))
    # The supplied presentation sheet has isolated bright specks and an
    # occasional fragment of the neighbouring pose at a cell edge. Retain
    # disconnected boots/staff, but reject specks and cropped neighbours.
    foreground = ~outside
    visited = np.zeros_like(foreground)
    components = []
    for cy, cx in np.argwhere(foreground):
        if visited[cy, cx]:
            continue
        component = []
        pending = [(int(cx), int(cy))]
        while pending:
            x, y = pending.pop()
            if x < 0 or y < 0 or x >= width or y >= height:
                continue
            if visited[y, x] or not foreground[y, x]:
                continue
            visited[y, x] = True
            component.append((y, x))
            pending.extend((x+dx, y+dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
        if component:
            components.append(component)
    clean = np.zeros_like(foreground)
    largest_size = max(map(len, components), default=0)
    for component in components:
        if len(component) < 16:
            continue
        if len(component) < largest_size//2 and any(x == 0 or x == width-1 for _, x in component):
            continue
        for y, x in component:
            clean[y, x] = True
    alpha = Image.fromarray(clean.astype('uint8') * 255)
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError('Empty reference cell')
    rgba = crop.convert('RGBA')
    rgba.putalpha(alpha)
    return rgba.crop(bounds)


def load_reference(path, colors):
    source = Image.open(path).convert('RGB')
    if source.size != (1536, 1024):
        raise ValueError('Character reference must retain its original 1536x1024 size')
    palette = [component for color in colors for component in color] + [0]*720
    choices = np.asarray(colors[1:], dtype=np.int32)
    result = []
    for pair in CENTERS:
        cells = [cut_sprite(source, center, row) for row in ROWS for center in pair]
        # Keep a 24x36 body inside the established 32x48 DMA canvas. Feet
        # remain on the same baseline; NPCs no longer crowd the foreground.
        scale = min(24/max(im.width for im in cells), 36/max(im.height for im in cells))
        frames = []
        for cell in cells:
            size = (max(1, round(cell.width*scale)), max(1, round(cell.height*scale)))
            small = cell.resize(size, Image.Resampling.BOX)
            data = np.asarray(small)
            rgb = data[:, :, :3].astype(np.int32)
            # Weighted RGB distance preserves warm skin, red embroidery and
            # the blue skirt while keeping all five residents in one palette.
            delta = rgb[:, :, None, :] - choices[None, None, :, :]
            distance = (delta*delta*np.array((2, 3, 2))).sum(axis=3)
            indexed = (distance.argmin(axis=2)+1).astype('uint8')
            indexed[data[:, :, 3] < 128] = 0
            frame = Image.new('P', (32, 48), 0)
            frame.putpalette(palette)
            imported = Image.fromarray(indexed)
            frame.paste(imported, ((32-size[0])//2, 48-size[1]))
            frames.append(frame)
        # Preserve the existing front/front/blink IDs; add both profile
        # directions and the rear pair after them.
        blink = frames[0].copy()
        # The two front samples already have distinct eye/shoulder pixels.
        # A one-pixel brow darkening gives a brief third idle frame.
        values = np.asarray(blink).copy()
        for y in range(12, 32):
            for x in range(8, 24):
                if values[y, x] in (1, 2, 3, 4) and values[y-1, x] in (12, 13, 14):
                    values[y-1, x] = 12
        if np.array_equal(values, np.asarray(frames[0])):
            for y, x in np.argwhere((values == 13) | (values == 14)):
                if 12 <= y < 32:
                    values[y, x] = 12
                    break
        blink.putdata(values.ravel())
        result.append(frames[:2] + [blink] + frames[2:])
    return result
