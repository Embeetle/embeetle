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
import threading, os, sys, traceback, functools
import qt, data, purefunctions, gui, functions, serverfunctions
import components.thread_switcher as _sw_
import bpathlib.path_power as _pp_
import project.segments.chip_seg.chip as _chip_
import hardware_api.chip_unicum as _chip_unicum_
import project.segments.lib_seg.lib_seg as _lib_seg_
import project.segments.version_seg.version_seg as _version_seg_
import project.segments.board_seg.board as _board_
import hardware_api.board_unicum as _board_unicum_
import hardware_api.probe_unicum as _probe_unicum_
import project.segments.probe_seg.probe as _probe_
import project.segments.path_seg.treepath_seg as _treepath_seg_
import project.segments.path_seg.toolpath_seg as _toolpath_seg_
import project.startup.project_new as _project_new_
import project.startup.project_load as _project_load_
import helpdocs.help_texts as _ht_
import sa_tab.items.status_items.status_items as _status_items_
import sa_tab.items.dependency_items.dependency_items as _dependency_items_
import sa_tab.items.cpu_load_items.cpu_load_items as _cpu_load_items_
import sa_tab.items.clear_cache_items.clear_cache_items as _clear_cache_items_
import hardware_api.file_generator as _file_generator_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import gui.forms
    import gui.forms.mainwindow
    import project.segments.project_segment as _ps_
    import wizards.intro_wizard.intro_wizard as _wiz_
    import bpathlib.treepath_obj as _treepath_obj_
    import bpathlib.tool_obj as _tool_obj_
    import tree_widget.widgets.item_btn as _item_btn_
    import tree_widget.widgets.item_lbl as _item_lbl_
    import tree_widget.widgets.item_dropdown as _item_dropdown_
    import sa_tab.chassis.sa_tab as _chassis_sa_tab_
from various.kristofstuff import *


