"""Custom keyboard color editor used by the tray application."""

from PyQt6.QtWidgets import (QColorDialog, QDialog, QDialogButtonBox,
                              QGridLayout, QPushButton, QVBoxLayout,
                              QHBoxLayout, QGroupBox, QLabel, QInputDialog,
                              QMessageBox, QSizePolicy, QScrollArea,
                              QWidget, QFrame, QLayout)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from constants import (KEYS, KEY_GROUPS, KEY_DISPLAY_LABELS,
                       KEYBOARD_LAYOUT, PRESETS)
from hardware import _send_keys
from state import save_state


class CustomColorEditor:
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
