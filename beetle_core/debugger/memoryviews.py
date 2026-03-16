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
import enum
import pprint
import traceback
import qt
import data
import functions
import iconfunctions
import gui.templates.baseobject
import gui.templates.widgetgenerator
import gui.stylesheets.frame
import gui.stylesheets.scrollbar


class MemoryViewType(enum.Enum):
    GeneralRegisters = "general-registers"
    SpecialFunctionRegisters = "special-function-registers"
    RawMemory = "raw-memory"
    VariableWatch = "variable-watch"


class MemoryViewBase(qt.QFrame, gui.templates.baseobject.BaseObject):
    def __init__(self, parent, main_form, typ):
        qt.QFrame.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=typ.name,
            icon="icons/memory/memory.png",
        )

        # Store view-type
        self.__type = typ

        # General attributes
        self.__auto_update = False
        self.table_view_offset = None

        # Connect the signals
        data.signal_dispatcher.debug_connected.connect(
            self.__debugger_connected
        )
        data.signal_dispatcher.debug_disconnected.connect(
            self.__debugger_disconnected
        )
        data.signal_dispatcher.debug_stack_updated.connect(self.stack_update)

    def get_type(self):
        return self.__type

    def get_auto_update(self):
        return self.__auto_update

    def __update_toggle_button(self):
        button = self.cache_buttons["update-toggle"]
        button.setChecked(self.get_auto_update())
        if self.get_auto_update() == True:
            button.setIcon(
                iconfunctions.get_qicon("icons/dialog/refresh-brown(check).png")
            )
        else:
            button.setIcon(
                iconfunctions.get_qicon("icons/dialog/refresh-brown(del).png")
            )

    def set_auto_update(self, value):
        self.__auto_update = value
        self.__update_toggle_button()

    def auto_update_toggle(self):
        self.__auto_update = not self.__auto_update
        self.__update_toggle_button()
        data.signal_dispatcher.save_layout.emit(True)

    def stack_update(self):
        raise Exception(
            "Unimplemented! Sub-class and create an implementation."
        )

    def show_update_memory(self):
        data.signal_dispatcher.memory_view_show_region.emit(
            self.get_type().value
        )

    def add_items(self, button_groups, parent, in_layout):
        """Function for adding items to the button bar."""
        wg = gui.templates.widgetgenerator

        for g, d in button_groups.items():
            # Add group
            new_group = wg.create_groupbox_with_layout(
                parent=parent,
                name=g,
                borderless=True,
                vertical=False,
                margins=(2, 2, 2, 2),
                spacing=2,
                h_size_policy=qt.QSizePolicy.Policy.Fixed,
                v_size_policy=qt.QSizePolicy.Policy.Fixed,
            )
            in_layout.addWidget(new_group)
            self.cache_views[g] = new_group

            # Add the comboboxes, if any
            if "comboboxes" in d.keys():
                for k, v in d["comboboxes"].items():
                    new_combobox = wg.create_advancedcombobox(
                        parent=new_group,
                        no_selection_text=v["initial-text"],
                    )
                    if "items" in v.keys():
                        for cbi in v["items"]:
                            new_combobox.add_item(cbi)
                    if "selected-item" in v.keys():
                        new_combobox.set_selected_name(v["selected-item"])
                    if "disabled" in v.keys() and v["disabled"] == True:
                        new_combobox.disable()
                    self.cache_comboboxes[v["name"]] = new_combobox
                    new_group.layout().addWidget(new_combobox)
                    new_group.layout().setAlignment(
                        new_combobox,
                        qt.Qt.AlignmentFlag.AlignLeft
                        | qt.Qt.AlignmentFlag.AlignVCenter,
                    )

            # Add buttons to group
            for k, v in d["buttons"].items():
                disabled = False
                if "disabled" in v.keys():
                    disabled = v["disabled"]
                checkable = False
                if "toggle" in v.keys():
                    checkable = v["toggle"]
                if "icon-path" in v.keys() or "icon" in v.keys():
                    new_button = wg.create_pushbutton(
                        parent=new_group,
                        name=v["name"],
                        icon_name=v["icon-path"],
                        tooltip=v["tooltip"],
                        statustip=v["tooltip"],
                        click_func=v["click-func"],
                        disabled=disabled,
                        style="debugger",
                        checkable=checkable,
                    )
                else:
                    new_button = wg.create_pushbutton(
                        parent=new_group,
                        name=v["name"],
                        text=v["text"],
                        tooltip=v["tooltip"],
                        statustip=v["tooltip"],
                        click_func=v["click-func"],
                        disabled=disabled,
                        style="debugger",
                        checkable=checkable,
                    )
                self.cache_buttons[v["name"]] = new_button
                new_group.layout().addWidget(new_button)
                new_group.layout().setAlignment(
                    new_button,
                    qt.Qt.AlignmentFlag.AlignLeft
                    | qt.Qt.AlignmentFlag.AlignVCenter,
                )

    def initialize_view(self, button_groups=None):
        wg = gui.templates.widgetgenerator

        # Initialize view element caches
        self.cache_views = {}
        self.cache_labels = {}
        self.cache_buttons = {}
        self.cache_comboboxes = {}

        # Layout
        layout = wg.create_layout(vertical=True)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(layout)

        # Scroll area
        scroll_area = wg.create_scroll_area()
        layout.addWidget(scroll_area)
        self.scroll_area = scroll_area
        # Main view
        main_view = wg.create_groupbox_with_layout(
            parent=self,
            name="DebuggerMainView",
            borderless=True,
            vertical=True,
        )
        scroll_area.setWidget(main_view)
        self.cache_views["main"] = main_view
        main_layout = main_view.layout()

        if button_groups is not None:
            self.add_items(button_groups, self, main_layout)

        # Main splitter
        widget_splitter = qt.QSplitter(qt.Qt.Orientation.Vertical, self)
        main_layout.addWidget(widget_splitter)
        self.widget_splitter = widget_splitter

        self.cache_table = {}

    """
    General
    """

    def __debugger_connected(self, *args):
        for k, v in self.cache_buttons.items():
            v.enable()
        for k, v in self.cache_comboboxes.items():
            v.enable()

    def __debugger_disconnected(self, *args):
        for k, v in self.cache_buttons.items():
            if k not in ("update-toggle",):
                v.disable()
        for k, v in self.cache_comboboxes.items():
            v.disable()

    def clear_all_memory(self):
        for name in self.cache_table.keys():
            table = self.cache_table[name]
            if not table.is_empty():
                model = table.model()
                if model is not None:
                    table.setModel(None)
                    model.deleteLater()
                table.set_empty()

    def clear_all_content(self):
        for table in self.cache_table.values():
            if not table.is_empty():
                model = table.model()
                if model is not None:
                    table.setModel(None)
                    model.deleteLater()
                table.set_empty()

    def update_style(self):
        # Frame
        self.setStyleSheet(gui.stylesheets.frame.get_default())

        # Table style
        self.setStyleSheet(gui.stylesheets.frame.get_memoryview())
        for k, v in self.cache_table.items():
            v.horizontalHeader().setSectionResizeMode(
                qt.QHeaderView.ResizeMode.ResizeToContents
            )
            v.verticalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )
            v.horizontalScrollBar().setContextMenuPolicy(
                qt.Qt.ContextMenuPolicy.NoContextMenu
            )

        # Rest
        for k, v in self.cache_buttons.items():
            v.update_style()
        for k, v in self.cache_labels.items():
            v.update_style()
        for k, v in self.cache_comboboxes.items():
            v.update_style()


