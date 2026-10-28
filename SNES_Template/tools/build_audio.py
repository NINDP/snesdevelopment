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
    # A short two-partial bell fits one startup transfer while the forest is
    # animating. A long seal stream is unsuitable for a live time warning.
    chime=[int(9000*(math.sin(2*math.pi*420*i/2000)+.25*math.sin(2*math.pi*780*i/2000))*math.exp(-i/38)) for i in range(160)]
    bow=[int(11000*(.7*math.sin(2*math.pi*170*i/2000)+.3*rng.uniform(-1,1))*math.exp(-i/24)) for i in range(144)]
    impact=[int(10000*(math.sin(2*math.pi*(650*i/2000-950*(i/2000)**2))+.2*rng.uniform(-1,1))*math.exp(-i/30)) for i in range(160)]
    attack=[int(8500*(.6*math.sin(2*math.pi*(95*i/2000+120*(i/2000)**2))+
                            .4*rng.uniform(-1,1))*math.exp(-i/38)) for i in range(128)]
    shove=[int(9500*rng.uniform(-1,1)*math.sin(math.pi*i/112)*math.exp(-i/46)) for i in range(112)]
    hurt=[int(11000*(.6*math.sin(2*math.pi*72*i/2000)+.4*rng.uniform(-1,1))*math.exp(-i/27)) for i in range(144)]
    asm=['; Original generated BRR effects.','.include "hdr.asm"']
    for name,samples in [('heartbeat',heartbeat),('latch',latch),('seal',seal),('chime',chime),
                         ('bow',bow),('impact',impact),('attack',attack),('shove',shove),('hurt',hurt)]:
        (OUT/(name+'.brr')).write_bytes(encode_brr(samples))
        with wave.open(str(OUT/(name+'.wav')),'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate if name in ('latch','seal') else 2000)
            f.writeframes(struct.pack('<%dh'%len(samples),*samples))
        # C takes a 16-bit end address. Reserve a byte after the label so it
        # cannot land at $10000 when narrative growth repacks the ROM banks.
        asm+=['.section "sfx_%s" superfree'%name,name+'_sound:',
              '.incbin "assets/generated/%s.brr"'%name,name+'_sound_end:', '.db 0', '.ends']
    (ROOT/'Data/content/audio.asm').write_text('\n'.join(asm)+'\n')
    print('Generated nine original ambient and combat WAV/BRR effects')
if __name__=='__main__': main()
