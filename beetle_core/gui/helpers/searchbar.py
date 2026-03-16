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

import enum
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
import traceback
from typing import *

import data
import functions
import gui.forms.customeditor
import gui.stylesheets.groupbox
import gui.stylesheets.searchbar
import gui.templates.widgetgenerator
import iconfunctions
import qt


class SearchType(enum.Enum):
    Selection = "Selection"
    File = "File"
    OpenDocuments = "Open documents"
    Directory = "Directory"
    Project = "Project"
    Toolchain = "Toolchain"
    Filename = "Filename"


class SearchBar(qt.QGroupBox):
    escape_pressed = qt.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.main_form = parent
        self.setObjectName("SearchBar")
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,
            qt.QSizePolicy.Policy.Maximum,
        )
        self.setContentsMargins(0, 0, 0, 0)

        # Flags
        self.show_replace_flag = False

        # Layout
        layout: qt.QHBoxLayout = cast(
            qt.QHBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=False),
        )
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetMinimumSize)
        self.setLayout(layout)

        ## Search bar
        tooltip = "Enter search text here"
        # Frame
        self.search_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="SearchGroupBox",
                vertical=False,
                borderless=False,
                spacing=0,
                margins=(0, 0, 0, 0),
                adjust_margins_to_text=False,
                override_margin_top=0,
            )
        )
        # Textbox
        self.search_textbox = gui.templates.widgetgenerator.create_textbox(
            name="FindTextbox",
            no_border=True,
        )
        self.search_textbox.setPlaceholderText(tooltip)
        self.search_groupbox.layout().addWidget(self.search_textbox)
        self.search_groupbox.setToolTip(tooltip)
        self.search_groupbox.setStatusTip(tooltip)
        # Add search groupbox to search bar
        layout.addWidget(self.search_groupbox)

        # Small padding
        layout.addSpacing(1)

        ## Next/ previous buttons
        button_side_length = data.get_custom_tab_pixelsize()
        # Button groupbox
        self.updown_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="ButtonGroupBox",
                vertical=False,
                borderless=True,
                spacing=0,
                margins=(0, 0, 0, 0),
            )
        )
        self.updown_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        self.updown_groupbox.layout().setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )

        # Previous button
        def previous_function():
            self.search(direction="prev")

        self.previous_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="previous-button",
            tooltip="Find previous occurrence",
            icon_name="icons/arrow/triangle/triangle_up.png",
            size=(button_side_length, button_side_length),
            click_func=previous_function,
            no_border=True,
        )
        self.previous_button.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.updown_groupbox.layout().addWidget(self.previous_button)

        # Next button
        def next_function():
            self.search(direction="next")

        self.next_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="next-button",
            tooltip="Find next occurrence",
            icon_name="icons/arrow/triangle/triangle_down.png",
            size=(button_side_length, button_side_length),
            click_func=next_function,
            no_border=True,
        )
        self.next_button.setObjectName("#SearchBarNextButton")
        self.next_button.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.updown_groupbox.layout().addWidget(self.next_button)

        # All button
        def all_function():
            self.search(direction="all")

        self.all_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="all-button",
            tooltip="Find all occurrences",
            icon_name="icons/arrow/triangle/triangle_three_down.png",
            size=(button_side_length, button_side_length),
            click_func=all_function,
            no_border=True,
        )
        self.all_button.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Expanding,
        )
        self.updown_groupbox.layout().addWidget(self.all_button)
        # Add button groupbox to search bar
        layout.addWidget(self.updown_groupbox)
        layout.addSpacing(10)

        # Connect the find next to the enter press of the search textbox
        def enter_press():
            modifiers = data.application.keyboardModifiers()
            if modifiers == qt.Qt.KeyboardModifier.ControlModifier:
                previous_function()
            else:
                next_function()

        self.search_textbox.returnPressed.connect(enter_press)

        # Connect the text changed signal to do incremental search forward
        def text_changed(new_text):
            valid_types = (
                SearchType.Selection,
                SearchType.File,
                SearchType.OpenDocuments,
            )
            if (
                self.get_type() in valid_types
                and not self.replace_groupbox.isVisible()
            ):
                self.search(incremental=True)

        self.search_textbox.textChanged.connect(text_changed)

        ## Checkboxes
        # Groupbox
        self.checkbox_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="ButtonGroupBox",
                vertical=False,
                borderless=True,
                spacing=3,
                margins=(3, 0, 3, 0),
            )
        )
        self.checkbox_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Preferred,
            qt.QSizePolicy.Policy.Expanding,
        )
        # Add button groupbox to search bar
        layout.addWidget(self.checkbox_groupbox)
        layout.addSpacing(10)
        # Highlight all
        self.button_highlight_all = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="highlight_all",
                tooltip="The search text will also be highlighted",
                icon_name="icons/searchbar/marker.png",
                size=(button_side_length, button_side_length),
                checkable=True,
                no_border=True,
            )
        )

        def highlight_check_changed(toggled):
            valid_types = (
                SearchType.Selection,
                SearchType.File,
                SearchType.OpenDocuments,
            )
            if (
                self.get_type() in valid_types
                and not self.replace_groupbox.isVisible()
            ):
                if not toggled:
                    widget = self.main_form.get_tab_by_indication()
                    if widget is not None and isinstance(
                        widget, gui.forms.customeditor.CustomEditor
                    ):
                        widget.clear_highlights()
                else:
                    self.search(only_highlight=True)

        self.button_highlight_all.toggled.connect(highlight_check_changed)
        self.checkbox_groupbox.layout().addWidget(self.button_highlight_all)
        # Case sensitivity
        self.button_case_sensitive = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="case_sensitive",
                tooltip="The search text will be treated with case sensitivity",
                icon_name="icons/searchbar/case_sensitive.png",
                size=(button_side_length, button_side_length),
                checkable=True,
                no_border=True,
            )
        )

        def case_check_changed(toggled):
            valid_types = (
                SearchType.Selection,
                SearchType.File,
                SearchType.OpenDocuments,
            )
            if (
                self.get_type() in valid_types
                and not self.replace_groupbox.isVisible()
            ):
                self.search(incremental=True)

        self.button_case_sensitive.toggled.connect(case_check_changed)
        self.checkbox_groupbox.layout().addWidget(self.button_case_sensitive)
        # Regex
        self.button_regex = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="regex",
            tooltip="The search text will be treated as a regular expression",
            icon_name="icons/searchbar/regex.png",
            size=(button_side_length, button_side_length),
            checkable=True,
            no_border=True,
        )
        self.checkbox_groupbox.layout().addWidget(self.button_regex)

        ## Replace bar
        tooltip = "Enter replace text here"
        # Frame
        self.replace_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="replaceGroupBox",
                vertical=False,
                borderless=False,
                spacing=0,
                margins=(0, 0, 0, 0),
                adjust_margins_to_text=False,
                override_margin_top=0,
            )
        )
        # Icon
        self.replace_image = gui.templates.widgetgenerator.create_label(
            image="icons/searchbar/pencil.png"
        )
        self.replace_groupbox.layout().addWidget(self.replace_image)
        # Textbox
        self.replace_textbox = gui.templates.widgetgenerator.create_textbox(
            "ReplaceTextbox",
            no_border=True,
        )
        self.replace_textbox.setPlaceholderText(f"Replace text")
        self.replace_groupbox.layout().addWidget(self.replace_textbox)
        self.replace_groupbox.setToolTip(tooltip)
        self.replace_groupbox.setStatusTip(tooltip)
        # Add replace groupbox to search bar
        layout.addWidget(self.replace_groupbox)
        self.replace_groupbox.setVisible(False)

        # Small padding
        layout.addSpacing(1)

        ## Replace buttons
        # Button groupbox
        self.replace_updown_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="ButtonGroupBox",
                vertical=False,
                borderless=True,
                spacing=0,
                margins=(0, 0, 0, 0),
            )
        )
        self.replace_updown_groupbox.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Minimum,
        )
        self.replace_updown_groupbox.layout().setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )

        # Next button
        def replace_next_function():
            self.replace(direction="next")

        self.replace_next_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="next-button",
                tooltip="Replace next occurrence",
                icon_name="icons/arrow/triangle/triangle_down.png",
                size=(button_side_length, button_side_length),
                click_func=replace_next_function,
                no_border=True,
            )
        )
        self.replace_updown_groupbox.layout().addWidget(
            self.replace_next_button
        )
        # Add button groupbox to replace bar
        layout.addWidget(self.replace_updown_groupbox)

        # All button
        def replace_all_function():
            self.replace(direction="all")

        self.replace_all_button = (
            gui.templates.widgetgenerator.create_pushbutton(
                parent=self,
                name="all-button",
                tooltip="Replace all occurrences",
                icon_name="icons/arrow/triangle/triangle_three_down.png",
                size=(button_side_length, button_side_length),
                click_func=replace_all_function,
                no_border=True,
            )
        )
        self.replace_updown_groupbox.layout().addWidget(self.replace_all_button)

        # Spacing
        layout.addSpacing(1)

        # Type combobox
        search_types = [
            {
                "name": SearchType.Selection.value,
                "widgets": ({"type": "text", "text": "Selection"},),
                "tooltip": "Search in selection",
            },
            {
                "name": SearchType.File.value,
                "widgets": ({"type": "text", "text": "File"},),
                "tooltip": "Search in the currently focused file",
            },
            {
                "name": SearchType.OpenDocuments.value,
                "widgets": ({"type": "text", "text": "Open documents"},),
                "tooltip": "Search in all open documents",
            },
            {
                "name": SearchType.Directory.value,
                "widgets": ({"type": "text", "text": "Directory"},),
                "tooltip": "Search in a selected directory",
            },
            {
                "name": SearchType.Project.value,
                "widgets": ({"type": "text", "text": "Project"},),
                "tooltip": "Search in the project directory",
            },
            {
                "name": SearchType.Toolchain.value,
                "widgets": ({"type": "text", "text": "Toolchain"},),
                "tooltip": "Search in the compiler toolchain directory",
            },
            {
                "name": SearchType.Filename.value,
                "widgets": ({"type": "text", "text": "Filename"},),
                "tooltip": "Search for files in a specific directory",
            },
        ]
        self.type_box = gui.templates.widgetgenerator.create_advancedcombobox(
            parent=self,
            initial_item="File",
            initial_items=search_types,
            contents_margins=(0, 0, 0, 0),
            spacing=0,
            image_size=data.get_custom_tab_pixelsize(),
        )
        self.type_box.selection_changed.connect(self.__type_changed)
        self.setStatusTip("Select where to search in")
        self.type_box.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum,
            qt.QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.type_box)
        layout.setAlignment(self.type_box, qt.Qt.AlignmentFlag.AlignVCenter)

        # Spacing
        layout.addSpacing(10)

        # Message label
        self.message_label = gui.templates.widgetgenerator.create_label(
            text="", bold=False
        )
        self.message_label.setStyleSheet(
            gui.stylesheets.label.get_default(transparent=True)
        )
        layout.addWidget(self.message_label)

        # Wait animation
        self.animation_wait = qt.QLabel()
        self.animation_wait.setAttribute(
            qt.Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        movie = qt.QMovie(
            iconfunctions.get_icon_abspath(
                "icons/loading_animation/hourglass_animation/hourglass.gif"
            )
        )
        self.animation_wait.setMovie(movie)
        movie.start()
        self.animation_wait.setScaledContents(True)
        self.animation_wait.setVisible(False)
        layout.addWidget(self.animation_wait)

        # Padding
        layout.addStretch(1)

        ## Close button
        def close_function():
            self.hide()

        self.close_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="close_button",
            tooltip="Hide the search bar",
            icon_name="icons/arrow/chevron/chevron_down.png",
            size=(
                data.get_custom_tab_pixelsize(),
                data.get_custom_tab_pixelsize(),
            ),
            click_func=close_function,
            no_border=True,
        )
        self.close_button.visible = True
        #        self.close_button.setObjectName("close-button")
        self.close_button.setToolTip("Hide the search bar")
        layout.addWidget(self.close_button)

        self.update_style()

        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == qt.QEvent.Type.KeyPress:
            # Key press
            key = event.key()
            modifiers = event.modifiers()
            if key == qt.Qt.Key.Key_Escape:
                self.escape_pressed.emit()

        return False

    def display_message(self, message, msec=None):
        self.message_label.setText(message)
        if isinstance(msec, int) and msec > 0:
            qt.QTimer.singleShot(msec, lambda: self.message_label.setText(""))

    def __type_changed(self):
        self.set_search_type()

    def update_style(self):
        self.setStyleSheet(
            gui.stylesheets.searchbar.get_default("SearchBar", no_border=True)
        )
        self.search_groupbox.setStyleSheet(
            gui.stylesheets.groupbox.get_default(no_border=True)
        )
        self.replace_groupbox.setStyleSheet(
            gui.stylesheets.groupbox.get_default(no_border=True)
        )
        button_side_length = data.get_custom_tab_pixelsize()
        button_side_length_adjusted = button_side_length * 1.1
        new_size = (button_side_length_adjusted, button_side_length_adjusted)
        self.next_button.update_style(new_size)
        self.next_button.setFixedHeight(int(button_side_length_adjusted))
        self.previous_button.update_style(new_size)
        self.previous_button.setFixedHeight(int(button_side_length_adjusted))
        self.all_button.update_style(new_size)
        self.all_button.setFixedHeight(int(button_side_length_adjusted))
        self.button_highlight_all.update_style(new_size)
        self.button_case_sensitive.update_style(new_size)
        self.button_regex.update_style(new_size)
        self.close_button.update_style()
        self.close_button.setFixedSize(
            int(button_side_length), int(button_side_length)
        )
        size = data.get_general_font_pointsize() * 2
        textbox_width = functions.get_text_width("0" * 40)
        self.search_textbox.setFixedWidth(textbox_width)
        self.search_textbox.update_style()
        self.updown_groupbox.adjustSize()
        self.replace_updown_groupbox.adjustSize()
        self.updown_groupbox.update_style()
        self.replace_updown_groupbox.update_style()
        self.replace_textbox.setFixedWidth(textbox_width)
        self.replace_textbox.update_style()
        self.replace_image.setFixedSize(int(size), int(size))
        self.replace_image.setStyleSheet(
            f"background-color: {data.theme['fonts']['default']['background']};"
        )
        self.replace_next_button.setFixedHeight(
            int(button_side_length_adjusted)
        )
        self.replace_next_button.update_style(new_size)
        self.replace_all_button.setFixedHeight(int(button_side_length_adjusted))
        self.replace_all_button.update_style(new_size)

        self.type_box.update_style()

        self.message_label.update_style()
        self.animation_wait.setFixedSize(int(size), int(size))

        self.adjustSize()

    def show(self, show_replace=False):
        super().show()
        self.show_replace_flag = show_replace
        self.set_search_type()

    def hide(self):
        super().hide()
        widget = self.main_form.get_tab_by_indication()
        if widget is not None:
            widget.setFocus()
            if hasattr(widget, "clear_highlights"):
                widget.clear_highlights()

    def __repolish(self):
        self.search_textbox.style().unpolish(self.search_textbox)
        self.search_textbox.style().polish(self.search_textbox)
        self.search_textbox.update()

    def nothing_found_set(self):
        self.search_textbox.setProperty("background_lightred", True)
        self.__repolish()
        self.display_message("Nothing found!")

    def nothing_found_reset(self):
        self.search_textbox.setProperty("background_lightred", False)
        self.__repolish()
        self.display_message("")

    def set_search_type(self):
        _type = self.get_type()
        self.search_textbox.setFocus()

        # Initial search text
        tab = self.main_form.get_tab_by_indication()
        if (
            tab
            and isinstance(tab, gui.forms.customeditor.CustomEditor)
            and _type != SearchType.Selection
        ):
            if tab.hasSelectedText():
                selected_text = tab.selectedText()
                self.search_textbox.setText(selected_text)
        self.search_textbox.selectAll()

        def set_visibility(
            # Search
            search_textbox: bool,
            previous_button: bool,
            next_button: bool,
            all_button: bool,
            # Checkboxes
            button_highlight_all: bool,
            button_case_sensitive: bool,
            button_regex: bool,
            # Replace
            replace_textbox: bool,
            replace_next_button: bool,
            replace_all_button: bool,
        ) -> None:
            # Search
            self.search_textbox.setVisible(search_textbox)
            self.previous_button.setVisible(previous_button)
            self.next_button.setVisible(next_button)
            self.all_button.setVisible(all_button)
            # Checkboxes
            self.button_highlight_all.setVisible(button_highlight_all)
            self.button_case_sensitive.setVisible(button_case_sensitive)
            self.button_regex.setVisible(button_regex)
            # Replace
            self.replace_textbox.setVisible(replace_textbox)
            self.replace_next_button.setVisible(replace_next_button)
            self.replace_all_button.setVisible(replace_all_button)

        if _type == SearchType.Selection:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=False,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=False,
                replace_all_button=True,
            )
        elif _type == SearchType.File:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=True,
                next_button=True,
                all_button=True,
                # Checkboxes
                button_highlight_all=True,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        elif _type == SearchType.OpenDocuments:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=True,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        elif _type == SearchType.Directory:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=False,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        elif _type == SearchType.Project:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=False,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        elif _type == SearchType.Toolchain:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=False,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        elif _type == SearchType.Filename:
            set_visibility(
                # Search
                search_textbox=True,
                previous_button=False,
                next_button=False,
                all_button=True,
                # Checkboxes
                button_highlight_all=False,
                button_case_sensitive=True,
                button_regex=True,
                # Replace
                replace_textbox=True,
                replace_next_button=True,
                replace_all_button=True,
            )
        else:
            raise Exception(f"[SearchBar] Unknown search type: {_type}")

        non_replacable = (
            SearchType.OpenDocuments,
            SearchType.Directory,
            SearchType.Project,
            SearchType.Toolchain,
        )
        if self.show_replace_flag == True and not (_type in non_replacable):
            self.replace_groupbox.setVisible(True)
            self.replace_updown_groupbox.setVisible(True)
            self.replace_textbox.setFocus()
        else:
            self.replace_groupbox.setVisible(False)
            self.replace_updown_groupbox.setVisible(False)

    def _test_search_text(self):
        search_text = self.search_textbox.text()
        if search_text == "":
            return False
        return True

    def get_type(self):
        return SearchType(self.type_box.get_selected_item_name())

    def get_flags(self):
        result = {
            "highlight_all": self.button_highlight_all.isChecked(),
            "case_sensitivity": self.button_case_sensitive.isChecked(),
            "regex": self.button_regex.isChecked(),
        }
        return result

    def search(self, direction="next", incremental=False, only_highlight=False):
        self.nothing_found_reset()

        _type = self.get_type()
        if _type == SearchType.Selection:
            self._search_in_selection()
        elif _type == SearchType.File:
            self._search_in_file(direction, incremental, only_highlight)
        elif _type == SearchType.OpenDocuments:
            self._search_in_open_documents(
                direction, incremental, only_highlight
            )
        elif _type == SearchType.Directory:
            self._search_in_directory(
                search_type=SearchType.Directory,
            )
        elif _type == SearchType.Project:
            project_directory = functions.unixify_path_join(
                data.current_project.get_proj_rootpath(),
            )
            self._search_in_directory(
                search_type=SearchType.Directory,
                search_directory=project_directory,
                exclude_directories=(
                    ".beetle",
                    "build",
                ),
            )
        elif _type == SearchType.Toolchain:
            toolchain_directory = functions.unixify_path(
                os.path.dirname(
                    data.current_project.get_toolpath_seg().get_abspath(
                        "COMPILER_TOOLCHAIN"
                    )
                )
            )
            if toolchain_directory:
                self._search_in_directory(
                    search_type=SearchType.Directory,
                    search_directory=toolchain_directory,
                )
            else:
                self.display_message(
                    "The Toolchain path is not set! Check if there "
                    + "is a tool selected."
                )
        elif _type == SearchType.Filename:
            self._search_in_directory(
                search_type=SearchType.Filename,
            )

    def _search_in_selection(self):
        widget = self.main_form.get_tab_by_indication()
        if not isinstance(widget, gui.forms.customeditor.CustomEditor):
            self.display_message(
                "The window you are trying to search in "
                + "doesn't have search functionality!"
            )
            return
        search_text = self.search_textbox.text()
        flags = self.get_flags()
        # Checks
        sel_line_from, sel_index_from, sel_line_to, sel_index_to = (
            widget.getSelection()
        )
        if (
            sel_line_from == -1
            and sel_index_from == -1
            and widget.background_selection is None
        ):
            self.display_message("No text selected!")
            return
        if widget.background_selection:
            sel_line_from, sel_index_from, sel_line_to, sel_index_to = (
                widget.background_selection
            )
        index_from = widget.positionFromLineIndex(sel_line_from, sel_index_from)
        index_to = widget.positionFromLineIndex(sel_line_to, sel_index_to)
        # Paint the background
        widget.set_indicator("background_selection")
        widget.background_selection = (
            sel_line_from,
            sel_index_from,
            sel_line_to,
            sel_index_to,
        )
        widget.highlight_raw((widget.background_selection,))
        widget.setCursorPosition(sel_line_to, sel_index_to)
        # Reset highlighting
        widget.clear_highlight_indicator()
        # Search
        matches = widget.find_all(
            self.search_textbox.text(),
            case_sensitive=flags["case_sensitivity"],
            regular_expression=flags["regex"],
            text_range=(index_from, index_to),
        )
        adjusted_matches = []
        for m in matches:
            adjusted_matches.append(
                (m[0], m[1] + index_from, m[2], m[3] + index_from)
            )
        if len(adjusted_matches) > 0:
            widget.set_indicator("highlight")
            widget.highlight_raw(adjusted_matches)
            self.display_message("")
        else:
            self.nothing_found_set()

    def _search_in_file(self, direction, incremental, only_highlight):
        widget = self.main_form.get_tab_by_indication()
        widget_tab_name = self.main_form.get_tabname_by_indication()
        if widget is None:
            self.display_message("No selected window!")
            return
        if isinstance(widget, gui.forms.customeditor.CustomEditor):
            widget.clear_highlights()
            if self._test_search_text() == False:
                if widget.hasSelectedText():
                    widget.set_cursor_to_start_of_selection()
                    self.main_form.display.write_to_statusbar(
                        "Enter search text!"
                    )
                return
            search_text = self.search_textbox.text()
            flags = self.get_flags()
            backward = False
            if direction == "prev":
                backward = True
            if not only_highlight:
                try:
                    if direction == "all":
                        pass
                    else:
                        result = widget.find_text(
                            search_text,
                            case_sensitive=flags["case_sensitivity"],
                            search_forward=not (backward),
                            regular_expression=flags["regex"],
                            incremental=incremental,
                        )
                        if result is None:
                            self.nothing_found_set()
                except Exception as ex:
                    self.main_form.display.display_error(str(ex))
                    return
            if flags["highlight_all"] or direction == "all":
                matches = widget.find_all(
                    search_text,
                    flags["case_sensitivity"],
                    flags["regex"],
                    text_to_bytes=True,
                )
                if matches:
                    if flags["highlight_all"]:
                        widget.set_indicator("highlight")
                        widget.highlight_raw(matches)

                    if direction == "all":
                        # Convert matches to (line, index)
                        line_matches = []
                        for m in matches:
                            line_fr, index_fr = widget.lineIndexFromPosition(
                                m[1]
                            )
                            line_to, index_to = widget.lineIndexFromPosition(
                                m[3]
                            )
                            line = widget.text(line_fr)
                            line_matches.append(
                                (
                                    line_fr,
                                    index_fr,
                                    line_to,
                                    index_to,
                                    "'" + line + "'",
                                )
                            )
                        result = (
                            search_text,
                            widget.save_name,
                            line_matches,
                            widget,
                        )
                        self.main_form.display.show_search_results(
                            (result,), _type=SearchType.File
                        )
        else:
            message = "The {} window does not have search functionality".format(
                widget_tab_name
            )
            self.display_message(message)

    def _search_in_open_documents(self, direction, incremental, only_highlight):
        search_text = self.search_textbox.text()
        flags = self.get_flags()
        if direction == "all":
            matches = []
            editors = self.main_form.get_all_editors()
            for e in editors:
                match = e.find_all(
                    search_text,
                    flags["case_sensitivity"],
                    flags["regex"],
                    text_to_bytes=True,
                )
                line_matches = []
                for m in match:
                    line_fr, index_fr = e.lineIndexFromPosition(m[1])
                    line_to, index_to = e.lineIndexFromPosition(m[3])
                    line = e.text(line_fr)
                    line_matches.append(
                        (line_fr, index_fr, line_to, index_to, line)
                    )
                result = (
                    search_text,
                    e.save_name,
                    line_matches,
                    e,
                )
                matches.append(result)
            self.main_form.display.show_search_results(
                matches, _type=SearchType.File
            )
        else:
            self.main_form.editing.find_in_open_documents(
                search_text,
                flags["case_sensitivity"],
                flags["regex"],
            )

    def __set_enabled(self, state: bool) -> None:
        self.setEnabled(state)
        self.animation_wait.setVisible(not state)

    def _search_in_directory(
        self,
        search_type=SearchType.Directory,
        search_directory=None,
        exclude_directories=[],
    ):
        search_text = self.search_textbox.text()
        if search_text == "":
            self.display_message("No search text!")
            return
        flags = self.get_flags()
        if search_directory is None:
            search_directory = self.main_form._get_directory_with_dialog()
        # Check search directory
        if search_directory.strip() == "" or search_directory is None:
            return
        elif not os.path.isdir(search_directory):
            print(f"[SearchBar] Invalid directory: {search_directory}")
            self.display_message("Invalid directory!")
            return
        # Execute search
        self.__set_enabled(False)
        self.searcher = Searcher(
            self,
            search_type,
            search_text,
            search_directory,
            flags["case_sensitivity"],
            flags["regex"],
            exclude_directories=exclude_directories,
        )
        self.searcher.start()

    @qt.pyqtSlot(dict)
    def _directory_search_complete(self, search_results):
        try:
            self.main_form.display.show_search_results(
                search_results, _type=SearchType.Directory
            )
        finally:
            self.__set_enabled(True)

    @qt.pyqtSlot(dict)
    def _filename_search_complete(self, search_results):
        try:
            self.main_form.display.show_search_results(
                search_results, _type=SearchType.Filename
            )
        finally:
            self.__set_enabled(True)

    @qt.pyqtSlot(str)
    def _error_search_complete(self, error_message):
        try:
            self.display_message(f"Error: {error_message}")
        finally:
            self.__set_enabled(True)

    def replace(self, direction: str) -> None:
        _type = self.get_type()
        if _type == SearchType.Selection:
            self._replace_in_selection(direction)
        elif _type == SearchType.File:
            self._replace_in_file(direction)
        elif _type == SearchType.OpenDocuments:
            pass
        elif _type == SearchType.Directory:
            pass
        elif _type == SearchType.Project:
            pass
        return

    def _replace_in_selection(self, direction: str) -> None:
        widget = self.main_form.get_tab_by_indication()
        if widget is None or not isinstance(
            widget, gui.forms.customeditor.CustomEditor
        ):
            return
        search_text = self.search_textbox.text()
        replace_text = self.replace_textbox.text()
        flags = self.get_flags()
        if not self._test_search_text():
            self.main_form.display.write_to_statusbar(
                "Please enter search text!"
            )
            return
        if direction == "all":
            try:
                widget.replace_in_selection(
                    search_text=search_text,
                    replace_text=replace_text,
                    case_sensitive=flags["case_sensitivity"],
                    regular_expression=flags["regex"],
                )
                self.display_message("")
            except:
                self.main_form.display.display_error(traceback.format_exc())
                self.display_message(
                    "Error while replacing!!! Check messages window."
                )
        return

    def _replace_in_file(self, direction: str) -> None:
        """"""
        widget = self.main_form.get_tab_by_indication()
        if widget is None or not isinstance(
            widget, gui.forms.customeditor.CustomEditor
        ):
            return
        search_text = self.search_textbox.text()
        replace_text = self.replace_textbox.text()
        flags = self.get_flags()
        if not self._test_search_text():
            self.main_form.display.write_to_statusbar(
                "Please enter search text!"
            )
            return
        if direction == "next":
            if widget.hasSelectedText():
                widget.set_cursor_to_start_of_selection()
            try:
                result = widget.find_and_replace(
                    search_text=search_text,
                    replace_text=replace_text,
                    case_sensitive=flags["case_sensitivity"],
                    search_forward=not direction,
                    regular_expression=flags["regex"],
                )
                self.display_message("")
            except:
                self.main_form.display.display_error(traceback.format_exc())
                self.display_message(
                    "Error while replacing!!! Check messages window."
                )

        elif direction == "all":
            try:
                widget.replace_all(
                    search_text=search_text,
                    replace_text=replace_text,
                    case_sensitive=flags["case_sensitivity"],
                    regular_expression=flags["regex"],
                )
                self.display_message("")
            except:
                self.main_form.display.display_error(traceback.format_exc())
                self.display_message(
                    "Error while replacing!!! Check messages window."
                )
        return


