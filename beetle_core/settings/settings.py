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

##  FILE DESCRIPTION:
##      Module used to save, load, ... settings of embeetle

import os
import os.path
import os_checker
import time
import traceback
import data
import themes
import purefunctions
import iconfunctions
import components.lockcache
from . import constants

# Editor settings
editor = constants.editor["default"].copy()
# Keyboard shortcuts
keys = constants.keys["default"].copy()


def check_shortcut_combination(combination_string):
    keys = []
    current_key = []
    for c in combination_string:
        if c == "+" and not (len(current_key) == 0):
            if len(current_key) > 0:
                keys.append("".join(current_key))
                current_key = []
        else:
            current_key.append(c)
    else:
        if len(current_key) > 0:
            keys.append("".join(current_key))
        else:
            keys = []
    valid_modifiers = ("ctrl", "shift", "alt")
    valid_key_names = {
        "add": "+",
        "plus": "+",
        "minus": "-",
        "subtract": "-",
        "divide": "/",
        "multiply": "*",
        "asterisk": "*",
        "down": "down",
        "tab": "tab",
        "backspace": "backspace",
        "escape": "escape",
        "up": "up",
        "left": "left",
        "right": "right",
        "home": "home",
        "end": "end",
        "pageup": "pageup",
        "pagedown": "pagedown",
        "delete": "delete",
        "insert": "insert",
        "escape": "escape",
        "f1": "F1",
        "f2": "F2",
        "f3": "F3",
        "f4": "F4",
        "f5": "F5",
        "f6": "F6",
        "f7": "F7",
        "f8": "F8",
        "f9": "F9",
        "f10": "F10",
        "f11": "F11",
        "f12": "F12",
    }
    out_keys = []
    for k in keys:
        key = k.lower()
        if len(key) > 1 and key in valid_modifiers:
            out_keys.append(k)
        elif len(key) > 1 and key in valid_key_names.keys():
            out_keys.append(valid_key_names[key])
        elif len(key) == 1:
            out_keys.append(k)
        else:
            out_keys = None
            break
    return out_keys


def check_settings_directory():
    if not os.path.isdir(data.settings_directory):
        os.mkdir(data.settings_directory)


"""
-------------------------------------------
Object for manipulating settings
-------------------------------------------
"""


