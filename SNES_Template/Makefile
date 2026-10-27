ifeq ($(strip $(PVSNESLIB_HOME)),)
$(error Set PVSNESLIB_HOME to PVSnesLib 4.6.0, or run sh tools/get_sdk.sh)
endif
export ROMNAME := chernorechye
export ROMTITLE := NABLA CHERNORECHYE
export ROMBANKS := 32
export ROMSIZE := 0A
export COUNTRY := 01
export FASTROM := 1
export SRC := Data
# Explicit manifest: legacy demo states/music and compiler .asm are not linked.
override CFILES := main.c Data/gameState.c $(wildcard Data/core/*.c) $(wildcard Data/platform/*.c) $(wildcard Data/content/*.c)
override SFILES := Data/content/assets.asm Data/content/audio.asm Data/perspective_oam.asm
include $(PVSNESLIB_HOME)/devkitsnes/snes_rules
CFLAGS += -DSNES_TARGET
export OFILES := $(sort $(CFILES:.c=.obj) $(SFILES:.asm=.obj))
$(ROMNAME).sfc: $(OFILES) Makefile tools/link_rom.py
	python3 tools/link_rom.py --linker "$(LD)" --library-dir "$(LIBDIRSOBJS)" --output "$@" $(OFILES)
# Headers must invalidate C -> .ps, not just the assembler/object stage.
$(CFILES:.c=.ps): Makefile $(wildcard Data/include/*.h)
$(OFILES): Makefile
.SECONDARY:
.PHONY: all assets clean buildActual
buildActual: $(ROMNAME).sfc
all: assets
	$(MAKE) buildActual
assets:
	python3 tools/build_content.py
	python3 tools/build_assets.py
	python3 tools/build_audio.py
clean: cleanBuildRes cleanRom cleanLogs