# Standalone function to run in separate process
def _run_search_in_process(
    search_type,
    search_text,
    search_directory,
    case_sensitivity,
    regex_search,
    exclude_directories,
    result_queue,
):
    """This function runs in a separate process."""
    try:
        if search_type == SearchType.Directory.value:
            search_results = functions.index_strings_in_files(
                search_text,
                search_directory,
                case_sensitivity,
                regex_search,
                text_to_bytes=True,
                exclude_directories=exclude_directories,
            )
            result_queue.put(("directory", search_results))
        elif search_type == SearchType.Filename.value:
            search_results = functions.find_files_by_name(
                search_text=search_text,
                search_dir=search_directory,
                case_sensitive=case_sensitivity,
                regex_search=regex_search,
                search_subdirs=True,
            )
            # Build nested result structure
            result = {
                "path": search_directory,
                "search-text": search_text,
                "directories": {},
                "files": [],
            }
            for file in search_results:
                current_directory = result
                removed_path = functions.unixify_path_remove(
                    file, search_directory
                )
                split_path = functions.split_all_path_items(removed_path)
                for item in split_path[:-1]:
                    if item not in current_directory["directories"]:
                        current_directory["directories"][item] = {
                            "path": functions.unixify_path_join(
                                search_directory,
                                *split_path[: split_path.index(item) + 1],
                            ),
                            "directories": {},
                            "files": [],
                        }
                    current_directory = current_directory["directories"][item]
                current_directory["files"].append(split_path[-1])
            result_queue.put(("filename", result))
        else:
            raise ValueError(f"Unknown search type: {search_type}")
    except Exception:
        # Send error info if needed, or just skip
        print("[Searcher Process] Error:")
        traceback.print_exc()
        result_queue.put(("error", {}))