class SettingsFileManipulator:
    """Object that will be used for saving, loading, ...

    all of the embeetle settings
    """

    # Class variables
    main_form = None
    settings_filename_with_path = ""
    beetle_core_directory = ""
    resources_directory = "resources/"
    level_spacing = "    "
    max_number_of_recent_files = 30
    max_number_of_recent_projects = 100
    recent_files = []
    recent_projects = []
    # General settings
    default_theme_name = "Crystal"
    theme = themes.get(default_theme_name)
    layout = constants.default_layout
    data_variables = (
        # Scaling
        "global_scale",
        "general_font_scale",
        "general_icon_scale",
        "toolbar_scale",
        "toplevel_menu_scale",
        "toplevel_font_scale",
        "custom_tab_scale",
        "scrollbar_zoom",
        "progressbar_zoom",
        "splitter_pixelsize",
        "window_radius",
        "home_window_button_scale",
        "mouse_scale",
        "current_font_name",
        "editor_font_name",
        "embeetle_base_url_override",
        # Default directories
        "default_project_create_directory",
        "default_project_open_directory",
        "default_project_import_directory",
        # Global settings
        "diagnostic_cap",
        "ribbon_style_toolbar",
        "icon_style",
    )

    def __init__(self, app_dir, res_dir, main_form=None):
        # Store reference to the main window
        self.main_form = main_form

        def display_func(*args, **kwargs):
            print(*args, **kwargs)

        display_functions = (
            "display_success",
            "display_warning",
            "display_error",
        )
        if main_form is not None:
            for f in display_functions:
                # Matic, I had an error like this here:
                #     AttributeError: 'MainWindow' object has no attribute 'display'
                # So I added an extra check: hasattr(main_form, 'display')
                if hasattr(main_form, "display") and hasattr(
                    main_form.display, f
                ):
                    setattr(self, f, getattr(main_form.display, f))
                else:
                    setattr(self, f, display_func)
        else:
            for f in display_functions:
                setattr(self, f, display_func)
        # Assign the application directory
        self.beetle_core_directory = app_dir
        self.resources_directory = res_dir
        # Create the user settings directory if needed
        check_settings_directory()
        # Join the application directory with the settings filename
        self.settings_filename_with_path = os.path.join(
            data.settings_directory, data.settings_filename["mk1"]
        )
        # Load the settings from the settings file
        self.load_settings()

    def set_theme(self, new_theme):
        self.theme = new_theme
        data.theme = new_theme

    def check_settings_file(self):
        """Check if the settings file exists."""
        return purefunctions.test_text_file(self.settings_filename_with_path)

    @components.lockcache.file_lock("create-settings-file-lock")
    def create_settings_file(self, settings_data):
        """Create the settings file with redundancy."""
        for i in range(5):
            try:
                ## Create the 'new' file
                new_file = self.settings_filename_with_path + ".new"
                try:
                    purefunctions.write_json_file(new_file, settings_data)
                except:
                    traceback.print_exc()
                    raise Exception(
                        "[Settings] Unable to create settings file!"
                    )

                ## Rename the current settings file to '.old'
                old_file = self.settings_filename_with_path + ".old"
                if os.path.isfile(old_file):
                    os.remove(old_file)
                if os.path.isfile(self.settings_filename_with_path):
                    os.rename(self.settings_filename_with_path, old_file)

                ## Rename the new file to the used
                os.rename(new_file, self.settings_filename_with_path)
                break
            except:
                traceback.print_exc()
                print(
                    "[SETTINGS-ERROR] An error occured during creation of the settings file!"
                )
                time.sleep(0.1)

    def write_settings_file(self, theme, recent_files, recent_projects):
        settings_data = {
            "theme": theme["name"],
            "recent_files": recent_files,
            "recent_projects": recent_projects,
            "editor": editor,
            "keys": keys,
        }
        for dv in self.data_variables:
            settings_data[dv] = getattr(data, dv)

        # Save the file to disk
        self.create_settings_file(settings_data)

    def save_settings(self):
        """Save all settings to the settings file."""
        self.write_settings_file(
            data.theme,
            self.recent_files,
            self.recent_projects,
        )

    def load_settings(self):
        """Load all setting from the settings file."""
        ## Try the old format first
        old_settings_filename_with_path = purefunctions.unixify_path_join(
            data.settings_directory, data.settings_filename["mk0"]
        )
        if os.path.isfile(
            old_settings_filename_with_path
        ) and not os.path.isfile(self.settings_filename_with_path):
            try:
                if self.__load_settings_mk0():
                    self.save_settings()
                    return True
            except:
                traceback.print_exc()

        ## New format
        # Check if the settings file exists
        if self.check_settings_file() is None:
            # Create the settings file
            self.write_settings_file(
                themes.get(self.default_theme_name),
                self.recent_files,
                self.recent_projects,
            )
            # Invoke main form callback
            if self.main_form is not None and hasattr(
                self.main_form, "_no_config_callback"
            ):
                self.main_form._no_config_callback()

        old_file = self.settings_filename_with_path + ".old"
        try:
            try:
                if not self.__restore_settings(
                    self.settings_filename_with_path
                ):
                    self.__restore_settings(old_file)
                    self.display_warning(
                        "Settings file doesn't exist, "
                        + "restored settings from a backup."
                    )
            except:
                try:
                    if self.__restore_settings(old_file):
                        self.display_warning(
                            "Settings file has errors, "
                            + "restored settings from a backup."
                        )
                    else:
                        self.save_settings()
                        self.display_success(
                            "Settings file doesn't exists, creating a new one."
                        )
                except:
                    self.save_settings()
                    self.display_success(
                        "Settings file doesn't exists or has errors,"
                        + "creating a new one and reseting all settings."
                    )
            # Return success
            return True
        except:
            self.display_error(traceback.format_exc())
            self.set_theme(themes.get(self.default_theme_name))
            self.recent_files = []
            self.recent_projects = []
            # Return error
            return False

    def __restore_settings(self, file):
        global keys
        global editor

        if os.path.isfile(file):
            settings_data = purefunctions.load_json_file(file)
            if settings_data is None:
                raise Exception(
                    "[Settings] Error loading settings file: {}".format(file)
                )
            # $ Theme
            if "theme" in settings_data.keys():
                self.set_theme(themes.get(settings_data["theme"]))
            # $ Recent files
            if "recent_files" in settings_data.keys():
                self.recent_files = settings_data["recent_files"]
            # $ Recent projects
            if "recent_files" in settings_data.keys():
                self.recent_projects = settings_data["recent_projects"]
            # $ Keys
            if "keys" in settings_data.keys():
                for k, v in settings_data["keys"].items():
                    keys[k] = v
            if "editor" in settings_data.keys():
                for k, v in settings_data["editor"].items():
                    editor[k] = v
            # $ Data variables
            for v in self.data_variables:
                if v in settings_data.keys():
                    if v.lower() == "icon_style":
                        # It is possible that 'settings_data[v]' is holding a deprecated icon style
                        # identifier. My 'filter_style()' solves this problem.
                        settings_data[v] = iconfunctions.filter_style(
                            settings_data[v]
                        )
                    setattr(data, v, settings_data[v])
                else:
                    print("Setting is not in settings file: '{}'".format(v))

            return True
        else:
            return False

    """
    Old system with a Python code file
    """

    def __load_settings_mk0(self):
        """Load all setting from the settings file."""
        globs = {
            "data": data,
        }
        settings_filename_with_path = purefunctions.unixify_path_join(
            data.settings_directory, data.settings_filename["mk0"]
        )
        old_file = settings_filename_with_path + ".old"

        def restore(file):
            if os.path.isfile(file):
                # New theme check
                with open(file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    f.close()

                for i, line in enumerate(lines):
                    if "theme = themes." in line:
                        current_theme = line.replace(
                            "theme = themes.", ""
                        ).strip()
                        lines[i] = f"theme = {repr(current_theme)}\n"
                        with open(file, "w", encoding="utf-8") as f:
                            f.write("".join(lines))
                            f.close()
                        break
                # New theme check
                init_module = purefunctions.load_module(file, globs)

                # Theme
                if init_module["theme"]:
                    if isinstance(init_module["theme"], str):
                        self.set_theme(themes.get(init_module["theme"]))
                # Recent files
                if "recent_files" in init_module.keys():
                    self.recent_files = init_module["recent_files"]
                # Recent projects
                if "recent_projects" in init_module.keys():
                    self.recent_projects = init_module["recent_projects"]
                # Keys
                if "keys" in init_module.keys():
                    global keys
                    for k, v in init_module["keys"].items():
                        keys[k] = v
                if "editor" in init_module.keys():
                    global editor
                    for k, v in init_module["editor"].items():
                        editor[k] = v

                def set_setting(name, custom_module_name=None):
                    init_module_name = name
                    if custom_module_name:
                        init_module_name = custom_module_name
                    try:
                        setattr(data, name, init_module[init_module_name])
                    except:
                        print("Error loading setting: ", name)

                for v in self.data_variables:
                    set_setting(v)

                return True
            else:
                return False

        try:
            try:
                if not restore(settings_filename_with_path):
                    restore(old_file)
                    self.display_warning(
                        "Settings file doesn't exist, "
                        + "restored settings from a backup."
                    )
            except:
                try:
                    if restore(old_file):
                        self.display_warning(
                            "Settings file has errors, "
                            + "restored settings from a backup."
                        )
                    else:
                        self.save_settings()
                        self.display_success(
                            "Settings file doesn't exists, creating a new one."
                        )
                except:
                    self.save_settings()
                    self.display_success(
                        "Settings file doesn't exists, creating a new one."
                    )
            # Return success
            return True
        except:
            self.display_error(traceback.format_exc())
            self.set_theme(themes.get(self.default_theme_name))
            self.recent_files = []
            self.recent_projects = []
            # Return error
            return False

    """
    Old system with a Python code file
    """

    def add_recent_file(self, new_file):
        """Add a new file to the recent file list."""
        # Replace back-slashes to forward-slashes on windows
        if os_checker.is_os("windows"):
            new_file = purefunctions.unixify_path(new_file)
        # Check recent files list length
        while len(self.recent_files) > self.max_number_of_recent_files:
            # The recent files list is to long
            self.recent_files.pop(0)
        # Check if the new file is already in the list
        if new_file in self.recent_files:
            # Check if the file is already at the top
            if self.recent_files.index(new_file) == (
                self.max_number_of_recent_files - 1
            ):
                return
            # Remove the old file with the same name as the new file from the list
            self.recent_files.pop(self.recent_files.index(new_file))
            # Add the new file to the end of the list
            self.recent_files.append(new_file)
        else:
            # The new file is not in the list, append it to the end of the list
            self.recent_files.append(new_file)
        # Save the new settings
        self.save_settings()

    def add_recent_project(self, new_project):
        """Add a new project to the recent project list."""
        # Replace back-slashes to forward-slashes on windows
        if os_checker.is_os("windows"):
            new_project = purefunctions.unixify_path(new_project)
        # Check recent projects list length
        while len(self.recent_projects) > self.max_number_of_recent_projects:
            self.recent_projects.pop(0)
        # Check if the new project is already in the list
        if new_project in self.recent_projects:
            # Check if the file is already at the top
            if self.recent_projects.index(new_project) == (
                self.max_number_of_recent_projects - 1
            ):
                return
            # Remove the old file with the same name as the new file from the list
            self.recent_projects.pop(self.recent_projects.index(new_project))
            # Add the new file to the end of the list
            self.recent_projects.append(new_project)
        else:
            # The new file is not in the list, append it to the end of the list
            self.recent_projects.append(new_project)
        # Save the new settings
        self.save_settings()

    """
    Property manipulation functions
    """

    def main_form_send(self, command):
        if self.main_form is not None:
            self.main_form.send(command)

    def pmf_autocompletion_toggle(self, state):
        editor["autocompletion"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_autocompletion_type_select(self, state):
        editor["autocompletion_type"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_wordwrap_toggle(self, state):
        editor["word_wrap"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_edge_marker_toggle(self, state):
        editor["edge_marker_visible"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_edge_marker_column_set(self, value):
        editor["edge_marker_column"] = value
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_end_of_line_toggle(self, state):
        editor["end_of_line_visibility"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_cursor_line_visibility_toggle(self, state):
        editor["cursor_line_visible"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_whitespace_visible_toggle(self, state):
        editor["whitespace_visible"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_tabs_use_spaces_toggle(self, state):
        editor["tabs_use_spaces"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_makefile_uses_tabs_toggle(self, state):
        editor["makefile_uses_tabs"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_makefile_whitespace_visible_toggle(self, state):
        editor["makefile_whitespace_visible"] = state
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_tab_width_set(self, value):
        editor["tab_width"] = value
        self.save_settings()
        components.thesquid.TheSquid.update_options_on_all_editors()
        self.main_form_send("restyle")

    def pmf_ribbon_style_toolbar_toggle(self, state=None):
        if state is None:
            data.ribbon_style_toolbar = not data.ribbon_style_toolbar
        else:
            data.ribbon_style_toolbar = state
        self.save_settings()
        self.main_form_send("restyle")
        if self.main_form is not None and hasattr(self.main_form, "toolbar"):
            self.main_form.settings.restore(echo=False)

    def pmf_theme_set(self, value, notify_restart_needed=False):
        data.theme = themes.get(value)
        iconfunctions.update_style()
        self.save_settings()
        self.main_form_send("restyle")
        data.signal_dispatcher.update_styles.emit()
        if notify_restart_needed:
            data.signal_dispatcher.restart_needed_notify.emit("Theme changed")

    def pmf_icons_set(self, name):
        new_icon_style = iconfunctions.get_style_value_by_name(name)
        iconfunctions.change_style(new_icon_style)
        self.save_settings()
        data.signal_dispatcher.restart_needed_notify.emit("Icon theme changed")

    def pmf_general_font_set(self, font_name, notify_restart_needed=False):
        data.current_font_name = font_name
        self.save_settings()
        self.main_form_send("restyle")
        data.signal_dispatcher.update_styles.emit()
        if notify_restart_needed:
            data.signal_dispatcher.restart_needed_notify.emit(
                "General font changed"
            )

    def pmf_editor_font_set(self, font_name, notify_restart_needed=False):
        data.editor_font_name = font_name
        self.save_settings()
        self.main_form_send("restyle")
        data.signal_dispatcher.update_styles.emit()
        if notify_restart_needed:
            data.signal_dispatcher.restart_needed_notify.emit(
                "Editor font changed"
            )

    def pmf_embeetle_base_url_override_set(self, new_url):
        data.embeetle_base_url_override = new_url
        data.signal_dispatcher.base_url_override_change.emit()
        self.save_settings()
        self.main_form_send("restyle")
        data.signal_dispatcher.update_styles.emit()
