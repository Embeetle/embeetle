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

from typing import *
import os
import re
import enum
import json
import time
import queue
import pprint
import traceback
import threading
import subprocess
import qt
import data
import functions
import gui.forms.customeditor
import gui.templates.baseobject
import gui.templates.widgetgenerator
import gui.stylesheets.splitter
import gui.templates.textmanipulation
import debugger.debugger
import debugger.breakpointwidget
import debugger.stackframewidget


def safe_execute(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as ex:
            self.console_write(
                "<b style='color:{};'>[Send-Command-Error]</b><br>".format(
                    data.theme["indication"]["error"],
                ),
                html=True,
            )
            self.console_write(
                "&nbsp;&nbsp;&nbsp;&nbsp;<b style='color:{};'>{}</b><br>".format(
                    data.theme["indication"]["error"],
                    str(ex),
                ),
                html=True,
            )

    return wrapper


class DebugState(enum.Enum):
    Disconnected = enum.auto()
    Halted = enum.auto()
    Running = enum.auto()
    Unknown = enum.auto()


class DebuggerWindow(qt.QStackedWidget, gui.templates.baseobject.BaseObject):
    debugger_command_completed_signal = qt.pyqtSignal(object)

    __debugger = None
    __state = None
    __cache_views = None
    __cache_labels = None
    __cache_buttons = None
    __cache_comboboxes = None
    __cache_input_fields = None
    __stored_editor_data = None
    __stored_breakpoint_data = None
    __stored_watchpoint_data = None
    __stored_general_register_data = None
    __stack_cursor_data = None

    def self_destruct(self):
        if self.__debugger is not None:
            self.__debugger.self_destruct()
            self.__debugger = None
        if self.__cache_views is not None:
            for v in self.__cache_views:
                try:
                    v.deleteLater()
                    v.setParent(None)
                except:
                    pass
            self.__cache_views = None

    def __init__(self, parent, main_form):
        qt.QStackedWidget.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="DebuggerWindow",
            icon="icons/gen/debug.png",
        )
        self.__initialize_view()
        self.update_style()

        self.state = DebugState.Disconnected

        self.__program_state_changed(data.program_state)

        # Signal connections
        data.signal_dispatcher.program_state_changed.connect(
            self.__program_state_changed
        )
        data.signal_dispatcher.debug_state_changed.connect(
            self.__debug_state_changed
        )
        data.signal_dispatcher.debug_breakpoint_insert.connect(
            self.debugger_breakpoint_insert
        )
        data.signal_dispatcher.debug_breakpoint_delete.connect(
            self.debugger_breakpoint_delete
        )
        data.signal_dispatcher.debug_watchpoint_insert.connect(
            self.debugger_watchpoint_insert
        )
        data.signal_dispatcher.debug_watchpoint_delete.connect(
            self.debugger_watchpoint_delete
        )
        data.signal_dispatcher.debug_delete_all_watch_and_break_points.connect(
            self.debugger_delete_all_watch_and_break_points
        )
        data.signal_dispatcher.memory_view_show_region.connect(
            self.debugger_show_memory_region
        )
        data.signal_dispatcher.debug_variable_object_create.connect(
            self.debugger_variable_object_create
        )
        data.signal_dispatcher.memory_watch_manual_update.connect(
            self.debugger_variable_object_update
        )
        data.signal_dispatcher.memory_watch_delete_variable.connect(
            self.debugger_variable_object_delete
        )
        data.signal_dispatcher.source_analyzer.memory_regions_update.connect(
            self.__update_memory_regions
        )

        self.installEventFilter(self)

        self.__sai = functions.import_module(
            "components.sourceanalyzerinterface"
        ).SourceAnalysisCommunicator()

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value: DebugState) -> None:
        if self.__state == value:
            data.signal_dispatcher.debug_state_changed.emit(value)
            return

        colors = {
            DebugState.Disconnected: data.theme["fonts"]["default"]["color"],
            DebugState.Halted: data.theme["fonts"]["warning"]["color"],
            DebugState.Running: data.theme["fonts"]["success"]["color"],
            DebugState.Unknown: data.theme["fonts"]["error"]["color"],
        }
        text = "<b style='color:{};'>{}</b>".format(
            colors[value],
            value.name,
        )
        self.__cache_labels["state-value"].setText(text)
        self.__state = value
        data.signal_dispatcher.debug_state_changed.emit(value)

    def eventFilter(self, object, event):
        if event.type() == qt.QEvent.Type.MouseButtonPress:
            self.set_focus()

        return super().eventFilter(object, event)

    def hideEvent(self, event):
        return super().hideEvent(event)

    def set_focus(self):
        self.setFocus()

    def __program_state_changed(self, new_state):
        if new_state != data.ProgramState.Flashed:
            self.__warning_show(
                f"""
<p style="color: {data.theme["fonts"]["error"]["color"]}; background-color: {data.theme["fonts"]["error"]["background"]}">
    <b>&nbsp;Not flashed - debugger displays may be inconsistent with source code!</b>
</p>
"""
            )
        else:
            self.__warning_hide()

    def __initialize_view(self):
        wg = gui.templates.widgetgenerator

        # Initialize view element caches
        self.__cache_views = {}
        self.__cache_labels = {}
        self.__cache_buttons = {}
        self.__cache_comboboxes = {}
        self.__cache_input_fields = {}
        # Scroll area
        scroll_area = wg.create_scroll_area()
        self.addWidget(scroll_area)
        self.setCurrentWidget(scroll_area)
        # Main view
        main_view = wg.create_groupbox_with_layout(
            parent=self,
            name="DebuggerMainView",
            borderless=True,
            vertical=True,
        )
        scroll_area.setWidget(main_view)
        self.__cache_views["main"] = main_view

        # Button groups
        button_groups = {
            "experimental": {
                "buttons": {
                    "connect-direct": {
                        "name": "connect-direct",
                        "text": "DIRECT-CONNECT",
                        "icon-path": "icons/debug/connect.png",
                        "tooltip": (
                            "CONNECT:\n\nConnect the debugger directly without OpenOCD and stop execution."
                        ),
                        "click-func": self.debugger_connect_direct,
                    },
                },
                "input-fields": {
                    "gdb-url-input": {
                        "name": "gdb-url",
                        "initial-text": "localhost:3333",
                    },
                },
            },
            "general": {
                "buttons": {
                    "connect": {
                        "name": "connect",
                        "text": "CONNECT",
                        "icon-path": "icons/debug/connect.png",
                        "tooltip": (
                            "CONNECT:\n\nConnect the debugger and stop execution."
                        ),
                        "click-func": self.debugger_connect,
                    },
                    "disconnect": {
                        "name": "disconnect",
                        "text": "DISCONNECT",
                        "icon-path": "icons/debug/disconnect.png",
                        "tooltip": "DISCONNECT:\n\nDisconnect the debugger.",
                        "click-func": self.debugger_disconnect,
                    },
                    "reset": {
                        "name": "reset",
                        "text": "RESET/HALT",
                        "icon-path": "icons/debug/reset(pause).png",
                        "tooltip": (
                            "RESET & HALT:\n\nHalts the program execution and resets the program counter through OpenOCD."
                        ),
                        "click-func": self.debugger_reset_halt,
                    },
                    "halt": {
                        "name": "halt",
                        "text": "HALT",
                        "icon-path": "icons/debug/pause.png",
                        "tooltip": (
                            "HALT:\n\nHalts the program execution through OpenOCD."
                        ),
                        "click-func": self.debugger_halt,
                    },
                    "continue": {
                        "name": "continue",
                        "text": "CONTINUE",
                        "icon-path": "icons/debug/run.png",
                        "tooltip": (
                            "RUN:\n\nResumes the execution of the inferior program,\nwhich will continue to execute until it reaches a debugger stop event."
                        ),
                        "click-func": self.debugger_continue,
                    },
                    "step": {
                        "name": "step",
                        "text": "STEP",
                        "icon-path": "icons/debug/step_in.png",
                        "tooltip": (
                            "STEP-IN:\n\nResumes execution of the inferior program, stopping when the beginning of the next source line is reached,\nif the next source line is not a function call. If it is, stop at the first instruction of the called function."
                        ),
                        "click-func": self.debugger_step,
                    },
                    "next": {
                        "name": "next",
                        "text": "NEXT",
                        "icon-path": "icons/debug/step_over.png",
                        "tooltip": (
                            "STEP-OVER:\n\nResumes execution of the inferior program,\nstopping when the beginning of the next source line is reached. "
                        ),
                        "click-func": self.debugger_next,
                    },
                    "finish": {
                        "name": "finish",
                        "text": "FINISH",
                        "icon-path": "icons/debug/step_out.png",
                        "tooltip": (
                            "STEP-OUT:\n\nResumes the execution of the inferior program until the current function is exited.\nDisplays the results returned by the function."
                        ),
                        "click-func": self.debugger_finish,
                    },
                }
            },
            "register-memory": {
                "comboboxes": {
                    "memory-region-select": {
                        "name": "memory-region-select",
                        "initial-text": "Select memory region",
                        "disabled": not data.debugging_active,
                        "tooltip": (
                            "Selecting a memory region from this drop-down menu\n"
                            + "will open the appropriate memory window and\n"
                            + "download and display the appropriate memory region,\n"
                            + "based on what was selected.\n\n"
                            + "NOTE: This may take a few seconds for larger memory regions like RAM or FLASH,\n"
                            + "      depending on the microcontroller."
                        ),
                        "statustip": (
                            "Select an option to view a memory region in a separate window"
                        ),
                    }
                },
                "buttons": {
                    #                    "show-memory-region": {
                    #                        "name": "show-memory-region",
                    #                        "text": "SHOW-MEMORY",
                    #                        "icon-path": "icons/memory/memory.png",
                    #                        "tooltip": "Show selected memory region in the memory view.",
                    #                        "click-func": self.__show_memory_region,
                    #                        "disabled": not data.debugging_active,
                    #                    },
                },
            },
        }

        # Add the warning label
        new_label = wg.create_label(
            text="",
            bold=True,
            parent=self,
        )
        main_view.layout().addWidget(new_label)
        self.__cache_labels["program-state-warning"] = new_label
        new_label.setVisible(False)

        for g, d in button_groups.items():
            # Add group
            new_group = wg.create_frame(
                name=g,
                parent=self,
                layout_vertical=False,
                layout_margins=(2, 2, 2, 2),
                layout_spacing=2,
                layout_size_constraing=qt.QLayout.SizeConstraint.SetFixedSize,
            )
            main_view.layout().addWidget(new_group)
            self.__cache_views[g] = new_group

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
                    if "disabled" in v.keys():
                        if v["disabled"]:
                            new_combobox.disable()
                    if "tooltip" in v.keys():
                        new_combobox.setToolTip(v["tooltip"])
                    if "statustip" in v.keys():
                        new_combobox.setStatusTip(v["statustip"])
                    self.__cache_comboboxes[v["name"]] = new_combobox
                    new_group.layout().addWidget(new_combobox)
                    new_group.layout().setAlignment(
                        new_combobox,
                        qt.Qt.AlignmentFlag.AlignLeft
                        | qt.Qt.AlignmentFlag.AlignVCenter,
                    )

            if "input-fields" in d.keys():
                for k, v in d["input-fields"].items():
                    new_textbox = wg.create_textbox(
                        name=k,
                        parent=new_group,
                        no_border=True,
                    )
                    if "initial-text" in v.keys():
                        new_textbox.setText(v["initial-text"])
                    self.__cache_input_fields[v["name"]] = new_textbox
                    new_group.layout().addWidget(new_textbox)

            # Add buttons to group
            for k, v in d["buttons"].items():
                if "icon-path" in v.keys() or "icon" in v.keys():
                    new_button = wg.create_pushbutton(
                        parent=new_group,
                        name=v["name"],
                        icon_name=v["icon-path"],
                        tooltip=v["tooltip"],
                        statustip=v["tooltip"],
                        click_func=v["click-func"],
                        style="debugger",
                    )
                else:
                    new_button = wg.create_pushbutton(
                        parent=new_group,
                        name=v["name"],
                        text=v["text"],
                        tooltip=v["tooltip"],
                        statustip=v["tooltip"],
                        click_func=v["click-func"],
                        style="debugger",
                    )
                if v["name"] not in (
                    "connect",
                    "connect-direct",
                ):
                    new_button.disable()
                if "disabled" in v.keys():
                    if v["disabled"]:
                        new_button.disable()
                self.__cache_buttons[v["name"]] = new_button
                new_group.layout().addWidget(new_button)
                new_group.layout().setAlignment(
                    new_button,
                    qt.Qt.AlignmentFlag.AlignLeft
                    | qt.Qt.AlignmentFlag.AlignVCenter,
                )

            if g == "general":
                # Add state value label
                new_label = wg.create_label(
                    text="",
                    bold=True,
                    parent=new_group,
                )
                new_group.layout().addWidget(new_label)
                self.__cache_labels["state-value"] = new_label

        # Main splitter
        widget_splitter = qt.QSplitter(qt.Qt.Orientation.Vertical, self)
        main_view.layout().addWidget(widget_splitter)

        # Breakpoint view
        breakpoints_groupbox = wg.create_groupbox_with_layout(
            parent=self,
            name="BreakpointsView",
            borderless=True,
            vertical=True,
            h_size_policy=qt.QSizePolicy.Policy.MinimumExpanding,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        breakpoints_groupbox.setToolTip(
            "This window displays the breakpoints and watchpoints\nwhen the debugger is active."
        )
        breakpoints_groupbox.setStatusTip(
            "This window displays the breakpoints and watchpoints\nwhen the debugger is active."
        )
        widget_splitter.addWidget(breakpoints_groupbox)
        self.__cache_views["breakpoints"] = breakpoints_groupbox
        # Breakpoint widget
        breakpoints = debugger.breakpointwidget.BreakpointWidget(
            main_view, self.main_form, self
        )
        breakpoints.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Ignored,
            )
        )
        breakpoints_groupbox.layout().addWidget(breakpoints)
        self.breakpoints = breakpoints

        # StackFrame view
        stackframe_groupbox = wg.create_groupbox_with_layout(
            parent=self,
            name="stackframeView",
            borderless=True,
            vertical=True,
            h_size_policy=qt.QSizePolicy.Policy.MinimumExpanding,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        stackframe_groupbox.setToolTip(
            "This window displays the stack data during debugging."
        )
        stackframe_groupbox.setStatusTip(
            "This window displays the stack data during debugging."
        )
        widget_splitter.addWidget(stackframe_groupbox)
        self.__cache_views["stackframe"] = stackframe_groupbox
        # StackFrame widget
        stackframe = debugger.stackframewidget.StackFrameWidget(
            main_view, self.main_form, self
        )
        stackframe.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Ignored,
            )
        )
        stackframe_groupbox.layout().addWidget(stackframe)
        self.stackframe = stackframe

        # Console view
        console_groupbox = wg.create_groupbox_with_layout(
            parent=self,
            name="DebuggerConsoleView",
            borderless=True,
            vertical=True,
            h_size_policy=qt.QSizePolicy.Policy.MinimumExpanding,
            v_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        console_groupbox.setToolTip(
            "This window displays the output\nfrom OpenOCD and GDB when debugging."
        )
        console_groupbox.setStatusTip(
            "This window displays the output\nfrom OpenOCD and GDB when debugging."
        )
        widget_splitter.addWidget(console_groupbox)
        self.__cache_views["console"] = console_groupbox
        # Console widget
        console = gui.templates.textmanipulation.ConsoleDisplay(main_view, self)
        console.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Ignored,
            )
        )
        console_groupbox.layout().addWidget(console)
        self.console = console
        # Input widget
        console_input = wg.create_textbox(
            name="DebuggerConsoleInput",
            parent=console_groupbox,
            no_border=True,
        )
        console_input.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Fixed,
            )
        )
        tooltip = "Enter debugger commands here (GDB or MI commands)"
        console_input.setToolTip(tooltip)
        console_input.setPlaceholderText(tooltip)

        def check_text(*args, **kwargs):
            if console_input.text() == "":
                console_input.setProperty("showing-placeholder-text", True)
            else:
                console_input.setProperty("showing-placeholder-text", False)
            console_input.style().unpolish(console_input)
            console_input.style().polish(console_input)
            console_input.update()

        check_text()
        console_input.textChanged.connect(check_text)
        console_input.returnPressed.connect(self.console_input_request)
        console_input.key_release_signal.connect(self.console_input_keypress)
        self.console_input = console_input
        self.console_input.setEnabled(False)
        console_groupbox.layout().addWidget(console_input)

        # Initialize the memory region combobox regions
        self.__update_memory_regions()

        # Connect the memory region combobox signals
        def change_region(name, item):
            if name != "select-region":
                self.__show_memory_region()
                self.__cache_comboboxes[
                    "memory-region-select"
                ].set_selected_name("select-region")

        self.__cache_comboboxes[
            "memory-region-select"
        ].selection_changed.connect(change_region)

        def __resize(*args):
            # Set initial sizes
            widget_splitter.setSizes(
                [
                    int(widget_splitter.size().height() * 2 / 10),
                    int(widget_splitter.size().height() * 2 / 10),
                    int(widget_splitter.size().height() * 6 / 10),
                ]
            )

        qt.QTimer.singleShot(100, __resize)

    def __debug_state_changed(self, new_state):
        # Update button states only when debugging is active
        if data.debugging_active == True:
            if new_state == DebugState.Halted:
                button_states = {
                    "reset": True,
                    "halt": False,
                    "continue": True,
                    "step": True,
                    "next": True,
                    "finish": True,
                }
                for k, v in button_states.items():
                    self.__cache_buttons[k].setEnabled(v)
            elif new_state == DebugState.Running:
                button_states = {
                    "reset": True,
                    "halt": True,
                    "continue": False,
                    "step": False,
                    "next": False,
                    "finish": False,
                }
                for k, v in button_states.items():
                    self.__cache_buttons[k].setEnabled(v)

    def __update_memory_regions(self, memory_dictionary={}):
        try:
            combobox = self.__cache_comboboxes["memory-region-select"]
            combobox.clear()
            combobox.add_items(
                [
                    {
                        "name": "select-region",
                        "widgets": [
                            {
                                "type": "text",
                                "text": "Select a memory region",
                            },
                        ],
                    },
                    {
                        "name": "general-registers",
                        "widgets": [
                            {
                                "type": "image",
                                "icon-path": "icons/memory/memory.png",
                            },
                            {
                                "type": "text",
                                "text": "General Registers",
                            },
                        ],
                    },
                ]
            )
            combobox.set_selected_name("select-region")

            for name, _data in memory_dictionary.items():
                new_item = {
                    "name": name,
                    "widgets": [
                        {
                            "type": "image",
                            "icon-path": "icons/memory/memory.png",
                        },
                        {
                            "type": "text",
                            "text": name,
                        },
                    ],
                }
                combobox.add_item(new_item)
            combobox.update_style()

        except:
            traceback.print_exc()

    def __warning_show(self, text) -> None:
        label = self.__cache_labels["program-state-warning"]
        label.setText(text)
        label.setVisible(True)

    def __warning_hide(self) -> None:
        label = self.__cache_labels["program-state-warning"]
        label.setVisible(False)

    """
    Items
    """

    def items_enable(self):
        for k, v in self.__cache_buttons.items():
            if k in (
                "connect",
                "connect-direct",
            ):
                v.disable()
            else:
                v.enable()
        for k, v in self.__cache_comboboxes.items():
            v.enable()
        self.console_input.setEnabled(True)

    def items_disable(self):
        for k, v in self.__cache_buttons.items():
            if k not in (
                "connect",
                "connect-direct",
            ):
                v.disable()
            else:
                v.enable()
        for k, v in self.__cache_comboboxes.items():
            v.disable()
        self.console_input.setEnabled(False)

    """
    Console
    """
    console_buffer_list = []
    console_buffer_index = 0

    def console_write(self, *args, **kwargs):
        if self.console is not None:
            self.console.add_text(*args, **kwargs)

            # Special response parsing
            disconnect_strings = (
                "examination failed, gdb will be halted.",
                "target disconnected.",
                "connection closed",
                # The following two conditions also cause a disconnection
                # when executing a RESET&HALT, so they cannot be used!
                #                "dropped 'gdb' connection",
                #                "dropped 'telnet' connection",
            )
            running_strings = ("running\n",)
            halt_strings = (
                "target halted",
                "interrupt.",
                "command aborted.",
            )
            for arg in args:
                message = str(arg).lower()
                if any([x in message for x in disconnect_strings]):
                    self.debugger_disconnect()
                    self.state = DebugState.Disconnected

                elif any([x in message for x in running_strings]):
                    # Update debug state
                    self.state = DebugState.Running
                    # Hide the stack-cursor
                    gui.forms.customeditor.CustomEditor.debugger_clear_position_marker()

                elif any([x in message for x in halt_strings]):
                    # Update debug state
                    self.state = DebugState.Halted

    def console_manual_command(self, command: str) -> None:
        msg = "[MANUAL-COMMAND-EXECUTE] {}".format(command)
        print(msg)
        self.console_write(msg + "\n")

    def console_input_request(self, *args) -> None:
        command = self.console_input.text().strip()
        self.console_input.setText("")
        if command != "":
            if (
                len(self.console_buffer_list) > 0
                and command != self.console_buffer_list[-1]
                or len(self.console_buffer_list) == 0
            ):
                self.console_buffer_list.append(command)
            self.console_buffer_index = len(self.console_buffer_list)
        if command == "":
            return
        try:
            self.console_write(
                "<b style='color:{};'>{}</b><br>".format(
                    data.theme["indication"]["warning"],
                    f"(gdb) {command}",
                ),
                html=True,
            )
            # Execute command
            self.__debugger.execute_user_command(command)
        except Exception as ex:
            self.console_write(
                "<b style='color:{};'>{}</b><br>".format(
                    data.theme["indication"]["error"],
                    str(ex),
                ),
                html=True,
            )

    def console_input_keypress(self, key):
        if len(self.console_buffer_list) == 0:
            return

        if key == qt.Qt.Key.Key_Up:
            self.console_buffer_index -= 1
            if self.console_buffer_index < 0:
                self.console_buffer_index = 0
            stored_command = self.console_buffer_list[self.console_buffer_index]
            self.console_input.setText(stored_command)
        elif key == qt.Qt.Key.Key_Down:
            self.console_buffer_index += 1
            last_index = len(self.console_buffer_list) - 1
            if self.console_buffer_index > last_index:
                self.console_buffer_index = last_index
            stored_command = self.console_buffer_list[self.console_buffer_index]
            self.console_input.setText(stored_command)

    def __display_error(self, message: str) -> None:
        traceback.print_exc()
        self.console_write(
            "<b style='color:{};'>{}</b><br>".format(
                data.theme["indication"]["error"],
                message,
            ),
            html=True,
        )

    """
    Debugger
    """

    def __debugger_parse_response(self, response):
        end_message_list = []

        for r in response:
            # Enable debugging
            if not data.debugging_active:
                if "message" in r.keys() and r["message"] == "connected":
                    # Special architectures
                    #                    try:
                    #                        arch = data.current_project.get_chip().get_chip_unicum().get_chip_family().get_isa()
                    #                        if arch == "riscv":
                    #                            self.__debugger.execute("set arch riscv:rv32")
                    #                    except Exception as ex:
                    #                        self.__display_error(str(ex).replace('\n', "<br>"))
                    # Symbol (.elf) file loading
                    self.load_symbol_file()
                    #                    self.__debugger.stop_execution()
                    self.items_enable()
                    self.__debugger.set_state_connected()
                    # Update global debug functionality
                    data.debugging_active = True
                    for editor in self.main_form.get_all_editors():
                        editor.update_debug_settings()
                    # Update debug cursor position
                    self.debugger_stack_frame()
                    # Send the global signal
                    data.signal_dispatcher.debug_connected.emit()
                    # Set initial state
                    self.state = DebugState.Halted

            # Variable list
            if "token" in r.keys() and r["token"] is not None:
                if int(r["token"]) == self.__debugger.TOKENS["symbol-value"]:
                    """
                    {
                        'type': 'result',
                        'message': 'done',
                        'payload': {
                            'value': '939'
                        },
                        'token': 0,
                        'stream': 'stdout'
                    }
                    """
                    if self.__stored_editor_data is not None:
                        editor = self.__stored_editor_data["editor"]
                        word = self.__stored_editor_data["word"]
                        value = r["payload"]["value"]
                        editor.symbol_show_value_callback(word, value)
                        self.__stored_editor_data = None

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["general-register-names"]
                ):
                    self.__stored_general_register_data = {}
                    for i, name in enumerate(r["payload"]["register-names"]):
                        if name.strip() == "":
                            continue

                        self.__stored_general_register_data[i] = {
                            "name": name,
                            "value": None,
                        }

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["general-register-values"]
                ):
                    success = False
                    try:
                        for item in r["payload"]["register-values"]:
                            number = int(item["number"])
                            value = item["value"]
                            self.__stored_general_register_data[number][
                                "value"
                            ] = value
                        # Show in memory-view
                        self.main_form.projects.show_general_registers()
                        general_register_window = (
                            self.main_form.projects.get_general_register_window()
                        )
                        general_register_window.show_general_register_data(
                            self.__stored_general_register_data
                        )
                        continue
                    except:
                        traceback.print_exc()

                elif int(r["token"]) == self.__debugger.TOKENS["raw-memory"]:
                    """
                    memory: [
                        {
                            begin="0xbffff154",
                            offset="0x00000000",
                            end="0xbffff15e",
                            contents="01000000020000000300"
                        },
                        ...
                    ]
                    """
                    try:
                        memory = r["payload"]["memory"][0]
                        address = int(memory["begin"], 16)
                        contents = memory["contents"]
                        contents_list = re.findall("..", contents)
                        # Show in memory-view
                        self.main_form.projects.show_raw_memory(
                            self.__queried_memory_region
                        )
                        memory_view_window = (
                            self.main_form.projects.get_raw_memory_window(
                                self.__queried_memory_region
                            )
                        )
                        memory_view_window.show_memory_data(
                            address, contents_list
                        )
                        continue
                    except:
                        traceback.print_exc()

                elif int(r["token"]) == self.__debugger.TOKENS["stack-list"]:
                    """{'stack': [{'addr': '0x0800044e', 'arch': 'arm', 'file':

                    '../source/user_code/systick.c', 'fullname': 'J:/embeetle/Co
                    de/00.Blink/gd32e231c-start/source/user_code/systick.c',
                    'func': 'delay_1ms', 'level': '0', 'line': '71'}, {'addr':
                    '0x080003f2', 'arch': 'arm', 'file':
                    '../source/user_code/main.c', 'fullname': 'J:/embeetle/Code/
                    00.Blink/gd32e231c-start/source/user_code/main.c', 'func':
                    'main', 'level': '1', 'line': '74'}]}
                    """
                    stack_list = r["payload"]["stack"]
                    self.stackframe.set_stack_list(stack_list)
                    data.signal_dispatcher.debug_stack_updated.emit()
                    self.debugger_stack_variable_list()
                    if len(stack_list) > 0:
                        for sl in stack_list:
                            if "fullname" in sl.keys() and "line" in sl.keys():
                                result = self.__update_stack_cursor(
                                    sl["fullname"], sl["line"]
                                )
                                end_message_list.append(result)
                                break

                elif (
                    int(r["token"]) == self.__debugger.TOKENS["stack-variables"]
                ):
                    """{ 'variables': [ {'name': 'a', 'value': '444'} ] }"""
                    variable_list = r["payload"]["variables"]
                    self.stackframe.set_stack_variables(variable_list)

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["variable-object-create"]
                ):
                    """{ 'has_more': '0', 'name': 'a', 'numchild': '0', 'thread-
                    id': '1', 'type': 'volatile int', 'value': '123' }"""
                    variable_data = r["payload"]
                    data.signal_dispatcher.memory_watch_add_variable.emit(
                        variable_data
                    )

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["variable-object-delete"]
                ):
                    variable_data = r["payload"]

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["variable-object-delete-all"]
                ):
                    variable_data = r["payload"]

                elif (
                    int(r["token"])
                    == self.__debugger.TOKENS["variable-object-update"]
                ):
                    """{ 'has_more': '0', 'name': 'a', 'numchild': '0', 'thread-
                    id': '1', 'type': 'volatile int', 'value': '123' }"""
                    update_data = r["payload"]
                    data.signal_dispatcher.memory_watch_update_variables.emit(
                        update_data
                    )

            # Handle response
            if (
                (r["payload"] is not None)
                and (isinstance(r["payload"], dict))
                and (data.debugging_active == True)
            ):
                payload = r["payload"]

                if (
                    "stopped-threads" in payload.keys()
                    and payload["stopped-threads"] == "all"
                ):
                    self.state = DebugState.Halted

                # Position in code
                position_display_condition = (
                    "reason" in payload.keys()
                    and (
                        (
                            payload["reason"] == "signal-received"
                            and "signal-meaning" in payload.keys()
                            and payload["signal-meaning"] == "Interrupt"
                        )
                        or (payload["reason"] == "end-stepping-range")
                        or (payload["reason"] == "breakpoint-hit")
                    )
                ) or ("frame" in payload.keys())
                if position_display_condition:
                    try:
                        frame = payload["frame"]
                        if (
                            "fullname" in frame.keys()
                            and "line" in frame.keys()
                        ):
                            result = self.__update_stack_cursor(
                                frame["fullname"], frame["line"]
                            )
                            end_message_list.append(result)
                        # Update stack-frame list
                        self.debugger_stack_frame_list()
                        # Update watch variables signal
                        self.debugger_variable_object_update()
                        # Update the state
                        self.state = DebugState.Halted
                    except Exception as ex:
                        self.__display_error(str(ex).replace("\n", "<br>"))

                if "variables" in payload.keys():
                    if self.__stored_editor_data is not None:
                        editor = self.__stored_editor_data["editor"]
                        word = self.__stored_editor_data["word"]
                        editor.variable_list_callback(payload, word)

            # Display response in debugger console
            #            if r["type"] in ("console", "notify", "output", "target"):
            if r["stream"] == "stdout" and r["payload"] is not None:
                self.console_write(r["payload"])
            elif r["stream"] == "stdout" and r["payload"] is None:
                # Standard raw output messages
                message = r["message"]
                self.console_write(r["message"] + "\n")
            elif r["stream"] == "stderr" and r["payload"] is not None:
                payload = r["payload"]
                if not isinstance(payload, str):
                    payload = pprint.pformat(payload)
                self.console_write(
                    "<b style='color:{};'>{}</b><br>".format(
                        data.theme["indication"]["error"],
                        str(payload).replace("\n", "<br>"),
                    ),
                    html=True,
                )
            else:
                self.console_write(r)

            # Check breakpoint insertion feedback
            self.__breakpoint_insertion_check_feedback(r)
            # Check breakpoint list feedback
            self.__breakpoint_list_check_feedback(r)

            # Display end messages
            for message, html in end_message_list:
                self.console_write(message, html=html)

    def __update_stack_cursor(self, fullname, line):
        filepath = functions.unixify_path(fullname)
        self.main_form.open_file(filepath)
        line = int(line)
        editor = self.main_form.get_tab_by_save_name(filepath)
        editor.goto_line(line)
        editor.debugger_show_position_marker(line)
        #        offset = editor.positionFromLineIndex(line - 1, 0)
        # Give last index of the line before the '\n',
        # in order for the emtpy-loop-check to work correctly
        scintilla_line = line - 1
        line_text = editor.text(scintilla_line)
        if "{" in line_text:
            scintilla_index = line_text.index("{") + 1
        elif "}" in line_text:
            scintilla_index = line_text.index("}")
        else:
            scintilla_index = len(line_text.strip()) - 1
        offset = editor.positionFromLineIndex(scintilla_line, scintilla_index)
        self.__stack_cursor_data = {
            "path": fullname,
            "offset": offset,
            "line": line,
        }
        # Display position update in console
        return (
            "<b style='color:{};'>{}</b><br>".format(
                data.theme["fonts"]["success"]["color"],
                "Successfully updated debug cursor position.",
            ),
            True,
        )

    def __breakpoint_list_check_feedback(self, response):
        if not isinstance(response, dict):
            return

        if "payload" in response.keys():
            payload = response["payload"]
            if (
                isinstance(payload, dict)
                and "BreakpointTable" in payload.keys()
            ):
                breakpoint_list = payload["BreakpointTable"]["body"]
                formated_string = json.dumps(
                    breakpoint_list, indent=2, ensure_ascii=False
                )
                self.console_write("Breakpoint list: ")
                self.console_write(formated_string + "\n")

    def __breakpoint_insertion_check_feedback(self, response):
        #        RESPONSE EXAMPLE:
        #        [
        #            {
        #                'type': 'result',
        #                'message': 'done',
        #                'payload': {
        #                    'bkpt': {
        #                        'number': '1',
        #                        'type': 'breakpoint',
        #                        'disp': 'keep',
        #                        'enabled': 'y',
        #                        'addr': '0x080022ca',
        #                        'func': 'main',
        #                        'file': '../source/user_code/main.c',
        #                        'fullname': 'D:\\embedoffice_stuff\\projects\\nucleo-f767zi-debugger-testing\\source\\user_code\\main.c',
        #                        'line': '98',
        #                        'thread-groups': ['i1'],
        #                        'times': '0',
        #                        'original-location': 'D:/embedoffice_stuff/projects/nucleo-f767zi-debugger-testing/source/user_code/main.c:97'
        #                    }
        #                },
        #                'token': None,
        #                'stream': 'stdout'
        #            }
        #        ]
        if response is None:
            return

        breakpoint_number = -1
        r = response

        if (
            "payload" in r.keys()
            and r["payload"] is not None
            and "type" in r.keys()
            and r["type"] == "result"
            and "message" in r.keys()
            and r["message"] == "done"
        ):
            payload = r["payload"]

            # Break-point
            if "bkpt" in payload.keys():
                breakpoint_data = payload["bkpt"]
                breakpoint_number = int(breakpoint_data["number"])

                if (
                    "fullname" in breakpoint_data.keys()
                    and "line" in breakpoint_data.keys()
                ):
                    filepath = functions.unixify_path(
                        breakpoint_data["fullname"]
                    )
                    editor = self.main_form.get_tab_by_save_name(filepath)
                    if editor is not None:
                        scintilla_line = int(breakpoint_data["line"]) - 1
                        # Check if breakpoint is already in the breakpoint tree-widget
                        found = False
                        for k, v in self.breakpoints.get_breakpoints().items():
                            bp_line = v["line"]
                            bp_filepath = v["filepath"]
                            if (
                                bp_line == scintilla_line
                                and bp_filepath == filepath
                            ):
                                found = True
                                break
                        # Add the breakpoint
                        if not found:
                            editor.debugger_breakpoint_insert(
                                scintilla_line, breakpoint_number
                            )

                    self.breakpoints.add_breakpoint(breakpoint_data)

            # Watch-point
            if "wpt" in payload.keys():
                watchpoint_data = payload["wpt"]
                self.breakpoints.add_watchpoint(
                    watchpoint_data,
                    self.__stored_watchpoint_data,
                )
                self.__stored_watchpoint_data = None

        # Display insertion success
        if breakpoint_number != -1:
            self.console_write(
                "<b style='color:{};'>{}</b><br>".format(
                    data.theme["fonts"]["success"]["color"],
                    f"Breakpoint '{breakpoint_number}' inserted.",
                ),
                html=True,
            )

    def debugger_connect(self):
        try:
            return self.__debugger_connect()
        except Exception as ex:
            self.__display_error(traceback.format_exc().replace("\n", "<br>"))
            self.__display_error(str(ex).replace("\n", "<br>"))

    def __debugger_connect(self):
        if data.current_project is None:
            self.main_form.display.display_error(
                "[Debugging] Project not yet loaded!"
            )
            return
        self.console_write("Staring OpenOCD/GDB connection process ...\n")
        # Get absolute path to '.elf' file. Can be None or 'none' if not specified in the Dashboard.
        elf_abspath = data.current_project.get_treepath_seg().get_abspath(
            "ELF_FILE"
        )
        if not isinstance(elf_abspath, str) or not os.path.isfile(elf_abspath):
            raise Exception("[Debugger] The '.elf' file cannot be located!")
        # Get absolute path to 'openocd.exe'. Can be without the '.exe' suffix on Linux. Can also be
        # None or 'none' if not specified in the Dashboard. Watch out: the returned path can also be
        # a totally different flashtool, such as AVRDUDE, Bossac, ...
        openocd_abspath = data.current_project.get_toolpath_seg().get_abspath(
            "FLASHTOOL"
        )
        if not isinstance(openocd_abspath, str) or not os.path.isfile(
            openocd_abspath
        ):
            raise Exception("[Debugger] The flashtool file cannot be located!")
        # Get absolute path to 'gdb.exe'. Can be without the '.exe' suffix on Linux. This tool is nowhere specified in the Dashboard. My code
        # looks for the tool inside the compiler toolchain. Returns None or 'none' if nothing found.
        gdb_abspath = data.current_project.get_toolpath_seg().get_gdb_abspath()
        if not isinstance(gdb_abspath, str) or not os.path.isfile(gdb_abspath):
            compiler_abspath = (
                data.current_project.get_toolpath_seg().get_abspath(
                    "COMPILER_TOOLCHAIN"
                )
            )
            if not isinstance(compiler_abspath, str) or not os.path.isfile(
                compiler_abspath
            ):
                raise Exception("[Debugger] Cannot determine debugger path!")
            gdb_abspath = "gdb".join(compiler_abspath.rsplit("gcc", 1))
            if not isinstance(gdb_abspath, str) or not os.path.isfile(
                gdb_abspath
            ):
                raise Exception("[Debugger] Cannot determine debugger path!")
        # Get absolute path to 'openocd_probe.cfg'. Can be None or 'none' if not specified in the
        # Dashboard.
        openocd_probe_abspath = (
            data.current_project.get_treepath_seg().get_abspath(
                "OPENOCD_PROBEFILE"
            )
        )
        # Get absolute path to 'openocd_chip.cfg'. Can be None or 'none' if not specified in the
        # Dashboard.
        openocd_chip_abspath = (
            data.current_project.get_treepath_seg().get_abspath(
                "OPENOCD_CHIPFILE"
            )
        )
        # Store the paths
        self.gdb_abspath = gdb_abspath
        self.openocd_abspath = openocd_abspath
        self.openocd_probe_abspath = openocd_probe_abspath
        self.openocd_chip_abspath = openocd_chip_abspath
        self.elf_abspath = elf_abspath
        self.console_write("[GDB-ABSOLUTE-PATH] '{}'\n".format(gdb_abspath))
        self.console_write(
            "[OPENOCD-ABSOLUTE-PATH] '{}'\n".format(openocd_abspath)
        )
        self.console_write(
            "[OPENOCD-PROBE-ABSOLUTE-PATH] '{}'\n".format(openocd_probe_abspath)
        )
        self.console_write(
            "[OPENOCD-CHIP-ABSOLUTE-PATH] '{}'\n".format(openocd_chip_abspath)
        )
        self.console_write("[ELF-ABSOLUTE-PATH] '{}'\n".format(elf_abspath))
        # Initialize the debugger component
        self.__debugger = debugger.debugger.Debugger(
            self,
            gdb_abspath,
            openocd_abspath,
            openocd_probe_abspath,
            openocd_chip_abspath,
            self.debugger_command_completed_signal,
        )
        #        self.__debugger.openocd_stdout_received.connect(self.__openocd_stdout_print)
        self.__debugger.openocd_stdout_received.connect(
            self.__openocd_telnet_print
        )
        self.__debugger.openocd_start()
        self.__debugger.openocd_started.connect(self.__openocd_started)
        self.__debugger.data_received_signal.connect(
            self.__debugger_parse_response
        )
        self.__debugger.error_response_signal.connect(self.__display_error)

        # Update the chip's memory regions
        memory_dictionary = self.__sai.get_memory_regions()
        self.__update_memory_regions(memory_dictionary)

    def debugger_connect_direct(self):
        try:
            return self.__debugger_connect_direct()
        except Exception as ex:
            self.__display_error(traceback.format_exc().replace("\n", "<br>"))
            self.__display_error(str(ex).replace("\n", "<br>"))

    def __debugger_connect_direct(self):
        if data.current_project is None:
            self.main_form.display.display_error(
                "[Debugging] Project not yet loaded!"
            )
            return
        self.console_write("Staring direct GDB connection process ...\n")
        # Get absolute path to '.elf' file. Can be None or 'none' if not specified in the Dashboard.
        elf_abspath = data.current_project.get_treepath_seg().get_abspath(
            "ELF_FILE"
        )
        if not isinstance(elf_abspath, str) or not os.path.isfile(elf_abspath):
            raise Exception("[Debugger] The '.elf' file cannot be located!")
        # Get absolute path to 'gdb.exe'. Can be without the '.exe' suffix on Linux. This tool is nowhere specified in the Dashboard. My code
        # looks for the tool inside the compiler toolchain. Returns None or 'none' if nothing found.
        gdb_abspath = data.current_project.get_toolpath_seg().get_gdb_abspath()
        if not isinstance(gdb_abspath, str) or not os.path.isfile(gdb_abspath):
            compiler_abspath = (
                data.current_project.get_toolpath_seg().get_abspath(
                    "COMPILER_TOOLCHAIN"
                )
            )
            if not isinstance(compiler_abspath, str) or not os.path.isfile(
                compiler_abspath
            ):
                raise Exception("[Debugger] Cannot determine debugger path!")
            gdb_abspath = "gdb".join(compiler_abspath.rsplit("gcc", 1))
            if not isinstance(gdb_abspath, str) or not os.path.isfile(
                gdb_abspath
            ):
                raise Exception("[Debugger] Cannot determine debugger path!")
        # Store the paths
        self.gdb_abspath = gdb_abspath
        self.elf_abspath = elf_abspath
        self.console_write("[GDB-ABSOLUTE-PATH] '{}'\n".format(gdb_abspath))
        self.console_write("[ELF-ABSOLUTE-PATH] '{}'\n".format(elf_abspath))
        # Initialize the debugger component
        self.__debugger = debugger.debugger.Debugger(
            self,
            gdb_abspath,
            None,
            None,
            None,
            self.debugger_command_completed_signal,
        )
        self.__debugger.data_received_signal.connect(
            self.__debugger_parse_response
        )
        self.__debugger.error_response_signal.connect(self.__display_error)

        # Update the chip's memory regions
        memory_dictionary = self.__sai.get_memory_regions()
        self.__update_memory_regions(memory_dictionary)

        # Initialization of the debugger
        gdb_url = self.__cache_input_fields["gdb-url"].text()
        target = f"extended-remote {gdb_url}"
        self.__debugger.init(target=target)

    def __openocd_stdout_print(self, text):
        if text.strip().lower().startswith("warn :"):
            filtered_text = "<b style='color:{};'>{}</b><br>".format(
                data.theme["indication"]["warning"], text
            )
            self.console_write(filtered_text, html=True)
        else:
            self.console_write(text)

    def __openocd_telnet_print(self, text):
        if text.strip().lower().startswith("warn :"):
            filtered_text = "<b style='color:{};'>{}</b><br>".format(
                data.theme["indication"]["warning"], text
            )
            self.console_write(filtered_text, html=True)
        else:
            self.console_write(text)

    @safe_execute
    def __openocd_started(self):
        try:
            # Initialization of the debugger
            self.__debugger.init()
        except Exception as ex:
            self.__display_error(traceback.format_exc().replace("\n", "<br>"))
            self.__display_error(str(ex).replace("\n", "<br>"))

    def debugger_disconnect(self):
        try:
            self.__debugger_disconnect()
            self.state = DebugState.Disconnected
            self.items_disable()
            if self.__debugger is not None:
                self.__debugger.set_state_disconnected()
            # Delete break and watch points
            self.breakpoints.delete_all_breakpoints()
            self.breakpoints.delete_all_watchpoints()
            # Clear memory view
            data.signal_dispatcher.memory_view_clear_all.emit()
            # Clear memory view watch-table variables
            data.signal_dispatcher.memory_watch_delete_all_variables.emit()
            # Clear stack
            self.stackframe.clear_stack_list()
            self.stackframe.clear_stack_variables()
            # Update global debug functionality
            gui.forms.customeditor.CustomEditor.debugger_clear_position_marker()
            gui.forms.customeditor.CustomEditor.debugger_breakpoint_delete_all()
            data.debugging_active = False
            data.signal_dispatcher.debug_disconnected.emit()
            for editor in self.main_form.get_all_editors():
                editor.update_debug_settings()
        except Exception as ex:
            self.__display_error(traceback.format_exc().replace("\n", "<br>"))
            self.__display_error(str(ex).replace("\n", "<br>"))

    @safe_execute
    def load_symbol_file(self):
        self.console_write("[LOADING-ELF-FILE] {}\n".format(self.elf_abspath))
        self.__debugger.load_symbol_file(self.elf_abspath)

    @safe_execute
    def __debugger_disconnect(self):
        self.__debugger.self_destruct()

    @safe_execute
    def debugger_halt(self):
        self.console_manual_command("halt")
        self.__debugger.openocd_halt()

    @safe_execute
    def debugger_reset_halt(self):
        self.console_manual_command("reset&halt")
        self.__debugger.openocd_reset_halt()

    @safe_execute
    def debugger_continue(self):
        self.console_manual_command("continue")
        self.__debugger.continue_execution()

    @safe_execute
    def debugger_step(self):
        step_flag = True
        if self.__stack_cursor_data is not None:
            test = self.__sai.check_empty_loop(
                self.__stack_cursor_data["path"],
                self.__stack_cursor_data["offset"],
            )
            if test:
                # Execute instruction step
                self.console_manual_command("step-i")
                self.__debugger.step_instruction()
                step_flag = False
        if step_flag:
            # Execute command
            self.console_manual_command("step")
            self.__debugger.step()

    @safe_execute
    def debugger_step_instruction(self):
        self.console_manual_command("step-i")
        # Execute command
        self.__debugger.step_instruction()

    @safe_execute
    def debugger_next(self):
        step_flag = True
        if self.__stack_cursor_data is not None:
            test = self.__sai.check_empty_loop(
                self.__stack_cursor_data["path"],
                self.__stack_cursor_data["offset"],
            )
            if test:
                # Execute instruction step
                self.console_manual_command("step-i")
                self.__debugger.step_instruction()
                step_flag = False
        if step_flag:
            # Execute command
            self.console_manual_command("step")
            self.__debugger.next()

    @safe_execute
    def debugger_next_instruction(self):
        self.console_manual_command("next-i")
        # Execute command
        self.__debugger.next_instruction()

    @safe_execute
    def debugger_finish(self):
        self.console_manual_command("finish")
        # Execute command
        self.__debugger.finish()

    @safe_execute
    def debugger_stack_frame(self):
        self.console_manual_command("stack-frame")
        # Execute command
        self.__debugger.stack_frame()

    @safe_execute
    def debugger_stack_depth(self):
        self.console_manual_command("stack-depth")
        # Execute command
        self.__debugger.stack_depth()

    @safe_execute
    def debugger_stack_frame_list(self, *args):
        self.console_manual_command("stack-frame-list")
        # Execute command
        self.__debugger.stack_frame_list()

    @safe_execute
    def debugger_stack_variable_list(self, *args):
        self.console_manual_command("stack-variable-list")
        # Execute command
        self.__debugger.stack_variable_list()

    @safe_execute
    def debugger_symbol_value(self, editor_data):
        self.console_manual_command("symbol-value")
        # Execute command
        self.__debugger.symbol_value(editor_data["word"])
        # Store editor reference
        self.__stored_editor_data = editor_data

    """
    Break-points
    """

    @safe_execute
    def debugger_breakpoints_show(self):
        self.console_manual_command("breakpoint-show-list")
        self.__debugger.breakpoint_show_list()

    @safe_execute
    def debugger_breakpoint_insert(
        self, filename, line_number, scintilla_line_number
    ):
        if not data.debugging_active:
            self.console_write(
                "<b style='color:{};'>Debugging not active, skipping inserting breakpoint!</b><br>".format(
                    data.theme["indication"]["error"],
                ),
                html=True,
            )
            return

        self.console_manual_command("breakpoint-insert")
        self.__stored_breakpoint_data = {
            "file": filename,
            "line": line_number,
            "scintilla-line": scintilla_line_number,
        }
        # Execute command
        self.__debugger.breakpoint_insert(filename, line_number)

    @safe_execute
    def debugger_breakpoint_delete(
        self, filename, line_number, scintilla_line_number, breakpoint_number
    ):
        if not data.debugging_active:
            self.console_write(
                "<b style='color:{};'>Debugging not active, skipping deleting breakpoint!</b><br>".format(
                    data.theme["indication"]["error"],
                ),
                html=True,
            )
            return

        self.console_manual_command("breakpoint-delete")
        # Execute command
        self.__debugger.breakpoint_delete(breakpoint_number)
        editor = self.main_form.get_tab_by_save_name(filename)
        if editor is not None:
            editor.debugger_breakpoint_delete(
                scintilla_line_number, breakpoint_number
            )
        self.breakpoints.delete_breakpoint(breakpoint_number)
        # Display deletion success
        self.console_write(
            "<b style='color:{};'>{}</b><br>".format(
                data.theme["indication"]["warning"],
                f"Breakpoint '{breakpoint_number}' deleted.",
            ),
            html=True,
        )

    @safe_execute
    def debugger_breakpoints_delete_all(self, *args):
        self.console_manual_command("breakpoint-delete-all")
        #        self.__debugger.breakpoint_delete_all()
        numbers = self.breakpoints.get_breakpoint_numbers()
        self.__debugger.breakpoint_delete(numbers)
        self.breakpoints.delete_all_breakpoints()
        data.signal_dispatcher.debug_breakpoint_delete_all.emit()

    @safe_execute
    def debugger_delete_all_watch_and_break_points(self, *args):
        self.console_manual_command("breakpoint-delete-all")
        self.__debugger.delete_all_watch_and_break_points()
        self.breakpoints.delete_all_breakpoints()
        data.signal_dispatcher.debug_breakpoint_delete_all.emit()
        self.breakpoints.delete_all_watchpoints()
        data.signal_dispatcher.debug_watchpoint_delete_all.emit()

    """
    Watch-points
    """

    @safe_execute
    def debugger_watchpoint_insert(self, name, filepath, index, _type):
        if not data.debugging_active:
            self.console_write(
                "<b style='color:{};'>Debugging not active, skipping inserting watchpoint!</b><br>".format(
                    data.theme["indication"]["error"],
                ),
                html=True,
            )
            return

        self.console_manual_command("watchpoint-insert")
        self.__stored_watchpoint_data = {
            "name": name,
            "filepath": filepath,
            "index": index,
            "type": _type,
        }
        # Execute command
        self.__debugger.watchpoint_insert(name)

    @safe_execute
    def debugger_watchpoint_delete(self, watchpoint_number):
        if not data.debugging_active:
            self.console_write(
                "<b style='color:{};'>Debugging not active, skipping deleting watchpoint!</b><br>".format(
                    data.theme["indication"]["error"],
                ),
                html=True,
            )
            return

        self.console_manual_command("watchpoint-delete")
        # Execute command
        self.__debugger.breakpoint_delete(watchpoint_number)
        self.breakpoints.delete_watchpoint(watchpoint_number)
        # Display deletion success
        self.console_write(
            "<b style='color:{};'>{}</b><br>".format(
                data.theme["indication"]["warning"],
                f"Watchpoint '{watchpoint_number}' deleted.",
            ),
            html=True,
        )

    @safe_execute
    def debugger_watchpoints_delete_all(self, *args):
        self.console_manual_command("watchpoint-delete-all")
        numbers = self.breakpoints.get_watchpoint_numbers()
        self.__debugger.breakpoint_delete(numbers)
        self.breakpoints.delete_all_watchpoints()
        data.signal_dispatcher.debug_watchpoint_delete_all.emit()

    """
    Memory
    """

    @safe_execute
    def debugger_general_register_values(self):
        self.console_manual_command("general-register-values")
        self.__debugger.get_register_values()

    @safe_execute
    def debugger_show_memory_region(self, selected_region):
        try:
            if selected_region == "general-registers":
                self.debugger_general_register_values()
            else:
                memory_dictionary = self.__sai.get_memory_regions()
                if selected_region in memory_dictionary.keys():
                    memory = memory_dictionary[selected_region]
                    self.console_manual_command(
                        "{} {} {}".format(
                            "data-read-memory-bytes",
                            hex(memory["origin"]),
                            hex(memory["size"]),
                        )
                    )
                    self.__queried_memory_region = selected_region

                    self.__debugger.get_memory(
                        "raw-memory",
                        #                        int(memory["origin"], 16),
                        #                        int(memory["size"], 16),
                        memory["origin"],
                        memory["size"],
                    )
                else:
                    self.__display_error(
                        f"Memory region '{selected_region}' not in chip's memory regions!"
                    )
        except:
            traceback.print_exc()

    """
    Variable objects
    """

    @safe_execute
    def debugger_variable_object_create(self, name: str) -> None:
        self.console_manual_command("var-create")
        self.__debugger.variable_object_create(name)

    @safe_execute
    def debugger_variable_object_delete(self, name: str) -> None:
        self.console_manual_command("var-delete")
        self.__debugger.variable_object_delete(name)

    @safe_execute
    def debugger_variable_object_update(self):
        self.console_manual_command("var-update")
        watch_view = self.main_form.projects.get_variable_watch_view()
        if watch_view is not None and watch_view.has_variables():
            self.__debugger.variable_object_update()

    """
    Memory view
    """

    def __show_memory_region(self):
        selected_region = self.__cache_comboboxes[
            "memory-region-select"
        ].get_selected_item_name()
        data.signal_dispatcher.memory_view_show_region.emit(selected_region)

    """
    General
    """

    def get_gdb_url(self) -> str:
        gdb_url = self.__cache_input_fields["gdb-url"].text()
        return gdb_url

    def set_gdb_url(self, gdb_url: str) -> None:
        self.__cache_input_fields["gdb-url"].setText(gdb_url)

    def update_style(self) -> None:
        for k, v in self.__cache_buttons.items():
            v.update_style(
                (
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                )
            )
        for k, v in self.__cache_labels.items():
            v.update_style()
        for k, v in self.__cache_input_fields.items():
            v.update_style()
        for k, v in self.__cache_comboboxes.items():
            v.update_style()
        self.console_input.update_style()

    def copy(self, *args) -> None:
        self.console.copy()