# Constants for Windows console suppression
CREATE_NO_WINDOW = 0x08000000


# --- Helper Function to Build Ripgrep Args (re-used from previous answer) ---
def _build_ripgrep_args(
    search_text: str,
    search_directory: str,
    case_sensitivity: bool,
    regex_search: bool,
    exclude_directories: list[str],
) -> list[str]:
    """
    Builds the ripgrep command line arguments, using '--glob' negation
    to handle directory exclusions for older ripgrep versions.
    """
    command = ["rg", "--json", "--no-require-git"]

    if not case_sensitivity:
        command.append("-i")  # Ignore case

    if regex_search:
        command.append("-E")  # Treat pattern as an extended regular expression

    # Use negative globs to exclude directories (compatible with more versions)
    for directory in exclude_directories:
        if directory:
            # The pattern is: !directoryname/**
            exclude_pattern = f"!{directory}/**"
            command.extend(["--glob", exclude_pattern])

    # Search Pattern and Path
    command.append(search_text)
    command.append(search_directory)

    return command


def _run_ripgrep_in_process(
    search_text: str,
    search_directory: str,
    case_sensitivity: bool,
    regex_search: bool,
    exclude_directories: list[str],
    result_queue: multiprocessing.Queue,
):
    """
    Runs ripgrep in a separate process, parses the JSON output into a tree structure
    and sends the result back via the multiprocessing Queue.

    Match objects are structured as: [line_number, start_index, line_number, end_index, match_text]
    """
    # Initialize the result structure with 'files': {} (a dictionary)
    result: Dict[str, Any] = {
        "path": (
            os.path.abspath(search_directory).replace("\\", "/")
        ),  # Use Unix paths for consistency
        "search-text": search_text,
        "directories": {},
        "files": {},  # Dictionary for files
    }

    try:
        # NOTE: _build_ripgrep_args is required here
        command = _build_ripgrep_args(
            search_text,
            search_directory,
            case_sensitivity,
            regex_search,
            exclude_directories,
        )

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= CREATE_NO_WINDOW

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            startupinfo=startupinfo,
            encoding="utf-8",
        )

        if process.returncode > 1:
            error_message = f"Ripgrep Error (Code {process.returncode}): {process.stderr.strip()}"
            print(error_message)
            result_queue.put(("error", error_message))
            return

        # Prepare base directory path for calculating relative paths
        base_dir = os.path.abspath(search_directory).replace("\\", "/")
        if not base_dir.endswith("/"):
            base_dir += "/"

        # Parse the JSON Lines output and build the tree
        for line in process.stdout.splitlines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if data["type"] == "match":
                match = data["data"]

                # Ripgrep paths are relative to the search directory, normalize to Unix path
                relative_path = match["path"]["text"].replace("\\", "/")
                line_number = match.get("line_number", 0)
                # Line indexes are 0-based
                line_number -= 1

                # --- NEW LOGIC: Iterate over submatches ---
                submatches = match.get("submatches", [])

                for submatch in submatches:

                    # Extract start/end indices and match text from the submatch data
                    # These indices are 0-based byte offsets relative to the start of the line.
                    start_index = submatch.get("start", 0)
                    end_index = submatch.get("end", 0)

                    # ripgrep provides the match text directly in the submatch structure
                    match_text = submatch["match"]["text"]

                    # Construct the required match object: [line_number, start_index, line_number, end_index, match_text]
                    # Note: We repeat line_number twice as per your requested format.
                    match_object = [
                        line_number,
                        start_index,
                        line_number,
                        end_index,
                        match_text,
                    ]

                    # --- END NEW LOGIC ---

                    # Split the relative path for traversal
                    parts = relative_path.split("/")

                    # Navigate/create the tree structure for this match
                    current_node = result
                    current_path_parts = []

                    for i, part in enumerate(parts):
                        is_file = i == len(parts) - 1

                        if is_file:
                            filename = part

                            # Add match to the file's list of matches
                            if filename not in current_node["files"]:
                                current_node["files"][filename] = []

                            current_node["files"][filename].append(match_object)
                            break

                        else:
                            # Directory traversal/creation
                            current_path_parts.append(part)

                            if part not in current_node["directories"]:
                                full_dir_path = "/".join(current_path_parts)

                                current_node["directories"][part] = {
                                    "path": full_dir_path,
                                    "directories": {},
                                    "files": {},
                                }
                            current_node = current_node["directories"][part]

        # Send the final successful result back
        result_queue.put(("directory", result))

    except Exception:
        print("[Ripgrep Process] Fatal Error:")
        traceback.print_exc()
        # Send a general error message back
        result_queue.put(
            (
                "error",
                "A fatal internal error occurred during ripgrep execution.",
            )
        )


