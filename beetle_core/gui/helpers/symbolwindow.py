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
import traceback
import qt
import data
import functions
import iconfunctions
import gui.templates.basemenu
import gui.templates.baseobject
import gui.templates.treewidget
import gui.templates.widgetgenerator
import gui.stylesheets.frame
import components.symbolhandler
import components.sourceanalyzerinterface
import source_analyzer
import functools
import queue
import helpdocs.help_texts


def goto(tree_widget, path, offset, *args):
    """Goto function for navigating to a symbol location."""
    if path is not None:
        file_path = functions.unixify_path(path)
        tree_widget.main_form.open_file(file_path)
        tab = tree_widget.main_form.get_tab_by_save_name(file_path)
        if tab is not None and offset is not None:
            tab.goto_index(offset)


def create_menu(tree_widget, _type, path, offset, text, create_open_item=True):
    """Menu with additional symbol options."""
    # Create menu
    menu = gui.templates.basemenu.BaseMenu(tree_widget)
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
            functools.partial(goto, tree_widget, path, offset)
        )
        menu.addAction(action_open)

    # Copy item text
    def clipboard_copy():
        cb = data.application.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(text, mode=cb.Mode.Clipboard)

    action_copy = qt.QAction("Copy the item text to the clipboard", menu)
    action_copy.setStatusTip("Copy the item text to the clipboard.")
    action_copy.setIcon(iconfunctions.get_qicon(f"icons/menu_edit/paste.png"))
    action_copy.triggered.connect(clipboard_copy)
    menu.addAction(action_copy)
    # Show the menu
    cursor = qt.QCursor.pos()
    menu.popup(cursor)


id_counter = 32768


def add_locations(tree_widget, name, field, parent_node):
    """Function for adding file symbols to a tree."""
    global id_counter
    last_index = len(field) - 1
    items = []
    for i, d in enumerate(reversed(field)):
        path = d.file.path
        offset = d.begin_offset
        try:
            # Try to get the location information
            line_number, line, line_from_offset = (
                functions.get_line_from_offset(path, offset)
            )
        except:
            message = traceback.format_exc()
            tree_widget.main_form.display.display_error(message)
            continue
        if len(line) > 40:
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

        item_text = f"{os.path.basename(path)}, {line_number}, '{line}'"
        tooltip = (
            f"{name.title()} information. "
            + "Click to go to location. "
            + "Right-click for more options."
        )
        icon_path = "icons/symbols/arrow.png"
        items.append(
            {
                "text": item_text,
                "id": id_counter,
                "parent": parent_node,
                "icon": icon_path,
                "data": {
                    "info_func": functools.partial(
                        create_menu,
                        tree_widget,
                        name[:-1],
                        path,
                        offset,
                        item_text,
                    ),
                    "click_func": functools.partial(
                        goto, tree_widget, path, offset
                    ),
                },
                "tooltip": tooltip,
                "statustip": tooltip,
            }
        )
        id_counter += 1

    return tree_widget.multi_add(items)


