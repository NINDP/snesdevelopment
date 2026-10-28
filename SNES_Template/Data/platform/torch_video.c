#include <snes.h>
#include "../include/torch.h"
#include "../include/video_layout.h"
extern u8 torch_tiles, torch_palette, sprite_tiles;
void torch_oam_draw(SkU16 offset);
void torch_oam_hide(void);
void torch_upload(u8 *data);
SkU16 torch_slot = 52;
static SkU8 uploaded = 255, pending = 255;
void torch_enter(void) {
    torch_upload(&torch_tiles);
    uploaded = 0;
    pending = 255;
    dmaCopyCGram(&torch_palette, 224, 32);
    torch_oam_hide();
}
void torch_leave(void) {
    /* Tile96 begins3072B into the legacy atlas. Restore it for the prologue. */
    dmaCopyVram(&sprite_tiles + 3072, VIDEO_OBJ_TILES + 1536, TORCH_TILE_BYTES);
    torch_oam_hide();
}
void torch_draw(const Game *g) {
    SkU16 offset;
    if (!g->lamp) {
        torch_oam_hide();
        return;
    }
    if (!g->oil) {
        torch_oam_hide();
        return;
    }
    /* Precomputed eight-sprite poses: two shifts, no software multiply,
       division, random source, WRAM particle pool, or frame-time OAM loop. */
    offset = (g->bow_mode ? 4096 : (SkU16)((g->direction >> 1) & 3) << 10) +
             ((g->tick & 31) << 5);
    torch_oam_draw(offset);
    if (((g->tick >> 2) & 7) != uploaded)
        pending = (g->tick >> 2) & 7;
}
void torch_commit(void) {
    if (pending == 255) return;
    torch_upload(&torch_tiles + ((SkU16)pending << 9));
    uploaded = pending;
    pending = 255;
}
