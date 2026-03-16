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

import qt
import data
import purefunctions


class TheSquid:
    """The static object for executing functions that encompass multiple
    objects."""

    home_form = None
    main_form = None
    windows = None
    modules = None
    """
    Project window
    """

    @staticmethod
    def init_objects(main_form):
        TheSquid.main_form = main_form
        TheSquid.update_objects()

    @staticmethod
    def update_objects():
        TheSquid.modules = {
            "customeditor": purefunctions.import_module(
                "gui.forms.customeditor"
            ),
            "plaineditor": purefunctions.import_module("gui.forms.plaineditor"),
            "homewindow": purefunctions.import_module("gui.forms.homewindow"),
            "tabwidget": purefunctions.import_module("gui.forms.tabwidget"),
            "baseprogressbar": purefunctions.import_module(
                "gui.templates.baseprogressbar"
            ),
            "treedisplaybase": purefunctions.import_module(
                "gui.templates.treedisplaybase"
            ),
            "simplecombobox": purefunctions.import_module(
                "gui.helpers.simplecombobox"
            ),
        }
        TheSquid.windows = TheSquid.main_form.findChildren(
            TheSquid.modules["tabwidget"].TabWidget
        )

    @staticmethod
    def update_options_on_all_editors():
        if TheSquid.main_form is None or isinstance(
            TheSquid.main_form, TheSquid.modules["homewindow"].HomeWindow
        ):
            return

        def apply_to_editors(window):
            for i in range(window.count()):
                widget = window.widget(i)
                if isinstance(
                    widget, TheSquid.modules["customeditor"].CustomEditor
                ):
                    widget.update_variable_settings()
                if isinstance(
                    widget, TheSquid.modules["plaineditor"].PlainEditor
                ):
                    widget.update_variable_settings()

        TheSquid.update_objects()
        for w in TheSquid.windows:
            apply_to_editors(w)
        TheSquid.main_form.display.messages_window.update_variable_settings()
        TheSquid.main_form.settings.save(restyle=False)

    @staticmethod
    def update_styles():
        if TheSquid.main_form is None:
            return

        TheSquid.update_objects()
        # Stylesheet
        TheSquid.main_form.view.reset_entire_style_sheet()
        # Window and menubar menus
        for k, v in TheSquid.main_form.menubar.stored_menus.items():
            if hasattr(v, "update_style"):
                v.update_style()
        for k, v in TheSquid.main_form.stored_menus.items():
            if hasattr(v, "update_style"):
                v.update_style()
        # Messages box
        if TheSquid.main_form.display.messages_window:
            TheSquid.main_form.display.messages_window.update_variable_settings()
        # Toolbar
        TheSquid.main_form.update_toolbar_style()
        # Statusbar
        TheSquid.main_form.update_statusbar_style()
        # All boxes
        for box in TheSquid.main_form.get_all_boxes():
            box.update_style()
        # All progressbars
        for pb in TheSquid.modules[
            "baseprogressbar"
        ].BaseProgressBar.get_ref_iter():
            if pb is not None:
                pb.restyle()
        # All comboboxes
        comboboxes = TheSquid.main_form.findChildren(
            TheSquid.modules["simplecombobox"].SimpleComboBox
        )
        for cb in comboboxes:
            cb.update_style()

        # Tab windows updates
        windows = TheSquid.main_form.get_all_windows()
        if hasattr(TheSquid.main_form, "popup_tabs"):
            windows.append(TheSquid.main_form.popup_tabs)
        for window in windows:
            window.update_style()

            for i in range(window.count()):
                subwindow = window.widget(i)

                if hasattr(subwindow, "corner_widget"):
                    if hasattr(subwindow.corner_widget, "update_style"):
                        subwindow.corner_widget.update_style()
                    if data.get_custom_tab_pixelsize() is not None:
                        subwindow.corner_widget.setIconSize(
                            qt.create_qsize(
                                data.get_custom_tab_pixelsize(),  # @Kristof
                                data.get_custom_tab_pixelsize(),  # @Kristof
                            )
                        )
                    else:
                        subwindow.corner_widget.setIconSize(
                            qt.create_qsize(16, 16)
                        )

                if hasattr(subwindow, "icon_manipulator"):
                    subwindow.icon_manipulator.restyle_corner_button_icons()

                if hasattr(subwindow, "update_style"):
                    subwindow.update_style()

                if issubclass(
                    subwindow.__class__,
                    TheSquid.modules["treedisplaybase"].TreeDisplayBase,
                ):
                    subwindow.update_icon_size()
                    subwindow.customize_context_menu()

                if hasattr(subwindow, "chassis_rescale_or_refresh_recursive"):
                    subwindow.chassis_rescale_or_refresh_recursive(
                        action="refresh",
                        force_stylesheet=True,
                        callback=None,
                        callbackArg=None,
                    )
                    continue

                if hasattr(subwindow, "rescale_later"):
                    subwindow.rescale_later(
                        callback=None,
                        callbackArg=None,
                    )
                    continue

                if isinstance(
                    subwindow, TheSquid.modules["customeditor"].CustomEditor
                ) or isinstance(
                    subwindow, TheSquid.modules["plaineditor"].PlainEditor
                ):
                    subwindow.set_style()
                    subwindow.refresh_lexer()
                    subwindow.update_variable_settings()

        # All actions
        TheSquid.main_form.update_actions()

        return

    """
    Home window
    """

    @staticmethod
    def init_home_form(home_form):
        TheSquid.home_form = home_form

    @staticmethod
    def update_home_form():
        home_form = TheSquid.home_form
        if home_form is None:
            return

        home_form.view.set_style_sheet()
        home_form.update_statusbar_style()
        for k in home_form.menubar.stored_menus.keys():
            home_form.menubar.stored_menus[k].update_style()

        home_form.view.update_style(adjust=False)

        home_form.statusbar.setStyleSheet(
            "color: {0};".format(data.theme["fonts"]["default"]["color"])
        )

        # Update all other styling
        home_form.update_custom_styles()

        # Kristof's widgets
        if data.libman_widg is not None:
            data.libman_widg.chassis_rescale_or_refresh_recursive(
                "refresh", True, None, None
            )
        if data.toolbox_widg is not None:
            data.toolbox_widg.chassis_rescale_or_refresh_recursive(
                "refresh", True, None, None
            )

    """
    General functions
    """

    @staticmethod
    def self_destruct() -> None:
        """"""
        return

    @staticmethod
    def update_all():
        TheSquid.update_styles()
        TheSquid.update_home_form()