def _build_grep_args(
    grep_executable: str,
    search_text: str,
    search_directory: str,
    case_sensitivity: bool,
    regex_search: bool,
    exclude_directories: list[str],
) -> list[str]:
    """
    Builds the 'grep' command to extract file path, line number, and full matching line.
    """
    # Use -r for recursive, -n for line number, -E for extended regex,
    # and --with-filename to ensure file name is always printed.
    command = [grep_executable, "-r", "-n", "-Z", "--with-filename"]

    if regex_search:
        command.append("-E")
    else:
        # Use -F for fixed strings if not using regex (faster/more accurate)
        command.append("-F")

    if not case_sensitivity:
        command.append("-i")  # Ignore case

    # Exclusions: Grep requires '--exclude-dir' for directory exclusion (GNU grep)
    for directory in exclude_directories:
        command.extend(["--exclude-dir", directory])

    # Search Pattern and Path
    command.append(search_text)
    command.append(search_directory)

    return command


def _run_grep_in_process(
    search_text: str,
    search_directory: str,
    case_sensitivity: bool,
    regex_search: bool,
    exclude_directories: list[str],
    result_queue: multiprocessing.Queue,
):
    """
    Runs grep, parses its plaintext output for file path, line number, and match text
    (the full line), and organizes results into the directory tree structure.

    Match objects are structured as: [line_number, match_text]
    """
    result: Dict[str, Any] = {
        "path": os.path.abspath(search_directory).replace("\\", "/"),
        "search-text": search_text,
        "directories": {},
        "files": {},
    }

    # Set up subprocess info
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= CREATE_NO_WINDOW

    try:
        # --- NEW: Locate Grep and Fallback ---
        grep_path = shutil.which("grep")
        print(os.getenv("PATH"))
        if not grep_path:
            error_message = "Grep executable not found in system PATH. Ensure Grep is installed and accessible."
            print(error_message)
            result_queue.put(("error", error_message))
            return

        # ===================================================================
        # STEP 1: Execute Grep Command
        # ===================================================================

        # Build arguments list without the "grep" command name
        command_list = _build_grep_args(
            grep_path,
            search_text,
            search_directory,
            case_sensitivity,
            regex_search,
            exclude_directories,
        )

        process = subprocess.run(
            command_list,  # Pass the list of arguments
            capture_output=True,
            text=True,
            check=False,
            startupinfo=startupinfo,
            encoding="utf-8",
            shell=False,  # Explicitly use shell=False for safety
        )

        if process.returncode > 1:
            error_message = f"Grep Error (Code {process.returncode}): {process.stderr.strip()}"
            print(error_message)
            result_queue.put(("error", error_message))
            return

        # Prepare base directory path for calculating relative paths
        base_dir_unix = result["path"].rstrip("/") + "/"

        # ===================================================================
        # STEP 2: Parse Standard Grep Output and Build Tree Structure
        # Grep output format: FILE_PATH:LINE_NUMBER:MATCHING_LINE
        # ===================================================================
        for output_line in process.stdout.splitlines():
            # Standard grep output is 'FILE:LINE_NUM:LINE_CONTENT'
            try:
                byte_list = output_line.encode("utf-8")

                file_path_raw_bytes, line_and_text_bytes = byte_list.split(
                    b"\0"
                )
                file_path_raw = file_path_raw_bytes.decode("utf-8")
                line_number_string, match_text = line_and_text_bytes.decode(
                    "utf-8"
                ).split(":", 1)
                line_number = int(line_number_string) - 1
            except Exception:
                traceback.print_exc()
                continue  # Skip malformed lines

            file_path = os.path.abspath(file_path_raw).replace("\\", "/")

            # Construct the simplified match object
            match_object = [line_number, match_text]

            # --- Build Tree Structure (Re-used Logic) ---

            # Calculate relative path
            if file_path.startswith(base_dir_unix):
                relative_path = file_path[len(base_dir_unix) :]
            else:
                # Fallback for edge cases
                relative_path = os.path.relpath(
                    file_path, base_dir_unix.rstrip("/")
                ).replace("\\", "/")
                if relative_path.startswith("../"):
                    continue  # Skip files outside search directory

            parts = relative_path.split("/")

            current_node = result
            current_path_parts = []

            for i, part in enumerate(parts):
                is_file = i == len(parts) - 1

                if is_file:
                    filename = part
                    if filename not in current_node["files"]:
                        current_node["files"][filename] = []

                    current_node["files"][filename].append(match_object)
                    break

                else:
                    current_path_parts.append(part)

                    if part not in current_node["directories"]:
                        full_dir_path = base_dir_unix + "/".join(
                            current_path_parts
                        )

                        current_node["directories"][part] = {
                            "path": full_dir_path,
                            "directories": {},
                            "files": {},
                        }
                    current_node = current_node["directories"][part]

        # Send the final successful result back
        result_queue.put(("directory", result))

    except Exception:
        print("[Grep Process] Fatal Error:")
        traceback.print_exc()
        result_queue.put(
            ("error", "A fatal internal error occurred during grep execution.")
        )


