"""Storage management for AAC device.

Handles SD card mounting, SPI bus sharing, file path resolution
(SD card first, flash fallback), and bidirectional file sync.
"""

import os
import time
import board
import busio


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class StorageManager:
    """Manages SD card and file path resolution.

    Files on the SD card override same-path files on flash.
    Code always runs from flash; content (menus, sounds, images)
    can live on either.
    """

    def __init__(self, config):
        """Initialize storage, optionally mounting SD card.

        Args:
            config: Hardware config dictionary with sd_* keys.
        """
        self._sd_mounted = False
        self._sd_files = set()
        self._spi = None
        self._config = config

        if config.get("sd_card", False):
            self._try_mount_sd(config)
        else:
            print("Storage: no SD card configured")

    def _try_mount_sd(self, config):
        """Attempt to mount the SD card. Fail silently if not present."""
        import sdcardio
        import storage

        try:
            # Release any displayio-held SPI bus from a previous run
            # (critical when SD and display share the same SPI pins)
            if config.get("sd_shares_display_spi", False):
                import displayio
                displayio.release_displays()

            # Create SPI bus (shared with display if sd_shares_display_spi)
            self._spi = busio.SPI(
                _pin(config["sd_sclk"]),
                MOSI=_pin(config["sd_mosi"]),
                MISO=_pin(config["sd_miso"]),
            )

            sd = sdcardio.SDCard(self._spi, _pin(config["sd_cs"]))
            vfs = storage.VfsFat(sd)
            storage.mount(vfs, "/sd")
            self._sd_mounted = True
            print("Storage: SD card mounted at /sd")

            # Scan SD card contents for fast path resolution
            self._scan_sd()

        except Exception as e:
            print("Storage: SD card not available ({})".format(e))
            self._sd_mounted = False

    def _scan_sd(self):
        """Scan relevant SD card directories and build a path lookup set.

        Only scans content directories (menus, button_sounds) and root
        content files — not the entire card (which may have hundreds of
        unrelated files like CircuitPython libraries).
        """
        self._sd_files.clear()
        count = 0
        # Scan content directories (menus, sounds, button_sounds)
        for d in ["/sd/menus", "/sd/button_sounds", "/sd/sounds"]:
            count += self._scan_dir(d)
        # Scan root-level content files (bmp, mp3, menu)
        try:
            for f in os.listdir("/sd"):
                lower = f.lower()
                if (lower.endswith(".bmp") or lower.endswith(".mp3")
                        or lower.endswith(".wav") or lower.endswith(".menu")):
                    self._sd_files.add("/sd/" + f)
                    count += 1
        except OSError:
            pass
        print("Storage: {} content files indexed on SD".format(count))

    def _scan_dir(self, path):
        """Recursively scan a directory, adding file paths to _sd_files."""
        count = 0
        try:
            for entry in os.listdir(path):
                full = path + "/" + entry
                try:
                    # Try to listdir — if it works, it's a directory
                    os.listdir(full)
                    count += self._scan_dir(full)
                except OSError:
                    # It's a file
                    self._sd_files.add(full)
                    count += 1
        except OSError:
            pass
        return count

    def resolve_path(self, path):
        """Resolve a path: check SD card first, fall back to flash.

        Args:
            path: Absolute path (e.g., "/menus/food.menu").

        Returns:
            "/sd/menus/food.menu" if it exists on SD, else the original path.
        """
        if not self._sd_mounted or not path:
            return path
        sd_path = "/sd" + path
        if sd_path in self._sd_files:
            return sd_path
        return path

    def rescan(self):
        """Re-scan the SD card (call after files are added/removed)."""
        if self._sd_mounted:
            self._scan_sd()

    @property
    def spi(self):
        """Shared SPI bus instance (for display_manager to reuse)."""
        return self._spi

    @property
    def sd_available(self):
        """True if SD card is mounted and accessible."""
        return self._sd_mounted

    # ------------------------------------------------------------------
    # Bidirectional sync
    # ------------------------------------------------------------------

    def sync_flash_to_sd(self, dirs=None):
        """Copy content from flash to SD card.

        Use this to populate a new/blank SD card with the current
        device configuration. Only copies files that don't already
        exist on the SD card (won't overwrite).

        Args:
            dirs: List of directories to sync (default: menus, button_sounds).

        Returns:
            Number of files copied.
        """
        if not self._sd_mounted:
            print("Sync: SD card not available")
            return 0

        if dirs is None:
            dirs = ["/menus", "/button_sounds"]

        copied = 0
        for src_dir in dirs:
            try:
                os.listdir(src_dir)
            except OSError:
                continue
            copied += self._copy_tree(src_dir, "/sd" + src_dir, overwrite=False)

        # Also copy root-level content files
        for f in self._list_content_files("/"):
            src = "/" + f
            dst = "/sd/" + f
            if dst not in self._sd_files:
                self._copy_file(src, dst)
                copied += 1

        if copied > 0:
            self._scan_sd()  # Refresh index
        print("Sync: flash→SD copied {} files".format(copied))
        return copied

    def process_move_to_sd(self):
        """Move files from /move_to_sd/ on flash to SD card.

        Files in /move_to_sd/ are copied to /sd/ maintaining their
        directory structure, then deleted from flash to free space.
        This allows deploying large content (language packs) via USB
        that gets transferred to SD on next boot.

        Example: /move_to_sd/button_sounds/languages/ja/milk.wav
              -> /sd/button_sounds/languages/ja/milk.wav
              -> flash file deleted after successful copy
        """
        if not self._sd_mounted:
            return 0

        staging = "/move_to_sd"
        try:
            os.listdir(staging)
        except OSError:
            return 0  # No staging directory

        print("move_to_sd: processing...")
        moved = self._move_tree(staging, "/sd")

        # Remove the empty staging directory
        self._remove_empty_dirs(staging)
        try:
            os.rmdir(staging)
        except OSError:
            pass

        if moved > 0:
            self._scan_sd()  # Refresh SD index
        print("move_to_sd: {} files moved to SD".format(moved))
        return moved

    def _move_tree(self, src_dir, dst_dir):
        """Recursively copy files from src to dst, deleting src after copy."""
        moved = 0
        self._ensure_dir(dst_dir)

        try:
            entries = os.listdir(src_dir)
        except OSError:
            return 0

        for entry in entries:
            src = src_dir + "/" + entry
            dst = dst_dir + "/" + entry

            try:
                os.listdir(src)
                # Directory — recurse
                moved += self._move_tree(src, dst)
            except OSError:
                # File — copy to SD (delete from flash if possible)
                self._copy_file(src, dst)
                moved += 1
                try:
                    os.remove(src)
                except OSError:
                    pass  # Flash is read-only at runtime — OK

        return moved

    def _remove_empty_dirs(self, path):
        """Remove empty directories recursively (bottom-up)."""
        try:
            entries = os.listdir(path)
        except OSError:
            return
        for entry in entries:
            child = path + "/" + entry
            try:
                os.listdir(child)
                self._remove_empty_dirs(child)
                try:
                    os.rmdir(child)
                except OSError:
                    pass
            except OSError:
                pass

    def sync_sd_to_flash(self, dirs=None):
        """Copy content from SD card to flash.

        Use this to apply updates from an SD card (e.g., someone
        sends new menus/sounds on an SD card). Only copies files
        that are newer or don't exist on flash.

        Args:
            dirs: List of directories to sync (default: menus, button_sounds).

        Returns:
            Number of files copied.
        """
        if not self._sd_mounted:
            print("Sync: SD card not available")
            return 0

        if dirs is None:
            dirs = ["/menus", "/button_sounds"]

        copied = 0
        for src_dir in dirs:
            sd_dir = "/sd" + src_dir
            try:
                os.listdir(sd_dir)
            except OSError:
                continue
            copied += self._copy_tree(sd_dir, src_dir, overwrite=True)

        if copied > 0:
            print("Sync: SD→flash copied {} files".format(copied))
        else:
            print("Sync: SD→flash nothing to copy")
        return copied

    def _copy_tree(self, src_dir, dst_dir, overwrite=False):
        """Recursively copy a directory tree."""
        copied = 0
        self._ensure_dir(dst_dir)

        try:
            entries = os.listdir(src_dir)
        except OSError:
            return 0

        for entry in entries:
            src = src_dir + "/" + entry
            dst = dst_dir + "/" + entry

            try:
                os.listdir(src)
                # It's a directory — recurse
                copied += self._copy_tree(src, dst, overwrite)
            except OSError:
                # It's a file
                if overwrite or not self._file_exists(dst):
                    self._copy_file(src, dst)
                    copied += 1

        return copied

    def _copy_file(self, src, dst):
        """Copy a single file."""
        self._ensure_dir(self._dirname(dst))
        try:
            with open(src, "rb") as sf:
                with open(dst, "wb") as df:
                    while True:
                        chunk = sf.read(4096)
                        if not chunk:
                            break
                        df.write(chunk)
            print("  Copied:", src, "->", dst)
        except Exception as e:
            print("  Copy failed:", src, "->", dst, e)

    def _file_exists(self, path):
        """Check if a file exists."""
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    def _ensure_dir(self, path):
        """Create directory and parents if they don't exist."""
        if not path or path == "/":
            return
        parts = path.strip("/").split("/")
        current = ""
        for part in parts:
            current += "/" + part
            try:
                os.listdir(current)
            except OSError:
                try:
                    os.mkdir(current)
                except OSError:
                    pass

    def _dirname(self, path):
        """Return the directory portion of a path."""
        idx = path.rfind("/")
        if idx <= 0:
            return "/"
        return path[:idx]

    def _list_content_files(self, directory):
        """List content files (bmp, mp3) in a directory (non-recursive)."""
        content = []
        try:
            for f in os.listdir(directory):
                lower = f.lower()
                if lower.endswith(".bmp") or lower.endswith(".mp3"):
                    content.append(f)
        except OSError:
            pass
        return content
