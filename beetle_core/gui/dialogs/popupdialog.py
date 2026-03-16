# Copyright © 2018-2026 Johan Cockx, Matic Kukovec & Kristof Mulier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import *
import os
import os.path
import functools
import time
import qt
import data
import functions
import iconfunctions
import gui.helpers.buttons
import gui.helpers.advancedcombobox
import gui.templates.generaldialog
import gui.templates.widgetgenerator
import gui.stylesheets.button
import gui.stylesheets.dialogs
import bpathlib.path_power
import helpdocs.help_texts
import os_checker


def get_button_size():
    return data.get_general_icon_pixelsize() * 1.5


"""
---------------------------------------------------------
Custom Yes/No dialog window
---------------------------------------------------------
"""


class PopupDialog(gui.templates.generaldialog.GeneralDialog):
    # Signals
    enter_pressed_signal = qt.pyqtSignal()

    # Class variables
    state = False
    return_value = None
    dialog_type = None
    stored_gboxes = None
    checkbox_data = None

    # Static reference to the MainWindow object
    static_parent = None

    def __init__(
        self,
        parent,
        text,
        dialog_type=None,
        icon_path=None,
        title_text=None,
        add_textbox=False,
        initial_text=None,
        text_click_func=None,
        selected_text=None,
        lists=None,
        icons=None,
        large_text=False,
        missing_tool_options=None,
        buttons=None,
        center=False,
        scroll_layout=True,
        text_centered=False,
        settings_manipulator=None,
    ):
        """Initialization of widget and background."""
        super().__init__(parent, scroll_layout=scroll_layout)

        self.stored_gboxes = {}
        self.checkbox_data = {}
        self.settings_manipulator = settings_manipulator

        if title_text is None:
            self.setWindowTitle(dialog_type.title())
        else:
            self.setWindowTitle(title_text)

        self.setWindowFlags(
            qt.Qt.WindowType.Dialog
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowSystemMenuHint
            | qt.Qt.WindowType.WindowCloseButtonHint
        )

        if icon_path is not None:
            self.setWindowIcon(iconfunctions.get_qicon(icon_path))
        else:
            self.setWindowIcon(qt.QIcon(data.application_icon_abspath))

        self.return_value = qt.QMessageBox.StandardButton.Cancel
        self.init_gui(
            text,
            dialog_type,
            add_textbox,
            initial_text,
            text_click_func,
            selected_text,
            lists,
            icons,
            large_text,
            missing_tool_options=missing_tool_options,
            buttons=buttons,
            center=center,
            text_centered=text_centered,
        )
        self.layout().itemAt(0).widget().keyPressEvent = self.keyPressEvent

    def init_gui(
        self,
        text,
        dialog_type,
        add_textbox,
        initial_text,
        text_click_func,
        selected_text,
        lists,
        icons,
        large_text,
        missing_tool_options=None,
        buttons=None,
        center=False,
        text_centered=False,
    ) -> None:
        """

        :param text:
        :param dialog_type:
        :param add_textbox:
        :param initial_text:
        :param text_click_func:
        :param selected_text:
        :param lists:
        :param icons:
        :param large_text:
        :param missing_tool_options:
        :param buttons:
        :param center:
        :return:
        """
        self.dialog_type = dialog_type
        # Set the main layout
        self.main_layout: qt.QHBoxLayout = cast(
            qt.QHBoxLayout,
            gui.templates.widgetgenerator.create_layout(),
        )
        # Buttons and label
        font = data.get_general_font()
        font.setBold(True)

        self.group_box = (
            gui.templates.widgetgenerator.create_borderless_groupbox("Popup")
        )
        self.group_box.setSizePolicy(
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.group_layout = gui.templates.widgetgenerator.create_layout(
            vertical=True,
            margins=(5, 5, 5, 5),
            spacing=5,
        )
        self.group_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.group_layout.setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )
        self.group_box.setLayout(self.group_layout)
        # Add the label
        if large_text:
            self.label = gui.templates.widgetgenerator.create_textbrowser(
                "MainLabel"
            )
            screen_size = functions.get_screen_size()
            self.label.setMinimumWidth(int(screen_size.width() / 4))
            self.label.setMinimumHeight(int(screen_size.height() / 4))
            self.label.setHtml(text)
            self.group_layout.addWidget(self.label)
            if callable(text_click_func):

                def click_func(*args, parent=None, **kwargs):
                    text_click_func(*args, parent=parent, **kwargs)

                self.label.anchorClicked.connect(click_func)
        else:
            self.label = self._create_label(text, False)
            self.label.setContentsMargins(10, 10, 10, 10)
            self.label.setTextFormat(qt.Qt.TextFormat.AutoText)
            self.label.setWordWrap(False)
            self.label.setSizePolicy(
                qt.QSizePolicy.Policy.Expanding,
                qt.QSizePolicy.Policy.Expanding,
            )
            if callable(text_click_func):
                self.label.setOpenExternalLinks(False)

                def click_func(*args, parent=None, **kwargs):
                    text_click_func(*args, parent=parent, **kwargs)

                self.label.linkActivated.connect(click_func)
            self.group_layout.addWidget(self.label)

        if text_centered == True:
            self.label.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )

        # Add a input textbox
        if add_textbox == True:
            self.input_textbox: gui.templates.widgetgenerator.TextBox = (
                self._create_textbox(name="InputTextBox")
            )
            self.input_textbox.setText("")
            if initial_text is not None:
                self.input_textbox.setText(initial_text)
            self.group_layout.addWidget(self.input_textbox)

            # Connect the Enter press signal
            def enter_pressed():
                if dialog_type == "question":
                    self.close_and_return(qt.QMessageBox.StandardButton.Yes)
                elif dialog_type == "ok_cancel":
                    self.close_and_return(qt.QMessageBox.StandardButton.Ok)

            self.input_textbox.returnPressed.connect(enter_pressed)

        def create_ok_cancel_buttons(_icons=None):
            button_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            button_layout = qt.QHBoxLayout()
            button_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            button_box.setLayout(button_layout)
            self.group_layout.addWidget(button_box)

            # OK button
            self.button_ok = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Ok,
                parent=self,
                text="OK",
            )
            self.button_ok.on_signal.connect(self.update_state_ok)
            self.button_ok.off_signal.connect(self.update_state_reset)
            self.button_ok.click_signal.connect(self.close_and_return)
            button_layout.addWidget(self.button_ok)

            # Cancel button
            self.button_cancel = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Cancel,
                parent=self,
                text="CANCEL",
            )
            self.button_cancel.on_signal.connect(self.update_state_cancel)
            self.button_cancel.off_signal.connect(self.update_state_reset)
            self.button_cancel.click_signal.connect(self.close_and_return)
            button_layout.addWidget(self.button_cancel)

        # Setup the buttons
        if dialog_type == "question" or dialog_type == "warning":
            button_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            button_layout = qt.QHBoxLayout()
            button_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            button_box.setLayout(button_layout)
            self.group_layout.addWidget(button_box)

            self.button_yes = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Yes,
                parent=self,
                text="YES",
            )
            self.button_yes.on_signal.connect(self.update_state_on)
            self.button_yes.off_signal.connect(self.update_state_reset)
            self.button_yes.click_signal.connect(self.close_and_return)
            self.button_no = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.No,
                parent=self,
                text="NO",
            )
            self.button_no.on_signal.connect(self.update_state_off)
            self.button_no.off_signal.connect(self.update_state_reset)
            self.button_no.click_signal.connect(self.close_and_return)

            button_layout.addWidget(self.button_yes)
            button_layout.addSpacing(20)
            button_layout.addWidget(self.button_no)

        elif dialog_type == "ok" or dialog_type == "blank":
            button_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            button_layout = qt.QHBoxLayout()
            button_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            button_box.setLayout(button_layout)
            self.group_layout.addWidget(button_box)

            self.button_ok = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Ok,
                parent=self,
                text="OK",
            )
            self.button_ok.on_signal.connect(self.update_state_ok)
            self.button_ok.off_signal.connect(self.update_state_reset)
            self.button_ok.click_signal.connect(self.close_and_return)
            button_layout.addWidget(self.button_ok)

        elif dialog_type == "ok_cancel":
            create_ok_cancel_buttons(icons)

        elif dialog_type == "checkboxes":

            def add_groupbox(gb_key, gb_name, gb_text, lb_text):
                self.stored_gboxes[gb_key] = (
                    gui.templates.widgetgenerator.create_groupbox_with_layout_and_info_button(
                        gb_name,
                        gb_text,
                        vertical=True,
                        adjust_margins_to_text=True,
                        info_size=data.get_general_icon_pixelsize(),
                        info_func=lambda: helpdocs.help_texts.dashboard_info(
                            gb_key
                        ),
                        background_color=data.theme["fonts"]["default"][
                            "background"
                        ],
                    )
                )
                layout = self.stored_gboxes[gb_key].layout()
                layout.setAlignment(
                    qt.Qt.AlignmentFlag.AlignLeft
                    | qt.Qt.AlignmentFlag.AlignVCenter
                )
                label = gui.templates.widgetgenerator.create_label(lb_text)
                layout.addWidget(label)
                self.group_layout.addWidget(self.stored_gboxes[gb_key])

            def update_checks(checkbox, boxes, name, state, *args, **kwargs):
                if state != qt.Qt.CheckState.Checked:
                    checkbox.on()

                for box in boxes:
                    if box is not checkbox:
                        box.off()
                self.checkbox_data[name] = boxes[0].state

            def add_files(gb_key, file_list, text_0, text_1, add_diff=False):
                if (file_list is not None) and (len(file_list) > 0):
                    layout = self.stored_gboxes[gb_key].layout()
                    grid_gb = (
                        gui.templates.widgetgenerator.create_borderless_groupbox()
                    )
                    grid_layout = qt.QGridLayout(grid_gb)
                    grid_gb.setLayout(grid_layout)
                    layout.addWidget(grid_gb)
                    if add_diff:
                        label_diff = gui.templates.widgetgenerator.create_label(
                            "diff"
                        )
                        grid_layout.addWidget(
                            label_diff,
                            0,
                            2,
                            alignment=qt.Qt.AlignmentFlag.AlignCenter
                            | qt.Qt.AlignmentFlag.AlignVCenter,
                        )
                    label_0 = gui.templates.widgetgenerator.create_label(text_0)
                    label_1 = gui.templates.widgetgenerator.create_label(text_1)
                    grid_layout.addWidget(
                        label_0,
                        0,
                        3,
                        alignment=qt.Qt.AlignmentFlag.AlignCenter
                        | qt.Qt.AlignmentFlag.AlignVCenter,
                    )
                    grid_layout.addWidget(
                        label_1,
                        0,
                        4,
                        alignment=qt.Qt.AlignmentFlag.AlignCenter
                        | qt.Qt.AlignmentFlag.AlignVCenter,
                    )
                    column_widths = [50, 200, 70, 70, 70]
                    for i, cw in enumerate(column_widths):
                        width = int(cw * data.get_global_scale())
                        grid_layout.setColumnMinimumWidth(i, width)
                    # Make the filename column stretch to fill all available space
                    grid_layout.setColumnStretch(1, 2)
                    row = 1
                    for f in file_list:
                        image, name, diff, diff_text, state = f
                        self.checkbox_data[name] = True
                        pixmap = gui.templates.widgetgenerator.create_label(
                            image=image
                        )
                        size = get_button_size() / 2
                        pixmap.setFixedSize(qt.create_qsize(size, size))
                        grid_layout.addWidget(
                            pixmap,
                            row,
                            0,
                            alignment=qt.Qt.AlignmentFlag.AlignCenter
                            | qt.Qt.AlignmentFlag.AlignVCenter,
                        )
                        grid_layout.addWidget(
                            gui.templates.widgetgenerator.create_label(name),
                            row,
                            1,
                            alignment=qt.Qt.AlignmentFlag.AlignLeft
                            | qt.Qt.AlignmentFlag.AlignVCenter,
                        )
                        if diff:
                            label_diff = (
                                gui.templates.widgetgenerator.create_label(
                                    diff_text
                                )
                            )
                            if callable(text_click_func):
                                label_diff.setOpenExternalLinks(False)

                                def click_func(*args, parent=None, **kwargs):
                                    text_click_func(
                                        *args, parent=parent, **kwargs
                                    )

                                label_diff.linkActivated.connect(click_func)
                            grid_layout.addWidget(
                                label_diff,
                                row,
                                2,
                                alignment=qt.Qt.AlignmentFlag.AlignCenter
                                | qt.Qt.AlignmentFlag.AlignVCenter,
                            )
                        checkbox_0 = (
                            gui.templates.widgetgenerator.create_checkbox(
                                grid_gb, "Item0Chbx", (30, 30)
                            )
                        )
                        checkbox_0.on()
                        grid_layout.addWidget(
                            checkbox_0,
                            row,
                            3,
                            alignment=qt.Qt.AlignmentFlag.AlignCenter
                            | qt.Qt.AlignmentFlag.AlignVCenter,
                        )
                        checkbox_1 = (
                            gui.templates.widgetgenerator.create_checkbox(
                                grid_gb, "Item1Chbx", (30, 30)
                            )
                        )
                        checkbox_1.off()
                        grid_layout.addWidget(
                            checkbox_1,
                            row,
                            4,
                            alignment=qt.Qt.AlignmentFlag.AlignCenter
                            | qt.Qt.AlignmentFlag.AlignVCenter,
                        )
                        # Set the click functions
                        checkbox_0.clicked.connect(
                            functools.partial(
                                update_checks,
                                checkbox_0,
                                [checkbox_0, checkbox_1],
                                name,
                            )
                        )
                        checkbox_1.clicked.connect(
                            functools.partial(
                                update_checks,
                                checkbox_1,
                                [checkbox_0, checkbox_1],
                                name,
                            )
                        )

                        row += 1
                else:
                    layout = self.stored_gboxes[gb_key].layout()
                    label = gui.templates.widgetgenerator.create_label(
                        "No items!", bold=True
                    )
                    layout.addWidget(label)

            def check_list(lst):
                return (lst is not None) and (len(lst) > 0)

            if check_list(lists["files_modified_list"]):
                add_groupbox(
                    "files_modified",
                    "ModifiedGroupbox",
                    "Files to be modified:",
                    "The following files will be modified:",
                )
                add_files(
                    "files_modified",
                    lists["files_modified_list"],
                    "modify",
                    "don't touch",
                    True,
                )
            if check_list(lists["files_deleted_list"]):
                add_groupbox(
                    "files_deleted",
                    "DeletedGroupbox",
                    "Files to be deleted:",
                    "The following files will be deleted:",
                )
                add_files(
                    "files_deleted",
                    lists["files_deleted_list"],
                    "delete",
                    "don't touch",
                )
            if check_list(lists["files_added_list"]):
                add_groupbox(
                    "files_added",
                    "AddedGroupbox",
                    "Files to be added:",
                    "The following files will be added:",
                )
                add_files(
                    "files_added",
                    lists["files_added_list"],
                    "add",
                    "don't touch",
                )
            if check_list(lists["files_repoint_list"]):
                add_groupbox(
                    "files_repointed",
                    "RepointedGroupbox",
                    "Repointed:",
                    "The 'PROJECT LAYOUT' section in the dashboard will repoint:",
                )
                add_files(
                    "files_repointed",
                    lists["files_repoint_list"],
                    "repoint",
                    "don't touch",
                )

            create_ok_cancel_buttons()

        elif dialog_type == "missing_tool":
            # Toggle button
            self.button_toggle = (
                gui.templates.widgetgenerator.create_pushbutton(
                    parent=self,
                    name="ToggleButton",
                    size=(get_button_size(), get_button_size()),
                    checkable=True,
                )
            )
            self.button_toggle.setText(
                missing_tool_options["toggle_button_text_off"]
            )
            self.button_toggle.setStyleSheet(
                gui.stylesheets.button.get_simple_toggle_stylesheet()
            )

            def toggle(*args):
                if self.button_toggle.isChecked():
                    self.button_toggle.setText(
                        missing_tool_options["toggle_button_text_on"]
                    )
                    self.dropdown.reset()
                else:
                    self.button_toggle.setText(
                        missing_tool_options["toggle_button_text_off"]
                    )

            self.button_toggle.toggled.connect(toggle)
            self.group_layout.addWidget(self.button_toggle)

            # Second text label
            self.second_label = self._create_label(
                missing_tool_options["second_label_text"], False
            )
            self.second_label.set_colors(background_color="transparent")
            #            # linux hack for the last text line cut-off
            #            if os_checker.is_os("linux"):
            #                self.second_label.setText(self.label.text() + "\n")
            self.group_layout.addWidget(self.second_label)

            # Dropdown menu
            self.dropdown = gui.helpers.advancedcombobox.AdvancedComboBox(
                parent=self,
                initial_items=missing_tool_options["dropdown_options"],
            )

            def changed(*args) -> None:
                self.button_toggle.setChecked(False)
                return

            self.dropdown.selected_changed.connect(changed)
            self.group_layout.addWidget(self.dropdown)

            # OK button
            self.button_ok = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Ok,
                parent=self,
                text="OK",
            )
            self.button_ok.on_signal.connect(self.update_state_ok)
            self.button_ok.off_signal.connect(self.update_state_reset)

            def close_and_return(*args):
                result = {
                    "toggle_state": self.button_toggle.isChecked(),
                    "dropdown_selection": self.dropdown.get_selected_item(),
                }
                self.close_and_return(
                    (result, qt.QMessageBox.StandardButton.Ok)
                )

            self.button_ok.click_signal.connect(close_and_return)
            self.group_layout.addWidget(self.button_ok)

        elif dialog_type == "custom_buttons":
            button_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            button_layout = qt.QHBoxLayout()
            button_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            button_box.setLayout(button_layout)
            self.group_layout.addWidget(button_box)

            # Add buttons
            def custom_update_state_ok(button):
                button.on()

            def custom_update_state_reset(button):
                button.off()

            def custom_close_and_return(button):
                self.set_return_value(button.return_code)
                self.close()

            if buttons is not None and len(buttons) > 0:
                self.buttons = []
                for b in buttons:
                    text, return_code = b
                    new_button = gui.helpers.buttons.PopupDialogButton(
                        return_code, parent=self, text=text, button_padding=4
                    )
                    new_button.on_signal.connect(
                        functools.partial(custom_update_state_ok, new_button)
                    )
                    new_button.off_signal.connect(
                        functools.partial(custom_update_state_reset, new_button)
                    )
                    new_button.click_signal.connect(
                        functools.partial(custom_close_and_return, new_button)
                    )
                    button_layout.addWidget(new_button)
                    self.buttons.append(new_button)
            else:
                self.button_ok = gui.helpers.buttons.PopupDialogButton(
                    qt.QMessageBox.StandardButton.Ok,
                    parent=self,
                    text="OK",
                    button_padding=4,
                )
                self.button_ok.on_signal.connect(self.update_state_ok)
                self.button_ok.off_signal.connect(self.update_state_reset)
                self.button_ok.click_signal.connect(self.close_and_return)
                button_layout.addWidget(self.button_ok)

        elif dialog_type == "style_selector":
            if self.settings_manipulator is None:
                raise Exception("theme-and-settings manipulator must be valid!")

            # General button initialization
            self.buttons = []

            def custom_update_state_ok(button):
                button.on()

            def custom_update_state_reset(button):
                button.off()

            def custom_close_and_return(button):
                self.set_return_value(button.return_code)
                self.close()

            # Main box
            main_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            main_layout = qt.QVBoxLayout()
            main_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            main_box.setLayout(main_layout)
            self.group_layout.addWidget(main_box)

            # Theme and scale holder box
            selector_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            selector_layout = qt.QHBoxLayout()
            selector_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            selector_box.setLayout(selector_layout)
            main_layout.addWidget(selector_box)

            # Theme
            theme_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            theme_layout = qt.QVBoxLayout()
            theme_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            theme_box.setLayout(theme_layout)
            selector_layout.addWidget(theme_box)

            # Add buttons
            def adjust_theme(selected_theme):
                self.settings_manipulator.pmf_theme_set(
                    selected_theme, notify_restart_needed=False
                )
                self._init_background()
                self.label.update_style()
                for b in self.buttons:
                    b.update_style()
                self.settings_manipulator.save_settings()
                functions.center_to_current_screen(self)

            adjust_theme("Crystal")
            buttons = (
                (
                    "Crystal (Light theme) ",
                    "icons/theme/theme-crystal.svg",
                    "Crystal",
                    True,
                ),
                (
                    "Air (Light theme)",
                    "icons/theme/theme-air.svg",
                    "Air",
                    False,
                ),
                (
                    "Graphite (Dark theme) ",
                    "icons/theme/theme-graphite.svg",
                    "Graphite",
                    False,
                ),
                (
                    "Obsidian (Dark theme) ",
                    "icons/theme/theme-obsidian.svg",
                    "Obsidian",
                    False,
                ),
                (
                    "Water (Blue theme)",
                    "icons/theme/theme-water.svg",
                    "Water",
                    False,
                ),
            )
            for b in buttons:
                text, icon, name, state = b
                new_button = gui.helpers.buttons.RadioButton(
                    text=text,
                    parent=self,
                )
                new_button.setIcon(iconfunctions.get_qicon(icon))
                new_button.toggled.connect(
                    functools.partial(adjust_theme, name)
                )
                theme_layout.addWidget(new_button)
                self.buttons.append(new_button)
                new_button.setChecked(state)

            # Scale
            scale_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            scale_layout = qt.QVBoxLayout()
            scale_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            scale_box.setLayout(scale_layout)
            selector_layout.addWidget(scale_box)

            # Add buttons
            def adjust_scale(scale):
                data.global_scale = scale
                self._init_background()
                self.label.update_style()
                for b in self.buttons:
                    b.update_style()
                self.resize_and_center()
                self.settings_manipulator.save_settings()
                functions.center_to_current_screen(self)

            adjust_scale(100)
            buttons = (
                ("Small  (100%)", 100, True),
                ("Medium (125%)", 125, False),
                ("Large  (150%)", 150, False),
            )
            for b in buttons:
                text, scale, state = b
                new_button = gui.helpers.buttons.RadioButton(
                    text=text,
                    parent=self,
                )
                new_button.toggled.connect(
                    functools.partial(adjust_scale, scale)
                )
                scale_layout.addWidget(new_button)
                self.buttons.append(new_button)
                new_button.setChecked(state)

            # OK button
            bottom_box = (
                gui.templates.widgetgenerator.create_borderless_groupbox()
            )
            bottom_layout = qt.QVBoxLayout()
            bottom_layout.setAlignment(
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )
            bottom_box.setLayout(bottom_layout)
            main_layout.addWidget(bottom_box)
            ok_button = gui.helpers.buttons.PopupDialogButton(
                qt.QMessageBox.StandardButton.Ok,
                parent=self,
                text="OK",
            )
            ok_button.on_signal.connect(
                functools.partial(custom_update_state_ok, ok_button)
            )
            ok_button.off_signal.connect(
                functools.partial(custom_update_state_reset, ok_button)
            )
            ok_button.click_signal.connect(
                functools.partial(custom_close_and_return, ok_button)
            )
            bottom_layout.addWidget(ok_button)
            self.buttons.append(ok_button)

        # Set the default option according to the dialog type
        if add_textbox == True:
            if dialog_type == "ok_cancel":
                self.update_state_ok()
            elif dialog_type == "question":
                self.update_state_on()
            self.input_textbox.setFocus()
            if selected_text is not None:
                self.input_textbox.setSelection(*selected_text)

        # Adjust the size of the dialog
        # according to the size of the text
        self._reset_fixed_size()

        # Finish up the layout
        self.main_layout.addWidget(self.group_box)
        self.main_layout.setAlignment(
            self.group_box,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )
        self.main_groupbox.setLayout(self.main_layout)

        if center:

            def _adjust(*args):
                self._adjust_size()
                functions.center_to_current_screen(self)

            qt.QTimer.singleShot(50, _adjust)
        else:
            qt.QTimer.singleShot(50, self._adjust_size)
        return

    def _adjust_size(self):
        screen_size = functions.get_screen_size()
        width = self.main_groupbox.size().width() * 1.05
        height = self.main_groupbox.size().height()
        if height > (screen_size.height() * 0.90):
            height = screen_size.height() - (screen_size.height() * 0.20)

        if self.scroll_layout:
            self.resize(int(width), int(height))
            qt.QTimer.singleShot(0, self.center_to_parent)

    def set_text(self, text):
        self.label.setText(text)

    def update_state_ok(self):
        self.state = True
        self.button_ok.on()
        if self.dialog_type == "ok_cancel":
            self.button_cancel.off()

    def update_state_cancel(self):
        self.state = False
        self.button_cancel.on()
        if self.dialog_type == "ok_cancel":
            self.button_ok.off()

    def update_state_on(self):
        self.state = True
        self.button_no.off()

    def update_state_off(self):
        self.state = False
        self.button_yes.off()

    def update_state_reset(self):
        self.state = None

    def state_on(self):
        self.state = True
        self.button_no.off()
        self.button_yes.on()

    def state_off(self):
        self.state = False
        self.button_no.on()
        self.button_yes.off()

    def state_reset(self):
        self.state = None
        self.button_no.off()
        self.button_yes.off()

    def center_to_desktop(self):
        # qr = self.frameGeometry()
        # # WARNING: qt.QDesktopWidget() no longer exists in PyQt6!
        # cp = qt.QDesktopWidget().availableGeometry().center()
        # qr.moveCenter(cp)
        # self.move(qr.topLeft())

        screens = data.application.screens()
        for i, s in enumerate(screens):
            if s is data.main_form.windowHandle().screen():
                screen: qt.QScreen = data.application.primaryScreen()
                geometry = screen.geometry()
                left = geometry.left()
                top = geometry.top()
                width = geometry.width()
                height = geometry.height()
                center = qt.create_qpoint(
                    int(left + (width / 2)), int(top + (height / 2))
                )

                def move(*args):
                    self.move(center)

                qt.QTimer.singleShot(0, move)

    def center_to_parent(self):
        if data.main_form is not None:
            global_position = data.main_form.mapToGlobal(
                data.main_form.rect().center()
            )
            self.move(
                int(global_position.x() - self.width() / 2),
                int(global_position.y() - self.height() / 2),
            )

    def close_and_return(self, result):
        self.set_return_value(result)
        self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def keyPressEvent(self, key_event):
        pressed_key = key_event.key()
        # Check for escape keypress
        if pressed_key == qt.Qt.Key.Key_Escape:
            if self.dialog_type == "question" or self.dialog_type == "warning":
                self.button_no.on()
                self.repaint()
                time.sleep(0.1)
                self.close_and_return(qt.QMessageBox.StandardButton.No)
            elif self.dialog_type == "ok" or self.dialog_type == "blank":
                self.button_ok.on()
                self.repaint()
                time.sleep(0.1)
                self.close_and_return(qt.QMessageBox.StandardButton.Ok)
            elif self.dialog_type == "ok_cancel":
                self.button_cancel.on()
                self.repaint()
                time.sleep(0.1)
                self.close_and_return(qt.QMessageBox.StandardButton.Cancel)
            else:
                time.sleep(0.1)
                self.close_and_return(qt.QMessageBox.StandardButton.Cancel)
        elif pressed_key == qt.Qt.Key.Key_Right:
            if self.dialog_type == "question" or self.dialog_type == "warning":
                self.state_off()
            elif self.dialog_type == "ok_cancel":
                self.update_state_cancel()
        elif pressed_key == qt.Qt.Key.Key_Left:
            if self.dialog_type == "question" or self.dialog_type == "warning":
                self.state_on()
            elif self.dialog_type == "ok_cancel":
                self.update_state_ok()
        elif (
            pressed_key == qt.Qt.Key.Key_Enter
            or pressed_key == qt.Qt.Key.Key_Return
        ):
            if self.dialog_type == "question" or self.dialog_type == "warning":
                if self.state == True:
                    self.close_and_return(qt.QMessageBox.StandardButton.Yes)
                elif self.state == False:
                    self.close_and_return(qt.QMessageBox.StandardButton.No)
            elif self.dialog_type == "ok" or self.dialog_type == "blank":
                self.close_and_return(qt.QMessageBox.StandardButton.Ok)
            elif self.dialog_type == "ok_cancel":
                if self.state == True:
                    self.close_and_return(qt.QMessageBox.StandardButton.Ok)
                elif self.state == False:
                    self.close_and_return(qt.QMessageBox.StandardButton.Cancel)
            elif self.dialog_type == "custom_buttons":
                first_button = self.buttons[0]
                first_button.on()
                self.repaint()
                time.sleep(0.1)
                self.close_and_return(first_button.return_code)

    def set_return_value(self, value):
        self.return_value = value

    @staticmethod
    def set_static_parent(parent):
        PopupDialog.static_parent = parent

    @staticmethod
    def create_dialog(
        dialog_type,
        text,
        title_text=None,
        text_click_func=None,
        icon_path=None,
        modal_style=False,
        non_blocking=False,
        large_text=False,
        parent=None,
        scroll_layout=True,
        **kwargs,
    ):
        new_dialog = PopupDialog(
            parent,
            text,
            dialog_type,
            icon_path,
            title_text,
            text_click_func=text_click_func,
            large_text=large_text,
            scroll_layout=scroll_layout,
            **kwargs,
        )
        # Modal style or not
        if non_blocking:
            return new_dialog
        elif modal_style == True:
            new_dialog.exec()
        else:
            new_dialog.show()
            new_dialog.activateWindow()
            new_dialog.raise_()
            while new_dialog.isVisible():
                functions.process_events(delay=0.001)
        value = new_dialog.return_value
        return value

    def create_checkbox_dialog(
        dialog_type,
        text,
        title_text=None,
        icon_path=None,
        text_click_func=None,
        modal_style=False,
        files_modified_list=None,
        files_deleted_list=None,
        files_added_list=None,
        files_repoint_list=None,
        parent=None,
    ):
        new_dialog = PopupDialog(
            parent,
            text,
            dialog_type,
            icon_path,
            title_text,
            text_click_func=text_click_func,
            lists={
                "files_modified_list": files_modified_list,
                "files_deleted_list": files_deleted_list,
                "files_added_list": files_added_list,
                "files_repoint_list": files_repoint_list,
            },
        )
        # Modal style or not
        if modal_style == True:
            new_dialog.exec()
        else:
            new_dialog.show()
            new_dialog.activateWindow()
            new_dialog.raise_()
            while new_dialog.isVisible():
                functions.process_events(delay=0.001)
        value = new_dialog.return_value
        checkbox_data = new_dialog.checkbox_data
        return value, checkbox_data

    def create_missing_tool_dialog(
        dialog_type,
        text,
        title_text=None,
        icon_path=None,
        text_click_func=None,
        modal_style=False,
        missing_tool_options=None,
        parent=None,
    ):
        new_dialog = PopupDialog(
            parent,
            text,
            dialog_type,
            icon_path,
            title_text,
            text_click_func=text_click_func,
            missing_tool_options=missing_tool_options,
        )
        # Modal style or not
        if modal_style == True:
            new_dialog.exec()
        else:
            new_dialog.show()
            new_dialog.activateWindow()
            new_dialog.raise_()
            while new_dialog.isVisible():
                functions.process_events(delay=0.001)
        value = new_dialog.return_value
        return value

    @staticmethod
    def create_dialog_with_text(
        dialog_type,
        text,
        title_text=None,
        add_textbox=False,
        initial_text=None,
        text_click_func=None,
        icon_path=None,
        selected_text=None,
        modal_style=False,
        icons=None,
        large_text=False,
        parent=None,
        buttons=None,
        center=True,
        **kwargs,
    ) -> tuple[Union[str, qt.QMessageBox.StandardButton], str]:
        """

        :param dialog_type:
        :param text:
        :param title_text:
        :param add_textbox:
        :param initial_text:
        :param text_click_func:
        :param icon_path:
        :param selected_text:
        :param modal_style:
        :param icons:
        :param large_text:
        :param parent:
        :param buttons:
        :param center:
        :param kwargs:
        :return:
        """
        new_dialog = PopupDialog(
            parent,
            text,
            dialog_type,
            icon_path,
            title_text,
            add_textbox=add_textbox,
            initial_text=initial_text,
            text_click_func=text_click_func,
            selected_text=selected_text,
            icons=icons,
            large_text=large_text,
            buttons=buttons,
            center=True,
            **kwargs,
        )
        # Modal style or not
        if modal_style == True:
            new_dialog.exec()
        else:
            new_dialog.show()
            new_dialog.activateWindow()
            new_dialog.raise_()
            if add_textbox:
                new_dialog.input_textbox.setFocus()
            while new_dialog.isVisible():
                functions.process_events(delay=0.001)
        value = new_dialog.return_value
        if add_textbox:
            text = new_dialog.input_textbox.text()
        else:
            text = ""
        return value, text

    @classmethod
    def blank(cls, text, title_text=None, icon_path=None, parent=None):
        return PopupDialog.create_dialog(
            "blank",
            text,
            title_text,
            icon_path,
            parent=parent,
        )

    @classmethod
    def ok(
        cls,
        text,
        title_text=None,
        text_click_func=None,
        icon_path=None,
        non_blocking=False,
        large_text=False,
        parent=None,
    ):
        return PopupDialog.create_dialog(
            "ok",
            text,
            title_text=title_text,
            text_click_func=text_click_func,
            icon_path=icon_path,
            non_blocking=non_blocking,
            large_text=large_text,
            parent=parent,
        )

    @classmethod
    def ok_cancel(
        cls,
        text,
        title_text=None,
        add_textbox=False,
        initial_text=None,
        text_click_func=None,
        icon_path=None,
        selected_text=None,
        icons=None,
        large_text=False,
        parent=None,
    ):
        return PopupDialog.create_dialog_with_text(
            "ok_cancel",
            text,
            title_text,
            add_textbox,
            initial_text,
            text_click_func,
            icon_path,
            selected_text,
            icons=icons,
            large_text=large_text,
            parent=parent,
        )

    @classmethod
    def accept_decline(
        cls,
        text,
        title_text=None,
        add_textbox=False,
        initial_text=None,
        text_click_func=None,
        icon_path=None,
        selected_text=None,
        parent=None,
    ):
        return PopupDialog.create_dialog_with_text(
            "custom_buttons",
            text,
            title_text,
            add_textbox,
            initial_text,
            text_click_func,
            icon_path,
            selected_text,
            buttons=[
                ("DECLINE", "DECLINE"),
                ("ACCEPT", "ACCEPT"),
            ],
            modal_style=True,
            parent=parent,
            center=True,
        )

    @classmethod
    def go_back_or_continue(
        cls,
        text,
        title_text=None,
        text_click_func=None,
        icon_path=None,
        parent=None,
    ):
        return PopupDialog.create_dialog_with_text(
            "custom_buttons",
            text,
            title_text,
            False,
            None,
            text_click_func,
            icon_path,
            None,
            buttons=[
                ("GO BACK", "go_back"),
                ("CONTINUE ANYWAY", "continue"),
            ],
            modal_style=True,
            parent=parent,
        )

    @classmethod
    def custom_buttons(
        cls,
        text,
        title_text=None,
        text_click_func=None,
        icon_path=None,
        parent=None,
        buttons=None,
        **kwargs,
    ):
        return PopupDialog.create_dialog_with_text(
            "custom_buttons",
            text,
            title_text,
            False,
            None,
            text_click_func,
            icon_path,
            None,
            modal_style=True,
            parent=parent,
            buttons=buttons,
            **kwargs,
        )

    @classmethod
    def style_selector(cls, text, settings_manipulator, parent=None, **kwargs):
        return PopupDialog.create_dialog_with_text(
            "style_selector",
            text,
            title_text="Style selector",
            modal_style=True,
            parent=parent,
            settings_manipulator=settings_manipulator,
            **kwargs,
        )

    @classmethod
    def question(
        cls,
        text,
        title_text=None,
        icon_path=None,
        parent=None,
        text_click_func=None,
    ):
        return PopupDialog.create_dialog(
            "question",
            text,
            title_text,
            icon_path=icon_path,
            parent=parent,
            text_click_func=text_click_func,
            scroll_layout=False,
        )

    @classmethod
    def warning(
        cls,
        text,
        title_text=None,
        icon_path=None,
        parent=None,
        text_click_func=None,
    ):
        return PopupDialog.create_dialog(
            "warning",
            text,
            title_text,
            icon_path=icon_path,
            parent=parent,
            text_click_func=text_click_func,
        )

    @classmethod
    def error(
        cls,
        text,
        title_text=None,
        icon_path=None,
        parent=None,
        text_click_func=None,
    ):
        return PopupDialog.create_dialog(
            "error",
            text,
            title_text,
            icon_path=icon_path,
            parent=parent,
            text_click_func=text_click_func,
        )

    @classmethod
    def checkboxes(
        cls,
        text,
        title_text=None,
        icon_path=None,
        text_click_func=None,
        files_modified_list=None,
        files_deleted_list=None,
        files_added_list=None,
        files_repoint_list=None,
        parent=None,
    ):
        return PopupDialog.create_checkbox_dialog(
            "checkboxes",
            text,
            title_text,
            text_click_func=text_click_func,
            icon_path=icon_path,
            files_modified_list=files_modified_list,
            files_deleted_list=files_deleted_list,
            files_added_list=files_added_list,
            files_repoint_list=files_repoint_list,
            parent=parent,
        )

    @classmethod
    def missing_tool(
        cls,
        text,
        title_text=None,
        icon_path=None,
        text_click_func=None,
        missing_tool_options=None,
        parent=None,
    ):
        return PopupDialog.create_missing_tool_dialog(
            "missing_tool",
            text,
            title_text,
            text_click_func=text_click_func,
            icon_path=icon_path,
            missing_tool_options=missing_tool_options,
        )

    @classmethod
    def choose_file(cls, start_directory: str) -> Optional[str]:
        assert os.path.isdir(start_directory)
        dialog = qt.QFileDialog()
        dialog.setDirectory(start_directory)
        dialog.setFileMode(qt.QFileDialog.FileMode.AnyFile)
        dialog.setViewMode(qt.QFileDialog.ViewMode.List)
        filepaths = None
        if dialog.exec():
            filepaths = dialog.selectedFiles()
        if filepaths is None:
            return None
        filepath = filepaths[0]
        new_abspath = bpathlib.path_power.standardize_abspath(filepath)
        return new_abspath

    @classmethod
    def choose_folder(cls, start_directory: str) -> Optional[str]:
        assert os.path.isdir(start_directory)
        dialog = qt.QFileDialog()
        dialog.setDirectory(start_directory)
        dialog.setFileMode(qt.QFileDialog.FileMode.Directory)
        dialog.setViewMode(qt.QFileDialog.ViewMode.List)
        dirpaths = None
        if dialog.exec():
            dirpaths = dialog.selectedFiles()
        if dirpaths is None:
            return None
        dirpath = dirpaths[0]
        new_abspath = bpathlib.path_power.standardize_abspath(dirpath)
        return new_abspath

    @classmethod
    def kristof_test(cls):
        raise NotImplementedError("This was a testfunction!")
