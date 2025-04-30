#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2025 April 28

@author: Michael Kadie
@description: Software to scroll through button options on screen
"""
import displayio
import adafruit_ili9341
import terminalio
import storage
from adafruit_bitmapsaver import save_pixels


import sdcardio


def DrawMenu (across=4,down=2, display=None, group=None):
    """
    Draw the menu on the display
    """
    #display.clear()
    menu_width = int(display.width // across) 
    menu_height = int(display.height // down) 

    for i in range (across) :
        for j in range (down) :
            xStart = i * menu_width
            yStart = j * menu_height
            outer_bitmap = displayio.Bitmap(menu_width, menu_height, 1)
            outer_palette = displayio.Palette(1)
            outer_palette[0] = 0xFFFFFF  # Black
            outer_sprite = displayio.TileGrid(
                outer_bitmap, pixel_shader=outer_palette, x=xStart, y=yStart
            )
            group.append(outer_sprite)


            inner_bitmap = displayio.Bitmap(menu_width - 4 * 2, menu_height - 4 * 2, 1)
            inner_palette = displayio.Palette(1)
            inner_palette[0] = 0x000000  # Black
            inner_sprite = displayio.TileGrid(
                inner_bitmap, pixel_shader=inner_palette, x=xStart+4, y=yStart+4
            )
            group.append(inner_sprite)
    #display.show()
    # print('Taking Screenshot...')
    # save_pixels('/sd/screenshot.bmp', display, group)
    # print('Screenshot taken')
