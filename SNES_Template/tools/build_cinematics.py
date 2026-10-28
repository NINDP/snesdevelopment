"""Convert checked-in cinematic artwork into native SNES indexed backgrounds."""
from pathlib import Path
import numpy as np
from PIL import Image

SOURCE = Path(__file__).resolve().parents[1] / 'assets/cinematics'


def indexed_scene(name, height=144, banks=(0, 2, 3, 4, 5, 6, 7), world=False):
    source = name.convert('RGB') if isinstance(name, Image.Image) else Image.open(SOURCE / name).convert('RGB')
    width = source.width if isinstance(name, Image.Image) else 256
    if world:
        source_width, source_height = source.size
        source = source.crop((0, source_height*24//224, source_width, source_height*192//224))
    source = source.resize((width, height), Image.Resampling.LANCZOS)
    # Seven native 16-color banks. Bank 1 is reserved for the text layer.
    # Cluster 8x8 tiles, then derive a local palette for each cluster.
    pixels = np.asarray(source, dtype=np.int32)
    columns = width // 8
    tiles = pixels.reshape(height//8, 8, columns, 8, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 64, 3)
    features = np.concatenate((tiles.mean(axis=1), tiles.std(axis=1)), axis=1)
    centers = [features[np.argmin(features[:, :3].sum(axis=1))]]
    for _ in range(len(banks)-1):
        distance = ((features[:, None, :] - np.array(centers)[None, :, :])**2).sum(axis=2)
        centers.append(features[np.argmax(distance.min(axis=1))])
    centers = np.array(centers)
    for _ in range(12):
        labels = ((features[:, None, :] - centers[None, :, :])**2).sum(axis=2).argmin(axis=1)
        for group in range(len(banks)):
            if np.any(labels == group):
                centers[group] = features[labels == group].mean(axis=0)
    palette = [0] * 384
    indexed = np.zeros((height, width), dtype=np.uint8)
    for group, bank in enumerate(banks):
        members = np.flatnonzero(labels == group)
        if not len(members):
            continue
        sample = Image.fromarray(tiles[members].astype(np.uint8).reshape(-1, 64, 3))
        reduced = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT,
                                  dither=Image.Dither.NONE)
        colors = np.array(reduced.getpalette()[:45], dtype=np.int32).reshape(15, 3)
        palette[bank*48+3:bank*48+48] = colors.reshape(-1).tolist()
        for member in members:
            values = ((tiles[member, :, None, :] - colors[None, :, :])**2).sum(axis=2).argmin(axis=1)
            y, x = divmod(int(member), columns)
            indexed[y*8:y*8+8, x*8:x*8+8] = (values.reshape(8, 8) + 1 + bank*16)
    scene = Image.new('P', (width, 224), 0)
    scene.putpalette(palette + [0] * (768 - len(palette)))
    image = Image.frombytes('P', (width, height), indexed.tobytes())
    scene.paste(image, (0, 24 if world else 0))
    if world:
        for bright, dim in ((0, 2), (3, 5), (4, 6)):
            for color in range(16):
                offset = bright*48 + color*3
                destination = dim*48 + color*3
                palette[destination:destination+3] = [int(palette[offset]*.24),
                                                       int(palette[offset+1]*.29),
                                                       int(palette[offset+2]*.36)]
        scene.putpalette(palette + [0] * (768 - len(palette)))
    return scene


def scenes():
    # Both screens share tiles and palettes: crossing the doorway needs only
    # BG1 scroll writes, with no forced blank, DMA or palette replacement.
    panorama = Image.new('RGB', (512, 128))
    for column, name in enumerate(('OpeningGymScene.png', 'Scene2Corridor-down.png')):
        panorama.paste(Image.open(SOURCE / name).convert('RGB').resize(
            (256, 128), Image.Resampling.LANCZOS), (column * 256, 0))
    panorama = indexed_scene(panorama, 128)
    panorama.paste(0, (0, 0, 8, 8))
    return [panorama,
            indexed_scene('basement.png'), indexed_scene('arrival-torch.png')]


def world_scenes():
    return [indexed_scene(name+'.png', 168, banks=(0, 3, 4), world=True)
            for name in ('village', 'forest', 'chapel', 'cellar')]