class FileSymbols(gui.templates.treewidget.TreeWidget):
    __includer_cache = []
    symbolhandler: components.symbolhandler.SymbolHandler = None
    main_nodes = None
    main_node_id_counter = -1_000_000

    def __init__(self, parent, main_form, symbolhandler):
        super().__init__(
            parent,
            main_form,
            "FileSymbols",
            iconfunctions.get_qicon("icons/gen/balls.png"),
            click_type="symbol-click",
        )

        if symbolhandler is not None:
            self.add_symbolhandler(symbolhandler)

        self.main_nodes = {}

        self.tree_items_add = []
        self.tree_items_remove = []

        self.update_style()

    def add_symbolhandler(self, symbolhandler):
        if self.symbolhandler is not None:
            try:
                self.symbolhandler.symbols_added_signal.disconnect()
                self.symbolhandler.symbols_removed_signal.disconnect()
                self.symbolhandler = None
            except:
                traceback.print_exc()
        # Connect the signals
        symbolhandler.symbols_added_signal.connect(self.symbols_added)
        symbolhandler.symbols_removed_signal.connect(self.symbols_removed)
        self.symbolhandler = symbolhandler

    def __info_func(self, text, sym):
        # Create menu
        menu = gui.templates.basemenu.BaseMenu(self)

        # Open file
        def open_file():
            file_path = functions.unixify_path(sym.file)
            self.main_form.open_file(file_path)
            main = self.main_form
            tab = main.get_tab_by_save_name(file_path)
            if tab is not None:
                tab.goto_index(sym.begin_offset)

        action_open = qt.QAction(f"Go to '{sym.name}'", menu)
        action_open.setStatusTip(
            "Open the file in an editor and move to the line "
            + f"where the '{sym.name}' "
            + "is located"
        )
        action_open.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/goto.png")
        )
        action_open.triggered.connect(open_file)
        menu.addAction(action_open)

        # Copy diagnostic to clipboard
        def clipboard_copy():
            cb = data.application.clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            cb.setText(text, mode=cb.Mode.Clipboard)

        action_copy = qt.QAction("Copy the symbol text to the clipboard.", menu)
        action_copy.setStatusTip("Copy message to clipboard")
        action_copy.setIcon(
            iconfunctions.get_qicon(f"icons/menu_edit/paste.png")
        )
        action_copy.triggered.connect(clipboard_copy)
        menu.addAction(action_copy)
        # Show the menu
        cursor = qt.QCursor.pos()
        menu.popup(cursor)

    def __click_func(self, sym):
        file_path = functions.unixify_path(sym.file)
        self.main_form.open_file(file_path)
        tab = self.main_form.get_tab_by_save_name(file_path)
        if tab is not None and sym.begin_offset is not None:
            tab.goto_index(sym.begin_offset)

    def __add_main_node(
        self,
        node_key,
        file_path=None,
        text=None,
        icon_path=None,
    ):
        if node_key is None:
            raise Exception("[FileSymbols] Node key has to be a value!")

        # Add the main file node
        if file_path is not None:
            if not (file_path in self.main_nodes.keys()):
                file_name = os.path.basename(file_path)
                new_main_item = self.add(
                    text=file_name,
                    _id=self.main_node_id_counter,
                    icon_path="icons/file/file.png",
                    in_data={
                        "scope": None,
                    },
                )
                self.main_node_id_counter += 1
                self.main_nodes[node_key] = new_main_item

        # Add a normal main node
        elif text is not None:
            new_main_item = self.add(
                text=text,
                _id=self.main_node_id_counter,
                icon_path=icon_path,
                in_data={
                    "scope": None,
                },
            )
            self.main_node_id_counter += 1
            self.main_nodes[node_key] = new_main_item

        # Error
        else:
            raise Exception("[FileSymbols] Unknown main node type!")

    def __check_header(self, file_path):
        # Check if header file
        includes_id = f"includes-{file_path}"
        if functions.is_header_file(file_path):
            if includes_id not in self.main_nodes.keys():
                # Remove all includes
                for item in self.__includer_cache:
                    self.remove(item.id)
                self.__includer_cache = []
                for k in list(self.main_nodes.keys()):
                    if k.startswith("includes-"):
                        self.remove(self.main_nodes[k].id)
                        self.main_nodes.pop(k, None)

                # Add includes
                includes = components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_file_include_locations(
                    file_path
                )
                if includes is not None:
                    lists = []
                    includes_text = "Included-from:"
                    self.__add_main_node(
                        node_key=includes_id,
                        text=(
                            includes_text
                            if (len(includes) > 0)
                            else f"{includes_text} None"
                        ),
                        icon_path=data.SYMBOL_ICONS["usage"],
                    )
                    self.main_nodes[includes_id].setToolTip(
                        0, "All includes of the header file"
                    )
                    lists.append(
                        ("includes", includes, self.main_nodes[includes_id])
                    )
                    # Add the lists
                    self.__includer_cache = []
                    for l in lists:
                        _name, _list, _parent = l
                        new_items = add_locations(self, _name, _list, _parent)
                        self.__includer_cache.extend(new_items)
                        _parent.setExpanded(True)
        else:
            # Remove all needed
            self.__includers_remove_all()

    def __includers_remove_all(self):
        for item in self.__includer_cache:
            self.remove(item.id)
        self.__includer_cache = []
        for k in list(self.main_nodes.keys()):
            if k.startswith("includes-"):
                self.remove(self.main_nodes[k].id)
                self.main_nodes.pop(k, None)

    @qt.pyqtSlot(list)
    def symbols_added(self, symbol_list):
        for s in symbol_list:
            symbol, path = s
            kind = symbol.kind

            # text = f"{symbol.name} (index: {symbol.begin_offset})"
            text = symbol.name

            if not hasattr(self, "add_queue"):
                self.add_queue = queue.Queue()
            self.add_queue.put(
                (
                    text,
                    symbol,
                    kind,
                )
            )

        self.add_data()

    @qt.pyqtSlot(object, str)
    def symbol_added(self, symbol, path):
        kind = symbol.kind

        #        text = f"{symbol.name} (index: {symbol.offset})"
        text = symbol.name

        if not hasattr(self, "add_queue"):
            self.add_queue = queue.Queue()
        self.add_queue.put(
            (
                text,
                symbol,
                kind,
            )
        )

        self.add_data()

    def add_data(self):
        new_items = []
        try:
            while True:
                text, symbol, kind = self.add_queue.get_nowait()
                # print(text, symbol.kind_name.title())
                new_items.append(
                    (
                        text,
                        "icons/symbols/symbol_kind/type.png",
                        {
                            "info_func": functools.partial(
                                self.__info_func, text, symbol
                            ),
                            "click_func": functools.partial(
                                self.__click_func, symbol
                            ),
                            "scope": symbol.scope,
                        },
                        symbol,
                        kind,
                    )
                )
        except queue.Empty:
            for item in new_items:
                text, icon, in_data, symbol, kind = item
                # Adjust text
                text = "{}: {}".format(
                    text,
                    source_analyzer.entity_kind_name(kind).title(),
                )
                self.tree_items_add.append(
                    {
                        "text": text,
                        "icon": icon,
                        "in_data": in_data,
                        "symbol": symbol,
                        "kind": kind,
                    }
                )

            self.__initiate_add_remove_timer()

    def __initiate_add_remove_timer(self):
        qt.start_named_qtimer(
            owner=self,
            timer_name="adding_timer",
            interval_ms=100,
            callback=self.__add_remove_items,
        )

    def __add_remove_items(self):
        ## Add
        if len(self.tree_items_add) > 0:
            new_items = []
            remove_item_list = []
            for item in self.tree_items_add:
                symbol = item["symbol"]
                # Determine parent
                parent = None
                if symbol.scope is not None:
                    parent = symbol.scope._id
                else:
                    file_path = symbol.file
                    self.__check_header(file_path)
                    self.__add_main_node(
                        file_path,
                        file_path=file_path,
                    )
                    parent = self.main_nodes[file_path]
                # Add the new item to list
                new_items.append(
                    {
                        "text": item["text"],
                        "id": symbol._id,
                        "parent": parent,
                        "icon": item["icon"],
                        "data": item["in_data"],
                    }
                )

                remove_item_list.append(item)
            
            # Batch add items to tree
            self.multi_add(new_items)
            
            for ri in remove_item_list:
                self.tree_items_add.remove(ri)

            # Update item count and expand the main items
            for k, v in self.main_nodes.items():
                item_text = v.text(0)
                child_count = v.childCount()
                if "(" in item_text:
                    item_text = item_text[: item_text.index("(")].strip()
                text = f"{item_text} ({child_count})"
                v.setText(0, text)
                v.setExpanded(True)
            self.sort()

        else:
            self.__includers_remove_all()

        ## Remove
        if len(self.tree_items_remove) > 0:
            remove_item_list = []
            for item in self.tree_items_remove:
                symbol = item["symbol"]
                try:
                    self.remove(symbol._id)
                except:
                    print(
                        f"[NewFiletree] Could not delete symbol '{symbol._id} / {symbol.name}', skipping deletion."
                    )

                # Update item count
                for k, v in self.main_nodes.items():
                    item_text = v.text(0)
                    child_count = v.childCount()
                    if "(" in item_text:
                        item_text = item_text[: item_text.index("(")].strip()
                    text = f"{item_text} ({child_count})"
                    v.setText(0, text)

                remove_item_list.append(item)

            for ri in remove_item_list:
                self.tree_items_remove.remove(ri)

            self.empty_check()
            self.update_style()

    @qt.pyqtSlot(list)
    def symbols_removed(self, symbol_list):
        for symbol in symbol_list:
            kind = symbol.kind
            self.tree_items_remove.append(
                {
                    "symbol": symbol,
                }
            )

        self.__initiate_add_remove_timer()

    @qt.pyqtSlot(object)
    def symbol_removed(self, symbol):
        self.tree_items_remove.append(
            {
                "symbol": symbol,
            }
        )

        self.__initiate_add_remove_timer()

    def empty_check(self):
        for k in list(self.main_nodes.keys()):
            if self.main_nodes[k].childCount() == 0:
                self.remove(self.main_nodes[k].id)
                self.main_nodes.pop(k, None)

    def highlight(self, symbol):
        super()._highlight(symbol._id)

    def get_rightclick_menu_function(self):
        def show_menu():
            # Main menu
            menu = gui.templates.basemenu.BaseMenu(self.main_form)
            # Help action
            help_action = qt.QAction("Help", self.main_form)
            help_action.setStatusTip("Display editor help")
            help_action.setIcon(
                iconfunctions.get_qicon("icons/dialog/help.png")
            )

            def help_func(*args):
                helpdocs.help_texts.symbol_window_hamburger_help()
                return

            help_action.triggered.connect(help_func)
            menu.addAction(help_action)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        return show_menu


