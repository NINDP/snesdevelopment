/*****************************************************************************/
/*  Автор         		: Дракончик				                             */
/*  Приставка     		: Super Nintendo Entertainment System	             */
/*  Язык	      		: GNU TCC C                                          */
/*                                                                           */
/*  Содержимое файла	: Стадия главного меню		                         */
/*  Атрибут файла		: SOURCE                                             */
/*  Имя файла     		: menuState.c	                                     */
/*                                                                           */
/*****************************************************************************/

#include <snes.h>

#include "include/gameState.h"
#include "include/menuState.h"
#include "include/overState.h"
#include "include/introState.h"
#include "include/musicManager.h"

#include "extern/menuState.ext"

int menuTimer;

extern int ChangeState;

void MenuStart(void)
{
	// Copy tiles to VRAM
	bgInitTileSet(0, &TitlePic, &TitlePal, 0, (&TitlePic_end - &TitlePic), (&TitlePal_end - &TitlePal), BG_16COLORS, 0x4000);

	// Copy Map to VRAM
	bgInitMapSet(0, &TitleMap, (&TitleMap_end - &TitleMap), SC_32x32, 0x0000);
		
	playMusic(0);
    
    // Initialize text console with our font
    consoleSetTextVramBGAdr(0x6800);
    consoleSetTextVramAdr(0x3000);
    consoleSetTextOffset(0x0100);
    consoleInitText(1, 16 * 2, &FontPic, &FontPal);

    // Init background
    bgSetGfxPtr(1, 0x2000);
    bgSetMapPtr(1, 0x6800, SC_32x32);

    // Now Put in 16 color mode and disable Bgs except current
    setMode(BG_MODE1, 0);
    setMode(BG_MODE1, 1);
    bgSetDisable(2);
	
	setFadeEffect(FADE_IN);
	setScreenOn();

	
	menuTimer = 0;
    
}
 
void MenuUpdate(void)
{
	 unsigned short padnr = 0;
	padnr = padsCurrent(0);
	if( padnr == KEY_START)
	{
		ChangeState = 8;
	}
	
	
	menuTimer++;
	if(menuTimer == 12000)
	{
		setFadeEffect(FADE_OUT);
	}
	
	if(menuTimer == 12005)
	{
		ChangeState = 0;
	}
	
}

void MenuDraw(void)
{
	char test[] = "Yf;vbnmt ryjgre Cnfhn";
	consoleDrawText(2, 20, "Nht,etncz rjvfylf lkz ghjtrnf");
	WaitForVBlank();
}

void MenuEnd(void)
{
	
}

