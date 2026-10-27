"""Readable, prebuilt context and result panels for live exploration."""
import json
import struct
import textwrap

NOTICE_KEYS=('', 'OIL_OK','WRONG','FOREST_NEED','CHAPEL_NEED','CHARGE',
             'PUZZLE_WRONG','ECHO_WAIT','WARD_OK','WARD_EMPTY','WARD_NEED',
             'BELL_WRONG','FOREST_DONE','SIGN_ONE','SIGN_TWO','RUNE_DONE',
             'TABLE_DONE','APPROACH','TABLE_NEED','TOKEN_NEED','MIRO_NEED',
             'SIGN_ORDER','RUNE_WAIT','RUNES_NEED')

def panel(message):
    rows=[256|(7<<10)|(1<<13)]*128
    attr=(7<<10)|(1<<13)
    for x in range(1,31):
        rows[x]=261|attr;rows[96+x]=262|attr
    for index,tile in ((0,265),(31,266),(32,263),(63,264),(64,263),(95,264),(96,267),(127,268)):
        rows[index]=tile|attr
    lines=[]
    for line in message.split('\n'):
        lines+=textwrap.wrap(line,28,break_long_words=False,break_on_hyphens=False) or ['']
    assert len(lines)<=2,(message,lines)
    for y,line in enumerate(lines,1):
        encoded=line.encode('cp1251');assert len(encoded)<=28
        for x,ch in enumerate(encoded,2):rows[y*32+x]=ch|attr
    return struct.pack('<128H',*rows)

def build(out,assembly):
    story=json.loads((out.parent/'story.json').read_text())
    points=bytearray()
    for room,data in enumerate(story['rooms']):
        assert len(data['hotspots'])<=15
        values=bytes([len(data['hotspots'])]+[v for x,y,_ in data['hotspots'] for v in (x,y)])
        points.extend(values.ljust(32,b'\0'))
        maps=bytearray()
        for index in range(16):
            message=''
            if index<len(data['hotspots']):
                name=data['hotspots'][index][2]
                hint='НАЖМИ A ДЛЯ ОСМОТРА'
                if (room,index) in ((0,0),(0,1),(1,1),(2,0),(2,1),(3,0)):
                    hint='НАЖМИ A ДЛЯ РАЗГОВОРА'
                if (room,index) in ((0,2),(1,6),(2,2),(3,6)):
                    hint='СМОЛА И СТРЕЛЫ: НАЖМИ A'
                if (room,index) in ((0,5),(1,8),(3,8)):
                    hint='ОСВЕТИ СЛЕД ОКОЛО СЕКУНДЫ'
                if room==1 and index in (2,3,4):hint='ПОРЯДОК: ВОДА > РОД > СВЕТ'
                if room==3 and index in (2,3,4):hint='ОСВЕТИ УЗЕЛ, ЗАТЕМ НАЖМИ A'
                message='A: '+name+'\n'+hint
            maps.extend(panel(message))
        name='interaction%d'%room
        (out/(name+'.map')).write_bytes(maps)
        assembly+=['.section "'+name+'" superfree',name+'_maps:',
                   '.incbin "assets/generated/'+name+'.map"','.ends']
    (out/'interaction-points.bin').write_bytes(points)
    assembly+=['.section "interaction_points" superfree','interaction_points:',
               '.incbin "assets/generated/interaction-points.bin"','.ends']
    payload=b''.join(panel(story['ui'][key] if key else '') for key in NOTICE_KEYS)
    (out/'interaction-notices.map').write_bytes(payload)
    assembly+=['.section "interaction_notices" superfree','interaction_notice_maps:',
               '.incbin "assets/generated/interaction-notices.map"','.ends']
