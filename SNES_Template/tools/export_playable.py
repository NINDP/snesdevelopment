#!/usr/bin/env python3
"""Keep the local playable copies in sync with the successfully linked ROM.

The full source/review package is still produced by tools/package.py after its
complete validation suite. This small archive is for opening the current game.
"""
import hashlib
import json
import os
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'Nabla-Chernorechye-SNES.zip'
DOCUMENTS = ('STORY.md', 'AMBUSH.md', 'SCENES.md', 'STORY_AUDIT.md',
             'STORY_REFERENCE.md', 'STORY_REFERENCE_V2.md', 'AUDIO.md', 'AUDIO_VALIDATION.md')


def export(root=ROOT):
    rom = (root/'chernorechye.sfc').read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    manifest = json.loads((root/'build/link_manifest.json').read_text())
    if len(rom) != 2097152 or digest != manifest['rom_sha256']:
        raise ValueError('ROM does not match the successful link manifest')
    complement, checksum = struct.unpack_from('<HH', rom, 0x7fdc)
    if complement ^ checksum != 65535 or sum(rom) & 65535 != checksum:
        raise ValueError('Invalid SNES checksum')
    sha = digest+'  chernorechye.sfc\n'
    readme = ('Текущая игровая сборка.\n\n'
              'Открой chernorechye.sfc заново через Load Game в эмуляторе.\n'
              'Reset уже открытой игры не перечитывает обновлённый файл.\n'
              'Для проверки сюжета начни новую историю без старого save state.\n'
              'Карты сохранены; изменения описаны в STORY.md.\n\n'
              'Это архив для запуска. Исходники находятся в репозитории.\n'
              'SHA-256: '+digest+'\n')
    dist = root/'dist'
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='export-', dir=dist) as temp:
        staging = Path(temp)
        (staging/'chernorechye.sfc').write_bytes(rom)
        (staging/'sha256.txt').write_text(sha)
        with zipfile.ZipFile(staging/ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('chernorechye.sfc', rom)
            archive.writestr('sha256.txt', sha)
            archive.writestr('README.txt', readme)
            for name in DOCUMENTS:
                archive.write(root/'docs'/name, name)
        for name in ('chernorechye.sfc', 'sha256.txt', ARCHIVE):
            os.replace(staging/name, dist/name)
        audio = root/'build/msu1'
        if audio.exists():
            files = [audio/'chernorechye.msu', *[audio/f'chernorechye-{n}.pcm' for n in range(1,9)]]
            if not all(p.is_file() for p in files):
                raise ValueError('Incomplete MSU-1 music pack')
            name = 'Nabla-Chernorechye-MSU1.zip'
            with zipfile.ZipFile(staging/name, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('chernorechye.sfc', rom)
                archive.writestr('sha256.txt', sha)
                archive.writestr('README.txt', readme+'\nДля полной музыки распакуй ВСЕ файлы рядом и открой ROM в эмуляторе с MSU-1.\n')
                archive.write(root/'docs/AUDIO.md', 'AUDIO.md')
                archive.write(root/'docs/AUDIO_VALIDATION.md', 'AUDIO_VALIDATION.md')
                for path in files:
                    archive.write(path, path.name)
            os.replace(staging/name, dist/name)
            # Local playable copies are ready to launch with full music too.
            for destination in (root, dist):
                for path in files:
                    installed = staging/path.name
                    shutil.copyfile(path, installed)
                    os.replace(installed, destination/path.name)
    print('Current playable ROM and archive exported to dist/: '+digest[:12])


if __name__ == '__main__':
    export()
