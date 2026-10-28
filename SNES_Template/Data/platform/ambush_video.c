#include <snes.h>
#include "../include/platform.h"
extern u8 ambush_ground_vram, ambush_ground_palette;
extern u8 ambush_sky_tiles, ambush_sky_tiles_end, ambush_sky_palette;
extern u8 ambush_obj_tiles, ambush_obj_tiles_end;
extern u8 ambush_hero_palette, ambush_fox_palette, ambush_fx_palette;
extern u8 ambush_modes_active, ambush_layers_active, ambush_modes_overlay, ambush_layers_overlay;
extern u8 perspective_scale, sprite_tiles, sprite_tiles_end, sprite_palette;
extern u8 ambush_fox_frame0;
extern u8 ambush_fox_frame1;
extern u8 ambush_fox_frame2;
extern u8 ambush_fox_frame3;
extern u8 ambush_fox_frame4;
extern u8 ambush_fox_frame5;
extern u8 ambush_fox_frame6;
extern u8 ambush_fox_frame7;
extern u8 ambush_fox_frame8;
extern u8 ambush_fox_frame9;
extern u8 ambush_fox_frame10;
extern u8 ambush_fox_frame11;
extern u8 ambush_fox_frame12;
extern u8 ambush_fox_frame13;
extern u8 ambush_fox_frame14;
extern u8 ambush_fox_frame15;
extern u8 ambush_fox_frame16;
extern u8 ambush_fox_frame17;
extern u8 ambush_fox_frame18;
extern u8 ambush_fox_frame19;
extern u8 ambush_fox_frame20;
extern u8 ambush_fox_frame21;
extern u8 ambush_fox_frame22;
extern u8 ambush_fox_frame23;
extern u8 ambush_fox_frame24;
extern u8 ambush_fox_frame25;
extern u8 ambush_fox_frame26;
extern u8 ambush_fox_frame27;
extern u8 ambush_fox_frame28;
extern u8 ambush_fox_frame29;
extern u8 ambush_fox_frame30;
extern u8 ambush_fox_frame31;
extern u8 ambush_fox_frame32;
extern u8 ambush_fox_frame33;
extern u8 ambush_fox_frame34;
extern u8 ambush_fox_frame35;
extern u8 ambush_fox_frame36;
extern u8 ambush_fox_frame37;
extern u8 ambush_fox_frame38;
extern u8 ambush_fox_frame39;
extern u8 ambush_fox_frame40;
extern u8 ambush_fox_frame41;
extern u8 ambush_fox_frame42;
extern u8 ambush_fox_frame43;
extern u8 ambush_fox_frame44;
extern u8 ambush_fox_frame45;
extern u8 ambush_fox_frame46;
extern u8 ambush_fox_frame47;
extern u8 ambush_fox_frame48;
extern u8 ambush_fox_frame49;
extern u8 ambush_fox_frame50;
extern u8 ambush_fox_frame51;
extern u8 ambush_fox_frame52;
extern u8 ambush_fox_frame53;
extern u8 ambush_fox_frame54;
extern u8 ambush_fox_frame55;
extern u8 ambush_fox_frame56;
extern u8 ambush_fox_frame57;
extern u8 ambush_fox_frame58;
extern u8 ambush_fox_frame59;
extern u8 ambush_fox_frame60;
extern u8 ambush_fox_frame61;
extern u8 ambush_fox_frame62;
extern u8 ambush_fox_frame63;
static u8 *const fox_frames[64] = {&ambush_fox_frame0,&ambush_fox_frame1,&ambush_fox_frame2,&ambush_fox_frame3,&ambush_fox_frame4,&ambush_fox_frame5,&ambush_fox_frame6,&ambush_fox_frame7,&ambush_fox_frame8,&ambush_fox_frame9,&ambush_fox_frame10,&ambush_fox_frame11,&ambush_fox_frame12,&ambush_fox_frame13,&ambush_fox_frame14,&ambush_fox_frame15,&ambush_fox_frame16,&ambush_fox_frame17,&ambush_fox_frame18,&ambush_fox_frame19,&ambush_fox_frame20,&ambush_fox_frame21,&ambush_fox_frame22,&ambush_fox_frame23,&ambush_fox_frame24,&ambush_fox_frame25,&ambush_fox_frame26,&ambush_fox_frame27,&ambush_fox_frame28,&ambush_fox_frame29,&ambush_fox_frame30,&ambush_fox_frame31,&ambush_fox_frame32,&ambush_fox_frame33,&ambush_fox_frame34,&ambush_fox_frame35,&ambush_fox_frame36,&ambush_fox_frame37,&ambush_fox_frame38,&ambush_fox_frame39,&ambush_fox_frame40,&ambush_fox_frame41,&ambush_fox_frame42,&ambush_fox_frame43,&ambush_fox_frame44,&ambush_fox_frame45,&ambush_fox_frame46,&ambush_fox_frame47,&ambush_fox_frame48,&ambush_fox_frame49,&ambush_fox_frame50,&ambush_fox_frame51,&ambush_fox_frame52,&ambush_fox_frame53,&ambush_fox_frame54,&ambush_fox_frame55,&ambush_fox_frame56,&ambush_fox_frame57,&ambush_fox_frame58,&ambush_fox_frame59,&ambush_fox_frame60,&ambush_fox_frame61,&ambush_fox_frame62,&ambush_fox_frame63};
static dmaMemory mode_source,layer_source,scale_source,sky_source;
static SkU8 sky_scroll[4],overlay=0,palette_overlay=255;
static SkU8 loaded_pose[4],pending_pose[4],stream_cursor=0;
static SkS16 camera_x=512,old_x=128;
static SkU8 stream_index=255;
static u8 *stream_frame;
static SkU16 stream_vram,camera_hofs;
static SkS16 sky_parallax;
extern SkU16 video_late_commits;
void perspective_obj(SkU16 slot,SkS16 x,SkS16 y,SkU16 tile,SkU16 large);
void perspective_clear(void);
static void object(SkU16 id,SkS16 x,SkS16 y,SkU16 tile,SkU16 palette,SkU16 large) {
    perspective_obj(id,x,y,tile|(palette<<9),large);
}
static void ui_palette(void) {
    if(overlay==palette_overlay)return;
    if(overlay) {
        setPaletteColor(29,RGB5(4,7,10));
        setPaletteColor(30,RGB5(21,24,25));
        setPaletteColor(31,RGB5(14,17,17));
    } else {
        setPaletteColor(29,RGB5(27,28,25));
        setPaletteColor(30,RGB5(4,7,10));
        setPaletteColor(31,RGB5(17,20,17));
    }
    mode_source.mem.p=overlay?&ambush_modes_overlay:&ambush_modes_active;
    layer_source.mem.p=overlay?&ambush_layers_overlay:&ambush_layers_active;
    REG_A1T1LH=mode_source.mem.c.addr;REG_A1B1=mode_source.mem.c.bank;
    REG_A1T2LH=layer_source.mem.c.addr;REG_A1B2=layer_source.mem.c.bank;
    palette_overlay=overlay;
}
void ambush_video_enter(void) {
    SkU8 i;
    setScreenOff();REG_HDMAEN=0;
    dmaCopyVram(&ambush_ground_vram,0,32768);
    dmaCopyCGram(&ambush_ground_palette,0,32);
    dmaCopyVram(&ambush_sky_tiles,0x4000,&ambush_sky_tiles_end-&ambush_sky_tiles);
    dmaCopyCGram(&ambush_sky_palette,64,32);
    dmaCopyVram(&ambush_obj_tiles,VIDEO_OBJ_TILES,&ambush_obj_tiles_end-&ambush_obj_tiles);
    dmaCopyCGram(&ambush_hero_palette,192,32);
    dmaCopyCGram(&ambush_fox_palette,208,32);
    dmaCopyCGram(&ambush_fx_palette,224,32);
    for(i=0;i<4;++i) {
        dmaCopyVram(fox_frames[0],0x7000+((SkU16)i<<10),2048);
        loaded_pose[i]=0;pending_pose[i]=255;
    }
    stream_cursor=0;overlay=1;palette_overlay=255;
    setMode7(0x80);
    REG_BG2SC=0x38;REG_BG12NBA=0x40;
    REG_BG2VOFS=0;REG_BG2VOFS=0;
    REG_M7B=0;REG_M7B=0;REG_M7C=0;REG_M7C=0;
    REG_M7Y=0;REG_M7Y=2;
    REG_M7VOFS=92;REG_M7VOFS=1;
    REG_TMW=REG_TSW=REG_W12SEL=REG_W34SEL=REG_WOBJSEL=0;
    REG_CGWSEL=REG_CGADSUB=REG_TS=0;REG_COLDATA=0xe0;
    sky_scroll[0]=1;sky_scroll[3]=0;
    scale_source.mem.p=&perspective_scale;sky_source.mem.p=sky_scroll;
    /* Channels 1..5 keep the same targets throughout the encounter.
       Channel 7 belongs to the SDK's OAM upload in every NMI. */
    REG_DMAP1=0;REG_BBAD1=0x05;
    REG_DMAP2=0;REG_BBAD2=0x2c;
    REG_DMAP3=2;REG_BBAD3=0x1b;
    REG_A1T3LH=scale_source.mem.c.addr;REG_A1B3=scale_source.mem.c.bank;
    REG_DMAP4=2;REG_BBAD4=0x1e;
    REG_A1T4LH=scale_source.mem.c.addr;REG_A1B4=scale_source.mem.c.bank;
    REG_DMAP5=2;REG_BBAD5=0x0f;
    REG_A1T5LH=sky_source.mem.c.addr;REG_A1B5=sky_source.mem.c.bank;
    ui_palette();
    old_x=128;setScreenOn();
}
void ambush_video_leave(void) {
    setScreenOff();REG_HDMAEN=0;
    dmaCopyVram(&sprite_tiles,VIDEO_OBJ_TILES,&sprite_tiles_end-&sprite_tiles);
    dmaCopyCGram(&sprite_palette,128,32);
    setPaletteColor(29,RGB5(28,28,24));setPaletteColor(30,RGB5(1,2,3));
    setPaletteColor(31,RGB5(29,24,15));
    REG_TMW=REG_TSW=REG_W12SEL=REG_W34SEL=REG_WOBJSEL=0;
    REG_CGWSEL=REG_CGADSUB=REG_TS=0;
    setMode(BG_MODE1,BG3_MODE1_PRIORITY_HIGH);
}
void ambush_video_draw(const Game *g) {
    SkU8 i,j,q,swap,index,pose,lod,flip,angle;
    SkU8 order[4];
    SkU16 tile,flags;
    SkS16 x,target;
    const Enemy *fox;
    const Arrow *arrow;
    perspective_clear();
    overlay=1;
    if(g->mode==G_AMBUSH) {
        if(g->ambush_phase==AMBUSH_ACTIVE)overlay=0;
        if(g->ambush_phase==AMBUSH_BREATHER)overlay=0;
    }
    camera_x=512+(g->x-128)/5;
    camera_hofs=camera_x-128;
    sky_parallax=(camera_x-512)/3;
    tile=g->bow_cooldown>7?8:(g->bow_cooldown>2?12:0);
    if(g->x!=old_x)tile=96+((g->tick>>3)&1)*4;
    object(0,g->x-16,154,tile,0,1);
    object(1,g->x-16,186,tile+64,0,0);
    object(2,g->x,186,tile+66,0,0);
    if(g->hurt_timer>40)object(7,g->x-8,174,226,2,0);
    old_x=g->x;
    for(i=0;i<4;++i)order[i]=i;
    for(i=0;i<3;++i)for(j=i+1;j<4;++j)
        if(g->enemies[order[j]].y>g->enemies[order[i]].y) {
            swap=order[i];order[i]=order[j];order[j]=swap;
        }
    for(i=0;i<4;++i) {
        index=order[i];fox=&g->enemies[index];pending_pose[index]=255;
        if(fox->hp) {
            lod=ambush_fox_lod(fox->y);
            pose=((g->tick>>3)+index)&3;
            if(fox->state==FOX_WINDUP)pose=4;
            if(fox->state==FOX_CHARGE)pose=5;
            if(fox->state==FOX_RETREAT)pose=6+((g->tick>>3)&1);
            pending_pose[index]=(lod<<3)+pose;
            if((loaded_pose[index]>>3)>lod+1)continue;
            target=g->x;
            if(fox->state==FOX_WINDUP || fox->state==FOX_CHARGE || fox->state==FOX_RETREAT)
                target=fox->respawn;
            flip=target>=fox->x;
            flags=flip?0x4000:0;
            tile=256+((SkU16)index<<6);
            for(q=0;q<4;++q) {
                x=fox->x-32;
                if(flip) { if((q&1)==0)x+=32; }
                else if(q&1)x+=32;
                object(8+i*4+q,x,fox->y-48+(q>>1)*32,tile+q*4+flags,1,1);
            }
            if(fox->state==FOX_WINDUP || fox->state==FOX_CHARGE)
                object(24+index,(SkS16)fox->respawn-8,188,232,2,0);
        } else if(fox->hit) {
            object(24+index,fox->x-8,fox->y-20-(22-fox->hit)/2,226,2,0);
        }
    }
    for(i=0;i<COMBAT_ARROWS;++i) {
        arrow=&g->arrows[i];if(arrow->life==0)continue;
        angle=((combat_direction(arrow->dx,arrow->dy)+1)>>1)&7;
        object(28+i,arrow->x/4-8,arrow->y/4-8,192+angle*2,2,0);
    }
    if(g->ambush_aim_ticks) {
        tile=g->combat_notice==1?226:224;
        object(3,g->aim_x-8,g->aim_y-8,tile,2,0);
    }
    for(i=0;i<g->ambush_health;++i)object(4+i,194+i*17,18,228,2,0);
    for(i=0;i<4;++i)object(32+i,((g->tick>>2)+i*67)&255,
        100+((g->tick/3+i*29)&63),230,2,0);
    for(i=0;i<2;++i) {
        x=i?229:0;x-=(g->x-128)/10;
        object(40+i*3,x,154,104,2,1);
        object(41+i*3,x,186,168,2,0);
        object(42+i*3,x+16,186,170,2,0);
    }
    object(46,34-(g->x-128)/15,121,108,2,1);
    object(47,196-(g->x-128)/12,150,108,2,1);
    object(48,37-(g->x-128)/10,183,172,2,0);
    object(49,53-(g->x-128)/10,183,174,2,0);
    object(50,201-(g->x-128)/10,197,172,2,0);
    object(51,217-(g->x-128)/10,197,174,2,0);
    /* Select the next pose during visible time, leaving only the transfer
       and PPU register writes for the short NTSC VBlank. */
    stream_index=255;
    for(i=0;i<4;++i) {
        index=stream_cursor;stream_cursor=(stream_cursor+1)&3;
        if(pending_pose[index]==255)continue;
        if(pending_pose[index]==loaded_pose[index])continue;
        stream_index=index;
        stream_frame=fox_frames[pending_pose[index]];
        stream_vram=0x7000+((SkU16)index<<10);
        break;
    }
}
void ambush_video_commit(SkU8 full_ui) {
    REG_HDMAEN=0;
    if(full_ui==0) {
        if(stream_index<4) {
            /* The final tile row's right half is transparent padding. A single
               1792-byte DMA is faster than three calls for 1536 useful bytes. */
            dmaCopyVram(stream_frame,stream_vram,1792);
            loaded_pose[stream_index]=pending_pose[stream_index];
        }
    }
    ui_palette();
    REG_BGMODE=7;
    REG_M7X=camera_x;REG_M7X=camera_x>>8;
    REG_M7HOFS=camera_hofs;REG_M7HOFS=camera_hofs>>8;
    sky_scroll[1]=sky_parallax;sky_scroll[2]=sky_parallax>>8;
    REG_TM=0;
    REG_HDMAEN=0x3e;REG_INIDISP=15;
    if((REG_HVBJOY&0x80)==0)++video_late_commits;
}
