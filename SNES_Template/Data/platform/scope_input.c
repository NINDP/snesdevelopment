#include <snes.h>
#include "../include/scope_input.h"
#define SK_OPHCT (*(vuint8 *)0x213c)
#define SK_OPVCT (*(vuint8 *)0x213d)

/* Super Scope emits short optical packets. PVSnesLib skips its input reader
   on lag frames. Capture the raw packet on every VBlank, including transitions,
   so a gun button cannot disappear while a dialogue map is being prepared.
   This adapter owns NMI; the project does not use consoleDrawText/consoleVblank. */
static volatile ScopePacket queue[4];
static volatile SkU8 head = 0, tail = 0, connected = 0;
static SkU16 last_raw_x = 0, last_raw_y = 0;
static SkU16 previous_buttons = 0;
static volatile SkU16 held_pad = 0;
/* TURBO is a switch, not a button edge. Keep it on idle frames too. */
static volatile SkU16 held_scope = 0;
static SkU16 previous_pad = 0;

void scope_capture_vblank(void) {
    SkU16 buttons, edges, pad, pad_edges;
    SkU8 latched, next, index;
    while (REG_HVBJOY & 1) {
    } /* wait for controller auto-read to finish */
    pad = REG_JOYxLH(0);
    if (pad & 15)
        pad = 0;
    pad_edges = (pad ^ previous_pad) & pad;
    previous_pad = pad;
    held_pad = pad;
    buttons = REG_JOYxLH(1);
    connected = (buttons & 0x0cff) == 0x00ff;
    held_scope = connected ? buttons & (SSC_FIRE | SSC_CURSOR | SSC_PAUSE | SSC_TURBO) : 0;
    edges = 0;
    if (connected) {
        edges = (buttons ^ previous_buttons) & buttons;
        previous_buttons = buttons;
        if ((buttons & SSC_TURBO) && (buttons & SSC_FIRE))
            edges |= SSC_FIRE;
    } else
        previous_buttons = 0;
    edges &= SSC_FIRE | SSC_CURSOR | SSC_PAUSE;
    if (!edges && !pad_edges)
        return;
    index = head;
    next = (head + 1) & 3;
    if (next == tail)
        return; /* bounded queue, no shared writer for tail */
    queue[index].buttons = edges | (buttons & SSC_TURBO);
    queue[index].pad_pressed = pad_edges;
    queue[index].flags = 0;
    queue[index].valid = 0;
    queue[index].raw_x = last_raw_x;
    queue[index].raw_y = last_raw_y;
    if (edges & (SSC_FIRE | SSC_CURSOR)) {
        queue[index].flags = buttons & (SSC_OFFSCREEN | SSC_NOISE);
        latched = (REG_STAT78 & 0x40) != 0;
        if (latched && !queue[index].flags) {
            last_raw_x = SK_OPHCT;
            last_raw_x |= (SkU16)(SK_OPHCT & 1) << 8;
            last_raw_y = SK_OPVCT;
            last_raw_y |= (SkU16)(SK_OPVCT & 1) << 8;
            queue[index].raw_x = last_raw_x;
            queue[index].raw_y = last_raw_y;
            queue[index].valid = 1;
        }
    }
    /* Publish only after every field has been written. 8-bit stores are atomic. */
    head = next;
}

void scope_take_packet(ScopePacket *packet) {
    static SkU16 previous_x = 0, previous_y = 0;
    SkU8 index;
    packet->buttons = held_scope & SSC_TURBO;
    packet->flags = 0;
    packet->valid = 0;
    packet->pad_pressed = 0;
    packet->raw_x = previous_x;
    packet->raw_y = previous_y;
    packet->connected = connected;
    if (tail == head)
        return;
    index = tail;
    packet->buttons = (queue[index].buttons & (SSC_FIRE | SSC_CURSOR | SSC_PAUSE)) |
                      (held_scope & SSC_TURBO);
    packet->pad_pressed = queue[index].pad_pressed;
    packet->flags = queue[index].flags;
    packet->raw_x = queue[index].raw_x;
    packet->raw_y = queue[index].raw_y;
    packet->valid = queue[index].valid;
    previous_x = packet->raw_x;
    previous_y = packet->raw_y;
    /* ISR cannot overwrite this slot until tail is published. No NMI toggles. */
    tail = (tail + 1) & 3;
}

SkU16 scope_pad_buttons(void) {
    return held_pad;
}
SkU16 scope_held_buttons(void) {
    return held_scope;
}
SkU8 scope_packets_pending(void) {
    return head != tail;
}
