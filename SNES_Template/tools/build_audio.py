#!/usr/bin/env python3
"""Original synthetic SFX: WAV for the designer and filter-0 BRR for SPC."""
import math,random,struct,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/generated'
def encode_brr(samples):
    samples=list(samples); samples+=[0]*((-len(samples))%16); out=bytearray()
    for off in range(0,len(samples),16):
        block=samples[off:off+16]; peak=max(abs(x) for x in block)
        shift=min(12,max(0,math.ceil(math.log2(max(1,peak)/7))))
        values=[max(-8,min(7,round(x/(1<<shift))))&15 for x in block]
        out.append((shift<<4)|(1 if off+16==len(samples) else 0))
        out.extend((values[i]<<4)|values[i+1] for i in range(0,16,2))
    return bytes(out)
def main():
    (ROOT/'Data/content').mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(1193); rate=8000
    # A 60 Hz thump needs no 8 kHz sample stream. Preserve its 100 ms envelope
    # at 2 kHz: thirteen BRR blocks fit the normal SPC startup transfer, so a
    # heartbeat cannot stall forest rendering with repeated streaming bursts.
    heartbeat_rate=2000
    heartbeat=[int(12000*math.sin(2*math.pi*60*i/heartbeat_rate)*math.exp(-i/40)) for i in range(200)]
    latch=[int(rng.uniform(-1,1)*8000*math.exp(-i/22)) for i in range(160)]
    seal=[int(8000*(math.sin(2*math.pi*440*i/rate)+.3*math.sin(2*math.pi*660*i/rate))*math.exp(-i/750)) for i in range(2400)]
    asm=['; Original generated BRR effects.','.include "hdr.asm"']
    for name,samples in [('heartbeat',heartbeat),('latch',latch),('seal',seal)]:
        (OUT/(name+'.brr')).write_bytes(encode_brr(samples))
        with wave.open(str(OUT/(name+'.wav')),'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(heartbeat_rate if name=='heartbeat' else rate)
            f.writeframes(struct.pack('<%dh'%len(samples),*samples))
        asm+=['.section "sfx_%s" superfree'%name,name+'_sound:','.incbin "assets/generated/%s.brr"'%name,name+'_sound_end:','.ends']
    (ROOT/'Data/content/audio.asm').write_text('\n'.join(asm)+'\n')
    print('Generated original heartbeat, latch and seal WAV/BRR')
if __name__=='__main__': main()
