#!/usr/bin/env python3
"""G213 keyboard lighting control — KDE system tray."""
import sys
import json
import os
import locale
import usb.core
import usb.util
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu,
                              QColorDialog, QDialog, QDialogButtonBox,
                              QGridLayout, QPushButton, QVBoxLayout,
                              QHBoxLayout, QGroupBox, QLabel, QInputDialog,
                              QMessageBox, QSizePolicy, QScrollArea,
                              QWidget, QFrame, QLayout)
from PyQt6.QtGui import QIcon, QColor, QAction
from PyQt6.QtCore import Qt

VENDOR  = 0x046d
CONFIG  = os.path.expanduser("~/.config/g213tray.json")
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
    ("White",  0xff, 0xff, 0xff),
    ("Red",    0xff, 0x00, 0x00),
    ("Green",  0x00, 0xff, 0x00),
    ("Blue",   0x00, 0x00, 0xff),
    ("Purple", 0x80, 0x00, 0xff),
    ("Orange", 0xff, 0x60, 0x00),
    ("Cyan",   0x00, 0xff, 0xff),
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
    "Print Screen": "PrtSc",
    "Scroll Lock": "ScrLk",
    "Pause": "Pause",
    "Page Up": "PgUp",
    "Page Down": "PgDn",
    "Insert": "Ins",
    "Delete": "Del",
    "Backspace": "Bksp",
    "Caps Lock": "Caps",
    "Left": "◀",
    "Right": "▶",
    "Up": "▲",
    "Down": "▼",
    "Num Lock": "Num",
    "Num /": "/",
    "Num *": "*",
    "Num -": "-",
    "Num +": "+",
    "Num Enter": "Enter",
    "Num .": ".",
    "Num 0": "0",
    "Num 1": "1",
    "Num 2": "2",
    "Num 3": "3",
    "Num 4": "4",
    "Num 5": "5",
    "Num 6": "6",
    "Num 7": "7",
    "Num 8": "8",
    "Num 9": "9",
    "Super": "Win",
    "Right Super": "Win",
    "Right Alt": "AltGr",
    "Right Ctrl": "Ctrl",
    "Right Shift": "Shift",
}

KEYBOARD_LAYOUT = [
    # Row 0: Function & System Keys
    [
        ("Esc", 4), (None, 4),
        ("F1", 4), ("F2", 4), ("F3", 4), ("F4", 4), (None, 2),
        ("F5", 4), ("F6", 4), ("F7", 4), ("F8", 4), (None, 2),
        ("F9", 4), ("F10", 4), ("F11", 4), ("F12", 4),
        (None, 2),
        ("Print Screen", 4), ("Scroll Lock", 4), ("Pause", 4),
        (None, 2),
        (None, 16),
    ],
    # Row 1: Number Row & Numpad Top
    [
        ("`", 4), ("1", 4), ("2", 4), ("3", 4), ("4", 4), ("5", 4),
        ("6", 4), ("7", 4), ("8", 4), ("9", 4), ("0", 4), ("-", 4),
        ("=", 4), ("Backspace", 8),
        (None, 2),
        ("Insert", 4), ("Home", 4), ("Page Up", 4),
        (None, 2),
        ("Num Lock", 4), ("Num /", 4), ("Num *", 4), ("Num -", 4),
    ],
    # Row 2: QWERTY & Numpad 7-9
    [
        ("Tab", 6), ("Q", 4), ("W", 4), ("E", 4), ("R", 4), ("T", 4),
        ("Y", 4), ("U", 4), ("I", 4), ("O", 4), ("P", 4), ("[", 4),
        ("]", 4), ("\\", 6),
        (None, 2),
        ("Delete", 4), ("End", 4), ("Page Down", 4),
        (None, 2),
        ("Num 7", 4), ("Num 8", 4), ("Num 9", 4), ("Num +", 4, 2),
    ],
    # Row 3: Home Row & Numpad 4-6
    [
        ("Caps Lock", 7), ("A", 4), ("S", 4), ("D", 4), ("F", 4),
        ("G", 4), ("H", 4), ("J", 4), ("K", 4), ("L", 4), (";", 4),
        ("'", 4), ("Enter", 9),
        (None, 2),
        (None, 12),
        (None, 2),
        ("Num 4", 4), ("Num 5", 4), ("Num 6", 4),
    ],
    # Row 4: Shift Row & Up Arrow & Numpad 1-3
    [
        ("Shift", 9), ("Z", 4), ("X", 4), ("C", 4), ("V", 4),
        ("B", 4), ("N", 4), ("M", 4), (",", 4), (".", 4),
        ("/", 4), ("Right Shift", 11),
        (None, 2),
        (None, 4), ("Up", 4), (None, 4),
        (None, 2),
        ("Num 1", 4), ("Num 2", 4), ("Num 3", 4), ("Num Enter", 4, 2),
    ],
    # Row 5: Bottom Row, Arrows & Numpad 0/.
    [
        ("Ctrl", 5), ("Super", 5), ("Alt", 5), ("Space", 25),
        ("Right Alt", 5), ("Right Super", 5), ("Menu", 5), ("Right Ctrl", 5),
        (None, 2),
        ("Left", 4), ("Down", 4), ("Right", 4),
        (None, 2),
        ("Num 0", 8), ("Num .", 4),
    ],
]


