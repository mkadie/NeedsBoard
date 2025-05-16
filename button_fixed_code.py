import adafruit_24lc32
import time
import array
import math
import audiocore
import board
import audiobusio
import board
import analogio
import time
import digitalio
import struct

import sdcardio
import storage
import os

import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import adafruit_ili9341

import adafruit_24lc32
import rotaryio
import usb_hid
import adafruit_pca9554
import fourwire 

import button_config
import SpriteMenu

print ("Starting")

import neopixel
import audiomp3

demo_test = False

rp2350 = True
if rp2350 :
    Neopixel_pin = board.D13
    tft_cs = board.D10
    rot_a = board.D6
    rot_b = board.D5
else : 
    Neopixel_pin = board.D6
    tft_cs = board.D10
    rot_a = board.D12
    rot_b = board.D13
int_pin = board.D25
button_int = digitalio.DigitalInOut(int_pin)
# Make the display context
button_int.direction = digitalio.Direction.INPUT
button_int.pull = digitalio.Pull.UP


reset_Button_Latch_pin = board.D24

reset_Button_Latch = digitalio.DigitalInOut(reset_Button_Latch_pin)
# Make the display context
reset_Button_Latch.direction = digitalio.Direction.OUTPUT
reset_Button_Latch.value = True

red = (100,0,0)
green = (0,100,0)
blue = (0,0,100)
pixel = None

def ShowCurButtonWithLight (ButtonNumber = None) :
    global pixel
    if (pixel is not None) : 
        pixel.fill((0, 0, 0))
        if (ButtonNumber is not None) and (ButtonNumber < number_of_buttons) : 
            #print ("Engaging")
            first_pixel = ButtonNumber * 4
            on_color = (50,50,50)
            pixel[first_pixel] = on_color

def EngageWithLight (ButtonNumber = 0) :
    global pixel
    if (pixel is not None) : 
        #print ("Engaging")
        first_pixel = ButtonNumber * 4
        chase_pattern = (1,2,0,3)
        all_pixels = (0,1,2,3)
        on_color = (100,10,100)
        off_color = (10,100,10)
        really_off = (0,0,0)
        color_sequence = (red,green,blue)
        for i in (chase_pattern):
            pixel[i+first_pixel] = on_color
            time.sleep(.05)
            #pixel[i+first_pixel] = off_color
            pixel[i+first_pixel] = really_off
        for i in (chase_pattern):
            pixel[i+first_pixel] = really_off
        for color in (color_sequence) :
            for i in (all_pixels):
                pixel[i+first_pixel] = color
            time.sleep(.05)
            for i in  (all_pixels):
                pixel[i+first_pixel] = really_off





from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

print ("Start LCD")
displayio.release_displays()

screen_width=320 
screen_height=240
Thermister = False
spi = board.SPI()
spi.try_lock()
spi.configure(baudrate=5000000)
spi.unlock()
tft_reset = board.A0
#tft_cs = board.D10
tft_dc = board.TX

display_bus = fourwire.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset
)
display = adafruit_ili9341.ILI9341(display_bus, width=screen_width, height=screen_height, rotation = 180)

splash = displayio.Group()
display.root_group = splash #circuit python v 9
#display.show(splash) # circuit python 7-8

# SPDX-FileCopyrightText: 2019 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

if demo_test :
    import adafruit_imageload
    bitmap, palette = adafruit_imageload.load("/lcd_images/0_needs_small.bmp",
                                            bitmap=displayio.Bitmap,
                                            palette=displayio.Palette)

    # Create a TileGrid to hold the bitmap
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

    # Create a Group to hold the TileGrid
    group = displayio.Group()

    # Add the TileGrid to the Group
    group.append(tile_grid)

    # Add the Group to the Display
    display.root_group = group
    time.sleep(1)

pixel = neopixel.NeoPixel(Neopixel_pin, 32)    ## 2 button boards
number_of_buttons = 8
if demo_test :    
    for selected_button in range (number_of_buttons):
        # EngageWithLight(selected_button)
        pixel.fill((selected_button *30, 0, 0))
        time.sleep(.25)

    # EngageWithLight is better demo
    # for __ in range (4):
    #     for i in range(32):
    #         if (i > 0) : 
    #             pixel[i-1] = (0,0,0,0)
    #         pixel[i] = (100,10,100)
    #         time.sleep(.1)
        pixel.fill((0, 0, 0))



audio = audiobusio.I2SOut(board.A1, board.A2, board.A3)
#audio_enable = digitalio.DigitalInOut(board.D13)
# Make the display context
#audio_enable.direction = digitalio.Direction.OUTPUT
#audio_enable.value = False
#time.sleep(1)
tone_volume = 0.02  # Increase this to increase the volume of the tone.
frequency = 440  # Set this to the Hz of the tone you want to generate.
length = 2000 // frequency
sine_wave = array.array("h", [0] * length)
for i in range(length):
    sine_wave[i] = int((math.sin(math.pi * 2 * i / length)) * tone_volume * (2 ** 15 - 1))
sine_wave_sample = audiocore.RawSample(sine_wave)

audio.play(sine_wave_sample, loop=True)
time.sleep(.2)
audio.stop()

if demo_test :
    with open("/button_sounds/milk_นม.wav", "rb") as wave_file:
        wav = audiocore.WaveFile(wave_file)
        print("Playing wav file!")
        time.sleep(2)
        audio.play(wav)
        while audio.playing:
            pass
pixel.fill((0, 0, 0))




print ('Starting')
#time.sleep(4)

#SD Code
# Use the filesystem as normal! Our files are under /sd

# This helper function will print the contents of the SD


