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
                              QHBoxLayout, QGroupBox, QLabel, QInputDialog)
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
    "Right Shift": 0xe7, "Menu": 0xe8,
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

KEYBOARD_LAYOUT = [
    (0, [("Esc", 2), ("F1", 2), ("F2", 2), ("F3", 2), ("F4", 2),
        ("F5", 2), ("F6", 2), ("F7", 2), ("F8", 2), ("F9", 2),
        ("F10", 2), ("F11", 2), ("F12", 2)]),
    (0, [("`", 2), ("1", 2), ("2", 2), ("3", 2), ("4", 2),
        ("5", 2), ("6", 2), ("7", 2), ("8", 2), ("9", 2),
        ("0", 2), ("-", 2), ("=", 2), ("Backspace", 4)]),
    (1, [("Tab", 3), ("Q", 2), ("W", 2), ("E", 2), ("R", 2),
        ("T", 2), ("Y", 2), ("U", 2), ("I", 2), ("O", 2),
        ("P", 2), ("[", 2), ("]", 2), ("\\", 2)]),
    (1, [("Caps Lock", 3), ("A", 2), ("S", 2), ("D", 2), ("F", 2),
        ("G", 2), ("H", 2), ("J", 2), ("K", 2), ("L", 2),
        (";", 2), ("'", 2), ("Enter", 4)]),
    (0, [("Shift", 4), ("Z", 2), ("X", 2), ("C", 2), ("V", 2),
        ("B", 2), ("N", 2), ("M", 2), (",", 2), (".", 2),
        ("/", 2), ("Right Shift", 4)]),
        (0, [("Ctrl", 3), ("Super", 3), ("Alt", 3), ("Space", 11),
            ("Right Alt", 3), ("Right Super", 3), ("Right Ctrl", 3),
            ("Menu", 3)]),
    (1, [("Print Screen", 2), ("Scroll Lock", 2), ("Pause", 2),
        ("Insert", 2), ("Home", 2), ("Page Up", 2),
        ("Num Lock", 2), ("Num /", 2), ("Num *", 2)]),
    (1, [("Delete", 2), ("End", 2), ("Page Down", 2), ("Num 7", 2),
        ("Num 8", 2), ("Num 9", 2), ("Num -", 2)]),
    (5, [("Up", 2), ("Num 4", 2), ("Num 5", 2), ("Num 6", 2),
        ("Num +", 2)]),
    (3, [("Left", 2), ("Down", 2), ("Right", 2), ("Num 1", 2),
        ("Num 2", 2), ("Num 3", 2), ("Num Enter", 2)]),
    (8, [("Num 0", 4), ("Num .", 2)]),
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
    try:
        items = [(KEYS[name], color) for name, color in key_colors.items()
                 if name in KEYS]
        for start in range(0, len(items), 14):
            packet = list(profile["key_packet_prefix"])
            for key_id, color in items[start:start + 14]:
                packet.extend((key_id, *color))
            packet.extend([0x00] * (64 - len(packet)))
            dev.ctrl_transfer(0x21, 0x09, 0x0211, iface, packet)
        commit = [0x11, 0xff, 0x0c, 0x5a]
        dev.ctrl_transfer(0x21, 0x09, 0x0211, iface,
                          commit + [0x00] * 16)
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
        quit_a.triggered.connect(app.quit)
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
        layout = QVBoxLayout(dialog)
        selected = set(self.state["key_colors"])
        selected_color = [*self.state["color"]]

        if not self._per_key_supported():
            layout.addWidget(QLabel(self._text("per_key_unavailable")))
            all_keys = QPushButton(self._text("all_keys"))
            all_keys.clicked.connect(lambda: self._pick_color())
            layout.addWidget(all_keys)
        else:
            group_box = QGroupBox(self._text("groups")["title"])
            group_layout = QHBoxLayout(group_box)
            none_button = QPushButton(self._text("none"))
            none_button.clicked.connect(
                lambda: self._clear_selection(selected, key_buttons))
            group_layout.addWidget(none_button)
            for group in KEY_GROUPS:
                button = QPushButton(self._text("groups")[group])
                button.clicked.connect(
                    lambda checked, name=group: self._select_group(
                        name, selected, key_buttons))
                group_layout.addWidget(button)
            layout.addWidget(group_box)

            key_box = QGroupBox(self._text("individual_keys"))
            key_layout = QGridLayout(key_box)
            key_buttons = {}
            for row, (offset, row_keys) in enumerate(KEYBOARD_LAYOUT):
                column = offset
                for name, span in row_keys:
                    button = QPushButton(name)
                    button.setCheckable(True)
                    button.setChecked(name in selected)
                    button.clicked.connect(
                        lambda checked, key=name: self._toggle_key(
                            key, checked, selected))
                    key_buttons[name] = button
                    key_layout.addWidget(button, row, column, 1, span)
                    column += span
            layout.addWidget(key_box)

            color_row = QHBoxLayout()
            color_label = QLabel(self._text("selected_color"))
            color_button = QPushButton()
            self._style_key_button(color_button, selected_color)
            color_button.clicked.connect(
                lambda: self._choose_dialog_color(selected_color, color_button))
            color_row.addWidget(color_label)
            color_row.addWidget(color_button)
            layout.addLayout(color_row)

            presets_box = QGroupBox(self._text("saved_presets"))
            presets_layout = QHBoxLayout(presets_box)
            for preset in self.state["custom_presets"]:
                button = QPushButton(preset["name"])
                button.clicked.connect(
                    lambda checked, value=preset: self._load_custom_preset(
                        value, selected, selected_color, key_buttons,
                        color_button))
                presets_layout.addWidget(button)
            if not self.state["custom_presets"]:
                presets_layout.addWidget(QLabel(self._text("no_saved_presets")))
            layout.addWidget(presets_box)

            action_row = QHBoxLayout()
            apply_button = QPushButton(self._text("apply"))
            apply_button.clicked.connect(
                lambda: self._apply_selection(selected, selected_color))
            save_button = QPushButton(self._text("save_preset"))
            save_button.clicked.connect(
                lambda: self._save_custom_preset(selected, selected_color))
            action_row.addWidget(apply_button)
            action_row.addWidget(save_button)
            layout.addLayout(action_row)

        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject)
        layout.addWidget(close)
        dialog.exec()

    def _toggle_key(self, key, checked, selected):
        if checked:
            selected.add(key)
        else:
            selected.discard(key)

    def _clear_selection(self, selected, key_buttons):
        selected.clear()
        for button in key_buttons.values():
            button.setChecked(False)

    def _select_group(self, group, selected, key_buttons):
        for key in KEY_GROUPS[group]:
            selected.add(key)
            key_buttons[key].setChecked(True)

    def _choose_dialog_color(self, selected_color, button):
        color = QColorDialog.getColor(QColor(*selected_color))
        if color.isValid():
            selected_color[:] = [color.red(), color.green(), color.blue()]
            self._style_key_button(button, selected_color)

    def _apply_selection(self, selected, selected_color):
        for key in selected:
            self.state["key_colors"][key] = list(selected_color)
        if selected:
            self.state["on"] = True
            _send_keys(self.state["key_colors"], self.state["keyboard"],
                       self.state["language"])
            save_state(self.state)

    def _save_custom_preset(self, selected, selected_color):
        if not selected:
            return
        name, accepted = QInputDialog.getText(
            None, self._text("save_preset"), self._text("preset_name"))
        if accepted and name.strip():
            self.state["custom_presets"].append({
                "name": name.strip(),
                "keys": sorted(selected),
                "color": list(selected_color),
            })
            save_state(self.state)

    def _load_custom_preset(self, preset, selected, selected_color,
                            key_buttons, color_button):
        selected.clear()
        selected.update(preset["keys"])
        selected_color[:] = preset["color"]
        for key, button in key_buttons.items():
            button.setChecked(key in selected)
        self._style_key_button(color_button, selected_color)

    def _style_key_button(self, button, color):
        button.setStyleSheet("background-color: rgb(%d, %d, %d)" % tuple(color))


if __name__ == "__main__":
    if not TRANSLATIONS:
        raise RuntimeError("No language options found")
    app = App = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = G213Tray(app)
    sys.exit(app.exec())
