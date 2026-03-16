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
import multiprocessing
from typing import *
import qt
import data
import purefunctions
import iconfunctions
import functions
import settings
import gui.stylesheets.statusbar
import gui.templates.widgetgenerator
import components.communicator
import components.interpreter
import components.thesquid
import os_checker


class BaseAppWindow(qt.QMainWindow):
    # Signals
    send_data = qt.pyqtSignal(object)
    received = qt.pyqtSignal(object)

    # Variables
    communicator: components.communicator.Communicator
    receive_queue: multiprocessing.Queue
    menubar_functions: Dict[str, Callable] = {}
    # Flag indicating the first time the user config file was imported
    __first_scan = True

    def self_destruct(self) -> None:
        """"""
        self.__del__()
        components.thesquid.TheSquid.self_destruct()
        return

    def __init__(self, name: str) -> None:
        super().__init__()
        # Initialize the communicator
        self.communicator = components.communicator.Communicator(name)
        self.send_data.connect(self.communicator.send)
        self.receive_queue = multiprocessing.Queue()
        # Install the event filter
        #        self.installEventFilter(self.EventFilter(self))
        # Initialize the global window reference
        data.main_form = self

    def __del__(self) -> None:
        if hasattr(self, "communicator") and self.communicator is not None:
            self.communicator.self_destruct()
            del self.communicator

    def _basic_initialization(
        self, name: str, object_name: str, title: str
    ) -> None:
        # Set the name of the main window
        self.name = name
        self.setObjectName(object_name)
        self.title = title
        # Initialize the main window
        self.__set_title()
        # Initialize menubar function storage
        self.menubar_functions = {}
        return

    def __set_title(self) -> None:
        version_string = functions.get_embeetle_version()
        self.setWindowTitle("{} {}".format(self.title, version_string))
        # Set the main window icon if it exists
        if os.path.isfile(data.application_icon_abspath):
            self.setWindowIcon(qt.QIcon(data.application_icon_abspath))

    def change_title(self, new_title: str) -> None:
        self.title = new_title
        self.__set_title()

    def _show(self) -> None:
        maximized_flag = False
        if self.isMaximized():
            maximized_flag = True
        self._set_flags(qt.Qt.WindowType.Window)  # Needed for Linux
        self.__flags_cache = self.windowFlags()
        self.__set_title()
        if maximized_flag:
            self.showMaximized()
        else:
            self.showNormal()
        self.activateWindow()

        if os_checker.is_os("windows"):
            # Hackish, but works
            self.setWindowFlags(
                self.__flags_cache | qt.Qt.WindowType.WindowStaysOnTopHint
            )
            self.show()
            qt.QTimer.singleShot(10, self._reset_flags)

    def _reset_flags(self):
        self.setWindowFlags(self.__flags_cache)
        self.show()

    def _set_flags(self, flags: Union[int, qt.Qt.WindowType]) -> None:
        self.setWindowFlags(flags)
        self.setWindowFlags(
            self.windowFlags()
            | qt.Qt.WindowType.WindowMaximizeButtonHint
            | qt.Qt.WindowType.WindowMinimizeButtonHint
        )

    def connect_received_signal(self, func: Callable[[object], None]) -> None:
        self.communicator.received.connect(func)

    def send(self, _data: str) -> None:
        self.send_data.emit(_data)

    def receive_queue_clear(self):
        # Clear the receive queue
        while not self.receive_queue.empty():
            self.receive_queue.get()

    def _init_statusbar(self):
        statusbar = qt.QStatusBar(self)
        gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
            name="statusbar-left-groupbox",
            vertical=False,
            borderless=True,
            margins=(3, 0, 3, 0),
            h_size_policy=qt.QSizePolicy.Policy.Minimum,
        )
        # Add label for showing the cursor position in a basic widget
        statusbar_label_left = gui.templates.widgetgenerator.create_label(
            text=""
        )
        statusbar_label_left.set_colors()
        gb.layout().addWidget(statusbar_label_left)
        statusbar.addWidget(gb)
        # Add the statusbar to the MainWindow
        self.setStatusBar(statusbar)
        # Store references
        self.statusbar = statusbar
        self.statusbar_label_left = statusbar_label_left
        # Set the style
        self.update_statusbar_style()

    def update_statusbar_style(self):
        self.statusbar.setFont(data.get_general_font())
        self.statusbar.setStyleSheet(gui.stylesheets.statusbar.get_default())
        self.statusbar_label_left.setFont(data.get_general_font())
        self.statusbar_label_left.update_style()

    def exit(self, event=None):
        self.close()

    """
    Widget creation functions
    """

    def _create_groupbox(self, name, text):
        return gui.templates.widgetgenerator.create_groupbox(name, text)

    def _create_pushbutton(
        self, name, tooltip, icon_name, size, checkable=False
    ):
        return gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name=name,
            tooltip=tooltip,
            icon_name=icon_name,
            size=size,
            checkable=checkable,
        )

    def _create_label(self, text=None, bold=False, image=None, parent=None):
        if parent is None:
            parent = self
        return gui.templates.widgetgenerator.create_label(
            text,
            bold,
            image,
            parent=parent,
            transparent_background=True,
        )

    def show_system_explorer(self, directory=None):
        if os_checker.is_os("windows"):
            command = ["explorer ."]
            if directory is not None:
                directory = directory.replace("/", "\\")
                #                print(directory)
                command = ["explorer", directory]
        else:
            raise Exception(
                f"File explorer unimplemented yet for {os_checker.get_os()}!"
            )
        purefunctions.subprocess_popen(command)

    """
    Geometry
    """

    def resizeEvent(self, *args):
        super().resizeEvent(*args)
        functions.check_size(self)

    def moveEvent(self, *args):
        super().moveEvent(*args)
        functions.check_size(self)

    """
    Actions/Menus
    """

    def add_and_store_shortcut(
        self, shorcut_name, shortcut_keys, shortcut_function
    ):
        if not hasattr(self, "stored_keyboard_shortcuts"):
            self.stored_keyboard_shortcuts = {}
        if shorcut_name in self.stored_keyboard_shortcuts.keys():
            #            delattr(self, shorcut_name)
            old_shortcut = self.stored_keyboard_shortcuts.pop(shorcut_name)
            old_shortcut["shortcut"].setParent(None)
            del old_shortcut["shortcut"]
            del old_shortcut["function"]
        shortcut = qt.QShortcut(shortcut_keys, self)
        #        setattr(self, shorcut_name, shortcut)
        shortcut.activated.connect(shortcut_function)
        self.stored_keyboard_shortcuts[shorcut_name] = {
            #            "shortcut": getattr(self, shorcut_name),
            "shortcut": shortcut,
            "function": shortcut_function,
        }

    def set_shortcut_enabled(self, shorcut_name: str, state: bool) -> None:
        self.stored_keyboard_shortcuts[shorcut_name]["shortcut"].setEnabled(
            state
        )

    def reassign_shortcuts(self):
        for k, v in self.action_cache.items():
            if v.get_keys_data() is not None:
                key_combo, keys, keys_text = self.__create_key_combination(
                    v.get_keys_data()
                )
                if k in self.stored_keyboard_shortcuts.keys():
                    # Reassign the key combination
                    shortcut_data = self.stored_keyboard_shortcuts[k]
                    shortcut_data["shortcut"].setKey(keys)
                    # Update the action text
                    v.set_shortcut(key_combo)

    def __create_key_combination(self, keys_data):
        key_combo = None
        keys_text = None
        if keys_data is not None:
            if isinstance(keys_data, str):
                key_combo = keys_data
            elif keys_data[0] == "#":
                keys_text = settings.keys[keys_data[1]][keys_data[2]]
            elif len(keys_data) == 3 and isinstance(keys_data[2], int):
                key_combo = settings.keys[keys_data[0]][keys_data[1]][
                    keys_data[2]
                ]
            else:
                key_combo = settings.keys[keys_data[0]][keys_data[1]]
        keys = None
        if key_combo is not None and key_combo != "":
            if isinstance(key_combo, list):
                if len(key_combo) == 1:
                    keys = key_combo[0]
                elif any([isinstance(x, str) for x in key_combo]):
                    keys = []
                    for k in key_combo:
                        keys.append(k)
                else:
                    raise Exception(
                        "Key combination list has to contain only strings!"
                    )
            elif isinstance(key_combo, str):
                keys = key_combo
            else:
                raise Exception(
                    f"Unknown key combination type: {key_combo.__class__}"
                )
        return key_combo, keys, keys_text

    def create_action(
        self,
        name,
        text,
        keys_data,
        tooltip,
        statustip,
        icon,
        function,
        enabled=True,
        menubar_action=True,
        warn_of_existing_shortcut=True,
    ):
        if not hasattr(self, "used_key_combinations"):
            self.used_key_combinations = {}
        # Key combination
        key_combo, keys, keys_text = self.__create_key_combination(keys_data)
        if key_combo is not None and key_combo != "":
            if (
                warn_of_existing_shortcut
                and key_combo in self.used_key_combinations.keys()
            ):
                functions.echo(
                    f"Key combination '{key_combo}' is already "
                    + f"used by '{function.__name__}'!"
                )
            self.used_key_combinations[key_combo] = function
        else:
            if keys_text is not None:
                text = "{}\t{}".format(text, keys_text)
        # Add shortcut to the main window
        if keys is not None:
            self.add_and_store_shortcut(name, keys, function)
        # All keyboard shortcuts are now processed by the MainWindow
        # so the names of the actions have to have the shotcut
        # combination in them!
        if menubar_action:
            base_class = self.MenuBarAction
        else:
            base_class = self.BaseAction
        action = base_class(
            text,
            self,
            keys=key_combo,
            keys_data=keys_data,
        )
        if tooltip:
            action.setToolTip(tooltip)
        if statustip:
            action.setStatusTip(statustip)
        # Icon and pixmap
        action.pixmap = None
        if icon is not None:
            action.set_icon(icon)
            action.pixmap = iconfunctions.get_qpixmap(icon, 32, 32)
        # Function
        if function is not None and name is not None:
            # Add the raw function to the menubar
            action.triggered.connect(function)
            action.function = function
            self.menubar_functions[function.__name__] = function
            data.global_function_information[function.__name__] = (
                name,
                function,
                icon,
                keys,
                statustip,
            )
        # Toggle action according to passed
        # parameter and return the action
        action.setEnabled(enabled)
        # Store the action in the menubar
        if name is not None:
            self.menubar.add_action(name, action)

        if not hasattr(self, "action_cache"):
            self.action_cache = {}
        elif name in self.action_cache.keys():
            old_action = self.action_cache.pop(name)
            del old_action
        self.action_cache[name] = action

        return action

    def update_actions(self) -> None:
        for k, v in self.action_cache.items():
            v.reset_icon()

    """
    Common objects
    """

    class MenuBar(qt.QMenuBar):
        stored_actions = {}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set the default font
            self.setFont(data.get_toplevel_font())

        def keyPressEvent(self, e):
            """This needs to be here to not propagate key press event any
            further, in order to ensure that the information overlay will not be
            displayed while the menubar is active."""
            super().keyPressEvent(e)
            e.accept()

        def contextMenuEvent(self, e):
            # Disable the show/hide toolbars menu on right-click
            e.accept()

        def add_action(self, name, action):
            BaseAppWindow.MenuBar.stored_actions[name] = action

    class BaseAction(qt.QAction):
        _text = None
        __keys_data = None
        __keyboard_shorcut = None
        __icon_path = None

        def __init__(self, *args, keys=None, keys_data=None):
            super().__init__(*args)
            if len(args) == 3:
                icon, text, parent = args
            elif len(args) == 2:
                text, parent = args
            else:
                raise Exception(
                    "[MenuBarAction] Unsupported constructor parameters!"
                )
            self._text = text
            self.set_shortcut(keys)
            self.set_keys_data(keys_data)

        def get_keys_data(self):
            return self.__keys_data

        def set_keys_data(self, keys_data):
            self.__keys_data = keys_data

        def get_shortcut(self):
            return self.__keyboard_shorcut

        def set_shortcut(self, keys):
            if keys is not None and keys.startswith("#") == False:
                self.__keyboard_shorcut = keys
                self.setText(self._text)

        def clear_shortcut(self, keys):
            self.__keyboard_shorcut = None
            self.setText(self._text)

        def set_icon(self, icon_path):
            self.__icon_path = icon_path
            self.reset_icon()

        def reset_icon(self):
            if self.__icon_path is None:
                return
            icon = iconfunctions.get_qicon(self.__icon_path)
            self.setIcon(icon)

    class MenuBarAction(BaseAction):
        def set_shortcut(self, keys):
            if keys is not None and keys.startswith("#") == False:
                self.__keyboard_shorcut = keys
                self.setText("{}\t{}".format(self._text, keys))

    """
    Interpreter
    """

    def _init_interpreter(
        self,
        get_references_func,
        print_func,
        print_success_func,
        print_warning_func,
        print_error_func,
    ):
        """Initialize the python interactive interpreter that will be used with
        the python REPL QLineEdit."""
        self.print_func = print_func
        self.print_success_func = print_success_func
        self.print_warning_func = print_warning_func
        self.print_error_func = print_error_func
        self.interpreter = components.interpreter.CustomInterpreter(
            get_references_func,
            print_func,
        )
        # Import the user functions
        self.import_user_functions()

    def import_user_functions(self):
        """Import the user defined functions form the user_functions.cfg
        file."""
        user_file_path = os.path.join(
            data.settings_directory, data.config_filename
        )
        # Test if user_functions file exists
        if os.path.isfile(user_file_path) == False:
            functions.create_default_config_file()
            self.print_success_func("Default user functions file generated!")
            return
        user_file = open(user_file_path, "r", encoding="utf-8")
        user_code = user_file.read()
        user_file.close()
        result = self.interpreter.eval_command(user_code, False)
        if result is not None:
            self.print_error_func(
                "ERROR IN USER CONFIGURATION FILE:\n" + result
            )
            return
        # Execute the data module's first_scan function once
        if self.__first_scan == True:
            result = self.interpreter.eval_command(
                """
if "first_scan" in locals() and callable(first_scan):
    first_scan()
                """,
                False,
            )
            if result is not None:
                self.print_error_func(result)
            self.__first_scan = False

        # Update the styles of all objects
        components.thesquid.TheSquid.update_styles()

    def _reset_interpreter(self):
        new_references, ac_list_prim, ac_list_sec = self.get_references_func()
        # Clear the references
        self.interpreter.reset_locals()
        # Update the interpreter with the new locals
        self.interpreter.update_locals(new_references)
        # Reimport the user functions
        self.import_user_functions()
