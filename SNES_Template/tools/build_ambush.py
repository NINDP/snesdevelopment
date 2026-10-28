"""Native moonlit Mode 7 encounter, streamed eight-scale fox animations."""
import math
import random
import struct
from PIL import Image, ImageDraw
from build_hero import PALETTE as HERO_PALETTE, bow_actor, actor

BG_COLORS=[(100,129,145),(42,62,92),(95,123,143),(239,232,194),
 (73,112,98),(46,80,71),(110,144,113),(35,66,65),
 (157,181,177),(80,112,121),(26,44,55),(135,150,150),
 (94,119,121),(166,187,179),(229,171,77),(48,70,86)]
FOX_COLORS=[(0,0,0),(30,39,47),(53,46,43),(83,52,39),
 (126,61,32),(166,75,32),(204,96,36),(228,124,48),
 (242,156,73),(151,121,91),(194,173,136),(156,164,153),
 (217,211,178),(237,230,194),(251,244,215),(232,192,89)]
FX_COLORS=[(0,0,0),(30,48,63),(245,238,207),(152,193,207),
 (163,113,51),(231,169,67),(86,130,105),(177,206,178),
 (165,61,43),(224,111,56),(206,180,130),(107,147,160),
 (184,203,183),(255,228,129),(238,244,224),(79,109,116)]
WIDTHS=(16,20,24,28,36,44,52,60)

def canvas(size,colors):
    im=Image.new('P',size,0)
    im.putpalette([v for c in colors for v in c]+[0]*(768-len(colors)*3))
    return im

