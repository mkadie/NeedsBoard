"""Verify every asset a menu references actually exists before deploying.

This exists because a missing sound is invisible on the device: action.py
catches the error and audio_player.py catches it again, so a broken cell
prints to a serial console nobody is watching and is otherwise identical to
working hardware that happens to be quiet. Every item in the Food/Drink
submenu was silent for exactly this reason -- deploy.sh never copied
menus/sounds/ -- and nothing anywhere noticed.

Paths resolve the way action.py::_resolve_path does at runtime: a leading
"/" is the device root (the repo root here), anything else is relative to
menus/.

Usage:
    python3 check_menus.py                 # walk base_fruitjam.menu + submenus
    python3 check_menus.py base.menu       # walk a different start menu
    python3 check_menus.py --all           # every menus/*.menu
    python3 check_menus.py --root installer/content   # check a shipped copy
"""

import glob
import os
import re
import sys

DEFAULT_START = "base_fruitjam.menu"
ASSET_KEYS = ("image", "sound", "background")


def refs(menu_path, key):
    """Every `key = value` value in a menu file, in file order."""
    txt = open(menu_path).read()
    return re.findall(r"^%s\s*=\s*(\S+)" % key, txt, re.M)


def resolve(root, value):
    """Menu reference -> filesystem path, mirroring action.py::_resolve_path."""
    if value.startswith("/"):
        return os.path.join(root, value.lstrip("/"))
    return os.path.join(root, "menus", value)


def walk(root, start, seen, problems):
    """Check `start` and follow its submenus, depth first."""
    if start in seen:
        return
    seen.add(start)

    path = os.path.join(root, "menus", start)
    if not os.path.exists(path):
        problems.append((start, "menu file not found", path))
        return

    for key in ASSET_KEYS:
        for value in refs(path, key):
            target = resolve(root, value)
            if not os.path.exists(target):
                problems.append((start, key, value))

    for value in refs(path, "submenu"):
        walk(root, value, seen, problems)


def main(argv):
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]

    if "--all" in argv:
        argv.remove("--all")
        starts = sorted(os.path.basename(p)
                        for p in glob.glob(os.path.join(root, "menus", "*.menu")))
    else:
        starts = argv[1:] or [DEFAULT_START]

    seen, problems = set(), []
    for start in starts:
        walk(root, start, seen, problems)

    print("Checked {} menu(s) under {}: {}".format(
        len(seen), os.path.normpath(root), ", ".join(sorted(seen))))

    if problems:
        print("\nMissing references:")
        for menu, key, value in problems:
            print("  {:24s} {:10s} {}".format(menu, key, value))
        print("\n{} missing reference(s).".format(len(problems)))
        return 1

    unchecked = sorted(
        os.path.basename(p)
        for p in glob.glob(os.path.join(root, "menus", "*.menu"))
        if os.path.basename(p) not in seen)
    if unchecked:
        print("Not reached from these start menus: " + ", ".join(unchecked))
    print("All referenced assets present.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