class MemoryViewGeneralRegisters(MemoryViewBase):
    def __init__(self, parent, main_form):
        super().__init__(
            parent,
            main_form,
            MemoryViewType.GeneralRegisters,
        )

        # Initialize the special attributes
        self.__row_limit = 8
        self.__register_cache = {}

        # Initialize the view
        self.initialize_view()

        # Update style
        self.update_style()

    def initialize_view(self):
        # Button groups
        button_groups = {
            "general": {
                "buttons": {
                    "display-memory": {
                        "name": "display-memory",
                        "text": "DISPLAY-MEMORY",
                        "icon-path": "icons/chip/chip(refresh).png",
                        "tooltip": (
                            "DOWNLOAD-AND-DISPLAY-MEMORY:\n\nDownload and display the memory table."
                        ),
                        "disabled": not data.debugging_active,
                        "click-func": self.show_update_memory,
                    },
                    "update-toggle": {
                        "name": "update-toggle",
                        "text": "UPDATE-TOGGLE",
                        "icon-path": "icons/dialog/refresh.svg",
                        "tooltip": (
                            "UPDATE-TOGGLE:\n\nToggle of the automatic refresh of this memory table\non every debugger stack update."
                        ),
                        "toggle": True,
                        "click-func": self.auto_update_toggle,
                    },
                }
            },
        }
        # Initialize view
        super().initialize_view(button_groups=button_groups)

        # Add register view
        new_table = MemoryTable(self)
        new_table.setObjectName("RegisterTable")
        tooltip = (
            "This table is used for displaying general register data\n"
            + "by selecting the 'General Registers' option in the the dropdown menu\n"
            + "of the debugger's 'Show a memory region' dropdown box."
        )
        new_table.setToolTip(tooltip)
        new_table.setStatusTip(tooltip)
        self.widget_splitter.addWidget(new_table)
        self.cache_table["register"] = new_table

    def __parse_register_name(self, register):
        return register["name"].lower()

    def show_general_register_data(self, _data):
        table = self.cache_table["register"]

        table.setSortingEnabled(False)
        table.setUpdatesEnabled(False)

        # Clean the model
        model = table.model()
        if model is not None:
            table.setModel(None)
            model.deleteLater()

        # Table Settings
        table.verticalHeader().hide()
        table.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setEditTriggers(qt.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(
            qt.QAbstractItemView.SelectionMode.SingleSelection
        )
        #        table.itemSelectionChanged.connect(self._table_selection_changed)
        #        table.itemClicked.connect(self._table_item_clicked)

        # Filter the data to columns based on row limit
        column_list = []
        current_list = []
        registers = [v for k, v in _data.items()]
        registers.sort(key=self.__parse_register_name)
        for v in registers:
            # Name
            name = v["name"]
            # Value
            try:
                value = "{:08x}".format(int(v["value"], 16))
            except:
                value = v["value"]
            if value is None:
                value = ""
            # Color
            color = None
            if name in self.__register_cache.keys():
                previous_value = self.__register_cache[name]
                if value != previous_value:
                    color = "green"
            self.__register_cache[name] = value
            current_list.append((name, value, color))
            if len(current_list) >= self.__row_limit:
                column_list.append(current_list)
                current_list = []
        else:
            if len(current_list) > 0:
                column_list.append(current_list)

        # Create rows
        rows = []
        for row in range(len(column_list[0])):
            current_row = []
            for col in range(len(column_list)):
                if row < len(column_list[col]):
                    column_data = column_list[col][row]
                    current_row.append((column_data[0], None))
                    current_row.append((column_data[1], column_data[2]))
            rows.append(current_row)

        # Headers
        headers = {}
        widths = []
        for i, item in enumerate(range(len(rows[0]))):
            if (i % 2) == 0:
                headers[i] = "Register"
                widths.append(80)
            else:
                headers[i] = "Value"
                widths.append(80)

        model = HexRegisterModel(rows, headers, parent=table)
        table.setModel(model)

        # Column widths
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)

        # Set the table state to not-empty
        table.set_filled()

        table.setUpdatesEnabled(True)

        # Cannot be called directly, because then the positions are
        # restored to early and are incorrect
        qt.QTimer.singleShot(0, self.update_scroll_position)

    def update_scroll_position(self):
        if self.table_view_offset is not None:
            # Update previous view
            table = self.cache_table["register"]
            x, y = self.table_view_offset
            table.horizontalScrollBar().setValue(x)
            table.verticalScrollBar().setValue(y)

    def stack_update(self):
        if self.get_auto_update():
            table = self.cache_table["register"]
            x = table.horizontalScrollBar().value()
            y = table.verticalScrollBar().value()
            self.table_view_offset = (x, y)
            self.show_update_memory()


