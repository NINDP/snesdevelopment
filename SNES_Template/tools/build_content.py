#!/usr/bin/env python3
"""Validate UTF-8 narrative and generate the CP1251 text used by the SNES."""
import json
import textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORDER='PROLOG HEAD EGOR KIND LOCK BIRCH MIRO CONFESS DENY FOREST PRIEST TIKHON TOKEN CHAPEL REVEAL FREE BIND RITUAL FINAL GOOD BAD SECRET MODERN GATE GRAVE WITNESS MARK NO_LIGHT RETRY ECHO_HOME ECHO_BOAT ECHO_STONE BELL_HINT BELL_DONE EGOR_RETURN EGOR_CAGED REMEMBER MIRO_RETRY MIRO_RELEASE RITUAL_READY FINAL_WARNING REPAIR END_STAY END_LOST FINAL_READY HEAD_RETURN'.split()
def literal(s):
    return '"'+''.join('\\%03o'%b if b>=128 else '\\n' if b==10 else '\\"' if b==34 else '\\\\' if b==92 else chr(b) for b in s.encode('cp1251'))+'"'
def wrap(s):
    lines=[]
    for paragraph in s.split('\n'):
        lines.extend(textwrap.wrap(paragraph,30,break_long_words=False,break_on_hyphens=False) or [''])
    if any(len(x)>30 for x in lines) or len(lines)>5:
        raise ValueError('Page exceeds 5 x 30: '+s)
    return '\n'.join(lines)
def main():
    (ROOT/'Data/content').mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'assets/story.json').read_text())
    expected=['D_'+x for x in ORDER]
    if set(data['dialogues'])!=set(expected): raise ValueError('Dialogue enum mismatch')
    out=['/* Generated: edit assets/story.json instead. */','#include "../include/game.h"']
    for key in expected:
        if not 1<=len(data['dialogues'][key])<=255: raise ValueError('Scene page count: '+key)
        out.append('static const StoryLine lines_%s[] = {'%key)
        for page in data['dialogues'][key]:
            if '\n' in page['speaker'] or len(page['speaker'])>30: raise ValueError('Speaker label too wide')
            wrapped=wrap(page['text'])
            out.append('    {%s, %s, %d},'%(literal(page['speaker']),literal(wrapped),len(wrapped.encode('cp1251'))))
        out.append('};')
    out.append('static const StoryLine *const scenes[D_COUNT] = {'+','.join('lines_'+x for x in expected)+'};')
    out.append('static const SkU8 counts[D_COUNT] = {'+','.join(str(len(data['dialogues'][x])) for x in expected)+'};')
    for i,room in enumerate(data['rooms']):
        out.append('static const Hotspot hotspots_%d[] = {'%i)
        for x,y,name in room['hotspots']:
            assert 12<=x<=244 and 24<=y<192
            out.append('    {%d,%d,%s},'%(x,y,literal(name)))
        out.append('};')
    out.append('static const Hotspot *const rooms[4] = {hotspots_0,hotspots_1,hotspots_2,hotspots_3};')
    out.append('static const SkU8 hotspot_counts[4] = {'+','.join(str(len(x['hotspots'])) for x in data['rooms'])+'};')
    out.append('static const char *const names[4] = {'+','.join(literal(x['name']) for x in data['rooms'])+'};')
    out.append('static const char *const choices[4][2] = {'+','.join('{'+','.join(literal(x) for x in pair)+'}' for pair in data['choices'])+'};')
    out += ['const StoryLine *story_line(SkU8 id,SkU8 page) { return id<D_COUNT && page<counts[id]?&scenes[id][page]:0; }',
            'SkU8 story_pages(SkU8 id) { return id<D_COUNT?counts[id]:0; }',
            'SkU8 game_hotspot_count(SkU8 room) { return room<4?hotspot_counts[room]:0; }',
            'const Hotspot *game_hotspot(SkU8 room,SkU8 index) { return room<4 && index<hotspot_counts[room]?&rooms[room][index]:0; }',
            'const char *room_name(SkU8 room) { return room<4?names[room]:names[0]; }',
            'const char *choice_text(SkU8 id,SkU8 option) { return id<4 && option<2?choices[id][option]:0; }']
    (ROOT/'Data/content/story.c').write_text('\n'.join(out)+'\n')
    header=['/* Generated UTF-8 -> CP1251. */','#ifndef CHERNORECHYE_UI_H','#define CHERNORECHYE_UI_H']
    for key,value in data['ui'].items():
        if any(len(line)>30 for line in value.split('\n')): raise ValueError('UI too wide: '+key)
        header.append('#define TXT_'+key+' '+literal(value))
    header.append('#endif')
    (ROOT/'Data/include/ui_text.h').write_text('\n'.join(header)+'\n')
    page_count=sum(len(data['dialogues'][x]) for x in expected)
    script=['# Сокращённый сценарий SNES-сборки','',
            'Групп сцен: %d; экранов: %d. Исходник — assets/story.json.'%(len(expected),page_count),'',
            'Кирилл после победы над Тенью спускается в подвал НовГУ',
            'и оказывается в Черноречье, в теле Всеволода.','']
    for key in expected:
        script+=['## '+key,'']
        for number,page in enumerate(data['dialogues'][key],1):
            script+=['**%s · %d**'%(page['speaker'],number),'',page['text'],'']
    script+=['## Решения','']
    for number,pair in enumerate(data['choices'],1):
        script+=['%d. %s / %s'%(number,pair[0],pair[1]),'']
    (ROOT/'docs/SCENES.md').write_text('\n'.join(script).rstrip()+'\n')
    print('Content validated:',len(expected),'scenes,',page_count,'pages')
if __name__=='__main__': main()
