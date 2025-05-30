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

print ("Starting")

import neopixel

rp2350 = False
if rp2350 :
    Neopixel_pin = board.D13
    tft_cs = board.D12
    rot_a = board.D6
    rot_b = board.D13
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

use_button_board = True
red = (100,0,0)
green = (0,100,0)
blue = (0,0,100)
pixel = None

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
        for __ in range (3):
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
            time.sleep(.1)
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
tft_reset = board.A0
#tft_cs = board.D10
tft_dc = board.TX

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset
)
display = adafruit_ili9341.ILI9341(display_bus, width=screen_width, height=screen_height, rotation = 180)

splash = displayio.Group()
display.root_group = splash #circuit python v 9
#display.show(splash) # circuit python 7-8

odb = displayio.OnDiskBitmap('/tramp.bmp')
face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
splash.append(face)

if use_button_board : 
    #pixel = neopixel.NeoPixel(Neopixel_pin, 16)    
    pixel = neopixel.NeoPixel(Neopixel_pin, 32)    ## 2 button boards
    number_of_buttons = 8
    for selected_button in range (number_of_buttons):
        EngageWithLight(selected_button)
    # EngageWithLight is better demo
    # for __ in range (4):
    #     for i in range(32):
    #         if (i > 0) : 
    #             pixel[i-1] = (0,0,0,0)
    #         pixel[i] = (100,10,100)
    #         time.sleep(.1)
        pixel.fill((0, 0, 0))

else : 
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

#pixel.brightness = 0.3
#pixel[0] = (100,10,10)
#pixel.fill((255, 0, 0))

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
time.sleep(1)
audio.stop()
# with open("Trampoline.wav", "rb") as wave_file:
#     wav = audiocore.WaveFile(wave_file)

#     print("Playing wav file!")
#     time.sleep(2)
#     audio.play(wav)
#     while audio.playing:
#         pass
#try :
pixel.fill((0, 0, 0))




print ('Starting')
time.sleep(4)

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

    print("Files on filesystem:")
    print("====================")
    print_directory("/sd")
    print_directory("/sd/sound")
    # print ("Play Tramp")
    # with open("/sd/sound/Trampoline.wav", "rb") as wave_file: 
    #     wav = audiocore.WaveFile(wave_file)
    #     print("Playing wav file!")
    #     time.sleep(.2)
    #     audio.play(wav)
    #     while audio.playing:
    #         pass    
    # print ("Play Street Chicken")
    # with open("/sd/sound/StreetChicken.wav", "rb") as wave_file:
    #     wav = audiocore.WaveFile(wave_file)

    #     print("Playing wav file!")
    #     time.sleep(2)
    #     audio.play(wav)
    #     while audio.playing:
    #      pass    
except :
    print ("No SD I Hope ..")

