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
import argparse
import os_checker
import purefunctions
import qt
import os
import sys
import itertools
import functools
import inspect
import keyword
import re
import collections
import functools
import gc
import inspect
import itertools
import json
import keyword
import os
import queue
import re
import sys
import time
import traceback
import types
import webbrowser
from typing import *

import constants
import data
import gui.dialogs.popupdialog
import gui.dialogs.scalingdialog
import gui.forms.customeditor
import gui.forms.dockingoverlay
import gui.forms.informationoverlay
import gui.forms.messagewindow
import gui.forms.newfiletree
import gui.forms.plaineditor
import gui.forms.repllineedit
import gui.forms.settingswindow
import gui.forms.tabwidget
import gui.forms.terminal
import gui.forms.thebox
import lexers
import purefunctions
import qt

if data.PINCONFIG_ENABLED:
    import gui.forms.pinconfigurator

import beetle_console.make_console
import beetle_console.serial_console
import bpathlib.path_power
import chipconfigurator.widgets
import components.actionfilter
import components.buttonparser
import components.filechecker
import components.interpreter
import components.keyboardmanipulator
import components.lockcache
import components.sourceanalyzerinterface
import components.thesquid
import dashboard.chassis.dashboard
import debugger.debuggerwindow
import debugger.memoryviews
import functions
import gui.helpers.diagnosticwindow
import gui.helpers.info
import gui.helpers.popupsplitter
import gui.helpers.progresswidget
import gui.helpers.searchbar
import gui.helpers.searchresultswindow
import gui.helpers.symbolpopup
import gui.helpers.symbolwindow
import gui.helpers.textdiffer
import gui.stylesheets.mainwindow
import gui.templates.baseappwindow
import gui.templates.basemenu
import gui.templates.basetoolbar
import gui.templates.widgetgenerator
import helpdocs.help_subjects.debugging
import helpdocs.help_subjects.pinconfig
import helpdocs.help_texts
import iconfunctions
import new_dashboard.new_dashboard
import pieces.pieceswindow
import project.makefile_target_executer
import project.project
import sa_tab.chassis.sa_tab
import serverfunctions
import settings
import themes
import wizards.lib_wizard.lib_wizard
import wizards.zipped_lib_wizard.zipped_lib_wizard

"""
-------------------------------------------------
Main window and its supporting objects
-------------------------------------------------
"""