class MemoryViewRawMemory(MemoryViewBase):
    def __init__(self, parent, main_form, typ):
        super().__init__(
            parent,
            main_form,
            MemoryViewType.RawMemory,
        )

        self.__memory_type = typ

        # Initialize the view
        self.initialize_view()

        # Connect the additional signals
        data.signal_dispatcher.memory_view_clear_memory.connect(
            self.clear_all_memory
        )
        #        data.signal_dispatcher.memory_view_clear_all.connect(self.clear_all_content)

        # Update style
        self.update_style()

    def get_memory_type(self):
        return self.__memory_type

    def initialize_view(self):
        # Button groups
        button_groups = {
            "general": {
                "buttons": {
                    "display-memory": {
                        "name": "display-memory",
                        "text": "DISPLAY-MEMORY",
                        "icon-path": "icons/chip/chip(refresh).png",
                        "tooltip": (
                            "DOWNLOAD-AND-DISPLAY-MEMORY:\n\nDownload and display the memory table.\nMay take a long time depending on the\nsize of the memory region."
                        ),
                        "disabled": not data.debugging_active,
                        "click-func": self.show_update_memory,
                    },
                    "update-toggle": {
                        "name": "update-toggle",
                        "text": "UPDATE-TOGGLE",
                        "icon-path": "icons/dialog/refresh.svg",
                        "tooltip": (
                            "UPDATE-TOGGLE:\n\nToggle of the automatic refresh of this memory table\non every debugger stack update."
                        ),
                        "toggle": True,
                        "click-func": self.auto_update_toggle,
                    },
                }
            },
        }
        # Initialize view
        super().initialize_view(button_groups=button_groups)

        # Add memory table
        new_table = MemoryTable(self)
        new_table.setObjectName("MemoryTable")
        tooltip = (
            "This table is used for displaying memory data\n"
            + "by selecting a memory option in the dropdown menu\n"
            + "of the debugger's 'Show a memory region' dropdown box."
        )
        new_table.setToolTip(tooltip)
        new_table.setStatusTip(tooltip)
        self.widget_splitter.addWidget(new_table)
        self.cache_table["memory"] = new_table

    def show_memory_data(self, address, contents_list):
        table = self.cache_table["memory"]

        table.setSortingEnabled(False)
        table.setUpdatesEnabled(False)

        # Clean the model
        model = table.model()
        if model is not None:
            table.setModel(None)
            model.deleteLater()

        # Table Settings
        table.verticalHeader().hide()
        table.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setEditTriggers(qt.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(
            qt.QAbstractItemView.SelectionMode.SingleSelection
        )
        #        table.itemSelectionChanged.connect(self._table_selection_changed)
        #        table.itemClicked.connect(self._table_item_clicked)

        verticalHeader = table.verticalHeader()
        verticalHeader.setSectionResizeMode(qt.QHeaderView.ResizeMode.Fixed)
        horizontalHeader = table.horizontalHeader()
        horizontalHeader.setSectionResizeMode(qt.QHeaderView.ResizeMode.Fixed)

        # Parse the data into lists of 16
        size = 16
        chunks = [
            contents_list[x : x + size]
            for x in range(0, len(contents_list), size)
        ]

        # Add the data
        address_offset = 0
        rows = []
        for chunk in chunks:
            # Address
            current_address = address + address_offset
            address_offset += size
            address_string = "{:04x}".format(current_address, 16)
            # ASCII string
            ascii_list = []
            for num in chunk:
                char = chr(int(num, 16))
                if (
                    char
                    in """0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&'()*+,-./:;<=>?@[]^_`{|}~"""
                ):
                    ascii_list.append(char)
                else:
                    ascii_list.append(".")
            ascii_string = "".join(ascii_list)
            # Create row
            row = [address_string] + chunk + [ascii_string]
            rows.append(row)

        # Set headers and rows
        model = HexMemoryModel(rows, parent=table)
        table.setModel(model)

        # Column widths
        widths = [
            100,
            *[40 for x in range(size)],
            140,
        ]
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)

        # Set the table state to not-empty
        table.set_filled()

        table.setUpdatesEnabled(True)

        # Cannot be called directly, because then the positions are
        # restored to early and are incorrect
        qt.QTimer.singleShot(0, self.update_scroll_position)

    def update_scroll_position(self):
        if self.table_view_offset is not None:
            # Update previous view
            table = self.cache_table["memory"]
            x, y = self.table_view_offset
            table.horizontalScrollBar().setValue(x)
            table.verticalScrollBar().setValue(y)

    def show_update_memory(self):
        data.signal_dispatcher.memory_view_show_region.emit(
            self.get_memory_type()
        )

    def stack_update(self):
        #        print(self.get_memory_type(), self.get_auto_update())
        if self.get_auto_update():
            table = self.cache_table["memory"]
            x = table.horizontalScrollBar().value()
            y = table.verticalScrollBar().value()
            self.table_view_offset = (x, y)
            self.show_update_memory()
        else:
            self.clear_all_memory()


