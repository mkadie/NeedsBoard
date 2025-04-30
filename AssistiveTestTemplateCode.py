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

reset_LED_pin = board.D24

reset_LED = digitalio.DigitalInOut(reset_LED_pin)
# Make the display context
reset_LED.direction = digitalio.Direction.OUTPUT
reset_LED.value = True

use_button_board = True
if use_button_board : 
    pixel = neopixel.NeoPixel(Neopixel_pin, 16)    
    #pixel = neopixel.NeoPixel(Neopixel_pin, 32)    : 2 button boards
else : 
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

pixel.brightness = 0.3
pixel[1] = (100,10,10)
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
#audio.stop()
with open("Trampoline.wav", "rb") as wave_file:
    wav = audiocore.WaveFile(wave_file)

    print("Playing wav file!")
    time.sleep(2)
    audio.play(wav)
    while audio.playing:
        pass
#try :
pixel.fill((0, 0, 0))


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
display = adafruit_ili9341.ILI9341(display_bus, width=screen_width, height=screen_height)


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
    board.I2C().deinit()
    i2c = board.I2C()
    tft_io_expander = dict(board.TFT_IO_EXPANDER)

    pcf = adafruit_pca9554.PCA9554(i2c, address=tft_io_expander['i2c_address'])
    button_up = pcf.get_pin(board.BTN_UP)
    button_up.switch_to_input(pull=digitalio.Pull.UP)

    while True:
        print(button_up.value)
        time.sleep(0.01)  # debounce


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

splash = displayio.Group()
display.root_group = splash #circuit python v 9
#display.show(splash) # circuit python 7-8

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

with open("StreetChicken.wav", "rb") as wave_file:
    wav = audiocore.WaveFile(wave_file)

    print("Playing wav file!")
    audio.play(wav)
    while audio.playing:
        pass

print("Done!")



print (analog_data)
while (True) : #for i in range (100) :
    can_str = ""
    lastPosition = encoder.position 
    lastButton = button.value
    for i in range (4):
        analog_data[i]=int(therm[i].value/256)
        if analog_data[i] < 0:
            analog_data[i] = 0
        if analog_data[i] > 255 : 
            analog_data[i] = 255
        can_str = can_str + chr ( analog_data[i])
        time.sleep(0.001)
    if lastPosition >= 0 and lastPosition < 256: 
        analog_data[4] = lastPosition
    else : 
        analog_data[4] = 0
    if lastButton : #inverted
        analog_data[5] = 0
    else : 
        analog_data[5] = 1
        
    print (max(analog_data))
    Rotary_area.text= "{:4.0f}".format(encoder.position)
    can_str = can_str +"xxxx"
    Volt_area.text = "{:3d},{:3d},{:3d},{:3d}\n{:3d},{:3d}".format(analog_data[0], analog_data[1], analog_data[2], analog_data[3], analog_data[4], analog_data[5])
    print (analog_data)
    print (can_str)
    stupid_temp = struct.pack("<BBBBBB", analog_data[0],analog_data[1],analog_data[2],analog_data[3], analog_data[4], analog_data[5])
    print (stupid_temp)

    print(encoder.position)
    count = 0
    while (count < 100 and lastButton== button.value and lastPosition == encoder.position):
        #print (message)
        count = count + 1 
        time.sleep(0.01)
    if (not button.value) : 
        text_area.text = "Pressed"
    else :
        text_area.text = "Not Pressed"