class MainWindow(gui.templates.baseappwindow.BaseAppWindow):
    """Main form that holds all Qt objects."""

    MINIMUM_SIZE = (200, 100)

    # Define main form control references
    name = "Main Window"
    main_groupbox = None  # QGroupBox that will hold everything
    messages_tabwidget = None  # Reference to a tab widget that holds messages
    messages_tab = None  # Reference to a tab that displays REPL messages
    diagnostics_tabwidget = None
    symbols_tabwidget = None
    filetree_tabwidget = None
    dashboard_tabwidget = None
    debugger_tabwidget = None
    pieces_tabwidget = None
    new_dashboard_tabwidget = None
    chipconfigurator_tabwidget = None
    memory_view_tabwidgets = {}
    sa_tabwidget = None
    node_tree_tab = (
        None  # Reference to a tab that displays NODE TREE information
    )
    menubar = None  # Menubar
    stored_menus = {}
    toolbar = None  # Toolbar
    statusbar = None  # Statusbar
    searchbar = None
    keyboard_manipulator = None
    progress_widget: Optional[gui.helpers.progresswidget.ProgressWidget] = None
    toolbar_save = None
    toolbar_save_all = None
    # Flag for locking the main window keypress and release
    key_lock = False
    # Last directory browsed by the "Open File" and other dialogs
    last_browsed_dir = ""
    # Generator for supplying the number when a new document is created
    new_file_count = itertools.count(0, 1)
    # Generator for supplying the number of opened consoles
    console_count = itertools.count(0, 1)
    # References for enabling/disabling saving of the current document in the menubar
    save_file_action = None
    save_ascii_file_action = None
    save_ansiwin_file_action = None
    # Attribute for signaling the state of the save buttons in the "File" menubar
    save_state = False
    # Supported Embeetle file extension types
    exco_file_exts = [
        "*" + ext
        for ext in itertools.chain.from_iterable(
            constants.file_extensions[key]
            for key in [
                "python",
                "cython",
                "c",
                "h",
                "cpp",
                "hpp",
                "pascal",
                "oberon",
                "ada",
                "json",
                "d",
                "nim",
                "perl",
                "xml",
                "text",
                "ini",
            ]
        )
    ]
    # Last focused widget and tab needed by the function wheel overlay
    last_focused_widget = None
    last_focused_tab = None
    """Namespace references for grouping functionality."""
    # settings:Optional[MainWindow.Settings]   = None
    # view:Optional[MainWindow.View]           = None
    # system:Optional[MainWindow.System]       = None
    # editing:Optional[MainWindow.Editing]     = None
    # display:Optional[MainWindow.Display]     = None
    # bookmarks:Optional[MainWindow.Bookmarks] = None
    # projects:Optional[MainWindow.Projects]   = None

    # Private attributes
    __initialized = False
    __parsed_buttons = None

    @property
    def initialized(self):
        return self.__initialized

    @initialized.setter
    def initialized(self, value):
        self.__initialized = value

    def __init__(
        self,
        options,
        logging=False,
        file_arguments=None,
        startup_project: Optional[str] = None,
        name: Optional[str] = None,
        source_analysis_only=False,
        source_analysis_result_file=None,
    ):
        """Initialization routine for the main form."""
        self.initialized = False
        # Initialize superclass, from which the main form is inherited
        if isinstance(startup_project, str):
            super().__init__(startup_project)
        else:
            super().__init__(name)
        self._basic_initialization(
            "Main Window",
            "Form",
            "Embeetle Project",
        )
        self.command_line_options: argparse.Namespace = options

        # Initialize the namespace references
        self.settings: Optional[Settings] = Settings(self)
        self.view: Optional[View] = View(self)
        self.system: Optional[System] = System(self)
        self.editing: Optional[Editing] = Editing(self)
        self.display: Optional[Display] = Display(self)
        self.bookmarks: Optional[Bookmarks] = Bookmarks(self)
        self.projects: Optional[Projects] = Projects(self)

        # Initialize multiprocessing locks
        functions.initialize_locks()

        # Initialize repl interpreter
        self._init_interpreter(
            self.get_references_autocompletions,
            self.display.display_message,
            self.display.display_success,
            self.display.display_warning,
            self.display.display_error,
        )
        # Initialize global references
        data.filechecker = components.filechecker.FileChecker()
        data.filechecker.file_changed.connect(self._reload_changed_file)
        data.filechecker.file_removed.connect(self._file_removed)
        # Initialize the docking overlay
        self.docking_overlay = gui.forms.dockingoverlay.DockingOverlay(self)
        # Initialize the global keyboard shortcut manipulator
        self.keyboard_manipulator = (
            components.keyboardmanipulator.KeyboardManipulator(self)
        )
        # Initialize statusbar
        self.progress_widget: Optional[
            gui.helpers.progresswidget.ProgressWidget
        ] = None
        self._init_statusbar()
        # Initialize basic window widgets(main, side_up, side_down)
        self.__init_widgets()
        # Initialize the menubar
        self.__init_menubar()
        # Initialize search bar
        self.__init_searchbar()
        # Set the initial window size according to the system resolution
        initial_size = qt.create_qsize(700, 600)
        initial_width = initial_size.width() * 14 / 10
        initial_height = initial_size.height() * 11 / 10
        self.resize(int(initial_width), int(initial_height))
        # Load the settings
        self.settings.restore()
        # Refresh theme
        self.view.refresh_theme()
        # Open the file passed as an argument to the QMainWindow initialization
        if file_arguments is not None:
            for file in file_arguments:
                self.open_file(file=file, tab_widget=self.get_largest_window())
        # Add a custom event filter
        self.installEventFilter(self)
        # Connect signals
        data.signal_dispatcher.notify_message.connect(
            self.display.display_message
        )
        data.signal_dispatcher.notify_success.connect(
            self.display.display_success
        )
        data.signal_dispatcher.notify_warning.connect(
            self.display.display_warning
        )
        data.signal_dispatcher.notify_error.connect(self.display.display_error)
        data.signal_dispatcher.source_analyzer.project_initialized.connect(
            self.set_current_symbol_analysis
        )
        data.signal_dispatcher.file_tree_watchdog_observer_error.connect(
            self.display.watchdog_observer_error
        )
        data.signal_dispatcher.project_loaded.connect(
            self.projects.check_debugger
        )
        if data.PINCONFIG_ENABLED:
            data.signal_dispatcher.project_loaded.connect(
                self.projects.check_pinconfig
            )
        if data.CHIPCONFIGURATOR_ENABLED:
            data.signal_dispatcher.project_loaded.connect(
                self.projects.check_chipconfigurator
            )
        data.signal_dispatcher.program_state_changed.connect(
            self.__change_program_state
        )
        data.signal_dispatcher.makefile_command_executed.connect(
            self.__makefile_command_executed
        )
        data.signal_dispatcher.file_edited.connect(
            self.__included_file_edited_check
        )
        data.signal_dispatcher.restart_needed_notify.connect(
            self.__restart_notification_received
        )
        data.signal_dispatcher.save_layout.connect(self.view.layout_save)
        data.signal_dispatcher.diagnostics_show_unknown.connect(
            self.__unknown_diagnostic
        )
        data.signal_dispatcher.source_analyzer.progress_completed.connect(
            self.enable_build_flash
        )
        data.signal_dispatcher.source_analyzer.progress_updated.connect(
            self.disable_build_flash
        )
        data.signal_dispatcher.file_folder.file_renamed_sig.connect(
            self.__renamed_file
        )
        data.signal_dispatcher.file_folder.folder_renamed_sig.connect(
            self.__renamed_directory
        )
        components.sourceanalyzerinterface.SourceAnalysisCommunicator().internal_sa_err_sig.connect(
            self.display.show_internal_error,
        )
        components.sourceanalyzerinterface.SourceAnalysisCommunicator().project_generated_sig.connect(
            self.initialize_source_analysis_objects
        )
        # Save / Save all relevant signals
        data.signal_dispatcher.editor_state_changed.connect(
            self.__check_save_buttons
        )
        data.signal_dispatcher.tab_index_changed.connect(
            self.__check_save_buttons
        )
        data.signal_dispatcher.indication_changed.connect(
            self.__check_save_buttons
        )

        # Set the initial program state
        data.signal_dispatcher.program_state_changed.emit(
            data.ProgramState.Saved
        )

        # $ Initialize the Clang engine
        @functions.safe_execute
        def display_message(message: str) -> None:
            data.signal_dispatcher.notify_message.emit(message)
            return

        @functions.safe_execute
        def display_warning(message: str) -> None:
            data.signal_dispatcher.notify_warning.emit(message)
            return

        @functions.safe_execute
        def display_error(message: str) -> None:
            data.signal_dispatcher.notify_error.emit(message)
            return

        # $ Check startup project validity
        if startup_project is not None:
            # Standardize the absolute path to the project rootfolder. This should:
            #     - make sure it's an absolute path
            #     - expand symlinks
            #     - turn '\' into '/'
            #     - remove a trailing '/'

            startup_project = bpathlib.path_power.standardize_abspath(
                startup_project
            )
            # Make sure the project rootfolder exists. Quit otherwise.
            if not os.path.isdir(startup_project):
                self.exit()
                sys.exit(f"Startup project '{startup_project}' does not exist!")

        # $ Initialize source analysis
        assert self.progress_widget is not None
        components.sourceanalyzerinterface.init(
            progress_widget=self.progress_widget,
            debug_mode=self.command_line_options.debug_mode,
        )
        # Connect to the communicator signals
        self.connect_received_signal(self._data_received)
        # Check if only source analysis should be performed
        self.source_analysis_only = source_analysis_only
        self.source_analysis_result_file = source_analysis_result_file
        self.source_analysis_only_diagnostic_cap = (
            self.command_line_options.source_analysis_only_diagnostic_cap
        )
        if source_analysis_result_file is None:
            self.source_analysis_result_file = functions.unixify_path_join(
                startup_project, "source_analysis_results.json"
            )
        # $ Initialize TheSquid object
        components.thesquid.TheSquid.init_objects(self)
        # $ Connect update style signal
        data.signal_dispatcher.update_styles.connect(self.settings.restore)

        # Connect debugger signals
        data.signal_dispatcher.debug_connected.connect(
            self.parsed_buttons_disable
        )
        data.signal_dispatcher.debug_connected.connect(
            self.editors_readonly_check
        )
        data.signal_dispatcher.debug_disconnected.connect(
            self.parsed_buttons_enable
        )
        data.signal_dispatcher.debug_disconnected.connect(
            self.editors_readonly_check
        )
        data.signal_dispatcher.debug_breakpoint_delete_all.connect(
            gui.forms.customeditor.CustomEditor.debugger_breakpoint_delete_all
        )

        # $ Open a startup project if valid
        if startup_project is not None:
            # At this point, the 'startup_project' path to the project's rootfolder is already
            # checked for validity (see above). The assertions only confirm that.
            assert isinstance(startup_project, str)
            assert os.path.isdir(startup_project)
            assert os.path.isabs(startup_project)
            project_name = functions.get_last_directory_from_path(
                startup_project
            )
            self.change_title(f"{project_name} - Embeetle")

            def open_project(*args) -> None:
                self.projects.load_project(startup_project)
                return

            qt.QTimer.singleShot(0, open_project)

        return

    def __check_save_buttons(
        self, index: int, tab_widget: object, state: str
    ) -> None:
        if self.toolbar_save is None or self.toolbar_save_all is None:
            return
        # 'Save' toolbar button
        if state == "saved" or state == "edited":
            if tab_widget.indicated:
                widget = tab_widget.widget(index)
                if hasattr(widget, "save_status"):
                    if widget.save_status == data.FileStatus.MODIFIED:
                        self.toolbar_save.setEnabled(True)
                        self.save_file_action.setEnabled(True)
                        self.set_shortcut_enabled("file-save", True)
                    else:
                        self.toolbar_save.setEnabled(False)
                        self.save_file_action.setEnabled(False)
                        self.set_shortcut_enabled("file-save", False)
        elif state == "indication-changed":
            indicated_tab = self.get_tab_by_indication()
            if hasattr(indicated_tab, "save_status"):
                if indicated_tab.save_status == data.FileStatus.MODIFIED:
                    self.toolbar_save.setEnabled(True)
                    self.save_file_action.setEnabled(True)
                    self.set_shortcut_enabled("file-save", True)
                else:
                    self.toolbar_save.setEnabled(False)
                    self.save_file_action.setEnabled(False)
                    self.set_shortcut_enabled("file-save", False)
            else:
                self.toolbar_save.setEnabled(False)
                self.save_file_action.setEnabled(False)
                self.set_shortcut_enabled("file-save", False)
        # 'Save All' toolbar button
        editors = self.get_all_editors()
        for e in editors:
            if e.save_status == data.FileStatus.MODIFIED:
                self.toolbar_save_all.setEnabled(True)
                self.save_project_action.setEnabled(True)
                self.set_shortcut_enabled("file-save-all", True)
                break
        else:
            self.toolbar_save_all.setEnabled(False)
            self.save_project_action.setEnabled(False)
            self.set_shortcut_enabled("file-save-all", False)
            # Disable also the single save button
            self.toolbar_save.setEnabled(False)
            self.save_file_action.setEnabled(False)
            self.set_shortcut_enabled("file-save", False)

    def __renamed_file(self, src, dest, is_synthetic):
        editors = self.get_all_editors()
        for e in editors:
            if e.save_name == src:
                e.save_name = dest
                index = e._parent.indexOf(e)
                if index != -1:
                    e._parent.setTabText(index, os.path.basename(dest))
                    e._parent.reset_text_changed(index=index)

    def __renamed_directory(self, src, dest, is_synthetic):
        pass

    @qt.pyqtSlot(object)
    def _data_received(self, _data: object) -> None:
        _from, message = _data

        # Initialization safety check
        if not self.initialized:
            return

        if message == "ping":
            self.send("pong")
        elif message.startswith("show-project:"):
            project_name = message.split("::")[1].strip()
            this_project = data.current_project.get_proj_rootpath()
            if project_name == this_project:
                self.send("project-found")
                self._show()
        elif message == "restyle":
            if _from != self.communicator.name:
                self.settings.restore(echo=False)
        elif message == "reassign-shortcuts":
            if _from != self.communicator.name:
                self.reassign_shortcuts()
        elif message == "geometry":
            geometries = {}
            geometries["project_window"] = functions.get_geometry(self)
            for k in self.display.dialogs:
                dialog = getattr(self, k)
                if dialog is not None and dialog.isVisible():
                    geometries[k] = functions.get_geometry(dialog)
            self.send(functions.json_encode(geometries))
        elif "add_tool(" in message:
            try:
                msg = message[9:-1]
                data.toolman.receive_add_tool_msg(msg)
            except Exception as e:
                functions.echo(f"ERROR: Cannot interpret message {message}")
                self.receive_queue.put(_data)
        elif "delete_tool(" in message:
            try:
                msg = message[12:-1]
                data.toolman.receive_delete_tool_msg(msg)
            except Exception as e:
                traceback.print_exc()
                functions.echo(f"ERROR: Cannot interpret message {message}")
                self.receive_queue.put(_data)
        else:
            self.receive_queue.put(_data)
        return

    @qt.pyqtSlot(
        object,
        object,
        object,
    )
    def initialize_source_analysis_objects(
        self, project, diagnostics, symbolhandler
    ):
        if self.projects.diagnostics_window is not None:
            self.projects.diagnostics_window.add_diagnostics(diagnostics)
        if self.projects.symbols_window is not None:
            self.projects.symbols_window.get_file_symbols().add_symbolhandler(
                symbolhandler
            )

    @qt.pyqtSlot()
    def __source_analysis_complete(self):
        if self.source_analysis_only == True:
            # Additional delay
            for i in range(10):
                functions.process_events(10, delay=0.1)

            console_name = "Output"
            new_console = self.create_console(
                console_name=console_name,
                console_type=data.ConsoleType.Make,
            )
            # Execute commands
            executioner = (
                project.makefile_target_executer.MakefileTargetExecuter()
            )
            executioner.execute_makefile_targets(
                console=new_console,
                target="build",
                callback=self.__build_completed,
                callbackArg=None,
            )

    @qt.pyqtSlot()
    def __build_completed(self, result, callbackArg):
        while self.projects.diagnostics_window.adding():
            functions.process_events(10)

        # Additional delay
        for i in range(10):
            functions.process_events(10, delay=0.1)

        report = self.projects.diagnostics_window.get_report()
        report["build-result"] = result
        functions.write_json_file(
            self.source_analysis_result_file,
            report,
        )
        self.exit()

    def _no_config_callback(self):
        pass

    def update_statusbar_style(self):
        super().update_statusbar_style()
        if self.searchbar is not None:
            self.searchbar.update_style()
        if data.alert_buttons is not None:
            for k, v in data.alert_buttons.items():
                new_size = (
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                )
                v.update_style(new_size)
        if data.alert_labels is not None:
            for k, v in data.alert_labels.items():
                v.update_style()

    def get_form_references(self):
        """Create and return a dictionary that holds all the main form
        references that will be used by the REPL interpreter."""
        return dict(
            form=self,
            quit=self.exit,
            exit=self.exit,
            new=self.create_new,
            open=self.open_files,
            open_d=self.open_file_with_dialog,
            save=functions.write_to_file,
            version=functions.get_embeetle_version(),
            set_cwd=self.set_cwd,
            get_cwd=self.get_cwd,
            open_cwd=self.open_cwd,
            close_all=self.close_all_tabs,
            # Settings functions
            settings=self.settings.manipulator,
            save_settings=self.settings.save,
            load_settings=self.settings.restore,
            # System function
            find_files=self.system.find_files,
            find_in_files=self.system.find_in_files,
            replace_in_files=self.system.replace_in_files,
            # Document editing references
            find=self.editing.find,
            regex_find=self.editing.regex_find,
            find_and_replace=self.editing.find_and_replace,
            regex_find_and_replace=self.editing.regex_find_and_replace,
            goto_line=self.editing.line.goto,
            replace_all=self.editing.replace_all,
            regex_replace_all=self.editing.regex_replace_all,
            replace_in_selection=self.editing.replace_in_selection,
            regex_replace_in_selection=self.editing.regex_replace_in_selection,
            highlight=self.editing.highlight,
            regex_highlight=self.editing.regex_highlight,
            clear_highlights=self.editing.clear_highlights,
            find_in_open_documents=self.editing.find_in_open_documents,
            find_replace_in_open_documents=self.editing.find_replace_in_open_documents,
            replace_all_in_open_documents=self.editing.replace_all_in_open_documents,
            replace_line=self.editing.line.replace,
            remove_line=self.editing.line.remove,
            get_line=self.editing.line.get,
            set_line=self.editing.line.set,
            # Display functions
            echo=self.display.display_message_with_type,
            show_node_tree=self.display.show_nodes,
        )

    def get_references_autocompletions(self):
        """Get the form references and autocompletions."""
        new_references = dict(self.get_form_references().items())
        # Create auto completion list for the REPL
        ac_list_prim = [x for x in new_references]
        # Add Python/custom keywords to the primary level autocompletions
        ac_list_prim.extend(keyword.kwlist)
        ac_list_prim.extend(["range"])
        # Add current working directory items to the primary autocompletions
        ac_list_prim.extend(os.listdir(os.getcwd()))
        # Create the secondary autocompletion list
        # (methods and attributes of the primary list references)
        ac_list_sec = []
        keywords = new_references
        # Get all keyword methods and variables
        for key in keywords:
            ac_list_sec.append(key)
            # Add methods to secondary autocompletion list
            for method in inspect.getmembers(
                keywords[key], predicate=inspect.isroutine
            ):
                if str(method[0])[0] != "_":
                    ac_list_sec.append(str(key) + "." + str(method[0]))
            # Add variables to secondary autocompletion list
            try:
                for variable in keywords[key].__dict__:
                    if str(variable)[0] != "_":
                        ac_list_sec.append(str(key) + "." + str(variable))
            except:
                pass
        # Return the tuple
        return (new_references, ac_list_prim, ac_list_sec)

    def get_cwd(self):
        """Display the current working directory."""
        self.display.display_message_with_type(os.getcwd())

    def open_cwd(self):
        """Display the current working directory in the systems explorer."""
        cwd = os.getcwd()
        if os_checker.is_os("windows"):
            self.repl._repl_eval("r: explorer .")
        elif os_checker.is_os("linux"):
            self.repl._repl_eval('r: xdg-open "{}"'.format(cwd))
        else:
            self.display.display_message_with_type(
                f"Not implemented on '{os_checker.get_os()}' platform!"
            )

    def set_cwd(self, directory):
        """Set the current working directory and display it (Overridden to
        always set to project directory)"""
        #        os.chdir(directory)
        os.chdir(data.current_project.get_proj_rootpath())
        # Reset the interpreter and update its references
        #        self._reset_interpreter()
        # Update the last browsed directory to the class/instance variable
        self.last_browsed_dir = directory
        # Display the selected directory

    #        self.display.display_message_with_type("CWD changed to:")
    #        self.get_cwd()

    #    def leaveEvent(self,  event):
    #        """Event that fires when you leave the main form"""

    def check_closing_state(self, loop):
        """Checks the closing state of the pin-configurator window and exits the
        loop if closed."""
        if self.projects.pinconfigurator_window is not None:
            if self.projects.pinconfigurator_window.getClosingState():
                loop.quit()

    def closeEvent(self, event):
        """Event that fires when the main window is closed."""
        if self.display.state == False:
            event.ignore()
            return
        # Pin-configurator close event
        if self.projects.pinconfigurator_window is not None:
            self.projects.pinconfigurator_window.close_event()
            # Create an event loop to block until the window closes or timeout
            loop = qt.QEventLoop()
            timer = qt.QTimer()
            # Connect the timer to stop the loop after 3 seconds
            timer.timeout.connect(loop.quit)
            timer.start(3000)  # 3000 milliseconds = 3 seconds
            # Check every 100 milliseconds if the window has closed
            check_timer = qt.QTimer()
            check_timer.timeout.connect(lambda: self.check_closing_state(loop))
            check_timer.start(100)  # 100 milliseconds
            # Start the event loop, will exit if either timer or check_timer calls quit
            loop.exec()
            # Stop timers
            timer.stop()
            check_timer.stop()
        # Check if there are any modifications
        if self.check_document_states() == True:
            quit_message = "You have unsaved changes!\nWhat do you wish to do?"
            buttons = [
                ("Save && Quit", "save-and-quit"),
                ("Quit", "quit"),
                ("Cancel", "cancel"),
            ]
            reply = gui.dialogs.popupdialog.PopupDialog.custom_buttons(
                quit_message, parent=self, buttons=buttons, text_centered=True
            )
            if reply[0] == "cancel":
                event.ignore()
                return
            elif reply[0] == "save-and-quit":
                self.save_all()
            elif reply[0] == "quit":
                pass
        if self.check_dashboard_state() == True:
            quit_message = "You have unsaved changes!\nQuit anyway?"
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                quit_message, parent=self
            )
            if reply != qt.QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        # Abort the clang engine
        components.sourceanalyzerinterface.SourceAnalysisCommunicator().abort()
        # Save layout
        try:
            # Execute layout save
            self.view.layout_save(_async=False)
            # Check Layout save timer
        #            while self.view.check_layout_timer():
        #                functions.process_events()
        except:
            traceback.print_exc()
        # Close the symbol popup
        if hasattr(self, "symbol_popup"):
            if self.symbol_popup is not None:
                if qt.sip.isdeleted(self.symbol_popup) == False:
                    self.symbol_popup.__del__()
                    self.symbol_popup = None
        # Call the clean-up for the communicator
        self.self_destruct()
        # Execute the superclass closeEvent
        super().closeEvent(event)

    def self_destruct(self):
        super().self_destruct()
        # Filetree
        if data.filetree:
            data.filetree.self_destruct()
        # Symbol window
        if self.projects.symbols_window:
            self.projects.symbols_window.self_destruct()
        # Debugger
        if data.DEBUGGER_ENABLED:
            if self.projects.debugger_window:
                self.projects.debugger_window.self_destruct()
        # Pieces AI
        if self.projects.pieces_window is not None:
            del self.projects.pieces_window
        # New Dashboard
        if self.projects.new_dashboard_window is not None:
            del self.projects.new_dashboard_window
        # Chip Configurator
        if self.projects.chipconfigurator_window is not None:
            del self.projects.chipconfigurator_window

    def leaveEvent(self, event):
        super().leaveEvent(event)

    def eventFilter(self, object, event):
        #        if event.type() == 6:
        #            # Key press
        #            pass
        #        if event.type() == 7:
        #            # Key release
        #            functions.echo(event.type())
        #            key = event.key()
        #            modifiers = event.modifiers()
        #            key_combination = self.keyboard_manipulator.get_key_combination(
        #                key, modifiers
        #            )
        #            functions.echo(key_combination)

        #        if event.type() == qt.QEvent.Type.MouseButtonPress:
        #            # Mouse press
        #            print("[MainWindow] Mouse press")
        #        if event.type() == qt.QEvent.Type.MouseButtonRelease:
        #            # Mouse release
        #            print("[MainWindow] Mouse release")
        #        if event.type() == qt.QEvent.Type.MouseMove:
        #            pass

        #        if event.type() == qt.QEvent.Type.HoverMove:
        #            cursor = qt.QCursor.pos()
        #            widget = data.application.widgetAt(cursor)

        if event.type() == qt.QEvent.Type.Enter:
            self.display.docking_overlay_hide()

        if event.type() == qt.QEvent.Type.WindowActivate:
            pass

        if event.type() == qt.QEvent.Type.StatusTip:
            if self.display.statusbar_message_blocked_flag:
                event.ignore()
                return True
        # The part below doesn't work correctly on Linux only,
        # the first tab drag immediately hides the overlay, but the second
        # and all the rest drags work without problems
        #        elif event.type()== qt.QEvent.Type.WindowDeactivate:
        #            self.display.docking_overlay_hide()

        #        if event.type() == qt.QEvent.Type.Resize or \
        #           event.type() == qt.QEvent.Type.UpdateRequest or \
        #           event.type() == qt.QEvent.Type.LayoutRequest:
        #            pass

        return False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Hide the function whell if it is displayed
        self.view.hide_all_overlay_widgets()
        # Save the layout
        self.view.layout_save()

    def moveEvent(self, event):
        super().moveEvent(event)
        # Save the layout
        self.view.layout_save()

    def keyPressEvent(self, event):
        """QMainWindow keyPressEvent, to catch which key was pressed."""
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """QMainWindow keyReleaseEvent, to catch which key was pressed."""
        # Hide widgets on Escape press
        if event.key() == qt.Qt.Key.Key_Escape:
            self.searchbar.hide()
            self.view.hide_all_overlay_widgets()

        return super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        """Overridden main window mouse click event."""
        # Execute the superclass mouse press event
        super().mousePressEvent(event)
        # Hide the function wheel if it is shown
        if event.button() != qt.Qt.MouseButton.RightButton:
            self.view.hide_all_overlay_widgets()
        # Reset the click&drag context menu action
        components.actionfilter.ActionFilter.clear_action()

    def mouseReleaseEvent(self, event):
        # Execute the superclass mouse press event
        super().mouseReleaseEvent(event)

    def _key_events_lock(self):
        """Function for disabling/locking the keypress and keyrelease events
        (used by the gui.forms.repllineedit.ReplLineEdit widget)"""
        # Disable the key events of the QMainWindow
        self.key_lock = True
        # Disable the save/saveas buttons in the menubar
        self.set_save_file_state(False)

    def _key_events_unlock(self):
        """Function for enabling/unlocking the keypress and keyrelease events
        (used by the gui.forms.repllineedit.ReplLineEdit widget)"""
        # Reenable the key events of the QMainWindow
        self.key_lock = False

    def _get_directory_with_dialog(self):
        """Function for using a QFileDialog window for retrieving a directory
        name as a string."""
        dir_dialog = qt.QFileDialog
        directory = dir_dialog.getExistingDirectory()
        return directory

    #    def run_process(self, command, show_console=True, output_to_repl=False):
    #        """Run a command line process and display the result"""
    #        self.display.display_message_with_type("Executing CMD command: \"" + command + "\"")
    #        #Run the command and display the result
    #        result  = self.repl.interpreter.run_cmd_process(command, show_console, output_to_repl)
    #        self.display.display_message_with_type(result)

    def file_create_new(self):
        """The function name says it all."""
        self.create_new(tab_name=None, tab_widget=self.last_focused_widget)

    def file_open(self):
        """The function name says it all."""
        self.open_file_with_dialog(tab_widget=self.last_focused_widget)

    def __source_analyzer_reload_file(self, tab):
        """The function name says it all."""
        if (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().has_project()
        ):
            if not tab.isReadOnly():
                components.sourceanalyzerinterface.SourceAnalysisCommunicator().reload_file(
                    tab.save_name
                )
        else:
            self.display.display_error(
                "Source-analyzer project not initialized, "
                + "source-analyzer cannot reload file!"
            )

    def file_save(self, encoding="utf-8", line_ending="\n"):
        """The function name says it all."""
        focused_tab = self.get_tab_by_focus()
        if isinstance(focused_tab, gui.forms.customeditor.CustomEditor) == True:
            if (focused_tab is not None) and (
                focused_tab.savable == data.CanSave.YES
            ):
                focused_tab.save_document(
                    saveas=False,
                    last_dir=self.last_browsed_dir,
                    encoding=encoding,
                    line_ending="\n",
                )
                # Set the icon if it was set by the lexer
                focused_tab.icon_manipulator.update_icon(focused_tab)
                # Save the last browsed directory from the editor widget to the main form
                self.last_browsed_dir = focused_tab.last_browsed_dir
                # Reimport the user configuration file and update the menubar
                if functions.is_config_file(focused_tab.save_name) == True:
                    self.update_menubar()
                    self.import_user_functions()
                # Source analyzer reload
                self.__source_analyzer_reload_file(focused_tab)

    def file_saveas(self, encoding="utf-8"):
        """The function name says it all."""
        focused_tab = self.get_tab_by_focus()
        if focused_tab is not None:
            focused_tab.save_document(
                saveas=True,
                last_dir=self.last_browsed_dir,
                encoding=encoding,
                line_ending="\n",
            )
            # Set the icon if it was set by the lexer
            focused_tab.icon_manipulator.update_icon(focused_tab)
            # Save the last browsed directory from the editor widget to the main form
            self.last_browsed_dir = focused_tab.last_browsed_dir
            # Reimport the user configuration file and update the menubar
            if functions.is_config_file(focused_tab.save_name) == True:
                self.update_menubar()
                self.import_user_functions()
            # Source analyzer reload
            self.__source_analyzer_reload_file(focused_tab)

    def file_save_all(self, *args, encoding="utf-8"):
        """Save all open modified files."""
        # Create a list of the windows
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check the tabs
        saved_something = False
        for window in windows:
            for i in range(0, window.count()):
                tab = window.widget(i)
                # Skip to next tab if it is not a gui.forms.customeditor.CustomEditor
                if (
                    isinstance(tab, gui.forms.customeditor.CustomEditor)
                    == False
                ):
                    continue
                # Test if the tab is modified and savable
                if (
                    tab.savable == data.CanSave.YES
                    and tab.save_status == data.FileStatus.MODIFIED
                ):
                    # Set the saved flag, will be reset by the FileChecker
                    #                    tab.saved_flag = True
                    # Save the file
                    tab.save_document(
                        saveas=False,
                        last_dir=None,
                        encoding=encoding,
                        line_ending="\n",
                    )
                    # Set the icon if it was set by the lexer
                    tab.icon_manipulator.update_icon(tab)
                    # Update the toolbar buttons if it's the project's button file
                    self._special_file_modification_check(tab.save_name)
                    # Add file to the FileChecker
                    data.filechecker.checker_file_add(tab.save_name)
                    # Source analyzer reload
                    self.__source_analyzer_reload_file(tab)
                    # Kristof's update
                    try:
                        data.signal_dispatcher.file_folder.file_saved_sig.emit(
                            functions.unixify_path(tab.save_name)
                        )
                    except Exception as err:
                        traceback.print_exc()
                    # Set the saved something flag
                    saved_something = True
        # Save the layout
        self.view.layout_save()
        # Display the successful save
        if saved_something == False:
            self.display.display_warning("No modified documents to save")
        else:
            self.display.display_success("'Save all' executed successfully")
            data.signal_dispatcher.program_state_changed.emit(
                data.ProgramState.Saved
            )
            """
            Delayed checking for changes in the file-tree, as the build system
            needs a up-to-date filetree.mk file before starting a build.
            """
            # Wait for source-analyzer processing
            safety_counter: int = 0
            safety_limit: int = 100
            while (
                components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_project_status()
                == 1
            ):
                safety_counter += 1
                if safety_counter > safety_limit:
                    break
                # Event processing
                functions.process_events(10, delay=0.01)
            # Check if file-tree processing is completed
            safety_counter = 0
            while data.filetree.makefile_generation_in_progress:
                safety_counter += 1
                if safety_counter > safety_limit:
                    break
                # Event processing
                functions.process_events(10, delay=0.01)

    def save_all(self):
        # Save all the files opened in editors
        self.file_save_all()
        # Save the project
        if self.projects.dashboard_save_flag:
            self.projects.save_project()

    def reload_all_editors(self, file_list):
        windows = self.get_all_windows()
        for win in windows:
            for i in range(win.count()):
                if isinstance(
                    win.widget(i), gui.forms.customeditor.CustomEditor
                ):
                    editor: gui.forms.customeditor.CustomEditor = win.widget(i)
                    for f in file_list:
                        if editor.save_name == functions.unixify_path(f):
                            editor.reload_file()
                            break

    def update_menubar(self):
        """Update the Menubar in case any keyboard shortcuts were changed in the
        configuration file."""
        self.__init_menubar()
        self.settings.update_recent_files_list()
        self.settings.update_recent_projects_list()

    def _test_console(self):
        # Create a console
        raise NotImplementedError()

    def parse_buttons(self, *args) -> None:
        """"""
        # Parse new buttons
        button_file = data.current_project.get_treepath_seg().get_abspath(
            "BUTTONS_BTL"
        )
        button_file_relative = (
            data.current_project.get_treepath_seg().get_relpath("BUTTONS_BTL")
        )
        # Clean old buttons
        if not hasattr(self.toolbar, "button_list"):
            self.toolbar.button_list = []
        else:
            for a in self.toolbar.button_list:
                self.toolbar.removeAction(a)
            self.toolbar.button_list = []
        # Create the button parser
        button_parser = components.buttonparser.ButtonParser(self, button_file)
        buttons: Optional[List[Union[qt.QAction, qt.QWidgetAction]]] = None
        try:
            buttons = button_parser.parse()
            self.display.display_success(
                f"Successfully parsed '{button_file_relative}' buttons."
            )
        except:
            self.display.display_error(traceback.format_exc())
            self.display.display_error(button_file_relative)

        # Add the buttons and separators to the toolbar
        if (
            not hasattr(self, "toolbar_beginning_separator")
            or self.toolbar_beginning_separator is None
        ):
            self.toolbar_beginning_separator = self.toolbar.addSeparator()
        if (
            not hasattr(self, "toolbar_ending_separator")
            or self.toolbar_ending_separator is None
        ):
            self.toolbar_ending_separator = self.toolbar.addSeparator()
        self.__parsed_buttons = []
        if buttons is not None:
            for b in buttons:
                function = b["function"]
                if function is None:
                    if "commands" not in b.keys():
                        self.display.display_warning(
                            f"Skipping parsing toolbar button '{b['name']}', "
                            "missing 'commands' field in button description."
                        )
                        continue
                    commands = b["commands"]
                    current_working_directory = None
                    if "current-working-directory" in b.keys():
                        current_working_directory = b[
                            "current-working-directory"
                        ]
                    function = self.__parsed_buttons_custom_command(
                        commands, current_working_directory
                    )

                new_action = self.create_action(
                    name=f"parsed_button_{b['name']}",
                    text=f" {b['text']} ",
                    keys_data=b["shortcut"],
                    statustip=b["statustip"],
                    tooltip=b["tooltip"],
                    icon=b["icon"],
                    function=function,
                    enabled=b["enabled"],
                    menubar_action=b["menubar_action"],
                    warn_of_existing_shortcut=b["warn_of_existing_shortcut"],
                )

                self.toolbar.button_list.append(new_action)
                self.toolbar.insertAction(
                    self.toolbar_ending_separator, new_action
                )
                # Disable the buttons if debugger is active
                if data.debugging_active:
                    new_action.setEnabled(False)
                self.__parsed_buttons.append(new_action)

        # Update global shortcuts
        self.reassign_shortcuts()
        return

    def __parsed_buttons_custom_command(
        self, commands: List[str], current_working_directory: Optional[str]
    ) -> Callable:
        """
        Returns a button function that runs a list of commands sequentially
        in the specified working directory, using callbacks for sequencing.
        """

        def button_function(*args):
            console_name = "Output"
            new_console = self.create_console(
                console_name=console_name,
                console_type=data.ConsoleType.Standard,
            )
            # Execute the commands
            new_console.execute_commands(commands, current_working_directory)

        return button_function

    def parsed_buttons_disable(self):
        for b in self.__parsed_buttons:
            b.setEnabled(False)

    def parsed_buttons_enable(self):
        for b in self.__parsed_buttons:
            b.setEnabled(True)

    def editors_readonly_check(self):
        editors = self.get_all_editors()
        for e in editors:
            e.readonly_check()

    def reassign_shortcuts(self, update_preferences_window=True):
        super().reassign_shortcuts()
        for e in self.get_all_editors():
            e.keyboard.reassign_keyboard_bindings()
        if update_preferences_window:
            if self.settings.preferences_window is not None:
                self.settings.preferences_window.update_settings()

    def enable_build_flash(self):
        if self.__parsed_buttons is None:
            return
        for b in self.__parsed_buttons:
            if b.objectName() in ("parsed_button_clean",):
                continue
            b.setEnabled(True)

    def disable_build_flash(self):
        if self.__parsed_buttons is None:
            return
        for b in self.__parsed_buttons:
            if b.objectName() in ("parsed_button_clean",):
                continue
            b.setEnabled(False)

    def _init_toolbar(self):
        if data.current_project is None:
            return
        # Clean up the toolbar if it already exists
        serial_port_items = None
        serial_port_selected_item = None
        serial_port_visible = True
        if self.toolbar is not None:
            if hasattr(self, "serial_port"):
                serial_port_visible = self.serial_port.isVisible()
                serial_port_items = self.serial_port.acb.get_items()
                serial_port_selected_item = (
                    self.serial_port.acb.get_selected_item()
                )

            self.removeToolBar(self.toolbar)
            self.toolbar = None
            self.toolbar_beginning_separator = None
            self.toolbar_ending_separator = None
        # Create the new toolbar
        self.toolbar = gui.templates.basetoolbar.BaseToolBar()
        self.toolbar.setObjectName("ToolBar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # Add context menu
        def show_menu(*args):
            if not hasattr(self, "toolbar_menu"):
                self.toolbar_menu = gui.templates.basemenu.BaseMenu(self)
                # Open buttons file
                new_action = qt.QAction("Open buttons file", self.toolbar_menu)
                new_action.setStatusTip("Copy message to clipboard")
                new_action.setIcon(
                    iconfunctions.get_qicon(f"icons/folder/open/file.png")
                )

                def open_button_file(*args):
                    try:
                        button_file = (
                            data.current_project.get_treepath_seg().get_abspath(
                                "BUTTONS_BTL"
                            )
                        )
                        self.open_file(file=button_file)
                    except:
                        data.main_form.display.display_error(
                            traceback.format_exc()
                        )
                        traceback.print_exc()

                new_action.triggered.connect(open_button_file)
                self.toolbar_menu.addAction(new_action)
                # Reparse buttons
                new_action = qt.QAction("Reparse buttons", self.toolbar_menu)
                new_action.setStatusTip("Reparse the special button file")
                new_action.setIcon(
                    iconfunctions.get_qicon(f"icons/dialog/refresh.png")
                )
                new_action.triggered.connect(self.parse_buttons)
                self.toolbar_menu.addAction(new_action)
            # Show the menu
            cursor = qt.QCursor.pos()
            self.toolbar_menu.popup(cursor)

        self.toolbar.customContextMenuRequested.connect(show_menu)
        """Create the needed buttons."""
        # $ Home Button
        self.toolbar_home_button = gui.templates.widgetgenerator.create_action(
            parent=self.toolbar,
            name="home_button",
            statustip=gui.forms.informationoverlay.descriptions["Home Button"],
            tooltip=gui.forms.informationoverlay.descriptions["Home Button"],
            icon_path="icons/gen/home.png",
            func=self.open_home_window,
            ribbon_style=data.ribbon_style_toolbar,
            text=" home ",
        )
        self.toolbar.addAction(self.toolbar_home_button)
        self.toolbar.addSeparator()

        # $ Save Button
        def special_save_file(*args):
            self.file_save()

        tooltip = (
            "Save currently focused file in the UTF-8 encoding ({})".format(
                settings.keys["general"]["save_file"]
            )
        )
        self.toolbar_save = gui.templates.widgetgenerator.create_action(
            parent=self.toolbar,
            name="save_button",
            statustip=tooltip,
            tooltip=tooltip,
            icon_path="icons/save/save.png",
            func=special_save_file,
            ribbon_style=data.ribbon_style_toolbar,
            text=" save ",
        )
        self.toolbar_save.setEnabled(False)
        self.toolbar.addAction(self.toolbar_save)

        # $ Save All Button
        tooltip = "Save all modified documents in all windows in the UTF-8 encoding ({})".format(
            settings.keys["general"]["saveas_file"]
        )
        self.toolbar_save_all = gui.templates.widgetgenerator.create_action(
            parent=self.toolbar,
            name="save_all_button",
            statustip=tooltip,
            tooltip=tooltip,
            icon_path="icons/save/save_all.png",
            func=self.save_all,
            ribbon_style=data.ribbon_style_toolbar,
            text=" save all ",
        )
        self.toolbar_save_all.setEnabled(False)
        self.toolbar.addAction(self.toolbar_save_all)

        # Pin configurator
        if data.PINCONFIG_ENABLED:
            self.toolbar.addSeparator()
            self.toolbar_pinconfigurator_button = (
                gui.templates.widgetgenerator.create_action(
                    parent=self.toolbar,
                    name="pinconfigurator_button",
                    statustip="Show the pin configurator",
                    tooltip="Show the pin configurator",
                    icon_path="icons/gen/pinconfig.png",
                    func=self.projects.show_pinconfigurator,
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" config ",
                )
            )
            self.toolbar.addAction(self.toolbar_pinconfigurator_button)
            if not data.current_project.get_chip().get_chip_dict(board=None)[
                "pinconfig_enabled"
            ]:
                text = helpdocs.help_subjects.pinconfig.disabled_text()
                self.toolbar_pinconfigurator_button.set_enabled(False)
                self.toolbar_pinconfigurator_button.setToolTip(text)
                self.toolbar_pinconfigurator_button.setStatusTip(text)
                if isinstance(
                    self.toolbar_pinconfigurator_button, qt.QWidgetAction
                ):
                    self.toolbar_pinconfigurator_button.defaultWidget().setToolTip(
                        text
                    )
                    self.toolbar_pinconfigurator_button.defaultWidget().setStatusTip(
                        text
                    )
                # Disable the statusbar button if needed
                if "pin-configurator" in data.alert_buttons:
                    data.alert_buttons["pin-configurator"].setEnabled(False)
                    data.alert_buttons["pin-configurator"].setToolTip(text)
                    data.alert_buttons["pin-configurator"].setStatusTip(text)

        # Pieces button
        if data.PIECES_ENABLED:
            self.toolbar.addSeparator()

            self.toolbar_pieces_button = (
                gui.templates.widgetgenerator.create_action(
                    parent=self.toolbar,
                    name="pieces_button",
                    statustip="Show the Pieces AI assistant",
                    tooltip="Show the Pieces AI assistant",
                    icon_path="icons/logo/pieces.svg",
                    func=self.projects.show_pieces,
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" pieces ai ",
                )
            )
            self.toolbar.addAction(self.toolbar_pieces_button)

        # New Dashboard button
        if data.NEW_DASHBOARD_ENABLED:
            self.toolbar.addSeparator()

            self.toolbar_new_dashboard_button = (
                gui.templates.widgetgenerator.create_action(
                    parent=self.toolbar,
                    name="new_dashboard_button",
                    statustip="Show the new Dashboard",
                    tooltip="Show the new Dashboard",
                    icon_path="icons/gen/dashboard.svg",
                    func=self.projects.show_new_dashboard,
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" new dashboard ",
                )
            )
            self.toolbar.addAction(self.toolbar_new_dashboard_button)

        # Chip configurator button
        if data.CHIPCONFIGURATOR_ENABLED:
            self.toolbar.addSeparator()

            self.toolbar_chipconfigurator_button = (
                gui.templates.widgetgenerator.create_action(
                    parent=self.toolbar,
                    name="chipconfigurator_button",
                    statustip="Chip Configurator",
                    tooltip="Chip Configurator",
                    icon_path="icons/gen/pinconfig.png",
                    func=self.projects.show_chipconfigurator,
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" chip configurator ",
                )
            )
            self.toolbar.addAction(self.toolbar_chipconfigurator_button)

            if self.initialized == True:
                self.projects.check_chipconfigurator()

        # $ User Buttons
        self.parse_buttons()

        # $ Debugger
        if data.DEBUGGER_ENABLED:
            self.toolbar_debugger_button = (
                gui.templates.widgetgenerator.create_action(
                    parent=self.toolbar,
                    name="debugger_button",
                    statustip="Show the debugger",
                    tooltip="Show the debugger",
                    icon_path="icons/gen/debug.png",
                    func=self.projects.show_debugger,
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" debug ",
                )
            )
            self.toolbar.addAction(self.toolbar_debugger_button)
            if not data.current_project.get_chip().get_chip_dict(board=None)[
                "debugger_enabled"
            ]:
                text = helpdocs.help_subjects.debugging.disabled_text()
                self.toolbar_debugger_button.set_enabled(False)
                self.toolbar_debugger_button.setToolTip(text)
                self.toolbar_debugger_button.setStatusTip(text)
                if isinstance(self.toolbar_debugger_button, qt.QWidgetAction):
                    self.toolbar_debugger_button.defaultWidget().setToolTip(
                        text
                    )
                    self.toolbar_debugger_button.defaultWidget().setStatusTip(
                        text
                    )

            self.toolbar.addSeparator()

        # $ Serial Monitor Button
        def toolbar_serial_monitor_clicked(*args):
            try:
                console = data.main_form.create_console(
                    data.tab_names["serial-console"],
                    console_type=data.ConsoleType.Serial,
                )
            except:
                data.main_form.display.display_error(traceback.format_exc())
                traceback.print_exc()
            return

        # Note from Kristof:
        # I added a space before and after the 'monitor' button text in the ribbon toolbar, to give
        # the button more space.
        self.toolbar_serial_monitor = (
            gui.templates.widgetgenerator.create_action(
                parent=self.toolbar,
                name="serial_monitor_action",
                statustip="Show the serial monitor",
                tooltip="Show the serial monitor",
                icon_path="icons/console/serial_monitor.png",
                func=toolbar_serial_monitor_clicked,
                ribbon_style=data.ribbon_style_toolbar,
                text=" monitor ",
            )
        )
        self.toolbar.addAction(self.toolbar_serial_monitor)

        # $ Flash Port Button
        # Note from Kristof:
        # I added a space before and after the keyword 'flash port' to give the button more space
        # in the ribbon toolbar.
        try:
            self.serial_port = (
                gui.templates.widgetgenerator.create_toolbar_combobox(
                    parent=self.toolbar,
                    name="serial_port_action",
                    statustip="Select the serial port for all communication",
                    tooltip="Select the serial port for all communication",
                    ribbon_style=data.ribbon_style_toolbar,
                    text=" flash port ",
                )
            )
            self.toolbar.addAction(self.serial_port)
            data.serial_port_combobox = self.serial_port.acb
            data.serial_port_combobox.selection_changed_from_to.connect(
                functions.toolbar_comport_selection_changed_from_to
            )
            if (
                serial_port_items is not None
                and serial_port_selected_item is not None
            ):
                self.serial_port.acb.clear()
                for k, v in serial_port_items.items():
                    self.serial_port.acb.add_item(v)
                self.serial_port.acb.set_selected_item(
                    serial_port_selected_item
                )
            # Set visibility based on previous state, if any, else make it visible
            self.serial_port.setVisible(serial_port_visible)
        except:
            traceback.print_exc()

        # $ Last spacer
        spacer = gui.templates.widgetgenerator.create_spacer()
        spacer.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.Preferred,
        )
        self.fill_spacer = self.toolbar.addWidget(spacer)

    def update_toolbar_style(self):
        if self.toolbar is None:
            return
        factor = 1.0
        if data.ribbon_style_toolbar:
            factor = 2.0
        if data.get_toolbar_pixelsize() is not None:
            self.toolbar.setIconSize(
                qt.create_qsize(
                    int(data.get_toolbar_pixelsize() * factor),
                    int(data.get_toolbar_pixelsize() * factor),
                )
            )
        else:
            self.toolbar.setIconSize(
                qt.create_qsize(int(24 * factor), int(24 * factor))
            )
        for a in self.toolbar.actions():
            if isinstance(a, qt.QWidgetAction) and hasattr(a, "resize"):
                a.resize()
            if hasattr(a, "reset_icon"):
                a.reset_icon()

        # Set the toolbar style
        if data.ribbon_style_toolbar:
            self.toolbar.setToolButtonStyle(
                qt.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
            )
        else:
            self.toolbar.setToolButtonStyle(
                qt.Qt.ToolButtonStyle.ToolButtonIconOnly
            )

        self.toolbar.update_style()

        def __resize(*args):
            self.serial_port.acb.adjust_size()

        qt.QTimer.singleShot(10, __resize)

    @qt.pyqtSlot(int, int)
    def progress_report(self, current, total):
        progress_widget = self.progress_widget

        if not progress_widget.has("source-analysis"):
            # Create the progressbar if it doesn't exist yet.
            progress_widget.add(
                name="source-analysis",
                priority=9,
                text="analyzing %v/%m source files",
                minimum=0,
                maximum=total,
                value=current,
            )

        if current == total:
            # Remove the progressbar when maximum has been reached.
            progress_widget.remove("source-analysis")
            # Fire signal
            data.signal_dispatcher.source_analyzer.progress_completed.emit()
            # Reset symbol window symbol cache
            if self.projects.symbols_window is not None:
                self.projects.symbols_window.reset_cursor_symbol()
            # Testing only
            if self.source_analysis_only == True:
                if not hasattr(self, "source_analysis_test"):
                    self.source_analysis_test = True
                    self.__source_analysis_complete()
        else:
            progress_widget.set_value_and_max(
                name="source-analysis",
                value=current,
                maximum=total,
            )
            data.signal_dispatcher.source_analyzer.progress_updated.emit()

    @qt.pyqtSlot(int, int, str)
    def file_tree_initialization_progress_report(self, current, total, text):
        progress_widget = self.progress_widget
        bar_name = "file-tree-initialization"
        if not progress_widget.has(bar_name):
            # Create the progressbar if it doesn't exist yet.
            progress_widget.add(
                name=bar_name,
                priority=9,
                text=text,
                minimum=0,
                maximum=total,
                value=current,
            )

        if current == total:
            # Remove the progressbar when maximum has been reached.
            progress_widget.remove(bar_name)
            # Fire signal
            data.signal_dispatcher.source_analyzer.file_tree_handler_initialization_completed.emit()
        else:
            progress_widget.set_value_and_max(
                name=bar_name,
                value=current,
                maximum=total,
            )

    def __restart_notification_received(self, message):
        if message == "Theme changed":
            text = (
                "Embeetle needs to be restarted in order for all the\n"
                + "theme settings to upgrade. You can continue to use Embeetle,\n"
                + "but some things might not be styled according to the theme\n"
                + "you currently selected."
            )
        else:
            text = message

        def show_popup(*args):
            gui.dialogs.popupdialog.PopupDialog.ok(
                parent=self,
                icon_path="icons/dialog/info.png",
                title_text="WARNING",
                text=text,
            )

        qt.QTimer.singleShot(10, show_popup)

    def __makefile_command_executed(self, target, success):
        if target == "build":
            if success:
                data.signal_dispatcher.program_state_changed.emit(
                    data.ProgramState.Built
                )
        elif target == "flash":
            if success:
                data.signal_dispatcher.program_state_changed.emit(
                    data.ProgramState.Flashed
                )

    def __included_file_edited_check(self, file_abspath):
        result = data.filetree.api.is_file_included(file_abspath)
        if result:
            data.signal_dispatcher.program_state_changed.emit(
                data.ProgramState.Edited
            )

    def __show_manual_hint(
        self, text: str, point: Optional[qt.QPoint] = None
    ) -> None:
        if point is not None:
            position = point
        else:
            position = qt.QCursor.pos()
        qt.QToolTip.showText(position, text, self)

    def __unknown_diagnostic(self):
        self.__show_manual_hint(
            "This error seems to be missing!\n"
            + "If you are editing a document, please save it\n"
            + "in order for the diagnostics to be updates."
        )

    def __change_program_state(self, new_state: data.ProgramState) -> None:
        data.program_state = new_state
        if (
            isinstance(data.alert_labels, dict)
            and "program-state" in data.alert_labels.keys()
        ):
            data.alert_labels["program-state"].setText(new_state.name)
            data.alert_labels["program-state"].setStatusTip(
                "Program is in state: '{}'".format(new_state.name)
            )

    def _init_statusbar(self):
        wg = gui.templates.widgetgenerator

        super()._init_statusbar()

        # Progress widget
        if not hasattr(self, "progress_widget") or self.progress_widget is None:
            self.progress_widget = gui.helpers.progresswidget.ProgressWidget(
                self.statusbar, self
            )
            data.signal_dispatcher.source_analyzer.progress_report.connect(
                self.progress_report
            )
            data.signal_dispatcher.source_analyzer.file_tree_handler_initialization_report.connect(
                self.file_tree_initialization_progress_report
            )
        self.statusbar.addPermanentWidget(self.progress_widget)
        self.progress_widget.hide()

        ## Alert buttons and labels
        _create_button = wg.create_pushbutton
        data.alert_buttons = {}
        data.alert_labels = {}

        # State label
        new_label = wg.create_label(
            text="",
            bold=True,
            parent=self.statusbar,
        )
        self.statusbar.addPermanentWidget(new_label)
        data.alert_labels["program-state"] = new_label
        data.signal_dispatcher.program_state_changed.emit(data.program_state)

        # Source analyzer
        new_button = _create_button(
            parent=self.statusbar,
            name="source-analyzer-statusbar-button",
            tooltip="Show Source Analyzer tab",
            icon_name="icons/gen/source_analyzer.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["source-analyzer"] = new_button
        new_button.released.connect(self.projects.show_sa_tab)
        new_button.released.connect(new_button.popup_hide)

        # Filetree
        new_button = _create_button(
            parent=self.statusbar,
            name="filetree-statusbar-button",
            tooltip="Show Filetree",
            icon_name="icons/gen/tree.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["filetree"] = new_button
        new_button.released.connect(self.projects.show_filetree)
        new_button.released.connect(new_button.popup_hide)

        # Dashboard
        new_button = _create_button(
            parent=self.statusbar,
            name="dashboard-statusbar-button",
            tooltip="Show Dashboard",
            icon_name="icons/gen/dashboard.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["dashboard"] = new_button
        new_button.released.connect(self.projects.show_dashboard)
        new_button.released.connect(new_button.popup_hide)

        # Symbol window
        new_button = _create_button(
            parent=self.statusbar,
            name="symbols-statusbar-button",
            tooltip="Show the symbol window",
            icon_name="icons/gen/balls.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["symbols"] = new_button
        new_button.released.connect(self.projects.show_symbols)
        new_button.released.connect(new_button.popup_hide)

        # Diagnostics
        new_button = _create_button(
            parent=self.statusbar,
            name="diagnostics-statusbar-button",
            tooltip="Show the diagnostics window",
            icon_name="icons/gen/stethoscope.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["diagnostics"] = new_button
        new_button.released.connect(self.projects.show_diagnostics)
        new_button.released.connect(new_button.popup_hide)

        # Terminal
        new_button = _create_button(
            parent=self.statusbar,
            name="terminal-statusbar-button",
            tooltip="Add a terminal emulator",
            icon_name="icons/console/terminal.svg",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["terminal"] = new_button
        new_button.released.connect(self.display.add_terminal)
        new_button.released.connect(new_button.popup_hide)

        # Pin configurator
        #        if data.PINCONFIG_ENABLED:
        #            new_button = _create_button(
        #                parent=self.statusbar,
        #                name='pinconfigurator-statusbar-button',
        #                tooltip='Show the pin-configurator window',
        #                icon_name="icons/gen/pinconfig.svg",
        #                size=(
        #                    data.get_general_icon_pixelsize(),
        #                    data.get_general_icon_pixelsize()
        #                ),
        #                style="transparent",
        #                popup_bubble_parent=self,
        #                no_border=True,
        #            )
        #            self.statusbar.addPermanentWidget(new_button)
        #            data.alert_buttons["pin-configurator"] = new_button
        #            new_button.released.connect(self.projects.show_pinconfigurator)
        #            new_button.released.connect(new_button.popup_hide)

        # Preferences
        new_button = _create_button(
            parent=self.statusbar,
            name="settings-statusbar-button",
            tooltip="Show the preferences window",
            icon_name="icons/gen/gear.png",
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            popup_bubble_parent=self,
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["settings"] = new_button
        new_button.released.connect(self.settings.show_preferences)
        new_button.released.connect(new_button.popup_hide)

        # Debugger

    #        if data.DEBUGGER_ENABLED:
    #            new_button = _create_button(
    #                parent=self.statusbar,
    #                name='debugger-statusbar-button',
    #                tooltip='Show the debugger',
    #                icon_name="icons/gen/debug.png",
    #                size=(
    #                    data.get_general_icon_pixelsize(),
    #                    data.get_general_icon_pixelsize()
    #                ),
    #                style="transparent",
    #                popup_bubble_parent=self,
    #                no_border=True,
    #            )
    #            self.statusbar.addPermanentWidget(new_button)
    #            data.alert_buttons["debugger"] = new_button
    #            new_button.released.connect(self.projects.show_debugger)
    #            new_button.released.connect(new_button.popup_hide)

    def __init_menubar(self):
        """Initialize the menubar ("QAction.triggered.connect" signals first
        parameter is always "checked: bool").

        This is a very long function that should be trimmed sometime!
        """
        self.menubar = self.MenuBar(self)

        # Function for creating menus
        self.menubar.stored_menus = {}

        def add_menubar_menu(name):
            new_menu = gui.templates.basemenu.BaseMenu(name, self.menubar)
            self.menubar.addMenu(new_menu)
            self.menubar.stored_menus[name] = new_menu
            return new_menu

        # ^ =============================[ FILE ]============================= ^#
        def construct_file_menu():
            file_menu = add_menubar_menu("&File")

            #! ----------------------------[ New ]--------------------------- !#
            def special_create_new_file():
                self.file_create_new()

            new_file_action = self.create_action(
                "file-new",
                "New",
                ("general", "new_file"),
                "Create new empty file",
                "Create new empty file",
                f"icons/menu_edit/new_file.png",
                special_create_new_file,
            )
            file_menu.addAction(new_file_action)

            #! ---------------------------[ Open ]--------------------------- !#
            def special_open_file():
                self.file_open()

            open_file_action = self.create_action(
                "file-open",
                "Open",
                ("general", "open_file"),
                "Open file",
                "Open file",
                f"icons/folder/open/file.png",
                special_open_file,
            )
            file_menu.addAction(open_file_action)

            #! -----------------------[ Recent Files ]----------------------- !#
            recent_file_list_menu = self.view.create_recent_file_list_menu()
            file_menu.addMenu(recent_file_list_menu)
            file_menu.addSeparator()

            #! -------------------------[ Save ]------------------------- !#
            def special_save_file(*args):
                self.file_save()

            self.save_file_action = self.create_action(
                "file-save",
                "Save",
                ("general", "save_file"),
                "Save currently focused file",
                "Save currently focused file",
                "icons/save/save.png",
                special_save_file,
                enabled=False,
            )
            file_menu.addAction(self.save_file_action)

            #! -------------------------[ Save All ]------------------------- !#
            self.save_project_action = self.create_action(
                "file-save-all",
                "Save All",
                ("general", "saveas_file"),
                "Save all modified documents in all windows in the UTF-8 encoding",
                "Save all modified documents in all windows in the UTF-8 encoding",
                "icons/save/save_all.png",
                self.save_all,
                enabled=False,
            )
            file_menu.addAction(self.save_project_action)
            file_menu.addSeparator()

            #! ---------------------[ Open Home Window ]--------------------- !#
            open_home_action = self.create_action(
                "open-home-window",
                "Open Home Window",
                None,
                "Open the home window for creating/loading/... projects",
                "Open the home window for creating/loading/... projects",
                "icons/gen/home.png",
                self.open_home_window,
            )
            file_menu.addAction(open_home_action)
            file_menu.addSeparator()

            #! ---------------------------[ Exit ]--------------------------- !#
            exit_action = self.create_action(
                "exit",
                "Exit",
                None,
                "Exit application",
                "Exit application",
                "icons/system/log_out.png",
                self.exit,
            )
            exit_action.setShortcut("Alt+F4")
            file_menu.addAction(exit_action)

        # ^ =============================[ EDIT ]============================= ^#
        # Adding the basic options to the menu
        def construct_edit_basic_menu():
            edit_menu = add_menubar_menu("&Edit")

            #! ----------------------------[ Cut ]--------------------------- !#
            def cut():
                try:
                    self.get_tab_by_focus().cut()
                except:
                    pass

            cut_action = self.create_action(
                "edit-cut",
                "Cut",
                ("editor", "cut"),
                "Cut any selected text in the currently selected window to the clipboard",
                "Cut any selected text in the currently selected window to the clipboard",
                f"icons/menu_edit/cut.png",
                cut,
            )
            edit_menu.addAction(cut_action)

            #! ---------------------------[ Copy ]--------------------------- !#
            def copy():
                try:
                    self.get_tab_by_focus().copy()
                except:
                    traceback.print_exc()

            temp_string = "Copy any selected text in the currently "
            temp_string += "selected window to the clipboard"
            copy_action = self.create_action(
                "edit-copy",
                "Copy",
                ("editor", "copy"),
                temp_string,
                temp_string,
                f"icons/menu_edit/copy.png",
                copy,
            )
            edit_menu.addAction(copy_action)

            #! ---------------------------[ Paste ]-------------------------- !#
            def paste():
                try:
                    self.get_tab_by_focus().paste()
                except:
                    pass

            paste_action = self.create_action(
                "edit-paste",
                "Paste",
                ("editor", "paste"),
                "Paste the text in the clipboard to the currenty selected window",
                "Paste the text in the clipboard to the currenty selected window",
                f"icons/menu_edit/paste.png",
                paste,
            )
            edit_menu.addAction(paste_action)

            #! ---------------------------[ Undo ]--------------------------- !#
            def undo():
                try:
                    self.get_tab_by_focus().undo()
                except:
                    pass

            undo_action = self.create_action(
                "edit-undo",
                "Undo",
                ("editor", "undo"),
                "Undo last editor action in the currenty selected window",
                "Undo last editor action in the currenty selected window",
                f"icons/menu_edit/undo.png",
                undo,
            )
            edit_menu.addAction(undo_action)

            #! ---------------------------[ Redo ]--------------------------- !#
            def redo():
                try:
                    self.get_tab_by_focus().redo()
                except:
                    pass

            redo_action = self.create_action(
                "edit-redo",
                "Redo",
                ("editor", "redo"),
                "Redo last undone editor action in the currenty selected window",
                "Redo last undone editor action in the currenty selected window",
                f"icons/menu_edit/redo.png",
                redo,
            )
            edit_menu.addAction(redo_action)

            #! --------------------------[ Search ]-------------------------- !#
            def find_func():
                self.searchbar.show()

            searchbar_action = self.create_action(
                "edit-search",
                "Search",
                ("general", "find"),
                "Show the search bar",
                "Show the search bar",
                f"icons/menu_edit/find.png",
                find_func,
            )
            edit_menu.addAction(searchbar_action)

            #! --------------------------[ Replace ]------------------------- !#
            def replace_func():
                self.searchbar.show(show_replace=True)

            replace_dialog_action = self.create_action(
                "edit-replace",
                "Replace",
                ("general", "replace_selection"),
                "Show the search/replace/highlight dialog",
                "Show the search/replace/highlight dialog",
                f"icons/menu_edit/replace.png",
                replace_func,
            )
            edit_menu.addAction(replace_dialog_action)
            edit_menu.addSeparator()

            #! ---------------------------[ More ]--------------------------- !#
            self.stored_menus["basic_menu"] = edit_menu.addMenu("Basic")
            basic_menu = self.stored_menus["basic_menu"]
            basic_menu.setIcon(
                iconfunctions.get_qicon("icons/menu_edit/basic.png")
            )

            # * --------------[ More > Indent ]-------------- *#
            def indent():
                try:
                    self.get_tab_by_focus().custom_indent()
                except:
                    pass

            indent_action = self.create_action(
                "edit-indent",
                "Indent",
                ("#", "editor", "indent"),
                "Indent the selected lines by the default width (4 spaces) in the currenty selected window",
                "Indent the selected lines by the default width (4 spaces) in the currenty selected window",
                "icons/menu_edit/indent.png",
                indent,
            )
            basic_menu.addAction(indent_action)

            # * -------------[ More > Unindent ]------------- *#
            def unindent():
                try:
                    self.get_tab_by_focus().custom_unindent()
                except:
                    pass

            unindent_action = self.create_action(
                "edit-unindent",
                "Unindent",
                ("#", "editor", "unindent"),
                "Unindent the selected lines by the default width (4 spaces) in the currenty selected window",
                "Unindent the selected lines by the default width (4 spaces) in the currenty selected window",
                "icons/menu_edit/unindent.png",
                unindent,
            )
            basic_menu.addAction(unindent_action)

            # * ------------[ More > Select All ]------------ *#
            def select_all():
                try:
                    self.get_tab_by_focus().selectAll(True)
                except:
                    pass

            select_all_action = self.create_action(
                "edit-select-all",
                "Select All",
                ("#", "editor", "select_all"),
                "Select all of the text in the currenty selected window",
                "Select all of the text in the currenty selected window",
                f"icons/menu_edit/select_all.png",
                select_all,
            )
            basic_menu.addAction(select_all_action)

            # * -------------[ More > Line Cut ]------------- *#
            def line_cut():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_LINECUT)
                except:
                    pass

            line_cut_action = self.create_action(
                "edit-line-cut",
                "Line Cut",
                ("#", "editor", "line_cut"),
                "Cut out the current line/lines of the currently selected document",
                "Cut out the current line/lines of the currently selected document",
                f"icons/menu_edit/line_cut.png",
                line_cut,
            )
            basic_menu.addAction(line_cut_action)

            # * ------------[ More > Line Copy ]------------- *#
            def line_copy():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_LINECOPY)
                except:
                    pass

            line_copy_action = self.create_action(
                "edit-line-copy",
                "Line Copy",
                ("#", "editor", "line_copy"),
                "Copy the current line/lines of the currently selected document",
                "Copy the current line/lines of the currently selected document",
                f"icons/menu_edit/line_copy.png",
                line_copy,
            )
            basic_menu.addAction(line_copy_action)

            # * -----------[ More > Line Delete ]------------ *#
            def line_delete():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_LINEDELETE)
                except:
                    pass

            line_delete_action = self.create_action(
                "edit-line-delete",
                "Line Delete",
                ("#", "editor", "line_delete"),
                "Delete the current line of the currently selected document",
                "Delete the current line of the currently selected document",
                f"icons/menu_edit/line_delete.png",
                line_delete,
            )
            basic_menu.addAction(line_delete_action)

            # * ----------[ More > Line Transpose ]---------- *#
            def line_transpose():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_LINETRANSPOSE)
                except:
                    pass

            line_transpose_action = self.create_action(
                "edit-line-transpose",
                "Line Transpose",
                ("#", "editor", "line_transpose"),
                "Switch the current line with the line above it of the currently selected document",
                "Switch the current line with the line above it of the currently selected document",
                f"icons/menu_edit/line_transpose.png",
                line_transpose,
            )
            basic_menu.addAction(line_transpose_action)

            # * -----[ More > Line/Selection Duplicate ]----- *#
            def line_duplicate():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    # send_sci_message(qt.QsciScintillaBase.SCI_LINEDUPLICATE)
                    send_sci_message(
                        qt.QsciScintillaBase.SCI_SELECTIONDUPLICATE
                    )
                except:
                    pass

            line_duplicate_action = self.create_action(
                "edit-line-duplicate",
                "Line/Selection Duplicate",
                ("#", "editor", "line_selection_duplicate"),
                "Duplicate the current line/selection of the currently selected document",
                "Duplicate the current line/selection of the currently selected document",
                f"icons/menu_edit/line_copy.png",
                line_duplicate,
            )
            basic_menu.addAction(line_duplicate_action)

            # * ------------[ More > Scroll Up ]------------- *#
            def scroll_up():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_PAGEUP)
                except:
                    pass

            scroll_up_action = self.create_action(
                "edit-scroll-up",
                "Scroll up",
                ("#", "editor", "scroll_up"),
                "Scroll up one page of the currently selected document",
                "Scroll up one page of the currently selected document",
                "icons/menu_edit/scroll_up.png",
                scroll_up,
            )
            basic_menu.addAction(scroll_up_action)

            # * -----------[ More > Scroll Down ]------------ *#
            def scroll_down():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_PAGEDOWN)
                except:
                    pass

            scroll_down_action = self.create_action(
                "edit-scroll-down",
                "Scroll down",
                ("#", "editor", "scroll_down"),
                "Scroll down one page of the currently selected document",
                "Scroll down one page of the currently selected document",
                "icons/menu_edit/scroll_down.png",
                scroll_down,
            )
            basic_menu.addAction(scroll_down_action)

            # * -------[ More > Delete Start of Word ]------- *#
            def delete_start_of_word():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DELWORDLEFT)
                except:
                    pass

            del_start_word_action = self.create_action(
                "edit-delete-start-of-word",
                "Delete start of word",
                ("#", "editor", "delete_start_of_word"),
                "Delete the current word from the cursor to the starting index of the word",
                "Delete the current word from the cursor to the starting index of the word",
                f"icons/menu_edit/delete_start.png",
                delete_start_of_word,
            )
            basic_menu.addAction(del_start_word_action)

            # * --------[ More > Delete End of Word ]-------- *#
            def delete_end_of_word():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DELWORDRIGHT)
                except:
                    pass

            del_end_word_action = self.create_action(
                "edit-delete-end-of-word",
                "Delete end of word",
                ("#", "editor", "delete_end_of_word"),
                "Delete the current word from the cursor to the ending index of the word",
                "Delete the current word from the cursor to the ending index of the word",
                f"icons/menu_edit/delete_end.png",
                delete_end_of_word,
            )
            basic_menu.addAction(del_end_word_action)

            # * -------[ More > Delete Start of Line ]------- *#
            def delete_start_of_line():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DELLINELEFT)
                except:
                    pass

            del_start_line_action = self.create_action(
                "edit-delete-start-of-line",
                "Delete start of line",
                ("#", "editor", "delete_start_of_line"),
                "Delete the current line from the cursor to the starting index of the line",
                "Delete the current line from the cursor to the starting index of the line",
                f"icons/menu_edit/delete_start.png",
                delete_start_of_line,
            )
            basic_menu.addAction(del_start_line_action)

            # * --------[ More > Delete End of Line ]-------- *#
            def delete_end_of_line():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DELLINERIGHT)
                except:
                    pass

            del_end_line_action = self.create_action(
                "edit-delete-end-of-line",
                "Delete end of line",
                ("#", "editor", "delete_end_of_line"),
                "Delete the current line from the cursor to the ending index of the line",
                "Delete the current line from the cursor to the ending index of the line",
                f"icons/menu_edit/delete_end.png",
                delete_end_of_line,
            )
            basic_menu.addAction(del_end_line_action)

            # * -----------[ More > Go to Start ]------------ *#
            def goto_to_start():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DOCUMENTSTART)
                except:
                    pass

            go_to_start_action = self.create_action(
                "edit-goto-start",
                "Go to start",
                ("#", "editor", "go_to_start"),
                "Move cursor up to the start of the currently selected document",
                "Move cursor up to the start of the currently selected document",
                f"icons/menu_edit/goto_start.png",
                goto_to_start,
            )
            basic_menu.addAction(go_to_start_action)

            # * -------------[ More > Go to End ]------------ *#
            def goto_to_end():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DOCUMENTEND)
                except:
                    pass

            go_to_end_action = self.create_action(
                "edit-goto-end",
                "Go to end",
                ("#", "editor", "go_to_end"),
                "Move cursor down to the end of the currently selected document",
                "Move cursor down to the end of the currently selected document",
                f"icons/menu_edit/goto_end.png",
                goto_to_end,
            )
            basic_menu.addAction(go_to_end_action)

            # * ----------[ More > Select Page Up ]---------- *#
            def select_page_up():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_PAGEUPEXTEND)
                except:
                    pass

            select_page_up_action = self.create_action(
                "edit-select-page-up",
                "Select page up",
                ("#", "editor", "select_page_up"),
                "Select text up one page of the currently selected document",
                "Select text up one page of the currently selected document",
                f"icons/menu_edit/select_up.png",
                select_page_up,
            )
            basic_menu.addAction(select_page_up_action)

            # * ---------[ More > Select Page Down ]--------- *#
            def select_page_down():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_PAGEDOWN)
                except:
                    pass

            select_page_down_action = self.create_action(
                "edit-select-page-down",
                "Select page down",
                ("#", "editor", "select_page_down"),
                "Select text down one page of the currently selected document",
                "Select text down one page of the currently selected document",
                f"icons/menu_edit/select_down.png",
                select_page_down,
            )
            basic_menu.addAction(select_page_down_action)

            # * ----------[ More > Select to Start ]--------- *#
            def select_to_start():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(
                        qt.QsciScintillaBase.SCI_DOCUMENTSTARTEXTEND
                    )
                except:
                    pass

            select_to_start_action = self.create_action(
                "edit-select-to-start",
                "Select to start",
                ("#", "editor", "select_to_start"),
                "Select all text up to the start of the currently selected document",
                "Select all text up to the start of the currently selected document",
                f"icons/menu_edit/select_up.png",
                select_to_start,
            )
            basic_menu.addAction(select_to_start_action)

            # * -----------[ More > Select to End ]---------- *#
            def select_to_end():
                try:
                    send_sci_message = self.get_tab_by_focus().SendScintilla
                    send_sci_message(qt.QsciScintillaBase.SCI_DOCUMENTENDEXTEND)
                except:
                    pass

            select_to_end_action = self.create_action(
                "edit-select-to-end",
                "Select to end",
                ("#", "editor", "select_to_end"),
                "Select all text down to the start of the currently selected document",
                "Select all text down to the start of the currently selected document",
                f"icons/menu_edit/select_down.png",
                select_to_end,
            )
            basic_menu.addAction(select_to_end_action)

            # * ----[ More > Rectangular Block Selection ]--- *#
            rect_block_action = self.create_action(
                "edit-select-rectangle",
                "Rectangular block selection\tAlt+Mouse",
                None,
                "Select rectangle using the mouse in the currently selected document",
                "Select rectangle using the mouse in the currently selected document",
                f"icons/menu_edit/select_block.png",
                None,
            )
            basic_menu.addAction(rect_block_action)

            def reset_editor_zoom():
                try:
                    self.get_tab_by_focus()._parent.zoom_reset()
                except:
                    traceback.print_exc()
                return

            reset_scaling_action = self.create_action(
                "edit-reset-zoom",
                "Reset zoom",
                ("general", "reset_zoom"),
                "Reset the editor's zoom",
                "Reset the editor's zoom",
                "icons/menu_view/zoom_reset.png",
                reset_editor_zoom,
            )
            basic_menu.addAction(reset_scaling_action)

            #! -------------------------[ Advanced ]------------------------- !#
            self.stored_menus["edit_advanced_menu"] = edit_menu.addMenu(
                "Advanced"
            )
            edit_advanced_menu = self.stored_menus["edit_advanced_menu"]
            temp_icon = iconfunctions.get_qicon(f"icons/menu_edit/advanced.png")
            edit_advanced_menu.setIcon(temp_icon)
            edit_menu.addMenu(edit_advanced_menu)

            # * -------[ Advanced > Indent to Cursor ]------- *#
            def special_indent_to_cursor():
                try:
                    self.get_tab_by_focus().indent_lines_to_cursor()
                except:
                    pass

            temp_string = (
                "Indent the selected lines to the current cursor position "
            )
            temp_string += "(SPACE ON THE LEFT SIDE OF LINES IS STRIPPED!)"
            indent_to_cursor_action = self.create_action(
                "edit-indent-to-cursor",
                "Indent to cursor",
                ("general", "indent_to_cursor"),
                temp_string,
                temp_string,
                f"icons/menu_edit/indent_to_cursor.png",
                special_indent_to_cursor,
            )
            edit_advanced_menu.addAction(indent_to_cursor_action)

            # * -------[ Advanced > Indent to Cursor ]------- *#
            def special_to_uppercase():
                focused_tab = self.get_used_tab()
                self.editing.convert_to_uppercase(focused_tab._parent.name)

            to_uppercase_action = self.create_action(
                "edit-selection-to-uppercase",
                "Selection to UPPERCASE",
                ("general", "to_uppercase"),
                "Convert selected text to UPPERCASE",
                "Convert selected text to UPPERCASE",
                f"icons/menu_edit/to_upper.png",
                special_to_uppercase,
            )
            edit_advanced_menu.addAction(to_uppercase_action)

            # * -------[ Advanced > Indent to Cursor ]------- *#
            def special_to_lowercase():
                focused_tab = self.get_used_tab()
                self.editing.convert_to_lowercase(focused_tab._parent.name)

            to_lowercase_action = self.create_action(
                "edit-selection-to-lowercase",
                "Selection to lowercase",
                ("general", "to_lowercase"),
                "Convert selected text to lowercase",
                "Convert selected text to lowercase",
                f"icons/menu_edit/to_lower.png",
                special_to_lowercase,
            )
            edit_advanced_menu.addAction(to_lowercase_action)

            # * -----[ Advanced > Reload File from Disk ]---- *#
            def find_matching_brace():
                try:
                    self.get_tab_by_focus().find_matching_brace()
                except:
                    pass

            find_matching_brace_action = self.create_action(
                "edit-find-matching-brace",
                "Find matching brace",
                ("general", "find_brace"),
                "Find the matching braces if one is selected",
                "Find the matching braces if one is selected",
                "icons/menu_edit/to_matching_brace.png",
                find_matching_brace,
            )
            edit_advanced_menu.addAction(find_matching_brace_action)

            # * -----[ Advanced > Reload File from Disk ]---- *#
            def reload_file():
                try:
                    self.get_tab_by_focus().reload_file()
                except:
                    pass

            reload_file_action = self.create_action(
                "edit-reload-file-from-disk",
                "Reload File from Disk",
                ("general", "reload_file"),
                "Reload file from disk, will prompt if file contains changes",
                "Reload file from disk, will prompt if file contains changes",
                f"icons/menu_edit/reload_file.png",
                reload_file,
            )
            edit_advanced_menu.addAction(reload_file_action)

            # * ------[ Advanced > Comment/Uncomment ]------- *#
            def comment_uncomment():
                try:
                    self.get_tab_by_focus().toggle_comment_uncomment()
                except Exception as ex:
                    functions.echo(ex)

            toggle_comment_action = self.create_action(
                "edit-comment-uncomment",
                "Comment/Uncomment",
                ("general", "toggle_comment"),
                "Toggle comments for the selected lines or single line in the currently selected document",
                "Toggle comments for the selected lines or single line in the currently selected document",
                f"icons/menu_edit/comment.png",
                comment_uncomment,
            )
            edit_advanced_menu.addAction(toggle_comment_action)

            # * ----[ Advanced > Convert Tabs to Spaces ]---- *#
            def tabs_to_spaces():
                try:
                    self.get_tab_by_focus().tabs_to_spaces()
                except Exception as ex:
                    functions.echo(ex)

            tabs_to_spaces_action = self.create_action(
                "edit-tabs-to-spaces",
                "Convert Tabs to Spaces",
                None,
                "Convert all tabs in the editor to spaces",
                "Convert all tabs in the editor to spaces",
                f"icons/menu_edit/convert_tabs.png",
                tabs_to_spaces,
            )
            edit_advanced_menu.addAction(tabs_to_spaces_action)

        # ^ =============================[ VIEW ]============================= ^#
        def construct_view_menu():
            view_menu = add_menubar_menu("&View")

            #! ------------------------[ Scaling ]--------------------------- !#
            #            def show_scaling_dialog():
            #                self.display.dialog_show('scaling_dialog')
            #            scaling_action = self.create_action(
            #                "view-scaling",
            #                'Scaling',
            #                None,
            #                'Show the dialog for scaling the look of Embeetle',
            #                'Show the dialog for scaling the look of Embeetle',
            #                'icons/menu_view/zoom.png',
            #                show_scaling_dialog
            #            )
            #            view_menu.addAction(scaling_action)
            #            view_menu.addSeparator()

            def restore_default_layout():
                self.view.layout_restore(
                    settings.SettingsFileManipulator.layout,
                    data.current_project.get_proj_rootpath(),
                )

            reset_layout_action = self.create_action(
                "view-restore-layout",
                "Restore default layout",
                None,
                "Restore the default layout",
                "Restore the default layout",
                "icons/menu_view/reset.png",
                restore_default_layout,
            )
            view_menu.addAction(reset_layout_action)

            # Preferences
            def show_preferences():
                self.settings.show_preferences()

            show_preferences_action = self.create_action(
                "edit-show-preferences",
                "Preferences",
                None,
                "Show the preferences window",
                "Show the preferences window",
                "icons/gen/gear.png",
                show_preferences,
            )
            view_menu.addAction(show_preferences_action)

            # Separator
            view_menu.addSeparator()

            #! ----------------------[ Show Filetree ]----------------------- !#
            def show_filetree():
                self.projects.show_filetree()

            self.show_filetree_action = self.create_action(
                "view-show-filetree",
                "Filetree",
                None,
                "Show the project filetree",
                "Show the project filetree",
                "icons/gen/tree.png",
                show_filetree,
            )
            view_menu.addAction(self.show_filetree_action)

            #! ------------------[ Show Project Dashboard ]------------------ !#
            def show_dashboard():
                self.projects.show_dashboard()

            self.show_dashboard_action = self.create_action(
                "view-show-dashboard",
                "Dashboard",
                None,
                "Show the project dashboard",
                "Show the project dashboard",
                "icons/gen/dashboard.png",
                show_dashboard,
            )
            view_menu.addAction(self.show_dashboard_action)

            #! -------------------[ Show Project SA Tab ]-------------------- !#
            def show_sa_tab():
                self.projects.show_sa_tab()

            self.show_sa_tab_action = self.create_action(
                "view-show-satab",
                "Source Analyzer",
                None,
                "Show the source analyzer",
                "Show the source analyzer",
                "icons/gen/source_analyzer.png",
                show_sa_tab,
            )
            view_menu.addAction(self.show_sa_tab_action)

            #! ---------------------[ Show Diagnostics ]--------------------- !#
            def show_diagnostics():
                self.projects.show_diagnostics()

            self.show_diagnostics_action = self.create_action(
                "view-show-diagnostics",
                "Diagnostics",
                None,
                "Show the diagnostics window",
                "Show the diagnostics window",
                "icons/gen/stethoscope.png",
                show_diagnostics,
            )
            view_menu.addAction(self.show_diagnostics_action)

            #! --------------------[ Show Symbol Window ]-------------------- !#
            def show_symbols():
                self.projects.show_symbols()

            self.show_symbols_action = self.create_action(
                "view-show-symbol-window",
                "Symbol Window",
                None,
                "Show the symbol window",
                "Show the symbol window",
                "icons/gen/balls.png",
                show_symbols,
            )
            view_menu.addAction(self.show_symbols_action)

            # Debugger
            if data.DEBUGGER_ENABLED:

                def show_debugger():
                    self.projects.show_debugger()

                self.show_debugger_action = self.create_action(
                    "view-show-debugger",
                    "Debugger",
                    None,
                    "Show the debugging window",
                    "Show the debugging window",
                    "icons/gen/debug.png",
                    show_debugger,
                )
                view_menu.addAction(self.show_debugger_action)

            # Pin configurator
            if data.PINCONFIG_ENABLED:

                def show_pinconfigurator():
                    self.projects.show_pinconfigurator()

                self.show_pinconfigurator_action = self.create_action(
                    "view-show-pinconfigurator-window",
                    "Configurator",
                    None,
                    "Show the configurator window",
                    "Show the configurator window",
                    "icons/gen/pinconfig.png",
                    show_pinconfigurator,
                )
                view_menu.addAction(self.show_pinconfigurator_action)

            # Pieces AI assistant
            if data.PIECES_ENABLED:

                def show_pieces():
                    self.projects.show_pieces()

                self.show_pieces_action = self.create_action(
                    "view-show-pieces-window",
                    "Pieces AI Assistant",
                    None,
                    "Show the Pieces AI window",
                    "Show the Pieces AI window",
                    "icons/logo/pieces.png",
                    show_pieces,
                )
                view_menu.addAction(self.show_pieces_action)

            # New Dashboard
            if data.NEW_DASHBOARD_ENABLED:

                def show_new_dashboard():
                    self.projects.show_new_dashboard()

                self.show_new_dashboard_action = self.create_action(
                    "view-show-new-dashboard-window",
                    "New Dashboard",
                    None,
                    "Show the new Dashboard",
                    "Show the new Dashboard",
                    "icons/gen/dashboard.png",
                    show_new_dashboard,
                )
                view_menu.addAction(self.show_new_dashboard_action)

            # Chip configurator
            if data.CHIPCONFIGURATOR_ENABLED:

                def show_chipconfigurator():
                    self.projects.show_chipconfigurator()

                self.show_chipconfigurator_action = self.create_action(
                    "view-show-chipconfigurator-window",
                    "Chip Configurator",
                    None,
                    "Show the Chip Configurator",
                    "Show the Chip Configurator",
                    "icons/gen/pinconfig.png",
                    show_chipconfigurator,
                )
                view_menu.addAction(self.show_chipconfigurator_action)

            # Terminal
            def show_terminal():
                self.display.add_terminal()

            self.show_terminal_action = self.create_action(
                "view-show-terminal",
                "Terminal",
                None,
                "Add a new terminal emulator",
                "Add a new terminal emulator",
                "icons/console/terminal.svg",
                show_terminal,
            )
            view_menu.addAction(self.show_terminal_action)

            # Messages window
            def show_messages():
                self.display.show_messages_window()

            show_messages_action = self.create_action(
                "edit-show-messages",
                "Messages",
                None,
                "Show the messages window",
                "Show the messages window",
                "icons/dialog/message.png",
                show_messages,
            )
            view_menu.addAction(show_messages_action)

            # Separator
            view_menu.addSeparator()

            #! --------------------[ Maximize/Normalize ]-------------------- !#
            maximize_window_action = self.create_action(
                "view-maximize-normalize",
                "Maximize/Normalize",
                ("general", "maximize_window"),
                "Maximize/Normalize application window",
                "Maximize/Normalize application window",
                "icons/menu_view/fullscreen.png",
                self.view.toggle_window_size,
            )
            view_menu.addAction(maximize_window_action)
            view_menu.addSeparator()

            #! ----------------------[ Close Current Tabs ]---------------------- !#
            def close_tab():
                try:
                    current_window = self.get_window_by_indication()
                    if current_window is not None:
                        current_index = current_window.currentIndex()
                        if current_index > -1:
                            current_window.close_tab(current_index)
                            self.view.indicate_window(current_window)
                except:
                    self.display.display_error(traceback.format_exc())

            close_all_action = self.create_action(
                "view-close-tab",
                "Close Current Tab",
                ("general", "close_tab"),
                "Close currently selected tab",
                "Close currently selected tab",
                "icons/tab/close_tab.png",
                close_tab,
            )
            view_menu.addAction(close_all_action)

            #! ----------------------[ Close All Tabs ]---------------------- !#
            close_all_action = self.create_action(
                "view-close-all",
                "Close All Tabs",
                None,
                "Close all tabs in all windows",
                "Close all tabs in all windows",
                "icons/tab/close_all_tabs.png",
                self.close_all_tabs,
            )
            view_menu.addAction(close_all_action)

            #! ------------------------[ Bookmarks ]------------------------- !#
            self.stored_menus["bookmark_menu"] = (
                gui.templates.basemenu.BaseMenu("&Bookmarks", view_menu)
            )
            bookmark_menu = self.stored_menus["bookmark_menu"]
            temp_icon = iconfunctions.get_qicon(
                f"icons/menu_edit/bookmarks.png"
            )
            bookmark_menu.setIcon(temp_icon)
            self.bookmark_menu = bookmark_menu
            #            view_menu.addSeparator()
            #            view_menu.addMenu(bookmark_menu)

            # * -----[ Bookmarks > Toggle Bookmark ]-----*#
            def bookmark_toggle():
                try:
                    self.get_tab_by_focus().bookmarks.toggle()
                except:
                    pass

            bookmark_toggle_action = self.create_action(
                "view-bookmark-toggle",
                "Toggle Bookmark",
                ("general", "bookmark_toggle"),
                "Toggle a bookmark at the current document line",
                "Toggle a bookmark at the current document line",
                f"icons/menu_edit/bookmarks.png",
                bookmark_toggle,
            )

            # * -----[ Bookmarks > Clear Bookmarks ]-----*#
            def bookmarks_clear():
                self.bookmarks.clear()

            bookmark_clear_action = self.create_action(
                "view-bookmarks-clear",
                "Clear Bookmarks",
                None,
                "Clear Bookmarks",
                "Clear Bookmarks",
                f"icons/menu_edit/bookmarks_clear.png",
                bookmarks_clear,
            )

            # * ----------[ Bookmarks > Go To ]----------*#
            def bookmark_goto(number):
                self.bookmarks.goto(number)

            self.menubar_functions["bookmark_goto"] = bookmark_goto
            bookmark_goto_menu = bookmark_menu.addMenu("Go To")
            temp_icon = iconfunctions.get_qicon(
                f"icons/menu_edit/bookmarks_goto.png"
            )
            bookmark_goto_menu.setIcon(temp_icon)

            # * ----------[ Bookmarks > Store ]----------*#
            def bookmark_store(number):
                try:
                    current_tab = self.get_tab_by_focus()
                    current_line = current_tab.getCursorPosition()[0] + 1
                    self.bookmarks.add_mark_by_number(
                        current_tab, current_line, number
                    )
                except:
                    pass

            bookmark_store_menu = bookmark_menu.addMenu("Store")
            temp_icon = iconfunctions.get_qicon(
                f"icons/menu_edit/bookmarks_store.png"
            )
            bookmark_store_menu.setIcon(temp_icon)

            # * ---[ Fill 'Go To' & 'Store' entries ]----*#
            bookmark_menu.addAction(bookmark_toggle_action)
            bookmark_menu.addAction(bookmark_clear_action)
            bookmark_menu.addSeparator()
            for i in range(10):
                # $ Go To
                def create_goto_bookmark():
                    func = functools.partial(bookmark_goto, i)
                    func.__name__ = "bookmark_goto_{}".format(i)
                    return func

                bookmark_goto_action = self.create_action(
                    "view-bookmark-goto-{:d}".format(i),
                    "Bookmark Goto {:d}".format(i),
                    ("general", "bookmark_goto", i),
                    "Go to bookmark number:{:d}".format(i),
                    "Go to bookmark number:{:d}".format(i),
                    f"icons/menu_edit/bookmarks_goto.png",
                    create_goto_bookmark(),
                )
                bookmark_goto_menu.addAction(bookmark_goto_action)

                # $ Store
                def create_store_bookmark():
                    func = functools.partial(bookmark_store, i)
                    func.__name__ = "bookmark_store_{}".format(i)
                    return func

                bookmark_store_action = self.create_action(
                    "view-bookmark-store-{:d}".format(i),
                    "Bookmark Store {:d}".format(i),
                    ("general", "bookmark_store", i),
                    "Store bookmark number:{:d}".format(i),
                    "Store bookmark number:{:d}".format(i),
                    f"icons/menu_edit/bookmarks_store.png",
                    create_store_bookmark(),
                )
                bookmark_store_menu.addAction(bookmark_store_action)

        # ^ ===========================[ LIBRARIES ]========================== ^#
        def construct_libraries_menu():
            libraries_menu = add_menubar_menu("&Libraries")

            #! ----------------------[ Library Wizard ]---------------------- !#
            def show_library_wizard():
                if (
                    (data.libman_wizard is not None)
                    and (not data.libman_wizard.is_dead())
                    and (not qt.sip.isdeleted(data.libman_wizard))
                ):
                    data.libman_wizard.raise_()
                else:
                    data.libman_wizard = (
                        wizards.lib_wizard.lib_wizard.LibWizard(
                            parent=None,
                            callback=None,
                            callbackArg=None,
                        )
                    )
                    data.libman_wizard.show()
                return

            library_wizard_action = self.create_action(
                "library-manager-open",
                "Library Manager",
                None,
                "Open the library manager to add new libraries",
                "Open the library manager to add new libraries",
                "icons/gen/book.png",
                show_library_wizard,
            )
            libraries_menu.addAction(library_wizard_action)

            #! --------------------[ Add Zipped Library ]-------------------- !#
            def add_zipped_library():
                if data.libman_zipwizard is None:
                    data.libman_zipwizard = (
                        wizards.zipped_lib_wizard.zipped_lib_wizard.ZippedLibWizard()
                    )
                data.libman_zipwizard.show()
                return

            add_zipped_library_action = self.create_action(
                "library-add-library-from-zip",
                "Add Library from Zipfile",
                None,
                "Add a zipped library to this project",
                "Add a zipped library to this project",
                "icons/folder/closed/zip.png",
                add_zipped_library,
            )
            libraries_menu.addAction(add_zipped_library_action)
            return

        # ^ =============================[ HELP ]============================= ^#
        def construct_help_menu():
            help_menu = add_menubar_menu("&Help")

            def show_about():
                helpdocs.help_texts.about(self)
                return

            def open_online_manual():
                url = (
                    f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual"
                )
                webbrowser.open(url)
                return

            online_help_action = self.create_action(
                "help-online-manual",
                "Online manual",
                None,
                "Open the online manual in the default web browser.",
                "Open the online manual in the default web browser.",
                "icons/gen/world.png",
                open_online_manual,
            )
            help_menu.addAction(online_help_action)
            about_action = self.create_action(
                "help-about-embeetle",
                "About Embeetle",
                None,
                "Embeetle Information",
                "Embeetle Information",
                "icons/dialog/help.png",
                show_about,
            )
            help_menu.addAction(about_action)
            return

        # ^ ============================[ TESTING ]=========================== ^#
        def construct_test_menu():
            test_menu = self.menubar.addMenu("&Testing")

            #! --------------------[ Window System Test ]-------------------- !#
            def reindex():
                # self.view.reindex_all_windows()
                # main = self.findChild(gui.forms.thebox.TheBox, "Main")
                # children = main.get_child_boxes()
                # import pprint
                # pprint.pfunctions.echo(children)
                # json_layout = json.dumps(children, indent=4)
                # functions.echo(json_layout)
                functions.echo(self.view.layout_generate())

            test_0 = self.create_action(
                None,
                "Window System Test",
                None,
                "Window System Test",
                "Window System Test",
                "icons/dialog/help.png",
                reindex,
            )
            test_menu.addAction(test_0)

            def dashboard_test():
                parent = data.dashboard.get_parent()
                parent.tab_button_show(data.dashboard, "save")
                parent.tab_button_show(data.dashboard, "close")

            test_1 = self.create_action(
                "print-dashboard-parent",
                "Dashboard test",
                None,
                "Dashboard test",
                "Dashboard test",
                "icons/dialog/help.png",
                dashboard_test,
            )
            test_menu.addAction(test_1)

        # ---------------------------------------- #
        #           CONSTRUCT ALL MENUS            #
        # ---------------------------------------- #
        construct_file_menu()
        construct_edit_basic_menu()
        construct_view_menu()
        construct_libraries_menu()
        construct_help_menu()
        if data.debug_mode:
            construct_test_menu()
        self.setMenuBar(self.menubar)

    def __init_widgets(self):
        self.main_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                name="MainGroupBox",
                borderless=True,
            )
        )
        init_box = gui.forms.thebox.TheBox(
            "", "Main", qt.Qt.Orientation.Horizontal, self, self
        )
        self.main_groupbox.layout().addWidget(init_box)
        self.setCentralWidget(self.main_groupbox)
        self.centralWidget().setMinimumSize(*self.MINIMUM_SIZE)
        self.stored_widgets = {}
        self.symbol_popup = gui.helpers.symbolpopup.SymbolPopup(
            self, self, None
        )

        # Popup box
        self.__init_messages_window()

    def __init_messages_window(self):
        # Add the messages window
        self.display.messages_window = gui.forms.messagewindow.MessageWindow(
            self, self
        )
        self.display.messages_window.setVisible(False)

        # Add popup-box show/hide button
        new_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self.statusbar,
            icon_name="icons/dialog/message.png",
            tooltip="Show the messages window",
            click_func=self.display.show_messages_window,
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            style="transparent",
            no_border=True,
        )
        self.statusbar.addPermanentWidget(new_button)
        data.alert_buttons["messages"] = new_button

        # Set statusbar layout options
        self.statusbar.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.statusbar.layout().setContentsMargins(0, 0, 0, 0)

    def __init_searchbar(self):
        # Searchbar
        self.searchbar = gui.helpers.searchbar.SearchBar(self)
        self.searchbar.escape_pressed.connect(self.searchbar.hide)
        self.main_groupbox.layout().addWidget(self.searchbar)
        self.searchbar.hide()

    def create_new(self, tab_name=None, tab_widget=None):
        """Creates an empty scintilla document using a generator counter."""
        # Set the new tab name
        if tab_name is None:
            tab_name = "new_" + str(next(self.new_file_count))
        return_widget = self.get_largest_window().editor_add_document(
            tab_name, type="new"
        )
        # Set focus to the new widget
        return_widget.setFocus()
        # Return the widget reference
        return return_widget

    def create_console(
        self,
        console_name: str,
        console_type: data.ConsoleType,
        in_tab_widget: Optional[object] = None,
    ) -> object:
        working_directory = data.current_project.get_proj_rootpath()
        os.chdir(working_directory)
        new_console = self.get_tab_by_name(console_name)
        if new_console is not None:
            console_tab = self.get_tab_by_name(console_name)
            if console_tab:
                new_console = console_tab
            else:
                new_console = None
        if new_console is None:
            # Create the console and pass it to the project compiler
            if in_tab_widget is not None:
                tabs = in_tab_widget
            else:
                tabs = self.get_largest_window()
            new_console = tabs.console_add(
                tab_name=console_name, console_type=console_type
            )
        new_console.parent().setCurrentWidget(new_console)
        return new_console

    def open_file_with_dialog(self, tab_widget=None):
        """Open a file for editing using a file dialog."""
        # Create and show a file dialog window, restore last browsed directory and set the file filter
        file_dialog = qt.QFileDialog
        files = file_dialog.getOpenFileNames(
            self,
            "Open File",
            self.last_browsed_dir,
            "All Files (*);;Embeetle Files({:s})".format(
                " ".join(self.exco_file_exts)
            ),
        )
        # Check and then add the selected file to the main gui.forms.tabwidget.TabWidget if the window parameter is unspecified
        self.open_files(files, tab_widget)

    def open_files(self, files=None, tab_widget=None):
        """Open valid files always in the main window."""
        # Check if the files are valid
        if files is None or files == "":
            return
        largest_window = self.get_largest_window()
        if isinstance(files, str):
            # Single file
            self.open_file(files, largest_window)
        else:
            # List of files
            for file in files:
                self.open_file(file, largest_window)

    def open_file(
        self, file=None, tab_widget=None, save_layout=True, focus_tab=False
    ):
        """Read file contents into a gui.forms.tabwidget.TabWidget."""

        def open_file_function(in_file, tab_widget):
            # Check if file exists
            if os.path.isfile(in_file) == False:
                if "embeetle.py" in in_file.lower():
                    return
                self.display.display_message_with_type(
                    "File: {:s}\ndoesn't exist!".format(in_file),
                    message_type=data.MessageType.ERROR,
                )
                return

            # Check the file size
            file_size = functions.get_file_size_Mb(in_file)
            if file_size > 50:
                # Create the warning message
                warning = "The file is larger than 50 MB! ({:d} MB)\n".format(
                    int(file_size)
                )
                warning += "A lot of RAM will be needed!\n"
                warning += (
                    "Files larger than 300 MB can cause the system to hang!\n"
                )
                warning += "Are you sure you want to open it?"
                reply = gui.dialogs.popupdialog.PopupDialog.warning(
                    warning, parent=self
                )
                if reply != qt.QMessageBox.StandardButton.Yes:
                    return

            # Check if the file is open in any window
            tab = self.get_tab_by_save_name(in_file)
            if tab:
                tab._parent.setCurrentWidget(tab)
                self.view.indicate_window(tab._parent)
                tab.set_symbol_analysis()
                return

            # Check selected window
            if tab_widget is None:
                tab_widget = self.get_largest_window()
                # Special window selection process
                pass

            # Check if file is already open
            index = self.check_open_file(in_file, tab_widget)
            if index is not None:
                tab_widget.setCurrentIndex(index)
                tab_widget.currentWidget().set_symbol_analysis()
                return

            # Add new scintilla document tab to the tab widget
            try:
                new_tab = tab_widget.editor_add_document(
                    in_file, "file", bypass_check=False
                )
            except Exception as ex:
                self.display.display_error(traceback.format_exc())
                return

            if new_tab is not None:
                try:
                    # Set the icon if it was set by the lexer
                    new_tab.icon_manipulator.update_icon(new_tab)
                    # Read the whole file and display the text
                    file_text = functions.read_file_to_string(in_file)
                    # Remove the NULL characters
                    if "\0" in file_text:
                        # Use append, it does not remove the NULL characters
                        new_tab.append(file_text)
                        # Display a warning that the text has NULL characters
                        message = "CAUTION: NULL ('\\0') characters in file:\n'{}'".format(
                            in_file
                        )
                        self.display.display_warning(message)
                    else:
                        new_tab.setText(file_text)
                        new_tab.enable_edit_callbacks()
                    tab_widget.indication_set()
                except MemoryError:
                    message = "Insufficient memory to open the file!"
                    self.display.display_message_with_type(
                        message, message_type=data.MessageType.ERROR
                    )
                    self.display.write_to_statusbar(message, 10000)
                    tab_widget.widget(tab_widget.currentIndex()).setParent(None)
                    tab_widget.removeTab(tab_widget.currentIndex())
                    return None
                except:
                    message = traceback.format_exc()
                    self.display.display_error(message)
                    self.display.write_to_statusbar(message, 10000)
                    tab_widget.widget(tab_widget.currentIndex()).setParent(None)
                    tab_widget.removeTab(tab_widget.currentIndex())
                    return None
                # Reset the changed status of the current tab,
                # because adding the file content line by line was registered as a text change
                tab_widget.reset_text_changed()
                # Update the settings manipulator with the new file
                self.settings.update_recent_files_list(in_file)
                # Update the current working directory
                path = os.path.dirname(in_file)
                if path == "":
                    path = data.beetle_core_directory
                self.set_cwd(path)
                # Set focus to the newly opened document
                current_widget = tab_widget.currentWidget()
                current_widget.setFocus()
                if hasattr(current_widget, "set_symbol_analysis"):
                    current_widget.set_symbol_analysis()
                # Indicate the window
                self.view.indicate_window(tab_widget)
                # Update the Save/SaveAs buttons in the menubar
                self.set_save_file_state(True)
            else:
                message = "File cannot be read!\n"
                message += "It's probably not a text file!"
                self.display.display_message_with_type(
                    message, message_type=data.MessageType.ERROR
                )
                self.display.write_to_statusbar("File cannot be read!", 3000)
                tab_widget = None
            if save_layout == True:
                self.view.layout_save()
            return tab_widget

        if isinstance(file, str) == True:
            if file is not None and file != "":
                open_file_function(file, tab_widget)
                self.repaint()
                functions.process_events()
        elif isinstance(file, list) == True:
            for f in file:
                open_file_function(f, tab_widget)
                self.repaint()
                functions.process_events()
        else:
            self.display.display_message_with_type(
                "Unknown parameter type to 'open file' function!",
                message_type=data.MessageType.ERROR,
            )

    def open_home_window_old(self):
        if hasattr(self, "open_home_lock") == False:
            self.open_home_lock = False
        if self.open_home_lock == True:
            return
        self.open_home_lock = True
        try:
            self.receive_queue_clear()

            self.send("show-home-window")
            self.display.write_to_statusbar(
                "Waiting for response from the Home window ...", 4000
            )
            for i in range(10):
                # Test if home window returned a response
                qt.QCoreApplication.processEvents()
                time.sleep(0.05)
                try:
                    _from, _message = self.receive_queue.get_nowait()
                    if _message == "home-window-shown":
                        break
                except queue.Empty:
                    pass
            else:
                # Home window is not alive, create a new one
                arguments = []
                if self.command_line_options.new_mode:
                    arguments.append("-n")
                if self.command_line_options.debug_mode:
                    arguments.append("-d")
                functions.open_embeetle(arguments)
                self.display.write_to_statusbar(
                    "Opening the Home window ...", 4000
                )

            self.receive_queue_clear()
        finally:
            self.open_home_lock = False

    def open_home_window(self):
        self.receive_queue_clear()

        self.send("show-home-window")
        self.display.write_to_statusbar(
            "Waiting for response from the Home window ...", 4000
        )
        for i in range(10):
            # Test if home window returned a response
            qt.QCoreApplication.processEvents()
            time.sleep(0.05)
            try:
                _from, _message = self.receive_queue.get_nowait()
                if _message == "home-window-shown":
                    break
            except queue.Empty:
                pass
        else:
            # Home window is not alive, create a new one
            arguments = []
            if self.command_line_options.new_mode:
                arguments.append("-n")
            if self.command_line_options.debug_mode:
                arguments.append("-d")
            functions.open_embeetle(arguments)
            self.display.write_to_statusbar("Opening the Home window ...", 4000)

        self.receive_queue_clear()

    def check_open_file(self, file_with_path, tab_widget):
        """Check if a file is already open in one of the windows."""
        found_index = None
        # Change the windows style path to the Unix style
        file_with_path = file_with_path.replace("\\", "/")
        # Loop through all of the documents in the tab widget
        for i in range(tab_widget.count()):
            # Check the file name and file name with path
            if (
                tab_widget.widget(i).name == os.path.basename(file_with_path)
                and tab_widget.widget(i).save_name == file_with_path
            ):
                # If the file is already open, get its index in the tab widget
                found_index = i
                break
        return found_index

    def check_unsaved_files(self):
        for win in self.get_all_windows():
            for i in range(win.count()):
                if isinstance(
                    win.widget(i), gui.forms.customeditor.CustomEditor
                ):
                    if win.widget(i).save_status != data.FileStatus.OK:
                        return True
        return False

    def close_all_tabs(self):
        """Clear all documents from the main and upper window."""
        # Check if there are any modified documents
        if self.check_document_states() == True:
            message = "You have unsaved changes!\nWhat do you wish to do?"
            buttons = [
                ("Save && Close all", "save-and-close"),
                ("Close", "close"),
                ("Cancel", "cancel"),
            ]
            reply = gui.dialogs.popupdialog.PopupDialog.custom_buttons(
                message, parent=self, buttons=buttons, text_centered=True
            )
            if reply[0] == "cancel":
                return
            elif reply[0] == "save-and-close":
                self.save_all()
            elif reply[0] == "close":
                pass
        if self.check_dashboard_state() == True:
            message = "You have unsaved changes!\nClose all tabs?"
            reply = gui.dialogs.popupdialog.PopupDialog.question(
                message, parent=self
            )
            if reply == qt.QMessageBox.StandardButton.No:
                return

        # Close all tabs and remove all bookmarks from them
        def close_window_tabs(window):
            delete_list = []
            for i in range(window.count()):
                widget = window.widget(i)
                if (
                    data.current_project is not None
                    and isinstance(widget, gui.forms.newfiletree.NewFiletree)
                    == True
                    or isinstance(widget, gui.forms.messagewindow.MessageWindow)
                    == True
                    or isinstance(
                        widget, gui.helpers.diagnosticwindow.DiagnosticWindow
                    )
                    == True
                    or isinstance(widget, gui.helpers.symbolwindow.SymbolWindow)
                    == True
                    or isinstance(widget, dashboard.chassis.dashboard.Dashboard)
                    == True
                    or isinstance(widget, sa_tab.chassis.sa_tab.SATab) == True
                ):
                    continue
                if isinstance(
                    window.widget(i), gui.forms.customeditor.CustomEditor
                ):
                    self.bookmarks.remove_editor_all(window.widget(i))
                delete_list.append(i)
            for i in reversed(delete_list):
                window.close_tab(i)

        for w in self.get_all_windows():
            close_window_tabs(w)
        # Force a garbage collection cycle
        gc.collect()

    def close_file(self, file_path):
        # Close all tabs and remove all bookmarks from them
        def close_file_in_window(window):
            delete_list = []
            compare_file = functions.unixify_path(file_path)
            for i in range(window.count()):
                widget = window.widget(i)
                if isinstance(widget, gui.forms.customeditor.CustomEditor):
                    file = functions.unixify_path(widget.save_name)
                    if file == compare_file:
                        self.bookmarks.remove_editor_all(widget)
                        delete_list.append(i)
            for i in reversed(delete_list):
                window.close_tab(i)

        for w in self.get_all_windows():
            close_file_in_window(w)

    def close_directory(self, directory_path):
        # Close all tabs and remove all bookmarks from them
        def close_file_in_window(window):
            delete_list = []
            compare_directory = functions.unixify_path(directory_path)
            for i in range(window.count()):
                widget = window.widget(i)
                if isinstance(widget, gui.forms.customeditor.CustomEditor):
                    file = functions.unixify_path(widget.save_name)
                    if compare_directory in file:
                        self.bookmarks.remove_editor_all(widget)
                        delete_list.append(i)
            for i in reversed(delete_list):
                window.close_tab(i)

        for w in self.get_all_windows():
            close_file_in_window(w)

    def rename_file(self, old_path, new_path):
        def rename_file_in_window(window):
            for i in range(window.count()):
                widget = window.widget(i)
                if isinstance(widget, gui.forms.customeditor.CustomEditor):
                    current_path = functions.unixify_path(widget.save_name)
                    if current_path == old_path:
                        widget.save_name = new_path
                        window.setTabText(i, os.path.basename(new_path))
                        self.display.display_warning(
                            "Renamed:\n    {}\n  to:\n    {}".format(
                                current_path, new_path
                            )
                        )

        for w in self.get_all_windows():
            rename_file_in_window(w)

    def rename_directory(self, old_path, new_path):
        def rename_dir_in_window(window):
            for i in range(window.count()):
                widget = window.widget(i)
                if isinstance(widget, gui.forms.customeditor.CustomEditor):
                    current_path = functions.unixify_path(widget.save_name)
                    if old_path in current_path:
                        widget.save_name = widget.save_name.replace(
                            old_path, new_path
                        )
                        self.display.display_warning(
                            "Renamed directory of file:"
                            + "\n    {}\n  to:\n    {}".format(
                                current_path, widget.save_name
                            )
                        )

        for w in self.get_all_windows():
            rename_dir_in_window(w)

    def set_current_symbol_analysis(self):
        widget = self.get_tab_by_indication()
        if isinstance(widget, gui.forms.customeditor.CustomEditor):
            widget.set_symbol_analysis()
        else:
            last_editor = None
            for w in self.get_all_windows():
                current_widget = w.currentWidget()
                if isinstance(
                    current_widget, gui.forms.customeditor.CustomEditor
                ):
                    last_editor = current_widget
            if last_editor is not None:
                last_editor.set_symbol_analysis()

    def set_save_file_state(self, enable):
        """Enable or disable the save functionality and save options under
        "File" in the menubar."""
        #        self.save_file_action.setEnabled(enable)
        #        self.save_ascii_file_action.setEnabled(enable)
        #        self.save_ansiwin_file_action.setEnabled(enable)
        self.save_project_action.setEnabled(True)
        # Set the save state flag accordingly
        self.save_state = enable

    def get_tab_by_name(self, tab_name):
        """Find a tab using its name in the tab widgets."""
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check the tabs
        for window in windows:
            for i in range(0, window.count()):
                if window.tabText(i) == tab_name:
                    return window.widget(i)
        # Tab was not found
        return None

    def get_tab_by_save_name(self, tab_name):
        """Find a tab using its save name (file path) in the tab widgets."""
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check the tabs
        for window in windows:
            for i in range(0, window.count()):
                if (
                    isinstance(
                        window.widget(i), gui.forms.customeditor.CustomEditor
                    )
                    and window.widget(i).save_name == tab_name
                ):
                    return window.widget(i)
        # Tab was not found
        return None

    def get_tab_by_string_in_name(self, string):
        """Find a tab with 'string' in its name in the tab widgets."""
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check the tabs
        for window in windows:
            for i in range(0, window.count()):
                if string in window.tabText(i):
                    return window.widget(i)
        # Tab was not found
        return None

    def get_tab_by_focus(self):
        """Find the focused tab."""
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check the tab focus
        for window in windows:
            for i in range(0, window.count()):
                if (
                    isinstance(
                        window.widget(i), gui.helpers.textdiffer.TextDiffer
                    )
                    == True
                ):
                    if window.widget(i).editor_1.hasFocus() == True:
                        return window.widget(i).editor_1
                    elif window.widget(i).editor_2.hasFocus() == True:
                        return window.widget(i).editor_2
                else:
                    if window.widget(i).hasFocus() == True:
                        return window.widget(i)
        # No tab in the tab widgets has focus
        return None

    def get_tab_by_indication(self):
        windows = self.get_all_windows()
        for window in windows:
            for i in range(0, window.count()):
                if window.indicated == True:
                    return window.currentWidget()
        return None

    def get_tabname_by_indication(self):
        windows = self.get_all_windows()
        for window in windows:
            for i in range(0, window.count()):
                if window.indicated == True:
                    return window.tabText(i)
        return None

    def get_current_tab_by_parent_name(self, window_name):
        """Find the current tab by the parent gui.forms.tabwidget.TabWidget name
        property."""
        widget = None
        windows = self.get_all_windows()
        for w in windows:
            if window_name == w.objectName():
                widget = w.currentWidget()
        return widget

    def get_used_tab(self):
        """Get the tab that was last used (if none return the main tab)"""
        focused_tab = self.get_tab_by_focus()
        # Check if any tab is focused
        if focused_tab is None:
            focused_tab = self.get_largest_window().currentWidget()
        return focused_tab

    def get_window_by_focus(self):
        """Get the tab widget by focus."""
        windows = self.get_all_windows()
        # Loop through all the tab widgets/windows and check their focus
        for window in windows:
            if window.hasFocus() == True:
                return window
        # No tab in the tab widgets has focus
        return None

    def get_window_by_indication(self):
        windows = self.get_all_windows()
        for window in windows:
            for i in range(0, window.count()):
                if window.indicated == True:
                    return window
        return None

    def get_window_by_name(self, window_name=None):
        """Get the tab widget by name."""
        windows = self.get_all_windows()
        for w in windows:
            if window_name == w.objectName():
                return w
        return None

    def get_all_boxes(self):
        return self.findChildren(gui.forms.thebox.TheBox)

    def get_all_windows(self):
        tabs = self.findChildren(gui.forms.tabwidget.TabWidget)
        filtered_tabs = []
        for t in tabs:
            filtered_tabs.append(t)
        return filtered_tabs

    def get_all_editors(self):
        windows = self.get_all_windows()
        editors = []
        for w in windows:
            for i in range(w.count()):
                widget = w.widget(i)
                if isinstance(widget, gui.forms.customeditor.CustomEditor):
                    editors.append(widget)
        return editors

    def get_largest_window(self):
        largest_window = None
        surface = 0
        all_windows = self.get_all_windows()
        for tw in all_windows:
            compare_surface = tw.size().width() * tw.size().height()
            if compare_surface > surface:
                surface = compare_surface
                largest_window = tw
        if (largest_window is None) and (len(all_windows) > 0):
            largest_window = all_windows[-1]
        return largest_window

    def get_window_information(self):
        window_information = {}
        surface = 0
        all_windows = self.get_all_windows()
        for tw in all_windows:
            compare_surface = tw.size().width() * tw.size().height()
            if compare_surface > surface:
                surface = compare_surface
                largest_window = tw
        if (largest_window is None) and (len(all_windows) > 0):
            largest_window = all_windows[-1]

    def get_dashboard_window(self):
        windows = self.get_all_windows()
        for w in windows:
            for i in range(w.count()):
                widget = w.widget(i)
                if isinstance(widget, dashboard.chassis.dashboard.Dashboard):
                    return w
        return None

    def update_editor_diagnostics(self):
        if not hasattr(self, "diagnostics_update_timer"):
            self.diagnostics_update_timer = qt.QTimer(self)
            self.diagnostics_update_timer.setInterval(200)
            self.diagnostics_update_timer.timeout.connect(
                self.__update_editor_diagnostics
            )
        self.diagnostics_update_timer.stop()
        self.diagnostics_update_timer.start()

    @components.lockcache.inter_process_lock("update-editor-diagnostics")
    def __update_editor_diagnostics(self):
        self.diagnostics_update_timer.stop()
        diagnostics = (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_diagnostics()
        )
        if diagnostics is None:
            self.display.display_warning("Diagnostics not initialized yet!")
            return
        editors = self.get_all_editors()
        if diagnostics is None or len(editors) == 0:
            return
        for e in editors:
            e.diagnostics_handler.delete_all()
            for k, v in diagnostics.diagnostics_dict.items():
                if v.path == e.save_name:
                    if (
                        v.severity
                        == components.sourceanalyzerinterface.source_analyzer.Severity.ERROR
                    ):
                        e.diagnostics_handler.show_error(v)
                    elif (
                        v.severity
                        == components.sourceanalyzerinterface.source_analyzer.Severity.FATAL
                    ):
                        e.diagnostics_handler.show_fatal(v)
                    elif (
                        v.severity
                        == components.sourceanalyzerinterface.source_analyzer.Severity.WARNING
                    ):
                        e.diagnostics_handler.show_warning(v)

    def update_debugger_items(self):
        if not hasattr(self, "debbuger_update_timer"):
            self.debbuger_update_timer = qt.QTimer(self)
            self.debbuger_update_timer.setInterval(200)
            self.debbuger_update_timer.timeout.connect(
                self.__update_debugger_items
            )
        self.debbuger_update_timer.stop()
        self.debbuger_update_timer.start()

    def __update_debugger_items(self):
        self.debbuger_update_timer.stop()

    @qt.pyqtSlot(str)
    def _reload_changed_file(self, file_path):
        editors = self.get_all_editors()
        for e in editors:
            if e.save_name == file_path:
                if e.is_file_content_different():
                    e.reload_file()
                self._special_file_modification_check(e.save_name)

    def _special_file_modification_check(self, file_name):
        button_file = data.current_project.get_treepath_seg().get_abspath(
            "BUTTONS_BTL"
        )
        if file_name == button_file:
            self.parse_buttons()

    @qt.pyqtSlot(str)
    def _file_removed(self, file_path):
        editors = self.get_all_editors()
        for e in editors:
            if e.save_name == file_path:
                e.reset_file_reference()

    def _print_all_boxes_and_windows(self):
        functions.echo("Boxes / tabs:")
        for b in self.get_all_boxes():
            functions.echo(f"  box: {b.objectName()}")
        for t in self.get_all_windows():
            functions.echo(f"  tabs: {t.objectName()}")

    def check_document_states(self):
        """Check if there are any modified documents in the editor windows."""

        # Nested function for checking modified documents in a single tab widget
        # (just to play with nested functions)
        def check_documents_in_window(window):
            if window.count() > 0:
                for i in range(0, window.count()):
                    widget = window.widget(i)
                    if widget.savable == data.CanSave.YES:
                        if widget.save_status == data.FileStatus.MODIFIED:
                            return True
            return False

        # Check all widget in all three windows for changes
        windows = self.get_all_windows()
        close_check = [check_documents_in_window(x) for x in windows]
        if any(close_check):
            # Modified document found
            return True
        else:
            # No changes found
            return False

    def check_dashboard_state(self):
        """Check if there are any modified documents in the editor windows."""

        # Nested function for checking modified documents in a single tab widget
        # (just to play with nested functions)
        def check_documents_in_window(window):
            if window.count() > 0:
                for i in range(0, window.count()):
                    widget = window.widget(i)
                    if (
                        isinstance(
                            widget, dashboard.chassis.dashboard.Dashboard
                        )
                        == True
                    ):
                        if widget.has_unsaved_changes():
                            return True
            return False

        # Check all widget in all three windows for changes
        windows = self.get_all_windows()
        close_check = [check_documents_in_window(x) for x in windows]
        if any(close_check):
            # Modified document found
            return True
        else:
            # No changes found
            return False


