# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Pat Satyshur
#
# SPDX-License-Identifier: Unlicense

# Make sure to change the code based on the expander type you are using.

import time
import board
import digitalio

# Change this if you are not using a PCA9555
from i2c_expanders.PCA9555 import PCA9555

# To use default I2C bus (most boards)
i2c = board.I2C()  # uses board.SCL and board.SDA

# Change this to match the address of the device.
PCA9555_Address = 0x20

print (dir(PCA9555))
# Initialize the device and get pins
# Change this if you are not using a PCA9555
IOEXP1_dev = PCA9555(i2c, address=PCA9555_Address)
pin0 = IOEXP1_dev.get_pin(0)
pin1 = IOEXP1_dev.get_pin(1)
pin2 = IOEXP1_dev.get_pin(2)
pin3 = IOEXP1_dev.get_pin(3)

# Pin 0 is an output with an initial value of high (true)
pin0.switch_to_output(value=False)

# Pin 1 is an output with an initial value of low (false)
pin1.switch_to_output(value=True)

# Pin 2 is an input with a pull up resistor and standard polarity
pin2.switch_to_input(invert_polarity=False)

# Pin 3 is an input with a pull down resistor and inverted polarity
pin3.switch_to_input(invert_polarity=False)

# Toggle output pins. Read value from input pins.
while True:
    pin0.value = pin2.value
    pin1.value = pin3.value
    print("pin 0: True")
    print("pin 1: False")
    print("pin 2: ", pin2.value)
    print("pin 3: ", pin3.value)
    time.sleep(1)