class SymbolDetailsProcessor(qt.QObject):
    processing_finished = qt.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    @qt.pyqtSlot(object)
    def process_symbol(self, symbol):

        def add_locations(name, single_field_name, field):
            last_index = len(field) - 1
            items = []
            for i, d in enumerate(reversed(field)):
                path = None
                offset = None
                line_number = None
                line = None
                line_from_offset = None
                internal = False

                if d.file is not None:
                    path = d.file.path
                    offset = d.begin_offset
                else:
                    internal = True

                try:
                    alternate_content = components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_alternative_content(
                        path
                    )
                    if alternate_content is not None:
                        line_number_raw = alternate_content[:offset].count("\n")
                        line_number = line_number_raw + 1
                        sl = alternate_content.split("\n")
                        line = sl[line_number_raw]
                        line_from_offset = line
                    else:
                        if os.path.isfile(path):
                            # Try to get the location information
                            line_number, line, line_from_offset = (
                                functions.get_line_from_offset(path, offset)
                            )
                        elif os.path.isdir(path):
                            internal = True
                except:
                    traceback.print_exc()

                if line is not None:
                    if len(line) > 40:
                        if len(line_from_offset) > 40:
                            line = "..." + line_from_offset[:34] + "..."
                        else:
                            try:
                                try:
                                    offset_in_line = line.index(
                                        line_from_offset
                                    )
                                except:
                                    offset_in_line = 0
                                diff_0 = len(line) - len(line_from_offset)
                                diff_1 = 37 - len(line_from_offset)
                                if diff_0 > diff_1:
                                    line = (
                                        "..." + line[offset_in_line - diff_1 :]
                                    )
                                else:
                                    line = line[:37] + "..."
                            except:
                                line = ""
                    line = line.replace("\n", "").replace("\r", "")

                if internal == True:
                    item_text = "internal"
                    tooltip = (
                        "This location is internal and has no source code."
                    )
                    icon_path = "icons/symbols/arrow.png"
                    items.append(
                        {
                            "text": item_text,
                            "id": None,
                            "parent": None,
                            "icon": icon_path,
                            "tooltip": tooltip,
                            "statustip": tooltip,
                        }
                    )

                else:
                    item_text = (
                        f"{os.path.basename(path)}, {line_number}, '{line}'"
                    )
                    tooltip = (
                        f"{name} information. "
                        + "Click to go to location. "
                        + "Right-click for more options."
                    )
                    icon_path = "icons/symbols/arrow.png"

                    items.append(
                        {
                            "text": item_text,
                            "id": None,
                            "parent": None,
                            "icon": icon_path,
                            "data": {
                                "info_func": {
                                    "func": "create_menu",
                                    "name": single_field_name,
                                    "path": path,
                                    "offset": offset,
                                    "item_text": item_text,
                                    "create_open_item": True,
                                },
                                "click_func": {
                                    "func": "goto",
                                    "path": path,
                                    "offset": offset,
                                },
                            },
                            "tooltip": tooltip,
                            "statustip": tooltip,
                        }
                    )

            return items

        lists = []

        # Name and type
        name_text = f"{symbol.kind_name} {symbol.name}"
        name_data = {
            "text": name_text,
            "icon": data.SYMBOL_ICONS["name"],
            "data": {
                "info_func": {
                    "func": "create_menu",
                    "name": "",
                    "path": "",
                    "offset": 0,
                    "item_text": name_text,
                    "create_open_item": False,
                },
                "click_func": None,
            },
        }
        lists.append((name_text, "name", None, name_data))
        # Definitions
        if len(symbol.definitions) > 0:
            definitions = {
                "text": (
                    "Strong Definitions ({}):".format(len(symbol.definitions))
                    if (len(symbol.definitions) > 0)
                    else "Strong Definitions: None"
                ),
                "icon": data.SYMBOL_ICONS["definition"],
                "tooltip": "All definitions of the symbol",
                "implicit_parent": False,
            }
            lists.append(
                ("Definitions", "definition", symbol.definitions, definitions)
            )
        # Weak definitions
        if len(symbol.weak_definitions) > 0:
            weak_definitions = {
                "text": (
                    "Weak Definitions ({}):".format(
                        len(symbol.weak_definitions)
                    )
                    if (len(symbol.weak_definitions) > 0)
                    else "Weak Definitions: None"
                ),
                "icon": data.SYMBOL_ICONS["weak definition"],
                "tooltip": "All weak definitions of the symbol",
                "implicit_parent": False,
            }
            lists.append(
                (
                    "Weak definitions",
                    "weak definition",
                    symbol.weak_definitions,
                    weak_definitions,
                )
            )
        # Tentative definitions
        if len(symbol.tentative_definitions) > 0:
            tentative_definitions = {
                "text": (
                    "Tentative Definitions ({}):".format(
                        len(symbol.tentative_definitions)
                    )
                    if (len(symbol.tentative_definitions) > 0)
                    else "Tentative Definitions: None"
                ),
                "icon": data.SYMBOL_ICONS["tentative definition"],
                "tooltip": "All tentative definitions of the symbol",
                "implicit_parent": False,
            }
            lists.append(
                (
                    "Tentative definitions",
                    "tentative definition",
                    symbol.tentative_definitions,
                    tentative_definitions,
                )
            )
        # Declarations
        if len(symbol.declarations) > 0:
            declarations = {
                "text": (
                    "Declarations ({}):".format(len(symbol.declarations))
                    if (len(symbol.declarations) > 0)
                    else "Declarations: None"
                ),
                "icon": data.SYMBOL_ICONS["declaration"],
                "tooltip": "All declarations of the symbol",
                "implicit_parent": False,
            }
            lists.append(
                (
                    "Declarations",
                    "declaration",
                    symbol.declarations,
                    declarations,
                )
            )
        # Usages
        usages_node = {
            "text": (
                "Uses ({}):".format(len(symbol.uses))
                if (len(symbol.uses) > 0)
                else "Uses: None"
            ),
            "icon": data.SYMBOL_ICONS["usage"],
            "tooltip": "All uses of the symbol",
            "implicit_parent": False,
        }
        lists.append(("Usages", "usage", symbol.uses, usages_node))

        return_dict = {}
        for l in lists:
            _name, _single_name, _list, _node = l
            if "implicit_parent" in _node.keys():
                items = add_locations(_name, _single_name, _list)
                _node["items"] = items
            return_dict[_name] = _node

        self.processing_finished.emit(return_dict)


