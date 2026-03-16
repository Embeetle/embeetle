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
import qt
import data
import functions
import iconfunctions
import gui.dialogs.popupdialog
import gui.templates.basemenu
import gui.templates.treewidget
import components.diagnostics
import source_analyzer
import gui.stylesheets.groupbox
import gui.stylesheets.scrollbar
import functools
import webbrowser
import traceback
import urllib.parse
import helpdocs.help_texts


class DiagnosticWindow(gui.templates.treewidget.TreeWidget):
    diagnostics: components.diagnostics.Diagnostics = None
    severity_icons = {
        source_analyzer.Severity.WARNING: {
            "empty": "icons/dialog/warning.png",
            "expanded": "icons/dialog/warning.png",
            "closed": "icons/dialog/warning.png",
        },
        source_analyzer.Severity.ERROR: {
            "empty": "icons/dialog/fatal.png",
            "expanded": "icons/dialog/fatal.png",
            "closed": "icons/dialog/fatal.png",
        },
        source_analyzer.Severity.FATAL: {
            "empty": "icons/dialog/warning_red.svg",
            "expanded": "icons/dialog/warning_red.svg",
            "closed": "icons/dialog/warning_red.svg",
        },
    }
    severity_name = {
        source_analyzer.Severity.WARNING: "Warning",
        source_analyzer.Severity.ERROR: "Error",
        source_analyzer.Severity.FATAL: "Fatal",
    }

    def __init__(self, parent, main_form, diagnostics):
        super().__init__(
            parent,
            main_form,
            "Diagnostics",
            iconfunctions.get_qicon("icons/gen/stethoscope.png"),
        )

        if diagnostics is not None:
            self.add_diagnostics(diagnostics)

        self._adding = False
        self.main_nodes = {}

        self.setSortingEnabled(False)

        for it in reversed(source_analyzer.Severity):
            self.main_nodes[it] = self.add(
                it.name.title(),
                _id=it.value - 1000,
                icon_path=self.severity_icons[it]["empty"],
            )
            self.main_nodes[it].original_text = it.name.title()
            if it == source_analyzer.Severity.FATAL:
                self.main_nodes[it].setHidden(True)

        self.update_style()

    def add_diagnostics(self, diagnostics):
        if self.diagnostics is not None:
            try:
                self.diagnostics.message_added_signal.disconnect()
                self.diagnostics.message_bulk_add_signal.disconnect()
                self.diagnostics.message_removed_signal.disconnect()
                self.diagnostics.message_bulk_remove_signal.disconnect()
                self.diagnostics.message_available_signal.disconnect()
                self.diagnostics = None
            except:
                traceback.print_exc()
        # Connect the diagnostics signals
        diagnostics.message_added_signal.connect(self.message_added)
        diagnostics.message_bulk_add_signal.connect(self.message_bulk_added)
        diagnostics.message_removed_signal.connect(self.message_removed)
        diagnostics.message_bulk_remove_signal.connect(
            self.message_bulk_removed
        )
        diagnostics.message_available_signal.connect(
            self.more_messages_available
        )
        self.diagnostics = diagnostics

    def __get_message_text(self, message) -> None:
        diagnostic_text = ""
        if message.path:
            filename = os.path.basename(message.path)
            diagnostic_text = f"{message.message} ({filename})"
        else:
            diagnostic_text = f"{message.message}"
        return diagnostic_text

    @qt.pyqtSlot(object)
    def message_bulk_added(self, messages):
        # Functions
        def create_menu(msg):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Open file
            if msg.path is not None and msg.offset is not None:

                def open_file():
                    file_path = functions.unixify_path(msg.path)
                    self.main_form.open_file(file_path)
                    main = self.main_form
                    tab = main.get_tab_by_save_name(file_path)
                    if tab is not None:
                        tab.goto_index(msg.offset)

                action_open = qt.QAction(
                    f"Go to '{self.severity_name[severity]}'", menu
                )
                action_open.setStatusTip(
                    "Open the file in an editor and move to the line "
                    + f"where the '{self.severity_name[severity]}' "
                    + "is located"
                )
                action_open.setIcon(
                    iconfunctions.get_qicon("icons/menu_edit/goto.png")
                )
                action_open.triggered.connect(open_file)
                menu.addAction(action_open)

            # Copy diagnostic to clipboard
            def clipboard_copy():
                text = self.__get_message_text(msg)
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(text, mode=cb.Mode.Clipboard)

            action_copy = qt.QAction("Copy message to clipboard", menu)
            action_copy.setStatusTip("Copy message to clipboard")
            action_copy.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/paste.png")
            )
            action_copy.triggered.connect(clipboard_copy)
            menu.addAction(action_copy)

            # Search message on the web
            def search_on_web():
                filtered_message = urllib.parse.quote(msg.message)
                url = (
                    f"https://duckduckgo.com/?q={filtered_message}&t=lm&ia=web"
                )
                webbrowser.open(url)

            action_search_on_web = qt.QAction("Search message on the Web", menu)
            action_search_on_web.setStatusTip(
                "Search for the diagnostic message in "
                + "the system's default web-browser."
            )
            action_search_on_web.setIcon(
                iconfunctions.get_qicon("icons/gen/world.png")
            )
            action_search_on_web.triggered.connect(search_on_web)
            menu.addAction(action_search_on_web)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        def click_func(msg):
            if msg.path is not None and msg.offset is not None:
                file_path = functions.unixify_path(msg.path)
                self.main_form.open_file(file_path)
                tab = self.main_form.get_tab_by_save_name(file_path)
                if tab is not None:
                    tab.blink_error_index(msg.offset)

        def info_func(msg, menu_func):
            menu_func(msg)

        # Add the messages
        severities = []
        new_items = []
        for message in messages:
            severity = message.severity
            # General diagnostic
            diagnostic_text = self.__get_message_text(message)
            insert_item = None
            index = None
            new_items.append(
                {
                    "text": diagnostic_text,
                    "id": message._id,
                    "data": {
                        "info_func": functools.partial(
                            info_func, message, create_menu
                        ),
                        "click_func": functools.partial(click_func, message),
                    },
                    "parent": self.main_nodes[severity],
                    "insert_after": insert_item,
                    "index": index,
                }
            )
            severities.append(severity)
        self.multi_add(new_items)

        for severity in severities:
            self.main_nodes[severity].setExpanded(True)
            self._more_button_adjust(severity)
            self.refresh_counts(severity)

        self.update_style()
        self.main_form.update_editor_diagnostics()

    @qt.pyqtSlot(object)
    def message_bulk_removed(self, messages):
        severities = []
        for message in messages:
            severities.append(message.severity)
            self.remove(message._id)

        for severity in severities:
            self._more_button_adjust(severity)
            self.refresh_counts(severity)

        self.update_style()
        self.main_form.update_editor_diagnostics()

    @qt.pyqtSlot(object)
    def message_added(self, message):
        severity = message.severity

        # General diagnostic
        def create_menu(msg):
            # Create menu
            menu = gui.templates.basemenu.BaseMenu(self)
            # Open file
            if msg.path is not None and msg.offset is not None:

                def open_file():
                    file_path = functions.unixify_path(msg.path)
                    self.main_form.open_file(file_path)
                    main = self.main_form
                    tab = main.get_tab_by_save_name(file_path)
                    if tab is not None:
                        #                        tab.goto_line_column(msg.line, msg.column)
                        tab.goto_index(msg.offset)

                action_open = qt.QAction(
                    f"Go to '{self.severity_name[severity]}'", menu
                )
                action_open.setStatusTip(
                    "Open the file in an editor and move to the line "
                    + f"where the '{self.severity_name[severity]}' "
                    + "is located"
                )
                action_open.setIcon(
                    iconfunctions.get_qicon("icons/menu_edit/goto.png")
                )
                action_open.triggered.connect(open_file)
                menu.addAction(action_open)

            # Copy diagnostic to clipboard
            def clipboard_copy():
                cb = data.application.clipboard()
                cb.clear(mode=cb.Mode.Clipboard)
                cb.setText(msg.message, mode=cb.Mode.Clipboard)

            action_copy = qt.QAction("Copy message to clipboard", menu)
            action_copy.setStatusTip("Copy message to clipboard")
            action_copy.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/paste.png")
            )
            action_copy.triggered.connect(clipboard_copy)
            menu.addAction(action_copy)

            # Search message on the web
            def search_on_web():
                #                filtered_message = html.escape(message.message).replace(' ', '+')
                filtered_message = urllib.parse.quote(msg.message)
                url = (
                    f"https://duckduckgo.com/?q={filtered_message}&t=lm&ia=web"
                )
                webbrowser.open(url)

            action_search_on_web = qt.QAction("Search message on the Web", menu)
            action_search_on_web.setStatusTip(
                "Search for the diagnostic message in "
                + "the system's default web-browser."
            )
            action_search_on_web.setIcon(
                iconfunctions.get_qicon("icons/gen/world.png")
            )
            action_search_on_web.triggered.connect(search_on_web)
            menu.addAction(action_search_on_web)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        def click_func(msg):
            if msg.path is not None and msg.offset is not None:
                file_path = functions.unixify_path(msg.path)
                self.main_form.open_file(file_path)
                tab = self.main_form.get_tab_by_save_name(file_path)
                if tab is not None:
                    #                    tab.blink_error_line_column(msg.line, msg.column)
                    tab.blink_error_index(msg.offset)

        def info_func(msg):
            create_menu(msg)

        diagnostic_text = ""
        if message.path:
            filename = os.path.basename(message.path)
            diagnostic_text = f"{message.message} ({filename})"
        else:
            diagnostic_text = f"{message.message}"
        insert_item = None
        index = None
        if message.after:
            insert_item = self.item_cache[message.after._id]
        else:
            index = 0
        diagnostic_item = self.add(
            text=diagnostic_text,
            _id=message._id,
            in_data={
                "info_func": functools.partial(info_func, message),
                "click_func": functools.partial(click_func, message),
            },
            parent=self.main_nodes[severity],
            insert_after=insert_item,
            index=index,
        )
        self.main_nodes[severity].setExpanded(True)

        self._more_button_adjust(severity)
        self.update_style()
        self.main_form.update_editor_diagnostics()
        self.refresh_counts(severity)

        # Add a delay to make sure processing has ended
        if not hasattr(self, "check_timer"):
            self.check_timer = qt.QTimer(self)
            self.check_timer.setSingleShot(True)
            self.check_timer.setInterval(500)
            self.check_timer.timeout.connect(self._reset_adding_flag)
        else:
            self.check_timer.stop()
        self._adding = True
        self.check_timer.start()

    def _reset_adding_flag(self, *args):
        self._adding = False

    def adding(self):
        return self._adding

    @qt.pyqtSlot(object)
    def message_removed(self, message):
        severity = message.severity

        self.remove(message._id)

        self._more_button_adjust(severity)
        self.update_style()
        self.main_form.update_editor_diagnostics()
        self.refresh_counts(severity)

    @qt.pyqtSlot(object, int)
    def more_messages_available(self, severity, count):
        if count > 0:
            self._more_button_add(severity)
        else:
            self._more_button_remove(severity)
        self.refresh_counts(severity)

    def refresh_counts(self, severity):
        def refresh(*args):
            item_sum = self.diagnostics.get_item_sum(severity)
            original_text = self.main_nodes[severity].original_text
            if item_sum == 0:
                text = original_text
            else:
                #                child_sum = self.main_nodes[severity].childCount()
                #                text = f"{original_text} ({child_sum}/{item_sum})"
                text = f"{original_text} ({item_sum})"
            self.main_nodes[severity].setText(0, text)
            if severity == source_analyzer.Severity.FATAL:
                self.main_nodes[severity].setHidden(item_sum == 0)

        qt.QTimer.singleShot(0, refresh)

    def _more_button_add(self, severity):
        def show_more(*args):
            self.diagnostics.cap_increase(severity, data.diagnostic_cap)

        more_button_id = severity - 2000
        if not self.has(more_button_id):
            self.add(
                text="Show more errors",
                icon_path="icons/dialog/add.png",
                _id=more_button_id,
                in_data={
                    "click_func": show_more,
                },
                parent=self.main_nodes[severity],
            )

    def _more_button_remove(self, severity):
        more_button_id = severity.value - 2000
        self.remove(more_button_id)

    def _more_button_adjust(self, severity):
        more_button_id = severity.value - 2000
        if self.has(more_button_id):
            self._more_button_remove(severity)
            self._more_button_add(severity)

    def highlight(self, message):
        if hasattr(message, "_id") and message._id is not None:
            super()._highlight(message._id)
        else:
            data.signal_dispatcher.diagnostics_show_unknown.emit()

    def get_report(self):
        report = {}
        for number, main_item in self.item_cache.items():
            if number > -1:
                continue
            split_text = main_item.text(0).split()
            if len(split_text) > 1:
                text = " ".join(split_text[:-1])
            else:
                text = split_text[0]
            report[text] = []
            for i in range(main_item.childCount()):
                child = main_item.child(i)
                diagnostic_text = child.text(0)
                report[text].append(child.text(0))
        return report

    def get_rightclick_menu_function(self):
        def show_menu():
            # Main menu
            menu = gui.templates.basemenu.BaseMenu(self.main_form)
            # Diagnostic cap
            #            text = "Diagnostic cap: {}".format(data.diagnostic_cap)
            #            icon = "icons/gen/gear.png"
            #            new_action = qt.QAction(text, self.main_form)
            #            new_action.setStatusTip(
            #                "Set the number of diagnostic messages shown at one time."
            #            )
            #            new_action.setIcon(iconfunctions.get_qicon(icon))
            #            def set_cap(*args):
            #                result, new_cap_string = gui.dialogs.popupdialog.PopupDialog.ok_cancel(
            #                    "Set the diagnostics cap number:",
            #                    title_text="Diagnostic cap adjustment",
            #                    add_textbox=True,
            #                    initial_text=str(data.diagnostic_cap),
            #                    icon_path='icons/gen/gear.png',
            #                    parent=self.main_form
            #                )
            #                if result == qt.QMessageBox.StandardButton.Cancel:
            #                    return
            #                try:
            #                    new_cap = int(new_cap_string)
            #                    data.diagnostic_cap = new_cap
            #                    self.diagnostics.reset_capping()
            #                    self.main_form.settings.save(restyle=True)
            #                except:
            #                    self.main_form.display.display_error(traceback.format_exc())
            #            new_action.triggered.connect(set_cap)
            #            menu.addAction(new_action)
            # Help action
            help_action = qt.QAction("Help", self.main_form)
            help_action.setStatusTip("Display editor help")
            help_action.setIcon(
                iconfunctions.get_qicon("icons/dialog/help.png")
            )

            def help_func(*args):
                helpdocs.help_texts.show_diagnostics_help()
                return

            help_action.triggered.connect(help_func)
            menu.addAction(help_action)
            # Show the menu
            cursor = qt.QCursor.pos()
            menu.popup(cursor)

        return show_menu
