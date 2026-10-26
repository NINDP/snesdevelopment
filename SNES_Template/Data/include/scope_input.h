#ifndef SCOPE_INPUT_H
#define SCOPE_INPUT_H
#include "sneskit.h"
typedef struct {
    SkU16 buttons, flags, raw_x, raw_y, pad_pressed;
    SkU8 connected, valid;
} ScopePacket;
void scope_capture_vblank(void);
void scope_take_packet(ScopePacket *packet);
SkU16 scope_pad_buttons(void);
#endif
