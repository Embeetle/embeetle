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
import qt


class SourceAnalyzerDispatcher(qt.QObject):
    """
    This dispatcher contains two kinds of signals:

        - SA FEEDBACK:  Feedback provided by the SA.

        - SA CONTROL:   Signals to control the behavior of the SA or to give input to the SA.
    """

    # Initialization
    project_initialized = qt.pyqtSignal()

    # SA FEEDBACK
    # ===========
    file_analysis_change_sig = qt.pyqtSignal(object, int)
    file_inclusion_change_sig = qt.pyqtSignal(object, int)
    file_linking_change_sig = qt.pyqtSignal(object, int)
    hdir_inclusion_change_sig = qt.pyqtSignal(object, int)

    # SA CONTROL
    # ==========
    # The 'start_stop_engine_conditionally_sig' always attempts to start the SA (or just lets it
    # run if it was already running). However, if certain minimal requirements are not met, it will
    # switch the SA off.
    # Aside from this, the signal also refreshes the build settings stored by the SA, such as the
    # location of the build directory, the makefile, the make command, ...
    start_stop_engine_conditionally_sig = qt.pyqtSignal()

    # Add a file to the project if it wasn't in the project yet.
    add_file_sig = qt.pyqtSignal(
        str, int, object
    )  # p1=path, p2=mode, p3=python_object

    # Remove the file with the given path.
    remove_file_sig = qt.pyqtSignal(str)  # p1=path

    # Change the mode of a previously added file.
    set_file_mode_sig = qt.pyqtSignal(str, int)  # p1=path, p2=mode

    # Set the mode of an hdir.
    set_hdir_mode_sig = qt.pyqtSignal(
        str, int, object
    )  # p1=path, p2=mode, p3=python_object

    # Progress reporting signals
    progress_report = qt.pyqtSignal(int, int)
    progress_completed = qt.pyqtSignal()
    progress_updated = qt.pyqtSignal()

    # Filetree signals
    file_tree_handler_initialization_report = qt.pyqtSignal(int, int, str)
    file_tree_handler_initialization_completed = qt.pyqtSignal()

    # Memory regions
    memory_regions_update = qt.pyqtSignal(dict)
    memory_sections_update = qt.pyqtSignal(dict)

    # Alternate file content
    set_alternate_content = qt.pyqtSignal(object, str)

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        return


class FileFolderDispatcher(qt.QObject):
    """This dispatcher contains signals to notify about a file/folder change in
    Embeetle. I (Kristof)

    catch these signals in my Project()-object, then I take the following actions:
        - Let the Dashboard adapt to the new situation (eg. the makefile gets a new name, ...).
        - Notify the SA about new build settings, if needed.

    You (@Matic) already notify the SA when a file is saved. That's great. Do you also notify the SA
    when a file is renamed? We should sync our actions here, to avoid notifying the SA twice about
    certain things.
    """

    # FILE CHANGED
    # ============
    file_saved_sig = qt.pyqtSignal(str)  # p1=file_abspath
    file_added_sig = qt.pyqtSignal(
        str, bool
    )  # p1=file_abspath,  p2=explicit_action
    file_renamed_sig = qt.pyqtSignal(
        str, str, bool
    )  # p1=old_abspath,   p2=new_abspath,     p3=explicit_action
    file_deleted_sig = qt.pyqtSignal(
        str, bool
    )  # p1=file_abspath,  p2=explicit_action

    # DIRECTORY CHANGED
    # ==============
    folder_added_sig = qt.pyqtSignal(
        str, bool
    )  # p1=folder_abspath, p2=explicit_action
    folder_renamed_sig = qt.pyqtSignal(
        str, str, bool
    )  # p1=old_abspath,    p2=new_abspath,     p3=explicit_action
    folder_deleted_sig = qt.pyqtSignal(
        str, bool
    )  # p1=folder_abspath, p2=explicit_action

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        return


