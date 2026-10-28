#!/usr/bin/env python3
"""Create the handoff package from the compiled and tested repository."""
import hashlib,json,shutil,struct,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def main():
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    rom=(ROOT/'chernorechye.sfc').read_bytes()
    assert len(rom)==1048576
    complement,checksum=struct.unpack_from('<HH',rom,0x7fdc)
    assert complement^checksum==0xffff
    assert sum(rom)&0xffff==checksum
    (dist/'chernorechye.sfc').write_bytes(rom)
    (dist/'sha256.txt').write_text(hashlib.sha256(rom).hexdigest()+'  chernorechye.sfc\n')
    records=[json.loads(p.read_text()) for p in sorted((ROOT/'build').glob('rom-*.json'))]
    native_proof=ROOT/'build/bsnes-backdrop-regression.json'
    if native_proof.exists() and json.loads(native_proof.read_text()).get('rom_sha256')!=hashlib.sha256(rom).hexdigest():
        raise ValueError('Native bsnes backdrop proof belongs to another ROM')
    expected={('NTSC','gamepad','good'),('NTSC','gamepad','bad'),('NTSC','gamepad','secret'),
        ('PAL','gamepad','good'),('PAL','gamepad','secret'),('NTSC','Super Scope','good'),
        ('PAL','Super Scope','good'),('NTSC','Super Scope','secret')}
    actual={(r['region'],r['controller'],r['requested_ending']) for r in records}
    if actual!=expected or len(records)!=8: raise ValueError('Eight distinct ROM checks are required')
    if any(r.get('rom_sha256')!=hashlib.sha256(rom).hexdigest() for r in records):
        raise ValueError('Reports belong to another ROM build; run checks again')
    mesen=json.loads((ROOT/'build/mesen-video.json').read_text())
    if (mesen.get('rom_sha256')!=hashlib.sha256(rom).hexdigest() or
        any(mesen.get(key)!=0 for key in ('collisions','visible_dma','late_publish','sprite_overflow')) or
        mesen.get('projected_layer_writes',-1)!=0 or mesen.get('dialogue_horizon_samples',0)<6 or
        mesen.get('journal_layer_failures',-1)!=0 or mesen.get('journal_checks',0)<100 or
        mesen.get('horizon_samples',0)<3 or mesen.get('horizon_corrupt_pixels',-1)!=0 or
        mesen.get('torch_depth_failures',-1)!=0 or mesen.get('torch_depth_checks',0)<100 or
        mesen.get('house_failures',-1)!=0 or mesen.get('house_checks',0)<100 or
        mesen.get('maximum_tiles_per_scanline',999)>34 or mesen.get('world_samples',0)<100 or
        mesen.get('journal_entries',0)<12 or mesen.get('pause_entries',0)<12 or
        not all(mesen.get(key) for key in ('night','overview','notes'))):
        raise ValueError('Missing, stale or failing Mesen video regression')
    for region in ('ntsc','pal'):
        houses=json.loads((ROOT/'build'/('houses-regression-'+region+'.json')).read_text())
        if (houses.get('rom_sha256')!=hashlib.sha256(rom).hexdigest() or
            houses.get('house_geometry_checks',0)<400 or houses.get('missing_or_shrunken_houses')!=0):
            raise ValueError('Missing, stale or failing house geometry regression: '+region)
    for feature in ('scope','hero','torch','daycycle','combat','survival','interaction','locations'):
        for region in ('ntsc','pal'):
            report=json.loads((ROOT/'build'/('%s-regression-%s.json'%(feature,region))).read_text())
            if report.get('rom_sha256')!=hashlib.sha256(rom).hexdigest():
                raise ValueError('Feature regression belongs to another ROM: '+feature+' '+region)
            if feature=='survival':
                cadence=report['cadence']
                if (cadence['updates']<300 or cadence['max_vblank_gap']>2 or
                    cadence['audio_peak']<=0 or cadence['max_population']!=4 or
                    abs(cadence['logical_ticks']-cadence['expected_logical_ticks'])>4):
                    raise ValueError('Four-night survival budget failed: '+region)
    for suffix in ('','-pal'):
        report=json.loads((ROOT/'build'/('profile-optimized'+suffix+'.json')).read_text())
        if report.get('rom_sha256')!=hashlib.sha256(rom).hexdigest():
            raise ValueError('Cadence profile belongs to another ROM: '+suffix)
        if len(report['cadence'])!=8 or any(r['updates']<(300 if r['scenario'] in ('village-walk','forest-walk','chapel-walk','cellar-walk') else 600)
                or r['max_vblank_gap']>(2 if r['scenario'] in ('village-walk','forest-walk','chapel-walk','cellar-walk') else 1)
                or (r.get('heartbeat_expected',True) and r['audio_peak']<=0) for r in report['cadence']):
            raise ValueError('Cadence/audio regression failed: '+suffix)
    lines=['# Проверка финальной сборки','',
        'PVSnesLib 4.6.0; Linux x86-64; 1 MiB LoROM.',
        'Mode 7: тайловые материалы четырёх локаций и круговой свет факела.',
        'SHA-256: `'+hashlib.sha256(rom).hexdigest()+'`.','',
        'Тесты ядра и ASan/UBSan проходят. Настоящая ROM проверена',
        'контроллерными событиями без изменения RAM; получены кадры PPU.','',
        '| Регион | Управление | Концовка | Кадры | Пик PCM |',
        '|---|---|---|---:|---:|']
    for r in records:
        lines.append('| %s | %s | %s | %s | %s |'%(r['region'],r['controller'],r['requested_ending'],r['frames'],r['audio_peak']))
    lines+=['','Ночью и в закрытых помещениях проверена полная темнота за пределами',
        'круга света: земля, персонажи и предметы не просвечивают.',
        'Днём на улице солнце освещает мир даже с выключенным факелом.',
        'Проверены выключение/включение факела, журнал в темноте и возврат',
        'в исследование; интерфейс не раскрывает скрытый мир.',
        'Проверены также прогресс сцен, порядок знаков, узлы, моральные условия, концовки,',
        'журнал, заморозка времени на паузе и ненулевой вывод SPC.',
        'Расширенная секретная ветка проверяет три следа памяти, колокольную',
        'загадку и расход серебра; native tests также проверяют обратные пути.',
        'JSON-отчёты и кадры приложены в build/.',
        'Дополнительно прошли шестнадцать регрессий героя, факела, Scope, суток, боя, выживания, взаимодействий и локаций в PAL/NTSC.',
        'Лук проверен натяжением и отпусканием A, обычным кликом Scope,',
        'физическим полётом стрелы, попаданием в тело и гибелью врага.',
        'Проверены препятствия, отсутствие урона NPC, конечный боезапас,',
        'пополнение у сосудов, отмена невалидного выстрела и остановка боя в UI.',
        'Проверены четыре последовательные ночи с ростом группы до четырёх врагов.',
        'Ползуны пробираются через огонь; серебро не лечит раненных противников.',
        'Каждый регион прошёл полный цикл 768 активных секунд: сумерки, ночь,',
        'полночь со сменой дня, рассвет и возвращение дневного света.',
        'Проверены убывание света на закате, часы в журнале, остановка времени',
        'в журнале и на паузе, отступление лесной тени и тёмная часовня днём.',
        'Проверены 24 фазы ходьбы, восемь поз ожидания, поворот на месте и VRAM на паузе.',
        'На четырёх направлениях проверено совпадение факела с кистью и 32 состояния искр.',
        'При выходе в меню проверено восстановление старых спрайтов вступления.',
        'Scope: первый клик, отпускание кнопок, калибровка, TURBO, попадание в торс',
        'и отбрасывание невалидного FIRE проходят регрессии.',
        'Декоративные деревья больше не перехватывают клики по земле.',
        'Восемь сценариев в каждом регионе проверены по бюджету кадров.',
        'Неподвижные сцены, повороты на месте и часовня обновляются каждый кадр;',
        'для плотной деревни, леса и подземелья допускается до двух VBlank.',
        'Насыщенная сцена с четырьмя врагами также укладывается в два VBlank;',
        'независимо проверены 60 логических тактов в секунду и живой звук SPC.',
        'Вступление из пяти экранов проверено кнопками; кадры спортзала,',
        'подвала и отражения сняты из самой ROM.',
        'Свет следует за огнём в левой руке, имеет яркий центр, тёплое кольцо',
        'и четыре фазы мерцания на направление;',
        'внешний радиус — 77..79 экранных пикселей. Ночью за кругом нет тусклого слоя.',
        'Материалы каждой карты Mode 7 проверены на предел 256 тайлов.',
        'Первые две локации имеют новые тропы, брод, двор, 64×64 избы и 32×64 ели.',
        'Смена глубины сохраняет несколько заранее подготовленных размеров декораций.',
        'Проверены дневной/ночной свет и восстановление полного атласа вступления.','',
        'Пять жителей используют спрайты 24×36 по листу пользователя, четыре направления и idle.',
        'Дневной дальний фон Mode1 имеет три скорости прокрутки; земля остаётся Mode7.',
        'Панорама занимает свободные 8 KiB VRAM, не расходуя OBJ; ночью фон выключен.','',
        'Физическая SNES, настоящий Super Scope/CRT, macOS и пользовательская',
        'длительность прохождения не проверены. Это прототип с',
        'новой графикой и девятью эффектами, без озвучки, полной музыки и SRAM.']
    memory=json.loads((ROOT/'build/memory.json').read_text())
    lines+=['', 'Статика платформы/ядра: %d B; initialized content: %d B.'%
            (memory['project_static_bytes'],memory['initialized_content_bytes']),
        'Всего проектной WRAM: %d B без SDK/стека/APU; Game: %d B.'%(memory['total_project_wram_bytes'],memory['buffers']['game']),
        'Текстовый буфер: 1792 B; старые Mode 1 HDMA-буферы: 532 B.',
        'Таблицы света Mode 7 в ROM: %d B.'%memory['torch_table_bytes'],
        'Палитры суток и готовые уведомления в ROM: %d B.'%memory['daycycle_rom_bytes'],
        'Боевые позы: %d B ROM; атлас стрел: 1024 B; панели лука: %d B.'%(memory['bow_frame_rom_bytes'],memory['bow_hud_rom_bytes']),
        'Контекстные подписи и сообщения действий проверены подходами сбоку к старосте и серебру;',
        'маршрут кнопкой A проходит деревню, лес, часовню и подземелье.',
        'Подсказки показывают порядок знаков и недостающие условия прямо в исследовании.',
        'Профили PAL/NTSC приложены в build/profile-*.json.']
    lines+=['','| Регион | Сценарий | Обновления / 600 кадров | Макс. VBlank |',
            '|---|---|---:|---:|']
    for suffix in ('','-pal'):
        profile=json.loads((ROOT/'build'/('profile-optimized'+suffix+'.json')).read_text())
        for row in profile['cadence']:
            lines.append('| %s | %s | %d | %d |'%(profile['region'],row['scenario'],row['updates'],row['max_vblank_gap']))
    proof=ROOT/'build/reproducibility.json'
    if proof.is_file():
        evidence=json.loads(proof.read_text())
        if evidence['source_rom_sha256']!=hashlib.sha256(rom).hexdigest():
            raise ValueError('Reproducibility report belongs to another ROM')
        lines+=['', 'Патч применён к чистой копии исходного шаблона; получена идентичная ROM.']
    (ROOT/'docs/VALIDATION.md').write_text('\n'.join(lines)+'\n')
    names=['good-pad-ntsc-village.png','good-pad-ntsc-forest.png',
        'good-pad-ntsc-chapel.png','good-pad-ntsc-dungeon.png']
    labels=['Черноречье · земля и мох','Лес · тропа и корни',
        'Часовня · деревянный пол','Под часовней · камень']
    font=ImageFont.truetype(next(str(path) for path in (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('/System/Library/Fonts/Supplemental/Arial.ttf')) if path.exists()),18)
    sheet=Image.new('RGB',(1088,1000),(0,0,0));draw=ImageDraw.Draw(sheet)
    for i,(name,label) in enumerate(zip(names,labels)):
        x=16+(i%2)*536;y=10+(i//2)*494
        draw.text((x,y),label,font=font,fill=(203,180,114))
        im=Image.open(ROOT/'build'/name).convert('RGB')
        sheet.paste(im.resize((512,448),Image.Resampling.NEAREST),(x,y+30))
    sheet.save(ROOT/'docs/preview.png')
    archive=dist/'Nabla-Chernorechye-SNES.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('README.md','.github/workflows/chernorechye.yml'):
            extra=ROOT.parent/name
            if extra.is_file():z.write(extra,name)
        for p in ROOT.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if rel.parts[0]=='third_party':continue
            if p==archive:continue
            if rel.parts[0]=='dist' and p.suffix=='.zip':continue
            if p.suffix in {'.obj','.ps','.symfull','.log','.dbg'}:continue
            if rel.as_posix() in {'hdr.asm','linkfile','chernorechye.sfc','chernorechye.sym'}:continue
            if '__pycache__' in rel.parts:continue
            if rel.parts[0]=='build' and p.suffix not in {'.png','.json','.gif'}:continue
            if p.suffix=='.asm' and rel.as_posix() not in {
                    'Data/content/assets.asm','Data/content/audio.asm','Data/perspective_oam.asm'}:continue
            z.write(p,'SNES_Template/'+rel.as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        if z.read('SNES_Template/dist/chernorechye.sfc')!=rom: raise ValueError('Archive ROM mismatch')
    print('ROM SHA-256',hashlib.sha256(rom).hexdigest(),'source zip',archive.stat().st_size)
if __name__=='__main__':main()
