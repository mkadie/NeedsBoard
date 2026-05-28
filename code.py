"""AAC Communication Device — main entry point."""

import time
import gc


def _warm_flash():
    try:
        import es8311
    except ImportError:
        es8311 = None
    from adafruit_display_text import label
    from stim_games import subprogram, multi_lingual, game_config
    _ = (es8311, label, subprogram, multi_lingual, game_config)


gc.collect()
_warm_flash()
from machine import Machine
app = Machine()
app.run()
