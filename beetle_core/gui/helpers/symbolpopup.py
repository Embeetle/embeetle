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

import os
import sys
import time
import itertools
import inspect
import functools
import keyword
import re
import collections
import textwrap
import qt
import data
import functions
import iconfunctions
import themes
import gui.templates.basemenu
import gui.templates.treewidget
import gui.templates.widgetgenerator
import gui.stylesheets.scrollbar
import gui.stylesheets.tooltip
import settings
import lexers
import components.sourceanalyzerinterface
import traceback
import random
from typing import *


class SymbolPopup(qt.QWidget):
    MINIMUM_HEIGHT = 300
    MINIMUM_WIDTH = 500
    POSITION_CORRECTION = 50
    MAXIMUM_HEIGHT = 300
    MAXIMUM_WIDTH = 500

    _parent = None
    main_form = None
    symbol = None
    stored_widgets = None
    stored_boxes = None
    nodes = None
    cancel = False
    main_item_counter = 0

    def __del__(self):
        # Clean up references
        self._parent = None
        self.main_form = None
        self.symbol = None

    def __init__(self, parent, main_form, symbol):
        super().__init__(parent=parent)
        self._parent = parent
        self.main_form = main_form
        self.main_item_counter = 0
        self.setWindowTitle("Symbol information")
        self.setWindowIcon(qt.QIcon(data.application_icon_relpath))
        self.setWindowFlags(
            qt.Qt.WindowType.Window
            | qt.Qt.WindowType.WindowTitleHint
            | qt.Qt.WindowType.WindowSystemMenuHint
            | qt.Qt.WindowType.WindowCloseButtonHint
            | qt.Qt.WindowType.Tool
        )
        self.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.MinimumExpanding,
            )
        )
        self.set_stylesheet()
        self.stored_widgets = {}
        self.stored_boxes = {}
        self.nodes = {}

        main_groupbox = (
            gui.templates.widgetgenerator.create_borderless_groupbox(
                name="Main",
                parent=self,
            )
        )
        groupbox_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        main_groupbox.setLayout(groupbox_layout)

        main_layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        main_layout.addWidget(main_groupbox)

        # Add the treewidget
        self.symbol_tree = gui.templates.treewidget.TreeWidget(
            self, main_form, "Symbol Information", None
        )
        self.symbol_tree.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Preferred,
                qt.QSizePolicy.Policy.Preferred,
            )
        )
        groupbox_layout.addWidget(self.symbol_tree)

        self.setLayout(main_layout)
        if symbol is not None:
            self.generate_symbol_information(symbol)

    def set_stylesheet(self):
        style_sheet = f"""
            #Main {{
                background-color: {data.theme["general_background"]};
                border: 1px solid {data.theme["button_border"]};
                margin: 1px;
            }}
        """
        style_sheet += gui.stylesheets.tooltip.get_default()
        self.setStyleSheet(style_sheet)

    def _generate_symbol_string(self):
        symbol = self.symbol
        if isinstance(symbol, str) == False:
            # A real symbol
            def get_attributes(_type, field):
                locations = []
                field_attr = getattr(symbol, field)
                if len(field_attr) > 0:
                    locations.append(f"{_type}:")
                    for x in field_attr:
                        locations.extend(
                            [
                                f"  - Path: {x.path}",
                                f"    - Line: {x.line}",
                                f"    - Column: {x.column}",
                                f"    - Size: {x.size}",
                            ]
                        )
                else:
                    locations.append(f"{_type}: None")
                return locations

            # Definitions
            definitions = get_attributes("Definitions", "definitions")
            # Weak definitions
            weak_definitions = get_attributes(
                "Weak definitions", "weak_definitions"
            )
            # Declarations
            declarations = get_attributes("Declarations", "declarations")
            # Uses
            uses = get_attributes("Usages", "uses")
            # Symbol
            symbol_info = (
                f"Name: {symbol.name}",
                f"Kind: {symbol.kind_name}",
                *definitions,
                *weak_definitions,
                *declarations,
                *uses,
            )
            return "\n".join(symbol_info)
        else:
            # Included header
            return f"Header: {symbol}"

    def __generate_symbol_form(self, symbol):
        symbol = self.symbol
        main_layout = self.layout()
        self.symbol_tree.clear()

        SymbolPopup.cancel = False

        # Goto function for navigating to a symbol location
        def goto_func(path, offset, *args):
            if path is not None:
                file_path = functions.unixify_path(path)
                self.main_form.open_file(file_path)
                tab = self.main_form.get_tab_by_save_name(file_path)
                if tab is not None and offset is not None:
                    tab.goto_index(offset)
                self.hide()

        # Menu with additional symbol options
        def create_menu(_type, path, offset, text, create_open_item=True):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Open file
            if create_open_item:
                action_open = qt.QAction(f"Go to {_type}", menu)
                action_open.setStatusTip(
                    "Open the file in an editor and move to the line "
                    + "where the {_type} is located"
                )
                action_open.setIcon(
                    iconfunctions.get_qicon(f"icons/menu_edit/goto.png")
                )
                action_open.triggered.connect(
                    functools.partial(goto_func, path, offset)
                )
                menu.addAction(action_open)

            # Copy item text
            def clipboard_copy():
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(text, mode=cb.Mode.Clipboard)

            action_copy = qt.QAction(
                "Copy the item text to the clipboard.", menu
            )
            action_copy.setStatusTip("Copy the item text to the clipboard.")
            action_copy.setIcon(
                iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
            )
            action_copy.triggered.connect(clipboard_copy)
            menu.addAction(action_copy)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        lists = []

        def async_add_locatons():
            def add_locations(name, field, parent_node):
                last_index = len(field) - 1
                for i, d in enumerate(reversed(field)):
                    if SymbolPopup.cancel == True:
                        return
                    path = d.file.path
                    offset = d.begin_offset
                    try:
                        # Try to get the location information
                        line_number, line, line_from_offset = (
                            functions.get_line_from_offset(path, offset)
                        )
                    except:
                        message = traceback.format_exc()
                        self.main_form.display.display_error(message)
                        continue
                    if len(line) > 40:
                        #                            line = line[:40] + " ..."
                        if len(line_from_offset) > 40:
                            line = "..." + line_from_offset[:34] + "..."
                        else:
                            offset_in_line = line.index(line_from_offset)
                            diff_0 = len(line) - len(line_from_offset)
                            diff_1 = 37 - len(line_from_offset)
                            if diff_0 > diff_1:
                                line = "..." + line[offset_in_line - diff_1 :]
                            else:
                                line = line[:37] + "..."
                    line = line.replace("\n", "").replace("\r", "")

                    item_text = (
                        f"File: {os.path.basename(path)}, "
                        + f"Line number: {line_number}, "
                        + f"Line: '{line}'"
                    )
                    icon_path = "icons/symbols/arrow.png"
                    # if data.theme['is_dark']:
                    #     icon_path = 'icons/symbols/arrow_dark.png'
                    # else:
                    #     icon_path = 'icons/symbols/arrow.png'
                    item = self.symbol_tree.add(
                        text=item_text,
                        icon_path=icon_path,
                        in_data={
                            "info_func": functools.partial(
                                create_menu, name, path, offset, item_text
                            ),
                            "click_func": functools.partial(
                                goto_func, path, offset
                            ),
                        },
                        parent=parent_node,
                    )
                    item.setToolTip(
                        0,
                        f"{name.title()} information. "
                        + "Click to go to location. "
                        + "Right-click for more options.",
                    )

                    self.main_item_counter += 1

                    # Refresh the widget
                    self.refresh()
                    functions.process_events(10)

            for l in lists:
                _name, _list, _parent = l
                add_locations(_name, _list, _parent)
                _parent.setExpanded(True)
                if SymbolPopup.cancel == True:
                    break
            self.refresh()

        # Symbol
        if isinstance(symbol, str) == False and (symbol is not None):
            # Name and type
            #            name_text = f"Type: {symbol.kind_name} {symbol.name}"
            name_text = f"{symbol.kind_name} {symbol.name}"
            name_type = self.symbol_tree.add(
                text=name_text,
                icon_path=data.SYMBOL_ICONS["name"],
                in_data={
                    "info_func": functools.partial(
                        create_menu, "", "", 0, name_text, False
                    ),
                    "click_func": None,
                },
            )
            # Strong Definitions
            if len(symbol.definitions) > 0:
                definitions = self.symbol_tree.add(
                    text=(
                        "Strong Definitions:"
                        if (len(symbol.definitions) > 0)
                        else "Strong Definitions: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["definition"],
                )
                definitions.setToolTip(0, "All definitions of the symbol")
                lists.append(("definition", symbol.definitions, definitions))
            # Weak definitions
            if len(symbol.weak_definitions) > 0:
                weak_definitions = self.symbol_tree.add(
                    text=(
                        "Weak Definitions:"
                        if (len(symbol.weak_definitions) > 0)
                        else "Weak Definitions: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["weak definition"],
                )
                weak_definitions.setToolTip(
                    0, "All weak definitions of the symbol"
                )
                lists.append(
                    (
                        "weak_definitions",
                        symbol.weak_definitions,
                        weak_definitions,
                    )
                )
            # Tentative definitions
            if len(symbol.tentative_definitions) > 0:
                tentative_definitions = self.symbol_tree.add(
                    text=(
                        "Tentative Definitions:"
                        if (len(symbol.tentative_definitions) > 0)
                        else "Tentative Definitions: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["tentative definition"],
                )
                tentative_definitions.setToolTip(
                    0, "All tentative definitions of the symbol"
                )
                lists.append(
                    (
                        "tentative_definitions",
                        symbol.tentative_definitions,
                        tentative_definitions,
                    )
                )
            # Declarations
            if len(symbol.declarations) > 0:
                declarations = self.symbol_tree.add(
                    text=(
                        "Declarations:"
                        if (len(symbol.declarations) > 0)
                        else "Declarations: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["declaration"],
                )
                declarations.setToolTip(0, "All declarations of the symbol")
                lists.append(
                    ("declarations", symbol.declarations, declarations)
                )
            # Uses
            usages = self.symbol_tree.add(
                text=("Uses:" if (len(symbol.uses) > 0) else "Uses: None"),
                icon_path=data.SYMBOL_ICONS["usage"],
            )
            usages.setToolTip(0, "All uses of the symbol")
            lists.append(("usages", symbol.uses, usages))

            qt.QTimer.singleShot(10, async_add_locatons)

        # Header
        elif isinstance(symbol, str):
            # Name only
            header_path = symbol
            header_text = f"Header: {header_path}"
            header = self.symbol_tree.add(
                text=header_text,
                icon_path="icons/symbols/occurrence_kind/header.png",
                in_data={
                    "info_func": functools.partial(
                        create_menu, "header", header_path, 0, header_text
                    ),
                    "click_func": functools.partial(
                        goto_func, header_path, None, 1
                    ),
                },
            )
            header.setToolTip(0, "A header file")

            # Includers
            includes = components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_file_include_locations(
                header_path
            )
            if includes is not None:
                usages = self.symbol_tree.add(
                    text=(
                        "Includers:"
                        if (len(includes) > 0)
                        else "Includers: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["usage"],
                )
                usages.setToolTip(0, "All uses of the symbol")
                lists.append(("usages", includes, usages))

                qt.QTimer.singleShot(10, async_add_locatons)

        # Nothing
        else:
            nothing = self.symbol_tree.add(
                text="Nothing found at this cursor position.",
                icon_path="icons/dialog/cross.png",
            )
            nothing.setToolTip(0, "Nothing found at this cursor position.")
        self.refresh()

    def generate_symbol_information(self, symbol):
        self.main_item_counter = 0
        self.symbol = symbol

        self.__generate_symbol_form(symbol)

        qt.QTimer.singleShot(5, self.refresh)

    def adjust_minimum_size(self):
        if not self.isVisible():
            return
        toolbar_height = 30
        if self.main_item_counter < 1:
            self.main_item_counter = 1
        window_size = self.size()
        cursor_position = functions.get_cursor_position(self)
        desktop_size = qt.QSize(functions.get_screen_size())
        # Height
        height = int(data.get_general_icon_pixelsize())
        button_height = self.symbol_tree.get_child_count() * height
        sum_height = button_height + toolbar_height + 20
        if (cursor_position.y() + sum_height) > desktop_size.height():
            sum_height = desktop_size.height() - cursor_position.y() - 60
        # Width
        width = self.symbol_tree.columnWidth(0) + 20
        if (cursor_position.x() + width) > desktop_size.width():
            width = desktop_size.width() - cursor_position.x() - 50
        # Resize
        new_size = qt.create_qsize(width, sum_height)
        self.resize(new_size)

    def refresh(self):
        self.adjust_minimum_size()
        geometry = self.geometry()
        screen = functions.get_widget_screen(self)
        if geometry.y() + geometry.height() > screen.size().height():
            self.move(
                int(geometry.x()),
                int(
                    screen.size().height()
                    - geometry.height()
                    - self.POSITION_CORRECTION
                ),
            )

    def display_at_cursor(self):
        cursor_position = qt.QCursor.pos()
        self.move(cursor_position)
        self.show()

    def display_at_position(self, position):
        popup_position = position
        if isinstance(position, tuple):
            popup_position = qt.create_qpoint(*popup_position)
        self.move(popup_position)
        self.show()

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        released_key = event.key()
        if released_key == qt.Qt.Key.Key_Escape:
            self.hide()

    def show(self):
        super().show()
        self.adjust_minimum_size()
        SymbolPopup.cancel = False
        self.setFocus()
        self.activateWindow()
        self.raise_()

    def hide(self):
        super().hide()
        self.adjust_minimum_size()
        SymbolPopup.cancel = True
