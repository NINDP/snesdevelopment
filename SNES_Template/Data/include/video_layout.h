#ifndef CHERNORECHYE_VIDEO_LAYOUT_H
#define CHERNORECHYE_VIDEO_LAYOUT_H
/* PPU addresses are WORD addresses; payload sizes below are bytes. */
#define VIDEO_BG_TILES 0x0000
#define VIDEO_BG_MAP 0x4000
#define VIDEO_AMBIENT_MAP 0x4400
#define VIDEO_FONT_TILES 0x5000
#define VIDEO_TEXT_MAP 0x5c00
#define VIDEO_OBJ_TILES 0x6000
#define VIDEO_TEXT_ROWS 28
#define VIDEO_TEXT_ENTRIES 896
#define VIDEO_TEXT_BYTES 1792
#define VIDEO_HDMA_BYTES 133
#define VIDEO_ACTOR_SLOTS 18
/* Header (3), 42 four-line bands (126), footer (3), terminator (1). */
typedef char video_text_size_check[(VIDEO_TEXT_ENTRIES == 32 * VIDEO_TEXT_ROWS) ? 1 : -1];
typedef char video_hdma_size_check[(VIDEO_HDMA_BYTES == 3 + 42 * 3 + 3 + 1) ? 1 : -1];
#endif