class Settings:
    """Functions for manipulating the application settings (namespace/nested
    class to MainWindow)"""

    # Class varibles
    _parent = None
    # Custom object for manipulating the settings of Embeetle
    manipulator = None
    # GUI Settings manipulator
    gui_manipulator = None
    # Preferences
    preferences_window = None

    def __init__(self, parent):
        """Initialization of the Settings object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Initialize the Embeetle settings object with the current working directory
        self.manipulator = settings.SettingsFileManipulator(
            data.beetle_core_directory, data.resources_directory, parent
        )

    def update_recent_projects_list(self, new_project_path=None):
        # Update the file manipulator
        if new_project_path is not None:
            self.manipulator.add_recent_project(new_project_path)

    def update_recent_files_list(self, new_file=None):
        """Update the settings manipulator with the new file."""

        # Nested function for opening the recent file
        def new_file_function(file, *args):
            try:
                self._parent.open_file(file=file, tab_widget=None)
            except:
                pass

        # Update the file manipulator
        if new_file is not None:
            self.manipulator.add_recent_file(new_file)
        # Refresh the menubar recent list
        recent_files_menu = self._parent.stored_menus["recent_files_menu"]
        # !!Clear all of the actions from the menu OR YOU'LL HAVE MEMORY LEAKS!!
        for action in recent_files_menu.actions():
            recent_files_menu.removeAction(action)
            action.setParent(None)
            action.deleteLater()
            action = None
        recent_files_menu.clear()
        # Add the new recent files list to the menu
        for recent_file in reversed(self.manipulator.recent_files):
            # Iterate in the reverse order, so that the last file will be displayed
            # on the top of the menubar "Recent Files" menu
            recent_file_name = recent_file
            # Check if the filename has too many characters
            #            if len(recent_file_name) > 50:
            #                # Shorten the name that will appear in the menubar
            #                recent_file_name = "...{:s}".format(
            #                    os.path.splitdrive(recent_file)[1][-50:]
            #                )
            new_file_action = qt.QAction(recent_file_name, recent_files_menu)
            new_file_action.setStatusTip("Open: {:s}".format(recent_file))
            # Create a function reference for opening the recent file
            temp_function = functools.partial(new_file_function, recent_file)
            new_file_action.triggered.connect(temp_function)
            recent_files_menu.addAction(new_file_action)

    def restore(self, echo=False):
        """Restore the previously stored settings."""
        # Load the settings from the initialization file
        result = self.manipulator.load_settings()
        # Adjust icon style according to theme
        iconfunctions.update_style()
        # Update the theme
        data.theme = self.manipulator.theme
        self._parent.view.refresh_theme()
        # Update recent files and projects lists in the menubar
        self.update_recent_files_list()
        self.update_recent_projects_list()
        # Display message in statusbar
        self._parent.display.write_to_statusbar("Restored settings", 1000)
        # Update the styles
        components.thesquid.TheSquid.update_styles()
        # Update the toolbar
        self._parent._init_toolbar()
        self._parent.update_toolbar_style()
        # Update keyboard shortcuts
        self._parent.reassign_shortcuts()
        # Display the settings load error AFTER the theme has been set
        # Otherwise the error text color will not be styled correctly
        if result == False:
            self._parent.display.display_error(
                "Error loading the settings file, using the "
                + "default settings values!\n"
                + "THE SETTINGS FILE WILL NOT BE UPDATED!"
            )
        else:
            if echo:
                self._parent.send("restyle")

    def save(self, restyle=True):
        """Save the current settings."""
        self.manipulator.save_settings()
        # Display message in statusbar
        self._parent.display.write_to_statusbar("Saved settings", 1000)
        if restyle == True:
            self._parent.send("restyle")

    def show_preferences(self, in_tab_widget=None):
        tab_name = "Preferences"
        preferences = self._parent.get_tab_by_name(tab_name)
        if preferences is not None:
            preferences._parent.setCurrentWidget(self.preferences_window)
        else:
            tabs = None
            if in_tab_widget is not None:
                tabs = in_tab_widget
            else:
                tabs = self._parent.get_largest_window()
            if tabs is not None:
                self.preferences_window = tabs.preferences_add(tab_name)
                tabs.setCurrentWidget(self.preferences_window)
            else:
                self._parent.display.display_error(
                    "Layout not initialized yet!"
                )
                return
        self.preferences_window.setFocus()
        return self.preferences_window


class View:
    """Functions for manipulating the application appearance (namespace/nested
    class to MainWindow)"""

    # Class varibles
    _parent = None
    indicated_window = None
    __repositioning_webview_hack = False

    def __init__(self, parent: MainWindow) -> None:
        """Initialization of the View object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent: MainWindow = parent
        return

    """
    Signals comming from other widgets, like the CustomEditor, ...
    """

    def editor_control_press(self):
        pass

    def editor_control_release(self):
        pass

    """
    Layout
    """

    def _get_layout_classes(self):
        # Class name storage
        classes = {
            "FileExplorer": gui.forms.newfiletree.NewFiletree,
            "Dashboard": dashboard.chassis.dashboard.Dashboard,
            "SATab": sa_tab.chassis.sa_tab.SATab,
            "Editor": gui.forms.customeditor.CustomEditor,
            "Diagnostics": gui.helpers.diagnosticwindow.DiagnosticWindow,
            "Symbols": gui.helpers.symbolwindow.SymbolWindow,
            "Console": beetle_console.make_console.MakeConsole,
            "SerialConsole": beetle_console.serial_console.SerialConsole,
            "StandardConsole": gui.consoles.standardconsole.StandardConsole,
            "Terminal": gui.forms.terminal.Terminal,
            "Messages": gui.forms.messagewindow.MessageWindow,
            "Preferences": gui.forms.settingswindow.SettingsWindow,
            "Debugger": debugger.debuggerwindow.DebuggerWindow,
            "MemoryViewGeneralRegisters": (
                debugger.memoryviews.MemoryViewGeneralRegisters
            ),
            "MemoryViewRawMemory": debugger.memoryviews.MemoryViewRawMemory,
            "MemoryViewVariableWatch": (
                debugger.memoryviews.MemoryViewVariableWatch
            ),
            "SearchResultsWindow": (
                gui.helpers.searchresultswindow.SearchResultsWindow
            ),
            "PiecesWindow": pieces.pieceswindow.PiecesWindow,
            "NewDashboard": new_dashboard.new_dashboard.NewDashboard,
            "ChipConfigurator": chipconfigurator.widgets.ChipConfiguratorWindow,
        }
        if data.PINCONFIG_ENABLED:
            classes["PinConfiguratorWindow"] = (
                gui.forms.pinconfigurator.PinConfiguratorWindow
            )
        inverted_classes = {v: k for k, v in classes.items()}
        return classes, inverted_classes

    def _get_critical_widgets(self):
        return (
            "FileExplorer",
            "Dashboard",
            "Diagnostics",
            "Symbols",
        )

    def reindex_all_windows(self):
        # Adjust indexes if needed
        for box in self._parent.get_all_boxes():
            index = 0
            box.update_orientations()
            for i in range(box.count()):
                tab_widget = box.widget(i)
                if isinstance(tab_widget, gui.forms.tabwidget.TabWidget):
                    name = tab_widget.objectName()
                    base_name = functions.remove_tabs_from_name(name)
                    box_name = box.objectName()
                    if base_name != box_name:
                        name = box_name + ".Tabs0"
                    new_name = "{}{}".format(
                        functions.remove_tab_number_from_name(name), index
                    )
                    tab_widget.setObjectName(new_name)
                    index += 1
        # Adjust unnecessary box duplications in names and
        # more than one box at one position
        boxes = self._parent.get_all_boxes()
        for b in boxes:
            if (
                b.count() == 1
                and isinstance(b.widget(0), gui.forms.thebox.TheBox)
                and b.objectName() != "Main"
            ):
                index = b.parent().indexOf(b)
                b.parent().insertWidget(index, b.widget(0))

                b.setParent(None)
                b.deleteLater()
            elif b.count() == 0:
                pass

        def rename(box):
            for i in range(box.count()):
                widget = box.widget(i)
                if isinstance(widget, gui.forms.thebox.TheBox):
                    if widget.orientation() == qt.Qt.Orientation.Vertical:
                        widget.setObjectName(box.objectName() + f".V{i}")
                    else:
                        widget.setObjectName(box.objectName() + f".H{i}")
                    rename(widget)
                else:
                    tabs_name = widget.objectName().split(".")[-1]
                    widget.setObjectName(
                        widget.parent().objectName() + f".{tabs_name}"
                    )

        main_box = self._parent.findChild(gui.forms.thebox.TheBox, "Main")
        rename(main_box)
        qt.QTimer.singleShot(10, self._parent.view.layout_save)

    def layout_generate(self):
        main = self._parent.findChild(gui.forms.thebox.TheBox, "Main")
        children = main.get_child_boxes()
        window_size = self._parent.size()
        window_size = (window_size.width(), window_size.height())
        screen_index = functions.get_widget_screen_index(self._parent)
        top_left_offset = self._parent.pos()
        screen_data = functions.get_screen_data()
        if self._parent.isMaximized():
            window_size = "MAXIMIZED"
        layout = {
            "SCREEN-DATA": screen_data,
            "WINDOW-SIZE": window_size,
            "SCREEN-INDEX": screen_index,
            "X-Y-OFFSET": (top_left_offset.x(), top_left_offset.y()),
            "BOXES": children,
        }

        # Check that all critical widgets are in the layout
        critical_widgets = {x: False for x in self._get_critical_widgets()}

        def _finditem(obj, key):
            if key in obj.values():
                return True
            for k, v in obj.items():
                if isinstance(v, dict):
                    if _finditem(v, key):
                        return True
            return False

        for cw in critical_widgets.keys():
            critical_widgets[cw] = _finditem(layout["BOXES"], cw)

        json_layout = json.dumps(layout, indent=4)
        return json_layout

    def __move_tab_in(
        self, value, new_tabs, widget_name, container=None
    ) -> None:
        # Create boxes
        main_form = self._parent
        if value in main_form.stored_widgets.keys():
            new_tabs.move_tab_in(
                main_form.stored_widgets[value].widget,
                main_form.stored_widgets[value].tab_icon,
                main_form.stored_widgets[value].tab_text,
            )
        else:
            if container is None:
                setattr(main_form, widget_name, new_tabs)
            else:
                container[widget_name] = new_tabs
        return

    layout_initialized = False

    def layout_restore(self, json_layout, project_directory):
        main_form = self._parent
        main_groupbox = self._parent.main_groupbox

        # Class name storage
        classes, inverted_classes = self._get_layout_classes()

        # First load the JSON layout, to see if it's valid
        layout = json.loads(json_layout)

        # Store all current widgets
        for t in main_form.get_all_windows():
            tab_widget_name = t.objectName()
            for i in reversed(range(t.count())):
                cls = t.widget(i).__class__
                if cls in classes.values():
                    main_form.stored_widgets[inverted_classes[cls]] = (
                        types.SimpleNamespace(
                            widget=t.widget(i),
                            tab_icon=t.tabIcon(i),
                            tab_text=t.tabText(i),
                        )
                    )
                    t.widget(i).setParent(main_form)
            t.setParent(None)

        # Restore size
        window_size = layout["WINDOW-SIZE"]
        same_screen_data = False
        if "SCREEN-DATA" in layout:
            try:
                current_data = functions.get_screen_data()
                stored_data = layout["SCREEN-DATA"]
                same_screen_data = current_data == stored_data
            except:
                traceback.print_exc()
        screen_size = functions.get_screen_size()
        if window_size == "MAXIMIZED":
            try:
                if "X-Y-OFFSET" in layout and same_screen_data:
                    x_y_offest = layout["X-Y-OFFSET"]
                    self._parent.move(*x_y_offest)
            except:
                traceback.print_exc()
            self._parent.showMaximized()

        elif isinstance(window_size, tuple) or isinstance(window_size, list):
            w, h = window_size
            if w > screen_size.width() or h > screen_size.height():
                self._parent.showMaximized()
            else:
                self._parent.resize(qt.create_qsize(w, h))
                try:
                    if "X-Y-OFFSET" in layout and same_screen_data:
                        x_y_offest = layout["X-Y-OFFSET"]
                        self._parent.move(x_y_offest[0], x_y_offest[1])
                    else:
                        functions.center_to_current_screen(self._parent)
                except:
                    traceback.print_exc()

        init_box = main_groupbox.layout().itemAt(0).widget()
        init_box.clear_all()

        critical_widgets = {x: False for x in self._get_critical_widgets()}
        editor_storage = []
        tabs_storage = []

        def create_box(parent, box):
            for k, v in sorted(box.items()):
                if k.startswith("BOX"):
                    orientation = qt.Qt.Orientation.Horizontal
                    if k[-1] == "V":
                        orientation = qt.Qt.Orientation.Vertical
                    new_box = parent.add_box(orientation, add_tabs=False)
                    new_box.show()
                    for _k, _v in v.items():
                        create_box(new_box, _v)
                elif k == "SIZES":
                    new_box.setSizes(v)
                elif k.startswith("TABS"):
                    new_tabs = parent.add_tabs()

                    # Disable the updating
                    new_tabs.setUpdatesEnabled(False)
                    new_tabs.hide()

                    try:
                        tabs_storage.append(new_tabs)
                        new_tabs.check_close_button()
                        current_index = None
                        tab_index = None
                        widget_data = None
                        for key, value in v.items():
                            if key == "CURRENT-INDEX":
                                current_index = value
                                continue
                            elif isinstance(value, str):
                                cls = value
                            elif isinstance(value, tuple) or isinstance(
                                value, list
                            ):
                                cls, tab_index, widget_data = value
                            elif isinstance(value, dict):
                                cls = value["class"]
                                if "tab-index" in value.keys():
                                    tab_index = value["tab-index"]
                                if "data" in value.keys():
                                    widget_data = value["data"]

                            else:
                                self._parent.display.display_error(
                                    f"[LAYOUT] Unknown item 'value': {value.__class__}"
                                )
                                continue

                            if cls in classes.keys():
                                if cls in critical_widgets.keys():
                                    critical_widgets[cls] = True
                                if cls == "FileExplorer":
                                    self.__move_tab_in(
                                        cls, new_tabs, "filetree_tabwidget"
                                    )
                                    data.filetree = (
                                        self._parent.projects.show_filetree()
                                    )

                                elif cls == "Dashboard":
                                    self.__move_tab_in(
                                        cls, new_tabs, "dashboard_tabwidget"
                                    )
                                    self._parent.projects.dashboard = (
                                        self._parent.projects.show_dashboard()
                                    )
                                    data.dashboard = (
                                        self._parent.projects.dashboard
                                    )

                                elif cls == "SATab":
                                    self.__move_tab_in(
                                        cls, new_tabs, "sa_tabwidget"
                                    )
                                    self._parent.projects.sa_tab = (
                                        self._parent.projects.show_sa_tab()
                                    )
                                    data.sa_tab = self._parent.projects.sa_tab

                                elif cls == "Messages":
                                    self.__move_tab_in(
                                        cls, new_tabs, "messages_tabwidget"
                                    )
                                    # Add the messages widget to it's tabwidget
                                    self._parent.display.messages_window = self._parent.messages_tabwidget.messages_add(
                                        data.tab_names["messages"],
                                        existing_messages=self._parent.display.messages_window,
                                    )

                                elif cls == "Diagnostics":
                                    self.__move_tab_in(
                                        cls, new_tabs, "diagnostics_tabwidget"
                                    )
                                    self._parent.projects.show_diagnostics()

                                elif cls == "Symbols":
                                    self.__move_tab_in(
                                        cls, new_tabs, "symbols_tabwidget"
                                    )
                                    self._parent.projects.show_symbols()

                                elif cls == "Debugger":
                                    self.__move_tab_in(
                                        cls, new_tabs, "debugger_tabwidget"
                                    )
                                    self._parent.projects.show_debugger()
                                    if widget_data is not None:
                                        if "gdb-url" in widget_data:
                                            gdb_url = widget_data["gdb-url"]
                                            self._parent.projects.debugger_window.set_gdb_url(
                                                gdb_url
                                            )

                                elif cls == "PiecesWindow":
                                    self.__move_tab_in(
                                        cls, new_tabs, "pieces_tabwidget"
                                    )
                                    self._parent.projects.show_pieces()

                                elif cls == "NewDashboard":
                                    self.__move_tab_in(
                                        cls, new_tabs, "new_dashboard_tabwidget"
                                    )
                                    self._parent.projects.show_new_dashboard()

                                elif cls == "ChipConfigurator":
                                    self.__move_tab_in(
                                        cls,
                                        new_tabs,
                                        "chipconfigurator_tabwidget",
                                    )
                                    self._parent.projects.show_chipconfigurator()

                                elif cls == "MemoryViewGeneralRegisters":
                                    dictionary = (
                                        self._parent.memory_view_tabwidgets
                                    )
                                    name = data.tab_names["general-registers"]
                                    if name not in dictionary.keys():
                                        dictionary[name] = None
                                    self.__move_tab_in(
                                        cls,
                                        new_tabs,
                                        name,
                                        container=dictionary,
                                    )
                                    gr = (
                                        self._parent.projects.show_general_registers()
                                    )
                                    if widget_data is not None:
                                        gr.set_auto_update(
                                            widget_data["auto-update"]
                                        )

                                elif cls == "MemoryViewRawMemory":
                                    dictionary = (
                                        self._parent.memory_view_tabwidgets
                                    )
                                    memory_type = "Generic"
                                    if (
                                        widget_data is not None
                                        and "memory-type" in widget_data.keys()
                                    ):
                                        memory_type = widget_data["memory-type"]
                                    name = data.tab_names["raw-memory"].format(
                                        memory_type
                                    )
                                    if name not in dictionary.keys():
                                        dictionary[name] = None
                                    self.__move_tab_in(
                                        cls,
                                        new_tabs,
                                        name,
                                        container=dictionary,
                                    )
                                    rm = self._parent.projects.show_raw_memory(
                                        memory_type
                                    )
                                    if widget_data is not None:
                                        rm.set_auto_update(
                                            widget_data["auto-update"]
                                        )

                                elif cls == "MemoryViewVariableWatch":
                                    dictionary = (
                                        self._parent.memory_view_tabwidgets
                                    )
                                    name = data.tab_names["variable-watch"]
                                    if name not in dictionary.keys():
                                        dictionary[name] = None
                                    self.__move_tab_in(
                                        cls,
                                        new_tabs,
                                        name,
                                        container=dictionary,
                                    )
                                    self._parent.projects.show_variable_watch()

                                elif cls == "Preferences":
                                    new_preferences = (
                                        self._parent.settings.show_preferences(
                                            in_tab_widget=new_tabs
                                        )
                                    )

                                elif cls == "Terminal":
                                    new_terminal = new_tabs.terminal_add_tab()
                                    if widget_data is not None:
                                        if (
                                            "current-working-directory"
                                            in widget_data.keys()
                                        ):
                                            cwd = widget_data[
                                                "current-working-directory"
                                            ]
                                            if (
                                                cwd is not None
                                                and os.path.isdir(cwd)
                                            ):
                                                new_terminal.set_cwd(cwd)

                                elif cls == "PinConfiguratorWindow":
                                    new_pinconfigurator = new_tabs.pinconfigurator_add(
                                        data.tab_names["pin-configurator"],
                                        data.current_project.get_proj_rootpath(),
                                        data.current_project.get_chip().get_name(),
                                    )
                                    self._parent.projects.pinconfigurator_window = (
                                        new_pinconfigurator
                                    )
                                    if widget_data is not None:
                                        pass

                                elif cls == "Editor":
                                    file = key
                                    x_view_offset = None
                                    if isinstance(value, tuple) or isinstance(
                                        value, list
                                    ):
                                        if len(widget_data) == 4:
                                            (
                                                line,
                                                index,
                                                first_visible_line,
                                                x_view_offset,
                                            ) = widget_data
                                        else:
                                            line, index, first_visible_line = (
                                                widget_data
                                            )
                                    elif isinstance(value, dict):
                                        line = widget_data["line"]
                                        index = widget_data["index"]
                                        first_visible_line = widget_data[
                                            "first-visible-line"
                                        ]
                                        x_view_offset = widget_data[
                                            "x-view-offset"
                                        ]

                                    if file == "<main-project-source-file>":
                                        try:
                                            line = 0
                                            index = 0
                                            first_visible_line = 0
                                            x_view_offset = 0
                                            directory = (
                                                functions.unixify_path_join(
                                                    project_directory,
                                                    "source/user_code",
                                                )
                                            )
                                            if os.path.isdir(directory):
                                                found = None
                                                for item in os.listdir(
                                                    directory
                                                ):
                                                    if item.lower() == "main.c":
                                                        found = item
                                                        break
                                                    elif item.lower().endswith(
                                                        ".ino.cpp"
                                                    ):
                                                        found = item
                                                        break
                                                else:
                                                    continue
                                                file = (
                                                    functions.unixify_path_join(
                                                        directory, found
                                                    )
                                                )
                                            else:
                                                continue
                                        except:
                                            continue
                                    elif file.startswith("rel://"):
                                        try:
                                            file = functions.unixify_path_join(
                                                project_directory,
                                                file.replace("rel://", ""),
                                            )
                                        except:
                                            pass
                                    widget = self._parent.open_file(
                                        file, new_tabs, False
                                    )
                                    if tab_index is not None:
                                        widget = new_tabs.widget(tab_index)
                                        if widget is not None:
                                            widget.setCursorPosition(
                                                line, index
                                            )
                                            widget.setFirstVisibleLine(
                                                first_visible_line
                                            )
                                            if x_view_offset is not None:
                                                widget.SendScintilla(
                                                    qt.QsciScintilla.SCI_SETXOFFSET,
                                                    x_view_offset,
                                                )

                                elif cls == "Console":
                                    new_tabs.console_add(
                                        tab_name=key,
                                        console_type=data.ConsoleType.Make,
                                    )

                                elif cls == "StandardConsole":
                                    new_tabs.console_add(
                                        tab_name=key,
                                        console_type=data.ConsoleType.Standard,
                                        cwd=widget_data.get(
                                            "current-working-directory", None
                                        ),
                                    )

                                elif cls == "SerialConsole":
                                    name = data.tab_names["serial-console"]
                                    console = data.main_form.create_console(
                                        name,
                                        console_type=data.ConsoleType.Serial,
                                        in_tab_widget=new_tabs,
                                    )

                            elif cls == "Messages":
                                """Messages is now in the popup box."""
                                pass
                            else:
                                self._parent.display.display_error(
                                    f"Unknown tab type: {cls}"
                                )
                    finally:
                        # Re-enable tabwidget updates
                        new_tabs.setUpdatesEnabled(True)
                        new_tabs.show()

                    if current_index is not None:
                        qt.QTimer.singleShot(
                            100,
                            lambda *args: new_tabs.setCurrentIndex(
                                current_index
                            ),
                        )
                else:
                    self._parent.display.display_error(
                        "Unknown box child type: {}".format(k)
                    )

        # Open the permanent items
        for k, v in sorted(layout["BOXES"].items()):
            create_box(init_box, v)
        # Check if all critical widgets have been added
        tabs = self._parent.get_largest_window()
        if tabs is None:
            tabs = tabs_storage[0]
        for k, v in critical_widgets.items():
            if v == False:
                if hasattr(self._parent, f"{k.lower()}_tabwidget"):
                    self.__move_tab_in(k, tabs, f"{k.lower()}_tabwidget")
                    if k == "FileExplorer":
                        data.filetree = self._parent.projects.show_filetree()
                    elif k == "Dashboard":
                        self._parent.projects.dashboard = (
                            self._parent.projects.show_dashboard()
                        )
                        data.dashboard = self._parent.projects.dashboard
                    elif k == "Diagnostics":
                        self._parent.projects.show_diagnostics()
                    elif k == "Symbols":
                        self._parent.projects.show_symbols()

        self.layout_initialized = True

    def layout_save(self, _async=True):
        if data.current_project is None or self.layout_initialized == False:
            return

        def save(*args, **kwargs):
            try:
                if _async:
                    self.layout_save_timer.stop()
                layout = self.layout_generate()
                file_path = f"{data.current_project.get_proj_rootpath()}/.beetle/window_config.btl"
                functions.write_to_file(layout, file_path)

                if not self.__repositioning_webview_hack:
                    if not self._parent.isMaximized():
                        self.__repositioning_webview_hack = True
                        self._parent.move(
                            self._parent.pos().x(),
                            self._parent.pos().y(),
                        )
            except:
                traceback.print_exc()

        if _async:
            if not hasattr(self, "layout_save_timer"):
                # Create the layout save timer if it doesn't exist yet
                self.layout_save_timer = qt.QTimer(self._parent)
                self.layout_save_timer.setInterval(500)
                self.layout_save_timer.setSingleShot(True)
                self.layout_save_timer.timeout.connect(save)
            timer = self.layout_save_timer
            if timer.isActive():
                timer.stop()
            timer.start()
        else:
            save()

    def check_layout_timer(self):
        if hasattr(self, "layout_save_timer"):
            timer = self.layout_save_timer
            return timer.isActive()
        else:
            return False

    def show_about(self):
        """Show ExCo information."""
        about = gui.helpers.info.ExCoInfo(
            self._parent,
            app_dir=self._parent.settings.manipulator.beetle_core_directory,
        )
        # The exec() function shows the dialog in MODAL mode (the parent is unclickable while the dialog is shown)
        about.exec()

    def toggle_window_size(self):
        """Maximize the main application window."""
        if self._parent.isMaximized() == True:
            self._parent.showNormal()
        else:
            self._parent.showMaximized()

    def hide_all_overlay_widgets(self):
        """
        Hide every overlay widget: function wheel, settings gui manipulator, ...
        """
        pass

    def reset_entire_style_sheet(self):
        style_sheet = gui.stylesheets.mainwindow.get_default()
        self._parent.setStyleSheet(style_sheet)
        windows = self._parent.get_all_windows()
        for w in windows:
            for i in range(w.count()):
                item = w.widget(i)
                if isinstance(item, gui.forms.customeditor.CustomEditor):
                    item.set_theme(data.theme)
                    item.set_style()

    def indicate_window(self, indicated_window):
        windows = self._parent.get_all_windows()
        for w in windows:
            if w is indicated_window:
                w.indication_set()
                self.indicated_window = w
                # Fire signal
                data.signal_dispatcher.indication_changed.emit(
                    w.currentIndex(), w, "indication-changed"
                )
                # Update statusbar
                current_tab = w.currentWidget()
                if hasattr(current_tab, "display_widget_statusbar_status"):
                    current_tab.display_widget_statusbar_status()
            else:
                w.indication_reset()

    def refresh_theme(self):
        windows = self._parent.get_all_windows()
        for window in windows:
            for i in range(window.count()):
                if hasattr(window.widget(i), "refresh_lexer") == True:
                    window.widget(i).refresh_lexer()
                elif hasattr(window.widget(i), "set_theme") == True:
                    window.widget(i).set_theme(data.theme)
        self.reset_entire_style_sheet()
        self._parent.update_statusbar_style()
        # Update the taskbar menu
        self._parent.display.update_theme_taskbar_icon()

    def reload_themes(self):
        current_theme_name = data.theme["name"]
        data.theme = themes.get(current_theme_name)
        self.refresh_theme()

    def create_recent_file_list_menu(self):
        self._parent.stored_menus["recent_files_menu"] = (
            gui.templates.basemenu.BaseMenu("Recent Files")
        )
        menu = self._parent.stored_menus["recent_files_menu"]
        temp_icon = iconfunctions.get_qicon(f"icons/menu_edit/recent_files.png")
        menu.setIcon(temp_icon)
        return menu

    def create_recent_project_list_menu(self):
        self._parent.stored_menus["recent_projects_menu"] = (
            gui.templates.basemenu.BaseMenu("Recent Projects")
        )
        menu = self._parent.stored_menus["recent_projects_menu"]
        temp_icon = iconfunctions.get_qicon(f"icons/folder/open/chip.png")
        menu.setIcon(temp_icon)
        #            menu.setToolTip("Shows the recently opened project")
        menu.setStatusTip("Shows the recently opened project")
        return menu

    def delete_recent_file_list_menu(self):
        self._parent.stored_menus["recent_files_menu"].setParent(None)
        self._parent.stored_menus["recent_files_menu"] = None