def background():
    im=canvas((256,224),BG_COLORS);d=ImageDraw.Draw(im)
    d.rectangle((0,0,255,223),fill=1)
    d.rectangle((0,48,255,87),fill=15)
    # Fine native pixels, a smaller cratered moon, and cloud wisps.
    d.ellipse((153,8,201,56),fill=2)
    d.ellipse((158,13,196,51),fill=13)
    d.ellipse((161,16,193,48),fill=3)
    d.ellipse((166,22,173,27),fill=13)
    d.ellipse((181,32,187,37),fill=12)
    d.point((175,40),fill=8)
    for x,y in ((13,26),(43,14),(77,32),(102,20),(126,38),(216,18),(243,33)):
        d.point((x,y),fill=8)
    d.line((114,37,139,36,146,38),fill=2)
    d.line((195,44,220,42,243,44),fill=2)
    # Three rows of broken crowns; tree clusters are deliberately quiet.
    for x in range(-7,268,17):
        y=57+(x*7%9)
        d.polygon([(x,y-16),(x-7,y-1),(x-4,y-2),(x-11,y+13),
                   (x+11,y+13),(x+4,y-2),(x+7,y-1)],fill=9)
    for x,y in ((2,58),(25,57),(53,63),(76,65),(208,60),(233,56),(257,61)):
        d.polygon([(x,y-18),(x-6,y-5),(x-3,y-6),(x-11,y+7),(x-6,y+5),
                   (x-15,y+21),(x+15,y+21),(x+6,y+5),(x+11,y+7),
                   (x+3,y-6),(x+6,y-5)],fill=7)
        d.line((x,y-9,x,y+22),fill=15)
    # Log chapel, recessed door, roof ribs, cupola and Orthodox cross.
    d.rectangle((108,66,147,85),fill=9)
    for y in (69,73,77,81):d.line((109,y,146,y),fill=15)
    d.polygon([(99,67),(127,47),(156,67),(151,70),(127,53),(104,70)],fill=10)
    d.polygon([(104,66),(127,50),(150,66),(128,58)],fill=9)
    for x in range(107,151,7):d.line((x,66,127,51),fill=15)
    d.rectangle((123,72,132,85),fill=10)
    d.rectangle((125,74,130,84),fill=14)
    d.line((128,74,128,84),fill=12)
    d.rectangle((118,47,135,53),fill=15)
    d.polygon([(119,47),(127,37),(135,47)],fill=9)
    d.line((127,28,127,41),fill=8)
    d.line((122,32,132,32),fill=8)
    d.line((124,38,131,36),fill=8)
    d.line((98,85,157,85),fill=8)
    # Birch branches frame the view without covering the central target area.
    for x,w,top in ((5,10,15),(31,5,35),(60,3,52),(241,11,10),(217,5,36)):
        d.polygon([(x,top),(x+w,top),(x+w+2,87),(x-1,87)],fill=8)
        d.line((x+w-1,top,x+w+1,86),fill=9,width=2)
        for y in range(top+8,86,11):
            d.line((x+1,y,x+w//2,y+1),fill=15)
            d.point((x+w-2,y+5),fill=7)
        side=1 if x<128 else -1
        d.line((x+w//2,top+24,x+side*20,top+10),fill=8,width=2)
    for x,y in ((0,17),(21,25),(47,39),(245,17),(221,27),(199,43)):
        d.polygon([(x-22,y+5),(x-16,y),(x-8,y+2),(x-2,y-3),(x+9,y),
                   (x+16,y-1),(x+23,y+6),(x+15,y+12),(x+5,y+10),
                   (x-3,y+14),(x-12,y+10),(x-24,y+11)],fill=7)
        d.line((x-13,y+4,x-2,y+2,x+11,y+5),fill=9)
    d.rectangle((0,86,255,87),fill=2)
    return im

def fox(frame):
    """Lean red fox: articulated legs, long muzzle and a separate full tail."""
    im=canvas((64,48),FOX_COLORS);d=ImageDraw.Draw(im)
    d.ellipse((10,40,54,46),fill=11)
    for x in range(10,55,3):d.point((x,45),fill=0)
    if frame>=6:
        stride=(-2,2)[frame&1]
        # Retreat is authored from behind, rather than walking backwards.
        d.polygon([(30,15),(39,12),(45,18),(46,31),(38,39),(23,35),(20,26)],fill=5,outline=1)
        d.polygon([(32,15),(40,14),(44,20),(36,23),(27,19)],fill=7)
        for x,step in ((27,stride),(40,-stride)):
            d.line((x,29,x+step,42),fill=2,width=4)
            d.line((x,29,x+step,36),fill=5,width=3)
            d.line((x+step-1,43,x+step+3,43),fill=1,width=2)
        d.polygon([(24,23),(18,23),(12,30),(5,32),(2,38),(8,42),
                   (16,37),(28,33),(32,28)],fill=6,outline=1)
        d.polygon([(2,38),(5,32),(11,32),(12,38),(8,42)],fill=13)
        d.line((12,33,21,27,26,27),fill=8,width=2)
        d.polygon([(35,16),(36,5),(41,10),(48,7),(49,19),(43,23)],fill=6,outline=1)
        d.polygon([(38,8),(38,14),(41,12)],fill=3)
        d.polygon([(46,10),(47,16),(44,14)],fill=3)
        d.line((39,19,44,21),fill=10)
        return im
    crouch=frame==4;leap=frame==5
    bob=(0,-1,1,0,3,-4)[frame]
    stride=(-4,0,4,0,0,-6)[frame]
    # The long brush sweeps behind the rump. Its cream tip is moonlit.
    tail_y=(0,-2,1,2,3,-3)[frame]
    d.polygon([(33,22+bob),(43,18+tail_y),(50,10+tail_y),(59,9+tail_y),
               (63,14+tail_y),(59,22+tail_y),(49,28+tail_y),(37,31+bob)],fill=5,outline=1)
    d.polygon([(51,11+tail_y),(59,9+tail_y),(63,14+tail_y),(59,21+tail_y),
               (53,22+tail_y),(56,16+tail_y)],fill=13)
    d.line((38,24+bob,46,21+tail_y,53,14+tail_y),fill=8,width=2)
    # Rear legs bend at the hock, with black stockings and weight-bearing paws.
    for x,step in ((34,-stride),(43,stride//2)):
        knee=(x+3,32+bob)
        foot=(x+step,42 if crouch else 44-(2 if step>0 else 0))
        d.line((x,23+bob,*knee,*foot),fill=1,width=5)
        d.line((x,23+bob,*knee),fill=4,width=3)
        d.line((*knee,*foot),fill=2,width=3)
        d.line((foot[0]-2,foot[1],foot[0]+3,foot[1]),fill=1,width=2)
    d.polygon([(16,18+bob),(26,13+bob),(38,17+bob),(45,27+bob),
               (39,34+bob),(25,35+bob),(16,29+bob)],fill=6,outline=1)
    d.polygon([(21,18+bob),(29,15+bob),(38,19+bob),(40,24+bob),
               (29,23+bob),(20,25+bob)],fill=8)
    d.line((21,18+bob,29,16+bob,37,20+bob),fill=10)
    d.polygon([(18,25+bob),(25,28+bob),(34,29+bob),(36,34+bob),
               (24,35+bob),(17,30+bob)],fill=4)
    # Two forelegs alternate reach and support through all four gait frames.
    for x,step in ((18,stride),(26,-stride)):
        top=(x,25+bob)
        knee=(x-2,33+bob)
        foot=(x-3+step,43-(2 if step<0 else 0))
        if leap:foot=(x-9,37+(x&3))
        if crouch:foot=(x-6,43)
        d.line((*top,*knee,*foot),fill=1,width=5)
        d.line((*top,*knee),fill=7,width=3)
        d.line((*knee,*foot),fill=2,width=3)
        d.line((foot[0]-2,foot[1],foot[0]+3,foot[1]),fill=1,width=2)
    # Narrow forehead, two upright ears, long dark nose and modest pale cheeks.
    hy=bob+(1 if crouch else 0)
    d.polygon([(11,18+hy),(9,6+hy),(16,11+hy),(23,7+hy),(27,17+hy),
               (24,25+hy),(12,30+hy),(5,28+hy),(6,24+hy)],fill=6,outline=1)
    d.polygon([(11,9+hy),(12,18+hy),(16,14+hy)],fill=3)
    d.polygon([(22,10+hy),(23,17+hy),(25,18+hy)],fill=3)
    d.line((14,16+hy,20,13+hy,23,18+hy),fill=8,width=2)
    d.polygon([(8,22+hy),(15,22+hy),(21,20+hy),(21,26+hy),
               (12,31+hy),(5,28+hy),(5,25+hy)],fill=12)
    d.line((8,28+hy,13,29+hy,19,26+hy),fill=13)
    d.polygon([(4,25+hy),(8,23+hy),(11,26+hy),(8,29+hy),(4,28+hy)],fill=1)
    d.line((13,19+hy,17,18+hy),fill=1,width=2)
    d.point((15,18+hy),fill=15)
    d.point((22,18+hy),fill=1)
    d.line((14,26+hy,18,25+hy),fill=3)
    # Broken fur edges, not a large white cartoon mask.
    for x,y in ((18,23),(27,19),(34,22),(39,26),(22,29)):
        d.line((x,y+bob,x+2,y-1+bob),fill=7)
    return im

def palette(colors):
    return struct.pack('<16H',*(r//8+(g//8)*32+(b//8)*1024 for r,g,b in colors))

def mode7_ground(out,sky_map):
    rng=random.Random(119377);tiles=[];ids={};families={}
    # Coherent 16x16 material patches replace the old white-noise grass.
    for kind,variants in (('grass',6),('moss',3),('path',4),('water',2),('edge',3),('stone',2)):
        patterns=[]
        for phase in range(variants):
            im=Image.new('L',(16,16),4 if kind in ('grass','moss','edge') else (11 if kind=='path' else 12))
            d=ImageDraw.Draw(im)
            if kind=='grass':
                for _ in range(5):
                    x,y=rng.randrange(16),rng.randrange(16)
                    d.line((x,y,x+2,y-1),fill=5)
                for x,y in ((3+phase,4),(11,12-phase)):
                    d.line((x,y,x-1,y-3),fill=6)
                    d.point((x+1,y-2),fill=5)
            elif kind=='moss':
                d.ellipse((2,4,12,12),fill=5)
                d.line((4,6,10,5),fill=4)
                d.point((8,10),fill=6)
            elif kind=='path':
                d.line((3+phase,0,4+phase,15),fill=12,width=2)
                d.line((11+phase,0,12+phase,15),fill=12)
                for _ in range(5):
                    x,y=rng.randrange(16),rng.randrange(16)
                    d.line((x,y,x+1,y),fill=9 if _&1 else 13)
            elif kind=='water':
                d.rectangle((0,0,15,15),fill=9)
                d.line((1,3+phase,11,3+phase),fill=2)
                d.line((5,9,15,9),fill=8)
                d.line((2,13,8,13),fill=13)
            elif kind=='edge':
                d.polygon([(0,0),(10,0),(8,7),(12,15),(0,15)],fill=12)
                for y in (2,8,13):d.line((8,y,12,y-2),fill=6)
            else:
                d.polygon([(4,3),(10,2),(14,7),(11,13),(3,12),(1,7)],fill=9)
                d.line((4,4,9,3,12,6),fill=13)
                d.line((3,11,10,12),fill=5)
            quad=[]
            for y in (0,8):
                for x in (0,8):
                    tile=im.crop((x,y,x+8,y+8)).tobytes()
                    if tile not in ids:ids[tile]=len(tiles);tiles.append(tile)
                    quad.append(ids[tile])
            patterns.append(quad)
        families[kind]=patterns
    assert len(tiles)<128,'Reserve high Mode 7 characters for the far BG2 map'
    tilemap=bytearray(16384)
    for y in range(128):
        centre=64+round(math.sin((y-54)/14)*2)
        for x in range(128):
            delta=abs(x-centre);kind='grass'
            if (x//4+y//3)%9==0:kind='moss'
            if delta<=5:kind='path'
            elif delta==6:kind='edge'
            if 58<=y<=61 and centre+1<=x<=centre+4:kind='water'
            if delta in (8,10) and y%13 in (2,3):kind='stone'
            variants=families[kind];pattern=variants[(x//2*3+y//2*5)%len(variants)]
            tilemap[y*128+x]=pattern[(y&1)*2+(x&1)]
    payload=bytearray(32768)
    payload[0::2]=tilemap;payload[1::2]=b''.join(tiles).ljust(16384,b'\0')
    # Rows112..119 and characters224..255 are outside the camera/material set.
    # Use this unused corner for BG2's Mode 1 map, freeing 8 KiB for its graphics.
    payload[0x7000:0x7800]=sky_map
    (out/'ambush-ground.vram').write_bytes(payload)
    (out/'ambush-ground.pal').write_bytes(palette(BG_COLORS))
    return len(tiles)

def fox_strip(im):
    strip=canvas((128,32),FOX_COLORS)
    for part,(x,y) in enumerate(((0,0),(32,0),(0,32),(32,32))):
        strip.paste(im.crop((x,y,x+32,y+32)),(part*32,0))
    from build_assets import tile_image
    return tile_image(strip,False)[0]

def build(out,assembly):
    from build_assets import tile_image
    scene=background();tiles,tilemap=tile_image(scene,max_tiles=256)
    tilemap=struct.pack('<1024H',*(tile|(4<<10) for tile in struct.unpack('<1024H',tilemap)))
    for suffix,data in (('chr',tiles),('map',tilemap),('pal',palette(BG_COLORS))):
        (out/('ambush-sky.'+suffix)).write_bytes(data)
    materials=mode7_ground(out,tilemap)
    scene.crop((0,0,256,88)).convert('RGB').save(out/'ambush-background.png')
    atlas=canvas((128,128),HERO_PALETTE)
    for frame in range(4):atlas.paste(bow_actor('back',frame),(frame*32,0))
    for frame in range(2):
        hero=bow_actor('back',0);hero.paste(actor('back',2+frame*3).crop((0,32,32,48)),(0,32))
        atlas.paste(hero,(frame*32,48))
    # Foreground objects have roots, broken branches and rim-lit bark.
    tree=canvas((32,48),FX_COLORS);d=ImageDraw.Draw(tree)
    d.polygon([(12,0),(19,0),(20,34),(25,46),(17,44),(9,47),(11,32)],fill=12)
    d.polygon([(17,0),(19,0),(20,34),(23,43),(18,39)],fill=11)
    d.line((13,0,12,34,10,42),fill=7)
    for y in (5,15,27,36):
        d.line((12,y,16,y+1),fill=1)
        d.line((16,y+6,19,y+4),fill=15)
    d.line((13,17,5,10,2,9),fill=12,width=3)
    d.line((18,25,26,17,30,16),fill=11,width=3)
    d.line((9,44,3,46),fill=6,width=2)
    d.line((21,44,29,46),fill=6,width=2)
    atlas.paste(tree,(64,48))
    stone=canvas((32,32),FX_COLORS);d=ImageDraw.Draw(stone)
    d.ellipse((2,24,30,30),fill=1)
    d.polygon([(6,10),(17,6),(27,14),(29,23),(22,27),(4,25),(2,17)],fill=15)
    d.polygon([(6,10),(17,6),(27,14),(17,13),(8,17),(2,17)],fill=11)
    d.line((7,11,17,8,24,13),fill=12)
    for x,y in ((7,20),(11,23),(20,16),(22,24)):d.line((x,y,x+3,y-2),fill=6)
    atlas.paste(stone,(96,48))
    shrub=canvas((32,16),FX_COLORS);d=ImageDraw.Draw(shrub)
    for x,y in ((3,14),(8,13),(15,15),(22,13),(28,15)):
        d.line((x,y,x-2,y-8),fill=6)
        d.line((x,y-2,x+3,y-9),fill=7)
        d.line((x-2,y-8,x-4,y-10),fill=12)
    atlas.paste(shrub,(96,80))
    for angle in range(8):
        arrow=canvas((16,16),FX_COLORS);d=ImageDraw.Draw(arrow)
        dx=math.sin(angle*math.pi/4);dy=-math.cos(angle*math.pi/4)
        tip=(round(8+dx*6),round(8+dy*6));tail=(round(8-dx*5),round(8-dy*5))
        d.line((*tail,*tip),fill=1,width=3);d.line((*tail,*tip),fill=2)
        d.polygon([tip,(round(tip[0]-dx*4+dy*2),round(tip[1]-dy*4-dx*2)),
                   (round(tip[0]-dx*4-dy*2),round(tip[1]-dy*4+dx*2))],fill=3)
        atlas.paste(arrow,(angle*16,96))
    fx=canvas((128,16),FX_COLORS);d=ImageDraw.Draw(fx)
    d.ellipse((3,3,12,12),outline=1);d.ellipse((4,4,11,11),outline=2)
    for line in ((8,0,8,4),(8,11,8,15),(0,8,4,8),(11,8,15,8)):d.line(line,fill=2)
    d.point((8,8),fill=5)
    for line in ((24,1,24,14),(17,8,30,8),(19,3,28,12),(19,12,28,3)):d.line(line,fill=5)
    d.ellipse((22,6,26,10),fill=13)
    d.polygon([(34,5),(37,2),(40,5),(43,2),(46,5),(45,9),(40,14),(35,9)],fill=8,outline=1)
    d.line((36,5,37,4,39,6),fill=13)
    d.polygon([(49,8),(58,3),(62,5),(58,10),(51,11)],fill=6);d.line((50,10,60,5),fill=7)
    d.ellipse((65,4,79,12),outline=8);d.ellipse((68,6,76,10),outline=13)
    d.line((72,1,72,4),fill=8);d.line((72,12,72,15),fill=8)
    d.ellipse((82,6,94,11),fill=15)
    d.line((100,4,108,12),fill=8,width=2);d.line((108,4,100,12),fill=8,width=2)
    d.ellipse((115,4,124,12),outline=13)
    atlas.paste(fx,(0,112))
    payload,_=tile_image(atlas,False);assert len(payload)==8192
    (out/'ambush-obj.chr').write_bytes(payload)
    sheet=canvas((64*8,48),FOX_COLORS)
    for pose in range(8):sheet.paste(fox(pose),(pose*64,0))
    sheet.save(out/'ambush-foxes.png',transparency=0)
    assembly += ['.section "ambush_ground" superfree','ambush_ground_vram:',
      '.incbin "assets/generated/ambush-ground.vram"','.ends','',
      '.section "ambush_background" superfree','ambush_sky_tiles:',
      '.incbin "assets/generated/ambush-sky.chr"','ambush_sky_tiles_end:',
      'ambush_sky_map:','.incbin "assets/generated/ambush-sky.map"',
      'ambush_sky_palette:','.incbin "assets/generated/ambush-sky.pal"',
      'ambush_ground_palette:','.incbin "assets/generated/ambush-ground.pal"',
      'ambush_modes_active:','.db 88,9,120,7,1,9,0',
      'ambush_layers_active:','.db 88,$16,120,$11,1,4,0',
      'ambush_modes_overlay:','.db 48,9,1,9,0',
      'ambush_layers_overlay:','.db 48,$16,1,4,0','.ends','',
      '.section "ambush_objects" superfree','ambush_obj_tiles:',
      '.incbin "assets/generated/ambush-obj.chr"','ambush_obj_tiles_end:','.db 0','.ends','']
    for lod,width in enumerate(WIDTHS):
        assembly+=['.section "ambush_fox_lod%d" superfree'%lod]
        for pose in range(8):
            scaled=fox(pose).resize((width,width*3//4),Image.Resampling.NEAREST)
            cell=canvas((64,64),FOX_COLORS)
            cell.paste(scaled,((64-width)//2,48-scaled.height))
            name='ambush-fox-%02d.chr'%(lod*8+pose)
            (out/name).write_bytes(fox_strip(cell))
            assembly+=['ambush_fox_frame%d:'%(lod*8+pose),'.incbin "assets/generated/'+name+'"']
        assembly+=['.ends','']
    for name,colors in (('hero',HERO_PALETTE),('fox',FOX_COLORS),('fx',FX_COLORS)):
        (out/('ambush-'+name+'.pal')).write_bytes(palette(colors))
    assembly+=['.section "ambush_palettes" superfree','ambush_hero_palette:',
      '.incbin "assets/generated/ambush-hero.pal"','ambush_fox_palette:',
      '.incbin "assets/generated/ambush-fox.pal"','ambush_fx_palette:',
      '.incbin "assets/generated/ambush-fx.pal"','.ends','']
    print('Moon clearing:',materials,'Mode 7 materials,',len(tiles)//32,'native panorama tiles; 64 streamed fox poses')