class Project(object):
    @classmethod
    def create_default_project(
        cls,
        chip_unicum: _chip_unicum_.CHIP,
        board_unicum: _board_unicum_.BOARD,
        probe_unicum: _probe_unicum_.PROBE,
        rootpath: str,
        callback: Optional[Callable],
        callbackArg: Any,
        with_engine: bool = True,
        makefile_interface_version: Optional[Union[str, int]] = None,
    ) -> None:
        """Create a default project and return it in a callback.

        Only used in project generators!
        """
        _project_new_.create_default_project(
            chip_unicum,
            board_unicum,
            probe_unicum,
            rootpath,
            callback,
            callbackArg,
            with_engine,
            makefile_interface_version,
        )
        return

    @classmethod
    def load(
        cls,
        proj_rootpath: str,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Open an existing folder, create and return the projObj in a callback.

        NOTE:
        The Filetree() and Dashboard()-instances get created *after* this load() function completes!
        """
        assert isinstance(proj_rootpath, str)
        assert os.path.isdir(proj_rootpath)
        assert os.path.isabs(proj_rootpath)

        # Check for the latest online version when a project loads
        # This also serves as an internet connectivity test
        def version_check_callback(remote_version):
            if remote_version and remote_version.strip().lower() != "none":
                # Internet is available - reset the flag if it was set
                if data.internet_down:
                    data.internet_down = False
                    print("[CONNECTIVITY] Internet connection is available")

                # Print version info
                local_version = functions.get_embeetle_version()
                print(
                    f"[VERSION-CHECK] Latest Embeetle version: {remote_version} (Current: {local_version})"
                )
            else:
                # No valid version returned - internet is likely down
                data.internet_down = True
                print(
                    "[CONNECTIVITY] Internet connection appears to be down - disabling network requests"
                )

                # Show a warning popup to the user
                import gui.dialogs.popupdialog

                warning_msg = str(
                    f"No internet connection detected!\n\n"
                    f"Embeetle will continue to work offline, but some features like\n"
                    f"checking for updates or downloading tools will be disabled.\n\n"
                    f"To re-enable online features, please connect to the internet\n"
                    f"and restart Embeetle."
                )

                # Show dialog in a separate thread to avoid freezing the UI
                def show_warning_dialog():
                    # Create a custom dialog with the WindowStaysOnTopHint flag to keep it visible
                    dialog = gui.dialogs.popupdialog.PopupDialog(
                        parent=None,
                        text=warning_msg,
                        dialog_type="ok",
                        icon_path="icons/dialog/warning.png",
                        title_text="No Internet Connection",
                    )

                    # Set the window flags to make it stay on top
                    dialog.setWindowFlags(
                        dialog.windowFlags()
                        | qt.Qt.WindowType.WindowStaysOnTopHint
                    )

                    # Show dialog and wait for user response
                    dialog.show()
                    dialog.activateWindow()
                    dialog.raise_()

                    # Wait for dialog to close
                    while dialog.isVisible():
                        functions.process_events(delay=0.001)

                # Use QTimer to show the dialog after current operations complete
                qt.QTimer.singleShot(500, show_warning_dialog)

        # Non-blocking version check
        serverfunctions.get_remote_embeetle_version(version_check_callback)

        # Load the project
        _project_load_.load_01(proj_rootpath, callback, callbackArg)
        return

    def __init__(
        self,
        proj_rootpath: str,
        with_engine: bool = True,
    ) -> None:
        """Create a new Project()-instance with the given rootpath.

        :param proj_rootpath: Absolute path to project rootfolder.
        :param with_engine: Create a SA engine for this project. Turn off for
            project generation scripts.
        """
        if threading.current_thread() is threading.main_thread():
            # Register the main thread and start the cleaning procedure. This will not do anything
            # if it was already done before.
            _sw_.register_thread(
                name="main",
                qthread=qt.QThread.currentThread(),
            )
            _sw_.start_switcher_cleaner()
        self.__dead = False
        assert isinstance(proj_rootpath, str)
        self.intro_wiz: Optional[_wiz_.IntroWizard] = None
        self.__proj_rootpath = proj_rootpath
        self.__with_engine: bool = with_engine
        self.__old_source_dir: Optional[str] = None

        # & Project dictionary
        #     self.__proj_dict = {
        #         'iconpath'     : 'icons/board/arduino_uno.png',
        #         'board'        : Board(),
        #         'chip'         : Chip(),
        #         'probe'        : Probe(),
        #         'toolpath_seg' : ToolpathSeg(),
        #         'treepath_seg' : TreepathSeg(),
        #         'lib_seg'      : LibSeg(),
        #         'version_seg'  : VersionSeg(),
        #         'history'      : [
        #             Chip(),
        #             Probe(),
        #             ...
        #         ],
        #     }
        self.__proj_dict: Dict[
            str,
            Union[
                str,
                _board_.Board,
                _chip_.Chip,
                _probe_.Probe,
                _toolpath_seg_.ToolpathSeg,
                _treepath_seg_.TreepathSeg,
                _lib_seg_.LibSeg,
                _version_seg_.VersionSeg,
                List[
                    Union[
                        _board_.Board,
                        _chip_.Chip,
                        _probe_.Probe,
                        _toolpath_seg_.ToolpathSeg,
                        _treepath_seg_.TreepathSeg,
                        _lib_seg_.LibSeg,
                        _version_seg_.VersionSeg,
                    ]
                ],
            ],
        ] = {}

        # & Source Analyzer Tab
        # Store the items to be shown in the Source Analyzer Tab
        self.__sa_tab_items: Dict[
            str,
            Dict[
                str,
                Optional[
                    Union[
                        _status_items_.StatusRootItem,
                        _status_items_.LaunchStatusItem,
                        _status_items_.SAStatusItem,
                        _status_items_.LinkerStatusItem,
                        _status_items_.FeederStatusItem,
                        _status_items_.DigesterStatusItem,
                        _status_items_.InternalErrorItem,
                        _dependency_items_.DependencyRootItem,
                        _dependency_items_.BuildFolderItem,
                        _dependency_items_.MakefileItem,
                        _dependency_items_.BuildAutomationItem,
                        _dependency_items_.CompilerToolchainItem,
                        _cpu_load_items_.CPULoadRootItem,
                        _clear_cache_items_.ClearCacheRootItem,
                    ]
                ],
            ],
        ] = {
            "status_items": {
                "status_rootitem": None,
                "launch_status_item": None,
                "sa_status_item": None,
                "linker_status_item": None,
                "feeder_status_item": None,
                "digester_status_item": None,
                "internal_error_item": None,
            },
            "dependency_items": {
                "dependency_rootitem": None,
                "build_folder_item": None,
                "makefile_item": None,
                "build_automation_item": None,
                "compiler_toolchain_item": None,
            },
            "cpu_load_items": {
                "cpu_load_rootitem": None,
            },
            "clear_cache_items": {
                "clear_cache_rootitem": None,
            },
        }
        self.__sa_tab_initialized = False
        self.__sa_tab_check_loop_running = False
        self.__sa_tab_refresh_mutex = threading.Lock()
        data.current_project = self

        # & Tie file and folder signals to slots
        data.signal_dispatcher.file_folder.file_saved_sig.connect(
            self.__file_saved_notification
        )
        data.signal_dispatcher.file_folder.file_added_sig.connect(
            self.__file_added_notification
        )
        data.signal_dispatcher.file_folder.file_renamed_sig.connect(
            self.__file_renamed_notification
        )
        data.signal_dispatcher.file_folder.file_deleted_sig.connect(
            self.__file_deleted_notification
        )
        data.signal_dispatcher.file_folder.folder_added_sig.connect(
            self.__folder_added_notification
        )
        data.signal_dispatcher.file_folder.folder_renamed_sig.connect(
            self.__folder_renamed_notification
        )
        data.signal_dispatcher.file_folder.folder_deleted_sig.connect(
            self.__folder_deleted_notification
        )
        return

    def get_proj_rootpath(self) -> str:
        """Get the rootpath for this project."""
        return self.__proj_rootpath

    def get_all_rootpaths(self) -> List[str]:
        """Get the project rootpath and those to external folders."""
        return [
            self.__proj_rootpath,
        ]

    def get_rootpath_from_rootid(
        self,
        rootid: str,
        suppress_warnings: bool = False,
    ) -> Optional[str]:
        """Get the rootpath according to the specified id.

        In some cases this method gets invoked pure- ly to figure out if the
        corresponding rootpath still exists (eg. if the external folder has been
        removed). In such cases, it's okay to suppress warnings.
        """
        assert rootid.startswith("<") and rootid.endswith(">")
        if rootid == "<project>":
            return self.__proj_rootpath
        return None

    def get_rootid_from_rootpath(
        self,
        rootpath: str,
        double_angle: bool = True,
        html_angles: bool = False,
    ) -> Optional[str]:
        """The reverse operation.

        WARNING:
        If the parameters 'double_angle' and 'html_angles' differ from the defaults, the returned
        rootid is only fit for being shown in a GUI. Not for any internal processing!

        The 'double_angle' parameter only has effect for external roots.
        """
        assert not rootpath.startswith("<")
        rootid: Optional[str] = None
        if rootpath == self.__proj_rootpath:
            rootid = "<project>"
        return rootid

    def abspath_to_prefixed_relpath(
        self,
        abspath: str,
        double_angle: bool,
        html_angles: bool,
    ) -> Optional[str]:
        """
        This is the opposite operation from 'strip_rootid()' - as defined in 'purefunctions.py'. It
        takes an absolute path and returns a prefixed relpath. Return None if no rootpath matches
        the given abspath.

        :param abspath:         The abspath to be processed.
        :param double_angle:    Put the prefix between double angles << >> if we're dealing with an
                                external root.
        :param html_angles:     Replace the angles < > with html-codes.
        """
        rootpath = self.get_proj_rootpath()
        if not abspath.startswith(rootpath):
            return None
        rootid = self.get_rootid_from_rootpath(rootpath)
        if not double_angle:
            rootid = rootid.replace("<<", "<").replace(">>", ">")
        if html_angles:
            rootid = rootid.replace("<", "&#60;").replace(">", "&#62;")
        relpath = _pp_.abs_to_rel(
            rootpath=rootpath,
            abspath=abspath,
        )
        return f"{rootid}/{relpath}"

    def get_name(self) -> str:
        """Get the project's name, which is just the name of the rootfolder."""
        pathpart, base = os.path.split(self.__proj_rootpath)
        return base

    def get_board(self) -> _board_.Board:
        """"""
        return cast(_board_.Board, self.__proj_dict["board"])

    def get_chip(self) -> _chip_.Chip:
        """"""
        return cast(_chip_.Chip, self.__proj_dict["chip"])

    def get_probe(self) -> _probe_.Probe:
        """"""
        return cast(_probe_.Probe, self.__proj_dict["probe"])

    def get_treepath_seg(self) -> _treepath_seg_.TreepathSeg:
        """"""
        return cast(
            _treepath_seg_.TreepathSeg, self.__proj_dict["treepath_seg"]
        )

    def get_toolpath_seg(self) -> _toolpath_seg_.ToolpathSeg:
        """"""
        return cast(
            _toolpath_seg_.ToolpathSeg, self.__proj_dict["toolpath_seg"]
        )

    def get_lib_seg(self) -> _lib_seg_.LibSeg:
        """"""
        return cast(_lib_seg_.LibSeg, self.__proj_dict["lib_seg"])

    def get_version_seg(self) -> _version_seg_.VersionSeg:
        """"""
        return cast(_version_seg_.VersionSeg, self.__proj_dict["version_seg"])

    def register_old_source_dir(self, source_dir_relpath: str) -> None:
        """Register the old SOURCE_DIR variable, if present in the
        'dashboard_config.btl' file."""
        purefunctions.printc(
            f"\nWARNING: old project opened, "
            f"SOURCE_DIR = {q}{source_dir_relpath}{q}\n",
            color="warning",
        )
        self.__old_source_dir = source_dir_relpath
        return

    def get_old_source_dir(self) -> Optional[str]:
        """Access the old SOURCE_DIR variable, used for forced excluding."""
        return self.__old_source_dir

    def fill_project(
        self,
        chip: _chip_.Chip,
        lib_seg: _lib_seg_.LibSeg,
        version_seg: _version_seg_.VersionSeg,
        board: _board_.Board,
        probe: _probe_.Probe,
        treepath_seg: _treepath_seg_.TreepathSeg,
        toolpath_seg: _toolpath_seg_.ToolpathSeg,
    ) -> None:
        """Attention, it won't be shown yet on the Dashboard!"""
        self.__proj_dict = {
            "board": board,
            "chip": chip,
            "probe": probe,
            "treepath_seg": treepath_seg,
            "toolpath_seg": toolpath_seg,
            "lib_seg": lib_seg,
            "version_seg": version_seg,
            "history": [],
        }
        return

    # ^                                           DASHBOARD                                            ^#
    # % ============================================================================================== %#
    # % Methods to show the project segments on the dashboard and update them.                         %#
    # %                                                                                                %#

    def show_on_dashboard(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        assert data.dashboard is not None
        if data.startup_log_project:
            print(f"[startup] project.py -> show_on_dashboard()")

        def show_project(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> show_on_dashboard().show_project()"
                )
            self.__show_segments_on_dashboard(
                callback=create_orig_cfgfiles,
                callbackArg=None,
            )
            return

        def create_orig_cfgfiles(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"show_on_dashboard().create_next_orig_cfgfiles()"
                )
            data.dashboard.save_orig_cfgfiles(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if data.startup_log_project:
                print(f"[startup] project.py -> show_on_dashboard().finish()")
            if callback is not None:
                callback(callbackArg)
            return

        self.fill_sa_tab(
            callback=show_project,
            callbackArg=None,
        )
        return

    def __show_segments_on_dashboard(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""
        if data.startup_log_project:
            print(f"[startup] project.py -> __show_segments_on_dashboard()")

        # * =====================[ show_on_dashboard() ]====================== *#
        def show_board(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_board()"
                )
            self.get_board().show_on_dashboard(
                callback=show_chip,
                callbackArg=None,
            )
            return

        def show_chip(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_chip()"
                )
            self.get_chip().show_on_dashboard(
                callback=show_probe,
                callbackArg=None,
            )
            return

        def show_probe(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_probe()"
                )
            self.get_probe().show_on_dashboard(
                callback=show_toolpath_seg,
                callbackArg=None,
            )
            return

        def show_toolpath_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_toolpath_seg()"
                )
            self.get_toolpath_seg().show_on_dashboard(
                callback=show_treepath_seg,
                callbackArg=None,
            )
            return

        def show_treepath_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_treepath_seg()"
                )
            self.get_treepath_seg().show_on_dashboard(
                callback=show_lib_seg,
                callbackArg=None,
            )
            return

        def show_lib_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_lib_seg()"
                )
            self.get_lib_seg().show_on_dashboard(
                callback=show_version_seg,
                callbackArg=None,
            )
            return

        def show_version_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().show_version_seg()"
                )
            self.get_version_seg().show_on_dashboard(
                callback=update_states_board,
                callbackArg=None,
            )
            return

        # * =======================[ update_states() ]======================== *#
        def update_states_board(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().update_states_board()"
                )
            self.get_board().update_states(
                project_report=None,
                callback=update_states_chip,
                callbackArg=None,
            )
            return

        def update_states_chip(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().update_states_chip()"
                )
            # Even though the 'board' parameter is not provided, it will be
            # pulled by this method via data.current_project!
            self.get_chip().update_states(
                board=None,
                project_report=None,
                callback=update_states_lib_seg,
                callbackArg=None,
            )
            return

        def update_states_lib_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().update_states_lib()"
                )
            self.get_lib_seg().update_states(
                project_report=None,
                callback=update_states_version_seg,
                callbackArg=None,
            )
            return

        def update_states_version_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().update_states_version_seg()"
                )
            self.get_version_seg().update_states(
                project_report=None,
                callback=update_states_probe,
                callbackArg=None,
            )
            return

        def update_states_probe(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().update_states_probe()"
                )
            self.get_probe().update_states(
                project_report=None,
                callback=update_states_treepath_seg,
                callbackArg=None,
            )
            return

        def update_states_treepath_seg(*args) -> None:
            # Even though toolpathSeg and probe parameters are not provided, they will be pulled by
            # this method via data.current_project!
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().update_states_treepath_seg()"
                )
            self.get_treepath_seg().update_states(
                withgui=True,
                toolpath_seg=None,
                probe=None,
                project_report=None,
                check_existence=True,
                version=self.get_makefile_interface_version(),
                delete_nonexisting_paths=True,
                callback=update_states_toolpath_seg,
                callbackArg=None,
            )

        def update_states_toolpath_seg(*args) -> None:
            # Even though chip and probe parameters are not provided,
            # they will be pulled by this method via data.current_project!
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().update_states_toolpath_seg()"
                )
            self.get_toolpath_seg().update_states(
                withgui=True,
                chip=None,
                probe=None,
                project_report=None,
                callback=refresh_board,
                callbackArg=None,
            )
            return

        # * ==================[ trigger_dashboard_refresh() ]================= *#
        def refresh_board(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().refresh_board()"
                )
            self.get_board().trigger_dashboard_refresh(
                callback=refresh_chip,
                callbackArg=None,
            )
            return

        def refresh_chip(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().refresh_chip()"
                )
            self.get_chip().trigger_dashboard_refresh(
                callback=refresh_lib,
                callbackArg=None,
            )
            return

        def refresh_lib(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().refresh_lib()"
                )
            self.get_lib_seg().trigger_dashboard_refresh(
                callback=refresh_version,
                callbackArg=None,
            )
            return

        def refresh_version(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().refresh_version()"
                )
            self.get_version_seg().trigger_dashboard_refresh(
                callback=refresh_probe,
                callbackArg=None,
            )
            return

        def refresh_probe(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().refresh_probe()"
                )
            self.get_probe().trigger_dashboard_refresh(
                callback=refresh_treepath_seg,
                callbackArg=None,
            )
            return

        def refresh_treepath_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().refresh_treepath_seg()"
                )
            self.get_treepath_seg().trigger_dashboard_refresh(
                callback=refresh_toolpath_seg,
                callbackArg=None,
            )
            return

        def refresh_toolpath_seg(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> "
                    f"__show_segments_on_dashboard().refresh_toolpath_seg()"
                )
            self.get_toolpath_seg().trigger_dashboard_refresh(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if data.startup_log_project:
                print(
                    f"[startup] project.py -> __show_segments_on_dashboard().finish()"
                )
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        data.dashboard.set_page()
        # The normal sequence is:
        #     - <segment>.show_on_dashboard()
        #     - <segment>.update_states()
        #     - <segment>.trigger_dashboard_refresh()
        # However, the library segment deviates a bit from this usual sequence. It needs its 'update
        # _states()' method to run first, before the 'show_on_dashboard()'. This anomaly wasn't de-
        # tected, because the 'update_states()' actually already runs in the load() method - see the
        # method that generates a Project()-instance at the top.
        # Anyhow, a safety system is now implemented in the method 'show_on_dashboard()' from the
        # library segment to ensure that its 'update_states()' method runs first.
        show_board()
        return

    def update_all_states_with_report(
        self,
        project_report: Dict,
        delete_nonexisting_paths: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """"""

        def update_board(*_args) -> None:
            self.get_board().update_states(
                project_report=project_report,
                callback=update_chip,
                callbackArg=None,
            )
            return

        def update_chip(*_args) -> None:
            self.get_chip().update_states(
                board=self.get_board(),
                project_report=project_report,
                callback=update_lib_seg,
                callbackArg=None,
            )
            return

        def update_lib_seg(*_args) -> None:
            self.get_lib_seg().update_states(
                project_report=project_report,
                callback=update_version_seg,
                callbackArg=None,
            )
            return

        def update_version_seg(*_args) -> None:
            self.get_version_seg().update_states(
                project_report=project_report,
                callback=update_probe,
                callbackArg=None,
            )
            return

        def update_probe(*_args) -> None:
            self.get_probe().update_states(
                project_report=project_report,
                callback=update_toolpath_seg,
                callbackArg=None,
            )
            return

        def update_toolpath_seg(*_args) -> None:
            self.get_toolpath_seg().update_states(
                withgui=False,
                chip=self.get_chip(),
                probe=self.get_probe(),
                project_report=project_report,
                callback=update_treepath_seg,
                callbackArg=None,
            )
            return

        def update_treepath_seg(*_args) -> None:
            self.get_treepath_seg().update_states(
                withgui=False,
                toolpath_seg=self.get_toolpath_seg(),
                probe=self.get_probe(),
                project_report=project_report,
                check_existence=True,
                version=self.get_makefile_interface_version(),
                delete_nonexisting_paths=delete_nonexisting_paths,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            callback(callbackArg)
            return

        update_board()
        return

    # ^                                              SAVE                                              ^#
    # % ============================================================================================== %#
    # % Save this Project()-instance.                                                                  %#
    # %                                                                                                %#

    def save_project(
        self,
        save_editor: bool,
        save_dashboard: bool,
        ask_permissions: bool,
        forced_files: List[str],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        :param save_editor:     Save files opened in editor.
        :param save_dashboard:  Apply dashboard mods and save this Project()-instance to '.beetle/
                                dashboard_config.btl'.
        :param ask_permissions: Ask user permission to modify config files.
        :param forced_files:    Force these files to the list of impacted files.

        Note: Ctrl + S
            => Run function 'save_all()' in mainwindow.py line 696, which then calls this function.

            => save_editor    = True
               save_dashboard = dashboard_save_flag

        Flags 'dirtree_save_flag' and 'dashboard_save_flag' are kept by Matic. These flags are only
        set by my 'show_tab_savebutton_sig' emission (both Filetree and Dashboard have that signal).
        """
        save_params = {
            "save_editor": save_editor,
            "save_dashboard": save_dashboard,
            "ask_permissions": ask_permissions,
            "forced_files": forced_files,
            "callback": callback,
            "callbackArg": callbackArg,
        }
        # Save Editor
        if save_editor and isinstance(
            data.main_form, gui.forms.mainwindow.MainWindow
        ):
            data.main_form.file_save_all()

        # Start chain reaction
        self.__save_dashboard(save_params)
        return

    def __save_dashboard(self, save_params: Dict[str, Any]) -> None:
        """"""
        # & Sanity checks
        # If one of these conditions fails, the Dashboard should not be saved. Just finish the save
        # procedure.
        if not save_params["save_dashboard"]:
            self.__save_finish(save_params)
            return
        if data.dashboard is None:
            # This is okay.
            pass
        forced_files = save_params["forced_files"]
        ask_permissions = save_params["ask_permissions"]

        # & Apply Dashboard
        import dashboard.chassis.dashboard_worker as _dw_

        dashboard_worker: _dw_.DashboardWorker = _dw_.DashboardWorker()

        # $ List impacted files
        impacted_files = forced_files
        impacted_files.extend(self.get_board().get_impacted_files())
        impacted_files.extend(self.get_chip().get_impacted_files())
        impacted_files.extend(self.get_probe().get_impacted_files())
        impacted_files.extend(self.get_toolpath_seg().get_impacted_files())
        impacted_files.extend(self.get_treepath_seg().get_impacted_files())
        impacted_files = list(set(impacted_files))

        # $ Reorganize the list
        # Put chipcfg and probecfg files first because they can change name and therefore affect the
        # others.
        if "OPENOCD_CHIPFILE" in impacted_files:
            impacted_files.remove("OPENOCD_CHIPFILE")
            impacted_files = ["OPENOCD_CHIPFILE"] + impacted_files
        if "OPENOCD_PROBEFILE" in impacted_files:
            impacted_files.remove("OPENOCD_PROBEFILE")
            impacted_files = ["OPENOCD_PROBEFILE"] + impacted_files

        # $ Add 'dashboard.mk' if there are makefile interface issues
        if self.get_makefile_interface_version_needs_to_be_applied():
            if "DASHBOARD_MK" not in impacted_files:
                impacted_files.append("DASHBOARD_MK")

        # $ Always put 'dashboard.mk' at the end.
        if "DASHBOARD_MK" in impacted_files:
            impacted_files.remove("DASHBOARD_MK")
            impacted_files += ["DASHBOARD_MK"]

        dashboard_worker.apply_dashboard(
            impacted_files=impacted_files,
            ask_permissions=ask_permissions,
            callback=self.__save_dashboard_finish,
            callbackArg=save_params,
        )
        return

    def __save_dashboard_finish(
        self,
        success: bool,
        save_params: Dict[str, Any],
    ) -> None:
        """"""
        if not success:
            self.__save_abort(save_params)
            return

        # & Makefile interface version
        # The makefile interface version no longer needs to be applied. Clear the flag.
        self.set_makefile_interface_version_needs_to_be_applied(False)

        # & Create the dictionary with the content to save
        # The dictionary with the content to save is not affected in any way by the eventual save
        # format - be it python-style or json-style.
        dashboard_config_dict = {}  # noqa

        # $ 1. Version
        dashboard_config_dict["project_type"] = "makefile"
        dashboard_config_dict["project_version"] = str(
            self.get_version_seg().get_version_nr()
        )

        # $ 2. Chip
        dashboard_config_dict["chip_name"] = str(
            self.get_chip().get_name()
        ).lower()

        # $ 3. Board
        dashboard_config_dict["board_name"] = str(
            self.get_board().get_name()
        ).lower()

        # $ 4. Probe
        dashboard_config_dict["probe_name"] = str(
            self.get_probe().get_name()
        ).lower()
        dashboard_config_dict["transport_protocol"] = str(
            self.get_probe().get_transport_protocol_name()
        )
        dashboard_config_dict["COM_port"] = str(
            self.get_probe().get_comport_name()
        )

        # $ 5. Project Layout
        for unicum_name in self.get_treepath_seg().get_treepath_unicum_names():
            if unicum_name in (
                "FILETREE_MK",
                "DASHBOARD_MK",
                "BUTTONS_BTL",
            ):
                # These values must not be stored:
                #  - 'FILETREE_MK' and 'DASHBOARD_MK': They rely on the value of the makefile.
                #  - '*.BTL': The .btl files get a default value in the load() function.
                continue
            treepath_obj = self.get_treepath_seg().get_treepathObj(unicum_name)
            relpath: Optional[str] = treepath_obj.get_relpath()
            rootid: Optional[str] = treepath_obj.get_rootid()
            value: Optional[str] = None
            if (relpath is None) or (relpath.lower() == "none"):
                value = "None"
            else:
                value = f"{rootid}/{relpath}"
            dashboard_config_dict[unicum_name] = str(value)
            continue

        # $ 6. Tools
        for category in self.get_toolpath_seg().get_categories():
            dashboard_config_dict[category] = str(
                self.get_toolpath_seg().get_unique_id(category)
            )
            continue

        # & Write the file
        # Rely on the 'dashboard_config_handler.py' module to format the content from the dictionary
        # in either json-style, python-style or both. This module will also decide where to save the
        # stuff - be it in '.btl', '.json5' or both.
        _file_generator_.write_dashboard_config(
            dashboard_config_abspath=_pp_.rel_to_abs(
                rootpath=self.get_proj_rootpath(),
                relpath=".beetle/dashboard_config.btl",
            ),
            dashboard_config_dict=dashboard_config_dict,
        )

        # & Reset all history to baseline. This also refreshes the Dashboard if it exists.
        self.__clear_all_history(
            callback=self.__save_finish,
            callbackArg=save_params,
        )
        return

    def __save_finish(self, save_params: Dict[str, Any]) -> None:
        """"""
        data.signal_dispatcher.source_analyzer.start_stop_engine_conditionally_sig.emit()
        callback = save_params["callback"]
        callbackArg = save_params["callbackArg"]
        if data.dashboard is not None:
            # Repoints in the 'permission popup' could cause some entries in the layout-section of
            # the Dashboard to change. Sometimes, that should result in an error-state to disappear.
            # A refresh of the layout-section in the dashboard is therefore needed.
            def finish(*args):
                if callback is not None:
                    callback(True, callbackArg)
                return

            self.get_treepath_seg().trigger_dashboard_refresh(
                callback=finish,
                callbackArg=None,
            )
            return

        if callback is not None:
            callback(True, callbackArg)
        return

    def __save_abort(self, save_params: Dict[str, Any]) -> None:
        """"""
        data.signal_dispatcher.source_analyzer.start_stop_engine_conditionally_sig.emit()
        callback = save_params["callback"]
        callbackArg = save_params["callbackArg"]

        def abort_after_refresh(*args) -> None:
            if callback is not None:
                callback(False, callbackArg)
            return

        if data.dashboard is not None:
            data.dashboard.refresh_all_recursive(
                callback=abort_after_refresh,
                callbackArg=None,
            )
            return
        if callback is not None:
            callback(False, callbackArg)
        return

    def printout_in_terminal(self, printfunc: Callable) -> None:
        """Print all info about this Project()-instance to the given print
        function."""
        assert self is data.current_project
        printfunc(self.printout_short_in_terminal(printfunc))
        return

    def printout_short_in_terminal(self, printfunc: Callable) -> None:
        """Print only the essentials."""
        assert self is data.current_project
        boardfam_unicum = self.get_board().get_boardfam_unicum()
        board_unicum = self.get_board().get_board_unicum()
        chip_unicum = self.get_chip().get_chip_unicum()
        probe_unicum = self.get_probe().get_probe_unicum()
        printfunc("\n")
        printfunc(f"{self.get_proj_rootpath()}\n", "#ffffff")
        printfunc(f"boardfam_unicum = ", "#edd400")
        printfunc(f"{boardfam_unicum.get_name()}\n", "#ffffff")
        printfunc(f"board_unicum    = ", "#edd400")
        printfunc(f"{board_unicum.get_name()}\n", "#ffffff")
        printfunc(f"chip_unicum     = ", "#edd400")
        printfunc(f"{chip_unicum.get_name()}\n", "#ffffff")
        printfunc(f"probe_unicum    = ", "#edd400")
        printfunc(f"{probe_unicum.get_name()}\n", "#ffffff")
        return

    # ^                                            KILLING                                             ^#
    # % ============================================================================================== %#
    # % Destroy this Project()-instance completely.                                                    %#
    # %                                                                                                %#

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """Kill this Project()-instance."""
        print("Kill Project()-instance")
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError("Trying to kill Project() twice!")
            self.__dead = True

        def kill_board(*args) -> None:
            self.get_board().self_destruct(
                callback=kill_chip,
                callbackArg=None,
            )
            return

        def kill_chip(*args) -> None:
            self.get_chip().self_destruct(
                callback=kill_probe,
                callbackArg=None,
            )
            return

        def kill_probe(*args) -> None:
            self.get_probe().self_destruct(
                callback=kill_toolpath_seg,
                callbackArg=None,
            )
            return

        def kill_toolpath_seg(*args) -> None:
            self.get_toolpath_seg().self_destruct(
                callback=kill_treepath_seg,
                callbackArg=None,
            )
            return

        def kill_treepath_seg(*args) -> None:
            self.get_treepath_seg().self_destruct(
                callback=kill_lib_seg,
                callbackArg=None,
            )
            return

        def kill_lib_seg(*args) -> None:
            lib_seg: _lib_seg_.LibSeg = self.get_lib_seg()
            if lib_seg is None:
                kill_version_seg()
                return
            lib_seg.self_destruct(
                callback=kill_version_seg,
                callbackArg=None,
            )
            return

        def kill_version_seg(*args) -> None:
            version_seg: _version_seg_.VersionSeg = self.get_version_seg()
            if version_seg is None:
                finish()
                return
            version_seg.self_destruct(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        kill_board()
        return

    # ^                                            HISTORY                                             ^#
    # % ============================================================================================== %#
    # % Keep history of actions.                                                                       %#
    # %                                                                                                %#

    def push_projhistory(self, projsegment: _ps_.ProjectSegment) -> None:
        """"""
        # print(f'push_projhistory({projsegment.__class__.__name__}())\n')
        assert not projsegment.is_fake()
        assert (
            isinstance(projsegment, _board_.Board)
            or isinstance(projsegment, _chip_.Chip)
            or isinstance(projsegment, _probe_.Probe)
            or isinstance(projsegment, _treepath_seg_.TreepathSeg)
            or isinstance(projsegment, _toolpath_seg_.ToolpathSeg)
            or isinstance(projsegment, _version_seg_.VersionSeg)
        )

        history_list = cast(
            """
            List[
                Union[
                    _board_.Board,
                    _chip_.Chip,
                    _probe_.Probe,
                    _toolpath_seg_.ToolpathSeg,
                    _treepath_seg_.TreepathSeg,
                    _lib_seg_.LibSeg,
                    _version_seg_.VersionSeg,
                ]
            ]
            """,
            self.__proj_dict["history"],
        )
        history_list.append(projsegment)
        return

    def __pop_projhistory(self) -> Optional[_ps_.ProjectSegment]:
        """"""
        history_list = cast(
            """
            List[
                Union[
                    _board_.Board,
                    _chip_.Chip,
                    _probe_.Probe,
                    _toolpath_seg_.ToolpathSeg,
                    _treepath_seg_.TreepathSeg,
                    _lib_seg_.LibSeg,
                    _version_seg_.VersionSeg,
                ]
            ]
            """,
            self.__proj_dict["history"],
        )
        if len(history_list) == 0:
            return None
        el = history_list[-1]
        del history_list[-1]
        return el

    def undo(self) -> None:
        """"""
        print("Project().undo()")
        history_list = cast(
            """
            List[
                Union[
                    _board_.Board,
                    _chip_.Chip,
                    _probe_.Probe,
                    _toolpath_seg_.ToolpathSeg,
                    _treepath_seg_.TreepathSeg,
                    _lib_seg_.LibSeg,
                    _version_seg_.VersionSeg,
                ]
            ]
            """,
            self.__proj_dict["history"],
        )
        if len(history_list) == 0:
            print("Project history empty")
            return
        projsegment = self.__pop_projhistory()
        print(f"{projsegment.__class__.__name__}().get_history().pop()")
        projsegment.get_history().pop()
        data.dashboard.check_unsaved_changes()
        return

    def __clear_all_history(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        # Reset the baseline, but postpone refreshment until the end.
        self.get_board().get_history().reset_baseline(refresh=False)
        self.get_chip().get_history().reset_baseline(refresh=False)
        self.get_probe().get_history().reset_baseline(refresh=False)
        self.get_treepath_seg().get_history().reset_baseline(refresh=False)
        self.get_toolpath_seg().get_history().reset_baseline(refresh=False)
        try:
            self.get_version_seg().get_history().reset_baseline(refresh=False)
        except:
            traceback.print_exc()
        self.__proj_dict["history"] = []
        if data.dashboard is not None:
            data.dashboard.check_unsaved_changes()
            data.dashboard.refresh_all_recursive(
                callback=callback,
                callbackArg=callbackArg,
            )
        else:
            callback(callbackArg)
        return

    # ^                                       FILE NOTIFICATIONS                                       ^#
    # % ============================================================================================== %#
    # % WARNING: Still need to trigger a dashboard save here (or at least show                         %#
    # % the save icon)                                                                                 %#
    # %                                                                                                %#

    def __file_saved_notification(self, file_abspath: str) -> None:
        """
        ORIGIN:
        Matic calls this when a file in the editor gets saved.

        GOAL:
        If the saved file is:
            - a linkerscript -> reparse linkerscript [no longer needed]
            - a makefile     -> notify SA engine
            - a library file -> refresh all library segments
        """
        file_abspath = _pp_.standardize_abspath(file_abspath)
        filename = file_abspath.split("/")[-1]

        # Check if the saved file corresponds to something remarkable (eg. a linkerscript, makefile,
        # ..) such that something needs to be refreshed in the dashboard.
        show_filetree_mk_warning: bool = False
        chip: _chip_.Chip = self.get_chip()
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()
        lib_seg: _lib_seg_.LibSeg = self.get_lib_seg()

        # $ Makefile
        if (
            (file_abspath == treepath_seg.get_abspath("MAKEFILE"))
            or ("makefile" in filename)
            or filename.endswith((".mk", ".make"))
        ):
            if filename.lower() == "filetree.mk":
                # 'filetree.mk' was modified. A dialog should be shown to warn the user this is not
                # a good idea.
                _ht_.save_filetree_mk_warning()
            else:
                # Some makefile was modified. The SA should be informed. Matic's code already
                # takes care of that.
                pass

        # $ Linkerscript
        elif (
            (file_abspath == treepath_seg.get_abspath("LINKERSCRIPT"))
            or ("linker" in filename)
            or filename.endswith(".ld")
        ):
            # No longer needed to reparse the linkerscript. Johan takes care of that now.
            pass

        # $ Library properties file
        elif filename.endswith("library.properties"):
            # The libraries must be refreshed. Don't do that here, because this is running in a
            # loop! Wait for the loop to finish.
            self.refresh_all_lib_segs(
                callback=None,
                callbackArg=None,
            )

        # $ Other
        else:
            # This is probably an unremarkable file. Nothing needs to be done in the dashboard.
            pass
        return

    def __file_added_notification(
        self,
        file_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* adds a file.

        GOAL:
        Depending on the name of the added file, the user must be queried if one of the dashboard
        items should now point to this new file.

        APPROACH:
        [Add to TreepathSeg()]
        Obtain the corresponding PathObj()-instance from the TreepathSeg() and ask the user if it
        should point to the new 'file_abspath'.
        """
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()

        def ask_conditionally_and_apply(
            pathObj: _treepath_obj_.TreepathObj,
        ) -> bool:
            "Ask only if given pathObj points to nothing"
            cur_abspath = pathObj.get_abspath()
            if (
                (cur_abspath is not None)
                and (cur_abspath.lower() != "none")
                and os.path.isfile(cur_abspath)
            ):
                # $ Don't ask
                return False
            # $ Ask!
            ask_and_apply(pathObj)
            return True

        def ask_and_apply(pathObj: _treepath_obj_.TreepathObj) -> None:
            "Ask if given pathObj should redirect"
            if (pathObj.get_abspath() is not None) and (
                pathObj.get_abspath() == file_abspath
            ):
                # No point in asking...
                return

            css = purefunctions.get_css_tags()
            green = css["green"]
            end = css["end"]
            tab = css["tab"]
            answer = gui.dialogs.popupdialog.PopupDialog.question(
                title_text=f"Point to file?",
                icon_path=f"icons/dialog/help.png",
                text=str(
                    f"Do you want to make<br>"
                    f"{tab}{green}{q}{file_abspath}{q}{end}<br>"
                    f"<br>"
                    f"your default {green}{pathObj.get_name()}{end}?"
                ),
            )
            if answer != qt.QMessageBox.StandardButton.Yes:
                return
            treepath_seg.set_abspath(
                unicum=pathObj.get_unicum(),
                abspath=file_abspath,
                history=True,
                refresh=True,
                callback=None,
                callbackArg=None,
            )
            return

        # * Start
        filename = file_abspath.split("/")[-1]
        c_dot_ext = data.c_dot_ext
        h_dot_ext = data.h_dot_ext

        # $ Source file
        # No need to take action.
        if filename.endswith(c_dot_ext) or filename.endswith(h_dot_ext):
            return

        # $ 'dashboard.mk' or 'filetree.mk'
        # No need to take action. The point of reference for these files is always the main make-
        # file. Redirection should not happen based on these two files!
        if (filename == "dashboard.mk") or (filename == "filetree.mk"):
            return

        # $ Makefile
        # Always ask for redirection if the added file is explicitely named 'makefile'. Ask condi-
        # tionally if the added file merely ends in '.mk'.
        if "makefile" in filename.lower():
            path_obj = treepath_seg.get_treepathObj("MAKEFILE")
            ask_and_apply(path_obj)
            return
        if filename.endswith(".mk"):
            path_obj = treepath_seg.get_treepathObj("MAKEFILE")
            if ask_conditionally_and_apply(path_obj):
                return

        # $ Linkerscript
        # Always ask for redirection if the added file is explicitely named 'linkerscript'. Ask con-
        # ditionally if the added file merely ends in '.ld'.
        if "linkerscript" in filename.lower():
            path_obj = treepath_seg.get_treepathObj("LINKERSCRIPT")
            ask_and_apply(path_obj)
            return
        if filename.endswith(".ld"):
            path_obj = treepath_seg.get_treepathObj("LINKERSCRIPT")
            if ask_conditionally_and_apply(path_obj):
                return

        # $ GDB Flashfile
        # Always ask for redirection.
        if "gdb" in filename.lower():
            path_obj = treepath_seg.get_treepathObj("GDB_FLASHFILE")
            ask_and_apply(path_obj)
            return

        # $ OpenOCD cfg file
        # Always ask for redirection.
        if "openocd" in filename.lower():
            if ("chip" in filename.lower()) or ("mcu" in filename.lower()):
                path_obj = treepath_seg.get_treepathObj("OPENOCD_CHIPFILE")
                ask_and_apply(path_obj)
                return
            if "probe" in filename.lower():
                path_obj = treepath_seg.get_treepathObj("OPENOCD_PROBEFILE")
                ask_and_apply(path_obj)
                return

        # $ Library file
        # Refresh the LibSeg().
        if filename == "library.properties":
            self.refresh_all_lib_segs(
                callback=None,
                callbackArg=None,
            )
            return
        return

    def __file_renamed_notification(
        self,
        old_abspath: str,
        new_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* renames or moves a file.

        GOALS:
        [Repair TreepathSeg()s]
        If 'old_abspath' corresponds to a PathObj() in the TreepathSeg(), make the PathObj() point
        to the new filepath.

        [Add to TreepathSeg()]
        If there's no match with 'old_abspath', maybe 'new_abspath' means something. Invoke the no-
        tification for a newly added file.
        """
        # Figure out if a PathObj() corresponds to 'old_abspath'. If so, update it.
        match_found = False
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()
        path_obj = treepath_seg.get_treepathObj_from_abspath(old_abspath)

        def pre_finish(*args) -> None:
            # If 'old_abspath' corresponds to a library file, the library segments must be refresh-
            # ed. Same for 'new_abspath' of course - but that will be taken care of in 'file_added_
            # notification()'. However, only do that if the refreshment isn't active at this very
            # moment. It is possible that the File().self_destruct() method (which invokes this no-
            # tification method) was initiated by the library Dashboard refreshment function itself
            # when it refreshes part of the Filetree! Therefore, the 'skip_if_busy' parameter must
            # be True.
            # NOTE:
            # Actually, with the new Filetree, this particular case should not happen anymore.
            if old_abspath.endswith("library.properties"):
                self.refresh_all_lib_segs(
                    skip_if_busy=True,
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            # If there's no match with 'old_abspath', maybe 'new_abspath' means something. Invoke
            # the notification for a newly added file.
            if not match_found:
                self.__file_added_notification(
                    file_abspath=new_abspath,
                    explicit_action=explicit_action,
                )
                return
            return

        # * Start
        if path_obj is None:
            # Renamed file is not relevant to this TreepathSeg()
            pre_finish()
            return
        path_obj_unicum = path_obj.get_unicum()
        path_obj_name = path_obj_unicum.get_name()
        path_obj_abspath = path_obj.get_abspath()
        if path_obj_name in ("BUTTONS_BTL",):
            # Don't touch these paths
            pre_finish()
            return

        # At this point, we have a valid PathObj() from the observed TreepathSeg(). This Path-
        # Obj() corresponds to 'old_abspath'. Update it to point to 'new_abspath'.
        match_found = True
        treepath_seg.set_abspath(
            unicum=path_obj_unicum,
            abspath=new_abspath,
            history=True,
            refresh=True,
            callback=pre_finish,
            callbackArg=None,
        )
        return

    def __file_deleted_notification(
        self,
        file_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* deletes a file.

        GOAL:
        [Repair TreepathSeg()s]
        If 'file_abspath' corresponds to a PathObj() in the TreepathSeg(), make the PathObj() point
        to None.
        """
        # Figure out if a PathObj() corresponds to 'file_abspath'. If so, update it.

        def finish(*args) -> None:
            # If 'file_abspath' corresponds to a library file, the library segments must be refresh-
            # ed. However, only do that if the refreshment isn't active at this very moment. It is
            # possible that the File().self_destruct() method (which invokes this notification
            # method) was initiated by the library Dashboard refreshment function itself when it
            # refreshes part of the Filetree! Therefore, the 'skip_if_busy' parameter must be True.
            # NOTE:
            # Actually, with the new Filetree, this particular case should not happen anymore.
            if file_abspath.endswith("library.properties"):
                self.refresh_all_lib_segs(
                    skip_if_busy=True,
                    callback=None,
                    callbackArg=None,
                )
                return
            return

        # * Start
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()
        path_obj = treepath_seg.get_treepathObj_from_abspath(file_abspath)
        if path_obj is None:
            # Deleted file is not relevant to this TreepathSeg()
            finish()
            return

        path_obj_unicum = path_obj.get_unicum()
        path_obj_name = path_obj_unicum.get_name()
        path_obj_abspath = path_obj.get_abspath()
        if path_obj_name in ("BUTTONS_BTL",):
            # Don't touch these paths
            finish()
            return

        if path_obj.is_default_fallback():
            # PathObj()s that have a default fallback should not be touched just because the
            # file has been deleted. Eg: .bin file, ...
            finish()
            return

        # At this point, we have a valid PathObj() from the observed TreepathSeg(). This Path-
        # Obj() corresponds to the deleted 'file_abspath'. Update it to point to None.
        treepath_seg.set_abspath(
            unicum=path_obj.get_unicum(),
            abspath=None,
            history=True,
            refresh=True,
            with_gui=True,
            callback=finish,
            callbackArg=None,
        )
        return

    def __folder_added_notification(
        self,
        folder_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* adds a folder.

        GOAL:
        [Add to TreepathSeg()]
        If the foldername has 'build' in it, ask the user if he wants to redirect the corresponding
        PathObj() from the TreepathSeg().
        """
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()

        def ask_and_apply(pathObj: _treepath_obj_.TreepathObj) -> None:
            "Ask if given pathObj should redirect"
            # In practice, this will only be invoked for the 'BUILD_DIR'.
            css = purefunctions.get_css_tags()
            green = css["green"]
            end = css["end"]
            tab = css["tab"]
            answer = gui.dialogs.popupdialog.PopupDialog.question(
                title_text=f"Point to folder?",
                icon_path=f"icons/dialog/help.png",
                text=str(
                    f"Do you want to make<br>"
                    f"{tab}{green}{q}{folder_abspath}{q}{end}<br>"
                    f"<br>"
                    f"your default {green}{pathObj.get_name()}{end}?"
                ),
            )
            if answer != qt.QMessageBox.StandardButton.Yes:
                return
            treepath_seg.set_abspath(
                unicum=pathObj.get_unicum(),
                abspath=folder_abspath,
                history=True,
                refresh=True,
                callback=None,
                callbackArg=None,
            )
            return

        # * Start
        foldername = folder_abspath.split("/")[-1]
        # $ 'build/' folder
        if "build" in foldername.lower():
            path_obj = treepath_seg.get_treepathObj("BUILD_DIR")
            assert path_obj is not None
            if path_obj.get_abspath() == folder_abspath:
                # No point in asking. This strange situation can happen if this 'folder_added_noti-
                # fication()' was actually invoked from the 'folder_renamed_notification()' method.
                pass
            else:
                ask_and_apply(path_obj)
            return
        return

    def __folder_renamed_notification(
        self,
        old_abspath: str,
        new_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* renames or moves a folder.

        GOAL:
        [Repair TreepathSeg()s]
        If 'old_abspath' interferes with one or more PathObj()s in the TreepathSeg(), update these
        PathObj()s.

        [Add to TreepathSeg()]
        Also treat this case as if a new folder was added. In practice this means that the new fol-
        der will be checked for the presence of 'build' in its name. The user then gets the chance
        to make it his new 'BUILD_DIR' (*).

        (*) The 'folder_added_notification()' has a safety check for the corner case that 'old_abs-
        path' also matched the 'BUILD_DIR' and this PathObj() is already updated to 'new_abspath'.
        """

        def pre_finish(*args) -> None:
            # Renaming a folder could very well impact some libraries. Play it safe and refresh them
            # all. After that, also treat this case as if a new folder was added.
            self.refresh_all_lib_segs(
                skip_if_busy=False,
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            # Pretend new folder was added
            self.__folder_added_notification(
                folder_abspath=new_abspath,
                explicit_action=explicit_action,
            )
            return

        # * Start
        # Loop over all PathObj()s stored in the TreepathSeg(). Those that have an abspath - either
        # for a file or folder - starting with the old abspath, should be repaired (with some ex-
        # ceptions)!
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()
        refresh_treepath_seg: bool = False
        for path_obj in treepath_seg.get_treepath_obj_list():
            path_obj_unicum = path_obj.get_unicum()
            path_obj_name = path_obj_unicum.get_name()
            path_obj_abspath = path_obj.get_abspath()
            if path_obj_name in ("BUTTONS_BTL",):
                # Don't touch these paths
                continue

            if not path_obj_abspath.startswith(old_abspath):
                # Ignore this path
                continue

            # At this point, we have a valid PathObj() from the observed TreepathSeg(). This
            # PathObj() starts with 'old_abspath'. Update it.
            treepath_seg.set_abspath(
                unicum=path_obj_unicum,
                abspath=path_obj_abspath.replace(old_abspath, new_abspath, 1),
                history=True,
                refresh=False,  # Only refresh once in the end
                callback=None,
                callbackArg=None,
            )
            refresh_treepath_seg = True
            continue

        if refresh_treepath_seg:
            # One or more PathObj()s from this TreepathSeg() have been repaired.
            treepath_seg.trigger_dashboard_refresh(
                callback=pre_finish,
                callbackArg=None,
            )
            return
        pre_finish()
        return

    def __folder_deleted_notification(
        self,
        folder_abspath: str,
        explicit_action: bool,
    ) -> None:
        """
        ORIGIN:
        Should be invoked when the user *explicitely* deleted a folder.

        GOAL:
        [Repair TreepathSeg()s]
        If 'folder_abspath' interferes with one or more PathObj()s in one or more TreepathSeg()s,
        update these PathObj()s.
        """
        # Loop over all PathObj()s stored in the TreepathSeg(). Those that have an abspath - either
        # for a file or folder - starting with the deleted 'folder_abspath', should now point to
        # None (with some exceptions)!

        def finish(*args) -> None:
            # Deleting a folder could very well impact some libraries. Play it safe and refresh them
            # all. However, only do that if the refreshment isn't active at this very moment. It is
            # possible that the Folder().self_destruct() method (which invokes this notification
            # method) was initiated by the library Dashboard refreshment function itself when it re-
            # freshes part of the Filetree! Therefore, the 'skip_if_busy' parameter must be True.
            # NOTE:
            # Actually, with the new Filetree, this particular case should not happen anymore.
            self.refresh_all_lib_segs(
                skip_if_busy=True,
                callback=None,
                callbackArg=None,
            )
            return

        # * Start
        treepath_seg: _treepath_seg_.TreepathSeg = self.get_treepath_seg()
        refresh_treepath_seg = False
        for path_obj in treepath_seg.get_treepath_obj_list():
            path_obj_unicum = path_obj.get_unicum()
            path_obj_name = path_obj_unicum.get_name()
            path_obj_abspath = path_obj.get_abspath()
            if path_obj_name in ("BUTTONS_BTL",):
                # Don't touch these paths
                continue

            if not path_obj_abspath.startswith(folder_abspath):
                # Ignore this path
                continue

            if path_obj.is_default_fallback():
                # PathObj()s that have a default fallback should not be touched just because their
                # file/folder has been deleted. Eg: .bin file, ...
                continue

            # At this point, we have a valid PathObj() from the observed TreepathSeg(). This
            # PathObj() starts with 'folder_abspath'. Update it.
            treepath_seg.set_abspath(
                unicum=path_obj_unicum,
                abspath=None,
                history=True,
                refresh=False,  # Only refresh once in the end
                with_gui=True,
                callback=None,
                callbackArg=None,
            )
            refresh_treepath_seg = True
            continue

        if refresh_treepath_seg:
            # One or more PathObj()s from this TreepathSeg() have been repaired.
            treepath_seg.trigger_dashboard_refresh(
                callback=finish,
                callbackArg=None,
            )
            return
        finish()
        return

    def is_filetree_mk(self, file_abspath: str) -> bool:
        """Return True if the given file abspath points to a valid 'filetree.mk'
        file."""
        if self.get_treepath_seg().is_filetree_mk(file_abspath):
            return True
        return False

    def dashboard_mk_uses_COM_or_FLASH_PORT(self) -> str:
        """Return 'COM' if 'dashboard.mk' still refers to the old '$(COM)'
        variable.

        Otherwise, return the newer 'FLASH_PORT' convention.
        """
        abspath = self.get_treepath_seg().get_abspath("DASHBOARD_MK")
        if (
            (abspath is None)
            or (abspath.lower() == "none")
            or (not os.path.isfile(abspath))
        ):
            return "FLASH_PORT"
        content = ""
        try:
            with open(
                abspath, "r", encoding="utf-8", newline="\n", errors="replace"
            ) as f:
                content = f.read()
        except:
            purefunctions.printc(
                f"\nERROR: Cannot read {q}{abspath}{q}\n",
                color="error",
            )
            traceback.print_exc()
            print("\n")
            return "FLASH_PORT"
        if "$(COM)" in content:
            if "$(FLASH_PORT)" not in content:
                return "COM"
        return "$(FLASH_PORT)"

    def refresh_all_lib_segs(
        self,
        skip_if_busy: bool = False,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Refresh all LibSeg()-instances.

        Note: now there's only one.
        """

        def refresh(*args) -> None:
            # $ 'lib_seg' is busy
            # Try again in some milliseconds, unless the 'skip_if_busy' flag is set.
            if self.get_lib_seg().is_dashboard_refresh_running():
                if skip_if_busy:
                    # & Finish
                    if callback is not None:
                        callback(callbackArg)
                    return
                # Try again
                purefunctions.printc(
                    f"\nWARNING: refresh_all_lib_segs() -> dashboard refresh is "
                    f"already running!\n",
                    color="warning",
                )
                qt.QTimer.singleShot(
                    230,
                    refresh,
                )
                return
            # $ 'lib_seg' is not busy
            # The database is already updated at the very start of this whole procedure. It's a
            # shared database, so it wouldn't make sense to update it again. Therefore, the method
            # 'update_states()' should not be invoked here, only 'trigger_dashboard_refresh()'.
            # That's why the 'also_refresh_database' parameter should be False.
            self.get_lib_seg().trigger_dashboard_refresh(
                also_refresh_database=False,
                callback=callback,
                callbackArg=callbackArg,
            )
            return

        # First invoke 'update_state()' on any LibSeg()-instance. This triggers the LibManager()'s
        # database to refresh. It doesn't matter which LibSeg() is used for this purpose - the data-
        # base is shared amongst them all.
        # Note: Now there's actually only one LibSeg() left.
        self.get_lib_seg().update_states(callback=refresh, callbackArg=None)
        return

    def check_if_project_file(self, file_abspath: str) -> bool:
        """Return True if the given file is in the project folder."""
        file_abspath = _pp_.standardize_abspath(file_abspath)
        if file_abspath.startswith(f"{self.get_proj_rootpath()}/"):
            return True
        return False

    # ^                                     LAUNCH SOURCE ANALYZER                                     ^#
    # % ============================================================================================== %#
    # % WARNING: Still need to trigger a dashboard save here (or at least show the save icon)          %#
    # %                                                                                                %#

    def minimal_sa_requirements_met(self) -> str:
        """Return 'ok' if minimal requirements are met for the SA to start (or
        to keep it running).

        Re- turn a string describing the issue otherwise.
        """
        if not self.__with_engine:
            return "Engine off"

        # & Test makefile
        # $ Existence
        mkf = self.get_treepath_seg().get_abspath("MAKEFILE")
        if (
            (mkf is None)
            or (mkf.lower() == "none")
            or (not os.path.isfile(mkf))
        ):
            issue = "Makefile not found"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Rights makefile
        try:
            if os.access(mkf, os.R_OK):
                pass
            else:
                issue = "No read permission on makefile"
                purefunctions.printc(
                    f"\nWARNING: {issue}\n",
                    color="warning",
                )
                return issue
        except Exception as e:
            issue = "No read permission on makefile"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # & Test compiler toolchain
        # $ Existence toolchain
        toolchain = self.get_toolpath_seg().get_abspath("COMPILER_TOOLCHAIN")
        if (
            (toolchain is None)
            or (toolchain.lower() == "none")
            or (os.path.exists(toolchain) == False)
        ):
            issue = "Toolchain not found"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Matching toolchain
        if (
            self.get_toolpath_seg()
            .get_toolpathObj("COMPILER_TOOLCHAIN")
            .has_error()
        ):
            issue = f"Toolchain doesn{q}t match"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Existence compiler
        compiler = self.get_toolpath_seg().get_compiler_abspath()
        if (
            (compiler is None)
            or (compiler.lower() == "none")
            or (os.path.exists(compiler) == False)
        ):
            issue = "Compiler not found"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Rights compiler
        try:
            if os.access(compiler, os.X_OK):
                pass
            else:
                issue = "No execute permission on compiler"
                purefunctions.printc(
                    f"\nWARNING: {issue}\n",
                    color="warning",
                )
                return issue
        except Exception as e:
            issue = "No execute permission on compiler"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # & Test build automation
        # $ Existence build automation
        buildautomation = self.get_toolpath_seg().get_abspath(
            "BUILD_AUTOMATION"
        )
        if (
            (buildautomation is None)
            or (buildautomation.lower() == "none")
            or (os.path.exists(buildautomation) == False)
        ):
            issue = "Build automation tool not found"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Rights build automation
        try:
            if os.access(buildautomation, os.X_OK):
                pass
            else:
                issue = "No execute permission on build automation tool"
                purefunctions.printc(
                    f"\nWARNING: {issue}\n",
                    color="warning",
                )
                return issue
        except Exception as e:
            issue = "No execute permission on build automation tool"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # & Test build folder
        # $ Existence
        buildfolder = self.get_treepath_seg().get_abspath("BUILD_DIR")
        if (
            (buildfolder is None)
            or (buildfolder.lower() == "none")
            or (os.path.isdir(buildfolder) == False)
        ):
            issue = "Build folder not found"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # $ Rights build folder
        if not purefunctions.test_write_permissions(buildfolder, False):
            issue = "No write permission on build folder"
            purefunctions.printc(
                f"\nWARNING: {issue}\n",
                color="warning",
            )
            return issue

        # & All tests passed
        return "ok"

    # ^                                             SA TAB                                             ^#
    # % ============================================================================================== %#
    # % Fill SA Tab.                                                                                   %#
    # %                                                                                                %#

    def fill_sa_tab(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""
        # & StatusRootItem()
        status_rootitem = _status_items_.StatusRootItem()
        self.__sa_tab_items["status_items"]["status_rootitem"] = status_rootitem
        data.sa_tab.add_root(status_rootitem)
        # Status child items only need to be created in debug-mode.
        if data.debug_mode:
            # $ LaunchStatusItem()
            self.__sa_tab_items["status_items"]["launch_status_item"] = (
                _status_items_.LaunchStatusItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
            # $ InternalErrorItem()
            self.__sa_tab_items["status_items"]["internal_error_item"] = (
                _status_items_.InternalErrorItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
            # $ SAStatusItem()
            self.__sa_tab_items["status_items"]["sa_status_item"] = (
                _status_items_.SAStatusItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
            # $ LinkerStatusItem()
            self.__sa_tab_items["status_items"]["linker_status_item"] = (
                _status_items_.LinkerStatusItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
            # $ FeederStatusItem()
            self.__sa_tab_items["status_items"]["feeder_status_item"] = (
                _status_items_.FeederStatusItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
            # $ DigesterStatusItem()
            self.__sa_tab_items["status_items"]["digester_status_item"] = (
                _status_items_.DigesterStatusItem(
                    rootdir=status_rootitem,
                    parent=status_rootitem,
                )
            )
        del status_rootitem

        # & DependencyRootItem()
        dependency_rootitem = _dependency_items_.DependencyRootItem()
        self.__sa_tab_items["dependency_items"][
            "dependency_rootitem"
        ] = dependency_rootitem
        data.sa_tab.add_root(dependency_rootitem)
        # $ BuildFolderItem()
        self.__sa_tab_items["dependency_items"]["build_folder_item"] = (
            _dependency_items_.BuildFolderItem(
                rootdir=dependency_rootitem,
                parent=dependency_rootitem,
            )
        )
        # $ MakefileItem()
        self.__sa_tab_items["dependency_items"]["makefile_item"] = (
            _dependency_items_.MakefileItem(
                rootdir=dependency_rootitem,
                parent=dependency_rootitem,
            )
        )
        # $ BuildAutomationItem()
        self.__sa_tab_items["dependency_items"]["build_automation_item"] = (
            _dependency_items_.BuildAutomationItem(
                rootdir=dependency_rootitem,
                parent=dependency_rootitem,
            )
        )
        # $ CompilerToolchainItem()
        self.__sa_tab_items["dependency_items"]["compiler_toolchain_item"] = (
            _dependency_items_.CompilerToolchainItem(
                rootdir=dependency_rootitem,
                parent=dependency_rootitem,
            )
        )
        del dependency_rootitem

        # & CPULoadRootItem()
        cpu_load_rootitem = _cpu_load_items_.CPULoadRootItem()
        self.__sa_tab_items["cpu_load_items"][
            "cpu_load_rootitem"
        ] = cpu_load_rootitem
        data.sa_tab.add_root(cpu_load_rootitem)
        del cpu_load_rootitem

        # & ClearCacheRootItem
        clear_cache_rootitem = _clear_cache_items_.ClearCacheRootItem()
        self.__sa_tab_items["clear_cache_items"][
            "clear_cache_rootitem"
        ] = clear_cache_rootitem
        data.sa_tab.add_root(clear_cache_rootitem)
        del clear_cache_rootitem

        def add_next_dependency_child(
            child_iter: Iterator[
                Union[
                    _dependency_items_.BuildFolderItem,
                    _dependency_items_.MakefileItem,
                    _dependency_items_.BuildAutomationItem,
                    _dependency_items_.CompilerToolchainItem,
                ]
            ],
        ) -> None:
            try:
                child = next(child_iter)
            except StopIteration:
                # Status child items only need to be added in debug-mode. Jump
                # to finish otherwise.
                if data.debug_mode:
                    add_next_status_child(
                        iter(
                            [
                                cast(
                                    _status_items_.LaunchStatusItem,
                                    self.__sa_tab_items["status_items"][
                                        "launch_status_item"
                                    ],
                                ),
                                cast(
                                    _status_items_.InternalErrorItem,
                                    self.__sa_tab_items["status_items"][
                                        "internal_error_item"
                                    ],
                                ),
                                cast(
                                    _status_items_.SAStatusItem,
                                    self.__sa_tab_items["status_items"][
                                        "sa_status_item"
                                    ],
                                ),
                                cast(
                                    _status_items_.LinkerStatusItem,
                                    self.__sa_tab_items["status_items"][
                                        "linker_status_item"
                                    ],
                                ),
                                cast(
                                    _status_items_.FeederStatusItem,
                                    self.__sa_tab_items["status_items"][
                                        "feeder_status_item"
                                    ],
                                ),
                                cast(
                                    _status_items_.DigesterStatusItem,
                                    self.__sa_tab_items["status_items"][
                                        "digester_status_item"
                                    ],
                                ),
                            ]
                        )
                    )
                    return
                finish()
                return
            cast(
                _dependency_items_.DependencyRootItem,
                self.__sa_tab_items["dependency_items"]["dependency_rootitem"],
            ).add_child(
                child=child,
                alpha_order=False,
                show=False,
                callback=add_next_dependency_child,
                callbackArg=child_iter,
            )
            return

        def add_next_status_child(
            child_iter: Iterator[
                Union[
                    _status_items_.LaunchStatusItem,
                    _status_items_.InternalErrorItem,
                    _status_items_.SAStatusItem,
                    _status_items_.LinkerStatusItem,
                    _status_items_.FeederStatusItem,
                    _status_items_.DigesterStatusItem,
                ]
            ],
        ) -> None:
            try:
                child = next(child_iter)
            except StopIteration:
                finish()
                return
            cast(
                _status_items_.StatusRootItem,
                self.__sa_tab_items["status_items"]["status_rootitem"],
            ).add_child(
                child=child,
                alpha_order=False,
                show=False,
                callback=add_next_status_child,
                callbackArg=child_iter,
            )
            return

        def finish(*args) -> None:
            sa_tab_body: _chassis_sa_tab_.SATabBody = cast(
                "_chassis_sa_tab_.SATabBody",
                data.sa_tab.get_chassis_body(),
            )
            sa_tab_body.init_sa_tab_body()
            self.__sa_tab_initialized = True
            # self.start_stop_sa_conditionally()
            # The CPULoadRootItem() had a problem. Once I added the dropdown
            # widget, it no longer displayed itself properly: both the button,
            # label and dropdown were hidden if the SA Tab was not focused at
            # startup. Therefore, I added this solution here.
            try:
                _cpu_load_rootitem: _cpu_load_items_.CPULoadRootItem = cast(
                    _cpu_load_items_.CPULoadRootItem,
                    self.__sa_tab_items["cpu_load_items"]["cpu_load_rootitem"],
                )
                cpu_btn: _item_btn_.ItemBtn = cast(
                    "_item_btn_.ItemBtn",
                    _cpu_load_rootitem.get_widget("itemBtn"),
                )
                cpu_lbl: _item_lbl_.ItemLbl = cast(
                    "_item_lbl_.ItemLbl",
                    _cpu_load_rootitem.get_widget("itemLbl"),
                )
                cpu_dropdown: _item_dropdown_.ItemDropdown = cast(
                    "_item_dropdown_.ItemDropdown",
                    _cpu_load_rootitem.get_widget("itemDropdown"),
                )
                cpu_btn.show()
                cpu_lbl.show()
                cpu_dropdown.show()
                del _cpu_load_rootitem
            except:
                traceback.print_exc()

            if callback is not None:
                callback(callbackArg)
            return

        add_next_dependency_child(
            iter(
                [
                    cast(
                        _dependency_items_.BuildFolderItem,
                        self.__sa_tab_items["dependency_items"][
                            "build_folder_item"
                        ],
                    ),
                    cast(
                        _dependency_items_.MakefileItem,
                        self.__sa_tab_items["dependency_items"][
                            "makefile_item"
                        ],
                    ),
                    cast(
                        _dependency_items_.BuildAutomationItem,
                        self.__sa_tab_items["dependency_items"][
                            "build_automation_item"
                        ],
                    ),
                    cast(
                        _dependency_items_.CompilerToolchainItem,
                        self.__sa_tab_items["dependency_items"][
                            "compiler_toolchain_item"
                        ],
                    ),
                ]
            )
        )
        return

    def trigger_sa_tab_refresh(
        self,
        reason: str,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """
        ATTENTION:
        This method gets lots of refresh requests from:
            - linker_status_changed_slot()
            - project_status_changed_slot()
        Therefore I needed to implement a mechanism to avoid too many triggers.
        """
        if (not self.__sa_tab_initialized) or (
            not self.__sa_tab_refresh_mutex.acquire(blocking=False)
        ):
            # The SA Tab is not yet initialized OR the mutex cannot be acquired. Start a check loop
            # if there is none at the moment.
            if self.__sa_tab_check_loop_running:
                # No need to loop again. Just quit.
                # print(f'trigger_sa_tab_refresh({q}{reason}{q}) -> ignore')
                if callback is not None:
                    callback(callbackArg)
                return
            # Start a check loop.
            self.__sa_tab_check_loop_running = True
            # print(f'trigger_sa_tab_refresh({q}{reason}{q}) -> wait')
            qt.QTimer.singleShot(
                150,
                functools.partial(
                    self.trigger_sa_tab_refresh,
                    reason,
                    callback,
                    callbackArg,
                ),
            )
            return

        # At this point, we know that the SA Tab is initialized AND its mutex is grabbed. If a check
        # loop was running, it can stop now because the refresh is gonna start.
        # print(f'trigger_sa_tab_refresh({q}{reason}{q}) -> run')
        assert self.__sa_tab_initialized
        assert self.__sa_tab_refresh_mutex.locked()
        self.__sa_tab_check_loop_running = False

        def refresh_next_rootitem(
            rootitem_iter: Iterator[
                Union[
                    _status_items_.StatusRootItem,
                    _dependency_items_.DependencyRootItem,
                    _cpu_load_items_.CPULoadRootItem,
                    _clear_cache_items_.ClearCacheRootItem,
                ]
            ],
        ) -> None:
            try:
                rootitem = next(rootitem_iter)
            except StopIteration:
                self.__sa_tab_refresh_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return
            if self.__sa_tab_check_loop_running:
                # The 'trigger_sa_tab_refresh()' has been invoked while again. Stop refreshing now,
                # release the mutex and let the next round restart the refresh.
                self.__sa_tab_refresh_mutex.release()
                if callback is not None:
                    callback(callbackArg)
                return
            rootitem.refresh_recursive_later(
                refreshlock=True,
                force_stylesheet=False,
                callback=refresh_next_rootitem,
                callbackArg=rootitem_iter,
            )
            return

        refresh_next_rootitem(
            iter(
                [
                    cast(
                        _status_items_.StatusRootItem,
                        self.__sa_tab_items["status_items"]["status_rootitem"],
                    ),
                    cast(
                        _dependency_items_.DependencyRootItem,
                        self.__sa_tab_items["dependency_items"][
                            "dependency_rootitem"
                        ],
                    ),
                    cast(
                        _cpu_load_items_.CPULoadRootItem,
                        self.__sa_tab_items["cpu_load_items"][
                            "cpu_load_rootitem"
                        ],
                    ),
                    cast(
                        _clear_cache_items_.ClearCacheRootItem,
                        self.__sa_tab_items["clear_cache_items"][
                            "clear_cache_rootitem"
                        ],
                    ),
                ]
            )
        )
        return

    # ^                                   MAKEFILE VERSIONING SYSTEM                                   ^#
    # % ============================================================================================== %#
    # % WARNING: Still need to trigger a dashboard save here (or at least show the save icon)          %#
    # %                                                                                                %#

    def get_makefile_interface_version(self) -> Union[str, int]:
        """Get the makefile interface version."""
        return self.get_version_seg().get_version_nr()

    def set_makefile_interface_version_needs_to_be_applied(
        self, apply: bool
    ) -> None:
        """Dashboard save is needed to trigger correction?"""
        self.get_version_seg().set_version_needs_to_be_applied(apply)
        return

    def get_makefile_interface_version_needs_to_be_applied(self) -> bool:
        """True -> The makefile interface version is not properly mentioned in
        'dashboard.mk' or it is wrong.

        A Dashboard save is needed to trigger correction.
        """
        return self.get_version_seg().get_version_needs_to_be_applied()

    # ^                               BUILD AND FLASH ERROR SUGGESTIONS                                ^#
    # % ============================================================================================== %#
    # % Get suggestions for build and flash errors, to be printed in the make console.                 %#
    # %                                                                                                %#

    def __wrap_suggestions(self, target: str, message: str) -> str:
        """"""
        css = purefunctions.get_dark_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        orange = css["orange"]
        yellow = css["yellow"]
        end = css["end"]

        v_line = "&#9474;"
        corner_ul = "&#9484;"
        corner_ur = "&#9488;"
        corner_dr = "&#9496;"
        corner_dl = "&#9492;"
        h_line = "&#9472;"
        s = "&nbsp;"
        # $ Intro
        if target == "important message":
            result = [
                "",
                '<p align="left">',
                f"{orange}{corner_ul}{h_line*22}[ IMPORTANT ]{h_line*23}{corner_ur}{end}",
                f"{orange}{v_line}{s*58}{v_line}{end}",
            ]
        else:
            result = [
                "",
                '<p align="left">',
                f"{orange}{corner_ul}{h_line*21}[ {target.upper()} FAILED ]{h_line*21}{corner_ur}{end}",
                f"{orange}{v_line}{s*58}{v_line}{end}",
            ]

        # $ Content
        lines = message.splitlines()
        for line in lines:
            line_len = len(line)
            # Compute the trailing spaces string. A string like 'foo  ' will have two trailing
            # spaces and (57 - len('foo  ')) more.
            trailing_spaces = s * (len(line) - len(line.rstrip())) + s * (
                57 - len(line)
            )
            # Compute the leading spaces string. A string like '  foo' will have two leading spaces
            # and one extra (all strings get one extra leading space).
            leading_spaces = s + s * (len(line) - len(line.lstrip()))
            if line.startswith("**") and line.endswith("**"):
                line = line.strip("*")
                line = f"{yellow}{line}{end}{s*4}"
            if line_len < 57:
                # Glue the leading spaces on the left, then glue the trailing spaces on the right
                # and finish off with a vertical orange line.
                line = f"{leading_spaces}{line.strip()}{trailing_spaces}{orange}{v_line}{end}"
            else:
                # Only glue the leading spaces on the left.
                line = f"{leading_spaces}{line.strip()}"
            result.append(f"{orange}{v_line}{end}{line}")
            continue

        # $ End
        result.extend(
            [
                f"{orange}{v_line}{s*58}{v_line}{end}",
                f"{orange}{corner_dl}{h_line*58}{corner_dr}{end}",
                "</p>",
            ]
        )
        return "<br>".join(result)

    def get_special_wch_message(self) -> str:
        """Display this WCH message after each build and flash that succeeded.

        A similar WCH message for failed builds and flashes can be found in
        'get_build_error_suggestions()' and 'get_flash_error_suggestions()'.
        """
        message: str = str(
            f"\n"
            f"**WCH COMPILER:**\n"
            f"  Some of our users reported malfunctioning WCH sample\n"
            f"  projects, related to the compiler. Check out this\n"
            f"  webpage for a quick fix:\n"
            f"  <a href={q}{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler{q} style={q}color: #8fb3d9;{q}>{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler</a>\n"
        )
        return self.__wrap_suggestions(
            target="important message",
            message=message,
        )

    def get_build_error_suggestions(self) -> str:
        """"""
        # $ Print intro
        message: str = str(
            "**GENERAL SUGGESTIONS:**\n"
            " - Did you wait for the Source Analyzer to finish? Maybe\n"
            "   the progress bar in the bottom-right corner was still\n"
            "   running.\n"
            " - Check your Dashboard for problems.\n"
        )

        try:
            if (
                "wch"
                in self.get_board().get_board_dict()["manufacturer"].lower()
            ) or (
                "wch"
                in self.get_chip().get_chip_dict(None)["manufacturer"].lower()
            ):
                if "10.2.0" in self.get_toolpath_seg().get_unique_id(
                    "COMPILER_TOOLCHAIN"
                ):
                    message += str(
                        f"\n"
                        f"**WCH COMPILER:**\n"
                        f"  Some of our users reported malfunctioning WCH sample\n"
                        f"  projects, related to the compiler. Check out this\n"
                        f"  webpage for a quick fix:\n"
                        f"  <a href={q}{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler{q} style={q}color: #8fb3d9;{q}>{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler</a>\n"
                    )
        except:
            pass

        return self.__wrap_suggestions(
            target="build",
            message=message,
        )

    def get_flash_error_suggestions(self) -> str:
        """"""
        board: _board_.Board = self.get_board()
        board_link: Optional[str] = None
        if board is not None:
            try:
                board_link = board.get_board_dict()["link"]
            except:
                board_link = None
                traceback.print_exc()
        probe: _probe_.Probe = self.get_probe()
        probe_link: Optional[str] = None
        if probe is not None:
            try:
                probe_link = probe.get_probe_dict()["link"]
            except:
                probe_link = None
                traceback.print_exc()

        # $ Print intro
        message: str = str(
            "**GENERAL SUGGESTIONS:**\n"
            "  Check your Dashboard for problems.\n"
        )

        # $ Print flashtool info
        # Extract the flasthool unique ID. Then check if 'avrdude' is present in it. If so, check
        # the version of avrdude. If the version is below 7, a warning must be shown.
        flashtool_uid: Optional[str] = None
        version: Optional[str] = None
        suffix: Optional[str] = None
        is_avrdude: bool = False
        is_below_v7: bool = False

        tool_obj: _tool_obj_.ToolpathObj = (
            self.get_toolpath_seg().get_toolpathObj("FLASHTOOL")
        )
        if tool_obj is not None:
            flashtool_uid = tool_obj.get_unique_id()
            if flashtool_uid is not None:
                flashtool_uid = flashtool_uid.lower()
            if (flashtool_uid is not None) and (
                flashtool_uid.lower() == "none"
            ):
                flashtool_uid = None
            if (flashtool_uid is not None) and ("avrdude" in flashtool_uid):
                is_avrdude = True
                version = tool_obj.get_version_info("version")
                suffix = tool_obj.get_version_info("suffix")
        if is_avrdude and (version is not None):
            if purefunctions.is_more_recent_than("7.0.0", version):
                is_below_v7 = True
        if is_avrdude and is_below_v7:
            version_str: str = version
            if suffix is not None:
                version_str += f" ({suffix})"
            message += str(
                f"\n"
                f"**AVRDUDE VERSION:**\n"
                f"  Your current avrdude version is: {version_str}\n"
                f"  All avrdude versions below 7.0.0 have troubles to\n"
                f"  locate the {q}avrdude.conf{q} file. Go to:\n"
                f"      Dashboard > Tools > Flashtool\n"
                f"  and make sure you select an avrdude version of at\n"
                f"  least 7.0.0.\n"
            )
        if "blue-pill" in self.get_board().get_name().lower().replace("_", "-"):
            message += str(
                f"\n"
                f"**BLUE PILL MICROCONTROLLER:**\n"
                f"  Maybe the microcontroller on your Blue Pill\n"
                f"  is not a genuine STM32 chip. In that case,\n"
                f"  you{q}ll get the error {q}UNEXPECTED idcode{q}.\n"
                f"  Check the following page for the solution:\n"
                f"  <a href={q}{board_link}{q} style={q}color: #8fb3d9;{q}>{board_link}</a>\n"
            )
        elif "rpi-pico" in self.get_board().get_name().lower().replace(
            "_", "-"
        ):
            message += str(
                f"\n"
                f"**PI PICO BOARD:**\n"
                f"  Are you using a second Pi Pico board as a flash/debug\n"
                f"  device for your target Pi Pico? Flash the {q}picoprobe{q}\n"
                f"  firmware to that second Pi Pico board:\n"
                f"  <a href={q}{serverfunctions.get_base_url_wfb()}/#supported-hardware/raspberry-pi/probes/modified-pi-pico{q} style={q}color: #8fb3d9;{q}>{serverfunctions.get_base_url_wfb()}/#supported-hardware/raspberry-pi/probes/modified-pi-pico</a>\n"
                f"  Check also the connections on this page:\n"
                f"  <a href={q}{board_link}{q} style={q}color: #8fb3d9;{q}>{board_link}</a>\n"
                f"  \n"
                f"  Are you using the official Pi Debug Probe? Check the installation\n"
                f"  steps here:\n"
                f"  <a href={q}{serverfunctions.get_base_url_wfb()}/#supported-hardware/raspberry-pi/probes/pi-debug-probe{q} style={q}color: #8fb3d9;{q}>{serverfunctions.get_base_url_wfb()}/#supported-hardware/raspberry-pi/probes/pi-debug-probe</a>\n"
                f"  Check also the connections on this page:\n"
                f"  <a href={q}{board_link}{q} style={q}color: #8fb3d9;{q}>{board_link}</a>\n"
            )
            # This is all. No need to add more info.
            return self.__wrap_suggestions(
                target="flash",
                message=message,
            )
        elif (
            "wch" in self.get_board().get_board_dict()["manufacturer"].lower()
        ) or (
            "wch" in self.get_chip().get_chip_dict(None)["manufacturer"].lower()
        ):
            try:
                if "10.2.0" in self.get_toolpath_seg().get_unique_id(
                    "COMPILER_TOOLCHAIN"
                ):
                    message += str(
                        f"\n"
                        f"**WCH COMPILER:**\n"
                        f"  Some of our users reported malfunctioning WCH sample\n"
                        f"  projects, related to the compiler. Check out this\n"
                        f"  webpage for a quick fix:\n"
                        f"  <a href={q}{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler{q} style={q}color: #8fb3d9;{q}>{serverfunctions.get_base_url_wfb()}/#supported-hardware/wch/compiler</a>\n"
                    )
                if (flashtool_uid is not None) and ("wchisp" in flashtool_uid):
                    message += str(
                        f"\n"
                        f"**WCH ISP:**\n"
                        f"  This is the WCH ISP flashtool.\n"
                    )
            except:
                pass

        # $ Driver installations
        message += str(
            f"\n"
            f"**BOARD AND FLASH/DEBUG PROBE INSTALLATION:**\n"
            f"  Did you install the board (or flash/debug probe)?\n"
        )

        # $ Driver installations => board
        if board_link is not None:
            message += str(
                f"\n"
                f"  Check the board installation instructions:\n"
                f"  <a href={q}{board_link}{q} style={q}color: #8fb3d9;{q}>{board_link}</a>\n"
            )

        # $ Driver installation => probe
        if probe_link is not None:
            message += str(
                f"\n"
                f"  Check the flash/debug probe installation instructions:\n"
                f"  <a href={q}{probe_link}{q} style={q}color: #8fb3d9;{q}>{probe_link}</a>\n"
            )

        return self.__wrap_suggestions(
            target="flash",
            message=message,
        )