class System:
    """Functions that interact with the system (namespace/nested class to
    MainWindow)"""

    # Class varibles
    parent = None

    def __init__(self, parent):
        """Initialization of the System object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent

    def find_files(
        self,
        file_name,
        search_dir=None,
        case_sensitive=False,
        search_subdirs=True,
    ):
        """Return a list of files that match file_name as a list and display
        it."""
        # Check if the search directory is none, then use a dialog window
        # to select the real search directory
        if search_dir is None:
            search_dir = self._parent._get_directory_with_dialog()
            # Update the current working directory
            if os.path.isdir(search_dir):
                self._parent.set_cwd(search_dir)
        # Execute the find function
        found_files = functions.find_files_by_name(
            file_name, search_dir, case_sensitive, search_subdirs
        )
        # Check of the function return is valid
        if found_files is None:
            # Check if directory is valid
            self._parent.display.display_message_with_type(
                "Invalid search directory!", message_type=data.MessageType.ERROR
            )
            self._parent.display.write_to_statusbar(
                "Invalid search directory!", 2000
            )
            return
        elif found_files == []:
            # Check if any files were found
            self._parent.display.display_message_with_type(
                "No files found!", message_type=data.MessageType.WARNING
            )
            self._parent.display.write_to_statusbar("No files found!", 2000)
            return
        # Display the found files
        self._parent.display.show_found_files(
            "'{:s}' in its name".format(file_name), found_files, search_dir
        )

    def find_in_files(
        self,
        search_text,
        search_dir=None,
        case_sensitive=False,
        search_subdirs=True,
        break_on_find=False,
    ):
        """Return a list of files that contain the searched text as a list and
        display it."""
        # Check if the search directory is none, then use a dialog window
        # to select the real search directory
        if search_dir is None:
            search_dir = self._parent._get_directory_with_dialog()
            # Update the current working directory
            if os.path.isdir(search_dir):
                self._parent.set_cwd(search_dir)
        try:
            # Execute the find function
            found_files = functions.find_files_with_text_enum(
                search_text,
                search_dir,
                case_sensitive,
                search_subdirs,
                break_on_find,
            )
            # Check of the function return is valid
            if found_files is None:
                # Check if directory is valid
                self._parent.display.display_message_with_type(
                    "Invalid search directory!",
                    message_type=data.MessageType.ERROR,
                )
                self._parent.display.write_to_statusbar(
                    "Invalid search directory!", 2000
                )
                return
            elif found_files == {}:
                # Check if any files were found
                self._parent.display.display_message_with_type(
                    "No files found!", message_type=data.MessageType.WARNING
                )
                self._parent.display.write_to_statusbar("No files found!", 2000)
                return
            # Display the found files
            self._parent.display.show_found_files_with_lines_in_tree(
                "'{:s}' in its content".format(search_text),
                found_files,
                search_dir,
            )
        except Exception as ex:
            self._parent.display.display_message_with_type(
                str(ex), message_type=data.MessageType.ERROR
            )

    def replace_in_files(
        self,
        search_text,
        replace_text,
        search_dir=None,
        case_sensitive=False,
        search_subdirs=True,
    ):
        """Same as the function in the 'functions' module.

        Replaces all instances of search_string with the replace_string in the
        files, that contain the search string in the search_dir.
        """
        warning = "The replaced content will be saved back into the files!\n"
        warning += "You better have a backup of the files if you are unsure,\n"
        warning += "because this action CANNOT be undone!\n"
        warning += "Do you want to continue?"
        reply = gui.dialogs.popupdialog.PopupDialog.warning(
            warning, parent=self
        )
        if reply == qt.QMessageBox.StandardButton.No:
            return
        # Check if the search directory is none, then use a dialog window
        # to select the real search directory
        if search_dir is None:
            search_dir = self._parent._get_directory_with_dialog()
            # Update the current working directory
            if os.path.isdir(search_dir):
                self._parent.set_cwd(search_dir)
        # Replace the text in files
        result = functions.replace_text_in_files_enum(
            search_text,
            replace_text,
            search_dir,
            case_sensitive,
            search_subdirs,
        )
        # Check the return type
        if len(result) == 0:
            self._parent.display.display_message_with_type(
                "No files with '{:s}' in its text were found!".format(
                    search_text
                ),
                message_type=data.MessageType.WARNING,
            )
        elif isinstance(result, dict):
            self._parent.display.show_replaced_text_in_files_in_tree(
                search_text, replace_text, result, search_dir
            )
        else:
            self._parent.display.display_message_with_type(
                "Unknown error!", message_type=data.MessageType.ERROR
            )


class Editing:
    """Document editing functions (namespace/nested class to MainWindow)"""

    # Class varibles
    parent = None

    def __init__(self, parent):
        """Initialization of the Editing object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Initialize the namespace classes
        self.line = self.Line(self)

    def dialog_find_in_open_documents(self, *args, **kwargs):
        """The search function created for the search dialog."""
        focused_widget = self._parent.get_tab_by_indication()
        if focused_widget is None:
            return (
                "No editor is focused!\nFocus a window with at least 1 editor."
            )
        return self.find_in_open_documents(*args, **kwargs)

    def find_in_open_documents(
        self, search_text, case_sensitive=False, regular_expression=False
    ):
        """Find instances of search text accross all open document."""
        # Get the current widget
        editors = self._parent.get_all_editors()
        # Check if there are any editors
        if len(editors) == 0:
            message = "No open editors!"
            self._parent.display.display_message_with_type(
                message, message_type=data.MessageType.WARNING
            )
            return False
        # Get the currently selected editor
        selected_editor = self._parent.get_tab_by_indication()
        # Create a deque of the tab index order and start with the current index,
        # deque is used, because it can be rotated by default
        in_deque = collections.deque(editors)
        # Rotate the deque until the first element is the current index
        while in_deque[0] != selected_editor:
            in_deque.rotate(1)
        # Set a flag for the first document
        first_document = True
        for e in in_deque:
            # Place the cursor to the top of the document if it is not the current document
            if first_document == True:
                first_document = False
            else:
                e.setCursorPosition(0, 0)
            # Find the text
            result = e.find_text(
                search_text,
                case_sensitive,
                True,  # search_forward
                regular_expression,
            )
            # If something was found, return success
            if result == data.SearchResult.FOUND:
                return True
        return False

    def find_replace_in_open_documents(
        self,
        search_text,
        replace_text,
        case_sensitive=False,
        regular_expression=False,
        window_name=None,
    ):
        """Find and replace instaces of search string with replace string across
        all of the open documents in the selected window, one instance at a
        time, starting from the currently selected widget."""
        # Get the current widget
        tab_widget = self._parent.get_window_by_name(window_name)
        if window_name is None:
            window_name = "Main"
        # Check if there are any documents in the tab widget
        if tab_widget.count() == 0:
            message = "No documents in the " + tab_widget.name.lower()
            message += " editing window"
            self._parent.display.display_message_with_type(
                message, message_type=data.MessageType.WARNING
            )
            return
        # Save the current index to reset focus to it if no instances of search string are found
        saved_index = tab_widget.currentIndex()
        # Create a deque of the tab index order and start with the current index,
        # deque is used, because it can be rotated by default
        in_deque = collections.deque(range(tab_widget.count()))
        # Rotate the deque until the first element is the current index
        while in_deque[0] != tab_widget.currentIndex():
            in_deque.rotate(1)
        # Find the next instance
        for i in in_deque:
            result = tab_widget.widget(i).find_and_replace(
                search_text, replace_text, case_sensitive, regular_expression
            )
            # If a replace was done, return success
            if result == True:
                message = "Found and replaced in " + tab_widget.name.lower()
                message += " editing window"
                self._parent.display.write_to_statusbar(message)
                return True
        # Nothing found
        tab_widget.setCurrentIndex(saved_index)
        message = "No instances of '" + search_text + "' found in the "
        message += tab_widget.name.lower() + " editing window"
        self._parent.display.display_message_with_type(
            message, message_type=data.MessageType.WARNING
        )
        return False

    def replace_all_in_open_documents(
        self,
        search_text,
        replace_text,
        case_sensitive=False,
        regular_expression=False,
        window_name=None,
    ):
        """Replace all instaces of search string with replace string across all
        of the open documents in the selected window."""
        # Get the current widget
        tab_widget = self._parent.get_window_by_name(window_name)
        if window_name is None:
            window_name = "Main"
        # Loop over each widget and replace all instances of the search text
        for i in range(tab_widget.count()):
            tab_widget.widget(i).replace_all(
                search_text, replace_text, case_sensitive, regular_expression
            )
        message = "Replacing all in open documents completed"
        self._parent.display.display_success(message)

    """
    Special wraper functions that take a existing function and
    execute it for the currently focused gui.forms.customeditor.CustomEditor.
    """

    def _run_focused_widget_method(
        self, method_name, argument_list, window_name=None
    ):
        """Execute a focused widget method."""
        # Get the current widget
        widget = self._parent.get_tab_by_indication()
        # None-check the current widget in the selected window
        if widget is not None:
            if hasattr(widget, method_name):
                method = getattr(widget, method_name)
                # Argument list has to be preceded by the '*' character
                method(*argument_list)
            else:
                message = "Currently focused widget has no method '{}'!".format(
                    method_name
                )
                self._parent.display.display_warning(message)
                self._parent.display.write_to_statusbar(message, 5000)
        else:
            message = "No document in {:s} window!".format(window_name)
            self._parent.display.display_warning(message)
            self._parent.display.write_to_statusbar(message, 5000)

    def dialog_search(self, *args, **kwargs):
        """The search function created for the search dialog."""
        focused_widget = self._parent.get_tab_by_indication()
        if focused_widget is None:
            return "No editor is focused!\nFocus an editor and try again."
        elif (
            isinstance(focused_widget, gui.forms.customeditor.CustomEditor)
            == False
            and isinstance(focused_widget, gui.forms.plaineditor.PlainEditor)
            == False
            and isinstance(focused_widget, gui.helpers.textdiffer.TextDiffer)
            == False
        ):
            return "The focused window does not have search functionality!"
        focused_widget.find_text(*args, **kwargs)

    def dialog_highlight(self, *args, **kwargs):
        """The highlight function created for the search dialog."""
        focused_widget = self._parent.get_tab_by_indication()
        if focused_widget is None:
            return "No editor is focused!\nFocus an editor and try again."
        elif (
            isinstance(focused_widget, gui.forms.customeditor.CustomEditor)
            == False
            and isinstance(focused_widget, gui.forms.plaineditor.PlainEditor)
            == False
        ):
            return "The focused window does not have highlight functionality!"
        focused_widget.highlight_text(*args, **kwargs)

    def dialog_clear_highlights(self):
        """Clear highlights using the search dialog."""
        focused_widget = self._parent.get_tab_by_indication()
        if focused_widget is None:
            return "No editor is focused!\nFocus an editor and try again."
        elif (
            isinstance(focused_widget, gui.forms.customeditor.CustomEditor)
            == False
            and isinstance(focused_widget, gui.forms.plaineditor.PlainEditor)
            == False
        ):
            return "The focused window does not have highlight functionality!"
        focused_widget.clear_highlights()

    def dialog_replace(self, replace_type, replace_all_flag, *args, **kwargs):
        """Replace text using the search dialog."""
        focused_widget = self._parent.get_tab_by_indication()
        if focused_widget is None:
            return "No editor is focused!\nFocus an editor and try again."
        elif (
            isinstance(focused_widget, gui.forms.customeditor.CustomEditor)
            == False
            and isinstance(focused_widget, gui.forms.plaineditor.PlainEditor)
            == False
        ):
            return "The focused window does not have highlight functionality!"
        if replace_type == "replace_in_selection":
            focused_widget.replace_in_selection(*args, **kwargs)
        elif replace_type == "replace_all":
            focused_widget.replace_all(*args, **kwargs)
        elif replace_type == "replace_all_in_open_documents":
            self.replace_all_in_open_documents(
                *args, **kwargs, window_name=focused_widget._parent.name
            )
        elif replace_type == "replace_all_in_project":
            self._parent.display.display_error(
                "Replace in Project functionality not yet implemented!"
            )

    def find(
        self,
        search_text,
        case_sensitive=False,
        search_forward=True,
        regex=False,
        incremental=False,
        window_name=None,
    ):
        """Find text in the currently focused window."""
        argument_list = (
            search_text,
            case_sensitive,
            search_forward,
            regex,
            incremental,
        )
        self._run_focused_widget_method("find_text", argument_list, window_name)

    def regex_find(
        self,
        search_text,
        case_sensitive=False,
        search_forward=True,
        window_name=None,
    ):
        """Find text in the currently focused window."""
        argument_list = [search_text, case_sensitive, search_forward, True]
        self._run_focused_widget_method("find_text", argument_list, window_name)

    def find_and_replace(
        self,
        search_text,
        replace_text,
        case_sensitive=False,
        search_forward=True,
        window_name=None,
    ):
        """Find and replace text in the currently focused window."""
        argument_list = [
            search_text,
            replace_text,
            case_sensitive,
            search_forward,
        ]
        self._run_focused_widget_method(
            "find_and_replace", argument_list, window_name
        )

    def regex_find_and_replace(
        self,
        search_text,
        replace_text,
        case_sensitive=False,
        search_forward=True,
        window_name=None,
    ):
        """Find and replace text in the currently focused window using the
        regular expressions module."""
        argument_list = [
            search_text,
            replace_text,
            case_sensitive,
            search_forward,
            True,
        ]
        self._run_focused_widget_method(
            "find_and_replace", argument_list, window_name
        )

    def replace_all(
        self, search_text, replace_text, case_sensitive=False, window_name=None
    ):
        """Replace all occurences of a string in the currently focused
        window."""
        argument_list = [search_text, replace_text, case_sensitive]
        self._run_focused_widget_method(
            "replace_all", argument_list, window_name
        )

    def regex_replace_all(
        self, search_text, replace_text, case_sensitive=False, window_name=None
    ):
        """Replace all occurences of a string in the currently focused window
        using the regular expressions module."""
        argument_list = [search_text, replace_text, case_sensitive, True]
        self._run_focused_widget_method(
            "replace_all", argument_list, window_name
        )

    def replace_in_selection(
        self, search_text, replace_text, case_sensitive=False, window_name=None
    ):
        """Replace all occurences of a string in the current selection in the
        currently focused window."""
        argument_list = [search_text, replace_text, case_sensitive]
        self._run_focused_widget_method(
            "replace_in_selection", argument_list, window_name
        )

    def regex_replace_in_selection(
        self, search_text, replace_text, case_sensitive=False, window_name=None
    ):
        """Replace all occurences of a string in the current selection in the
        currently focused window using regular expressions module."""
        argument_list = [search_text, replace_text, case_sensitive, True]
        self._run_focused_widget_method(
            "replace_in_selection", argument_list, window_name
        )

    def highlight(self, highlight_text, case_sensitive=False, window_name=None):
        """Highlight all occurences of text in the currently focused window."""
        argument_list = [highlight_text, case_sensitive]
        self._run_focused_widget_method(
            "highlight_text", argument_list, window_name
        )

    def regex_highlight(
        self, highlight_text, case_sensitive=False, window_name=None
    ):
        """Highlight all occurences of text in the currently focused window
        using regular expressions."""
        argument_list = [highlight_text, case_sensitive, True]
        self._run_focused_widget_method(
            "highlight_text", argument_list, window_name
        )

    def clear_highlights(self, window_name=None):
        """Clear all highlights in the currently focused window."""
        argument_list = []
        self._run_focused_widget_method(
            "clear_highlights", argument_list, window_name
        )

    def convert_to_uppercase(self, window_name=None):
        """Change the case of the selected text in the currently focused
        window."""
        argument_list = [True]
        self._run_focused_widget_method(
            "convert_case", argument_list, window_name
        )

    def convert_to_lowercase(self, window_name=None):
        """Change the case of the selected text in the currently focused
        window."""
        argument_list = [False]
        self._run_focused_widget_method(
            "convert_case", argument_list, window_name
        )

    class Line:
        # Class varibles
        parent = None

        def __init__(self, parent):
            """Initialization of the Editing object instance."""
            # Get the reference to the MainWindow parent object instance
            self._parent = parent

        def goto(self, line_number, window_name=None):
            """Set focus and cursor to the selected line in the currently
            focused window."""
            argument_list = [line_number]
            self._parent._run_focused_widget_method(
                "goto_line", argument_list, window_name
            )

        def replace(self, replace_text, line_number, window_name=None):
            """Replace the selected line in the currently focused window."""
            argument_list = [replace_text, line_number]
            self._parent._run_focused_widget_method(
                "replace_line", argument_list, window_name
            )

        def remove(self, line_number, window_name=None):
            """Remove the selected line in the currently focused window."""
            argument_list = [line_number]
            self._parent._run_focused_widget_method(
                "remove_line", argument_list, window_name
            )

        def get(self, line_number, window_name=None):
            """Replace the selected line in the currently focused window."""
            argument_list = [line_number]
            self._parent._run_focused_widget_method(
                "get_line", argument_list, window_name
            )

        def set(self, line_text, line_number, window_name=None):
            """Replace the selected line in the currently focused window."""
            argument_list = [line_text, line_number]
            self._parent._run_focused_widget_method(
                "set_line", argument_list, window_name
            )


