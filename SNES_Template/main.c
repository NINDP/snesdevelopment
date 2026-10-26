/* Nabla / Chernorechye entry point for the SNES_Template lifecycle. */
#include "Data/include/gameState.h"
int main(void) {
    GameStart();
    while (1) {
        GameUpdate();
        GameDraw();
    }
    return 0;
}
