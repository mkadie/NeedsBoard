"""Parser for .menu configuration files.

Reads the INI-style .menu format into dictionaries that the
menu engine can use. Designed for CircuitPython (no configparser,
no regex, minimal memory).

File format:
    # comment
    [section_name]
    key = value
"""


def parse_menu_file(filepath):
    """Parse a .menu file into a header dict and list of press items.

    Returns:
        (header, items) where:
            header = dict of [menu] section keys
            items  = list of dicts, one per press item
    """
    header = {}
    items = []
    current_section = None
    current_dict = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue

            # Section header: [name]
            if line.startswith("[") and line.endswith("]"):
                # Save previous item
                if current_section and current_section != "menu" and current_dict:
                    items.append(current_dict)

                current_section = line[1:-1].strip()

                if current_section == "menu":
                    current_dict = header
                else:
                    current_dict = {"id": current_section}
                continue

            # Key = value pair
            if "=" in line and current_dict is not None:
                eq_pos = line.index("=")
                key = line[:eq_pos].strip()
                value = line[eq_pos + 1:].strip()

                # Auto-convert numeric values
                if value.isdigit():
                    value = int(value)
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False

                current_dict[key] = value

    # Don't forget the last section
    if current_section and current_section != "menu" and current_dict:
        items.append(current_dict)

    return header, items


def get_sorted_items(items, sort_by="alpha"):
    """Sort press items for list display.

    Args:
        items: List of item dicts from parse_menu_file.
        sort_by: "alpha" (by label) or "position" (by position key).

    Returns:
        New sorted list.
    """
    if sort_by == "position":
        return sorted(items, key=lambda x: x.get("position", 999))
    # Default: alphabetical by label
    return sorted(items, key=lambda x: x.get("label", "").lower())


def get_grid_items(items, columns, rows):
    """Arrange items into a grid by position number.

    Positions in .menu files are 1-based (1 = top-left) so that
    teachers and parents see familiar numbering. Internally the
    grid list is 0-based.

    Returns:
        List of length (columns * rows), with item dicts at their
        position index and None for empty slots.
    """
    size = columns * rows
    grid = [None] * size
    for item in items:
        pos = item.get("position")
        if pos is not None:
            idx = pos - 1  # Convert 1-based to 0-based
            if 0 <= idx < size:
                grid[idx] = item
    return grid


class MenuStack:
    """Navigation stack for the HyperCard menu metaphor.

    Tracks menu history so "back" returns to the previous menu.
    """

    def __init__(self, menus_dir="/menus", start_menu="base.menu"):
        self._menus_dir = menus_dir
        self._stack = []
        self._current_header = None
        self._current_items = None
        self.load(start_menu)

    def load(self, menu_filename):
        """Load a menu file and push it onto the navigation stack."""
        path = self._menus_dir + "/" + menu_filename
        print("Loading menu:", path)
        header, items = parse_menu_file(path)
        self._stack.append(menu_filename)
        self._current_header = header
        self._current_items = items

    def back(self):
        """Go back to the previous menu. Returns False if already at root."""
        if len(self._stack) <= 1:
            return False
        self._stack.pop()
        prev = self._stack.pop()  # Pop so load() re-pushes it
        self.load(prev)
        return True

    def navigate(self, menu_filename):
        """Navigate to a submenu (push onto stack)."""
        self.load(menu_filename)

    @property
    def header(self):
        """Current menu header dict."""
        return self._current_header

    @property
    def items(self):
        """Current menu items list."""
        return self._current_items

    @property
    def menu_type(self):
        """Current menu type: 'grid', 'list', or 'builder'."""
        return self._current_header.get("type", "grid")

    @property
    def name(self):
        """Current menu display name."""
        return self._current_header.get("name", "Menu")

    @property
    def depth(self):
        """How deep in the navigation stack (1 = root)."""
        return len(self._stack)

    @property
    def current_file(self):
        """Filename of the currently loaded menu."""
        if self._stack:
            return self._stack[-1]
        return None