class Display:
    """
    Functions for displaying of various functions such as:
    show_nodes, find_in_open_documents, ...
    (namespace/nested class to MainWindow)
    """

    # Class varibles
    _parent = None
    # Display bool state
    state = None
    # Attribute for storing which type of tab is used for dispaying node trees
    node_view_type = data.NodeDisplayType.TREE
    # Theme indicator label
    theme_indicatore = None
    # Theme menu
    theme_menu = None
    # Theme actions
    action_air = None
    action_earth = None
    action_water = None
    action_mc = None
    # References to the dynamically created menus
    stored_menus = []
    # Icons used for the special widgets
    node_tree_icon = None
    messages_icon = None
    system_found_files_icon = None
    system_found_in_files_icon = None
    system_replace_in_files_icon = None
    system_show_cwd_tree_icon = None
    # Messages editor and messages groupbox reference
    messages_window = None

    def __init__(self, parent):
        """Initialization of the Display object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        self.state = True
        # Initialize the stored icons
        self.node_tree_icon = iconfunctions.get_qicon(f"icons/gen/balls.png")
        self.messages_icon = iconfunctions.get_qicon(
            f"icons/dialog/message.png"
        )
        self.system_found_files_icon = iconfunctions.get_qicon(
            f"icons/system/find_files.png"
        )
        self.system_found_in_files_icon = iconfunctions.get_qicon(
            f"icons/system/find_in_files.png"
        )
        self.system_replace_in_files_icon = iconfunctions.get_qicon(
            f"icons/system/replace_in_files.png"
        )
        self.system_show_cwd_tree_icon = iconfunctions.get_qicon(
            f"icons/gen/tree.png"
        )
        # Initialize the theme menu
        # self.init_theme_menu()
        # Create all the dialogs
        self.dialogs_init()

    def toolbar_enable(self):
        self._parent.toolbar.setEnabled(True)

    def toolbar_disable(self):
        self._parent.toolbar.setEnabled(False)

    def init_theme_indicator(self):
        """Initialization of the theme indicator in the statusbar."""

        class ThemeIndicator(qt.QLabel):
            def __init__(self, parent):
                # Initialize superclass
                super().__init__()
                # Store the reference to the parent
                self._parent = parent

            def mouseReleaseEvent(self, event):
                # Execute the superclass event method
                super().mouseReleaseEvent(event)
                cursor = qt.QCursor.pos()
                self._parent.theme_menu.popup(cursor)

        tooltip = data.theme["tooltip"]
        image = data.theme["image_file"]
        raw_picture = qt.QPixmap(iconfunctions.get_icon_abspath(image))
        picture = raw_picture.scaled(
            16, 16, qt.Qt.AspectRatioMode.KeepAspectRatio
        )
        self.theme_indicatore = ThemeIndicator(self)
        self.theme_indicatore.setPixmap(picture)
        self.theme_indicatore.setStyleSheet(
            "ThemeIndicator {"
            + "    color: black;"
            + "    padding-top: 0px;"
            + "    padding-bottom: 0px;"
            + "    padding-left: 0px;"
            + "    padding-right: 4px;"
            + "}"
            + "QToolTip {"
            + "    color: black;"
            + "    padding-top: 0px;"
            + "    padding-bottom: 0px;"
            + "    padding-left: 0px;"
            + "    padding-right: 0px;"
            + "}"
        )
        self._parent.statusbar.addPermanentWidget(self.theme_indicatore)

    """
    Dialogs
    """
    dialogs = [
        "project_create",
        "project_new",
        "project_new_options",
        "project_new_create",
        "project_import",
        "project_import_options",
        "project_import_create",
        "scaling_dialog",
    ]

    def dialogs_init(self):
        parent = self._parent
        for d in self.dialogs:
            setattr(parent, d, None)

    def _dialog_show(self, dialog, init_class, *args):
        parent = self._parent
        self.hide_other_dialogs(getattr(parent, dialog))
        if self.dialog_test(dialog) == True:
            if getattr(parent, dialog).isVisible() == False:
                self._dialog_hide(dialog)
        if getattr(parent, dialog) is None:
            setattr(parent, dialog, init_class(parent, *args))
        show_dialog = getattr(parent, dialog)
        show_dialog.show()
        show_dialog.activateWindow()
        show_dialog.raise_()
        return show_dialog

    def _dialog_hide(self, dialog) -> None:
        parent = self._parent
        _dialog: Union[
            gui.dialogs.popupdialog.PopupDialog,
            gui.dialogs.scalingdialog.ScalingDialog,
        ] = getattr(parent, dialog)
        if _dialog is not None:
            _dialog.hide()
            _dialog.self_destruct()
            setattr(parent, dialog, None)
        return

    def dialog_check(self, dialog):
        if not (dialog in self.dialogs):
            raise Exception(f"Dialog {dialog} is invalid!")

    def dialog_test(self, dialog):
        self.dialog_check(dialog)
        return getattr(self._parent, dialog) is not None

    def hide_other_dialogs(self, dialog=None):
        parent = self._parent
        for d in self.dialogs:
            if not (dialog is getattr(parent, d)):
                self._dialog_hide(d)

    def dialog_show(self, dialog, *args):
        self.dialog_check(dialog)
        if dialog == "project_create":
            self._dialog_show(dialog, gui.ProjectCreationDialog)
        elif dialog == "project_new":
            self._dialog_show(dialog, gui.ProjectNewTypeSelector)
        elif dialog == "project_new_options":
            self._dialog_show(dialog, gui.ProjectNewOptions, *args)
        elif dialog == "project_new_create":
            self._dialog_show(dialog, gui.ProjectNewCreate, *args)
        elif dialog == "project_import":
            self._dialog_show(dialog, gui.ProjectImportTypeSelector)
        elif dialog == "project_import_options":
            self._dialog_show(dialog, gui.ProjectImportOptions, *args)
        elif dialog == "scaling_dialog":
            self._dialog_show(dialog, gui.dialogs.scalingdialog.ScalingDialog)
        return

    def dialog_hide(self, dialog):
        self.dialog_check(dialog)
        self._dialog_hide(dialog)

    """
    Docking overlay
    """

    def docking_overlay_show(self):
        parent = self._parent
        docking_overlay = parent.docking_overlay
        if docking_overlay is not None:
            window_list = parent.get_all_windows()
            docking_overlay.show_on_parent(window_list)

    def docking_overlay_hide(self):
        parent = self._parent
        if parent.docking_overlay is not None:
            parent.docking_overlay.hide()
            for window in parent.get_all_windows():
                window.check_close_button()

    """
    Theme menu in the status bar
    """

    def update_theme_taskbar_icon(self):
        # Check if the indicator is initialized
        if self.theme_indicatore is None:
            return
        # Set the theme icon and tooltip
        tooltip = data.theme["tooltip"]
        image = data.theme["image_file"]
        raw_picture = qt.QPixmap(iconfunctions.get_icon_abspath(image))
        picture = raw_picture.scaled(
            16, 16, qt.Qt.AspectRatioMode.KeepAspectRatio
        )
        self.theme_indicatore.setPixmap(picture)
        self.theme_indicatore.setStyleSheet(
            "ThemeIndicator {"
            + "    color: black;"
            + "    padding-top: 0px;"
            + "    padding-bottom: 0px;"
            + "    padding-left: 0px;"
            + "    padding-right: 4px;"
            + "}"
            + "QToolTip {"
            + "    color: black;"
            + "    padding-top: 0px;"
            + "    padding-bottom: 0px;"
            + "    padding-left: 0px;"
            + "    padding-right: 0px;"
            + "}"
        )

    def init_theme_menu(self):
        """Initialization of the theme menu used by the theme indicator."""

        def choose_theme(theme, *args):
            data.theme = theme
            self._parent.view.refresh_theme()
            self.update_theme_taskbar_icon()
            current_theme = data.theme["tooltip"]
            self.display_message_with_type(
                "Changed theme to: {}".format(current_theme),
                message_type=data.MessageType.SUCCESS,
            )

        if self.theme_menu is not None:
            # Clear the menu actions from memory
            self.theme_menu.clear()
            for action in self.theme_menu.actions():
                self.theme_menu.removeAction(action)
                action.setParent(None)
                action.deleteLater()
                action = None
        self.theme_menu = data.BaseMenu()
        # Add the theme actions
        for theme in themes.theme_list:
            action_theme = qt.QAction(theme.name, self.theme_menu)
            action_theme.triggered.connect(
                functools.partial(choose_theme, theme)
            )
            icon = iconfunctions.get_qicon(theme.image_file)
            action_theme.setIcon(icon)
            self.theme_menu.addAction(action_theme)

    """
    Statusbar
    """
    statusbar_message_blocked_flag = False

    def write_to_statusbar(self, message, msec=0):
        """Write a message to the statusbar."""
        if not self.statusbar_message_blocked_flag:
            self.statusbar_message_blocked_flag = True
            self._parent.statusbar_label_left.hide()
            self._parent.statusbar.showMessage(message)
            qt.QTimer.singleShot(msec, self.__reset_write_to_statusbar)

    def __reset_write_to_statusbar(self):
        self.statusbar_message_blocked_flag = False
        self._parent.statusbar.clearMessage()
        self._parent.statusbar_label_left.show()

    def __reset_statusbar_show(self):
        self.statusbar_message_blocked_flag = False
        self._parent.statusbar.clearMessage()

    def statusbar_show(self, message, msec=0):
        """Write a message to the statusbar (NORMAL PRIORITY)"""
        if not self.statusbar_message_blocked_flag:
            self.statusbar_message_blocked_flag = True
            self._parent.statusbar_label_left.setText(message)
            self._parent.statusbar_label_left.show()
            qt.QTimer.singleShot(msec, self.__reset_statusbar_show)

    """
    New messages
    """

    def _display_message(
        self,
        *message,
        scroll_to_end=False,
        show_messages=True,
        message_type=None,
        force_scroll_to_end=True,
    ):
        # Define references directly to the parent and mainform
        # for performance and clarity
        parent = self._parent
        if self.messages_window is None:
            _messages = self._parent.messages_tabwidget
            if _messages is not None:
                self.messages_window = (
                    self._parent.messages_tabwidget.messages_add(
                        data.tab_names["messages"]
                    )
                )
            else:
                return
        messages = self.messages_window
        # Parse the message arguments
        if len(message) > 1:
            message = "\n".join(message)
        else:
            message = message[0]
        # Check if message is a string class, if not then make it a string
        if message is None:
            return
        elif isinstance(message, str) == False:
            message = str(message)
        # Add the error message
        color_types = {
            data.MessageType.ERROR: data.theme["fonts"]["error"]["color"],
            data.MessageType.WARNING: data.theme["fonts"]["warning"]["color"],
            data.MessageType.SUCCESS: data.theme["fonts"]["success"]["color"],
            data.MessageType.DIFF_UNIQUE_1: data.theme["fonts"][
                "diff_unique_1"
            ]["color"],
            data.MessageType.DIFF_UNIQUE_2: data.theme["fonts"][
                "diff_unique_2"
            ]["color"],
            data.MessageType.DIFF_SIMILAR: data.theme["fonts"]["diff_similar"][
                "color"
            ],
        }
        # Add the message
        if message_type is not None and message_type in color_types.keys():
            selected_color = color_types[message_type]
            messages.append(
                '<p style="color: {:s}; margin: 0px;">{:s}</p>'.format(
                    selected_color, message
                )
            )
        else:
            selected_color = data.theme["fonts"]["default"]["color"]
            messages.append('<p style="margin: 0px;">{:s}</p>'.format(message))
        # Blink messages statusbar button
        if message_type == data.MessageType.ERROR:
            self.messages_button_blink()

    def display_message_with_type(self, message, message_type=None):
        self._display_message(
            message, show_messages=True, message_type=message_type
        )

    def _parse_messages(self, *messages):
        text = ""
        if len(messages) == 0:
            return text
        elif len(messages) > 1:
            text = "\n".join(messages)
        else:
            text = messages[0]
        return text

    def display_message(self, *messages):
        text = self._parse_messages(*messages)
        self._display_message(text, show_messages=True)

    def display_success(self, *messages):
        text = self._parse_messages(*messages)
        self._display_message(
            text, show_messages=True, message_type=data.MessageType.SUCCESS
        )

    def display_warning(self, *messages):
        text = self._parse_messages(*messages)
        self._display_message(
            text, show_messages=True, message_type=data.MessageType.WARNING
        )

    def display_error(self, *messages):
        text = self._parse_messages(*messages)
        self._display_message(
            text, show_messages=True, message_type=data.MessageType.ERROR
        )

    def display_clear(self):
        messages = self._parent.view.messages
        messages.setText("")
        messages.SendScintilla(qt.QsciScintillaBase.SCI_STYLECLEARALL)
        messages.set_theme(data.theme)

    def messages_button_blink(self) -> None:
        self.__blink_messages_state: bool = True
        self.__blink_counter: int = 0
        self.__blink_counter_limit: int = 19
        if not hasattr(self, "blink_messages_timer"):
            self.blink_messages_timer = qt.QTimer(self._parent)
            self.blink_messages_timer.setInterval(200)
            self.blink_messages_timer.setSingleShot(True)
            self.blink_messages_timer.timeout.connect(
                self.__messages_button_update
            )
        else:
            self.blink_messages_timer.stop()
        self.blink_messages_timer.start()

    def messages_button_reset(self) -> None:
        self.__blink_messages_state = False
        self.__blink_counter = 0
        if hasattr(self, "blink_messages_timer"):
            self.blink_messages_timer.stop()
        icon = iconfunctions.get_qicon("icons/dialog/message.svg")
        data.alert_buttons["messages"].setIcon(icon)

    def __messages_button_update(self) -> None:
        if self.__blink_messages_state:
            icon = iconfunctions.get_qicon("icons/dialog/warning_red.svg")
        else:
            icon = iconfunctions.get_qicon("icons/dialog/message.svg")
        data.alert_buttons["messages"].setIcon(icon)
        self.__blink_messages_state = not self.__blink_messages_state
        self.__blink_counter += 1
        if self.__blink_counter > self.__blink_counter_limit:
            self.__blink_counter = 0
            icon = iconfunctions.get_qicon("icons/dialog/message(warn_red).png")
            data.alert_buttons["messages"].setIcon(icon)
            return
        else:
            self.blink_messages_timer.start()

    def watchdog_observer_error(self, message):
        if os_checker.is_os("linux"):
            text = f"""
