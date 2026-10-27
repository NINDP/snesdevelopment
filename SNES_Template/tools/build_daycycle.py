"""Bank-contained daylight palette ramps; the torch's palette never changes."""
import json
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
    # Three complete BG3 rows, ready to copy without building a frame in C
    # during a live Mode 7 update. Keep CP1251 and the normal UI palette.
    story=json.loads((out.parent/'story.json').read_text())
    maps=bytearray()
    for phase in ('NIGHT','DAWN','DAY','DUSK'):
        rows=[256|(7<<10)|(1<<13)]*96
        for x in range(1,31):rows[x]=261|(7<<10)|(1<<13);rows[64+x]=262|(7<<10)|(1<<13)
        for index,tile in ((0,265),(31,266),(32,263),(63,264),(64,267),(95,268)):
            rows[index]=tile|(7<<10)|(1<<13)
        message=story['ui']['TIME_'+phase+'_EVENT'].encode('cp1251')
        assert len(message)<=28
        for x,ch in enumerate(message,34):rows[x]=ch|(7<<10)|(1<<13)
        maps.extend(struct.pack('<96H',*rows))
    (out/'daycycle-notices.map').write_bytes(maps)
    assembly+=['.section "daycycle_notices" superfree','daycycle_notices:',
               '.incbin "assets/generated/daycycle-notices.map"','.ends']
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