class Searcher(qt.QObject):
    directory_completed = qt.pyqtSignal(dict)
    filename_completed = qt.pyqtSignal(dict)
    error_completed = qt.pyqtSignal(str)

    def __init__(
        self,
        searchbar,
        search_type,
        search_text,
        search_directory,
        case_sensitivity,
        regex_search,
        exclude_directories=[],
    ):
        super().__init__()
        self.searchbar = searchbar
        self.search_type = search_type
        self.search_text = search_text
        self.search_directory = functions.unixify_path(search_directory)
        self.case_sensitivity = case_sensitivity
        self.regex_search = regex_search
        self.exclude_directories = exclude_directories

        # Connect signals
        self.directory_completed.connect(searchbar._directory_search_complete)
        self.filename_completed.connect(searchbar._filename_search_complete)
        self.error_completed.connect(searchbar._error_search_complete)

        # Setup multiprocessing
        self.result_queue = multiprocessing.Queue()
        self.process = None
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self._check_for_results)
        self.timer.start(100)  # Poll every 100 ms

    def start(self):
        """Start the search in a separate process."""
        if self.process and self.process.is_alive():
            self.process.terminate()
        search_type_value = (
            self.search_type.value
            if hasattr(self.search_type, "value")
            else self.search_type
        )
        self.process = multiprocessing.Process(
            #            target=_run_ripgrep_in_process,
            #            args=(
            #                self.search_text,
            #                self.search_directory,
            #                self.case_sensitivity,
            #                self.regex_search,
            #                self.exclude_directories,
            #                self.result_queue,
            #            ),
            target=_run_grep_in_process,
            args=(
                self.search_text,
                self.search_directory,
                self.case_sensitivity,
                self.regex_search,
                self.exclude_directories,
                self.result_queue,
            ),
        )
        self.process.start()

    def _check_for_results(self):
        """Poll the queue for results and emit appropriate signals."""
        if not self.result_queue.empty():
            try:
                msg_type, data = self.result_queue.get_nowait()
                if msg_type == "directory":
                    self.directory_completed.emit(data)
                elif msg_type == "filename":
                    self.filename_completed.emit(data)
                else:
                    self.error_completed.emit(
                        f"Unknown message type: '{msg_type}'"
                    )
                    print(f"Unknown message type: '{msg_type}'")
                # Stop polling once result is received
                self.timer.stop()
                if self.process and self.process.is_alive():
                    self.process.join(timeout=1)
            except Exception:
                pass  # Queue might be empty due to race condition

    def stop(self):
        """Terminate the process if still running."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
        self.timer.stop()