<div>
There was an error with initializing the File-tree.
<br>
We have detected that you are on Linux, please follow the instructions below.
<br>
<br>
</div>
<div style="margin-left: 20px;">
To check the current inotify watch limit, use this command in a terminal:
<br>
<p style="margin-left: 20px; margin-top: -10px; margin-bottom: -10px;">
    <b><cite>sudo sysctl fs.inotify.max_user_watches</cite></b>
    <br>
</p>
<div>
    To increase the inotify watch limit, use this command:
        <br>
</div>
<p style="margin-left: 20px; margin-top: -10px; margin-bottom: -10px;">
    <cite><b>sudo sysctl fs.inotify.max_user_watches=<b style="color: {data.theme["fonts"]["warning"]["color"]};">&lsaquo;new-value&rsaquo;</b></cite></b>
    <br>
    (replacing <b style="color: {data.theme["fonts"]["warning"]["color"]};"><cite>&lsaquo;new-value&rsaquo;</cite></b> by the desired value)
    <br>
</p>
<div>
    To make the new value persistent after reboot, use this command:
    <br>
</div>
<p style="margin-left: 20px; margin-top: -10px; margin-bottom: -10px;">
    <b><cite>echo fs.inotify.max_user_watches=<b style="color: {data.theme["fonts"]["warning"]["color"]};">&lsaquo;new-value&rsaquo;</b> | sudo tee /etc/sysctl.d/90-inotify.conf</cite></b>
    <br>
    (the command should be on one line)
    <br>
    (if you don't do this, the change disappears after reboot)
    <br>
</p>
</div>
<p>
{message}<br>
</p>
<p>
<b>Embeetle will now close!<b><br>
</p>
        """
        else:
            text = f"""
<div>
    There was an error with initializing the File-tree.
    <br>
    This is the error message:<br>
    <p>
        {message}
    </p>
</div>
<p>
<b>Embeetle will now close!<b><br>
</p>
        """
        self.show_internal_error(text.replace("\n", ""))
        self._parent.exit()

    def find_messages_tab(self):
        """Find the "REPL Message" tab in the tab widgets of the MainForm."""
        # Set the tab name for displaying REPL messages
        messages_tab_name = "REPL MESSAGES"
        # Call the MainForm function to find the repl tab by name
        self._parent.messages_tab = self._parent.get_tab_by_name(
            messages_tab_name
        )
        return self._parent.messages_tab

    """
    Search result displaying
    """

    def show_search_results(self, *args, _type=None):
        # Create a result window in the popup tabs
        tabs = self._parent.get_dashboard_window()
        if tabs is None:
            tabs = self._parent.get_largest_window()
        tab_text = "SEARCH RESULTS"
        results_tab = tabs.get_tab_by_tab_text(tab_text)
        if results_tab is None:
            results_tab = tabs.search_results_add_tab(tab_text)
        tabs.setCurrentWidget(results_tab)
        # Clear old results
        results_tab.clear()
        if _type == gui.helpers.searchbar.SearchType.File:
            results_tab.add_file_results(*args)
        elif _type == gui.helpers.searchbar.SearchType.Directory:
            results_tab.add_directory_results(*args)
        elif _type == gui.helpers.searchbar.SearchType.Filename:
            results_tab.add_filename_results(*args)
        else:
            raise Exception(f"[SEARCH] Unknown search type: {_type}")

    """
    Tree display
    """

    def show_nodes(self, custom_editor, parser):
        """Function for selecting which type of node tree will be displayed."""
        if self.node_view_type == data.NodeDisplayType.DOCUMENT:
            self.show_nodes_in_document(custom_editor, parser)
        elif self.node_view_type == data.NodeDisplayType.TREE:
            self.show_nodes_in_tree(custom_editor, parser)

    def show_nodes_in_tree(self, custom_editor, parser):
        """Show the node tree of a parsed file in a "NODE TREE" tree display
        widget in the upper window."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Check if the custom editor is valid
        if custom_editor is None:
            parent.display.display_error(
                "No document selected for node tree creation!"
            )
            parent.display.write_to_statusbar(
                "No document selected for node tree creation!", 5000
            )
            return
        # Check if the document type is Python or C
        if parser != "PYTHON" and parser != "C" and parser != "NIM":
            message = "Document is not C, Nim or Python 3!"
            parent.display.display_error(message)
            parent.display.write_to_statusbar(message, 5000)
            return
        # Define a name for the NODE tab
        node_tree_tab_name = "NODE TREE/LIST"
        # Find the "NODE TREE/LIST" tab in the tab widgets
        parent.node_tree_tab = parent.get_tab_by_name(node_tree_tab_name)
        if parent.node_tree_tab:
            parent.node_tree_tab._parent.close_tab(node_tree_tab_name)
        # Create a new NODE tab in the upper tab widget and set its icon
        parent.node_tree_tab = parent.get_largest_window().tree_add_tab(
            node_tree_tab_name
        )
        parent.node_tree_tab.current_icon = self.node_tree_icon
        node_tree_tab = parent.node_tree_tab
        node_tree_tab_index = node_tree_tab._parent.indexOf(node_tree_tab)
        node_tree_tab._parent.setTabIcon(
            node_tree_tab_index, self.node_tree_icon
        )
        # Connect the editor destruction signal to the tree display
        custom_editor.destroyed.connect(node_tree_tab.parent_destroyed)
        # Focus the node tree tab
        parent.node_tree_tab._parent.setCurrentWidget(parent.node_tree_tab)
        # Display the nodes according to file type
        if parser == "PYTHON":
            # Get all the file information
            try:
                python_node_tree = functions.get_python_node_tree(
                    custom_editor.text()
                )
                parser_error = False
            except Exception as ex:
                # Exception, probably an error in the file's syntax
                python_node_tree = []
                parser_error = ex
            # Display the information in the tree tab
            parent.node_tree_tab.display_python_nodes_in_tree(
                custom_editor, python_node_tree, parser_error
            )
            new_keywords = [
                x.name for x in python_node_tree if x.type == "import"
            ]
            new_keywords.extend(
                [x.name for x in python_node_tree if x.type == "class"]
            )
            new_keywords.extend(
                [x.name for x in python_node_tree if x.type == "function"]
            )
            new_keywords.extend(
                [
                    x.name
                    for x in python_node_tree
                    if x.type == "global_variable"
                ]
            )
            custom_editor.set_lexer(
                lexers.CustomPython(
                    custom_editor, additional_keywords=new_keywords
                ),
                "PYTHON",
            )
        elif parser == "C":
            # Get all the file information
            try:
                result = functions.get_c_node_tree_with_ctags(
                    custom_editor.text()
                )
            except Exception as ex:
                parent.display.display_error(str(ex))
                return
            c_nodes = result
            # Display the information in the tree tab
            parent.node_tree_tab.display_c_nodes(custom_editor, c_nodes)
        elif parser == "NIM":
            # Get all the file information
            nim_nodes = functions.get_nim_node_tree(custom_editor.text())
            # Display the information in the tree tab
            parent.node_tree_tab.display_nim_nodes(custom_editor, nim_nodes)

    def show_nodes_in_document(self, custom_editor, parser):
        """Show the node tree of a parsed file in a "NODE TREE" Scintilla
        document in the upper window."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Check if the custom editor is valid
        if custom_editor is None:
            parent.display.display_error(
                "No document selected for node tree creation!"
            )
            parent.display.write_to_statusbar(
                "No document selected for node tree creation!", 5000
            )
            return
        # Check if the document type is Python or C
        if parser != "PYTHON" and parser != "C":
            parent.display.display_error("Document is not Python or C!")
            parent.display.write_to_statusbar(
                "Document is not Python or C", 5000
            )
            return

        # Nested hotspot function
        def create_hotspot(node_tab):
            # Create the hotspot boundaries
            hotspot_line = node_tab.lines() - 2
            hotspot_first_ch = node_tab.text(hotspot_line).index("-")
            hotspot_line_length = node_tab.lineLength(hotspot_line)
            hotspot_start = node_tab.positionFromLineIndex(
                hotspot_line, hotspot_first_ch
            )
            hotspot_end = node_tab.positionFromLineIndex(
                hotspot_line, hotspot_line_length
            )
            hotspot_length = hotspot_end - hotspot_start
            # Style the hotspot on the node tab
            node_tab.hotspots.style(
                node_tab, hotspot_start, hotspot_length, color=0xFF0000
            )

        # Create the function and connect the hotspot release signal to it
        def hotspot_release(position, modifiers):
            # Get the line and index at where the hotspot was clicked
            line, index = parent.node_tree_tab.lineIndexFromPosition(position)
            # Get the document name and focus on the tab with the document
            document_name = re.search(
                r"DOCUMENT\:\s*(.*)\n", parent.node_tree_tab.text(0)
            ).group(1)
            goto_line_number = int(
                re.search(
                    r".*\(line\:(\d+)\).*", parent.node_tree_tab.text(line)
                ).group(1)
            )
            # Find the document, set focus to it and go to the line the hotspot points to
            document_tab = parent.get_tab_by_name(document_name)
            # Check if the document was modified
            if document_tab is None:
                # Then it has stars(*) in the name
                document_tab = parent.get_tab_by_name(
                    "*{:s}*".format(document_name)
                )
            try:
                document_tab._parent.setCurrentWidget(document_tab)
                document_tab.goto_line(goto_line_number)
            except:
                return

        # Define a name for the NODE tab
        node_tree_tab_name = "NODE TREE/LIST"
        # Find the "NODE" tab in the tab widgets
        parent.node_tree_tab = parent.get_tab_by_name(node_tree_tab_name)
        if parent.node_tree_tab:
            parent.node_tree_tab._parent.close_tab(node_tree_tab_name)
        # Create a new NODE tab in the upper tab widget
        parent.node_tree_tab = parent.get_largest_window().plain_add_document(
            node_tree_tab_name
        )
        parent.node_tree_tab.current_icon = self.node_tree_icon
        # Set the NODE document to be ReadOnly
        parent.node_tree_tab.setReadOnly(True)
        parent.node_tree_tab.setText("")
        parent.node_tree_tab.SendScintilla(
            qt.QsciScintillaBase.SCI_STYLECLEARALL
        )
        parent.node_tree_tab.parentWidget().setCurrentWidget(
            parent.node_tree_tab
        )
        # Check if the custom editor is valid
        if (
            isinstance(custom_editor, gui.forms.customeditor.CustomEditor)
            == False
        ):
            message = "The editor is not valid!"
            parent.display.display_error(message)
            parent.display.write_to_statusbar(message, 2000)
            return
        else:
            # Check the type of document in the custom editor
            parser = custom_editor.current_file_type
        # Get the node tree for the current widget in the custom editor
        if parser == "PYTHON":
            import_nodes, class_tree_nodes, function_nodes, global_vars = (
                functions.get_python_node_list(custom_editor.text())
            )
            init_space = "    -"
            extra_space = "     "
            # Display document name, used for finding the tab when clicking the hotspot
            document_name = os.path.basename(custom_editor.save_name)
            document_text = "DOCUMENT: {:s}\n".format(document_name)
            parent.node_tree_tab.append(document_text)
            parent.node_tree_tab.append("TYPE: {:s}\n\n".format(parser))
            # Display class nodes
            parent.node_tree_tab.append("CLASS/METHOD TREE:\n")
            for node in class_tree_nodes:
                node_text = init_space + str(node[0].name) + "(line:"
                node_text += str(node[0].lineno) + ")\n"
                parent.node_tree_tab.append(node_text)
                create_hotspot(parent.node_tree_tab)
                for child in node[1]:
                    child_text = (child[0] + 1) * extra_space + init_space
                    child_text += str(child[1].name) + "(line:"
                    child_text += str(child[1].lineno) + ")\n"
                    parent.node_tree_tab.append(child_text)
                    create_hotspot(parent.node_tree_tab)
                parent.node_tree_tab.append("\n")
            # Check if there were any nodes found
            if class_tree_nodes == []:
                parent.node_tree_tab.append("No classes found\n\n")
            # Display function nodes
            parent.node_tree_tab.append("FUNCTIONS:\n")
            for func in function_nodes:
                func_text = init_space + func.name + "(line:"
                func_text += str(func.lineno) + ")\n"
                parent.node_tree_tab.append(func_text)
                create_hotspot(parent.node_tree_tab)
            # Check if there were any nodes found
            if function_nodes == []:
                parent.node_tree_tab.append("No functions found\n\n")
            # Connect the hotspot mouserelease signal
            parent.node_tree_tab.SCN_HOTSPOTRELEASECLICK.connect(
                hotspot_release
            )
        elif parser == "C":
            function_nodes = functions.get_c_function_list(custom_editor.text())
            init_space = "    -"
            extra_space = "     "
            # Display document name, used for finding the tab when clicking the hotspot
            document_name = os.path.basename(custom_editor.save_name)
            document_text = "DOCUMENT: {:s}\n".format(document_name)
            parent.node_tree_tab.append(document_text)
            parent.node_tree_tab.append("TYPE: {:s}\n\n".format(parser))
            # Display functions
            parent.node_tree_tab.append("FUNCTION LIST:\n")
            for func in function_nodes:
                node_text = init_space + func[0] + extra_space
                node_text += "(line:" + str(func[1]) + ")\n"
                parent.node_tree_tab.append(node_text)
                create_hotspot(parent.node_tree_tab)
            # Check if there were any nodes found
            if function_nodes == []:
                parent.node_tree_tab.append("No functions found\n\n")
            # Connect the hotspot mouserelease signal
            parent.node_tree_tab.SCN_HOTSPOTRELEASECLICK.connect(
                hotspot_release
            )

    def show_found_files(self, search_text, file_list, directory):
        """Function for selecting which type of node tree will be displayed."""
        if self.node_view_type == data.NodeDisplayType.DOCUMENT:
            self.show_found_files_in_document(file_list, directory)
        elif self.node_view_type == data.NodeDisplayType.TREE:
            self.show_found_files_in_tree(search_text, file_list, directory)

    def show_found_files_in_document(self, file_list, directory):
        """Display the found files returned from the find_files system function
        in the REPL MESSAGES tab."""
        # Create lines that will be displayed in the REPL messages window
        display_file_info = []
        for file in file_list:
            display_file_info.append(
                "{:s} ({:s})".format(os.path.basename(file), file)
            )
        # Display all found files
        self._parent.display.display_message_with_type(
            "Found {:d} files:".format(len(file_list))
        )

        # Use scintilla HOTSPOTS to create clickable file links
        # Create the function and connect the hotspot release signal to it
        def hotspot_release(position, modifiers):
            # Get the line and index at where the hotspot was clicked
            line, index = self._parent.messages_tab.lineIndexFromPosition(
                position
            )
            file = (
                re.search(r".*\((.*)\)", self._parent.messages_tab.text(line))
                .group(1)
                .replace("\n", "")
            )
            # Open the files
            self._parent.open_file(file)
            # Because open_file updates the new CWD in the REPL MESSAGES,
            # it is needed to set the cursor back to where the hotspot was clicked
            self._parent.messages_tab.setCursorPosition(line, index)

        self._parent.messages_tab.SCN_HOTSPOTRELEASECLICK.connect(
            hotspot_release
        )
        # Get the start position
        pos = self._parent.messages_tab.getCursorPosition()
        hotspot_start = self._parent.messages_tab.positionFromLineIndex(
            pos[0], pos[1]
        )
        # self.display.display_message_with_type("\n".join(found_files))
        self._parent.display.display_message_with_type(
            "\n".join(display_file_info)
        )
        # Get the end position
        pos = self._parent.messages_tab.getCursorPosition()
        hotspot_end = self._parent.messages_tab.positionFromLineIndex(
            pos[0], pos[1]
        )
        # Style the hotspot on the node tab
        self._parent.messages_tab.hotspots.style(
            self._parent.messages_tab,
            hotspot_start,
            hotspot_end,
            color=0xFF0000,
        )

    def show_directory_tree(self, directory):
        """Display the directory information in a TreeDisplay widget."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Define a name for the FOUND FILES tab
        found_files_tab_name = "File/directory tree"
        # Find the "FILE/DIRECTORY TREE" tab in the tab widgets
        parent.found_files_tab = parent.get_tab_by_name(found_files_tab_name)
        if parent.found_files_tab:
            parent.found_files_tab._parent.close_tab(found_files_tab_name)

        # Create a new FOUND FILES tab in the upper tab widget
        found_files_tab = parent.get_largest_window().tree_add_tab(
            found_files_tab_name
        )
        found_files_tab.icon_manipulator.set_icon(
            found_files_tab, self.system_show_cwd_tree_icon
        )
        # Focus the node tree tab
        found_files_tab._parent.setCurrentWidget(found_files_tab)
        # Display the directory information in the tree tab
        found_files_tab.display_directory_tree(directory)
        found_files_tab.setFocus()

    def create_filetree(self, directory, in_project, excluded_directories=[]):
        """Display the directory information in a filetree widget."""
        # Define references directly to the parent and
        # mainform for performance and clarity
        parent = self._parent
        # Define a name for the tree tab
        project_tree_tab_name = data.tab_names["filetree"]
        # Find the tree tab in the tab widgets
        parent.project_tree_tab = parent.get_tab_by_name(project_tree_tab_name)
        if parent.project_tree_tab:
            parent.project_tree_tab._parent.close_tab(project_tree_tab_name)

        # Create the project tree raw or in a TabWidget
        if parent.filetree_tabwidget is not None:
            project_tree = parent.filetree_tabwidget.filetree_add_tab(
                project_tree_tab_name,
                directory,
                in_project,
                excluded_directories,
            )
            project_tree.icon_manipulator.set_icon(
                project_tree, self.system_show_cwd_tree_icon
            )
            # Focus the node tree tab
            project_tree._parent.setCurrentWidget(project_tree)
            project_tree.setFocus()
        else:
            exclude_directories = [
                data.current_project.get_treepath_seg().get_relpath(
                    "BUILD_DIR"
                ),
            ]
            project_tree = gui.forms.newfiletree.NewFiletree(
                None, parent, directory, exclude_directories=exclude_directories
            )
        return project_tree

    def add_terminal(self):
        # Get the window
        window = self._parent.get_window_by_indication()
        if window is None:
            window = self._parent.get_largest_window()
        if window is None:
            self._parent.display.display_error("Layout not yet initialized!")
            return
        # Add the terminal
        window.terminal_add_tab()
        # Set focus to the terminal
        window.currentWidget().setFocus()

    def show_found_files_in_tree(self, search_text, file_list, directory):
        """Display the found files returned from the find_files system function
        in a TreeDisplay widget."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Define a name for the FOUND FILES tab
        found_files_tab_name = "Found files"
        # Find the "FOUND FILES" tab in the tab widgets
        parent.found_files_tab = parent.get_tab_by_name(found_files_tab_name)
        if parent.found_files_tab:
            parent.found_files_tab._parent.close_tab(found_files_tab_name)
        found_files_tab = parent.found_files_tab
        # Create a new FOUND FILES tab in the upper tab widget
        found_files_tab = parent.get_largest_window().tree_add_tab(
            found_files_tab_name
        )
        found_files_tab.icon_manipulator.set_icon(
            found_files_tab, self.system_found_files_icon
        )
        # Focus the node tree tab
        found_files_tab._parent.setCurrentWidget(found_files_tab)
        # Display the found files information in the tree tab
        found_files_tab.display_found_files(search_text, file_list, directory)

    def show_found_files_with_lines_in_tree(
        self, search_text, file_list, directory
    ):
        """Display the found files with line information returned from the
        find_in_files and replace_in_files system function in a TreeDisplay."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Define a name for the FOUND FILES tab
        found_files_tab_name = "Found files"
        # Find the FOUND FILES tab in the tab widgets
        parent.found_files_tab = parent.get_tab_by_name(found_files_tab_name)
        if parent.found_files_tab:
            parent.found_files_tab._parent.close_tab(found_files_tab_name)
        found_files_tab = parent.found_files_tab
        # Create a new FOUND FILES tab in the upper tab widget
        found_files_tab = parent.get_largest_window().tree_add_tab(
            found_files_tab_name
        )
        found_files_tab.icon_manipulator.set_icon(
            found_files_tab, self.system_found_files_icon
        )
        # Focus the node tree tab
        found_files_tab._parent.setCurrentWidget(found_files_tab)
        # Display the found files information in the tree tab
        found_files_tab.display_found_files_with_lines(
            search_text, file_list, directory
        )

    def show_replaced_text_in_files_in_tree(
        self, search_text, replace_text, file_list, directory
    ):
        """Display the found files with line information returned from the
        find_in_files and replace_in_files system function in a TreeDisplay."""
        # Define references directly to the parent and mainform for performance and clarity
        parent = self._parent
        # Define a name for the FOUND FILES tab
        found_files_tab_name = "Replacements in files"
        # Find the FOUND FILES tab in the tab widgets
        parent.found_files_tab = parent.get_tab_by_name(found_files_tab_name)
        if parent.found_files_tab:
            parent.found_files_tab._parent.close_tab(found_files_tab_name)
        # Create a new FOUND FILES tab in the upper tab widget
        parent.found_files_tab = parent.get_largest_window().tree_add_tab(
            found_files_tab_name
        )
        parent.found_files_tab.icon_manipulator.set_icon(
            parent.found_files_tab, self.system_replace_in_files_icon
        )
        # Focus the node tree tab
        parent.found_files_tab._parent.setCurrentWidget(parent.found_files_tab)
        # Display the found files information in the tree tab
        parent.found_files_tab.display_replacements_in_files(
            search_text, replace_text, file_list, directory
        )

    def show_text_difference(
        self, text_1, text_2, text_name_1=None, text_name_2=None
    ):
        """Display the difference between two texts in a TextDiffer."""
        # Check if text names are valid
        if text_name_1 is None:
            text_name_1 = "TEXT 1"
        if text_name_2 is None:
            text_name_2 = "TEXT 2"
        # Create a reference to the main form for less typing
        parent = self._parent
        # Create and initialize a text differ
        text_differ = gui.helpers.textdiffer.TextDiffer(
            parent.get_largest_window(),
            parent,
            text_1,
            text_2,
            text_name_1,
            text_name_2,
        )
        # Find the "DIFF(...)" tab in the tab widgets and close it
        diff_tab_string = "DIFF("
        diff_tab = parent.get_tab_by_string_in_name(diff_tab_string)
        if diff_tab:
            diff_tab_index = diff_tab._parent.indexOf(diff_tab)
            diff_tab._parent.close_tab(diff_tab_index)
        # Add the created text differ to the main window
        diff_index = parent.get_largest_window().addTab(
            text_differ, "DIFF({:s} / {:s})".format(text_name_1, text_name_2)
        )
        # Set focus to the text differ tab
        parent.get_largest_window().setCurrentIndex(diff_index)

    internal_error_flag = False

    def show_internal_error(self, message: Optional[str]) -> None:
        if not self.internal_error_flag:
            self.internal_error_flag = True
            text, catch_click = helpdocs.help_texts.report_internal_error(
                message
            )
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="INTERNAL ERROR",
                text=text,
                text_click_func=catch_click,
            )
            self.internal_error_flag = False
            return

    def show_messages_window(self, *args):
        if not self.messages_window.isVisible():
            tabs = self._parent.get_dashboard_window()
            if tabs is None:
                tabs = self._parent.get_largest_window()
            if tabs:
                tabs.messages_add(
                    data.tab_names["messages"],
                    existing_messages=self.messages_window,
                )
        else:
            parent = self.messages_window.parent()
            while parent is not None:
                if isinstance(parent, gui.forms.tabwidget.TabWidget):
                    break
                parent = parent.parent()
            tabs = parent
            if tabs is not None:
                tabs.setCurrentWidget(self.messages_window)
        if tabs is not None:
            self._parent.view.indicate_window(tabs)
        # Reset button icon
        self.messages_button_reset()

    def create_lexers_menu(
        self,
        menu_name,
        set_lexer_func,
        store_menu_to_mainform=True,
        custom_parent=None,
    ):
        """Create a lexer menu. Currently used in the View menu and the
        gui.forms.customeditor.CustomEditor tab menu.

        Parameter set_lexer_func has to have:
            - parameter lexer: a lexers.Lexer object
            - parameter lexer_name: a string
        """
        set_lexer = set_lexer_func

        # Nested function for creating an action
        def create_action(
            name, key_combo, statustip, icon, function, menu_parent
        ):
            action = qt.QAction(name, menu_parent)
            # Key combination
            if (
                (key_combo is not None)
                and (key_combo != "")
                and (key_combo != [])
            ):
                if isinstance(key_combo, list):
                    action.setShortcuts(key_combo)
                else:
                    action.setShortcut(key_combo)
            action.setStatusTip(statustip)
            # Icon and pixmap
            action.pixmap = None
            if icon is not None:
                action.setIcon(iconfunctions.get_qicon(icon))
                action.pixmap = iconfunctions.get_qpixmap(icon, 32, 32)
            # Function
            if function is not None:

                def execute_function(*args):
                    function()

                action.triggered.connect(execute_function)
            action.function = function
            self._parent.menubar_functions[function.__name__] = function
            # Check if there is a tab character in the function
            # name and remove the part of the string after it
            if "\t" in name:
                name = name[: name.find("\t")]
            # Toggle action according to passed
            # parameter and return the action
            action.setEnabled(True)
            return action

        # The owner of the lexers menu is always the MainWindow
        if custom_parent is not None:
            parent = custom_parent
        else:
            parent = self._parent
        lexers_menu = gui.templates.basemenu.BaseMenu(menu_name, parent)

        def create_lexer(lexer, description):
            func = functools.partial(set_lexer, lexer, description)
            func.__name__ = "set_lexer_{}".format(lexer.__name__)
            return func

        NONE_action = create_action(
            "No lexer",
            None,
            "Disable document lexer",
            f"icons/file/file.png",
            create_lexer(lexers.Text, "Plain text"),
            lexers_menu,
        )
        ADA_action = create_action(
            "Ada",
            None,
            "Change document lexer to: Ada",
            "icons/languages/ada.png",
            create_lexer(lexers.Ada, "Ada"),
            lexers_menu,
        )
        ASSEMBLY_action = create_action(
            "Assembly",
            None,
            "Change document lexer to: Assembly",
            "icons/languages/assembly.png",
            create_lexer(lexers.Assembly, "Assembly"),
            lexers_menu,
        )
        BASH_action = create_action(
            "Bash",
            None,
            "Change document lexer to: Bash",
            "icons/languages/bash.png",
            create_lexer(lexers.Bash, "Bash"),
            lexers_menu,
        )
        BATCH_action = create_action(
            "Batch",
            None,
            "Change document lexer to: Batch",
            "icons/languages/batch.png",
            create_lexer(lexers.Batch, "Batch"),
            lexers_menu,
        )
        CMAKE_action = create_action(
            "CMake",
            None,
            "Change document lexer to: CMake",
            "icons/languages/cmake.png",
            create_lexer(lexers.CMake, "CMake"),
            lexers_menu,
        )
        C_CPP_action = create_action(
            "C / C++",
            None,
            "Change document lexer to: C / C++",
            "icons/languages/cpp.png",
            create_lexer(lexers.CustomC, "C / C++"),
            lexers_menu,
        )
        #            CSS_action = create_action(
        #                'CSS',
        #                None,
        #                'Change document lexer to: CSS',
        #                'icons/languages/css.png',
        #                create_lexer(lexers.CSS, 'CSS'),
        #                lexers_menu
        #            )
        #            D_action = create_action(
        #                'D',
        #                None,
        #                'Change document lexer to: D',
        #                'icons/languages/d.png',
        #                create_lexer(lexers.D, 'D'),
        #                lexers_menu
        #            )
        #            FORTRAN_action = create_action(
        #                'Fortran',
        #                None,
        #                'Change document lexer to: Fortran',
        #                'icons/languages/fortran.png',
        #                create_lexer(lexers.Fortran, 'Fortran'),
        #                lexers_menu
        #            )
        HTML_action = create_action(
            "HTML",
            None,
            "Change document lexer to: HTML",
            "icons/languages/html.png",
            create_lexer(lexers.HTML, "HTML"),
            lexers_menu,
        )
        #            LUA_action = create_action(
        #                'Lua',
        #                None,
        #                'Change document lexer to: Lua',
        #                'icons/languages/lua.png',
        #                create_lexer(lexers.Lua, 'Lua'),
        #                lexers_menu
        #            )
        MAKEFILE_action = create_action(
            "MakeFile",
            None,
            "Change document lexer to: MakeFile",
            f"icons/file/file_mk.png",
            create_lexer(lexers.Makefile, "MakeFile"),
            lexers_menu,
        )
        #            MATLAB_action = create_action(
        #                'Matlab',
        #                None,
        #                'Change document lexer to: Matlab',
        #                'icons/languages/matlab.png',
        #                create_lexer(lexers.Matlab, 'Matlab'),
        #                lexers_menu
        #            )
        #            NIM_action = create_action(
        #                'Nim',
        #                None,
        #                'Change document lexer to: Nim',
        #                'icons/languages/nim.png',
        #                create_lexer(lexers.Nim, 'Nim'),
        #                lexers_menu
        #            )
        #            OBERON_action = create_action(
        #                'Oberon / Modula',
        #                None,
        #                'Change document lexer to: Oberon / Modula',
        #                'icons/languages/oberon.png',
        #                create_lexer(lexers.Oberon, 'Oberon / Modula'),
        #                lexers_menu
        #            )
        #            PASCAL_action = create_action(
        #                'Pascal',
        #                None,
        #                'Change document lexer to: Pascal',
        #                'icons/languages/pascal.png',
        #                create_lexer(lexers.Pascal, 'Pascal'),
        #                lexers_menu
        #            )
        #            PERL_action = create_action(
        #                'Perl',
        #                None,
        #                'Change document lexer to: Perl',
        #                'icons/languages/perl.png',
        #                create_lexer(lexers.Perl, 'Perl'),
        #                lexers_menu
        #            )
        PYTHON_action = create_action(
            "Python",
            None,
            "Change document lexer to: Python",
            "icons/languages/python.png",
            create_lexer(lexers.Python, "Python"),
            lexers_menu,
        )
        #            RUBY_action = create_action(
        #                'Ruby',
        #                None,
        #                'Change document lexer to: Ruby',
        #                'icons/languages/ruby.png',
        #                create_lexer(lexers.Ruby, 'Ruby'),
        #                lexers_menu
        #            )
        #            ROUTEROS_action = create_action(
        #                'RouterOS',
        #                None,
        #                'Change document lexer to: RouterOS',
        #                'icons/languages/routeros.png',
        #                create_lexer(lexers.RouterOS, 'RouterOS'),
        #                lexers_menu
        #            )
        #            SQL_action = create_action(
        #                'SQL',
        #                None,
        #                'Change document lexer to: SQL',
        #                'icons/languages/sql.png',
        #                create_lexer(lexers.SQL, 'SQL'),
        #                lexers_menu
        #            )
        TCL_action = qt.QAction("TCL", lexers_menu)
        TCL_action.setIcon(iconfunctions.get_qicon("icons/languages/tcl.png"))
        TCL_action.triggered.connect(
            functools.partial(set_lexer, lexers.TCL, "TCL")
        )
        TCL_action = create_action(
            "TCL",
            None,
            "Change document lexer to: TCL",
            "icons/languages/tcl.png",
            create_lexer(lexers.TCL, "TCL"),
            lexers_menu,
        )
        #            TEX_action = create_action(
        #                'TeX',
        #                None,
        #                'Change document lexer to: TeX',
        #                'icons/languages/tex.png',
        #                create_lexer(lexers.TeX, 'TeX'),
        #                lexers_menu
        #            )
        #            VERILOG_action = create_action(
        #                'Verilog',
        #                None,
        #                'Change document lexer to: Verilog',
        #                'icons/languages/verilog.png',
        #                create_lexer(lexers.Verilog, 'Verilog'),
        #                lexers_menu
        #            )
        #            VHDL_action = create_action(
        #                'VHDL',
        #                None,
        #                'Change document lexer to: VHDL',
        #                'icons/languages/vhdl.png',
        #                create_lexer(lexers.VHDL, 'VHDL'),
        #                lexers_menu
        #            )
        XML_action = create_action(
            "XML",
            None,
            "Change document lexer to: XML",
            "icons/languages/xml.png",
            create_lexer(lexers.XML, "XML"),
            lexers_menu,
        )
        JSON_action = create_action(
            "JSON",
            None,
            "Change document lexer to: JSON",
            "icons/languages/json.png",
            create_lexer(lexers.JSON, "JSON"),
            lexers_menu,
        )
        #            YAML_action = create_action(
        #                'YAML',
        #                None,
        #                'Change document lexer to: YAML',
        #                'icons/languages/yaml.png',
        #                create_lexer(lexers.YAML, 'YAML'),
        #                lexers_menu
        #            )
        #            CoffeeScript_action = create_action(
        #                'CoffeeScript',
        #                None,
        #                'Change document lexer to: CoffeeScript',
        #                'icons/languages/coffeescript.png',
        #                create_lexer(lexers.CoffeeScript, 'CoffeeScript'),
        #                lexers_menu
        #            )
        #            CSharp_action = create_action(
        #                'C#',
        #                None,
        #                'Change document lexer to: C#',
        #                'icons/languages/csharp.png',
        #                create_lexer(lexers.CPP, 'C#'),
        #                lexers_menu
        #            )
        #            Java_action = create_action(
        #                'Java',
        #                None,
        #                'Change document lexer to: Java',
        #                'icons/languages/java.png',
        #                create_lexer(lexers.Java, 'Java'),
        #                lexers_menu
        #            )
        #            JavaScript_action = create_action(
        #                'JavaScript',
        #                None,
        #                'Change document lexer to: JavaScript',
        #                'icons/languages/javascript.png',
        #                create_lexer(lexers.JavaScript, 'JavaScript'),
        #                lexers_menu
        #            )
        #            Octave_action = create_action(
        #                'Octave',
        #                None,
        #                'Change document lexer to: Octave',
        #                'icons/languages/octave.png',
        #                create_lexer(lexers.Octave, 'Octave'),
        #                lexers_menu
        #            )
        #            PostScript_action = create_action(
        #                'PostScript',
        #                None,
        #                'Change document lexer to: PostScript',
        #                'icons/languages/postscript.png',
        #                create_lexer(lexers.PostScript, 'PostScript'),
        #                lexers_menu
        #            )
        #            Fortran77_action = create_action(
        #                'Fortran77',
        #                None,
        #                'Change document lexer to: Fortran77',
        #                'icons/languages/fortran77.png',
        #                create_lexer(lexers.Fortran77, 'Fortran77'),
        #                lexers_menu
        #            )
        #            IDL_action = create_action(
        #                'IDL',
        #                None,
        #                'Change document lexer to: IDL',
        #                'icons/languages/idl.png',
        #                create_lexer(lexers.IDL, 'IDL'),
        #                lexers_menu
        #            )
        lexers_menu.addAction(NONE_action)
        lexers_menu.addSeparator()
        lexers_menu.addAction(ADA_action)
        lexers_menu.addAction(ASSEMBLY_action)
        lexers_menu.addAction(BASH_action)
        lexers_menu.addAction(BATCH_action)
        lexers_menu.addAction(CMAKE_action)
        lexers_menu.addAction(C_CPP_action)
        #            lexers_menu.addAction(CoffeeScript_action)
        #            lexers_menu.addAction(CSharp_action)
        #            lexers_menu.addAction(CSS_action)
        #            lexers_menu.addAction(D_action)
        #            lexers_menu.addAction(Fortran77_action)
        #            lexers_menu.addAction(FORTRAN_action)
        lexers_menu.addAction(HTML_action)
        lexers_menu.addAction(JSON_action)
        #            lexers_menu.addAction(IDL_action)
        #            lexers_menu.addAction(Java_action)
        #            lexers_menu.addAction(JavaScript_action)
        #            lexers_menu.addAction(LUA_action)
        lexers_menu.addAction(MAKEFILE_action)
        #            lexers_menu.addAction(MATLAB_action)
        #            lexers_menu.addAction(NIM_action)
        #            lexers_menu.addAction(OBERON_action)
        #            lexers_menu.addAction(Octave_action)
        #            lexers_menu.addAction(PASCAL_action)
        #            lexers_menu.addAction(PERL_action)
        #            lexers_menu.addAction(PostScript_action)
        lexers_menu.addAction(PYTHON_action)
        #            lexers_menu.addAction(RUBY_action)
        #            lexers_menu.addAction(ROUTEROS_action)
        #            lexers_menu.addAction(SQL_action)
        #            lexers_menu.addAction(TCL_action)
        #            lexers_menu.addAction(TEX_action)
        #            lexers_menu.addAction(VERILOG_action)
        #            lexers_menu.addAction(VHDL_action)
        lexers_menu.addAction(XML_action)
        #            lexers_menu.addAction(YAML_action)
        # Clean-up the stored menus
        """
        This is needed only because the lexer menu is created on the fly!
        If this clean-up is ommited, then try clicking the gui.forms.customeditor.CustomEditor lexer
        menu button 20x times and watch the memory usage ballon up!
        """
        for i in range(len(self.stored_menus)):
            # Delete the QObjects by setting it's parent to None
            for l in self.stored_menus[i].actions():
                l.setParent(None)
            self.stored_menus[i].setParent(None)
        self.stored_menus = []
        # Add the newly created menu to the internal list for future cleaning
        if store_menu_to_mainform == True:
            self.stored_menus.append(lexers_menu)
        # Return the created menu
        return lexers_menu


