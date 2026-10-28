"""Native asset contracts for the supplied five-character reference sheet."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_npcs import COLORS, actor


class ReferenceSprites(unittest.TestCase):
    def test_five_complete_characters_fit_the_obj_budget(self):
        self.assertEqual(len(COLORS), 16)
        for role in range(5):
            frames = [actor(role, phase) for phase in range(9)]
            for frame in frames:
                self.assertEqual(frame.size, (32, 48))
                bounds = frame.getbbox()
                self.assertLessEqual(bounds[2]-bounds[0], 24)
                self.assertLessEqual(bounds[3]-bounds[1], 36)
                pixels = np.asarray(frame)
                self.assertLessEqual(int(pixels.max()), 15)
                self.assertGreater(np.count_nonzero(pixels), 200)
                self.assertLess(np.count_nonzero(pixels), 1250)
                self.assertTrue(np.any(pixels[45:]))
            # Three idle samples must remain separate DMA payloads. Facing
            # profiles and the rear must also survive palette reduction.
            self.assertEqual(len({frame.tobytes() for frame in frames[:3]}), 3)
            self.assertEqual(len({frames[index].tobytes() for index in (0, 3, 5, 7)}), 4)


if __name__ == '__main__':
    unittest.main()