class MemoryViewVariableWatch(MemoryViewBase):
    def __init__(self, parent, main_form):
        super().__init__(
            parent,
            main_form,
            MemoryViewType.VariableWatch,
        )

        # Initialize the view
        self.initialize_view()

        # Connect the additional signals
        data.signal_dispatcher.memory_watch_add_variable.connect(
            self.watch_add_variable
        )
        data.signal_dispatcher.memory_watch_update_variables.connect(
            self.watch_update_variables
        )
        data.signal_dispatcher.memory_watch_delete_variable.connect(
            self.watch_delete_variable
        )
        data.signal_dispatcher.memory_watch_delete_all_variables.connect(
            self.watch_delete_all
        )

        # Update style
        self.update_style()

    def initialize_view(self):
        super().initialize_view()

        wg = gui.templates.widgetgenerator

        # Add variable watch window
        watch_groupbox = wg.create_groupbox_with_layout(
            parent=self,
            name="DebuggerConsoleView",
            borderless=True,
            vertical=True,
            h_size_policy=qt.QSizePolicy.Policy.MinimumExpanding,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        tooltip = "This table is used for displaying variables that are being watched.\nThese variables are added by typing their names\nin the input field at the bottom of this window."
        watch_groupbox.setToolTip(tooltip)
        watch_groupbox.setStatusTip(tooltip)
        self.widget_splitter.addWidget(watch_groupbox)
        self.cache_views["watch"] = watch_groupbox
        # Watch table
        new_table = WatchTable(self)
        new_table.setObjectName("WatchTable")
        watch_groupbox.layout().addWidget(new_table)
        self.cache_table["watch"] = new_table
        # Input widget
        watch_input = wg.create_textbox(
            name="DebuggerwatchInput", parent=watch_groupbox
        )
        watch_input.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Fixed,
            )
        )
        tooltip = "Enter variable names (space separated)"
        watch_input.setToolTip(tooltip)
        watch_input.setPlaceholderText(tooltip)

        def check_text(*args, **kwargs):
            if watch_input.text() == "":
                watch_input.setProperty("showing-placeholder-text", True)
            else:
                watch_input.setProperty("showing-placeholder-text", False)
            watch_input.style().unpolish(watch_input)
            watch_input.style().polish(watch_input)
            watch_input.update()

        check_text()
        watch_input.textChanged.connect(check_text)
        watch_input.returnPressed.connect(self.watch_input_request)
        watch_input.key_release_signal.connect(self.watch_input_keypress)
        self.watch_input = watch_input
        self.watch_input.setEnabled(False)
        watch_groupbox.layout().addWidget(watch_input)

    """
    Watch window
    """
    watch_variables = {}

    def has_variables(self):
        return len(self.watch_variables.keys()) > 0

    def watch_add_variable(self, variable_data):
        """{ 'has_more': '0', 'name': 'a', 'numchild': '0', 'thread-id': '1',
        'type': 'volatile int', 'value': '123' }"""
        #        pprint.pprint(variable_data)
        name = variable_data["name"]
        self.watch_variables[name] = variable_data
        self.watch_update_table()

    def watch_delete_variable(self, name):
        if name in self.watch_variables.keys():
            self.watch_variables.pop(name)
        self.watch_update_table()

    def watch_delete_all(self):
        for name in list(self.watch_variables.keys()):
            data.signal_dispatcher.memory_watch_delete_variable.emit(name)
        self.watch_variables = {}
        self.watch_update_table()

    def watch_update_variables(self, new_data):
        """
        {
            'changelist': [
                {
                    'has_more': '0',
                    'in_scope': 'true',
                    'name': 'a',
                    'type_changed': 'false',
                    'value': '333'
                }
            ]
        }
        """
        if "changelist" in new_data.keys():
            changelist = new_data["changelist"]
            # Check if any changes are present
            if len(changelist) == 0:
                return

            # Update variables
            for c in changelist:
                if "name" in c.keys() and "value" in c.keys():
                    name = c["name"]
                    value = c["value"]
                    if name in self.watch_variables.keys():
                        self.watch_variables[name]["value"] = value
            # Update watch table
            self.watch_update_table()

    def watch_update_table(self):
        table = self.cache_table["watch"]

        table.setSortingEnabled(False)
        table.setUpdatesEnabled(False)

        # Clean the model
        model = table.model()
        if model is not None:
            table.setModel(None)
            model.deleteLater()

        # Table Settings
        table.verticalHeader().hide()
        table.setSelectionBehavior(
            qt.QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setEditTriggers(qt.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(
            qt.QAbstractItemView.SelectionMode.SingleSelection
        )
        #        table.itemSelectionChanged.connect(self._table_selection_changed)
        #        table.itemClicked.connect(self._table_item_clicked)

        if len(self.watch_variables) == 0:
            return

        # Add the data
        rows = []
        for k, v in self.watch_variables.items():
            name = v["name"]
            if name.endswith("_ptr"):
                name = "*{}".format(name.replace("_ptr", ""))
            new_row = {
                "name": v["name"],
                "type": v["type"],
                "value": v["value"],
                "color": None,
            }
            rows.append(new_row)

        model = HexWatchModel(rows, parent=table)
        table.setModel(model)

        # Set the table state to not-empty
        table.set_filled()

        table.setSortingEnabled(True)
        table.setUpdatesEnabled(True)

    """
    Watch input
    """
    watch_buffer_list = []
    watch_buffer_index = 0

    def watch_input_request(self, *args) -> None:
        command = self.watch_input.text().strip()
        self.watch_input.setText("")
        if command != "":
            if (
                len(self.watch_buffer_list) > 0
                and command != self.watch_buffer_list[-1]
                or len(self.watch_buffer_list) == 0
            ):
                self.watch_buffer_list.append(command)
            self.watch_buffer_index = len(self.watch_buffer_list)
        if command == "":
            return
        for c in command.split():
            data.signal_dispatcher.debug_variable_object_create.emit(c.strip())

    def watch_input_keypress(self, key):
        if len(self.watch_buffer_list) == 0:
            return

        if key == qt.Qt.Key.Key_Up:
            self.watch_buffer_index -= 1
            if self.watch_buffer_index < 0:
                self.watch_buffer_index = 0
            stored_command = self.watch_buffer_list[self.watch_buffer_index]
            self.watch_input.setText(stored_command)
        elif key == qt.Qt.Key.Key_Down:
            self.watch_buffer_index += 1
            last_index = len(self.watch_buffer_list) - 1
            if self.watch_buffer_index > last_index:
                self.watch_buffer_index = last_index
            stored_command = self.watch_buffer_list[self.watch_buffer_index]
            self.watch_input.setText(stored_command)

    def stack_update(self):
        pass


class MemoryTableState(enum.Enum):
    Empty = enum.auto()
    Filled = enum.auto()


class MemoryTable(qt.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__state = MemoryTableState.Empty

    def is_empty(self) -> bool:
        return self.__state == MemoryTableState.Empty

    def set_empty(self):
        self.__state = MemoryTableState.Empty

    def set_filled(self):
        self.__state = MemoryTableState.Filled


class WatchTable(MemoryTable):
    context_menu = None

    def __manual_update(self, *args):
        data.signal_dispatcher.memory_watch_manual_update.emit()

    def delete_variable(self, name, row):
        data.signal_dispatcher.memory_watch_delete_variable.emit(name)

    def delete_all(self):
        data.signal_dispatcher.memory_watch_delete_all_variables.emit()

    def contextMenuEvent(self, event):
        position = event.pos()
        row = self.rowAt(position.y())
        col = self.columnAt(position.y())
        item = None
        model = self.model()
        if model is None:
            return
        if row != -1:
            var_name = model.data(model.index(row, 0))

            # Create a menu
            if self.context_menu is not None:
                self.context_menu.setParent(None)
                self.context_menu = None
            self.context_menu = gui.templates.basemenu.BaseMenu(self)

            text = "Delete '{}' from table".format(var_name)
            new_action = qt.QAction(text, self.context_menu)
            new_action.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )

            def delete(*args):
                actual_name = var_name
                if var_name.startswith("*"):
                    actual_name = "{}_ptr".format(var_name[1:])
                self.delete_variable(actual_name, row)

            new_action.triggered.connect(delete)
            new_action.setStatusTip(text)
            self.context_menu.addAction(new_action)

            # Show menu
            cursor = qt.QCursor.pos()
            self.context_menu.popup(cursor)
            return super().contextMenuEvent(event)

        else:
            # Create a menu
            if self.context_menu is not None:
                self.context_menu.setParent(None)
                self.context_menu = None
            self.context_menu = gui.templates.basemenu.BaseMenu(self)

            text = "Update variable values"
            new_action = qt.QAction(text, self.context_menu)
            new_action.setIcon(
                iconfunctions.get_qicon("icons/dialog/refresh.png")
            )
            new_action.triggered.connect(self.__manual_update)
            new_action.setStatusTip(text)
            self.context_menu.addAction(new_action)

            text = "Delete all variables"
            new_action = qt.QAction(text, self.context_menu)
            new_action.setIcon(
                iconfunctions.get_qicon("icons/dialog/cross.png")
            )
            new_action.triggered.connect(self.delete_all)
            new_action.setStatusTip(text)
            self.context_menu.addAction(new_action)

            # Show menu
            cursor = qt.QCursor.pos()
            self.context_menu.popup(cursor)
            return super().contextMenuEvent(event)


"""
Table models
"""


class HexMemoryModel(qt.QAbstractTableModel):
    def __init__(self, row_data, parent=None):
        super().__init__(parent)
        self.__row_data = row_data
        self.__last_index = len(row_data[0]) - 1
        self.__headers = {0: "Address", self.__last_index: "ASCII"}
        for i in range(len(row_data[0]) - 2):
            self.__headers[i + 1] = "{:02x}".format(i)

    def rowCount(self, parent=None):
        return len(self.__row_data)

    def columnCount(self, parent=None):
        return len(self.__row_data[0]) if self.rowCount() else 0

    def data(self, index, role=qt.Qt.ItemDataRole.DisplayRole):
        if role == qt.Qt.ItemDataRole.DisplayRole:
            return self.__row_data[index.row()][index.column()]

        elif role == qt.Qt.ItemDataRole.TextAlignmentRole:
            column = index.column()
            if column == self.__last_index:
                return (
                    qt.Qt.AlignmentFlag.AlignLeft
                    | qt.Qt.AlignmentFlag.AlignVCenter
                )
            else:
                return (
                    qt.Qt.AlignmentFlag.AlignHCenter
                    | qt.Qt.AlignmentFlag.AlignVCenter
                )

    def headerData(
        self, section, orientation, role=qt.Qt.ItemDataRole.DisplayRole
    ):
        if (
            orientation == qt.Qt.Orientation.Horizontal
            and role == qt.Qt.ItemDataRole.DisplayRole
        ):
            return self.__headers[section]
        return super().headerData(section, orientation, role)


class HexRegisterModel(qt.QAbstractTableModel):
    def __init__(self, row_data, headers, parent=None):
        super().__init__(parent)
        self.__row_data = row_data
        self.__headers = headers

    def rowCount(self, parent=None):
        return len(self.__row_data)

    def columnCount(self, parent=None):
        return len(self.__row_data[0]) if self.rowCount() else 0

    def data(self, index, role=qt.Qt.ItemDataRole.DisplayRole):
        if role == qt.Qt.ItemDataRole.DisplayRole:
            try:
                value, color = self.__row_data[index.row()][index.column()]
                return value
            except:
                return ""

        elif role == qt.Qt.ItemDataRole.TextAlignmentRole:
            return (
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )

        elif role == qt.Qt.ItemDataRole.BackgroundRole:
            try:
                value, color = self.__row_data[index.row()][index.column()]
                if color is not None:
                    return qt.QColor(color)
            except:
                pass

    def headerData(
        self, section, orientation, role=qt.Qt.ItemDataRole.DisplayRole
    ):
        if (
            orientation == qt.Qt.Orientation.Horizontal
            and role == qt.Qt.ItemDataRole.DisplayRole
        ):
            return self.__headers[section]
        return super().headerData(section, orientation, role)


class HexWatchModel(qt.QAbstractTableModel):
    def __init__(self, row_data, parent=None):
        super().__init__(parent)
        self.__row_data = row_data
        self.__headers = {
            0: ("Name", "name"),
            1: ("Value", "value"),
            2: ("Type", "type"),
        }

    def rowCount(self, parent=None):
        return len(self.__row_data)

    def columnCount(self, parent=None):
        return len(self.__headers.keys()) if self.rowCount() else 0

    def data(self, index, role=qt.Qt.ItemDataRole.DisplayRole):
        if role == qt.Qt.ItemDataRole.DisplayRole:
            try:
                column_name = self.__headers[index.column()][1]
                value = self.__row_data[index.row()][column_name]
                return value
            except:
                return ""

        elif role == qt.Qt.ItemDataRole.TextAlignmentRole:
            return (
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter
            )

        elif role == qt.Qt.ItemDataRole.BackgroundRole:
            try:
                color = self.__row_data[index.row()]["color"]
                if color is not None:
                    return qt.QColor(color)
            except:
                pass

    def headerData(
        self, section, orientation, role=qt.Qt.ItemDataRole.DisplayRole
    ):
        if (
            orientation == qt.Qt.Orientation.Horizontal
            and role == qt.Qt.ItemDataRole.DisplayRole
        ):
            return self.__headers[section][0]
        return super().headerData(section, orientation, role)
