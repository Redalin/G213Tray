"""USB communication with supported Logitech keyboards."""

import sys

import usb.core
import usb.util

from constants import KEYS, KEYBOARDS, VENDOR
from state import TRANSLATIONS


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
               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
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
