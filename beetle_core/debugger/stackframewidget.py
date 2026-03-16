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


class StackFrameWidget(gui.templates.treewidget.TreeWidget):
    def __init__(self, parent, main_form, debugger_window):
        super().__init__(
            parent,
            main_form,
            "StackFrameWidget",
            None,
            click_type="symbol-click",
        )
        self.debugger_window = debugger_window

        self.__main_nodes = {}

        # Initialize the main stack node
        self.__main_nodes["stack"] = self.add(
            text="Stack",
            icon_path="icons/tab/burger.png",
            tooltip="List of stack frames",
            in_data={
                "info_func": self.__stack_context_func,
            },
        )
        self.__stack_frame_cache = {}

        # Initialize the main stack node
        self.__main_nodes["variables"] = self.add(
            text="Locals",
            icon_path="icons/tab/burger.png",
            tooltip="List of stack variables",
            in_data={
                "info_func": self.__variable_context_func,
            },
        )
        self.__stack_variable_cache = {}

    def __stack_context_func(self):
        # Create menu
        menu = gui.templates.basemenu.BaseMenu(self)
        # Delete breakpoint
        action_open = qt.QAction("Refresh stack frames", menu)
        action_open.setStatusTip("Refresh the stack frame.")
        action_open.setIcon(iconfunctions.get_qicon("icons/dialog/refresh.png"))
        action_open.triggered.connect(
            self.debugger_window.debugger_stack_frame_list
        )
        menu.addAction(action_open)
        # Show the menu
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def __variable_context_func(self):
        # Create menu
        menu = gui.templates.basemenu.BaseMenu(self)
        # Delete breakpoint
        action_open = qt.QAction("Refresh stack variable list", menu)
        action_open.setStatusTip("Refresh stack variable lis.")
        action_open.setIcon(iconfunctions.get_qicon("icons/dialog/refresh.png"))
        action_open.triggered.connect(
            self.debugger_window.debugger_stack_variable_list
        )
        menu.addAction(action_open)
        # Show the menu
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def clear_stack_list(self):
        for k in reversed(list(self.__stack_frame_cache.keys())):
            removed_node = self.__stack_frame_cache.pop(k)
            self.remove(removed_node)

    def set_stack_list(self, stack_list):
        self.clear_stack_list()

        def click_func(filepath, line):
            self.main_form.open_file(filepath)
            tab = self.main_form.get_tab_by_save_name(filepath)
            if tab is not None:
                tab.blink_error_line_column(line, 0)

        frame_dict = {}
        for sf in stack_list:
            level = int(sf["level"])
            frame_dict[level] = sf
        parent_node = self.__main_nodes["stack"]
        for k in reversed(sorted(frame_dict.keys())):
            sf = frame_dict[k]
            func = None
            if "func" in sf.keys():
                func = sf["func"]

            filepath = None
            if "fullname" in sf.keys():
                filepath = functions.unixify_path(sf["fullname"])
            file = None
            if "file" in sf.keys():
                file = os.path.basename(sf["file"])
            line_string = None
            line = None
            if "line" in sf.keys():
                line_string = sf["line"]
                line = int(sf["line"]) - 1
            out_click_func = None
            if "fullname" in sf.keys() and "line" in sf.keys():
                out_click_func = functools.partial(click_func, filepath, line)
            level = int(sf["level"])
            text_list = (
                level,
                func,
                file,
                line_string,
                sf["addr"],
            )
            text = " | ".join([str(x) for x in text_list if x is not None])
            new_node = self.add(
                parent=parent_node,
                text=text,
                icon_path="icons/arrow/arrow_blue/arrow_right.svg",
                tooltip=json.dumps(sf, indent=4, ensure_ascii=False),
                in_data={
                    "click_func": out_click_func,
                    #                    "info_func": info_func,
                },
            )
            parent_node.setExpanded(True)
            self.__stack_frame_cache[k] = new_node
            # Create nesting by updating the parent

    #            parent_node = new_node

    """
    Variables
    """

    def clear_stack_variables(self):
        for k in reversed(list(self.__stack_variable_cache.keys())):
            removed_node = self.__stack_variable_cache.pop(k)
            self.remove(removed_node)

    def set_stack_variables(self, variable_list):
        self.clear_stack_variables()

        def click_func(filepath, line):
            #            self.main_form.open_file(filepath)
            #            tab = self.main_form.get_tab_by_save_name(filepath)
            #            if tab is not None:
            #                tab.blink_error_line_column(line, 0)
            pass

        parent_node = self.__main_nodes["variables"]
        for v in variable_list:
            name = v["name"]
            value = v["value"]
            text_list = (
                name,
                value,
            )
            text = f"{name}: {value}"
            new_node = self.add(
                parent=parent_node,
                text=text,
                icon_path="icons/symbols/symbol_kind/type.png",
                tooltip=json.dumps(v, indent=4, ensure_ascii=False),
            )
            parent_node.setExpanded(True)
            self.__stack_variable_cache[name] = new_node
