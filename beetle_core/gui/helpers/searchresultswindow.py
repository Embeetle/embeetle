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
import qt
import data
import functions
import iconfunctions
import gui.templates.basemenu
import gui.templates.treewidget
import components.diagnostics
import source_analyzer
import gui.stylesheets.groupbox
import functools
import random
import multiprocessing
import webbrowser
import urllib.parse
from typing import *
from pprint import pprint


class SearchResultsWindow(gui.templates.treewidget.TreeWidget):
    def __init__(self, parent, main_form):
        super().__init__(
            parent,
            main_form,
            "SearchResults",
            iconfunctions.get_qicon("icons/gen/zoom.png"),
        )
        self.main_nodes = {}
        self.setSortingEnabled(False)
        self.update_style()

    def add_file_results(self, in_data):
        if len(in_data) == 0:
            self.add(
                f"Nothing found!",
                icon_path="icons/dialog/cross.png",
            )
            return
        for d in in_data:
            search_text, file_path, matches, editor = d
            # Details
            filename = os.path.basename(file_path)
            self.main_nodes[file_path] = self.add(
                f"DOCUMENT: {filename}",
                icon_path="icons/file/file.png",
            )
            self.main_nodes[file_path].setExpanded(True)

            def clipboard_copy(path):
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(path, mode=cb.Mode.Clipboard)

            def create_menu(path):
                # Create menu
                menu = gui.templates.basemenu.BaseMenu(self)
                # Copy diagnostic to clipboard
                action_copy = qt.QAction(
                    "Copy the path to the clipboard.", menu
                )
                action_copy.setStatusTip(
                    "Copy the file's path to the clipboard."
                )
                action_copy.setIcon(
                    iconfunctions.get_qicon("icons/menu_edit/paste.png")
                )
                action_copy.triggered.connect(
                    functools.partial(clipboard_copy, path)
                )
                menu.addAction(action_copy)
                # Show the menu
                cursor = qt.QCursor.pos()
                menu.popup(cursor)

            self.add(
                text=f"PATH: {file_path}",
                parent=self.main_nodes[file_path],
                icon_path="icons/gen/path.png",
                in_data={
                    "info_func": functools.partial(create_menu, file_path),
                    "click_func": functools.partial(
                        clipboard_copy,
                        file_path,
                    ),
                },
            )
            self.add(
                text=f'SEARCH TEXT: "{search_text}"',
                parent=self.main_nodes[file_path],
                icon_path="icons/gen/zoom.png",
            )
            # Results
            text = f"RESULTS: Nothing found"
            icon = "icons/dialog/stop.png"
            if len(matches) > 0:
                text = f"RESULTS: {len(matches)} matches found"
                icon = "icons/gen/diff_similar.png"
            results_node = self.add(
                text,
                parent=self.main_nodes[file_path],
                icon_path=icon,
            )
            if len(matches) > 0:
                results_node.setExpanded(True)

                def create_menu(path, line_fr, index_fr, line_to, index_to):
                    # Create menu
                    menu = gui.templates.basemenu.BaseMenu(self)

                    # Open file
                    def open_file():
                        file_path = functions.unixify_path(path)
                        self.main_form.open_file(file_path)
                        main = self.main_form
                        tab = main.get_tab_by_save_name(file_path)
                        if tab is not None:
                            tab.goto_line_column(line_fr, index_fr)
                            tab.setSelection(
                                line_fr, index_fr, line_to, index_to
                            )

                    action_open = qt.QAction(
                        f"Go to line '{line_fr}' / index {index_fr}", menu
                    )
                    action_open.setStatusTip(
                        "Open the file in an editor and move to the line "
                        + f"where the searched text is located."
                    )
                    action_open.setIcon(
                        iconfunctions.get_qicon("icons/menu_edit/goto.png")
                    )
                    action_open.triggered.connect(open_file)
                    menu.addAction(action_open)
                    # Show the menu
                    cursor = qt.QCursor.pos()
                    menu.popup(cursor)

                def click_func(path, line_fr, index_fr, line_to, index_to):
                    file_path = functions.unixify_path(path)
                    self.main_form.open_file(file_path)
                    main = self.main_form
                    tab = main.get_tab_by_save_name(file_path)
                    if tab is not None:
                        tab.goto_line_column(line_fr, index_fr)
                        tab.setSelection(line_fr, index_fr, line_to, index_to)

                for m in matches:
                    line_number_from = m[0]
                    index_from = m[1]
                    line_number_to = m[2]
                    index_to = m[3]
                    line = m[4].replace("\n", "")
                    self.add(
                        text=f"Line {line_number_from+1} / Index {index_from+1}: {line}",
                        icon_path=f"icons/menu_edit/goto.png",
                        parent=results_node,
                        in_data={
                            "info_func": functools.partial(
                                create_menu,
                                file_path,
                                line_number_from,
                                index_from,
                                line_number_to,
                                index_to,
                            ),
                            "click_func": functools.partial(
                                click_func,
                                file_path,
                                line_number_from,
                                index_from,
                                line_number_to,
                                index_to,
                            ),
                        },
                    )

        self.update_style()

    def add_directory_results(self, in_data):
        if "files" not in in_data.keys():
            self.add(
                f"Nothing found!",
                icon_path="icons/dialog/cross.png",
            )
            return
        elif (
            len(in_data["files"].keys()) == 0
            and len(in_data["directories"].keys()) == 0
        ):
            self.add(
                f"Nothing found!",
                icon_path="icons/dialog/cross.png",
            )
            return

        def clipboard_copy(path):
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(path, mode=cb.Mode.Clipboard)

        def create_menu_main(path):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Copy diagnostic to clipboard
            action_copy = qt.QAction("Copy the path to the clipboard.", menu)
            action_copy.setStatusTip("Copy the item's path to the clipboard.")
            action_copy.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/copy.png")
            )
            action_copy.triggered.connect(
                functools.partial(clipboard_copy, path)
            )
            menu.addAction(action_copy)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        quote = '"'
        self.add(
            text=f"SEARCH PATH: {quote}{in_data['path']}{quote}",
            icon_path="icons/gen/path.png",
            in_data={
                "info_func": functools.partial(
                    create_menu_main, in_data["path"]
                ),
                "click_func": functools.partial(
                    clipboard_copy,
                    in_data["path"],
                ),
            },
        )
        self.add(
            text=f"SEARCH TEXT: {quote}{in_data['search-text']}{quote}",
            icon_path="icons/gen/zoom.png",
        )

        def create_menu(path, line_fr, index_fr, line_to, index_to):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)

            # Open file
            def open_file():
                file_path = functions.unixify_path(path)
                self.main_form.open_file(file_path)
                main = self.main_form
                tab = main.get_tab_by_save_name(file_path)
                if tab is not None:
                    tab.goto_line_column(line_fr, index_fr)
                    tab.setSelection(line_fr, index_fr, line_to, index_to)

            action_open = qt.QAction(
                f"Go to line '{line_fr}' / index {index_fr}", menu
            )
            action_open.setStatusTip(
                "Open the file in an editor and move to the line "
                + f"where the searched text is located."
            )
            action_open.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/goto.png")
            )
            action_open.triggered.connect(open_file)
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        def click_func(path, line_fr, index_fr, line_to, index_to):
            file_path = functions.unixify_path(path)
            self.main_form.open_file(file_path)
            main = self.main_form
            tab = main.get_tab_by_save_name(file_path)
            if tab is not None:
                tab.goto_line_column(line_fr, index_fr)
                tab.setSelection(line_fr, index_fr, line_to, index_to)

        def parse_directory(parent_node, node_list, dir_data):
            nonlocal _id
            for directory_name, sub_data in dir_data["directories"].items():
                if directory_name.strip() == "":
                    directory_name = dir_data["path"]
                directory_node = {
                    "text": directory_name,
                    "icon": "icons/folder/closed/folder.png",
                    "parent": parent_node["id"],
                    "id": _id,
                    "expanded": True,
                }
                _id += 1
                node_list.append(directory_node)
                parse_directory(directory_node, node_list, sub_data)
            for file_name, matches in dir_data["files"].items():
                file_path = functions.unixify_path_join(
                    dir_data["path"], file_name
                )
                file_node = {
                    "text": file_name,
                    "icon": "icons/file/file.png",
                    "parent": parent_node["id"],
                    "id": _id,
                    "expanded": False,
                }
                _id += 1
                node_list.append(file_node)
                for m in matches:
                    if len(m) == 5:
                        line_number_from = m[0]
                        index_from = m[1]
                        line_number_to = m[2]
                        index_to = m[3]
                        line = m[4].replace("\n", "")
                    elif len(m) == 2:
                        line_number_from = m[0]
                        index_from = 0
                        line_number_to = m[0]
                        index_to = 0
                        line = m[1].replace("\n", "")
                    else:
                        raise Exception("Invalid search result!")
                    match_node = {
                        "text": (
                            f"Line {line_number_from+1} / Index {index_from+1}: {line}"
                        ),
                        "icon": f"icons/menu_edit/goto.png",
                        "parent": file_node["id"],
                        "data": {
                            "info_func": functools.partial(
                                create_menu,
                                file_path,
                                line_number_from,
                                index_from,
                                line_number_to,
                                index_to,
                            ),
                            "click_func": functools.partial(
                                click_func,
                                file_path,
                                line_number_from,
                                index_from,
                                line_number_to,
                                index_to,
                            ),
                        },
                        "id": _id,
                    }
                    _id += 1
                    node_list.append(match_node)

        nodes = []
        _id = 10
        main_node = {
            "text": "RESULTS:",
            "icon": "icons/system/find_in_files.png",
            "id": _id,
            "parent": None,
            "expanded": True,
        }
        _id += 1
        nodes.append(main_node)
        parse_directory(main_node, nodes, in_data)

        items = self.multi_add(nodes)

        self.update_style()

    def add_filename_results(self, in_data):
        if len(in_data) < 1:
            self.add(
                f"Nothing found!",
                icon_path="icons/dialog/cross.png",
            )
            return
        elif in_data["path"] is None or in_data["path"].strip() == "":
            self.add(
                f"Incorrect search directory: {directory}",
                icon_path="icons/dialog/cross.png",
            )
            return

        def clipboard_copy(path):
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(path, mode=cb.Mode.Clipboard)

        def create_menu_main(path):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Copy diagnostic to clipboard
            action_copy = qt.QAction("Copy the path to the clipboard.", menu)
            action_copy.setStatusTip("Copy the item's path to the clipboard.")
            action_copy.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/copy.png")
            )
            action_copy.triggered.connect(
                functools.partial(clipboard_copy, path)
            )
            menu.addAction(action_copy)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        quote = '"'
        self.add(
            text=f"SEARCH PATH: {quote}{in_data['path']}{quote}",
            icon_path="icons/gen/path.png",
            in_data={
                "info_func": functools.partial(
                    create_menu_main, in_data["path"]
                ),
                "click_func": functools.partial(
                    clipboard_copy,
                    in_data["path"],
                ),
            },
        )
        self.add(
            text=f"SEARCH TEXT: {quote}{in_data['search-text']}{quote}",
            icon_path="icons/gen/zoom.png",
        )
        results = self.add(
            text="RESULTS:",
            icon_path="icons/system/find_files.png",
        )
        results.setExpanded(True)

        def create_menu(path):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)

            # Copy name
            def __clipboard_copy_name(*args):
                name = os.path.basename(path)
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(name, mode=cb.Mode.Clipboard)

            action_open = qt.QAction("Copy name", menu)
            tooltip = "Copy item name to clipboard."
            action_open.setToolTip(tooltip)
            action_open.setStatusTip(tooltip)
            action_open.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/copy.png")
            )
            action_open.triggered.connect(__clipboard_copy_name)
            menu.addAction(action_open)

            # Copy path
            def __clipboard_copy_path(*args):
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(path, mode=cb.Mode.Clipboard)

            action_open = qt.QAction("Copy path", menu)
            tooltip = "Copy item path to clipboard."
            action_open.setToolTip(tooltip)
            action_open.setStatusTip(tooltip)
            action_open.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/copy.png")
            )
            action_open.triggered.connect(__clipboard_copy_path)
            menu.addAction(action_open)
            # Separator
            menu.addSeparator()

            # Open in explorer
            def __open_in_explorer(*args):
                functions.open_file_folder_in_explorer(path)

            action_open = qt.QAction("Open in explorer", menu)
            tooltip = "Open the item in the default OS file explorer."
            action_open.setToolTip(tooltip)
            action_open.setStatusTip(tooltip)
            action_open.setIcon(
                iconfunctions.get_qicon("icons/folder/open/magnifier.png")
            )
            action_open.triggered.connect(__open_in_explorer)
            menu.addAction(action_open)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        def click_func(path):
            file_path = functions.unixify_path(path)
            self.main_form.open_file(file_path)

        def parse_directory(node, dir_data):
            for directory_name, sub_data in dir_data["directories"].items():
                directory_path = sub_data["path"]
                if directory_name.strip() == "":
                    directory_name = directory_path
                directory_node = self.add(
                    directory_name,
                    icon_path="icons/folder/closed/folder.png",
                    parent=node,
                    in_data={
                        "info_func": functools.partial(
                            create_menu,
                            directory_path,
                        ),
                    },
                )
                directory_node.setExpanded(True)
                parse_directory(directory_node, sub_data)
            for file_name in dir_data["files"]:
                file_path = functions.unixify_path_join(
                    dir_data["path"], file_name
                )
                file_node = self.add(
                    file_name,
                    icon_path="icons/file/file.png",
                    parent=node,
                    in_data={
                        "info_func": functools.partial(
                            create_menu,
                            file_path,
                        ),
                        "click_func": functools.partial(
                            click_func,
                            file_path,
                        ),
                    },
                )

        parse_directory(results, in_data)

        self.update_style()
