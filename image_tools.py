"""Image scaling and conversion tools for AAC device.

Works on PC (PIL/Pillow) and can be adapted for embedded (displayio/bitmaptools).
Converts source images to BMP at target resolutions, preserving directory structure.

PC usage:
    from image_tools import ImageScaler
    scaler = ImageScaler(160, 128)
    scaler.convert_tree("master_images", "image_160x128")

CLI usage:
    python image_tools.py master_images 160 128
    python image_tools.py master_images 320 240
"""

import os
import sys

# Detect environment
try:
    from PIL import Image
    PLATFORM = "pc"
except ImportError:
    try:
        import displayio
        import bitmaptools
        PLATFORM = "embedded"
    except ImportError:
        PLATFORM = None


class ImageScaler:
    """Scale and convert images to BMP at a target resolution.

    Handles two image types based on filename:
      - Board/background images (*_board* or *board*): scale to exact target size
      - Button/cell images: scale proportionally to fit target resolution ratio
    """

    def __init__(self, target_width, target_height,
                 source_width=320, source_height=240):
        self.target_width = target_width
        self.target_height = target_height
        self.source_width = source_width
        self.source_height = source_height
        self.scale_x = target_width / source_width
        self.scale_y = target_height / source_height

    def is_board_image(self, filename):
        """Check if this is a full-screen background/board image."""
        name = os.path.basename(filename).lower()
        return "board" in name or "background" in name or "bg" in name

    def target_size(self, src_width, src_height, filename):
        """Calculate target dimensions for an image.

        Board images scale to exact target resolution.
        Other images scale proportionally.
        """
        if self.is_board_image(filename):
            return (self.target_width, self.target_height)

        new_w = max(1, round(src_width * self.scale_x))
        new_h = max(1, round(src_height * self.scale_y))
        return (new_w, new_h)

    def convert_file(self, src_path, dst_path):
        """Convert a single image file to BMP at the target size.

        Returns True on success, False on skip/error.
        """
        if PLATFORM == "pc":
            return self._convert_pc(src_path, dst_path)
        elif PLATFORM == "embedded":
            return self._convert_embedded(src_path, dst_path)
        else:
            print("No image library available")
            return False

    def _convert_pc(self, src_path, dst_path):
        """Convert using PIL on PC."""
        try:
            img = Image.open(src_path)
            w, h = img.size
            tw, th = self.target_size(w, h, src_path)

            if img.mode == "P":
                img = img.convert("RGB")
            elif img.mode == "RGBA":
                bg = Image.new("RGB", img.size, (0, 0, 0))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            if (w, h) != (tw, th):
                img = img.resize((tw, th), Image.LANCZOS)

            # Save as 16-bit BMP (RGB565) for embedded compatibility
            # PIL doesn't directly support RGB565 BMP, so save as 24-bit
            # which CircuitPython's OnDiskBitmap can read
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            img.save(dst_path, "BMP")
            print("  {} -> {} ({}x{})".format(
                os.path.basename(src_path), os.path.basename(dst_path), tw, th))
            return True
        except Exception as e:
            print("  ERROR {}: {}".format(src_path, e))
            return False

    def _convert_embedded(self, src_path, dst_path):
        """Convert using displayio/bitmaptools on embedded device.

        Limited: only handles BMP->BMP scaling via rotozoom.
        Slow but functional for on-device conversion.
        """
        try:
            import gc
            gc.collect()

            src_bmp = displayio.OnDiskBitmap(src_path)
            w, h = src_bmp.width, src_bmp.height
            tw, th = self.target_size(w, h, src_path)

            sx = tw / w
            sy = th / h

            dst_bmp = displayio.Bitmap(tw, th, 65536)
            bitmaptools.rotozoom(
                dst_bmp, src_bmp,
                scale=min(sx, sy),
                ox=tw // 2, oy=th // 2,
            )

            # Save BMP — embedded save is limited, may need custom writer
            # For now, mark as needing PC conversion
            print("  Embedded scaling: {}x{} (limited)".format(tw, th))
            return False  # Full save not yet implemented for embedded
        except Exception as e:
            print("  Embedded ERROR: {}".format(e))
            return False

    def convert_tree(self, src_dir, dst_dir, extensions=None):
        """Convert all images in src_dir tree to dst_dir, preserving structure.

        Args:
            src_dir: Source directory with original images.
            dst_dir: Destination directory for scaled images.
            extensions: Set of extensions to process. Default: common image types.

        Returns:
            Tuple of (converted_count, skipped_count, error_count).
        """
        if extensions is None:
            extensions = {".bmp", ".png", ".jpg", ".jpeg", ".gif", ".tiff"}

        converted = 0
        skipped = 0
        errors = 0

        for root, dirs, files in os.walk(src_dir):
            # Calculate relative path for output
            rel = os.path.relpath(root, src_dir)
            out_dir = os.path.join(dst_dir, rel) if rel != "." else dst_dir

            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in extensions:
                    skipped += 1
                    continue

                src_path = os.path.join(root, fname)
                # Always output as .bmp
                dst_name = os.path.splitext(fname)[0] + ".bmp"
                dst_path = os.path.join(out_dir, dst_name)

                if self._convert_pc(src_path, dst_path) if PLATFORM == "pc" \
                        else self.convert_file(src_path, dst_path):
                    converted += 1
                else:
                    errors += 1

        return (converted, skipped, errors)

    def generate_placeholder(self, width, height, color, text, dst_path):
        """Generate a solid-color placeholder BMP with centered text.

        PC only. Useful for creating initial board/button images.
        """
        if PLATFORM != "pc":
            print("Placeholder generation requires PC (PIL)")
            return False

        try:
            img = Image.new("RGB", (width, height), color)

            # Try to add text
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                # Use default font, centered
                bbox = draw.textbbox((0, 0), text)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x = (width - tw) // 2
                y = (height - th) // 2
                # Pick contrasting text color
                brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
                text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)
                draw.text((x, y), text, fill=text_color)
            except ImportError:
                pass  # No ImageDraw, just solid color

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            img.save(dst_path, "BMP")
            print("  Placeholder: {} ({}x{})".format(
                os.path.basename(dst_path), width, height))
            return True
        except Exception as e:
            print("  ERROR generating placeholder: {}".format(e))
            return False


def main():
    """CLI: python image_tools.py <source_dir> <width> <height> [dest_dir]"""
    if len(sys.argv) < 4:
        print("Usage: python image_tools.py <source_dir> <width> <height> [dest_dir]")
        print("  dest_dir defaults to image_<width>x<height>")
        sys.exit(1)

    src_dir = sys.argv[1]
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    dst_dir = sys.argv[4] if len(sys.argv) > 4 else "image_{}x{}".format(width, height)

    if not os.path.isdir(src_dir):
        print("Source directory not found:", src_dir)
        sys.exit(1)

    print("Converting images: {} -> {} ({}x{})".format(src_dir, dst_dir, width, height))
    scaler = ImageScaler(width, height)
    converted, skipped, errors = scaler.convert_tree(src_dir, dst_dir)
    print("\nDone: {} converted, {} skipped, {} errors".format(
        converted, skipped, errors))


if __name__ == "__main__":
    main()