class SymbolDetails(gui.templates.treewidget.TreeWidget):
    # Signals
    process_symbol = qt.pyqtSignal(object)
    # Attributes
    __thread = None
    __symbol_processor = None
    symbol = None

    def __init__(self, parent, main_form):
        super().__init__(
            parent, main_form, "SymbolDetails", "icons/gen/balls.png"
        )
        self.itemPressed.disconnect()
        self.itemPressed.connect(self.__press)
        # Symbol processing initialization
        self.__thread = qt.QThread(self)
        self.__symbol_processor = SymbolDetailsProcessor()
        self.__symbol_processor.processing_finished.connect(
            self.__symbol_processing_finished
        )
        self.process_symbol.connect(self.__symbol_processor.process_symbol)
        self.__symbol_processor.moveToThread(self.__thread)
        self.__thread.finished.connect(self.__thread.deleteLater)
        self.__thread.start()

    def self_destruct(self, *args):
        if self.__thread is not None:
            self.__thread.quit()
            del self.__thread

    def __press(self, *args):
        item, state = args
        buttons = data.application.mouseButtons()
        if buttons == qt.Qt.MouseButton.LeftButton:
            item_data = item.get_data()
            if self.symbol_click_type:
                if item_data is not None and "click_func" in item_data.keys():
                    if "mouse-position" in item_data.keys():
                        mouse_position = item_data["mouse-position"]
                        if (
                            mouse_position == "text"
                            or mouse_position == "icon-text"
                        ):
                            func = item_data["click_func"]
                            if isinstance(func, dict):
                                if func["func"] == "goto":
                                    goto(
                                        self,
                                        func["path"],
                                        func["offset"],
                                    )
                            elif callable(func):
                                func()
            else:
                if item_data is not None and "click_func" in item_data.keys():
                    func = item_data["click_func"]
                    if isinstance(func, dict):
                        if func["func"] == "goto":
                            goto(
                                self,
                                func["path"],
                                func["offset"],
                            )
                    elif callable(func):
                        func()

        elif buttons == qt.Qt.MouseButton.RightButton:
            item_data = item.get_data()
            if item_data is not None and "info_func" in item_data.keys():
                func = item_data["info_func"]
                if isinstance(func, dict) and func["func"] == "create_menu":
                    create_menu(
                        self,
                        func["name"],
                        func["path"],
                        func["offset"],
                        func["item_text"],
                        func["create_open_item"],
                    )
                elif callable(func):
                    func()

    @qt.pyqtSlot(dict)
    def __symbol_processing_finished(self, item_dict: dict) -> None:
        top_level_nodes = []
        for k, v in item_dict.items():
            node = self.add(
                text=v["text"],
                icon_path=v["icon"],
                implicit_parent=False,
            )
            if "items" in v.keys():
                for it in v["items"]:
                    it["parent"] = node
                self.multi_add(v["items"])
            top_level_nodes.append(node)
        self.addTopLevelItems(top_level_nodes)
        for tn in top_level_nodes:
            tn.setExpanded(True)

    def generate_symbol_information(self, symbol):
        self.setUpdatesEnabled(False)

        self.symbol = symbol
        self.clear_and_reset()

        # Symbol
        if isinstance(symbol, str) == False and (symbol is not None):
            lists = []

            self.process_symbol.emit(symbol)

        # Header
        elif isinstance(symbol, str):
            lists = []

            header_path = symbol

            # Name only
            header_name = os.path.basename(header_path)
            header_text = f"Header: {header_name}"
            header = self.add(
                text=header_text,
                icon_path="icons/symbols/occurrence_kind/header.png",
                in_data={
                    "info_func": functools.partial(
                        create_menu, self, "header", header_path, 0, header_text
                    ),
                    "click_func": functools.partial(
                        goto, self, header_path, None, 1
                    ),
                },
            )
            header.setToolTip(0, "A header file")
            # Path
            header_text = f"Path: {header_path}"
            path_item = self.add(
                text=header_text,
                icon_path="icons/gen/path.svg",
                in_data={
                    "info_func": functools.partial(
                        create_menu, self, "header", header_path, 0, header_text
                    ),
                    "click_func": functools.partial(
                        goto, self, header_path, None, 1
                    ),
                },
            )
            path_item.setToolTip(0, "The path to the header file")
            # Includers
            includes = components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_file_include_locations(
                header_path
            )
            if includes is not None:
                usages = self.add(
                    text=(
                        "Includers:"
                        if (len(includes) > 0)
                        else "Includers: None"
                    ),
                    icon_path=data.SYMBOL_ICONS["usage"],
                )
                usages.setToolTip(0, "All uses of the symbol")
                lists.append(("usages", includes, usages))

                # Add the lists
                for l in lists:
                    _name, _list, _parent = l
                    add_locations(self, _name, _list, _parent)
                    _parent.setExpanded(True)

        # Nothing
        else:
            nothing = self.add(
                text="Nothing found at this cursor position.",
                icon_path="icons/dialog/cross.png",
                tooltip="Nothing found at this cursor position.",
            )

        self.setUpdatesEnabled(True)


