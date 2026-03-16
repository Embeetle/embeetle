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
import json
import functools
import traceback

import qt
import data
import functions
import iconfunctions
import gui.templates.treewidget


class BreakpointWidget(gui.templates.treewidget.TreeWidget):
    def __init__(self, parent, main_form, debugger_window):
        super().__init__(
            parent,
            main_form,
            "BreakpointWidget",
            None,
            click_type="symbol-click",
        )
        self.debugger_window = debugger_window

        self.mouse_press_signal.connect(self.debugger_window.set_focus)
        self.no_item_right_click_signal.connect(self.__no_item_right_click)

        self.__main_nodes = {}

        # Initialize the main breakpoint node
        def breakpoint_info_func():
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Delete breakpoint
            action_open = qt.QAction(f"Delete all breakpoints", menu)
            action_open.setStatusTip("Delete all breakpoints")
            action_open.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            action_open.triggered.connect(
                self.debugger_window.debugger_breakpoints_delete_all
            )
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        self.__main_nodes["breakpoint"] = self.add(
            text="Breakpoints",
            icon_path="icons/tab/burger.png",
            tooltip="List of all the breakpoints",
            in_data={
                "info_func": breakpoint_info_func,
            },
        )

        self.__breakpoint_cache = {}

        # Initialize the main watchpoint node
        def watchpoint_info_func():
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Delete breakpoint
            action_open = qt.QAction(f"Delete all watchpoints", menu)
            action_open.setStatusTip("Delete all watchpoints")
            action_open.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            action_open.triggered.connect(
                self.debugger_window.debugger_watchpoints_delete_all
            )
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        self.__main_nodes["watchpoint"] = self.add(
            text="Watchpoints",
            icon_path="icons/tab/burger.png",
            tooltip="List of all the watchpoints",
            in_data={
                "info_func": watchpoint_info_func,
            },
        )

        self.__watchpoint_cache = {}

    """
    Break-points
    """

    def add_breakpoint(self, _data):
        """
        Example data:
        {
            'bkpt': {
                'addr': '0x0800039e',
                'disp': 'keep',
                'enabled': 'y',
                'file': '../source/user_code/main.c',
                'fullname': 'J:/embeetle/Code/00.Blink/gd32e231c-start/source/user_code/main.c',
                'func': 'main',
                'line': '61',
                'number': '1',
                'original-location': 'J:/embeetle/Code/00.Blink/gd32e231c-start/source/user_code/main.c:60',
                'thread-groups': ['i1'],
                'times': '0',
                'type': 'breakpoint'
            }
        }
        """
        number = int(_data["number"])
        file = os.path.basename(_data["file"])
        filepath = functions.unixify_path(_data["fullname"])
        func = None
        if "func" in _data.keys():
            func = _data["func"]
        line = int(_data["line"]) - 1
        text_list = (
            number,
            func,
            file,
            _data["line"],
        )
        text = " | ".join([str(x) for x in text_list if x is not None])
        filtered_data = {
            "raw-data": _data,
        }

        def click_func():
            self.main_form.open_file(filepath)
            tab = self.main_form.get_tab_by_save_name(filepath)
            if tab is not None:
                tab.blink_error_line_column(line, 0)

        def delete_func():
            data.signal_dispatcher.debug_breakpoint_delete.emit(
                filepath,
                line + 1,
                line,
                number,
            )

        def info_func():
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Goto breakpoint
            action_open = qt.QAction(f"Go to breakpoint", menu)
            action_open.setStatusTip(
                "Open the file in an editor and move to the line "
                + "where the breakpoint is located"
            )
            action_open.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/goto.png")
            )
            action_open.triggered.connect(click_func)
            menu.addAction(action_open)
            # Delete breakpoint
            action_open = qt.QAction(f"Delete breakpoint", menu)
            action_open.setStatusTip("Delete the breakpoint")
            action_open.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            action_open.triggered.connect(delete_func)
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        new_node = self.add(
            parent=self.__main_nodes["breakpoint"],
            text=text,
            icon_path="icons/dialog/stop_red.png",
            tooltip=json.dumps(filtered_data, indent=4, ensure_ascii=False),
            in_data={
                "click_func": click_func,
                "info_func": info_func,
                "number": number,
                "filepath": filepath,
                "line": line,
            },
        )
        self.__breakpoint_cache[number] = new_node

        self.__main_nodes["breakpoint"].setExpanded(True)

    def delete_breakpoint(self, number):
        removed_node = self.__breakpoint_cache.pop(number)
        self.remove(removed_node)

    def delete_all_breakpoints(self):
        for k in list(self.__breakpoint_cache.keys()):
            removed_node = self.__breakpoint_cache.pop(k)
            self.remove(removed_node)

    def get_breakpoint_numbers(self):
        return list(self.__breakpoint_cache.keys())

    def get_breakpoints(self):
        breakpoints = {}
        for k, v in self.__breakpoint_cache.items():
            breakpoints[k] = v.get_data()
        return breakpoints

    """
    Watch-points
    """

    def add_watchpoint(self, _data, stored_data):
        """
        Example data:
        {
            'wpt': {
                'exp': 'a',
                'number': '2'
            }
        }
        """
        symbol = _data["exp"]
        number = int(_data["number"])
        filepath = None
        file = None
        index = None
        _type = None
        if stored_data is not None:
            filepath = stored_data["filepath"]
            file = os.path.basename(filepath)
            index = stored_data["index"]
            _type = stored_data["type"]
        text_list = (
            number,
            symbol,
            file,
            _type,
        )
        text = " | ".join([str(x) for x in text_list if x is not None])
        filtered_data = {
            "raw-data": _data,
        }

        def click_func():
            if filepath is not None:
                self.main_form.open_file(filepath)
                tab = self.main_form.get_tab_by_save_name(filepath)
                if tab is not None and index is not None:
                    tab.blink_error_index(index)

        def delete_func():
            data.signal_dispatcher.debug_watchpoint_delete.emit(number)

        def info_func():
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Delete watchpoint
            action_open = qt.QAction(f"Delete watchpoint", menu)
            action_open.setStatusTip("Delete the watchpoint")
            action_open.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            action_open.triggered.connect(delete_func)
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        new_node = self.add(
            parent=self.__main_nodes["watchpoint"],
            text=text,
            icon_path="icons/dialog/stop_red.png",
            tooltip=json.dumps(filtered_data, indent=4, ensure_ascii=False),
            in_data={
                "click_func": click_func,
                "info_func": info_func,
                "number": number,
                "symbol": symbol,
            },
        )
        self.__watchpoint_cache[number] = new_node

        self.__main_nodes["watchpoint"].setExpanded(True)

    def delete_watchpoint(self, number):
        removed_node = self.__watchpoint_cache.pop(number)
        self.remove(removed_node)

    def delete_all_watchpoints(self, *args):
        for k in list(self.__watchpoint_cache.keys()):
            removed_node = self.__watchpoint_cache.pop(k)
            self.remove(removed_node)

    def get_watchpoint_numbers(self):
        return list(self.__watchpoint_cache.keys())

    """
    General
    """

    def delete_all(self):
        data.signal_dispatcher.debug_delete_all_watch_and_break_points.emit()

    def __no_item_right_click(self):
        # Create a menu
        if self.context_menu is not None:
            self.context_menu.setParent(None)
            self.context_menu = None
        self.context_menu = gui.templates.basemenu.BaseMenu(self)

        text = "Delete all"
        new_action = qt.QAction(text, self.context_menu)
        new_action.setIcon(iconfunctions.get_qicon("icons/dialog/cross.png"))
        new_action.triggered.connect(self.delete_all)
        new_action.setStatusTip(text)
        self.context_menu.addAction(new_action)

        # Show menu
        cursor = qt.QCursor.pos()
        self.context_menu.popup(cursor)

    def highlight(self, message):
        super()._highlight(message._id)
