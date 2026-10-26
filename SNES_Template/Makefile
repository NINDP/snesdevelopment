SRC := Data

# BEFORE including snes_rules :
# list in AUDIOFILES all your .it files in the right order. It will build to generate soundbank file
AUDIOFILES := Audio/BGM/pollen8.it
# then define the path to generate soundbank data. The name can be different but do not forget to update your include in .c file !
export SOUNDBANK := Data/soundbank

include ${PVSNESLIB_HOME}/devkitsnes/snes_rules

.PHONY: bitmaps all

#---------------------------------------------------------------------------------
# ROMNAME is used in snes_rules file
export ROMNAME := SnesGamejam

#Converting all the images to the files used by the SNES
Image_png = $(wildcard Graphics/Images/*.png)
Image_pal = $(addprefix Graphics/Palettes/,$(notdir $(Image_png:%.png=%.pal)))
Image_map = $(addprefix Graphics/Maps/,$(notdir $(Image_png:%.png=%.map)))
Image_chr = $(addprefix Graphics/Tiles/,$(notdir $(Image_png:%.png=%.chr)))

#path to the superfamiconv
IMGCONV=$(HOME)/SNESDevelopment/ImageConversion/superfamiconv

#path to the emulator
EMULATOR=$(HOME)/SNESDevelopment/MesenEmulator/Mesen

# to build musics, define SMCONVFLAGS with parameters you want
SMCONVFLAGS	:= -s -o $(SOUNDBANK) -V -b 5
musics: $(SOUNDBANK).obj

all: $(Image_pal) $(Image_map) $(Image_chr) musics bitmaps $(ROMNAME).sfc


Graphics/Palettes/%.pal: Graphics/Images/%.png
	$(IMGCONV) -i $^ -p $@

Graphics/Maps/%.map: Graphics/Images/%.png
	$(IMGCONV) -i $^ -m $@

Graphics/Tiles/%.chr: Graphics/Images/%.png
	$(IMGCONV) -i $^ -t $@


clean: cleanBuildRes cleanRom cleanGfx cleanAudio
	rm -f *.o *.sfc
	rm -f $(Image_pal) $(Image_map) $(Image_chr)
	
run:
	$(EMULATOR) $(ROMNAME).sfc
	
	
	
#---------------------------------------------------------------------------------

bitmaps : Graphics/Tiles/pvsneslib.chr Graphics/Tiles/Title.chr Graphics/Tiles/RUSSNES.chr
#Background.pic Ship.pic
