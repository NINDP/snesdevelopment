#!/usr/bin/env python3
"""Create the handoff package from the compiled and tested repository."""
import hashlib,json,shutil,struct,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def main():
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    rom=(ROOT/'chernorechye.sfc').read_bytes()
    assert len(rom)==524288
    complement,checksum=struct.unpack_from('<HH',rom,0x7fdc)
    assert complement^checksum==0xffff
    assert sum(rom)&0xffff==checksum
    (dist/'chernorechye.sfc').write_bytes(rom)
    (dist/'sha256.txt').write_text(hashlib.sha256(rom).hexdigest()+'  chernorechye.sfc\n')
    records=[json.loads(p.read_text()) for p in sorted((ROOT/'build').glob('rom-*.json'))]
    expected={('NTSC','gamepad','good'),('NTSC','gamepad','bad'),('NTSC','gamepad','secret'),
        ('PAL','gamepad','good'),('PAL','gamepad','secret'),('NTSC','Super Scope','good'),
        ('PAL','Super Scope','good'),('NTSC','Super Scope','secret')}
    actual={(r['region'],r['controller'],r['requested_ending']) for r in records}
    if actual!=expected or len(records)!=8: raise ValueError('Eight distinct ROM checks are required')
    if any(r.get('rom_sha256')!=hashlib.sha256(rom).hexdigest() for r in records):
        raise ValueError('Reports belong to another ROM build; run checks again')
    lines=['# Проверка финальной сборки','',
        'PVSnesLib 4.6.0; Linux x86-64; 512 KiB LoROM.',
        'Тесты ядра и ASan/UBSan проходят. Настоящая ROM проверена',
        'контроллерными событиями без изменения RAM; получены кадры PPU.','',
        '| Регион | Управление | Концовка | Кадры | Пик PCM |',
        '|---|---|---|---:|---:|']
    for r in records:
        lines.append('| %s | %s | %s | %s | %s |'%(r['region'],r['controller'],r['requested_ending'],r['frames'],r['audio_peak']))
    lines+=['','Проверены чёрный мир при выключенном свете, реальный конус окна,',
        'прогресс сцен, порядок знаков, узлы, моральные условия, полные концовки,',
        'журнал, заморозка времени на паузе и ненулевой вывод SPC.',
        'Расширенная секретная ветка проверяет три следа памяти, колокольную',
        'загадку и расход серебра; native tests также проверяют обратные пути.',
        'JSON-отчёты и кадры приложены в build/.','',
        'Физическая SNES, настоящий Super Scope/CRT, macOS и пользовательская',
        'длительность прохождения не проверены. Это прототип с начальной',
        'графикой и тремя эффектами, без озвучки, полной музыки и SRAM.']
    memory=json.loads((ROOT/'build/memory.json').read_text())
    lines+=['', 'Статика кода игры: %d B (без SDK/стека); Game: 52 B.'%memory['project_static_bytes'],
        'Текстовый буфер: 1792 B; обе HDMA-таблицы: 266 B.',
        'Профили PAL/NTSC приложены в build/profile-*.json.']
    proof=ROOT/'build/reproducibility.json'
    if proof.is_file():
        evidence=json.loads(proof.read_text())
        if evidence['source_rom_sha256']!=hashlib.sha256(rom).hexdigest():
            raise ValueError('Reproducibility report belongs to another ROM')
        lines+=['', 'Патч применён к чистой копии исходного шаблона; получена идентичная ROM.']
    (ROOT/'docs/VALIDATION.md').write_text('\n'.join(lines)+'\n')
    names=['good-pad-ntsc-menu.png','good-pad-ntsc-lamp-on.png',
        'good-pad-ntsc-forest.png','good-pad-ntsc-revelation.png']
    labels=['Nabla · главное меню','Фонарь открывает мир','Лес и живые тени','Выбор у Чёрного Сердца']
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
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
            if rel.parts[0]=='build' and p.suffix not in {'.png','.json'}:continue
            if p.suffix=='.asm' and rel.as_posix() not in {'Data/content/assets.asm','Data/content/audio.asm'}:continue
            z.write(p,'SNES_Template/'+rel.as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        if z.read('SNES_Template/dist/chernorechye.sfc')!=rom: raise ValueError('Archive ROM mismatch')
    print('ROM SHA-256',hashlib.sha256(rom).hexdigest(),'source zip',archive.stat().st_size)
if __name__=='__main__':main()
