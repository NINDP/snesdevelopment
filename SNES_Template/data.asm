.include "hdr.asm"

.section ".rodata1" superfree

;Folowing list is graphical data used for the game.

IntroPic:
.incbin "Graphics/Tiles/pvsneslib.chr"
IntroPic_end:

IntroMap:
.incbin "Graphics/Maps/pvsneslib.map"
IntroMap_end:

IntroPal: 
.incbin "Graphics/Palettes/pvsneslib.pal"
IntroPal_end:

FontPic:
.incbin "Graphics/Tiles/RUSSNES.chr"
FontPic_end:

FontPal: 
.incbin "Graphics/Palettes/RUSSNES.pal"
FontPal_end:

.ends

.section ".rodata2" superfree

TitlePic:
.incbin "Graphics/Tiles/Title.chr"
TitlePic_end:

TitleMap:
.incbin "Graphics/Maps/Title.map"
TitleMap_end:

TitlePal: 
.incbin "Graphics/Palettes/Title.pal"
TitlePal_end:

.ends

.section ".rodata3" superfree

.ends

