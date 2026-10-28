"""A broken or ambiguous link must never publish over a tested ROM."""
import importlib.util
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('link_rom', Path(__file__).resolve().parents[1] / 'tools/link_rom.py')
link_rom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(link_rom)

class JournalLayoutTests(unittest.TestCase):
    def test_story_text_fits_journal_boxes(self):
        source = Path(__file__).resolve().parents[1]/'assets/story.json'
        for key, value in json.loads(source.read_text())['ui'].items():
            if not key.startswith(('J_', 'G_')):
                continue
            lines = [line for paragraph in value.split('\n')
                     for line in textwrap.wrap(paragraph, 30, break_long_words=False,
                                               break_on_hyphens=False) or ['']]
            with self.subTest(key=key):
                self.assertLessEqual(len(lines), 4 if key.startswith('J_') else 2)
                self.assertTrue(all(len(line) <= 30 for line in lines))

class LinkFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.previous_root = link_rom.ROOT
        link_rom.ROOT = self.root
        self.sdk = self.root / 'sdk'
        self.sdk.mkdir()
        (self.sdk / 'runtime.obj').write_bytes(b'sdk')
        self.obj = self.root / 'game.obj'
        self.obj.write_bytes(b'object')
        self.output = self.root / 'game.sfc'
        self.output.write_bytes(b'previous verified ROM')

    def tearDown(self):
        link_rom.ROOT = self.previous_root
        self.temporary.cleanup()

    def test_duplicate_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            link_rom.link(Path('/unused'), self.sdk, self.output, [self.obj, self.obj])
        self.assertEqual(self.output.read_bytes(), b'previous verified ROM')

    def test_incomplete_rom_cannot_replace_previous(self):
        fake = self.root / 'fake-linker'
        fake.write_text('#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\nPath(sys.argv[-1]).write_bytes(b"bad ROM")\n')
        fake.chmod(0o755)
        with self.assertRaisesRegex(ValueError, '1 MiB'):
            link_rom.link(fake, self.sdk, self.output, [self.obj])
        self.assertEqual(self.output.read_bytes(), b'previous verified ROM')

if __name__ == '__main__':
    unittest.main()
