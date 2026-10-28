"""Opaque, larger Kirill poses in a bank-safe six-cell OBJ strip."""
from PIL import Image
from build_hero import frame_strip


def build(out,assembly,source,palette):
    fixed=Image.new('P',(1,1));fixed.putpalette(palette)
    names=['SceneTwoPlayerIdle.png']+['SceneTwoMainCharacterRunRight%d.png'%n for n in range(1,8)]
    for n,name in enumerate(names):
        rgba=Image.open(source/name).convert('RGBA').resize((24,48),Image.Resampling.NEAREST)
        indexed=rgba.convert('RGB').quantize(palette=fixed,dither=Image.Dither.NONE)
        # Opaque black clothing must never become transparent palette index0.
        indexed=indexed.point(lambda value:(value & 15) or 1)
        frame=Image.new('P',(32,48),0);frame.putpalette(palette)
        frame.paste(indexed,(4,0),rgba.getchannel('A').point(lambda a:255 if a>=128 else 0))
        filename='intro-actor-%d.chr'%n
        (out/filename).write_bytes(frame_strip(frame))
        frame.convert('RGB').save(out/('intro-actor-%d.png'%n))
        assembly+=['.section "intro_actor%d" superfree'%n,'intro_actor%d:'%n,
                   '.incbin "assets/generated/'+filename+'"','.ends','']
