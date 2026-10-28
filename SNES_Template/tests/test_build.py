"""A broken or ambiguous link must never publish over a tested ROM."""
import importlib.util
import hashlib
import json
import struct
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('link_rom', Path(__file__).resolve().parents[1] / 'tools/link_rom.py')
link_rom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(link_rom)
export_spec = importlib.util.spec_from_file_location('export_playable', Path(__file__).resolve().parents[1] / 'tools/export_playable.py')
export_playable = importlib.util.module_from_spec(export_spec)
export_spec.loader.exec_module(export_playable)

class PlayableExportTests(unittest.TestCase):
    def test_stale_copies_are_replaced_and_unlinked_rom_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for directory in ('build','docs','dist'):
                (root/directory).mkdir()
            rom=bytearray(1048576)
            checksum=510
            struct.pack_into('<HH',rom,0x7fdc,checksum^65535,checksum)
            digest=hashlib.sha256(rom).hexdigest()
            (root/'chernorechye.sfc').write_bytes(rom)
            (root/'build/link_manifest.json').write_text(json.dumps({'rom_sha256':digest}))
            for name in export_playable.DOCUMENTS:
                (root/'docs'/name).write_text(name)
            (root/'dist/chernorechye.sfc').write_bytes(b'old copy')
            export_playable.export(root)
            self.assertEqual((root/'dist/chernorechye.sfc').read_bytes(),rom)
            self.assertEqual((root/'dist/sha256.txt').read_text().split()[0],digest)
            with zipfile.ZipFile(root/'dist'/export_playable.ARCHIVE) as archive:
                self.assertEqual(archive.read('chernorechye.sfc'),rom)
            (root/'chernorechye.sfc').write_bytes(b'unlinked build')
            with self.assertRaisesRegex(ValueError,'link manifest'):
                export_playable.export(root)
            self.assertEqual((root/'dist/chernorechye.sfc').read_bytes(),rom)

class JournalLayoutTests(unittest.TestCase):
    def test_story_text_fits_journal_boxes(self):
        source = Path(__file__).resolve().parents[1]/'assets/story.json'
        for key, value in json.loads(source.read_text())['ui'].items():
            if not key.startswith(('J_', 'G_')):
                continue
            width = 25
            if key.startswith('J_'):
                value = value.replace('\n', ' ')
            lines = [line for paragraph in value.split('\n')
                     for line in textwrap.wrap(paragraph, width, break_long_words=False,
                                               break_on_hyphens=False) or ['']]
            with self.subTest(key=key):
                self.assertLessEqual(len(lines), 7 if key.startswith('J_') else 4)
                self.assertTrue(all(len(line) <= width for line in lines))

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