def load_languages():
    try:
        with open(LANGUAGES, encoding="utf-8") as language_file:
            return json.load(language_file)
    except (OSError, json.JSONDecodeError):
        return {}


TRANSLATIONS = load_languages()


def _send(r, g, b, keyboard, language="en"):
    profile = KEYBOARDS[keyboard]
    devices = list(usb.core.find(find_all=True, idVendor=VENDOR) or [])
    dev = next((candidate for candidate in devices
                if candidate.idProduct in profile["product_ids"]), None)
    if dev is None:
        detected = ", ".join(f"0x{candidate.idProduct:04x}"
                             for candidate in devices)
        message = TRANSLATIONS.get(language, TRANSLATIONS["en"])["not_found"]
        print(message.format(keyboard=profile["name"],
                             detected=detected or "none"), file=sys.stderr)
        return
    iface = 1
    detached = False
    if dev.is_kernel_driver_active(iface):
        dev.detach_kernel_driver(iface)
        detached = True
    usb.util.claim_interface(dev, iface)
    try:
        pkt = [0x11, 0xff, *profile["packet_prefix"], 0x00, 0x01, r, g, b,
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        dev.ctrl_transfer(0x21, 0x09, 0x0211, iface, pkt)
    finally:
        usb.util.release_interface(dev, iface)
        if detached:
            try:
                dev.attach_kernel_driver(iface)
            except Exception:
                pass


def _send_keys(key_colors, keyboard, language="en"):
    profile = KEYBOARDS[keyboard]
    if not profile["per_key"] or not key_colors:
        return
    devices = list(usb.core.find(find_all=True, idVendor=VENDOR) or [])
    dev = next((candidate for candidate in devices
                if candidate.idProduct in profile["product_ids"]), None)
    if dev is None:
        detected = ", ".join(f"0x{candidate.idProduct:04x}"
                             for candidate in devices)
        message = TRANSLATIONS.get(language, TRANSLATIONS["en"])["not_found"]
        print(message.format(keyboard=profile["name"],
                             detected=detected or "none"), file=sys.stderr)
        return
    iface = 1
    detached = False
    if dev.is_kernel_driver_active(iface):
        dev.detach_kernel_driver(iface)
        detached = True
    usb.util.claim_interface(dev, iface)
    try:
        items = sorted(
            ((KEYS[name], color) for name, color in key_colors.items()
             if name in KEYS),
            key=lambda item: item[0])
        for start in range(0, len(items), 14):
            packet = list(profile["key_packet_prefix"])
            for key_id, color in items[start:start + 14]:
                packet.extend((key_id, *color))
            packet.extend([0x00] * (64 - len(packet)))
            dev.ctrl_transfer(0x21, 0x09, 0x0212, iface, packet)
            try:
                dev.read(0x82, 64, timeout=1)
            except usb.core.USBError:
                pass
        commit = [0x11, 0xff, 0x0c, 0x5a]
        dev.ctrl_transfer(0x21, 0x09, 0x0211, iface,
                          commit + [0x00] * 16)
        try:
            dev.read(0x82, 64, timeout=1)
        except usb.core.USBError:
            pass
    finally:
        usb.util.release_interface(dev, iface)
        if detached:
            try:
                dev.attach_kernel_driver(iface)
            except Exception:
                pass


def detect_keyboard():
    devices = list(usb.core.find(find_all=True, idVendor=VENDOR) or [])
    for keyboard, profile in KEYBOARDS.items():
        if any(device.idProduct in profile["product_ids"]
               for device in devices):
            return keyboard
    return None


def detect_language():
    system_locale = locale.getlocale()[0] or ""
    return "de" if system_locale.lower().startswith("de") else "en"


def load_state():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except Exception:
        return {"on": True, "color": [255, 255, 255],
                "keyboard": "g213", "language": "de",
                "keyboard_auto": True, "language_auto": True}


def ensure_state(state, detected_keyboard, system_language):
    state.setdefault("on", True)
    state.setdefault("color", [255, 255, 255])
    state.setdefault("keyboard_auto", True)
    state.setdefault("language_auto", True)
    state.setdefault("key_colors", {})
    state.setdefault("custom_presets", [])
    if state["keyboard_auto"]:
        state["keyboard"] = detected_keyboard or "g213"
    if state["language_auto"]:
        state["language"] = system_language
    if state.get("keyboard") not in KEYBOARDS:
        state["keyboard"] = "g213"
    if state.get("language") not in TRANSLATIONS:
        state["language"] = "de"
    return state


def save_state(state):
    with open(CONFIG, "w") as f:
        json.dump(state, f)


class G213Tray:
    def __init__(self, app):
        self.app   = app
        self.state = ensure_state(load_state(), detect_keyboard(),
                                  detect_language())
        self.translations = TRANSLATIONS
        self.tray  = QSystemTrayIcon(QIcon.fromTheme("input-keyboard"), app)
        self.menu = QMenu()
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))
        self._apply_state()

        # left click = toggle
        self.tray.activated.connect(self._on_activate)

    def _text(self, key):
        return self.translations[self.state["language"]][key]

    def _build_menu(self):
        menu = self.menu
        menu.clear()

        toggle = QAction(self._text("toggle"), menu)
        toggle.triggered.connect(self._toggle)
        menu.addAction(toggle)
        menu.addSeparator()

        for index, (_, r, g, b) in enumerate(PRESETS):
            name = self.translations[self.state["language"]]["presets"][index]
            def make_cb(r=r, g=g, b=b):
                def cb():
                    self._set_all_color(r, g, b)
                return cb
            action = QAction(name, menu)
            action.triggered.connect(make_cb())
            menu.addAction(action)

        saved_menu = menu.addMenu(self._text("saved_presets"))
        if self.state["custom_presets"]:
            for preset in self.state["custom_presets"]:
                action = QAction(preset["name"], saved_menu)
                action.triggered.connect(
                    lambda checked=False, value=preset:
                    self._apply_custom_preset(value))
                saved_menu.addAction(action)
        else:
            empty = QAction(self._text("no_saved_presets"), saved_menu)
            empty.setEnabled(False)
            saved_menu.addAction(empty)

        menu.addSeparator()
        custom = QAction(self._text("custom_color"), menu)
        custom.triggered.connect(self._edit_custom_color)
        menu.addAction(custom)

        menu.addSeparator()
        keyboard_menu = menu.addMenu(self._text("keyboard"))
        auto_keyboard = QAction(self._text("automatic"), keyboard_menu)
        auto_keyboard.setCheckable(True)
        auto_keyboard.setChecked(self.state["keyboard_auto"])
        auto_keyboard.triggered.connect(self._select_auto_keyboard)
        keyboard_menu.addAction(auto_keyboard)
        keyboard_menu.addSeparator()
        for keyboard, profile in KEYBOARDS.items():
            action = QAction(profile["name"], keyboard_menu)
            action.setCheckable(True)
            action.setChecked(self.state["keyboard"] == keyboard)
            action.triggered.connect(
                lambda checked, selected=keyboard: self._select_keyboard(selected))
            keyboard_menu.addAction(action)

        language_menu = menu.addMenu(self._text("language"))
        auto_language = QAction(self._text("system_default"), language_menu)
        auto_language.setCheckable(True)
        auto_language.setChecked(self.state["language_auto"])
        auto_language.triggered.connect(self._select_system_language)
        language_menu.addAction(auto_language)
        language_menu.addSeparator()
        for language, translation in self.translations.items():
            action = QAction(translation["language_name"], language_menu)
            action.setCheckable(True)
            action.setChecked(self.state["language"] == language)
            action.triggered.connect(
                lambda checked, selected=language: self._select_language(selected))
            language_menu.addAction(action)

        menu.addSeparator()
        quit_a = QAction(self._text("quit"), menu)
        quit_a.triggered.connect(self.app.quit)
        menu.addAction(quit_a)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def _apply_state(self):
        if self.state["on"]:
            if self.state["key_colors"] and self._per_key_supported():
                _send_keys(self.state["key_colors"], self.state["keyboard"],
                           self.state["language"])
            else:
                r, g, b = self.state["color"]
                _send(r, g, b, self.state["keyboard"], self.state["language"])
        else:
            _send(0, 0, 0, self.state["keyboard"], self.state["language"])

    def _per_key_supported(self):
        return KEYBOARDS[self.state["keyboard"]]["per_key"]

    def _set_all_color(self, r, g, b):
        self.state["color"] = [r, g, b]
        self.state["key_colors"] = {}
        self.state["on"] = True
        _send(r, g, b, self.state["keyboard"], self.state["language"])
        save_state(self.state)

    def _apply_custom_preset(self, preset):
        colors = preset.get("colors", {})
        fallback = preset.get("color")
        if fallback is None and colors:
            fallback = colors[sorted(colors)[0]]
        if fallback is None:
            fallback = self.state["color"]

        if self._per_key_supported() and colors:
            self.state["key_colors"] = {
                key: list(colors.get(key, fallback))
                for key in preset.get("keys", [])
                if key in KEYS
            }
            if self.state["key_colors"]:
                self.state["color"] = list(next(
                    iter(self.state["key_colors"].values())))
                self.state["on"] = True
                _send_keys(self.state["key_colors"], self.state["keyboard"],
                           self.state["language"])
                save_state(self.state)
                return

        self._set_all_color(*fallback)

    def _select_keyboard(self, keyboard):
        self.state["keyboard_auto"] = False
        self.state["keyboard"] = keyboard
        save_state(self.state)
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))
        self._apply_state()

    def _select_auto_keyboard(self):
        self.state["keyboard_auto"] = True
        self.state["keyboard"] = detect_keyboard() or "g213"
        save_state(self.state)
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))
        self._apply_state()

    def _select_language(self, language):
        self.state["language_auto"] = False
        self.state["language"] = language
        save_state(self.state)
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))

    def _select_system_language(self):
        self.state["language_auto"] = True
        self.state["language"] = detect_language()
        save_state(self.state)
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))

    def _toggle(self):
        self.state["on"] = not self.state["on"]
        self._apply_state()
        save_state(self.state)

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:   # left click
            self._toggle()

    def _pick_color(self):
        r, g, b = self.state["color"]
        color = QColorDialog.getColor(QColor(r, g, b))
        if color.isValid():
            self._set_all_color(color.red(), color.green(), color.blue())

    def _edit_custom_color(self):
        dialog = QDialog()
        dialog.setWindowTitle(self._text("custom_color"))
        dialog.setMinimumWidth(980)
        layout = QVBoxLayout(dialog)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        selected = set()
        draft_colors = {key: list(color)
                for key, color in self.state["key_colors"].items()}
        selected_color = [*self.state["color"]]

        if not self._per_key_supported():
            layout.addWidget(QLabel(self._text("per_key_unavailable")))
            all_keys = QPushButton(self._text("all_keys"))
            all_keys.clicked.connect(lambda: self._pick_color())
            layout.addWidget(all_keys)
        else:
            group_box = QGroupBox(self._text("groups")["title"])
            group_box.setAlignment(Qt.AlignmentFlag.AlignLeft)
            group_box.setStyleSheet(
                "QGroupBox { font-weight: bold; } "
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 3px; }"
            )
            group_layout = QHBoxLayout(group_box)
            none_button = QPushButton(self._text("none"))
            none_button.setStyleSheet("background-color: #ffd6d6;")
            none_button.clicked.connect(
                lambda: self._clear_selection(selected, key_buttons,
                                               draft_colors,
                                               self.state["color"]))
            group_layout.addWidget(none_button)
            all_button = QPushButton(self._text("select_all"))
            all_button.clicked.connect(
                lambda: self._select_all(selected, selected_color,
                                         draft_colors, key_buttons))
            group_layout.addWidget(all_button)
            for group in KEY_GROUPS:
                button = QPushButton(self._text("groups")[group])
                button.clicked.connect(
                    lambda checked, name=group: self._select_group(
                        name, selected, selected_color, draft_colors,
                        key_buttons))
                group_layout.addWidget(button)
            layout.addWidget(group_box)

            key_label = QLabel(self._text("individual_keys"))
            key_label.setStyleSheet(
                "font-weight: bold; color: #475569; margin-top: 6px; margin-bottom: 2px;"
            )
            layout.addWidget(key_label)

            key_frame = QFrame()
            key_frame.setStyleSheet(
                "QFrame {"
                "  background-color: #1a1b1e;"
                "  border: 1px solid #2e3138;"
                "  border-radius: 8px;"
                "}"
            )
            key_layout = QGridLayout(key_frame)
            key_layout.setContentsMargins(10, 10, 10, 10)
            key_layout.setHorizontalSpacing(3)
            key_layout.setVerticalSpacing(3)
            for column in range(92):
                key_layout.setColumnStretch(column, 1)
            key_buttons = {}
            for row, row_keys in enumerate(KEYBOARD_LAYOUT):
                column = 0
                for entry in row_keys:
                    name, span = entry[:2]
                    row_span = entry[2] if len(entry) > 2 else 1
                    if name is None:
                        column += span
                        continue
                    display_text = KEY_DISPLAY_LABELS.get(name, name)
                    button = QPushButton(display_text)
                    button.setToolTip(name)
                    button.setCheckable(True)
                    button.setChecked(name in selected)
                    button.setSizePolicy(QSizePolicy.Policy.Expanding,
                                         QSizePolicy.Policy.Fixed)
                    if row_span > 1:
                        button.setFixedHeight(32 * row_span + 3 * (row_span - 1))
                    else:
                        button.setFixedHeight(32)
                    self._style_key_button(
                        button, draft_colors.get(name, selected_color),
                        name in selected)
                    button.clicked.connect(
                        lambda checked, key=name, key_button=button:
                        self._toggle_key(
                            key, checked, selected, key_button, draft_colors,
                            selected_color))
                    key_buttons[name] = button
                    key_layout.addWidget(button, row, column, row_span, span)
                    column += span
            layout.addWidget(key_frame)

            color_row = QHBoxLayout()
            color_label = QLabel(self._text("selected_color") + ":")
            color_button = QPushButton()
            color_button.setFixedSize(60, 28)
            self._style_key_button(color_button, selected_color)
            color_button.clicked.connect(
                lambda: self._choose_dialog_color(
                    selected_color, selected, draft_colors, key_buttons,
                    color_button))
            color_row.addWidget(color_label)
            color_row.addWidget(color_button)

            color_row.addSpacing(16)
            swatches_label = QLabel(self._text("quick_colors") + ":")
            color_row.addWidget(swatches_label)

            swatch_colors = [
                *[(r, g, b) for _, r, g, b in PRESETS],
                (0, 0, 0),
            ]
            for r, g, b in swatch_colors:
                swatch_btn = QPushButton()
                swatch_btn.setFixedSize(28, 28)
                self._style_key_button(swatch_btn, [r, g, b])
                if (r, g, b) == (0, 0, 0):
                    swatch_btn.setToolTip(self._text("off"))
                swatch_btn.clicked.connect(
                    lambda checked, c=[r, g, b]: self._set_active_color(
                        c, selected_color, selected, draft_colors, key_buttons,
                        color_button))
                color_row.addWidget(swatch_btn)

            color_row.addStretch()
            layout.addLayout(color_row)

            presets_box = QGroupBox(self._text("saved_presets"))
            presets_box.setAlignment(Qt.AlignmentFlag.AlignLeft)
            presets_box.setStyleSheet(
                "QGroupBox { font-weight: bold; } "
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 8px; padding: 0 3px; }"
            )
            presets_box_layout = QVBoxLayout(presets_box)

            presets_scroll = QScrollArea()
            presets_scroll.setWidgetResizable(True)
            presets_scroll.setMaximumHeight(130)
            presets_scroll.setMinimumHeight(65)
            presets_scroll.setStyleSheet(
                "QScrollArea { border: 1px solid #cbd5e1; border-radius: 6px; background-color: #f8fafc; }"
            )
            presets_widget = QWidget()
            presets_list_layout = QVBoxLayout(presets_widget)
            presets_list_layout.setContentsMargins(6, 6, 6, 6)
            presets_list_layout.setSpacing(4)
            presets_scroll.setWidget(presets_widget)
            presets_box_layout.addWidget(presets_scroll)

            self._rebuild_preset_buttons(
                presets_list_layout, selected, selected_color, draft_colors,
                key_buttons, color_button, dialog)
            layout.addWidget(presets_box)

            action_row = QHBoxLayout()
            save_button = QPushButton(self._text("save_preset"))
            save_button.clicked.connect(
                lambda checked=False: self._save_custom_preset(
                    selected, selected_color, draft_colors, presets_list_layout,
                    key_buttons, color_button, dialog))
            action_row.addWidget(save_button)
            action_row.addStretch()
            apply_button = QPushButton(self._text("apply"))
            apply_button.setStyleSheet("background-color: #d9f7d9;")
            apply_button.clicked.connect(
                lambda: self._apply_selection(
                    selected, selected_color, draft_colors, key_buttons))
            cancel_button = QPushButton(self._text("cancel"))
            cancel_button.clicked.connect(dialog.reject)
            ok_button = QPushButton(self._text("ok"))
            ok_button.clicked.connect(lambda checked=False: (
                self._apply_selection(
                    selected, selected_color, draft_colors, key_buttons),
                dialog.accept()))
            action_row.addWidget(apply_button)
            action_row.addWidget(cancel_button)
            action_row.addWidget(ok_button)
            layout.addLayout(action_row)

        if self._per_key_supported():
            pass
        else:
            close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            close.rejected.connect(dialog.reject)
            layout.addWidget(close)
        dialog.exec()

    def _toggle_key(self, key, checked, selected, button, draft_colors,
                    selected_color):
        if checked:
            selected.add(key)
            draft_colors[key] = list(selected_color)
        else:
            selected.discard(key)
        self._style_key_button(button, draft_colors.get(key, selected_color),
                               checked)

    def _clear_selection(self, selected, key_buttons, draft_colors,
                         default_color):
        selected.clear()
        for key, button in key_buttons.items():
            button.setChecked(False)
            self._style_key_button(button, draft_colors.get(key, default_color),
                                   False)

    def _select_all(self, selected, selected_color, draft_colors, key_buttons):
        for key in KEYS:
            selected.add(key)
            draft_colors[key] = list(selected_color)
            key_buttons[key].setChecked(True)
            self._style_key_button(key_buttons[key], draft_colors[key], True)

    def _select_group(self, group, selected, selected_color, draft_colors,
                      key_buttons):
        for key in KEY_GROUPS[group]:
            selected.add(key)
            draft_colors[key] = list(selected_color)
            key_buttons[key].setChecked(True)
            self._style_key_button(key_buttons[key], selected_color, True)

    def _set_active_color(self, color, selected_color, selected, draft_colors,
                          key_buttons, color_button):
        selected_color[:] = list(color)
        self._style_key_button(color_button, selected_color)
        for key in selected:
            draft_colors[key] = list(selected_color)
            self._style_key_button(key_buttons[key], selected_color, True)

    def _choose_dialog_color(self, selected_color, selected, draft_colors,
                             key_buttons, color_button):
        color = QColorDialog.getColor(QColor(*selected_color))
        if color.isValid():
            self._set_active_color(
                [color.red(), color.green(), color.blue()],
                selected_color, selected, draft_colors, key_buttons, color_button)

    def _apply_selection(self, selected, selected_color, draft_colors,
                         key_buttons):
        targets = set(selected) if selected else set(draft_colors.keys())
        for key in targets:
            self.state["key_colors"][key] = list(draft_colors.get(
                key, selected_color))
            draft_colors[key] = list(self.state["key_colors"][key])
            self._style_key_button(key_buttons[key], draft_colors[key], key in selected)
        if self.state["key_colors"]:
            self.state["on"] = True
            _send_keys(self.state["key_colors"], self.state["keyboard"],
                       self.state["language"])
            save_state(self.state)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout)
                sub_layout.deleteLater()

    def _rebuild_preset_buttons(self, presets_layout, selected,
                                selected_color, draft_colors, key_buttons,
                                color_button, dialog=None):
        self._clear_layout(presets_layout)
        if not self.state["custom_presets"]:
            presets_layout.addWidget(QLabel(self._text("no_saved_presets")))
            if dialog:
                dialog.adjustSize()
            return
        for index, preset in enumerate(self.state["custom_presets"]):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            button = QPushButton(preset["name"])
            button.setSizePolicy(QSizePolicy.Policy.Maximum,
                                 QSizePolicy.Policy.Fixed)
            button.clicked.connect(
                lambda checked, value=preset: self._load_custom_preset(
                    value, selected, selected_color, draft_colors,
                    key_buttons, color_button))
            delete_button = QPushButton("✕")
            delete_button.setFixedWidth(28)
            delete_button.setStyleSheet("background-color: #ffd6d6; font-weight: bold;")
            delete_button.clicked.connect(
                lambda checked, position=index: self._delete_preset(
                    position, presets_layout, selected, selected_color,
                    draft_colors, key_buttons, color_button, dialog))
            row.addWidget(button)
            row.addWidget(delete_button)
            row.addStretch()
            presets_layout.addWidget(row_widget)
        presets_layout.addStretch()
        if dialog:
            dialog.adjustSize()

    def _delete_preset(self, index, presets_layout, selected,
                       selected_color, draft_colors, key_buttons,
                       color_button, dialog=None):
        preset = self.state["custom_presets"][index]
        answer = QMessageBox.question(
            None, self._text("delete_preset"),
            self._text("confirm_delete").format(name=preset["name"]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        del self.state["custom_presets"][index]
        save_state(self.state)
        self._build_menu()
        self._rebuild_preset_buttons(
            presets_layout, selected, selected_color, draft_colors,
            key_buttons, color_button, dialog)

    def _save_custom_preset(self, selected, selected_color, draft_colors,
                            presets_layout, key_buttons, color_button,
                            dialog=None):
        keys_to_save = selected if selected else set(draft_colors.keys())
        if not keys_to_save:
            return
        name, accepted = QInputDialog.getText(
            None, self._text("save_preset"), self._text("preset_name"))
        if accepted and name.strip():
            colors = {
                key: list(draft_colors.get(key, selected_color))
                for key in keys_to_save
            }
            self.state["custom_presets"].append({
                "name": name.strip(),
                "keys": sorted(keys_to_save),
                "colors": colors,
            })
            save_state(self.state)
            self._build_menu()
            self._rebuild_preset_buttons(
                presets_layout, selected, selected_color, draft_colors,
                key_buttons, color_button, dialog)

    def _load_custom_preset(self, preset, selected, selected_color,
                            draft_colors, key_buttons, color_button):
        selected.clear()
        selected.update(preset["keys"])
        colors = preset.get("colors", {})
        fallback = preset.get("color", self.state["color"])
        for key in selected:
            draft_colors[key] = list(colors.get(key, fallback))
        if selected:
            selected_color[:] = list(draft_colors[next(iter(selected))])
        for key, button in key_buttons.items():
            button.setChecked(key in selected)
            self._style_key_button(
                button, draft_colors.get(key, self.state["color"]),
                key in selected)
        self._style_key_button(color_button, selected_color)

    def _style_key_button(self, button, color, selected=False):
        luminance = (0.299 * color[0] + 0.587 * color[1] +
                     0.114 * color[2])
        text_color = "#0f172a" if luminance > 145 else "#f8fafc"
        if selected:
            border = "2px solid #00d2ff"
        else:
            border = "1px solid rgba(255, 255, 255, 0.22)" if luminance < 100 else "1px solid rgba(0, 0, 0, 0.35)"
        button.setStyleSheet(
            "QPushButton {"
            f"  background-color: rgb({color[0]}, {color[1]}, {color[2]});"
            f"  color: {text_color};"
            f"  border: {border};"
            "  border-radius: 4px;"
            "  font-weight: bold;"
            "  font-size: 11px;"
            "  padding: 0px;"
            "}"
            "QPushButton:hover {"
            "  border: 2px solid #38bdf8;"
            "}"
        )


if __name__ == "__main__":
    if not TRANSLATIONS:
        raise RuntimeError("No language options found")
    app = App = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = G213Tray(app)
    detected_keyboard = detect_keyboard()
    if detected_keyboard:
        print(f"Supported keyboard found: {KEYBOARDS[detected_keyboard]['name']}. G213Tray is running in the system tray.")
    else:
        print("No supported Logitech keyboard found. G213Tray is running in the system tray, but no supported device was detected.")
    sys.exit(app.exec())
