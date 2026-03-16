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

from __future__ import annotations
from typing import *
import functools
import traceback
import qt
import data
import functions
import iconfunctions
import serverfunctions
import gui.fonts.fontloader
import gui.helpers.advancedcombobox
import gui.templates.treewidget
import gui.templates.widgetgenerator
import themes
import settings
import settings.constants

general_keys_for_editor = (
    "toggle_comment",
    "toggle_edge",
    "toggle_wrap",
    "toggle_autocompletion",
    "to_lowercase",
    "to_uppercase",
    "reset_zoom",
    "find_brace",
    "reload_file",
)


class SettingsWorker(qt.QObject):
    finished = qt.pyqtSignal(dict)

    def __init__(self, main_form):
        super().__init__()
        self.main_form = main_form

    def run(self):
        output = {}
        ## General
        output["general"] = {
            "text": "General:",
            "icon": "icons/gen/gear.png",
            "items": {},
        }

        # Ribbon style toolbar
        def _ribbon_style_toolbar_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_ribbon_style_toolbar_toggle(
                state
            )

        output["general"]["items"]["ribbon_style_toolbar_toggle"] = {
            "text": "Big toolbar",
            "tooltip": "Toggle big toolbar style",
            "func": _ribbon_style_toolbar_toggle,
            "value": data.ribbon_style_toolbar,
        }

        # Scaling
        def _show_scaling():
            self.main_form.display.dialog_show("scaling_dialog")

        output["general"]["items"]["show_scaling"] = {
            "text": "Scaling dialog",
            "tooltip": (
                "Show the scaling dialog to adjust Embeetle's visual style"
            ),
            "func": _show_scaling,
            "button-text": "SHOW",
            "button-icon": "icons/menu_view/zoom.png",
        }

        # Server
        output["server"] = {
            "text": "Server:",
            "icon": "icons/gen/world.png",
            "items": {},
        }
        # Used URL
        output["server"]["items"]["used-url"] = {
            "tooltip": (
                "The current actually used URL for updating, generating projects, ..."
            ),
        }
        # Base URL override
        override_items = ["AUTOMATIC"]
        for bu in data.BASE_URLS:
            override_items.append(bu)
        output["server"]["items"]["base-url-override"] = {
            "text": "Base server URL: ",
            "tooltip": (
                "Select the Embeetle server used for updating, generating projects, ..."
            ),
            "items": override_items,
            "initial-item": data.embeetle_base_url_override,
        }

        ## Theme
        output["theme"] = {
            "text": "Theme:",
            "icon": "icons/theme/themes.svg",
            "items": {},
        }

        # Color theme
        def _base_theme_change(combobox, new_value, new_item):
            if data.theme["name"] != new_value:
                self.main_form.settings.manipulator.pmf_theme_set(new_value)

        theme_list = themes.get_all()
        acb_items = []
        initial_item = None
        for t in sorted(theme_list, key=lambda x: x["name"]):
            new_item = {
                "name": t["name"],
                "widgets": (
                    {"type": "image", "icon-path": t["image_file"]},
                    {"type": "text", "text": t["name"]},
                ),
            }
            acb_items.append(new_item)
            if new_item["name"].lower() == data.theme["name"].lower():
                initial_item = new_item
        output["theme"]["items"]["base_theme_change"] = {
            "text": "Color theme: ",
            "tooltip": "Embeetle theme, used for styling all widgets",
            "func": _base_theme_change,
            "acb-items": acb_items,
            "acb-no-items-text": "No theme found!",
            "acb-initial-item": initial_item,
        }

        # Icon theme
        #        def _icon_theme_change(combobox, new_value, new_item):
        #            if data.icon_style != new_value:
        #                self.main_form.settings.manipulator.pmf_icons_set(new_value)
        ##        icon_style_list = iconfunctions.get_all_styles()
        #        icon_style_list = iconfunctions.get_valid_styles()
        #        acb_items = []
        #        initial_item = None
        #        for t in sorted(icon_style_list):
        #            new_item = {
        #                "name": t,
        #                "widgets":
        #                    (
        #                        {"type": "text", "text": t},
        #                    )
        #            }
        #            acb_items.append(new_item)
        #            if iconfunctions.get_style_value_by_name(new_item["name"]) == data.icon_style:
        #                initial_item = new_item
        #        output["theme"]["items"]["icon_theme_change"] = {
        #            "text": "Icon theme:  ",
        #            "tooltip": "Used Embeetle icon set",
        #            "func": _icon_theme_change,
        #            "acb-items": acb_items,
        #            "acb-no-items-text": "No icon set found!",
        #            "acb-initial-item": initial_item,
        #        }

        # Refresh theme
        def refresh_func(*args):
            self.main_form.settings.manipulator.pmf_theme_set(
                data.theme["name"]
            )

        output["theme"]["items"]["refresh"] = {
            "text": "Refresh theme",
            "tooltip": "Refresh the current theme",
            "func": refresh_func,
            "button-text": "REFRESH",
            "button-icon": "icons/dialog/refresh.png",
        }

        ## Fonts
        output["fonts"] = {
            "text": "Font:",
            "icon": "icons/menu_edit/to_lower.svg",
            "items": {},
        }
        initial_item = None
        font_items = gui.fonts.fontloader.get_all_fonts()
        output["fonts"]["items"]["general-font"] = {
            "text": "General font: ",
            "tooltip": (
                "Select the general font of Embeetle (menus, tree-widgets, ...)"
            ),
            "items": font_items,
            "initial-item": data.current_font_name,
        }
        output["fonts"]["items"]["editor-font"] = {
            "text": "Editor font:  ",
            "tooltip": "Select the editor font of Embeetle",
            "items": font_items,
            "initial-item": data.editor_font_name,
        }

        ## Editor
        output["editor"] = {
            "text": "Editor:",
            "icon": "icons/menu_edit/edit.png",
            "items": {},
        }

        # Autocompletion
        output["editor"]["items"]["autocompletion_toggle"] = {
            "text": "Enable autocompletion",
            "tooltip": "Toggle autocompletions on/off",
            "func": None,
            "value": settings.editor["autocompletion"],
        }
        # Autocompletion types
        output["editor"]["items"]["autocompletion_type_0"] = {
            "text": (
                "Show autocomplete on 'Ctrl+Space' press, 'Tab' or 'Enter' to insert selection"
            ),
            "tooltip": (
                "Show autocomplete on 'Ctrl+Space' press, 'Tab' or 'Enter' to insert selection"
            ),
            "func": None,
            "value": (
                settings.editor["autocompletion_type"]
                == settings.constants.AutocompletionType.CtrlPlusEnter
            ),
        }
        output["editor"]["items"]["autocompletion_type_1"] = {
            "text": (
                "Show autocomplete on 'Tab' press, 'Tab' or 'Enter' to insert selection"
            ),
            "tooltip": (
                "Show autocomplete on 'Tab' press, 'Tab' or 'Enter' to insert selection"
            ),
            "func": None,
            "value": (
                settings.editor["autocompletion_type"]
                == settings.constants.AutocompletionType.Tab
            ),
        }
        output["editor"]["items"]["autocompletion_type_2"] = {
            "text": (
                "Show autocomplete list while typing, 'Tab' or 'Enter' to insert selection"
            ),
            "tooltip": (
                "Show autocomplete list while typing, 'Tab' or 'Enter' to insert selection"
            ),
            "func": None,
            "value": (
                settings.editor["autocompletion_type"]
                == settings.constants.AutocompletionType.Automatic
            ),
        }

        # Word wrapping
        def _word_wrapping_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_wordwrap_toggle(state)

        output["editor"]["items"]["word_wrapping_toggle"] = {
            "text": "Wrap lines at word boundary",
            "tooltip": "Toggle word wrapping on/off",
            "func": _word_wrapping_toggle,
            "value": settings.editor["word_wrap"],
        }

        # Edge marker
        def _edge_marker_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_edge_marker_toggle(state)

        output["editor"]["items"]["edge_marker_toggle"] = {
            "text": "Show edge marker",
            "tooltip": "Toggle edge marker visibility on/off",
            "func": _edge_marker_toggle,
            "value": settings.editor["edge_marker_visible"],
        }

        # Edge marker column
        def _edge_marker_column_change(textbox, new_value):
            try:
                number_value = int(new_value)
                if number_value < 1:
                    number_value = 1
                    textbox.setText(number_value)
                elif number_value > 5000:
                    number_value = 5000
                    textbox.setText(number_value)
                self.main_form.settings.manipulator.pmf_edge_marker_column_set(
                    number_value
                )
                textbox.old_value = str(number_value)
            except:
                #                traceback.print_exc()
                if new_value != "":
                    textbox.setText(textbox.old_value)

        output["editor"]["items"]["edge_marker_column"] = {
            "text": "Edge marker column: ",
            "tooltip": "Set the column of the edge marker",
            "func": _edge_marker_column_change,
            "value": settings.editor["edge_marker_column"],
        }

        # End of line
        def _end_of_line_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_end_of_line_toggle(state)

        output["editor"]["items"]["end_of_line_toggle"] = {
            "text": "Show end of line",
            "tooltip": "Toggle the end of line character visibility on/off",
            "func": _end_of_line_toggle,
            "value": settings.editor["end_of_line_visibility"],
        }

        # Cursor visibility
        def _cursor_line_visibility_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_cursor_line_visibility_toggle(
                state
            )

        output["editor"]["items"]["cursor_line_visibility_toggle"] = {
            "text": "Show cursor line",
            "tooltip": "Toggle cursor line visibility on/off",
            "func": _cursor_line_visibility_toggle,
            "value": settings.editor["cursor_line_visible"],
        }

        # Whitespace visibility
        def _whitespace_visible_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_whitespace_visible_toggle(
                state
            )

        output["editor"]["items"]["whitespace_visible"] = {
            "text": "Whitespace characters visible",
            "tooltip": (
                "Toggle the visibility of whitespace characters in all editors"
            ),
            "func": _whitespace_visible_toggle,
            "value": settings.editor["whitespace_visible"],
        }

        # Tabs use spaces
        def _tabs_use_spaces_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_tabs_use_spaces_toggle(
                state
            )

        output["editor"]["items"]["tabs_use_spaces"] = {
            "text": "Tabs are spaces",
            "tooltip": "Toggle if tabs use the space character or not",
            "func": _tabs_use_spaces_toggle,
            "value": settings.editor["tabs_use_spaces"],
        }

        # Makefile overrides the tabs-use-spaces option
        def _makefile_uses_tabs_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_makefile_uses_tabs_toggle(
                state
            )

        output["editor"]["items"]["makefile_uses_tabs"] = {
            "text": "Makefile uses tabs for indentation",
            "tooltip": "Toggle whether Makefiles use tabs for indentation",
            "func": _makefile_uses_tabs_toggle,
            "value": settings.editor["makefile_uses_tabs"],
        }

        # Makefile overrides the tabs-use-spaces option
        def _makefile_whitespace_visible_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_makefile_whitespace_visible_toggle(
                state
            )

        output["editor"]["items"]["makefile_whitespace_visible"] = {
            "text": "Makefile shows whitespace characters",
            "tooltip": "Toggle whether Makefiles shows whitespace characters",
            "func": _makefile_whitespace_visible_toggle,
            "value": settings.editor["makefile_whitespace_visible"],
        }

        # Tab width
        def _tab_width_change(textbox, new_value):
            try:
                number_value = int(new_value)
                if number_value < 1:
                    number_value = 1
                    textbox.setText(number_value)
                elif number_value > 100:
                    number_value = 100
                    textbox.setText(number_value)
                self.main_form.settings.manipulator.pmf_tab_width_set(
                    number_value
                )
                textbox.old_value = str(number_value)
            except:
                traceback.print_exc()
                if new_value != "":
                    textbox.setText(textbox.old_value)

        output["editor"]["items"]["tab_width"] = {
            "text": "Tab width: ",
            "tooltip": "Set the number of spaces the 'tab' key inserts",
            "func": _tab_width_change,
            "value": settings.editor["tab_width"],
        }

        ## Keyboard shortcuts
        output["keyboard-shortcuts"] = {
            "text": "Keyboard shortcuts:",
            "icon": "icons/gen/keyboard.png",
            "tooltip": "Customize keyboard shortcuts",
            "statustip": "Customize keyboard shortcuts",
            "items": {},
        }

        # General keys
        output["keyboard-shortcuts"]["items"]["general"] = {
            "parent": "keyboard_shortcuts",
            "text": "General shortcuts",
            "icon": "icons/gen/preferences.png",
            "tooltip": "Customize keyboard shortcuts",
            "statustip": "Customize keyboard shortcuts",
            "items": [],
        }
        for k, v in settings.keys["general"].items():
            if k in general_keys_for_editor:
                continue
            if isinstance(v, list):
                for i, item in enumerate(v):
                    output["keyboard-shortcuts"]["items"]["general"][
                        "items"
                    ].append(
                        {
                            "text": "{} {}: {}".format(k, i, item),
                            "id": None,
                            "icon": "icons/gen/keyboard-shortcut.png",
                            "data": {
                                "name": k,
                                "index": i,
                                "shortcut": item,
                                "table": "general",
                            },
                            "parent": "general_keys",
                            "tooltip": (
                                "Click to change shortcut for: '{} {}'".format(
                                    k, i
                                )
                            ),
                            "statustip": (
                                "Click to change shortcut for: '{} {}'".format(
                                    k, i
                                )
                            ),
                        }
                    )
            else:
                output["keyboard-shortcuts"]["items"]["general"][
                    "items"
                ].append(
                    {
                        "text": "{}: {}".format(k, v),
                        "id": None,
                        "icon": "icons/gen/keyboard-shortcut.png",
                        "data": {
                            "name": k,
                            "index": None,
                            "shortcut": v,
                            "table": "general",
                        },
                        "parent": "general_keys",
                        "tooltip": "Click to change shortcut for: '{}'".format(
                            k
                        ),
                        "statustip": (
                            "Click to change shortcut for: '{}'".format(k)
                        ),
                    }
                )

        # Editor keys
        output["keyboard-shortcuts"]["items"]["editor"] = {
            "parent": "keyboard_shortcuts",
            "text": "Editor shortcuts",
            "icon": "icons/menu_edit/edit.png",
            "tooltip": "Customize keyboard shortcuts",
            "statustip": "Customize keyboard shortcuts",
            "items": [],
        }
        settings_items = {}
        for k, v in settings.keys["editor"].items():
            settings_items[k] = "editor"
        for i in general_keys_for_editor:
            settings_items[i] = "general"
        for key in sorted(settings_items.keys()):
            k = key
            table = settings_items[key]
            v = settings.keys[table][key]
            output["keyboard-shortcuts"]["items"]["editor"]["items"].append(
                {
                    "text": "{}: {}".format(k, v),
                    "id": None,
                    "icon": "icons/gen/keyboard-shortcut.png",
                    "data": {
                        "name": k,
                        "index": None,
                        "shortcut": v,
                        "table": "editor",
                    },
                    "parent": "editor_keys",
                    "tooltip": "Click to change shortcut for: '{}'".format(k),
                    "statustip": "Click to change shortcut for: '{}'".format(k),
                }
            )

        self.finished.emit(output)


