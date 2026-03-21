"""Quick test: flash FULL_POWER (A4) on Fruit Jam.
A4 HIGH = 3V3_Switched OFF, A4 LOW = 3V3_Switched ON.
Cycles: 5s on, 2s off, repeat.
"""

import board
import digitalio
import time

pin = digitalio.DigitalInOut(board.A4)
pin.direction = digitalio.Direction.OUTPUT

print("FULL_POWER flash test — 5s on, 2s off")
while True:
    pin.value = False  # ON
    print("ON")
    time.sleep(5)
    pin.value = True   # OFF
    print("OFF")
    time.sleep(2)
