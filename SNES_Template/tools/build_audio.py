#!/usr/bin/env python3
"""Build native BRR/tracker audio and full-length MSU-1 music from supplied masters."""
import ctypes as C
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
try:
    import numpy as np
except ImportError:
    for directory in (ROOT/'third_party/python/lib', ROOT/'.venv/lib'):
        sys.path.extend(str(p) for p in directory.glob('python*/site-packages'))
    import numpy as np
SOURCE = ROOT/'assets/audio'
OUT = ROOT/'assets/generated/audio'
STREAM_BYTES = 4096
PROFILES = [
    ('title', 'title', [('wind', .18)], True),
    ('university', None, [('university_room', .38)], False),
    ('basement', None, [('university_room', .23), ('river', .23)], False),
    ('arrival', None, [('river', .32), ('wind', .15)], False),
    ('village_day', 'explore', [('wind', .15), ('village_life', .30)], None),
    ('village_night', 'explore', [('wind', .16), ('night', .32)], None),
    ('forest_day', 'explore', [('wind', .15), ('leaves', .24), ('river', .12)], None),
    ('forest_night', 'explore', [('night', .25), ('leaves', .20), ('river', .12)], None),
    ('chapel', 'chapel_crypt', [('stone_room', .20)], None),
    ('crypt', 'chapel_crypt', [('stone_room', .34)], None),
    ('ambush', 'ambush', [('wind', .10), ('leaves', .15), ('night', .12)], False),
    ('final', 'final', [('stone_room', .24)], None),
    ('ending_guardian', 'ending_guardian', [('wind', .13), ('village_life', .14)], False),
    ('ending_silent', 'ending_silent', [('wind', .10)], False),
    ('ending_witnesses', 'ending_witnesses', [('university_room', .16)], False),
]
MUSIC = {
    'title': 'selected/background_sound.mp3',
    'explore': 'selected/background_sound.mp3',
    'ambush': 'selected/background_sound2.mp3',
    'chapel_crypt': 'selected/background_sound.mp3',
    'final': 'selected/background_sound2.mp3',
    'ending_guardian': 'prototype/music/music_ending_guardian.wav',
    'ending_silent': 'prototype/music/music_ending_silent.wav',
    'ending_witnesses': 'prototype/music/music_ending_witnesses.wav',
}
COMMON = ['bow_draw', 'bow_ready', 'player_heartbeat', 'bow_release_weak',
    'bow_release_strong', 'player_hurt_01', 'player_hurt_02', 'shade_warning',
    'crawler_warning', 'enemy_lunge', 'arrow_hit_enemy_01', 'arrow_hit_enemy_02', 'player_shove']
FOX = COMMON[:7] + ['fox_warning_01', 'fox_warning_02', 'fox_charge',
    'fox_hurt_01', 'fox_hurt_02', 'fox_retreat']


class SoundInfo(C.Structure):
    _fields_ = [('frames', C.c_int64), ('samplerate', C.c_int), ('channels', C.c_int),
               ('format', C.c_int), ('sections', C.c_int), ('seekable', C.c_int)]


def decode(path):
    """Use system libsndfile for WAV/MP3, or ffmpeg when it is unavailable."""
    library = ctypes.util.find_library('sndfile')
    if library:
        lib = C.CDLL(library)
        lib.sf_open.argtypes = [C.c_char_p, C.c_int, C.POINTER(SoundInfo)]
        lib.sf_open.restype = C.c_void_p
        lib.sf_readf_float.argtypes = [C.c_void_p, C.c_void_p, C.c_int64]
        lib.sf_readf_float.restype = C.c_int64
        lib.sf_close.argtypes = [C.c_void_p]
        info = SoundInfo()
        handle = lib.sf_open(os.fsencode(path), 16, C.byref(info))
        if not handle:
            raise ValueError('Cannot decode '+str(path))
        try:
            data = np.empty((info.frames, info.channels), np.float32)
            count = lib.sf_readf_float(handle, data.ctypes.data, info.frames)
            if count <= 0:
                raise ValueError('Empty audio decode: '+str(path))
            data = data[:count]
        finally:
            lib.sf_close(handle)
        return data, info.samplerate
    if path.suffix == '.wav':
        with wave.open(str(path), 'rb') as f:
            if f.getsampwidth() != 2:
                raise ValueError('Expected PCM16: '+str(path))
            data = np.frombuffer(f.readframes(f.getnframes()), '<i2') / 32768.
            return data.reshape(-1, f.getnchannels()), f.getframerate()
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
        '-f', 'f32le', '-ac', '2', '-ar', '44100', '-'])
    return np.frombuffer(data, '<f4').reshape(-1, 2), 44100