#show all i2c devices
try : 
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

    

    print ("I2C Mux")

    # SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
    # SPDX-FileCopyrightText: Copyright (c) 2023 Pat Satyshur
    #
    # SPDX-License-Identifier: Unlicense

    # Make sure to change the code based on the expander type you are using.

    # Change this if you are not using a PCA9555
    print ("IO Mux")
    from i2c_expanders.PCA9555 import PCA9555

    # To use default I2C bus (most boards)
    i2c = board.I2C()  # uses board.SCL and board.SDA

    # Change this to match the address of the device.
    PCA9555_Address = 0x24

    print (dir(PCA9555))
    # Initialize the device and get pins
    # Change this if you are not using a PCA9555
    IOEXP1_dev = PCA9555(i2c, address=PCA9555_Address)
    pin0 = IOEXP1_dev.get_pin(0)
    pin1 = IOEXP1_dev.get_pin(1)
    pin2 = IOEXP1_dev.get_pin(2)
    pin3 = IOEXP1_dev.get_pin(3)

    # Pin 0 is an output with an initial value of high (true)
    #pin0.switch_to_output(value=False)
    pin0.switch_to_input(invert_polarity=False)

    # Pin 1 is an output with an initial value of low (false)
    #pin1.switch_to_output(value=True)
    pin1.switch_to_input(invert_polarity=False)

    # Pin 2 is an input with a pull up resistor and standard polarity
    pin2.switch_to_input(invert_polarity=False)
    #IOEXP1_dev.set_int_pin (2,latch=True)

    # Pin 3 is an input with a pull down resistor and inverted polarity
    pin3.switch_to_input(invert_polarity=False)

    # Toggle output pins. Read value from input pins.
    while (True) : 
    #for __ in range (100):
        if (not button_int.value) : 
            print("pin 0: True")
            print("pin 1: False")
            print("pin 2: ", pin2.value)
            print("pin 3: ", pin3.value)
        #Tramp
        if (not pin0.value) :
            with open("/sd/sound/Trampoline.wav", "rb") as wave_file:
                wav = audiocore.WaveFile(wave_file)

                time.sleep(.2) # give processor chance to be ready so no static on playing file
                audio.play(wav)
                for __ in range (3) :
                    EngageWithLight(4)
                print("Playing wav file!")
                while audio.playing:
                    pass
        if (not pin1.value) :
            with open("/sd/sound/StreetChicken.wav", "rb") as wave_file:
                wav = audiocore.WaveFile(wave_file)

                audio.play(wav)
                for __ in range (3) :
                    EngageWithLight(5)
                print("Playing wav file!")
                while audio.playing:
                    pass
                break


        # pin0.value = pin2.value
        # pin1.value = pin3.value
        time.sleep(.1)    
    # board.I2C().deinit()
    # i2c = board.I2C()
    # tft_io_expander = dict(board.TFT_IO_EXPANDER)

    # pcf = adafruit_pca9554.PCA9554(i2c, address=tft_io_expander['i2c_address'])
    # button_up = pcf.get_pin(board.BTN_UP)
    # button_up.switch_to_input(pull=digitalio.Pull.UP)

    # while True:
    #     print(button_up.value)
    #     time.sleep(0.01)  # debounce


    #eeprom
    eeprom = adafruit_24lc32.EEPROM_I2C(i2c)#, address=0xb)

    print("length: {}".format(len(eeprom)))

    print(eeprom[0:4])

    if (bytearray(eeprom[0:4]) == bytearray([19, 3, 8, 1])):
        print ("Initialized")
    else:
        eeprom[0:4] = [19, 3, 8, 1]
        time.sleep(0.1)
        print(eeprom[0:4])
    time.sleep(3)
except : 
    print ("Hopefully no EEProm")



color_bitmap = displayio.Bitmap(screen_width, screen_height, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White
text = "Associative Assistive Device"
TextGroup = displayio.Group(scale=1, x=10, y= 31 )
text_area = label.Label(
    terminalio.FONT, text=text, color=0xFFFFFF, x=0, y=0
)
TextGroup.append (text_area)
splash.append(TextGroup)

RotaryGroup = displayio.Group(scale=3, x=10, y= 81 )
Rotary_area = label.Label(
    terminalio.FONT, text="Rotary", color=0xFFFFFF, x=0, y=0
)
RotaryGroup.append (Rotary_area)
splash.append (RotaryGroup)

VoltGroup = displayio.Group(scale=3, x=10, y= 81 )
Volt_area = label.Label(
    terminalio.FONT, text="v1,v2,v3,v4", color=0xFFFFFF, x=0, y=20
)
RotaryGroup.append (Volt_area)
splash.append (VoltGroup)

print (dir(board))

time.sleep(3)

use_alarm = None
if (use_alarm is not None) : 
    import alarm
    print ("Alarm")
    pin_alarm = alarm.pin.PinAlarm(pin=board.D13, value=False, pull=True)

    alarm.exit_and_deep_sleep_until_alarms(pin_alarm)

#if (usealarm) : 
#    print ("Bad")

encoder = rotaryio.IncrementalEncoder(rot_a, rot_b)
button = digitalio.DigitalInOut(board.D9)
# Make the display context
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

count = 0
analog_data= [0]*8

therm = []

now_ms = (time.monotonic_ns() // 1_000_000) & 0xffffffff
print(f"Sending message: count={count} now_ms={now_ms}")



time.sleep(1)
print ("Loop")




print (analog_data)
for i in range (2) :
    can_str = ""
    lastPosition = encoder.position 
    lastButton = button.value
    # for i in range (4):
    #     analog_data[i]=int(therm[i].value/256)
    #     if analog_data[i] < 0:
    #         analog_data[i] = 0
    #     if analog_data[i] > 255 : 
    #         analog_data[i] = 255
    #     can_str = can_str + chr ( analog_data[i])
    #     time.sleep(0.001)
    Rotary_area.text= "{:4.0f}".format(encoder.position)
    print(encoder.position)
    count = 0
    while (count < 1000 and lastButton== button.value and lastPosition == encoder.position):
        #print (message)
        count = count + 1 
        time.sleep(0.01)
    if (not button.value) : 
        text_area.text = "Pressed"
        print ("Pressed")
    else :
        text_area.text = "Not Pressed"
        print ("Not Pressed")

    