#!/usr/bin/env python3
"""Link and publish a matching ROM/symbol pair, failing on any tool error."""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def link(linker, library_dir, output, objects):
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    libraries = sorted(library_dir.glob('*.obj'))
    inputs = [Path(p) for p in objects] + libraries
    if not libraries or not inputs:
        raise ValueError('No object files or SDK runtime libraries')
    canonical = [p.resolve() for p in inputs]
    if len(canonical) != len(set(canonical)):
        raise ValueError('Duplicate translation unit in link manifest')
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = ROOT / 'linkfile'
    manifest.write_text('[objects]\n' + '\n'.join(str(p) for p in inputs) + '\n')
    with tempfile.TemporaryDirectory(prefix='link-', dir=build) as temporary:
        rom = Path(temporary) / output.name
        command = [str(linker), '-d', '-s', '-v', '-A', '-c', '-L',
                   str(library_dir), str(manifest), str(rom)]
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        (build / 'link.log').write_text(result.stdout)
        if result.returncode:
            raise RuntimeError('Linker failed:\n' + result.stdout[-8000:])
        data = rom.read_bytes()
        if len(data) != 524288:
            raise ValueError('Expected 512 KiB LoROM')
        complement, checksum = struct.unpack_from('<HH', data, 0x7fdc)
        if complement ^ checksum != 65535 or sum(data) & 65535 != checksum:
            raise ValueError('SNES checksum/complement mismatch')
        symbols = rom.with_suffix('.sym')
        text = symbols.read_text().replace(':', '')
        if '_game' not in text or 'GameUpdate' not in text:
            raise ValueError('Incomplete symbols for this ROM')
        symbols.write_text(text)
        # Never leave an old ROM beside newly generated debug addresses.
        os.replace(rom, output)
        os.replace(symbols, output.with_suffix('.sym'))
        record={'rom_sha256':hashlib.sha256(data).hexdigest(),
                'symbols_sha256':hashlib.sha256(text.encode()).hexdigest(),
                'objects':[str(p) for p in objects], 'sdk_objects':[p.name for p in libraries]}
        (build/'link_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Linked 512 KiB LoROM; checksum and object manifest verified')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--linker', type=Path, required=True)
    parser.add_argument('--library-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('objects', nargs='+')
    args = parser.parse_args()
    link(args.linker, args.library_dir, args.output, args.objects)
