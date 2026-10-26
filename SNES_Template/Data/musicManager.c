/*****************************************************************************/
/*  Автор         		: Дракончик				                             */
/*  Приставка     		: Super Nintendo Entertainment System	             */
/*  Язык	      		: GNU TCC C                                          */
/*                                                                           */
/*  Содержимое файла	: Управление  музики в игре	                         */
/*  Атрибут файла		: SOURCE                                             */
/*  Имя файла     		: musicManager.c                                     */
/*                                                                           */
/*****************************************************************************/

#include "include/musicManager.h"


void updateMusicManager()
{
	// Update music / sfx stream and wait vbl
	spcProcess();
	WaitForVBlank();
}

void playMusic(int musicNr)
{
	// Load music
	spcLoad(musicNr);
	
 	// Play file from the beginning
	spcPlay(0);
}