class Bookmarks:
    """All bookmark functionality."""

    # Class varibles
    parent = None
    # List of all the bookmarks
    marks = None

    def __init__(self, parent):
        """Initialization of the Bookmarks object instance."""
        # Get the reference to the MainWindow parent object instance
        self._parent = parent
        # Initialize all the bookmarks
        self.init()

    def init(self):
        self.marks = {}
        for i in range(10):
            self.marks[i] = {
                "editor": None,
                "line": None,
                "marker-handle": None,
            }

    def add(self, editor, line):
        # Bookmarks should only work in editors
        if (
            isinstance(editor, gui.forms.customeditor.CustomEditor) == False
            or editor.embedded == True
        ):
            return
        for i in range(10):
            if (
                self.marks[i]["editor"] is None
                and self.marks[i]["line"] is None
            ):
                self.marks[i]["editor"] = editor
                self.marks[i]["line"] = line
                self.marks[i]["handle"] = None
                self._parent.display.display_message_with_type(
                    "Bookmark '{:d}' was added!".format(i),
                    message_type=data.MessageType.SUCCESS,
                )
                return i
        else:
            self._parent.display.display_error(
                "All ten bookmarks are occupied!"
            )
            return None

    def add_mark_by_number(self, editor, line, mark_number):
        # Bookmarks should only work in editors
        if (
            isinstance(editor, gui.forms.customeditor.CustomEditor) == False
            or editor.embedded == True
        ):
            return
        # Clear the selected marker if it is not empty
        if (
            self.marks[mark_number]["editor"] is not None
            and self.marks[mark_number]["line"] is not None
        ):
            self.marks[mark_number]["editor"].bookmarks.toggle_at_line(
                self.marks[mark_number]["line"]
            )
            self.marks[mark_number]["editor"] = None
            self.marks[mark_number]["line"] = None
            self.marks[mark_number]["handle"] = None
        # Check if there is a bookmark already at the selected editor line
        for i in range(10):
            if (
                self.marks[i]["editor"] == editor
                and self.marks[i]["line"] == line
            ):
                self.marks[i]["editor"].bookmarks.toggle_at_line(
                    self.marks[i]["line"]
                )
                break
        # Set and store the marker on the editor
        handle = editor.bookmarks.add_marker_at_line(line)
        self.marks[mark_number]["editor"] = editor
        self.marks[mark_number]["line"] = line
        self.marks[mark_number]["handle"] = handle
        self._parent.display.display_message_with_type(
            "Bookmark '{:d}' was added!".format(mark_number),
            message_type=data.MessageType.SUCCESS,
        )

    def clear(self):
        cleared_any = False
        for i in range(10):
            if (
                self.marks[i]["editor"] is None
                and self.marks[i]["line"] is None
            ):
                self.marks[i]["editor"].bookmarks.toggle_at_line(
                    self.marks[i]["line"]
                )
                self.marks[i]["editor"] = None
                self.marks[i]["line"] = None
                self.marks[i]["handle"] = None
                cleared_any = True
        if cleared_any == False:
            self._parent.display.display_message_with_type(
                "Bookmarks are clear.", message_type=data.MessageType.WARNING
            )
            return

    def remove_by_number(self, mark_number):
        if self.bounds_check(mark_number) == False:
            return
        self.marks[mark_number]["editor"] = None
        self.marks[mark_number]["line"] = None
        self.marks[mark_number]["handle"] = None

    def remove_by_reference(self, editor, line):
        for i in range(10):
            if (
                self.marks[i]["editor"] == editor
                and self.marks[i]["line"] == line
            ):
                self.marks[i]["editor"] = None
                self.marks[i]["line"] = None
                self.marks[i]["handle"] = None
                self._parent.display.display_message_with_type(
                    "Bookmark '{:d}' was removed!".format(i),
                    message_type=data.MessageType.SUCCESS,
                )
                break
        else:
            self._parent.display.display_error("Bookmark not found!")

    def remove_editor_all(self, editor):
        """Remove all bookmarks of an editor."""
        removed_bookmarks = []
        for i in range(10):
            if self.marks[i]["editor"] == editor:
                self.marks[i]["editor"] = None
                self.marks[i]["line"] = None
                self.marks[i]["handle"] = None
                removed_bookmarks.append(i)
        if removed_bookmarks != []:
            close_message = "Bookmarks: "
            close_message += ", ".join(str(mark) for mark in removed_bookmarks)
            close_message += "\nwere removed."
            self._parent.display.display_message_with_type(
                close_message, message_type=data.MessageType.SUCCESS
            )

    def check(self, editor, line):
        for i in range(10):
            if (
                self.marks[i]["editor"] == editor
                and self.marks[i]["line"] == line
            ):
                return i
        else:
            return None

    def bounds_check(self, mark_number):
        if mark_number < 0 or mark_number > 9:
            self._parent.display.display_error("Bookmarks only go from 0 to 9!")
            return False
        else:
            return True

    def goto(self, mark_number):
        if self.bounds_check(mark_number) == False:
            return
        if (
            self.marks[mark_number]["editor"] is None
            and self.marks[mark_number]["line"] is None
        ):
            self._parent.display.display_message_with_type(
                "Bookmark '{:d}' is empty!".format(mark_number),
                message_type=data.MessageType.WARNING,
            )
        else:
            editor = self.marks[mark_number]["editor"]
            line = self.marks[mark_number]["line"]
            # Focus the stored editor and it's parent tab widget
            editor._parent.setCurrentWidget(editor)
            # Go to the stored line
            editor.goto_line(line)


