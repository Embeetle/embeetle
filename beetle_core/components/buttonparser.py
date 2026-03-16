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

import functools
import json
import os
import subprocess
import traceback
from contextlib import contextmanager
from typing import *

import data
import functions
import gui.dialogs.popupdialog
import gui.templates.widgetgenerator
import iconfunctions
import jinja2
import project.makefile_target_executer
import qt


class ButtonParser:
    store = None
    main_form = None
    button_file = None
    necessary_fields = (
        # "target",
        "icon",
        "hover-text",
        "help-text",
    )
    default_layout = """
# =========================================================================
# 💡 USER-DEFINED BUTTONS CONFIGURATION 💡
# =========================================================================
# This file defines the toolbar buttons for your Embeetle project.
# It uses a standard JSON format, but with a powerful twist: it's a
# Jinja template! This allows you to use variables to dynamically
# customize button behavior.
#
# HOW TO USE JINJA:
# -----------------
# 1. Use double curly braces `{{ variable_name }}` to insert values from
#    the Jinja environment dictionary. For instance, `{{ make }}` will be
#    replaced with the full path to your `make` executable.
# 2. You can use these variables in any string field. For example, to use
#    the project's build directory, simply write `{{ build_directory }}`.
#
# AVAILABLE VARIABLES:
# --------------------
# The following variables are available for templating:
#    - `{{ beetle_core_directory }}`: The path to the Beetle Core directory.
#    - `{{ project_directory }}`: The path to the current project's root directory.
#    - `{{ build_directory }}`: The path to the build output directory.
#    - `{{ makefile }}`: The path to the project's `Makefile`.
#    - `{{ make }}`: The path to the `make` executable.
#    - `{{ compiler }}`: The path to the compiler executable (e.g., GCC).
#
# TIP: For a quick reference of available icon paths, check the
#      'beetle_core/resources/icons/' folder within your Embeetle
#      installation directory.
#
# =========================================================================
{
    "clean":
    {
        "icon": "icons/gen/clean.png",
        "hover-text": "Run 'clean' target in makefile",
        "help-text": "Run 'clean' target in makefile",
        "shortcut": "F2"
    },

    "build":
    {
        "icon": "icons/gen/build.png",
        "hover-text": "Run 'build' target in makefile",
        "help-text": "Run 'build' target in makefile",
        "shortcut": "F3"
    },

    "flash":
    {
        "icon": "icons/chip/flash.png",
        "hover-text": "Run 'flash' target in makefile",
        "help-text": "Run 'flash' target in makefile",
        "shortcut": "F4"
    }
}
"""

    def __init__(self, main_form, button_file) -> None:
        """"""
        # Initialization
        self.main_form = main_form
        self.button_file = button_file
        # Parsing
        self.parse()
        return

    def parse(self) -> List[Union[qt.QAction, qt.QWidgetAction]]:
        """Parse the contents of the button file."""
        # Read layout
        if not os.path.isfile(self.button_file):
            with open(
                self.button_file, "w+", encoding="utf-8", newline="\n"
            ) as f:
                f.write(self.default_layout)
        layout = None
        with open(self.button_file, "r", newline="\n") as f:
            layout = f.read()
        # Parsing
        buttons: List[Union[qt.QAction, qt.QWidgetAction]] = []
        count: int = 2
        try:
            # Create the Jinja template
            template = jinja2.Template(layout)
            # Define your variables
            template_environment = {
                "beetle_core_directory": data.beetle_core_directory,
                "project_directory": data.current_project.get_proj_rootpath(),
                "build_directory": (
                    data.current_project.get_treepath_seg().get_abspath(
                        "BUILD_DIR"
                    )
                ),
                "makefile": (
                    data.current_project.get_treepath_seg().get_abspath(
                        "MAKEFILE"
                    )
                ),
                "make": (
                    data.current_project.get_toolpath_seg().get_abspath(
                        "BUILD_AUTOMATION"
                    )
                ),
                "compiler": (
                    data.current_project.get_toolpath_seg().get_abspath(
                        "COMPILER_TOOLCHAIN"
                    )
                ),
            }
            # Render the template
            rendered_template = template.render(template_environment)

            # Remove comments and parse json data
            button_layout: str = functions.remove_comments(rendered_template)
            json_data = json.loads(button_layout)
            # Parse loop
            for k, v in json_data.items():
                # Name
                name = k
                # Check fields
                keys = [x for x in json_data[name].keys()]
                missing_keys = []
                for f in self.necessary_fields:
                    if not (f in keys):
                        missing_keys.append(f)
                if len(missing_keys) > 0:
                    raise Exception(
                        "[ButtonParser] Missing button '{}' fields: {}".format(
                            name, missing_keys
                        )
                    )
                # Create buttons
                try:
                    if "shortcut" in v.keys():
                        shortcut = v["shortcut"]
                    else:
                        shortcut = "F{}".format(count)
                        count += 1
                    statustip = "{} (Shortcut: {})".format(
                        v["help-text"], shortcut
                    )
                    tooltip = "{} (Shortcut: {})".format(
                        v["hover-text"], shortcut
                    )

                    # Explicit makefile function
                    function = functools.partial(
                        self.__makefile_execution_function, name
                    )
                    function.__name__ = name

                    # Special properties
                    special_properties = (
                        "commands",
                        "current-working-directory",
                    )
                    found_special_properties = {}
                    for sp in special_properties:
                        if sp in v.keys():
                            found_special_properties[sp] = v[sp]
                            function = None

                    new_button = {
                        "name": name,
                        "text": k,
                        "shortcut": shortcut,
                        "statustip": statustip,
                        "tooltip": tooltip,
                        "function": function,
                        "icon": v["icon"],
                        "enabled": True,
                        "menubar_action": False,
                        "warn_of_existing_shortcut": False,
                    }
                    new_button.update(found_special_properties)
                    buttons.append(new_button)
                except:
                    self.main_form.display.display_error(traceback.format_exc())
        except:
            self.main_form.display.display_error(traceback.format_exc())

        return buttons

    def __command_callback(self, result, callbackArg):
        data.signal_dispatcher.command_completed.emit(result)

    def __makefile_execution_function(self, target, *args):
        try:
            # Output console
            console_name = "Output"
            new_console = self.main_form.create_console(
                console_name, console_type=data.ConsoleType.Make
            )
            # Execute commands
            executioner = (
                project.makefile_target_executer.MakefileTargetExecuter()
            )
            executioner.execute_makefile_targets(
                console=new_console,
                target=target,
                callback=self.__command_callback,
                callbackArg=None,
            )
        except:
            self.main_form.display.display_error(traceback.format_exc())
            traceback.print_exc()
        return