class SymbolWindow(qt.QFrame, gui.templates.baseobject.BaseObject):
    """The main symbol window stack frame that holds the file symbols and the
    detailed item view from the SymbolPopup."""

    # Private attributes
    __file_symbols = None
    __show_symbol_block = False
    __stored_cursor_symbol = None
    __symbol_details = None

    def __init__(self, parent, main_form, symbolhandler):
        qt.QFrame.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="SymbolStack",
            icon="icons/gen/balls.png",
        )
        wg = gui.templates.widgetgenerator
        # Create layout
        layout = wg.create_layout(
            vertical=True,
            parent=self,
        )
        self.setLayout(layout)

        # Add the stack selection buttons
        self.__cache_buttons = {}
        buttons_groupbox = wg.create_groupbox_with_layout(
            parent=self,
            name="ButtonsGroupBox",
            borderless=True,
            vertical=False,
            margins=(2, 2, 2, 2),
            spacing=2,
            h_size_policy=qt.QSizePolicy.Policy.Fixed,
            v_size_policy=qt.QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(buttons_groupbox)
        button_layout = buttons_groupbox.layout()
        # File symbols button
        file_symbols_button = wg.create_pushbutton(
            parent=buttons_groupbox,
            name="file-symbols-button",
            icon_name="icons/symbols/occurrence_kind/file.png",
            tooltip="Show the file symbols",
            statustip="Show the file symbols",
            click_func=lambda *args: self.set_current_widget(
                self.__file_symbols
            ),
            style="debugger",
        )
        file_symbols_button.setCheckable(True)
        button_layout.addWidget(file_symbols_button)
        button_layout.setAlignment(
            file_symbols_button,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        self.__cache_buttons["file-symbols-button"] = file_symbols_button
        # Symbol details button
        symbol_details_button = wg.create_pushbutton(
            parent=buttons_groupbox,
            name="symbol-details-button",
            icon_name="icons/symbols/symbol_kind/type.png",
            tooltip="Show the symbol details",
            statustip="Show the symbol details",
            click_func=lambda *args: self.set_current_widget(
                self.__symbol_details
            ),
            style="debugger",
        )
        symbol_details_button.setCheckable(True)
        button_layout.addWidget(symbol_details_button)
        button_layout.setAlignment(
            symbol_details_button,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        self.__cache_buttons["symbol-details-button"] = symbol_details_button

        # Add the stack
        self.stack = qt.QStackedWidget(self)
        self.stack.setObjectName("SymbolStack")
        layout.addWidget(self.stack)

        self.loading_symbol = False

        # Connect signals
        data.signal_dispatcher.show_symbol_details.connect(
            self.__show_symbol_details
        )

        # File symbols
        self.__file_symbols = FileSymbols(self, main_form, symbolhandler)
        self.stack.addWidget(self.__file_symbols)

        # Symbol details
        self.__symbol_details = SymbolDetails(self, main_form)
        self.stack.addWidget(self.__symbol_details)

        # Set the symbol window to be the default show widget
        self.set_current_widget(self.__file_symbols)

        self.update_style()

    def self_destruct(self, *args):
        if self.__symbol_details is not None:
            self.__symbol_details.self_destruct()

    def get_file_symbols(self):
        return self.__file_symbols

    def get_symbol_details(self):
        return self.__symbol_details

    def set_current_widget(self, widget):
        self.stack.setCurrentWidget(widget)
        if widget is self.__file_symbols:
            self.__cache_buttons["file-symbols-button"].setChecked(True)
            self.__cache_buttons["symbol-details-button"].setChecked(False)
        else:
            self.__cache_buttons["file-symbols-button"].setChecked(False)
            self.__cache_buttons["symbol-details-button"].setChecked(True)

    def show_file_symbols(self):
        self.set_current_widget(self.__file_symbols)

    def show_symbol_details(self, symbol=None):
        if symbol is not None:
            if self.__stored_cursor_symbol is None:
                self.__show_symbol_details(symbol)

            elif (
                isinstance(symbol, str)
                and self.__stored_cursor_symbol != symbol
            ):
                self.__show_symbol_details(symbol)

            elif not isinstance(symbol, str):
                if not isinstance(self.__stored_cursor_symbol, str):
                    if (
                        self.__stored_cursor_symbol.name != symbol.name
                        or self.__stored_cursor_symbol.kind != symbol.kind
                        or self.__stored_cursor_symbol.kind_name
                        != symbol.kind_name
                    ):
                        self.__show_symbol_details(symbol)
                    else:
                        self.set_current_widget(self.__symbol_details)
                else:
                    self.__show_symbol_details(symbol)

            else:
                # Just show the symbol details widget
                self.set_current_widget(self.__symbol_details)
        else:
            self.show_file_symbols()

    def reset_cursor_symbol(self):
        self.__stored_cursor_symbol = None

    @components.lockcache.cancelling_inter_process_lock(
        "show-symbols", cancel=True
    )
    def __show_symbol_details(self, symbol, show_tab=False):
        if not self.__show_symbol_block:
            self.set_current_widget(self.__symbol_details)
            if symbol is not None:
                self.__symbol_details.generate_symbol_information(symbol)
                self.__stored_cursor_symbol = symbol

                if show_tab:
                    try:
                        self._parent.setCurrentWidget(self)
                    except:
                        traceback.print_exc()
                        print(
                            "[SymbolWindow] Cannot focus Symbol-Window's tab!"
                        )

    def update_style(self):
        # Frame
        self.setStyleSheet(gui.stylesheets.frame.get_symbols_window())

        # Symbol trees
        self.get_file_symbols().update_style()
        self.get_symbol_details().update_style()

        # Buttons
        for k, v in self.__cache_buttons.items():
            v.update_style()
