"""Static keyboard, preset, and layout definitions."""

import os

VENDOR = 0x046d
CONFIG = os.path.expanduser("~/.config/g213tray.json")
LANGUAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "languages.json")

KEYBOARDS = {
    "g213": {
        "name": "Logitech G213",
        "product_ids": (0xc336,),
        "packet_prefix": (0x0c, 0x3a),
        "per_key": False,
    },
    "g512": {
        "name": "Logitech G512",
        "product_ids": (0xc342, 0xc33c),
        "packet_prefix": (0x0d, 0x3c),
        "key_packet_prefix": (0x12, 0xff, 0x0c, 0x3a, 0x00, 0x01, 0x00, 0x0e),
        "per_key": True,
    },
}

PRESETS = [
    ("White", 0xff, 0xff, 0xff),
    ("Red", 0xff, 0x00, 0x00),
    ("Green", 0x00, 0xff, 0x00),
    ("Blue", 0x00, 0x00, 0xff),
    ("Purple", 0x80, 0x00, 0xff),
    ("Orange", 0xff, 0x60, 0x00),
    ("Cyan", 0x00, 0xff, 0xff),
]

KEYS = {
    "A": 0x04, "B": 0x05, "C": 0x06, "D": 0x07, "E": 0x08,
    "F": 0x09, "G": 0x0a, "H": 0x0b, "I": 0x0c, "J": 0x0d,
    "K": 0x0e, "L": 0x0f, "M": 0x10, "N": 0x11, "O": 0x12,
    "P": 0x13, "Q": 0x14, "R": 0x15, "S": 0x16, "T": 0x17,
    "U": 0x18, "V": 0x19, "W": 0x1a, "X": 0x1b, "Y": 0x1c,
    "Z": 0x1d,
    "1": 0x1e, "2": 0x1f, "3": 0x20, "4": 0x21, "5": 0x22,
    "6": 0x23, "7": 0x24, "8": 0x25, "9": 0x26, "0": 0x27,
    "Enter": 0x28, "Esc": 0x29, "Backspace": 0x2a, "Tab": 0x2b,
    "Space": 0x2c, "-": 0x2d, "=": 0x2e, "[": 0x2f, "]": 0x30,
    "\\": 0x31, ";": 0x33, "'": 0x34, "`": 0x35, ",": 0x36,
    ".": 0x37, "/": 0x38, "Caps Lock": 0x39,
    "F1": 0x3a, "F2": 0x3b, "F3": 0x3c, "F4": 0x3d, "F5": 0x3e,
    "F6": 0x3f, "F7": 0x40, "F8": 0x41, "F9": 0x42, "F10": 0x43,
    "F11": 0x44, "F12": 0x45,
    "Print Screen": 0x46, "Scroll Lock": 0x47, "Pause": 0x48,
    "Insert": 0x49, "Home": 0x4a, "Page Up": 0x4b, "Delete": 0x4c,
    "End": 0x4d, "Page Down": 0x4e,
    "Right": 0x4f, "Left": 0x50, "Down": 0x51, "Up": 0x52,
    "Num Lock": 0x53, "Num /": 0x54, "Num *": 0x55, "Num -": 0x56,
    "Num +": 0x57, "Num Enter": 0x58, "Num 1": 0x59, "Num 2": 0x5a,
    "Num 3": 0x5b, "Num 4": 0x5c, "Num 5": 0x5d, "Num 6": 0x5e,
    "Num 7": 0x5f, "Num 8": 0x60, "Num 9": 0x61, "Num 0": 0x62,
    "Num .": 0x63,
    "Ctrl": 0xe0, "Shift": 0xe1, "Alt": 0xe2, "Super": 0xe3,
    "Right Alt": 0xe4, "Right Super": 0xe5, "Right Ctrl": 0xe6,
    "Right Shift": 0xe7, "Menu": 0x65,
}

