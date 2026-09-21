#!/usr/bin/env python3
"""G213 keyboard lighting control — KDE system tray."""
import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

from constants import (KEYBOARDS, PRESETS, KEYS, KEY_GROUPS,
                       KEY_DISPLAY_LABELS, KEYBOARD_LAYOUT)
from editor import CustomColorEditor
from hardware import _send, _send_keys, detect_keyboard
from state import (TRANSLATIONS, detect_language, ensure_state, load_state,
                   save_state)

class G213Tray(CustomColorEditor):
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