class SettingsWindow(gui.templates.treewidget.TreeWidget):
    ASYNC = True
    __leave_timer = None
    popup_cache: Optional[List[KeyboardShortcutPopup]] = None

    def __init__(self, parent, main_form):
        super().__init__(
            parent,
            main_form,
            "Preferences",
            iconfunctions.get_qicon("icons/gen/gear.png"),
        )
        # Initialize worker attributes
        self.__initialize_worker_stuff()
        # Update settings
        self.update_settings()
        #        self.__old_update_settings()
        # Connect to global signals
        data.signal_dispatcher.update_settings.connect(self.update_settings)

    def update_settings(self, *args, **kwargs):
        if self.ASYNC:
            if self.__thread is None and self.__worker is None:
                self.__thread = qt.QThread(self)
                self.__worker = SettingsWorker(self.main_form)
                self.__worker.moveToThread(self.__thread)
                self.__worker.finished.connect(self.__finished)
                self.__thread.finished.connect(self.__worker.deleteLater)
                self.__thread.start()
                qt.QTimer.singleShot(0, self.__worker.run)
        else:
            self.__update_settings_sync()

    def __initialize_worker_stuff(self):
        self.__thread = None
        self.__worker = None

    def __finished(self, output):
        self.__thread.exit()
        self.__thread.wait()
        self.__initialize_worker_stuff()
        self.__update_settings_async(output)

    def __update_settings_async(self, output):
        self.main_nodes = {}
        self.options = {}
        self.clear()
        self.setColumnCount(1)

        ## General
        general_node = self.add(
            text=output["general"]["text"],
            icon_path=output["general"]["icon"],
        )
        general_node.setExpanded(True)
        self.main_nodes["general"] = general_node

        # Ribbon style toolbar
        ribbon_style_toolbar_toggle = output["general"]["items"][
            "ribbon_style_toolbar_toggle"
        ]
        new_option = self.create_check_option(
            ribbon_style_toolbar_toggle["text"],
            ribbon_style_toolbar_toggle["tooltip"],
            ribbon_style_toolbar_toggle["func"],
            ribbon_style_toolbar_toggle["value"],
        )
        new_item = self.add(parent=general_node)
        self.setItemWidget(new_item, 0, new_option)

        # Scaling
        show_scaling = output["general"]["items"]["show_scaling"]
        new_option = self.create_button_option(
            show_scaling["text"],
            show_scaling["button-text"],
            show_scaling["tooltip"],
            show_scaling["func"],
            show_scaling["button-icon"],
        )
        new_item = self.add(parent=general_node)
        new_item.setFlags(new_item.flags() & ~qt.Qt.ItemFlag.ItemIsSelectable)
        self.setItemWidget(new_item, 0, new_option)

        ## Server
        server_node = self.add(
            text=output["server"]["text"],
            icon_path=output["server"]["icon"],
        )
        server_node.setExpanded(True)
        self.main_nodes["server"] = server_node

        # Used URL
        used_url = output["server"]["items"]["used-url"]
        new_option = self.add(
            text=f"Currently used server URL: '{serverfunctions.get_base_url_wfb()}'",
            tooltip=used_url["tooltip"],
            statustip=used_url["tooltip"],
            parent=server_node,
        )
        self.options["used-url"] = new_option

        # Base URL override
        def change_base_url_override(new_value: str) -> None:
            if new_value.lower() == "automatic":
                self.main_form.settings.manipulator.pmf_embeetle_base_url_override_set(
                    None
                )
            else:
                self.main_form.settings.manipulator.pmf_embeetle_base_url_override_set(
                    new_value
                )
            serverfunctions.store_url(
                base_url=None, base_url_override=new_value
            )
            return

        base_url_override = output["server"]["items"]["base-url-override"]
        new_option = self.create_combobox_option(
            base_url_override["text"],
            base_url_override["tooltip"],
            change_base_url_override,
            base_url_override["items"],
            initial_item=base_url_override["initial-item"],
        )
        new_item = self.add(parent=server_node)
        self.setItemWidget(new_item, 0, new_option)
        self.options["base-url-override"] = new_option

        ## Theme
        theme_node = self.add(
            text=output["theme"]["text"],
            icon_path=output["theme"]["icon"],
        )
        theme_node.setExpanded(True)
        self.main_nodes["theme"] = theme_node

        # Selected base theme
        theme_change = output["theme"]["items"]["base_theme_change"]
        new_option = self.create_advanced_combobox_option(
            theme_change["text"],
            theme_change["tooltip"],
            theme_change["func"],
            theme_change["acb-items"],
            theme_change["acb-no-items-text"],
            theme_change["acb-initial-item"],
        )
        new_item = self.add(parent=theme_node)
        self.setItemWidget(new_item, 0, new_option)

        # Refresh theme
        refresh_theme = output["theme"]["items"]["refresh"]
        new_option = self.create_button_option(
            refresh_theme["text"],
            refresh_theme["button-text"],
            refresh_theme["tooltip"],
            refresh_theme["func"],
            refresh_theme["button-icon"],
        )
        new_item = self.add(parent=theme_node)
        new_item.setFlags(new_item.flags() & ~qt.Qt.ItemFlag.ItemIsSelectable)
        self.setItemWidget(new_item, 0, new_option)

        ## Fonts
        def change_general_font(new_value):
            self.main_form.settings.manipulator.pmf_general_font_set(new_value)

        def editor_general_font(new_value):
            self.main_form.settings.manipulator.pmf_editor_font_set(new_value)

        fonts_node = self.add(
            text=output["fonts"]["text"],
            icon_path=output["fonts"]["icon"],
        )
        fonts_node.setExpanded(True)
        self.main_nodes["fonts"] = fonts_node
        # General font
        general_font = output["fonts"]["items"]["general-font"]
        new_option = self.create_combobox_option(
            general_font["text"],
            general_font["tooltip"],
            change_general_font,
            general_font["items"],
            initial_item=general_font["initial-item"],
        )
        new_item = self.add(parent=fonts_node)
        self.setItemWidget(new_item, 0, new_option)
        self.options["general-font"] = new_option

        # Editor font
        editor_font = output["fonts"]["items"]["editor-font"]
        new_option = self.create_combobox_option(
            editor_font["text"],
            editor_font["tooltip"],
            editor_general_font,
            editor_font["items"],
            initial_item=editor_font["initial-item"],
        )
        new_item = self.add(parent=fonts_node)
        self.setItemWidget(new_item, 0, new_option)
        self.options["editor-font"] = new_option

        ## Editor
        editor_node = self.add(
            text=output["editor"]["text"],
            icon_path=output["editor"]["icon"],
        )
        editor_node.setExpanded(True)
        self.main_nodes["editor"] = editor_node

        # Autocompletion functions
        def _autocompletion_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            for i, item in enumerate(self.autocompletion_items.items()):
                k, v = item
                groupbox = self.itemWidget(v, 0)
                groupbox.setEnabled(state)
                checkbox = groupbox.layout().itemAt(0).widget()
                if state == False:
                    checkbox.setChecked(False)
                else:
                    checkbox.setChecked(
                        settings.editor["autocompletion_type"] == i
                    )
            self.main_form.settings.manipulator.pmf_autocompletion_toggle(state)

        def _autocompletion_set_type(state):
            self.main_form.settings.manipulator.pmf_autocompletion_type_select(
                state
            )
            for i, item in enumerate(self.autocompletion_items.items()):
                k, v = item
                checkbox = self.itemWidget(v, 0).layout().itemAt(0).widget()
                checkbox.setChecked(settings.editor["autocompletion_type"] == i)

        # Autocompletion
        self.autocompletion_items = {}
        item = output["editor"]["items"]["autocompletion_toggle"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            _autocompletion_toggle,
            item["value"],
            label_click_toggles=False,
        )
        self.main_autocompletion_item = self.add(parent=editor_node)
        self.setItemWidget(self.main_autocompletion_item, 0, new_option)
        # Autocompletion types
        states = (
            settings.constants.AutocompletionType.CtrlPlusEnter,
            settings.constants.AutocompletionType.Tab,
            settings.constants.AutocompletionType.Automatic,
        )
        for state in states:
            item_name = f"autocompletion_type_{state}"
            item = output["editor"]["items"][item_name]
            new_option = self.create_check_option(
                item["text"],
                item["tooltip"],
                functools.partial(_autocompletion_set_type, state),
                item["value"]
                and output["editor"]["items"]["autocompletion_toggle"]["value"],
                style="round",
                checkbox_press_enabled=True,
            )
            new_item = self.add(parent=self.main_autocompletion_item)
            self.setItemWidget(new_item, 0, new_option)
            new_option.setEnabled(
                output["editor"]["items"]["autocompletion_toggle"]["value"]
            )
            self.autocompletion_items[item_name] = new_item
        self.main_autocompletion_item.setExpanded(True)

        # Word wrapping
        item = output["editor"]["items"]["word_wrapping_toggle"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Edge marker
        item = output["editor"]["items"]["edge_marker_toggle"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)
        # Edge marker column
        item = output["editor"]["items"]["edge_marker_column"]
        new_option = self.create_input_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # End of line
        item = output["editor"]["items"]["end_of_line_toggle"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Cursor line visibility
        item = output["editor"]["items"]["cursor_line_visibility_toggle"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Tab width
        item = output["editor"]["items"]["tab_width"]
        new_option = self.create_input_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Whitespace visible
        item = output["editor"]["items"]["whitespace_visible"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)
        checkbox_whitespace_visible = new_option.layout().itemAt(0).widget()

        def _whitespace_visible_update_check(*args):
            if settings.editor["whitespace_visible"]:
                checkbox_whitespace_visible.setCheckState(
                    qt.Qt.CheckState.Checked
                )
            else:
                checkbox_whitespace_visible.setCheckState(
                    qt.Qt.CheckState.Unchecked
                )

        data.signal_dispatcher.update_whitespace_visible.connect(
            _whitespace_visible_update_check
        )

        # Tabs use spaces
        item = output["editor"]["items"]["tabs_use_spaces"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)
        checkbox_tabs_use_spaces = new_option.layout().itemAt(0).widget()

        def _tabs_use_spaces_update_check(*args):
            if settings.editor["tabs_use_spaces"]:
                checkbox_tabs_use_spaces.setCheckState(qt.Qt.CheckState.Checked)
            else:
                checkbox_tabs_use_spaces.setCheckState(
                    qt.Qt.CheckState.Unchecked
                )

        data.signal_dispatcher.update_tabs_use_spaces.connect(
            _tabs_use_spaces_update_check
        )

        # Makefile uses tabs
        item = output["editor"]["items"]["makefile_uses_tabs"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Makefile whitespace visible
        item = output["editor"]["items"]["makefile_whitespace_visible"]
        new_option = self.create_check_option(
            item["text"],
            item["tooltip"],
            item["func"],
            item["value"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        ## Keyboard shortcuts
        # Shortcut change function
        self.popup_cache: Optional[List[KeyboardShortcutPopup]] = []

        def __clicked(*args):
            self.__close_all_popups()
            tree_node = args[0]
            node_data = tree_node.get_data()
            if isinstance(node_data, dict) and "shortcut" in node_data.keys():
                ksp = KeyboardShortcutPopup(
                    self.parent(),
                    node_data,
                    self,
                    tree_node,
                )
                self.popup_cache.append(ksp)
                ksp.popup()

        self.itemClicked.connect(__clicked)
        # Main shortcuts node
        item = output["keyboard-shortcuts"]
        keyboard_shortcuts = self.add(
            text=item["text"],
            icon_path=item["icon"],
            tooltip=item["tooltip"],
            statustip=item["statustip"],
        )
        keyboard_shortcuts.setExpanded(True)
        # General keys
        item = output["keyboard-shortcuts"]["items"]["general"]
        general_keys = self.add(
            parent=keyboard_shortcuts,
            text=item["text"],
            icon_path=item["icon"],
            tooltip=item["tooltip"],
            statustip=item["statustip"],
        )
        items = output["keyboard-shortcuts"]["items"]["general"]["items"]
        for i in items:
            i["parent"] = general_keys
        self.multi_add(items)

        # Editor keys
        item = output["keyboard-shortcuts"]["items"]["editor"]
        editor_keys = self.add(
            parent=keyboard_shortcuts,
            text=item["text"],
            icon_path=item["icon"],
            tooltip=item["tooltip"],
            statustip=item["statustip"],
        )
        items = output["keyboard-shortcuts"]["items"]["editor"]["items"]
        settings_items = {}
        for i in items:
            i["parent"] = editor_keys
        self.multi_add(items)

    def __update_settings_sync(self, *args, **kwargs):
        self.main_nodes = {}
        key_nodes = []
        self.clear()
        self.setColumnCount(1)

        ## General
        general_node = self.add(
            text="General:",
            icon_path="icons/gen/gear.png",
        )
        general_node.setExpanded(True)
        self.main_nodes["general"] = general_node

        # Ribbon style toolbar
        def _ribbon_style_toolbar_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_ribbon_style_toolbar_toggle(
                state
            )

        tooltip = "Toggle big toolbar style"
        new_option = self.create_check_option(
            "Big toolbar",
            tooltip,
            _ribbon_style_toolbar_toggle,
            data.ribbon_style_toolbar,
        )
        new_item = self.add(parent=general_node)
        self.setItemWidget(new_item, 0, new_option)

        # Scaling
        def _show_scaling():
            self.main_form.display.dialog_show("scaling_dialog")

        tooltip = "Show the scaling dialog to adjust Embeetle's visual style"
        new_option = self.create_button_option(
            "Scaling dialog",
            "SHOW",
            tooltip,
            _show_scaling,
            "icons/menu_view/zoom.png",
        )
        new_item = self.add(parent=general_node)
        new_item.setFlags(new_item.flags() & ~qt.Qt.ItemFlag.ItemIsSelectable)
        self.setItemWidget(new_item, 0, new_option)

        ## Theme
        theme_node = self.add(
            text="Theme:",
            icon_path="icons/theme/themes.png",
        )
        theme_node.setExpanded(True)
        self.main_nodes["theme"] = theme_node

        # Selected theme
        def _theme_change(combobox, new_value, new_item):
            if data.theme["name"] != new_value:
                self.main_form.settings.manipulator.pmf_theme_set(new_value)

        tooltip = "Embeetle theme, used for styling all widgets"
        theme_list = themes.get_all()
        acb_items = []
        initial_item = None
        for t in sorted(theme_list, key=lambda x: x["name"]):
            new_item = {
                "name": t["name"],
                "widgets": (
                    {"type": "image", "icon-path": t["image_file"]},
                    {"type": "text", "text": t["name"]},
                ),
            }
            acb_items.append(new_item)
            if new_item["name"].lower() == data.theme["name"].lower():
                initial_item = new_item
        new_option = self.create_advanced_combobox_option(
            "Current theme: ",
            tooltip,
            _theme_change,
            acb_items,
            "No theme found!",
            initial_item,
            #            extra_button={
            #                "name": "refresh_theme",
            #                "tooltip": "Refresh the current theme",
            #                "icon": "icons/dialog/refresh.png",
            #                "function": refresh_func,
            #            },
        )
        new_item = self.add(parent=theme_node)
        self.setItemWidget(new_item, 0, new_option)

        # Refresh theme
        def refresh_func(*args):
            self.main_form.settings.manipulator.pmf_theme_set(
                data.theme["name"]
            )

        new_option = self.create_button_option(
            "Refresh theme",
            "REFRESH",
            "Refresh the current theme",
            refresh_func,
            "icons/dialog/refresh.png",
        )
        new_item = self.add(parent=theme_node)
        new_item.setFlags(new_item.flags() & ~qt.Qt.ItemFlag.ItemIsSelectable)
        self.setItemWidget(new_item, 0, new_option)

        ## Editor
        editor_node = self.add(
            text="Editor:",
            icon_path="icons/menu_edit/edit.png",
        )
        editor_node.setExpanded(True)
        self.main_nodes["editor"] = editor_node

        # Autocompletion
        def _autocompletion_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_autocompletion_toggle(state)

        tooltip = "Toggle autocompletions on/off"
        new_option = self.create_check_option(
            "Enable autocompletion",
            tooltip,
            _autocompletion_toggle,
            settings.editor["autocompletion"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Word wrapping
        def _word_wrapping_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_wordwrap_toggle(state)

        tooltip = "Toggle word wrapping on/off"
        new_option = self.create_check_option(
            "Wrap lines at word boundary",
            tooltip,
            _word_wrapping_toggle,
            settings.editor["word_wrap"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Edge marker
        def _edge_marker_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_edge_marker_toggle(state)

        tooltip = "Toggle edge marker visibility on/off"
        new_option = self.create_check_option(
            "Show edge marker",
            tooltip,
            _edge_marker_toggle,
            settings.editor["edge_marker_visible"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # End of line
        def _end_of_line_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_end_of_line_toggle(state)

        tooltip = "Toggle the end of line character visibility on/off"
        new_option = self.create_check_option(
            "Show end of line",
            tooltip,
            _end_of_line_toggle,
            settings.editor["end_of_line_visibility"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # End of line
        def _cursor_line_visibility_toggle(check_state):
            state = False
            if qt.Qt.CheckState(check_state) == qt.Qt.CheckState.Checked:
                state = True
            self.main_form.settings.manipulator.pmf_cursor_line_visibility_toggle(
                state
            )

        tooltip = "Toggle cursor line visibility on/off"
        new_option = self.create_check_option(
            "Show cursor line",
            tooltip,
            _cursor_line_visibility_toggle,
            settings.editor["cursor_line_visible"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        # Tab width
        def _tab_width_change(textbox, new_value):
            try:
                number_value = int(new_value)
                if number_value < 1:
                    number_value = 1
                    textbox.setText(number_value)
                elif number_value > 100:
                    number_value = 100
                    textbox.setText(number_value)
                self.main_form.settings.manipulator.pmf_tab_width_set(
                    number_value
                )
                textbox.old_value = str(number_value)
            except:
                traceback.print_exc()
                if new_value != "":
                    textbox.setText(textbox.old_value)

        tooltip = "Set the number of spaces the 'tab' key inserts"
        new_option = self.create_input_option(
            "Tab width: ",
            tooltip,
            _tab_width_change,
            settings.editor["tab_width"],
        )
        new_item = self.add(parent=editor_node)
        self.setItemWidget(new_item, 0, new_option)

        ## Keyboard shortcuts
        # Shortcut change function
        self.popup_cache: Optional[List[KeyboardShortcutPopup]] = []

        def __clicked(*args):
            self.__close_all_popups()
            tree_node = args[0]
            node_data = tree_node.get_data()
            if isinstance(node_data, dict) and "shortcut" in node_data.keys():
                ksp = KeyboardShortcutPopup(
                    self.parent(),
                    node_data,
                    self,
                    tree_node,
                )
                self.popup_cache.append(ksp)
                ksp.popup()

        self.itemClicked.connect(__clicked)
        # Main shortcuts node
        keyboard_shortcuts = self.add(
            text="Keyboard shortcuts",
            icon_path="icons/gen/keyboard.png",
            tooltip="Customize keyboard shortcuts",
            statustip="Customize keyboard shortcuts",
        )
        keyboard_shortcuts.setExpanded(True)
        # General keys
        general_keys = self.add(
            text="General shortcuts",
            parent=keyboard_shortcuts,
            icon_path="icons/gen/preferences.png",
            tooltip="Customize keyboard shortcuts",
            statustip="Customize keyboard shortcuts",
        )
        key_nodes.append(general_keys)
        items = []
        for k, v in settings.keys["general"].items():
            if k in general_keys_for_editor:
                continue
            if isinstance(v, list):
                for i, item in enumerate(v):
                    items.append(
                        {
                            "text": "{} {}: {}".format(k, i, item),
                            "id": None,
                            "icon": "icons/gen/keyboard-shortcut.png",
                            "data": {
                                "name": k,
                                "index": i,
                                "shortcut": item,
                                "table": "general",
                            },
                            "parent": general_keys,
                            "tooltip": (
                                "Click to change shortcut for: '{} {}'".format(
                                    k, i
                                )
                            ),
                            "statustip": (
                                "Click to change shortcut for: '{} {}'".format(
                                    k, i
                                )
                            ),
                        }
                    )
            else:
                items.append(
                    {
                        "text": "{}: {}".format(k, v),
                        "id": None,
                        "icon": "icons/gen/keyboard-shortcut.png",
                        "data": {
                            "name": k,
                            "index": None,
                            "shortcut": v,
                            "table": "general",
                        },
                        "parent": general_keys,
                        "tooltip": "Click to change shortcut for: '{}'".format(
                            k
                        ),
                        "statustip": (
                            "Click to change shortcut for: '{}'".format(k)
                        ),
                    }
                )
        self.multi_add(items)

        # Editor keys
        editor_keys = self.add(
            text="Editor shortcuts",
            parent=keyboard_shortcuts,
            icon_path="icons/menu_edit/edit.png",
            tooltip="Customize keyboard shortcuts",
            statustip="Customize keyboard shortcuts",
        )
        key_nodes.append(editor_keys)
        items = []
        settings_items = {}
        for k, v in settings.keys["editor"].items():
            settings_items[k] = "editor"
        for i in general_keys_for_editor:
            settings_items[i] = "general"
        for key in sorted(settings_items.keys()):
            k = key
            table = settings_items[key]
            v = settings.keys[table][key]
            items.append(
                {
                    "text": "{}: {}".format(k, v),
                    "id": None,
                    "icon": "icons/gen/keyboard-shortcut.png",
                    "data": {
                        "name": k,
                        "index": None,
                        "shortcut": v,
                        "table": "editor",
                    },
                    "parent": editor_keys,
                    "tooltip": "Click to change shortcut for: '{}'".format(k),
                    "statustip": "Click to change shortcut for: '{}'".format(k),
                }
            )
        self.multi_add(items)

    def create_input_option(self, text, tooltip, function, initial_value):
        gb = self.create_groupbox()
        # Layout reference
        layout = gb.layout()
        # Label
        label = self.create_label(text, tooltip)
        label.set_colors(
            background_color="transparent",
        )
        layout.addWidget(label)
        layout.setAlignment(
            label,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Textbox
        textbox = gui.templates.widgetgenerator.create_textbox(
            "input-option", parent=gb, no_border=True
        )
        textbox.setText(str(initial_value))
        textbox.old_value = str(initial_value)
        textbox.setToolTip(tooltip)
        textbox.setStatusTip(tooltip)
        if function is not None:
            wrapped_func = functools.partial(function, textbox)
            textbox.textChanged.connect(wrapped_func)
        layout.addWidget(textbox)
        layout.setAlignment(
            textbox,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Stretch to fill empty space
        self.add_spacing(layout)

        # Updating the style
        def update_style():
            label.update_style()
            textbox.update_style()

        gb.update_style = update_style
        return gb

    def create_check_option(
        self,
        text,
        tooltip,
        function,
        initial_state,
        style=None,
        label_click_toggles=True,
        checkbox_press_enabled=False,
    ):
        gb = self.create_groupbox()
        # Layout reference
        layout = gb.layout()
        layout.setSpacing(6)
        # Checkbox
        checkbox = gui.templates.widgetgenerator.create_standard_checkbox(
            gb, text, style=style
        )
        checkbox.setToolTip(tooltip)
        checkbox.setStatusTip(tooltip)
        checkbox.setChecked(initial_state)
        if checkbox_press_enabled:
            checkbox.released.connect(function)
        else:
            checkbox.stateChanged.connect(function)
        layout.addWidget(checkbox)
        layout.setAlignment(
            checkbox,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Label
        label = self.create_label(text, tooltip)
        label.set_colors(
            background_color="transparent",
        )
        if label_click_toggles:

            def toggle_check(*args):
                if checkbox_press_enabled:
                    checkbox.released.emit()
                else:
                    checkbox.toggle()

            label.click_signal.connect(toggle_check)
        layout.addWidget(label)
        layout.setAlignment(
            label,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Stretch to fill empty space
        self.add_spacing(layout)

        # Updating the style
        def update_style():
            checkbox.update_style()
            label.update_style()

        gb.update_style = update_style
        return gb

    def create_combobox_option(
        self,
        text,
        tooltip,
        function,
        initial_list,
        initial_item=None,
        extra_button=None,
    ):
        gb = self.create_groupbox()
        # Layout reference
        layout = gb.layout()
        # Label
        label = self.create_label(text, tooltip)
        label.set_colors(
            background_color="transparent",
        )
        layout.addWidget(label)
        layout.setAlignment(
            label,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Combobox
        combobox = gui.templates.widgetgenerator.create_combobox(parent=self)
        combobox.addItems(initial_list)
        combobox.setToolTip(tooltip)
        combobox.setStatusTip(tooltip)
        combobox.setSizeAdjustPolicy(
            qt.QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        combobox.setSizePolicy(
            qt.QSizePolicy.Policy.Maximum,
            qt.QSizePolicy.Policy.Maximum,
        )
        combobox.setEditable(False)
        if initial_item is not None:
            combobox.setCurrentText(initial_item)
        if function is not None:
            combobox.currentTextChanged.connect(function)
        layout.addWidget(combobox)
        layout.setAlignment(
            combobox,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Extra button
        if extra_button is not None:
            button = gui.templates.widgetgenerator.create_pushbutton(
                parent=gb,
                name=extra_button["name"],
                tooltip=extra_button["tooltip"],
                icon_name=extra_button["icon"],
                size=(
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                ),
                click_func=extra_button["function"],
            )
            button.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Minimum,
            )
            layout.addWidget(button)
            layout.setAlignment(
                button,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
        # Stretch to fill empty space
        self.add_spacing(layout)

        # Updating the style
        def update_style():
            if not qt.sip.isdeleted(label):
                label.update_style()
            if not qt.sip.isdeleted(combobox):
                combobox.update_style()
            if extra_button is not None:
                button.update_style(
                    new_size=(
                        data.get_general_icon_pixelsize(),
                        data.get_general_icon_pixelsize(),
                    )
                )

        gb.update_style = update_style
        return gb

    def create_advanced_combobox_option(
        self,
        text,
        tooltip,
        function,
        initial_list,
        no_selection_text,
        initial_item,
        extra_button=None,
    ):
        gb = self.create_groupbox()
        # Layout reference
        layout = gb.layout()
        # Label
        label = self.create_label(text, tooltip)
        label.set_colors(
            background_color="transparent",
        )
        layout.addWidget(label)
        layout.setAlignment(
            label,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Combobox
        acb = gui.helpers.advancedcombobox.AdvancedComboBox(
            parent=self,
            contents_margins=(0, 0, 0, 0),
            spacing=2,
            no_selection_text=no_selection_text,
            initial_items=initial_list,
            initial_item=initial_item,
        )
        acb.setToolTip(tooltip)
        acb.setStatusTip(tooltip)
        if function is not None:
            wrapped_func = functools.partial(function, acb)
            acb.selection_changed.connect(wrapped_func)
        layout.addWidget(acb)
        layout.setAlignment(
            acb,
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        # Extra button
        if extra_button is not None:
            button = gui.templates.widgetgenerator.create_pushbutton(
                parent=gb,
                name=extra_button["name"],
                tooltip=extra_button["tooltip"],
                icon_name=extra_button["icon"],
                size=(
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                ),
                click_func=extra_button["function"],
            )
            button.setSizePolicy(
                qt.QSizePolicy.Policy.Minimum,
                qt.QSizePolicy.Policy.Minimum,
            )
            layout.addWidget(button)
            layout.setAlignment(
                button,
                qt.Qt.AlignmentFlag.AlignHCenter
                | qt.Qt.AlignmentFlag.AlignVCenter,
            )
        # Stretch to fill empty space
        self.add_spacing(layout)

        # Updating the style
        def update_style():
            if not qt.sip.isdeleted(label):
                label.update_style()
            if not qt.sip.isdeleted(acb):
                acb.update_style()
            if extra_button is not None:
                button.update_style(
                    new_size=(
                        data.get_general_icon_pixelsize(),
                        data.get_general_icon_pixelsize(),
                    )
                )

        gb.update_style = update_style
        return gb

    def __close_all_popups(self, *args):
        for popup in self.popup_cache:
            popup.self_destruct()
        self.popup_cache = []

    def leave_timer_start(self):
        if self.__leave_timer is not None:
            try:
                self.__leave_timer.timeout.disconnect()
            except:
                traceback.print_exc()
            self.__leave_timer.setParent(None)
            self.__leave_timer = None
        self.__leave_timer = qt.QTimer(self)
        self.__leave_timer.setInterval(3000)
        self.__leave_timer.setSingleShot(True)
        self.__leave_timer.timeout.connect(self.__close_all_popups)
        self.__leave_timer.start()

    def leave_timer_stop(self):
        if self.__leave_timer is not None:
            self.__leave_timer.stop()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.leave_timer_start()

    def enterEvent(self, e):
        super().enterEvent(e)
        self.leave_timer_stop()

    def keyReleaseEvent(self, e):
        super().keyReleaseEvent(e)
        if e.key() == qt.Qt.Key.Key_Escape:
            self.__close_all_popups()

    def get_rightclick_menu_function(self):
        return None


class KeyboardShortcutPopup(qt.QGroupBox):
    __size = (300, 60)
    __name = None
    __shortcut = None
    __node_data = None
    __settings_window = None
    __settings_item = None

    def self_destruct(self, *args) -> None:
        """"""
        if not qt.sip.isdeleted(self):
            self.__name = None
            self.__shortcut = None
            self.__node_data = None
            self.__settings_window = None
            self.__settings_item = None
            self.textbox = None
            self.setParent(None)  # noqa
            self.deleteLater()
        return

    def __init__(self, parent, node_data, settings_window, settings_item):
        super().__init__(parent)
        self.__name = node_data["name"]
        self.__shortcut = node_data["shortcut"]
        self.__node_data = node_data
        self.__settings_window = settings_window
        self.__settings_item = settings_item

        self.setStyleSheet(
            f"""
            background-color: {data.theme["general_background"]};
            border: 1px solid {data.theme["button_border"]};
        """
        )
        self.setFixedSize(
            qt.create_qsize(
                self.__size[0] * data.get_global_scale(),
                self.__size[1] * data.get_global_scale(),
            )
        )
        self.__init_widgets()

    def __init_widgets(self):
        # Layout
        layout: qt.QVBoxLayout = cast(
            qt.QVBoxLayout,
            gui.templates.widgetgenerator.create_layout(vertical=True),
        )
        self.setLayout(layout)
        ## Title & close button
        # Groupbox
        title_gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
            name="input-groupbox",
            vertical=False,
            borderless=True,
        )
        title_layout = title_gb.layout()
        # Label
        if self.__node_data["index"] is not None:
            title_text = "Keyboard shortcut: <b>{} ({})</b>".format(
                self.__name,
                self.__node_data["index"],
            )
        else:
            title_text = "Keyboard shortcut: <b>{}</b>".format(self.__name)
        title = gui.templates.widgetgenerator.create_label(
            text=title_text,
            alignment=qt.Qt.AlignmentFlag.AlignCenter
            | qt.Qt.AlignmentFlag.AlignVCenter,
            tooltip="Shows the current shortcut name",
            statustip="Shows the current shortcut name",
        )
        title.set_colors(
            background_color=data.theme["shade"][10],
        )
        title_layout.addWidget(title)
        # Close button
        close_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="close_button",
            tooltip="Close this popup",
            icon_name="icons/tab/close.png",
            size=(
                data.get_custom_tab_pixelsize(),
                data.get_custom_tab_pixelsize(),
            ),
            style="border",
            statustip="Close this popup",
            click_func=self.self_destruct,
        )
        close_button.setMinimumSize(0, 0)
        close_button.setMaximumSize(500, 500)
        close_button.setFixedWidth(data.get_custom_tab_pixelsize())
        close_button.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed,
            qt.QSizePolicy.Policy.Expanding,
        )
        title_layout.addWidget(close_button)
        # Add to main layout
        layout.addWidget(title_gb)

        ## Current value
        current_value = gui.templates.widgetgenerator.create_label(
            text="Current keys: <b>{}</b>".format(str(self.__shortcut)),
            alignment=qt.Qt.AlignmentFlag.AlignCenter
            | qt.Qt.AlignmentFlag.AlignVCenter,
            tooltip="Shows the current shortcut keys",
            statustip="Shows the current shortcut keys",
        )
        current_value.set_colors(
            background_color="transparent",
        )
        layout.addWidget(current_value)

        ## Input field & change button
        # Groupbox
        input_gb = gui.templates.widgetgenerator.create_groupbox_with_layout(
            name="input-groupbox",
            vertical=False,
            borderless=True,
            spacing=1,
        )
        input_layout = input_gb.layout()
        # Input field
        textbox = gui.templates.widgetgenerator.create_textbox(
            "shortcut-input", parent=input_gb, no_border=True
        )
        textbox.setAlignment(
            qt.Qt.AlignmentFlag.AlignCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        textbox.setText(str(self.__shortcut))
        textbox.setToolTip("Enter new key combination here")
        textbox.setStatusTip("Enter new key combination here")
        textbox.returnPressed.connect(self.__change_shortcut)
        input_layout.addWidget(textbox)
        self.textbox = textbox
        # Change button
        change_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self,
            name="change_button",
            tooltip="Change the '{}' shortcut keys".format(self.__shortcut),
            size=(
                data.get_custom_tab_pixelsize() * 4,
                data.get_custom_tab_pixelsize(),
            ),
            text="Change",
            style="border",
            statustip="Change the shortcut to what was entered",
            click_func=self.__change_shortcut,
        )
        change_button.setMinimumSize(0, 0)
        change_button.setMaximumSize(500, 500)
        change_button.setFixedWidth(data.get_custom_tab_pixelsize() * 4)
        change_button.setSizePolicy(
            qt.QSizePolicy.Policy.Fixed,
            qt.QSizePolicy.Policy.Expanding,
        )
        input_layout.addWidget(change_button)
        # Add to main layout
        layout.addWidget(input_gb)

        # Fill remaining space

    #        layout.addStretch()

    def __change_shortcut(self, *args):
        new_shortcut = self.textbox.text()
        valid_shortcut = settings.check_shortcut_combination(new_shortcut)
        if valid_shortcut is not None:
            #            print(self.__node_data)
            #            print(valid_shortcut)
            new_shortcut = "+".join(valid_shortcut)
            # Update the settings option
            table = self.__node_data["table"]
            name = self.__node_data["name"]
            if self.__node_data["index"] is not None:
                index = self.__node_data["index"]
                settings.keys[table][name][index] = new_shortcut
            else:
                settings.keys[table][name] = new_shortcut
            if table == "editor" and name in general_keys_for_editor:
                settings.keys["general"][name] = new_shortcut
            # Save the settings
            self.__settings_window.main_form.settings.save()
            # Update the settings window item text
            name = self.__node_data["name"]
            if self.__node_data["index"] is not None:
                name = "{} {}".format(
                    self.__node_data["name"],
                    self.__node_data["index"],
                )
            new_text = "{}: {}".format(name, new_shortcut)
            self.__settings_item.setText(0, new_text)
            node_data = self.__settings_item.get_data()
            node_data["shortcut"] = new_shortcut
            # Update the shortcuts on the main window
            data.main_form.reassign_shortcuts(update_preferences_window=False)
            data.main_form.send("reassign-shortcuts")
        else:
            msg = "Invalid key combinatin: {}".format(new_shortcut)
            data.main_form.display.write_to_statusbar(msg, 5000)
            data.signal_dispatcher.notify_error.emit(
                "Invalid key combinatin: {}".format(new_shortcut)
            )
        self.self_destruct()

    def enterEvent(self, e):
        super().enterEvent(e)
        self.__settings_window.leave_timer_stop()

    def popup(self):
        cursor = qt.QCursor.pos()
        position = self.mapToGlobal(self.pos())
        move_position = cursor - position
        if (move_position.x() + self.width()) > self.parent().width():
            #            print("overflow-x", (move_position.x() + self.width()), self.parent().width())
            x_offset = (
                move_position.x() + self.width()
            ) - self.parent().width()
            move_position.setX(move_position.x() - x_offset)
        if (move_position.y() + self.height()) > self.parent().height():
            #            print("overflow-y", (move_position.y() + self.height()), self.parent().height())
            y_offset = (
                move_position.y() + self.height()
            ) - self.parent().height()
            move_position.setY(move_position.y() - y_offset)
        self.move(move_position)
        self.show()
