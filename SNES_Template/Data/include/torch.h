#ifndef CHERNORECHYE_TORCH_H
#define CHERNORECHYE_TORCH_H
#include "game.h"
#define TORCH_TILE_BYTES 4096
#define TORCH_OAM_BYTES 4096
/* Mode7 only, under forced blank on enter/leave. Owns OBJ96..223, slots52..59. */
void torch_enter(void);
void torch_leave(void);
void torch_draw(const Game *g);
#endif
