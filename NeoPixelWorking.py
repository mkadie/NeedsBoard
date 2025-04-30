import board
import analogio
import adafruit_thermistor
import time
rp2040 = True
if not (rp2040) :
    import canio
import digitalio
import struct

import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import adafruit_ili9341
import adafruit_ST7735r 

import adafruit_24lc32
import rotaryio
import usb_hid
import neopixel

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

#try :
print ("Start")
displayio.release_displays()

Thermister = False
i2cDisplay = True
if (i2cDisplay):
    displayio.release_displays()
    
    WIDTH = 128
    HEIGHT = 32 #64  # Change to 32 if needed
    BORDER = 8
    FONTSCALE = 1

    i2c = board.I2C()
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)
    
    splash = displayio.Group()
    display.root_group = splash

    color_bitmap = displayio.Bitmap(display.width, display.height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(
        display.width - BORDER * 2, display.height - BORDER * 2, 1
    )
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000  # Black
    inner_sprite = displayio.TileGrid(
        inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
    )
    splash.append(inner_sprite)

    # Draw a label
    text = "Hello World!"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
    text_width = text_area.bounding_box[2] * FONTSCALE
    text_group = displayio.Group(
        scale=FONTSCALE,
        x=display.width // 2 - text_width // 2,
        y=display.height // 2,
    )
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

else : 
    spi = board.SPI()
    BoardV5 = True
    if (Thermister):
        tft_cs = board.D9
        tft_dc = board.D10
    elif BoardV5 : 
        tft_cs = board.SCL
        tft_dc = board.TX
        tft_reset = board.SDA
    else : 
        tft_cs = board.A5
        tft_dc = board.TX
        tft_reset = board.A4

    display_bus = displayio.FourWire(
        spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset
    #    spi, command=tft_dc, chip_select=tft_cs, reset=board.D21 
    )
    cheap1_8display = True
    if (cheap1_8display):
        screen_width=160 
        screen_height=128
        screen_scale = 2
        display = adafruit_ST7735r.ST7735R(display_bus, width=screen_width, height=screen_height, rotation = 90) #160, height=128)
    else : 
        screen_width=320 
        screen_height=240
        screen_scale = 3
        display = adafruit_ili9341.ILI9341(display_bus, width=screen_width, height=screen_height)


    print ('Starting')


    splash = displayio.Group()
    display.root_group = splash #circuit python v 9
    #display.show(splash) # circuit python 7-8

    color_bitmap = displayio.Bitmap(screen_width, screen_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White
    text = "FD Can Fiddle"
    TextGroup = displayio.Group(scale=screen_scale, x=0, y= 0 )
    text_area = label.Label(
        terminalio.FONT, text=text, color=0xFFFFFF, x=0, y=30
    )
    TextGroup.append (text_area)
    splash.append(TextGroup)

    Previous_Group = displayio.Group(scale=1, x=0, y= 0 )
    Previous_Area = label.Label(
        terminalio.FONT, text="Rotary", color=0xFFFFFF, x=20, y=20
    )
    Previous_Group.append (Previous_Area)
    splash.append (Previous_Group)

    Next_Group = displayio.Group(scale=1, x=0, y= 0 )
    Next_Area = label.Label(
        terminalio.FONT, text="v1,v2,v3,v4", color=0xFFFFFF, x=20, y=90
    )
    Next_Group.append (Next_Area)
    splash.append (Next_Group)

    Previous2_Group = displayio.Group(scale=1, x=0, y= 0)
    Previous2_Area = label.Label(
        terminalio.FONT, text="Rotary", color=0xFFFFFF, x=20, y=10
    )
    Previous2_Group.append (Previous2_Area)
    splash.append (Previous2_Group)

    Next2_Group = displayio.Group(scale=1, x=0, y= 0 )
    Next2_Area = label.Label(
        terminalio.FONT, text="v1,v2,v3,v4", color=0xFFFFFF, x=20, y=100
    )
    Next2_Group.append (Next2_Area)
    splash.append (Next2_Group)
time.sleep(3)

if (rp2040) :
    encoder = rotaryio.IncrementalEncoder(board.A1, board.A0)
    button = digitalio.DigitalInOut(board.D9)
else:
    encoder = rotaryio.IncrementalEncoder(board.D10, board.D13)
    button = digitalio.DigitalInOut(board.D9)
# Make the display context
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

if not (rp2040) :
    # If the CAN transceiver has a standby pin, bring it out of standby mode
    if hasattr(board, 'CAN_STANDBY'):
        standby = digitalio.DigitalInOut(board.CAN_STANDBY)
        standby.switch_to_output(False)
        print ("Has CAN_Standby")

    # If the CAN transceiver is powered by a boost converter, turn on its supply
    if hasattr(board, 'BOOST_ENABLE'):
        boost_enable = digitalio.DigitalInOut(board.BOOST_ENABLE)
        boost_enable.switch_to_output(True)
        print ("Has CAN_Boost")
    print ("pre can init")
    # Use this line if your board has dedicated CAN pins. (Feather M4 CAN and Feather STM32F405)
    #can = canio.CAN(rx=board.CAN_RX, tx=board.CAN_TX, baudrate=250_000, auto_restart=True)
    # On ESP32S2 most pins can be used for CAN.  Uncomment the following line to use IO5 and IO6
    can = canio.CAN(rx=board.D12, tx=board.D11, baudrate=500_000, auto_restart=True)
    print ("can init")
    old_bus_state = None
count = 0
can_data= [0]*8

print (dir(board))
therm = []
therm.append (analogio.AnalogIn(board.A3))
therm.append (analogio.AnalogIn(board.A2))
#therm.append (analogio.AnalogIn(board.A1))
#therm.append (analogio.AnalogIn(board.A0))

if not (rp2040) :
    bus_state = can.state
    if bus_state != old_bus_state:
        print(f"Bus state changed to {bus_state}")
        old_bus_state = bus_state

now_ms = (time.monotonic_ns() // 1_000_000) & 0xffffffff
print(f"Sending message: count={count} now_ms={now_ms}")

ModeList = ["Electric","Silent Drve", "Max Range", "OMRR Chrg", "Max Exp","Silent Exp","Max Chrg", "Silent Chrg"]

ModeDemo = True
if (ModeDemo):
    encoder.position = 0 #Start in electric drive for now
    lastPosition = encoder.position 
    while (True) :
        curPos = encoder.position
        if (curPos >= len(ModeList)) :
            curPos = 0
        elif (curPos < 0) :
            curPos = len(ModeList)-1

        lastPosition = curPos
        encoder.position = curPos

        if (button.value) :
            text_area.color=0xFFFFFF
        else :
            text_area.color = 0x00FF00

        text_area.text = ModeList[curPos]
        PrevPosition = curPos -1
        if (PrevPosition < 0) : 
            PrevPosition = len(ModeList)-1
        Previous_Area.text = ModeList[PrevPosition]
        NexPos = curPos + 1
        if (NexPos >= len(ModeList)) :
            NexPos = 0
        Next_Area.text = ModeList[NexPos]
        PrevPosition = PrevPosition -1
        if (PrevPosition < 0) : 
            PrevPosition = len(ModeList)-1
        Previous2_Area.text = ModeList[PrevPosition]
        NexPos = NexPos + 1
        if (NexPos >= len(ModeList)) :
            NexPos = 0
        Next2_Area.text = ModeList[NexPos]
        while (encoder.position == lastPosition and button.value) : 
            text_area.color=0xFFFFFF
            time.sleep(0.001)
        #time.sleep(0.1)
        

USE_AS_VOLUME = False
if USE_AS_VOLUME:
    # USB device
    consumer = ConsumerControl(usb_hid.devices)   
    VolumeOnMachine = None
    for i in range (50):
        consumer.send(ConsumerControlCode.VOLUME_DECREMENT)

    LastVolumePos = 0
    VolumeOnMachine = 0 
    while (button.value):
        CurVolume = 0
        for i in range (5):
            CurVolume += (therm[0].value/128)
            time.sleep(0.001)
        volumeChange = LastVolumePos-CurVolume
        LastVolumePos = CurVolume
        if (abs(volumeChange)>20) : 
            TargetVolume = 50-int(((CurVolume*50)/512)/5)
            while (not (VolumeOnMachine ==TargetVolume)) : 
                if (VolumeOnMachine > TargetVolume):
                    consumer.send(ConsumerControlCode.VOLUME_DECREMENT)
                    VolumeOnMachine -= 1
                else:
                    consumer.send(ConsumerControlCode.VOLUME_INCREMENT)   
                    VolumeOnMachine +=1
                time.sleep(0.001) 

print (can_data)
while (True) : #for i in range (100) :
    can_str = ""
    lastPosition = encoder.position 
    lastButton = button.value
    for i in range (4):
        can_data[i]=int(therm[i].value/256)
        if can_data[i] < 0:
            can_data[i] = 0
        if can_data[i] > 255 : 
            can_data[i] = 255
        can_str = can_str + chr ( can_data[i])
        time.sleep(0.001)
    if lastPosition >= 0 and lastPosition < 256: 
        can_data[4] = lastPosition
    else : 
        can_data[4] = 0
    if lastButton : #inverted
        can_data[5] = 0
    else : 
        can_data[5] = 1
        
    print (max(can_data))
    Previous_Area.text= "{:4.0f}".format(encoder.position)
    can_str = can_str +"xxxx"
    Volt_Group.text = "{:3d},{:3d},{:3d},{:3d}\n{:3d},{:3d}".format(can_data[0], can_data[1], can_data[2], can_data[3], can_data[4], can_data[5])
    print (can_data)
    print (can_str)
    stupid_temp = struct.pack("<BBBBBB", can_data[0],can_data[1],can_data[2],can_data[3], can_data[4], can_data[5])
    print (stupid_temp)

    if not (rp2040) :
        message = canio.Message(id=0x410, data=stupid_temp)#(can_str)) #struct.pack(can_str,8))
        can.send(message)
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
