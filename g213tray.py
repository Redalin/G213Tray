#!/usr/bin/env python3
"""G213 keyboard lighting control — KDE system tray."""
import sys
import json
import os
import locale
import usb.core
import usb.util
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu,
                              QColorDialog)
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
    },
    "g512": {
        "name": "Logitech G512",
        "product_ids": (0xc342, 0xc33c),
        "packet_prefix": (0x0d, 0x3c),
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
                    self.state["color"] = [r, g, b]
                    self.state["on"]    = True
                    _send(r, g, b, self.state["keyboard"],
                          self.state["language"])
                    save_state(self.state)
                return cb
            action = QAction(name, menu)
            action.triggered.connect(make_cb())
            menu.addAction(action)

        menu.addSeparator()
        custom = QAction(self._text("custom_color"), menu)
        custom.triggered.connect(self._pick_color)
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
            r, g, b = self.state["color"]
            _send(r, g, b, self.state["keyboard"], self.state["language"])
        else:
            _send(0, 0, 0, self.state["keyboard"], self.state["language"])

    def _select_keyboard(self, keyboard):
        self.state["keyboard_auto"] = False
        self.state["keyboard"] = keyboard
        save_state(self.state)
        self._build_menu()
        self.tray.setToolTip(self._text("lighting"))
        r, g, b = self.state["color"] if self.state["on"] else (0, 0, 0)
        _send(r, g, b, keyboard, self.state["language"])

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
        if self.state["on"]:
            r, g, b = self.state["color"]
        else:
            r, g, b = 0, 0, 0
        _send(r, g, b, self.state["keyboard"], self.state["language"])
        save_state(self.state)

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:   # left click
            self._toggle()

    def _pick_color(self):
        r, g, b = self.state["color"]
        initial = QColor(r, g, b)
        color = QColorDialog.getColor(initial)
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            self.state["color"] = [r, g, b]
            self.state["on"]    = True
            _send(r, g, b, self.state["keyboard"], self.state["language"])
            save_state(self.state)


if __name__ == "__main__":
    if not TRANSLATIONS:
        raise RuntimeError("No language options found")
    app = App = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = G213Tray(app)
    sys.exit(app.exec())