def resample(data, source_rate, rate):
    if source_rate == rate:
        return data.copy()
    cutoff = min(1., rate/source_rate)*.88
    taps = max(63, int(24/cutoff) | 1)
    x = np.arange(taps)-taps//2
    kernel = np.sinc(x*cutoff)*np.hanning(taps)
    kernel /= kernel.sum()
    filtered = np.convolve(data, kernel, 'same')
    return np.interp(np.arange(round(len(data)*rate/source_rate))*source_rate/rate,
                     np.arange(len(data)), filtered)


def pcm(data, peak=.72, loop=False):
    data = np.asarray(data, dtype=np.float64).copy()
    data -= data.mean()
    maximum = np.max(np.abs(data))
    if maximum:
        data *= min(4., peak/maximum)
    fade = min(len(data)//4, 128 if loop else 48)
    data[:fade] *= np.linspace(0, 1, fade)
    data[-fade:] *= np.linspace(1, 0, fade)
    data = np.pad(data, (0, (-len(data)) % 16))
    return np.clip(np.rint(data*32767), -32768, 32767).astype('<i2')


def encode_brr(samples):
    """Filter-0 encoder; account for the DSP's doubled 15-bit decoded values."""
    samples = np.pad(np.asarray(samples, np.int32), (0, (-len(samples)) % 16))
    blocks = samples.reshape(-1, 16)/2
    shifts = np.clip(np.ceil(np.log2(np.maximum(1, np.max(np.abs(blocks), axis=1))/7)), 0, 12).astype(int)
    values = np.clip(np.rint(blocks/(2.**shifts[:, None])), -8, 7).astype(np.int8) & 15
    out = np.empty((len(blocks), 9), np.uint8)
    out[:, 0] = shifts << 4
    out[-1, 0] |= 1
    out[:, 1:] = (values[:, ::2] << 4) | values[:, 1::2]
    return out.tobytes()


def write_it(path, samples, volumes=None, mute_channel=None):
    """Start looped samples once and hold order 1 without retriggering them."""
    n = len(samples)
    header = bytearray(192)
    header[:4] = b'IMPM'
    header[4:30] = path.stem.encode()[:26].ljust(26, b'\0')
    struct.pack_into('<9H', header, 30, 0x0410, 3, n, n, 2, 0x0214, 0x0214, 13, 0)
    header[48:54] = bytes([128, 64, 6, 125, 128, 0])
    header[64:128] = bytes([32]*64)
    header[128:192] = bytes([64]*64)
    if mute_channel is not None:
        header[128+mute_channel] = 0
    tables = 195
    result = header + bytes([0, 1, 255]) + bytes((n*2+2)*4)
    for i in range(n):
        struct.pack_into('<I', result, tables+i*4, len(result))
        instrument = bytearray(554)
        instrument[:4] = b'IMPI'
        instrument[24:26] = bytes([128, 32])
        instrument[64:304] = b''.join(bytes([note, i+1]) for note in range(120))
        result += instrument
    for i, (name, data, rate, loop) in enumerate(samples):
        struct.pack_into('<I', result, tables+(n+i)*4, len(result))
        sample = bytearray(80)
        sample[:4] = b'IMPS'
        sample[4:16] = name.encode()[:12].ljust(12, b'\0')
        sample[17:20] = bytes([64, 3 | (16 if loop else 0), 64])
        sample[20:46] = name.encode()[:26].ljust(26, b'\0')
        sample[46] = 1
        struct.pack_into('<7I', sample, 48, len(data), 0, len(data), rate, 0, 0, len(result)+80)
        result += sample + data.tobytes()
    first = bytearray()
    if volumes is not None:
        for channel, volume in enumerate(volumes):
            first += bytes([0x81+channel, 7, 60, channel+1, volume])
    first.append(0)
    hold = bytes(63) + bytes([0x81, 8, 2, 1, 0])
    for i, (rows, data) in enumerate(((1, first), (64, hold))):
        struct.pack_into('<I', result, tables+(n*2+i)*4, len(result))
        result += struct.pack('<HHI', len(data), rows, 0) + data
    path.write_bytes(result)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT/'Data/content').mkdir(parents=True, exist_ok=True)
    (ROOT/'build').mkdir(exist_ok=True)
    sources = {}
    def read(relative):
        if relative not in sources:
            sources[relative] = decode(SOURCE/relative)
        return sources[relative]
    def mono(relative, rate, seconds=None, start=0):
        data, original_rate = read(relative)
        end = len(data) if seconds is None else int((start+seconds)*original_rate)
        return resample(data[int(start*original_rate):end].mean(axis=1), original_rate, rate)
    steps = {}
    for style, filename in [('clean', 'steps_sound_clean.mp3'), ('echo', 'sounds_steps_echo.mp3')]:
        signal = mono('selected/'+filename, 4000)
        energy = np.convolve(signal**2, np.ones(80)/80, 'same')
        peaks = []
        for index in np.argsort(energy)[::-1]:
            if index < 100 or index+900 >= len(signal):
                continue
            if all(abs(int(index)-old) > 1600 for old in peaks):
                peaks.append(int(index))
            if len(peaks) == 3:
                break
        if len(peaks) != 3:
            raise ValueError('Could not isolate three steps from '+filename)
        steps[style] = [(signal[p-100:p+(780 if style == 'echo' else 540)], p-100) for p in sorted(peaks)]
    effects, records = {}, []
    paths = sorted((SOURCE/'prototype/effects').glob('*.wav'))
    paths += [SOURCE/'prototype/ambience'/name for name in ('bird_call.wav', 'water_drip.wav', 'wood_creak.wav')]
    for path in paths:
        name, relative, start = path.stem, str(path.relative_to(SOURCE)), 0
        if name.startswith('step_'):
            style = 'echo' if name.startswith(('step_stone', 'step_university')) else 'clean'
            data, offset = steps[style][int(name[-2:])-1]
            relative = 'selected/'+('sounds_steps_echo.mp3' if style == 'echo' else 'steps_sound_clean.mp3')
            start = offset/4000
        else:
            data = mono(relative, 4000)
        data = pcm(data, .64 if name.startswith(('step_', 'ui_')) else .78)
        brr = encode_brr(data)
        if len(brr) > STREAM_BYTES:
            raise ValueError('Effect exceeds SPC stream region: '+name)
        (OUT/(name+'.brr')).write_bytes(brr)
        effects[name] = (data, 4000)
        records.append(dict(id=name, source=relative, source_start_seconds=start,
                            duration=len(data)/4000, brr_bytes=len(brr)))
    names = sorted(effects)
    ids = {name: i for i, name in enumerate(names)}
    include = ['/* Generated by tools/build_audio.py. */', '#ifndef CHERNORECHYE_AUDIO_IDS_H',
        '#define CHERNORECHYE_AUDIO_IDS_H', 'enum AudioId {']
    include += ['    S_'+name.upper()+',' for name in names]
    include += ['    S_COUNT, S_NONE = 255', '};', 'enum AudioProfile {']
    include += ['    AP_'+name.upper()+',' for name, *_ in PROFILES]
    include += ['    AP_COUNT', '};', '#endif']
    (ROOT/'Data/include/audio_ids.h').write_text('\n'.join(include)+'\n')
    asm = ['; Imported audio. Generated by tools/build_audio.py.', '.include "hdr.asm"']
    for name in names:
        asm += [f'.section "audio_{name}" superfree', f'audio_{name}:',
                f'.incbin "assets/generated/audio/{name}.brr"', '.ends']
    asm += ['.section "audio_stream_table" superfree', 'audio_stream_table:']
    for name in names:
        volume = 5 if name.startswith('step_') else (7 if name.startswith('ui_') else 11)
        asm += [f'.db 2, 8, {volume}', f'.dw {(OUT/(name+".brr")).stat().st_size//9}',
                f'.dw audio_{name}', f'.db :audio_{name}']
    asm += ['audio_durations:', '.db '+','.join(str(min(255, round(len(effects[n][0])/4000*60)+3)) for n in names), '.ends']
    residents = sorted(set(COMMON+FOX+['ui_move','ui_confirm'] + [n for n in names if n.startswith('step_')]))
    write_it(OUT/'effects.it', [(n, *effects[n], False) for n in residents])
    modules, module_sizes, music_samples = [OUT/'effects.it'], [], {}
    for name, relative in MUSIC.items():
        data, rate = read(relative)
        duration = len(data)/rate
        native_rate = 4000 if duration <= 14 or duration > 40 else 2000
        seconds = min(duration, 12) if duration > 40 else duration
        if name == 'title':
            native_rate, seconds = 2000, 8
        music_samples[name] = pcm(mono(relative, native_rate, seconds), .62, True), native_rate
    for name, music, layers, torch in PROFILES:
        ambience = np.zeros(8000)
        for layer, gain in layers:
            data = mono('prototype/ambience/'+layer+'.wav', 2000, 4)
            ambience[:len(data)] += data*gain
        ambient_pcm = pcm(ambience, .28, True)
        fire = pcm(mono('selected/burning_torch_sound.mp3', 2000, 2, 8), .25, True)
        for lit in (0, 1):
            for msu in (0, 1):
                samples, volumes = [], []
                if music and not msu:
                    data, rate = music_samples[music]
                    samples.append((music, data, rate, True)); volumes.append(27 if name == 'ambush' else 34)
                samples.append(('ambient_'+name, ambient_pcm, 2000, True)); volumes.append(32)
                if torch is True or torch is None:
                    samples.append(('torch', fire, 2000, True)); volumes.append(28)
                path = OUT/(name+f'_{lit}_{msu}.it')
                write_it(path, samples, volumes, len(samples)-1 if torch is None and not lit else None)
                modules.append(path)
                module_sizes.append(sum((len(s[1])+15)//16*9 for s in samples)+2200)
    sdk = Path(os.environ.get('PVSNESLIB_HOME', ROOT/'third_party/pvsneslib'))
    driver_object = OUT/'spc700.obj'
    subprocess.run([str(sdk/'devkitsnes/bin/wla-spc700'), '-o', str(driver_object),
                    str(ROOT/'Data/audio/spc700.asm')], check=True)
    driver_link = OUT/'spc700.link'
    driver_link.write_text('[objects]\n'+str(driver_object)+'\n')
    subprocess.run([str(sdk/'devkitsnes/bin/wlalink'), '-b', str(driver_link),
                    str(OUT/'spc700.raw')], check=True)
    driver = (OUT/'spc700.raw').read_bytes().rstrip(b'\0')
    if len(driver)+0x400 > 0x1a00:
        raise ValueError('SPC driver overlaps the module region')
    (OUT/'spc700.bin').write_bytes(driver)
    result = subprocess.run([str(sdk/'devkitsnes/tools/smconv'), '-s', '-V', '-o',
        str(OUT/'soundbank')]+[str(p) for p in modules], cwd=ROOT, capture_output=True, text=True)
    (ROOT/'build/audio-converter.log').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError('smconv failed: '+result.stdout[-4000:]+result.stderr)
    bank = (OUT/'soundbank.bnk').read_bytes()
    address = int.from_bytes(bank[4:6], 'little')-0x8000 + bank[6]*0x8000
    count = struct.unpack_from('<H', bank, address+2)[0]
    source_ids = list(struct.unpack_from('<%dH'%count, bank, address+4))
    module_start = address+4+count*2
    table = module_start+32+200+256
    resident_sources = {}
    for i, name in enumerate(residents):
        sample = bank[table+i] + bank[table+64+i]*256 - 0x1a00
        resident_sources[name] = source_ids[bank[module_start+sample+4]]
    asm += ['.section "audio_residents" superfree', 'audio_residents:']
    slot_tables = []
    max_spc = 0
    for material in ('ground', 'wood', 'stone', 'university'):
        for fox in (0, 1):
            slots = [f'step_{material}_{v:02d}' for v in (1, 2, 3)] + (FOX if fox else COMMON)
            assert len(slots) == 16
            slot_tables.append(slots)
            total = sum(len(encode_brr(effects[n][0])) for n in slots)
            max_spc = max(max_spc, max(module_sizes)+total+STREAM_BYTES+0x1a00)
            if max_spc > 65280:
                raise ValueError('Music + effects + driver exceeds SPC RAM')
            asm += ['.dw '+','.join(str(resident_sources[n]) for n in slots)]
    title_slots = [f'step_ground_{v:02d}' for v in (1,2,3)]+['ui_move','ui_confirm']+COMMON[2:]
    slot_tables.append(title_slots)
    asm += ['.dw '+','.join(str(resident_sources[n]) for n in title_slots)]
    asm += ['audio_resident_ids:']
    for slots in slot_tables:
        asm += ['.db '+','.join(str(ids[n]) for n in slots)]
    asm += ['audio_resident_lookup:']
    for slots in slot_tables:
        asm += ['.db '+','.join(str(slots.index(n) if n in slots else 255) for n in names)]
    asm += ['audio_modules:', '.db '+','.join(str(i+1) for i in range(len(PROFILES)*4)),
        'audio_music_tracks:', '.db '+','.join(str(list(MUSIC).index(music)+1 if music else 0)
        for _, music, *_ in PROFILES), '.ends']
    for i, start in enumerate(range(0, len(bank), 32768)):
        asm += [f'.bank {40+i} slot 0', '.org 0', f'.section "audio_bank_{i}" force', f'audio_bank_{i}:',
            f'.incbin "assets/generated/audio/soundbank.bnk" skip {start} read {min(32768, len(bank)-start)}', '.ends']
    (ROOT/'Data/content/audio.asm').write_text('\n'.join(asm)+'\n')
    msu_dir = ROOT/'build/msu1'
    msu_dir.mkdir(parents=True, exist_ok=True)
    (msu_dir/'chernorechye.msu').write_bytes(b'')
    for track, (name, relative) in enumerate(MUSIC.items(), 1):
        data, rate = read(relative)
        if data.shape[1] == 1:
            data = np.repeat(data, 2, axis=1)
        if rate != 44100:
            data = np.stack([resample(data[:, ch], rate, 44100) for ch in range(2)], axis=1)
        data = np.clip(np.rint(data*.72*32767), -32768, 32767).astype('<i2')
        (msu_dir/f'chernorechye-{track}.pcm').write_bytes(b'MSU1'+struct.pack('<I', 0)+data.tobytes())
    manifest = dict(effects=records, music=[dict(id=n, track=i+1, source=p,
        source_seconds=len(read(p)[0])/read(p)[1], native_seconds=len(music_samples[n][0])/music_samples[n][1],
        native_rate=music_samples[n][1]) for i, (n, p) in enumerate(MUSIC.items())],
        profiles=[p[0] for p in PROFILES], native_bank_bytes=len(bank),
        stream_region_bytes=STREAM_BYTES, resident_slots=16, max_module_estimate_bytes=max(module_sizes),
        max_spc_estimate_bytes=max_spc, spc_memory_limit=65280,
        masters={str(p.relative_to(SOURCE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SOURCE.rglob('*')) if p.suffix.lower() in ('.wav', '.mp3')},
        replacements={'step_*': 'selected/steps_sound_clean.mp3 or sounds_steps_echo.mp3',
            'torch_fire': 'selected/burning_torch_sound.mp3',
            'music_title/explore/chapel_crypt': MUSIC['explore'], 'music_ambush/final': MUSIC['ambush']})
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    print(f'Imported {len(effects)} effects, 15 ambience profiles, 8 music tracks; bank {len(bank)} B')


if __name__ == '__main__':
    main()