class GlobalSignalDispatcher(qt.QObject):
    """Global signal dispatcher."""

    # GLOBAL NOTIFICATIONS
    # ====================
    notify_message = qt.pyqtSignal(str)
    notify_success = qt.pyqtSignal(str)
    notify_warning = qt.pyqtSignal(str)
    notify_error = qt.pyqtSignal(str)
    restart_needed_notify = qt.pyqtSignal(str)
    program_state_changed = qt.pyqtSignal(object)
    makefile_command_executed = qt.pyqtSignal(str, bool)
    file_edited = qt.pyqtSignal(str)
    save_layout = qt.pyqtSignal(bool)
    editor_state_changed = qt.pyqtSignal(int, object, str)
    tab_index_changed = qt.pyqtSignal(int, object, str)
    indication_changed = qt.pyqtSignal(int, object, str)
    command_completed = qt.pyqtSignal(bool)
    base_url_override_change = qt.pyqtSignal()

    # TOOL CHANGE NOTIFICATIONS
    # =========================
    # For tool change notification signals, please check:
    # https://forum.embeetle.com/t/global-signals-for-tool-changes/578
    # Note: it seems that these signals are not yet attached to any slot.
    build_automation_changed_sig = qt.pyqtSignal(
        object
    )  # Path to gnu make executable file.
    compiler_toolchain_changed_sig = qt.pyqtSignal(
        object
    )  # Path to toplevel toolchain folder(!).
    flashtool_changed_sig = qt.pyqtSignal(
        object
    )  # Path to flashtool executable file.

    # SETTINGS
    # ========
    update_settings = qt.pyqtSignal()
    update_styles = qt.pyqtSignal()
    update_whitespace_visible = qt.pyqtSignal()
    update_tabs_use_spaces = qt.pyqtSignal()
    show_symbol_details = qt.pyqtSignal(str, bool)
    feed_update = qt.pyqtSignal()

    # DEBUGGING
    # =========
    debug_connected = qt.pyqtSignal()
    debug_disconnected = qt.pyqtSignal()
    debug_breakpoint_insert = qt.pyqtSignal(str, int, int)
    debug_breakpoint_delete = qt.pyqtSignal(str, int, int, int)
    debug_breakpoint_delete_all = qt.pyqtSignal()
    debug_watchpoint_insert = qt.pyqtSignal(str, str, int, str)
    debug_watchpoint_delete = qt.pyqtSignal(int)
    debug_watchpoint_delete_all = qt.pyqtSignal()
    debug_variable_object_create = qt.pyqtSignal(str)
    debug_delete_all_watch_and_break_points = qt.pyqtSignal()
    debug_state_changed = qt.pyqtSignal(object)
    debug_stack_updated = qt.pyqtSignal()

    # MEMORY-VIEW
    # ===========
    memory_view_show_region = qt.pyqtSignal(str)
    memory_view_clear_memory = qt.pyqtSignal()
    memory_view_clear_all = qt.pyqtSignal()
    memory_watch_add_variable = qt.pyqtSignal(object)
    memory_watch_delete_variable = qt.pyqtSignal(str)
    memory_watch_delete_all_variables = qt.pyqtSignal()
    memory_watch_update_variables = qt.pyqtSignal(object)
    memory_watch_manual_update = qt.pyqtSignal()

    # DIAGNOSTICS
    # ===========
    diagnostics_show_unknown = qt.pyqtSignal()

    # FILE-TREE
    # =========
    file_tree_watchdog_observer_error = qt.pyqtSignal(str)
    file_tree_goto_path = qt.pyqtSignal(str, bool)

    # FILE-WATCHER
    # ============
    file_watcher_on_error = qt.pyqtSignal()

    # PROJECT
    # =======
    project_loaded = qt.pyqtSignal()

    # SUB-DISPATCHERS
    # ===============
    source_analyzer: Optional[SourceAnalyzerDispatcher] = None
    file_folder: Optional[FileFolderDispatcher] = None

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        # Initialize sub-dispatchers
        self.source_analyzer = SourceAnalyzerDispatcher()
        self.file_folder = FileFolderDispatcher()
        return