def print_directory(path, tabs=0):
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " by"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print('{0:<40} Size: {1:>10}'.format(prettyprintname, sizestr))

        # recursively print directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)


print ('Setup SD Card')
SD_CS = board.RX
try :
    sdcard = sdcardio.SDCard(spi, SD_CS)
    print ('Setup FAT')
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    if demo_test :
        print("Files on filesystem:")
        print("====================")
        print_directory("/sd")
except :
    print ("No SD I Hope ..")

print ("I2C Scanner")   
i2c = board.I2C()
while True:
    while not i2c.try_lock():
        pass

    print(
        "addresses found:",
        [hex(device_address) for device_address in i2c.scan()],
    )

    i2c.unlock()
    break

# setup menu and display images
menu = SpriteMenu.SpriteMenu(display=display,group=splash)
menu.initialize()

print ("I2C Mux")

# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Pat Satyshur
#
# SPDX-License-Identifier: Unlicense

# Make sure to change the code based on the expander type you are using.

# Change this if you are not using a PCA9555
print ("IO Mux")
from i2c_expanders.PCA9555 import PCA9555
print ("I2C pins")

# To use default I2C bus (most boards)
i2c = board.I2C()  # uses board.SCL and board.SDA

# Change this to match the address of the device.
PCA9555_Address0 = 0x20
PCA9555_Address1 = 0x24

print (dir(PCA9555))
# Initialize the device and get pins
# Change this if you are not using a PCA9555
IOEXP0_dev = PCA9555(i2c, address=PCA9555_Address0)
pin00 = IOEXP0_dev.get_pin(4)
pin01 = IOEXP0_dev.get_pin(5)
pin02 = IOEXP0_dev.get_pin(6)
pin03 = IOEXP0_dev.get_pin(7)

# Pin 0 is an output with an initial value of high (true)
#pin0.switch_to_output(value=False)
pin00.switch_to_input(invert_polarity=True)

# Pin 1 is an output with an initial value of low (false)
#pin1.switch_to_output(value=True)
pin01.switch_to_input(invert_polarity=True)

# Pin 2 is an input with a pull up resistor and standard polarity
pin02.switch_to_input(invert_polarity=True)
#IOEXP1_dev.set_int_pin (2,latch=True)

# Pin 3 is an input with a pull down resistor and inverted polarity
pin03.switch_to_input(invert_polarity=True)

# Initialize the device and get pins
# Change this if you are not using a PCA9555
IOEXP1_dev = PCA9555(i2c, address=PCA9555_Address1)
pin10 = IOEXP1_dev.get_pin(4)
pin11 = IOEXP1_dev.get_pin(5)
pin12 = IOEXP1_dev.get_pin(6)
pin13 = IOEXP1_dev.get_pin(7)

# Pin 0 is an output with an initial value of high (true)
#pin0.switch_to_output(value=False)
pin10.switch_to_input(invert_polarity=True)

# Pin 1 is an output with an initial value of low (false)
#pin1.switch_to_output(value=True)
pin11.switch_to_input(invert_polarity=True)

# Pin 2 is an input with a pull up resistor and standard polarity
pin12.switch_to_input(invert_polarity=True)
#IOEXP1_dev.set_int_pin (2,latch=True)

# Pin 3 is an input with a pull down resistor and inverted polarity
pin13.switch_to_input(invert_polarity=True)

encoder = rotaryio.IncrementalEncoder(rot_a, rot_b)
button = digitalio.DigitalInOut(board.D9)
# Make the display context
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
encoder.position = menu.default_menu
lastButton = button.value
lastPosition = encoder.position


def button_pressed(button_pressed):
    # Play the sound file
    print("Playing sound file!"+button_config.button_sound[button_pressed])
#    menu.set_menu (button_pressed)
    with open(button_config.button_sound[button_pressed], "rb") as wave_file:
        wav = audiocore.WaveFile(wave_file)
        time.sleep(.1)
        audio.play(wav)
        menu.set_menu (button_pressed)
        while audio.playing:
            EngageWithLight(button_pressed)
            pass
    menu.set_menu (menu.default_menu)
    print("Done playing sound file!")

# Toggle output pins. Read value from input pins.
while (True) : 
#for __ in range (100):
    if (not (lastButton== button.value and lastPosition == encoder.position)) : 
        lastPosition = encoder.position
        if lastPosition > menu.default_menu :
            lastPosition = 0
        if lastPosition < 0:
            lastPosition = menu.default_menu
        if (lastButton != button.value) :
            lastButton = button.value
            if (lastButton == False) :
                print("Button pressed")
                if (lastPosition < menu.default_menu) :
                    button_pressed(lastPosition)
        menu.set_menu (lastPosition)
        ShowCurButtonWithLight(lastPosition)
        encoder.position = lastPosition
        print("encoder: ", lastPosition)

        print("pin 0: ", pin10.value)
        print("pin 1: ", pin11.value)
        print("pin 2: ", pin12.value)
        print("pin 3: ", pin13.value)
    if (not pin00.value) :
        button_pressed(0)
    if (not pin01.value) :
        button_pressed(1)
    if (not pin02.value) :
        button_pressed(2)
    if (not pin03.value) :
        button_pressed(3)
    if (not pin10.value) :
        button_pressed(4)
    if (not pin11.value) :
        button_pressed(5)
    if (not pin12.value) :
        button_pressed(6)
    if (not pin13.value) :
        button_pressed(7)
    reset_Button_Latch.value = False
    time.sleep(.1)
    reset_Button_Latch.value = True

    time.sleep(.1)    
reset_Button_Latch.value = False
