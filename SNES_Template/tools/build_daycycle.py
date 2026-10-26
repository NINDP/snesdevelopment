"""Bank-contained daylight palette ramps; the torch's palette never changes."""
import struct


def ramp(payload, actors=False):
    original=struct.unpack('<%dH'%(len(payload)//2),payload)
    result=bytearray()
    for level in range(17):
        for index,color in enumerate(original):
            if not color or (not actors and index in (29,30,31)):
                result.extend(struct.pack('<H',color));continue
            rgb=((color&31),(color>>5)&31,(color>>10)&31)
            gains=(1.08,1.14,1.25) if actors else (1.70,1.85,2.10)
            lift=(0,0,0) if actors else (2,3,4)
            day=[min(31,round(c*gain+offset)) for c,gain,offset in zip(rgb,gains,lift)]
            values=[round((c*(16-level)+d*level)/16) for c,d in zip(rgb,day)]
            result.extend(struct.pack('<H',values[0]+values[1]*32+values[2]*1024))
    return result


def build(out,assembly):
    for room in range(2):
        name='daylight%d'%room
        (out/(name+'.pal')).write_bytes(ramp((out/('perspective%d.pal'%room)).read_bytes()))
        assembly+=['.section "'+name+'" superfree',name+'_palettes:',
                   '.incbin "assets/generated/'+name+'.pal"','.ends']
    (out/'daylight-actors.pal').write_bytes(ramp((out/'palette.pal').read_bytes()+
                                                   (out/'hero.pal').read_bytes(),True))
    assembly+=['.section "daylight_actors" superfree','daylight_actor_palettes:',
               '.incbin "assets/generated/daylight-actors.pal"',
               'perspective_sky_brightness:', '.db 127,15,97,15,0','.ends']
