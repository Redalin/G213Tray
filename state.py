"""Persistent application state and interface language handling."""

import json
import locale

from constants import CONFIG, LANGUAGES, KEYBOARDS


def load_languages():
    try:
        with open(LANGUAGES, encoding="utf-8") as language_file:
            return json.load(language_file)
    except (OSError, json.JSONDecodeError):
        return {}


TRANSLATIONS = load_languages()


def detect_language():
    system_locale = locale.getlocale()[0] or ""
    return "de" if system_locale.lower().startswith("de") else "en"


def load_state():
    try:
        with open(CONFIG) as state_file:
            return json.load(state_file)
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
    with open(CONFIG, "w") as state_file:
        json.dump(state, state_file)
