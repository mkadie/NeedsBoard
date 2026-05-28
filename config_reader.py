# ---------------------------------------------------------------------------
# Modified file — originally from T-Rex Talker (https://github.com/mkadie).
#
# Upstream license: MIT.
#     Copyright (c) T-Rex Talker contributors. All rights reserved under MIT.
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of the upstream software and associated documentation files,
#     to deal in the Software without restriction, subject to the conditions
#     in the upstream LICENSE file. See ../NOTICE for the full MIT text.
#
# Modifications in this file were added as part of T-Rex Talker Interactive
# and are licensed under the PolyForm Noncommercial License 1.0.0.
# See ../LICENSE for terms and ../upstream_patches/README.md for what changed.
# ---------------------------------------------------------------------------
"""Read user configuration from config.txt.

Parses a simple key=value text file and overlays values onto
the hardware config dict. This lets users customize behavior
without editing hardware_config.py.
"""


def _parse_value(raw):
    """Convert a string value to the appropriate Python type."""
    val = raw.strip()
    lower = val.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def load_config(path="/config.txt"):
    """Load config.txt and return a dict of key-value pairs.

    Returns an empty dict if the file doesn't exist.
    """
    config = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                config[key.strip()] = _parse_value(val)
    except OSError:
        pass
    return config


def apply_config(hw_config, user_config):
    """Overlay user config values onto hardware config dict.

    Only applies keys that are recognized user-configurable settings.
    Returns the modified hw_config.
    """
    allowed = {
        "sleep_enabled",
        "sleep_timeout",
        "volume",
        "playback_speed",
        "debounce_time",
        "encoder_direction_flip",
        "rotary_encoder",
        "encoder_navigation",
        "play_on_release",
        "show_border",
        "display_hint_text",
        "zoom_image_enabled",
        "start_menu",
        "emergency_push_enabled",
        "emergency_push_sound",
        "emergency_hold_enabled",
        "emergency_hold_seconds",
        # Subprogram boot — "mode = stim_games/aac_trainer.py" tells the
        # Machine to launch that subprogram after hardware init instead
        # of (or in addition to) showing the start_menu. When the
        # subprogram exits, control falls through to the menu loop.
        "mode",
    }

    for key, val in user_config.items():
        if key in allowed:
            hw_config[key] = val

    return hw_config