class Projects:
    """Project functionality."""

    # Class varibles
    _parent = None
    # Console references
    clean_console = None
    build_console = None
    ocd_console = None
    gdb_console = None
    # Widget references
    filetree = None
    dashboard = None
    sa_tab = None
    diagnostics_window = None
    symbols_window = None
    pinconfigurator_window = None
    debugger_window = None
    pieces_window = None
    new_dashboard_window = None
    chipconfigurator_window = None
    memory_view_windows = {}
    # Flags
    dashboard_save_flag = False

    def __init__(self, parent: MainWindow) -> None:
        # Get the reference to the MainWindow parent object instance
        self._parent: MainWindow = parent
        return

    def disable_project_menubar_buttons(self):
        return
        #            self._parent.project_import_action.setEnabled(False)
        self._parent.project_save_action.setEnabled(False)
        self._parent.project_clone_action.setEnabled(False)
        self._parent.project_rename_action.setEnabled(False)
        self._parent.show_dashboard_action.setEnabled(False)
        self._parent.show_sa_tab_action.setEnabled(False)
        self._parent.show_filetree_action.setEnabled(False)
        self._parent.project_close_action.setEnabled(False)

    def enable_project_menubar_buttons(self):
        return
        #            self._parent.project_import_action.setEnabled(True)
        self._parent.project_save_action.setEnabled(True)
        self._parent.project_clone_action.setEnabled(True)
        self._parent.project_rename_action.setEnabled(True)
        self._parent.show_dashboard_action.setEnabled(True)
        self._parent.show_sa_tab_action.setEnabled(True)
        self._parent.show_filetree_action.setEnabled(True)
        self._parent.project_close_action.setEnabled(True)

    def show_filetree(
        self, *args
    ) -> Optional[gui.forms.newfiletree.NewFiletree]:
        try:
            filetree_tab_name = data.tab_names["filetree"]
            if data.filetree is not None:
                filetree = self._parent.get_tab_by_name(filetree_tab_name)
                if filetree is not None:
                    if filetree._parent is not None:
                        filetree._parent.setCurrentWidget(filetree)
                else:
                    tabs = self._parent.get_largest_window()
                    tabs.addTab(data.filetree, filetree_tab_name)
                    tabs.setCurrentWidget(data.filetree)
                data.filetree.setFocus()
                return data.filetree
            if data.current_project is None:
                return None
            filetree = self._parent.display.create_filetree(
                data.current_project.get_proj_rootpath(),
                data.current_project,
                excluded_directories=[
                    data.current_project.get_treepath_seg().get_relpath(
                        "BUILD_DIR"
                    ),
                ],
            )
            data.signal_dispatcher.file_tree_goto_path.connect(
                self.filetree_goto_path
            )
            filetree.setFocus()
            return filetree
        except Exception as ex:
            self._parent.display.display_error(traceback.format_exc())
            traceback.print_exc()
        return None

    def filetree_goto_path(self, path, focus_filetree=None):
        if data.filetree is not None:
            pe = self._parent.get_tab_by_name("Filetree")
            if focus_filetree:
                try:
                    pe._parent.setCurrentWidget(pe)
                except Exception as e:
                    return
            if data.filetree.isVisible():
                data.filetree.goto_path(path, select=True)

    def show_dashboard(self, *args):
        try:
            dashboard_tab_name = data.tab_names["dashboard"]
            if data.dashboard is not None:
                dashboard = self._parent.get_tab_by_name(dashboard_tab_name)
                if dashboard is not None:
                    dashboard._parent.setCurrentWidget(dashboard)
                else:
                    tabs = self._parent.get_largest_window()
                    tabs.addTab(data.dashboard, dashboard_tab_name)
                    tabs.setCurrentWidget(data.dashboard)
                data.dashboard.setFocus()
                return data.dashboard

            dashboard = self._parent.get_tab_by_name(dashboard_tab_name)
            if dashboard is not None:
                dashboard._parent.close_tab(dashboard_tab_name)
            if self._parent.dashboard_tabwidget is None:
                new_dashboard = dashboard.chassis.dashboard.Dashboard(
                    self._parent, self
                )
            else:
                new_dashboard = (
                    self._parent.dashboard_tabwidget.dashboard_add_tab(
                        dashboard_tab_name
                    )
                )
                new_dashboard.icon_manipulator.set_icon(
                    new_dashboard,
                    iconfunctions.get_qicon("icons/gen/dashboard.png"),
                )

            # Connect the dashboard to the window communication system
            if not hasattr(new_dashboard, "_receive_signal_connected"):
                self._parent.connect_received_signal(new_dashboard.receive)
                new_dashboard._receive_signal_connected = True
            new_dashboard.setFocus()
            return new_dashboard
        except Exception as ex:
            self._parent.display.display_message_with_type(ex)
            traceback.print_exc()
        return None

    def show_sa_tab(self, *args):
        try:
            sa_tab_name = data.tab_names["source-analyzer"]
            if data.sa_tab is not None:
                sa_tab_tab = self._parent.get_tab_by_name(sa_tab_name)
                if sa_tab_tab is not None:
                    sa_tab_tab._parent.setCurrentWidget(sa_tab_tab)
                else:
                    tabs = self._parent.get_largest_window()
                    tabs.addTab(data.sa_tab, sa_tab_name)
                    tabs.setCurrentWidget(data.sa_tab)
                data.sa_tab.setFocus()
                return data.sa_tab

            satab_tab = self._parent.get_tab_by_name(sa_tab_name)
            if satab_tab is not None:
                satab_tab._parent.close_tab(sa_tab_name)
            if self._parent.sa_tabwidget is None:
                tabs = self._parent.get_largest_window()
                new_sa = sa_tab.chassis.sa_tab.SATab(self._parent, tabs)
            else:
                new_sa = self._parent.sa_tabwidget.source_analyzer_add_tab(
                    sa_tab_name
                )
                new_sa.icon_manipulator.set_icon(
                    new_sa,
                    iconfunctions.get_qicon("icons/gen/source_analyzer.png"),
                )

            # Connect the sa to the window communication system
            if not hasattr(new_sa, "_receive_signal_connected"):
                self._parent.connect_received_signal(new_sa.receive)
                new_sa._receive_signal_connected = True
            # new_sa.setFocus()
            return new_sa
        except Exception as ex:
            raise
            # self._parent.display.display_message_with_type(ex)
            # traceback.print_exc()
        return None

    def show_diagnostics(self, *args):
        tab_name = data.tab_names["diagnostics"]
        if self.diagnostics_window is None:
            self.initialize_diagnostics_window(tab_name)
        diagnostics_tab = self._parent.get_tab_by_name(tab_name)
        if diagnostics_tab is not None:
            diagnostics_tab._parent.setCurrentWidget(self.diagnostics_window)
        else:
            tabs = self._parent.get_largest_window()
            if tabs is not None:
                tabs.addTab(self.diagnostics_window, tab_name)
                tabs.setCurrentWidget(self.diagnostics_window)
            else:
                self._parent.display.display_error(
                    "Layout not initialized yet!"
                )
                return
        self.diagnostics_window.setFocus()
        return self.diagnostics_window

    def show_symbols(self):
        tab_name = data.tab_names["symbols"]
        if self.symbols_window is None:
            self.initialize_symbols_window(tab_name)
        symbols_tab = self._parent.get_tab_by_name(tab_name)
        if symbols_tab is not None:
            symbols_tab._parent.setCurrentWidget(self.symbols_window)
        else:
            tabs = self._parent.get_largest_window()
            if tabs is not None:
                tabs.addTab(self.symbols_window, tab_name)
                tabs.setCurrentWidget(self.symbols_window)
            else:
                self._parent.display.display_error(
                    "Layout not initialized yet!"
                )
                return
        self.symbols_window.setFocus()
        return self.symbols_window

    def show_pinconfigurator(self):
        tab_name = data.tab_names["pin-configurator"]
        pinconfigurator = self._parent.get_tab_by_name(tab_name)
        if pinconfigurator is not None:
            pinconfigurator._parent.setCurrentWidget(
                self.pinconfigurator_window
            )
        else:
            tabs = self._parent.get_largest_window()
            if tabs is not None:
                self.pinconfigurator_window = tabs.pinconfigurator_add(
                    tab_name,
                    data.current_project.get_proj_rootpath(),
                    data.current_project.get_chip().get_name(),
                )
                tabs.setCurrentWidget(self.pinconfigurator_window)
            else:
                self._parent.display.display_error(
                    "Layout not initialized yet!"
                )
                return
        if self.pinconfigurator_window is not None:
            # Had here this error before:
            # AttributeError: 'NoneType' object has no attribute 'setFocus'
            self.pinconfigurator_window.setFocus()
        return self.pinconfigurator_window

    def show_debugger(self):
        tab_name = data.tab_names["debugger"]
        if self.debugger_window is None:
            self.initialize_debugger_window(tab_name)
        debugger_tab = self._parent.get_tab_by_name(tab_name)
        if debugger_tab is not None:
            debugger_tab._parent.setCurrentWidget(self.debugger_window)
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.debugger_window, tab_name)
            tabs.setCurrentWidget(self.debugger_window)
        self.debugger_window.setFocus()
        return self.debugger_window

    def show_general_registers(self):
        return self.__show_memory_view("general-registers")

    def show_raw_memory(self, memory_type):
        return self.__show_raw_memory_view(memory_type)

    def show_variable_watch(self):
        return self.__show_memory_view("variable-watch")

    def __show_memory_view(self, typ):
        tab_name = data.tab_names[typ]
        if (
            tab_name not in self.memory_view_windows.keys()
            or self.memory_view_windows[tab_name] is None
        ):
            self.initialize_memory_window(typ, tab_name)
        general_register_tab = self._parent.get_tab_by_name(tab_name)
        if general_register_tab is not None:
            general_register_tab._parent.setCurrentWidget(
                self.memory_view_windows[tab_name]
            )
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.memory_view_windows[tab_name], tab_name)
            tabs.setCurrentWidget(self.memory_view_windows[tab_name])
        self.memory_view_windows[tab_name].setFocus()
        return self.memory_view_windows[tab_name]

    def __show_raw_memory_view(self, memory_type):
        typ = "raw-memory"
        tab_name = data.tab_names[typ].format(memory_type)
        if (
            tab_name not in self.memory_view_windows.keys()
            or self.memory_view_windows[tab_name] is None
        ):
            self.initialize_memory_window(typ, tab_name, memory_type)
        general_register_tab = self._parent.get_tab_by_name(tab_name)
        if general_register_tab is not None:
            general_register_tab._parent.setCurrentWidget(
                self.memory_view_windows[tab_name]
            )
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.memory_view_windows[tab_name], tab_name)
            tabs.setCurrentWidget(self.memory_view_windows[tab_name])
        self.memory_view_windows[tab_name].setFocus()
        return self.memory_view_windows[tab_name]

    def get_general_register_window(self):
        return self.memory_view_windows.get(data.tab_names["general-registers"])

    def get_raw_memory_window(self, memory_type):
        return self.memory_view_windows.get(
            data.tab_names["raw-memory"].format(memory_type)
        )

    def get_variable_watch_view(self):
        return self.memory_view_windows.get(data.tab_names["variable-watch"])

    def initialize_diagnostics_window(self, tab_name):
        # Get the CEC diagnostics
        diagnostics = (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_diagnostics()
        )
        # Create a diagnostics window
        diagnostics_tabwidget = self._parent.diagnostics_tabwidget
        if diagnostics_tabwidget is None:
            diagnostics_tabwidget = self._parent.get_largest_window()
        if diagnostics_tabwidget is None:
            self._parent.display.display_error("Layout not initialized yet!")
            return
        self.diagnostics_window = diagnostics_tabwidget.diagnostics_add(
            tab_name, diagnostics
        )
        # Focus back the diagnostics
        diagnostics_tabwidget.setCurrentWidget(self.diagnostics_window)

    def create_diagnostics_window(self):
        diagnostics = (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_diagnostics()
        )
        new_diagnostics = gui.helpers.diagnosticwindow.DiagnosticWindow(
            self._parent, self._parent, diagnostics
        )
        self.diagnostics_window = new_diagnostics

    def initialize_symbols_window(self, tab_name):
        # Get the CEC symbol handler
        symbolhandler = (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_symbolhandler()
        )
        # Create a symbol handler window
        symbols_tabwidget = self._parent.symbols_tabwidget
        if symbols_tabwidget is None:
            symbols_tabwidget = self._parent.get_largest_window()
        if symbols_tabwidget is None:
            self._parent.display.display_error("Layout not initialized yet!")
            return
        self.symbols_window = symbols_tabwidget.symbols_add(
            tab_name, symbolhandler
        )
        # Focus back the symbols
        symbols_tabwidget.setCurrentWidget(self.symbols_window)

    def create_symbols_window(self):
        symbolhandler = (
            components.sourceanalyzerinterface.SourceAnalysisCommunicator().get_symbolhandler()
        )
        new_symbols = gui.helpers.symbolwindow.SymbolWindow(
            self._parent, self._parent, symbolhandler
        )
        self.symbols_window = new_symbols

    def initialize_debugger_window(self, tab_name):
        # Create a symbol handler window
        debugger_tabwidget = self._parent.debugger_tabwidget
        if debugger_tabwidget is None:
            debugger_tabwidget = self._parent.get_largest_window()
        self.debugger_window = debugger_tabwidget.debugger_add(tab_name)
        # Focus back the debugger
        debugger_tabwidget.setCurrentWidget(self.debugger_window)

    def initialize_memory_window(self, typ, tab_name, memory_type=None):
        # Create a symbol handler window
        if tab_name not in self._parent.memory_view_tabwidgets.keys():
            self._parent.memory_view_tabwidgets[tab_name] = None
        tabwidget = self._parent.memory_view_tabwidgets[tab_name]
        if tabwidget is None:
            tabwidget = self._parent.get_largest_window()
        if typ == "general-registers":
            self.memory_view_windows[tab_name] = (
                tabwidget.general_registers_add(tab_name)
            )
        elif typ == "raw-memory":
            if memory_type is None:
                raise Exception("Memory-view has to have a type!")
            self.memory_view_windows[tab_name] = tabwidget.memory_add(
                tab_name, memory_type
            )
        elif typ == "variable-watch":
            self.memory_view_windows[tab_name] = tabwidget.variable_watch_add(
                tab_name
            )
        else:
            raise Exception("Unknown memory view type: {}".format(typ))
        # Focus back the debugger
        tabwidget.setCurrentWidget(self.memory_view_windows[tab_name])

    """
    Pieces
    """

    def show_pieces(self):
        tab_name = data.tab_names["pieces"]
        if self.pieces_window is None:
            self.initialize_pieces_window(tab_name)
        tab = self._parent.get_tab_by_name(tab_name)
        if tab is not None:
            tab._parent.setCurrentWidget(self.pieces_window)
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.pieces_window, tab_name)
            tabs.setCurrentWidget(self.pieces_window)
        self.pieces_window.setFocus()
        return self.pieces_window

    def initialize_pieces_window(self, tab_name: str) -> None:
        tabwidget = self._parent.pieces_tabwidget
        if tabwidget is None:
            tabwidget = self._parent.get_largest_window()
        current_project_path = functions.unixify_path(
            data.current_project.get_proj_rootpath()
        )
        self.pieces_window = tabwidget.pieces_add(
            tab_name, current_project_path
        )
        # Focus back the debugger
        tabwidget.setCurrentWidget(self.pieces_window)
        return

    """
    New Dashboard
    """

    def show_new_dashboard(self):
        tab_name = data.tab_names["new-dashboard"]
        if self.new_dashboard_window is None:
            self.initialize_new_dashboard_window(tab_name)
        tab = self._parent.get_tab_by_name(tab_name)
        if tab is not None:
            tab._parent.setCurrentWidget(self.new_dashboard_window)
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.new_dashboard_window, tab_name)
            tabs.setCurrentWidget(self.new_dashboard_window)
        self.new_dashboard_window.setFocus()
        return self.new_dashboard_window

    def initialize_new_dashboard_window(self, tab_name: str) -> None:
        tabwidget = self._parent.new_dashboard_tabwidget
        if (tabwidget is None) or (qt.sip.isdeleted(tabwidget)):
            self._parent.new_dashboard_tabwidget = None
            tabwidget = self._parent.get_largest_window()
        self.new_dashboard_window = tabwidget.new_dashboard_add(tab_name)
        # Focus back the debugger
        tabwidget.setCurrentWidget(self.new_dashboard_window)
        return

    """
    Chip Configurator
    """

    def show_chipconfigurator(self):
        tab_name = data.tab_names["chip-configurator"]
        if self.chipconfigurator_window is None:
            self.initialize_chipconfigurator_window(tab_name)
        tab = self._parent.get_tab_by_name(tab_name)
        if tab is not None:
            tab._parent.setCurrentWidget(self.chipconfigurator_window)
        else:
            tabs = self._parent.get_largest_window()
            tabs.addTab(self.chipconfigurator_window, tab_name)
            tabs.setCurrentWidget(self.chipconfigurator_window)
        self.chipconfigurator_window.setFocus()
        return self.chipconfigurator_window

    def initialize_chipconfigurator_window(self, tab_name):
        # Create a symbol handler window
        tabwidget = self._parent.chipconfigurator_tabwidget
        if tabwidget is None:
            tabwidget = self._parent.get_largest_window()
        current_project_path = functions.unixify_path(
            data.current_project.get_proj_rootpath()
        )
        series_json_file = f"{current_project_path}/.beetle/{data.chipconfigurator_series_filename}"
        chip_name = data.current_project.get_chip().get_name().upper()
        self.chipconfigurator_window = tabwidget.chipconfigurator_add(
            tab_name=tab_name,
            project_path=current_project_path,
            series_json_file=series_json_file,
            chip_name=chip_name,
        )
        # Focus back the debugger
        tabwidget.setCurrentWidget(self.chipconfigurator_window)

    """
    General project stuff
    """

    def init_project(self, rootpath: str) -> None:
        # At this point, the 'startup_project' path to the project's rootfolder is already
        # checked for validity - see constructor of the MainWindow(). The assertions only con-
        # firm that.
        assert isinstance(rootpath, str)
        assert os.path.isdir(rootpath)
        assert os.path.isabs(rootpath)
        if data.current_project is not None:
            current_project_path = functions.unixify_path(
                data.current_project.get_proj_rootpath()
            )
            new_project_path = functions.unixify_path(rootpath)
            if current_project_path == new_project_path:
                message = (
                    "The project you are trying to open is already opened!"
                )
                gui.dialogs.popupdialog.PopupDialog.ok(
                    message, parent=self._parent
                )
                return

            if self.close_project() == False:
                return
        # Open the project
        project.project.Project.load(
            proj_rootpath=rootpath,
            callback=self._async_load_project,
            callbackArg=rootpath,
        )
        # the callback must have two parameters:
        #   1. first parameter is the Project()-object
        #      that you want to assign to data.current_project
        #   2. Second parameter is whatever you passed to
        #      callbackArg
        return

    def load_project(self, rootpath: str) -> None:
        # At this point, the 'startup_project' path to the project's rootfolder is already
        # checked for validity - see constructor of the MainWindow(). The assertions only con-
        # firm that.
        assert isinstance(rootpath, str)
        assert os.path.isdir(rootpath)
        assert os.path.isabs(rootpath)
        try:
            self.init_project(rootpath)
        except Exception as ex:
            traceback.print_exc()
            self._parent.display.display_error(traceback.format_exc())
            self.disable_project_menubar_buttons()
        return

    def _async_load_project(self, projObj, rootpath):
        try:
            if not isinstance(projObj, project.project.Project):
                raise RuntimeError()
            if not isinstance(rootpath, str):
                raise RuntimeError()
            if not os.path.isdir(rootpath):
                raise RuntimeError()
            # Try to load the project layout
            project_layout = self.get_project_layout()
            message = "Restored project's layout."
            if project_layout == "":
                project_layout = self._parent.settings.manipulator.layout
                message = (
                    "Project has no layout yet. Generating default layout ..."
                )
            self._parent.view.layout_restore(
                project_layout, data.current_project.get_proj_rootpath()
            )
            self._parent.display.display_warning(message)

            # Initialize the toolbar
            self._parent._init_toolbar()

            # Display widgets
            widgets = (
                ("filetree", self.show_filetree),
                ("dashboard", self.show_dashboard),
                ("sa_tab", self.show_sa_tab),
            )
            for item in widgets:
                widget_name, func = item
                setattr(data, widget_name, func())
                widget = getattr(data, widget_name)
                setattr(self, widget_name, widget)
                tab_widget = widget._parent
                if tab_widget is not None:
                    index = tab_widget.indexOf(widget)
                    tab_widget.update_tabs(index)

            # DISABLE DASHBOARD FOR TEST
            if data.dashboard is not None:
                data.current_project.show_on_dashboard()
            # Enable the toolbar buttons
            self.enable_project_menubar_buttons()
            # Enable the toolbar buttons
            self._parent.display.toolbar_enable()
            self._parent.update_toolbar_style()
            # Update the recent project list
            if not self._parent.source_analysis_only:
                self._parent.settings.update_recent_projects_list(
                    functions.unixify_path(
                        data.current_project.get_proj_rootpath()
                    )
                )

            self._parent.initialized = True
            data.signal_dispatcher.project_loaded.emit()
        except Exception as ex:
            traceback.print_exc()
            if data.current_project is None:
                self._parent.display.display_error(
                    f"Error opening project!",
                )
            else:
                self._parent.display.display_error(
                    f"Error opening project: '{data.current_project.get_proj_rootpath()}'",
                )
            self.disable_project_menubar_buttons()

    def save_project(self, callback=None, callback_args=None):
        # Save the project
        data.current_project.save_later(
            save_editor=True,
            save_dashboard=True,
            save_filetree=False,
            callback=callback,
            callbackArg=callback_args,
        )

    def check_debugger(self, *args):
        is_debugger_enabled = data.current_project.get_chip().get_chip_dict(
            board=None
        )["debugger_enabled"]
        if not is_debugger_enabled:
            text = helpdocs.help_subjects.debugging.disabled_text()
            self._parent.show_debugger_action.setEnabled(False)
            self._parent.show_debugger_action.setToolTip(text)
            self._parent.show_debugger_action.setStatusTip(text)
            toolbar_debugger_button = self._parent.toolbar_debugger_button
            toolbar_debugger_button.set_enabled(False)
            toolbar_debugger_button.setToolTip(text)
            toolbar_debugger_button.setStatusTip(text)
            if isinstance(toolbar_debugger_button, qt.QWidgetAction):
                toolbar_debugger_button.defaultWidget().setToolTip(text)
                toolbar_debugger_button.defaultWidget().setStatusTip(text)

    def check_pinconfig(self, *args):
        is_pinconfig_enabled = data.current_project.get_chip().get_chip_dict(
            board=None
        )["pinconfig_enabled"]
        if not is_pinconfig_enabled:
            text = helpdocs.help_subjects.debugging.disabled_text()
            if data.PINCONFIG_ENABLED:
                self._parent.show_pinconfigurator_action.setEnabled(False)
                self._parent.show_pinconfigurator_action.setToolTip(text)
                self._parent.show_pinconfigurator_action.setStatusTip(text)
            toolbar_pinconfigurator_button = (
                self._parent.toolbar_pinconfigurator_button
            )
            toolbar_pinconfigurator_button.set_enabled(False)
            toolbar_pinconfigurator_button.setToolTip(text)
            toolbar_pinconfigurator_button.setStatusTip(text)
            if isinstance(toolbar_pinconfigurator_button, qt.QWidgetAction):
                toolbar_pinconfigurator_button.defaultWidget().setToolTip(text)
                toolbar_pinconfigurator_button.defaultWidget().setStatusTip(
                    text
                )

    def check_chipconfigurator(self, *args):
        current_project_path = functions.unixify_path(
            data.current_project.get_proj_rootpath()
        )
        series_json_file = f"{current_project_path}/.beetle/{data.chipconfigurator_series_filename}"
        is_chipconfigurator_enabled = os.path.isfile(series_json_file)
        if not is_chipconfigurator_enabled:
            text = "This project does not support the Chip Configurator!"
            if data.CHIPCONFIGURATOR_ENABLED:
                self._parent.show_chipconfigurator_action.setEnabled(False)
                self._parent.show_chipconfigurator_action.setToolTip(text)
                self._parent.show_chipconfigurator_action.setStatusTip(text)
            toolbar_chipconfigurator_button = (
                self._parent.toolbar_chipconfigurator_button
            )
            toolbar_chipconfigurator_button.set_enabled(False)
            toolbar_chipconfigurator_button.setToolTip(text)
            toolbar_chipconfigurator_button.setStatusTip(text)
            if isinstance(toolbar_chipconfigurator_button, qt.QWidgetAction):
                toolbar_chipconfigurator_button.defaultWidget().setToolTip(text)
                toolbar_chipconfigurator_button.defaultWidget().setStatusTip(
                    text
                )

    def get_project_layout(self):
        try:
            file_path = f"{data.current_project.get_proj_rootpath()}/.beetle/window_config.btl"
            with open(file_path, "r", newline="\n") as f:
                project_layout = f.read()
                f.close()
            return project_layout
        except:
            return ""

    def close_project(self):
        message = "Are you sure you want to close the current project?"
        reply = gui.dialogs.popupdialog.PopupDialog.question(
            message, self._parent
        )
        if reply == qt.QMessageBox.StandardButton.Yes:

            def start_closing(*args):
                data.current_project.self_destruct(
                    callback=finish_closing,
                    callbackArg=None,
                )
                return

            def finish_closing(*args):
                for w in self._parent.get_all_windows():
                    w.close_all()
                self.disable_project_menubar_buttons()
                self._parent.display.toolbar_disable()
                data.current_project = None
                data.filetree.setParent(None)
                self.dashboard.setParent(None)
                data.filetree = None
                self.dashboard = None
                self.sa_tab.setParent(None)
                self.sa_tab = None
                data.sa_tab = None
                return

            start_closing()
            return True
        return False