KEY_GROUPS = {
    "wasd": ("W", "A", "S", "D"),
    "arrows": ("Up", "Left", "Down", "Right"),
    "fkeys": tuple(f"F{i}" for i in range(1, 13)),
    "navigation": ("Insert", "Home", "Page Up", "Delete", "End", "Page Down"),
    "modifiers": ("Ctrl", "Shift", "Alt", "Super", "Right Alt", "Right Super",
                  "Right Ctrl", "Right Shift", "Menu"),
    "numpad": ("Num Lock", "Num /", "Num *", "Num -", "Num +", "Num Enter",
               "Num 1", "Num 2", "Num 3", "Num 4", "Num 5", "Num 6",
               "Num 7", "Num 8", "Num 9", "Num 0", "Num ."),
}

KEY_DISPLAY_LABELS = {
    "Print Screen": "PrtSc", "Scroll Lock": "ScrLk", "Pause": "Pause",
    "Page Up": "PgUp", "Page Down": "PgDn", "Insert": "Ins",
    "Delete": "Del", "Backspace": "Bksp", "Caps Lock": "Caps",
    "Left": "◀", "Right": "▶", "Up": "▲", "Down": "▼",
    "Num Lock": "Num", "Num /": "/", "Num *": "*", "Num -": "-",
    "Num +": "+", "Num Enter": "Enter", "Num .": ".",
    "Num 0": "0", "Num 1": "1", "Num 2": "2", "Num 3": "3",
    "Num 4": "4", "Num 5": "5", "Num 6": "6", "Num 7": "7",
    "Num 8": "8", "Num 9": "9", "Super": "Win", "Right Super": "Win",
    "Right Alt": "AltGr", "Right Ctrl": "Ctrl", "Right Shift": "Shift",
}

KEYBOARD_LAYOUT = [
    [("Esc", 4), (None, 4), ("F1", 4), ("F2", 4), ("F3", 4), ("F4", 4),
     (None, 2), ("F5", 4), ("F6", 4), ("F7", 4), ("F8", 4), (None, 2),
     ("F9", 4), ("F10", 4), ("F11", 4), ("F12", 4), (None, 2),
     ("Print Screen", 4), ("Scroll Lock", 4), ("Pause", 4), (None, 2),
     (None, 16)],
    [("`", 4), ("1", 4), ("2", 4), ("3", 4), ("4", 4), ("5", 4),
     ("6", 4), ("7", 4), ("8", 4), ("9", 4), ("0", 4), ("-", 4),
     ("=", 4), ("Backspace", 8), (None, 2), ("Insert", 4), ("Home", 4),
     ("Page Up", 4), (None, 2), ("Num Lock", 4), ("Num /", 4),
     ("Num *", 4), ("Num -", 4)],
    [("Tab", 6), ("Q", 4), ("W", 4), ("E", 4), ("R", 4), ("T", 4),
     ("Y", 4), ("U", 4), ("I", 4), ("O", 4), ("P", 4), ("[", 4),
     ("]", 4), ("\\", 6), (None, 2), ("Delete", 4), ("End", 4),
     ("Page Down", 4), (None, 2), ("Num 7", 4), ("Num 8", 4),
     ("Num 9", 4), ("Num +", 4, 2)],
    [("Caps Lock", 7), ("A", 4), ("S", 4), ("D", 4), ("F", 4),
     ("G", 4), ("H", 4), ("J", 4), ("K", 4), ("L", 4), (";", 4),
     ("'", 4), ("Enter", 9), (None, 2), (None, 12), (None, 2),
     ("Num 4", 4), ("Num 5", 4), ("Num 6", 4)],
    [("Shift", 9), ("Z", 4), ("X", 4), ("C", 4), ("V", 4), ("B", 4),
     ("N", 4), ("M", 4), (",", 4), (".", 4), ("/", 4),
     ("Right Shift", 11), (None, 2), (None, 4), ("Up", 4), (None, 4),
     (None, 2), ("Num 1", 4), ("Num 2", 4), ("Num 3", 4),
     ("Num Enter", 4, 2)],
    [("Ctrl", 5), ("Super", 5), ("Alt", 5), ("Space", 25),
     ("Right Alt", 5), ("Right Super", 5), ("Menu", 5), ("Right Ctrl", 5),
     (None, 2), ("Left", 4), ("Down", 4), ("Right", 4), (None, 2),
     ("Num 0", 8), ("Num .", 4)],
]
