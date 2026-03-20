"""AAC Communication Device — main entry point.

Change the machine variant in hardware_config.py (DEFAULT_VARIANT)
or pass it directly: Machine("CYD_PLUS") or Machine("TALKER_PICO2").
"""

from machine import Machine

app = Machine()
app.run()
