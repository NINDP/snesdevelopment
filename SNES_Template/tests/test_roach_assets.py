"""Validate the fear trial's native PPU tile, palette and sprite budgets."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_assets import tile_image
from build_roach import build


class RoachAssets(unittest.TestCase):
    def test_native_background_and_large_obj_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            assembly = []
            build(out, assembly, tile_image)
            tiles = (out/'roach-yard.chr').read_bytes()
            entries = struct.unpack('<1024H', (out/'roach-yard.map').read_bytes())
            self.assertLessEqual(len(tiles), 768*32)
            self.assertTrue(all((tile & 1023) < len(tiles)//32 for tile in entries))
            self.assertEqual(len((out/'roach-yard.pal').read_bytes()), 32)
            self.assertEqual(len((out/'roach-actors.chr').read_bytes()), 2048)
            self.assertEqual(len((out/'roach-actors.pal').read_bytes()), 32)
            with Image.open(out/'roach-actors.png') as actors:
                self.assertEqual(actors.size, (128, 32))
                # The reference's white backdrop must not become an OBJ rectangle.
                self.assertEqual(actors.getpixel((7, 0))[3], 0)
                for left in (0, 32, 64):
                    self.assertIsNotNone(actors.crop((left,0,left+32,32)).getbbox())
            first = {path.name: path.read_bytes() for path in out.iterdir()}
            build(out, [], tile_image)
            self.assertEqual(first, {path.name: path.read_bytes() for path in out.iterdir()})


if __name__ == '__main__':
    unittest.main()
