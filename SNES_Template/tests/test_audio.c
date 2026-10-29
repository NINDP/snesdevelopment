#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "audio.h"
static int heard(SkU8 wanted) {
    SkU8 id;int found=0;
    while ((id=sound_take())!=S_NONE) if (id==wanted) found=1;
    return found;
}
int main(void) {
    Game g;SkInput in;SkU8 i;
    memset(&in,0,sizeof(in));game_new(&g);sound_reset();
    g.mode=G_CORRIDOR;g.x=g.destination_x=CORRIDOR_START;
    in.held=SK_LEFT;
    for (i=0;i<40;++i) game_tick(&g,&in);
    assert(sound_take()==S_NONE); /* Holding into a wall is silent. */
    in.held=SK_RIGHT;
    for (i=0;i<24;++i) game_tick(&g,&in);
    assert(heard(S_STEP_UNIVERSITY_01));
    g.mode=G_EXPLORE;g.room=0;g.x=124;g.y=176;g.lamp=0;
    memset(&in,0,sizeof(in));in.pressed=SK_LIGHT;sound_reset();game_tick(&g,&in);
    assert(heard(S_TORCH_TOGGLE_ON));
    in.pressed=0;game_tick(&g,&in);assert(sound_take()==S_NONE);
    in.pressed=SK_JOURNAL;game_tick(&g,&in);assert(heard(S_JOURNAL_HANDLE_OPEN));
    in.pressed=SK_RIGHT;game_tick(&g,&in);assert(heard(S_JOURNAL_PAGE));
    in.pressed=SK_BACK;game_tick(&g,&in);assert(heard(S_JOURNAL_HANDLE_CLOSE));
    for (i=0;i<2;++i) {
        g.mode=G_DIALOGUE;g.dialogue=D_GRAVE;g.page=story_pages(D_GRAVE)-1;
        g.revealed=story_line(D_GRAVE,g.page)->length;
        sound_reset();in.pressed=SK_ACTION;game_tick(&g,&in);
        assert(heard(S_EVIDENCE_ADDED)==(i==0));
    }
    sound_story(D_ECHO_BOAT,0);
    assert(sound_take()==S_BOAT_CREAK);
    sound_story(D_PROLOG,2); /* Leaving a page cancels its delayed rope/water. */
    sound_step(200);assert(sound_take()==S_WORLD_CROSSING_ENTRY);assert(sound_take()==S_NONE);
    sound_schedule(S_UI_MOVE,0);sound_schedule(S_STEP_GROUND_01,0);sound_emit(S_FOX_WARNING_01);
    assert(sound_take()==S_FOX_WARNING_01);
    puts("PASS: footfalls, walls, torch edges, journal, unique evidence, page cancellation and warnings");
    return 0;
}
