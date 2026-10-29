"""Guard the supplied masters, playback durations and native memory limits."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class AudioAssetTests(unittest.TestCase):
    def test_all_effects_and_selected_replacements_are_built(self):
        folder=ROOT/'assets/generated/audio'
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertEqual(len(manifest['effects']),84)
        self.assertEqual(len(manifest['music']),8)
        self.assertLessEqual(manifest['max_spc_estimate_bytes'],manifest['spc_memory_limit'])
        for entry in manifest['effects']:
            with self.subTest(sound=entry['id']):
                data=(folder/(entry['id']+'.brr')).read_bytes()
                self.assertEqual(len(data),entry['brr_bytes'])
                self.assertEqual(len(data)%9,0)
                self.assertTrue(data[-9]&1)
                self.assertLessEqual(len(data),manifest['stream_region_bytes'])
                self.assertAlmostEqual(len(data)//9*16/4000,entry['duration'])
                if entry['id'].startswith('step_'):
                    self.assertTrue(entry['source'].startswith('selected/'))
        for name,digest in manifest['masters'].items():
            self.assertEqual(hashlib.sha256((ROOT/'assets/audio'/name).read_bytes()).hexdigest(),digest)
        for entry in manifest['music']:
            pcm=ROOT/'build/msu1'/('chernorechye-%s.pcm'%entry['track'])
            self.assertEqual(pcm.read_bytes()[:8],b'MSU1\0\0\0\0')
            self.assertAlmostEqual((pcm.stat().st_size-8)/4/44100,entry['source_seconds'],places=3)
