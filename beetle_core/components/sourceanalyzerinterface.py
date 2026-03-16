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

import os
import sys
import threading
import qt
import data
import purefunctions
import functions
import source_analyzer
import components.singleton
import components.diagnostics
import components.symbolhandler
import project.makefile_target_executer

from typing import *
from various.kristofstuff import *


class SourceAnalysisCommunicator(
    qt.QObject, metaclass=components.singleton.QSingleton
):
    linker_status_changed_sig = qt.pyqtSignal(int)
    project_status_changed_sig = qt.pyqtSignal(int)
    internal_sa_err_sig = qt.pyqtSignal(str)
    project_generated_sig = qt.pyqtSignal(object, object, object)

    def __init__(self) -> None:
        """"""
        super().__init__()
        self.__cec_project: Optional[Project] = None
        self.__log_text: List[str] = (
            []
        )  # Store text to be printed in the SA Tab
        self.__internal_error: bool = (
            False  # Keep track of internal errors in rest of Embeetle
        )
        self.__engine_on: bool = (
            False  # Keep track of the engine's on/off state
        )
        self.__build_path: Optional[str] = (
            None  # Keep track of absolute path to the build directory
        )
        # Keep track of the GNU Make settings
        self.__make_config: Dict[
            str, Union[List[str], Dict[str, str], None]
        ] = {
            "cmd_list": None,
            "environ_dict": None,
        }
        self.__project_status: int = 0
        self.__linker_status: int = 0

        # Keep a string that describes the current issue why the SA cannot start. The string is None
        # if there is no such issue.
        self.__sa_engine_launch_issue: Optional[str] = None

        self.linker_status_changed_sig.connect(
            self.__linker_status_changed_slot
        )
        self.project_status_changed_sig.connect(
            self.__project_status_changed_slot
        )
        self.internal_sa_err_sig.connect(
            self.__notify_about_internal_error_slot
        )

    #! ===================================[ GENERATE PROJECT ]=================================== !#
    #! First step in using the SA is to generate a Project()-instance - aka 'engine' - from it.   !#
    #!                                                                                            !#

    def generate_project(self, project_rootpath: str) -> None:
        """Create and store a new Source Analyzer Project()-instance.

        :param project_rootpath: Absolute path to toplevel project folder.
        """
        # Make sure this method runs in the main thread, such that all signals are tied to the slots
        # in the main thread.
        assert threading.current_thread() is threading.main_thread()

        # Project initialization
        self.__cec_project: Project = Project(
            project_rootpath,
            self.linker_status_changed_sig,
            self.project_status_changed_sig,
            self.internal_sa_err_sig,
        )

        data.signal_dispatcher.source_analyzer.start_stop_engine_conditionally_sig.connect(
            self.__start_stop_engine_conditionally
        )
        data.signal_dispatcher.source_analyzer.add_file_sig.connect(
            self.__cec_project.add_file
        )
        data.signal_dispatcher.source_analyzer.remove_file_sig.connect(
            self.__cec_project.remove_file
        )
        data.signal_dispatcher.source_analyzer.set_file_mode_sig.connect(
            self.__cec_project.set_file_mode
        )
        data.signal_dispatcher.source_analyzer.set_hdir_mode_sig.connect(
            self.__cec_project.set_hdir_mode
        )

        data.signal_dispatcher.source_analyzer.project_initialized.emit()

        self.project_generated_sig.emit(
            self.__cec_project,
            self.__cec_project.get_diagnostics(),
            self.__cec_project.get_symbolhandler(),
        )
        return

    def get_completions(
        self,
        path: str,
        pos: int,
        context: List[str],
    ) -> Optional[Tuple[int, List[str]]]:
        """"""
        try:
            if self.has_project():
                return self.__cec_project.get_completions(path, pos, context)
            else:
                return None
        except:
            return None

    def has_project(self) -> bool:
        """Check if a SA Project() was generated and if it still exists."""
        return self.__cec_project is not None

    def abort(self) -> None:
        """Abort queue processing."""
        source_analyzer.abort()
        return

    def get_memory_regions(self):
        try:
            if self.has_project():
                return self.__cec_project.get_memory_regions()
            else:
                return {}
        except:
            return {}

    def get_alternative_content(self, file_abspath_or_obj):
        try:
            if self.has_project():
                return self.__cec_project.get_alternative_content(
                    file_abspath_or_obj
                )
            else:
                return None
        except:
            return None

    def get_file_kind(self, path):
        return self.__cec_project.get_file_kind(path)

    #! =====================================[ START ENGINE ]===================================== !#
    #! After generating and storing the SA Project()-instance - aka 'engine' - it should be       !#
    #! started.                                                                                   !#

    def __start_stop_engine_conditionally(self, *args) -> None:
        """
        Everything okay:
            - Reset 'self.__sa_engine_launch_issue' to None.
            - Refresh build settings(*), but only if they changed.
            - Start engine if off(*).

        Issue(s) found:
            - Overwrite 'self.__sa_engine_launch_issue' to store the issue.
            - Stop engine if on(**).

        (*)  see 'self.__try_start_engine()'
        (**) see 'self.__try_stop_engine()'
        """
        assert data.current_project is not None
        self.__sa_engine_launch_issue = None

        # $ Check existence of SA Project()
        if not self.has_project():
            self.__sa_engine_launch_issue = "Engine off - not yet created"
            data.current_project.trigger_sa_tab_refresh(
                "start_stop_sa_conditionally()"
            )
            return

        # $ Beetle Project() okay
        issue = data.current_project.minimal_sa_requirements_met()
        if issue.lower() == "ok":
            try:
                data.alert_buttons["source-analyzer"].popup_hide()
                self.__try_start_engine()
            except:
                self.__try_stop_engine()
                self.internal_sa_err_sig.emit(
                    "Cannot start Source Code Analyzer"
                )
                data.alert_buttons["source-analyzer"].popup_show(
                    "source analyzer engine\n" "cannot start!"
                )
                self.__sa_engine_launch_issue = (
                    "Cannot start Source Code Analyzer"
                )
                data.current_project.trigger_sa_tab_refresh(
                    "start_stop_sa_conditionally()"
                )
                purefunctions.printc(
                    "\nERROR: Failed to start Source Code Analyzer",
                    color="error",
                )
            return

        # $ Beetle Project() not okay
        self.__try_stop_engine()
        data.alert_buttons["source-analyzer"].popup_show(
            "source analyzer engine\n" "cannot start!"
        )
        self.__sa_engine_launch_issue = issue
        data.current_project.trigger_sa_tab_refresh(
            "start_stop_sa_conditionally()"
        )
        purefunctions.printc(
            "\nWARNING: Cannot start Source Code Analyzer",
            color="warning",
        )
        return

    def __try_start_engine(self) -> None:
        """Refresh the settings for the Source Analyzer (such as the build path,
        the GNU Make settings, ...). Then attempt to start the engine (but only
        if the engine is not yet running).

        NOTE:
        Will only update the build and make settings if they have changed!
        """
        assert threading.current_thread() is threading.main_thread()
        if self.__internal_error:
            self.__try_stop_engine()
            return

        # Refresh build settings
        self.__set_build_path()
        self.__set_make_config()

        # Try to start the engine
        if not self.__engine_on:
            source_analyzer.start()
            self.__engine_on = True
            css = purefunctions.get_dark_css_tags()
            green = css["green"]
            end = css["end"]
            self.__display_message(
                msg=f"<b>{green}start engine{end}</b>",
                indent=0,
            )
            return
        return

    def __try_stop_engine(self) -> None:
        """Attempt to stop the engine (but only if the engine is currently
        running).

        NOTE:
        Won't do anything if the engine is already off.
        """
        assert threading.current_thread() is threading.main_thread()

        # Try to stop the engine
        if self.__engine_on:
            source_analyzer.stop()
            self.__engine_on = False
            css = purefunctions.get_dark_css_tags()
            red = css["red"]
            end = css["end"]
            self.__display_message(
                msg=f"<b>{red}stop engine{end}</b>",
                indent=0,
            )
            return
        return

    def is_engine_on(self) -> bool:
        """"""
        return self.__engine_on

    def get_sa_launch_issues(self) -> Optional[str]:
        """Get a string describing the SA launch issues (which minimal
        requirement is not met).

        If string is None, nothing is wrong.
        """
        return self.__sa_engine_launch_issue

    #! ================================[ ACCESS ENGINE RESULTS ]================================= !#
    #! Access results from the SA Project()-instance (aka 'engine').                              !#
    #!                                                                                            !#

    def get_diagnostics(self) -> Optional[components.diagnostics.Diagnostics]:
        """"""
        if self.__cec_project is None:
            return None
        return self.__cec_project.get_diagnostics()

    def get_symbolhandler(
        self,
    ) -> Optional[components.symbolhandler.SymbolHandler]:
        """"""
        if self.__cec_project is None:
            return None
        return self.__cec_project.get_symbolhandler()

    def find_symbols(self, name: str) -> List[source_analyzer.Symbol]:
        """Get a list of included symbols with a given name.

        :param name: Name of symbols to be returned.
        :return: A list of Python Symbol objects.
        """
        return self.__cec_project.find_symbols(name)

    def get_entity_data(
        self,
        absolute_file_path: str,
        offset: int,
    ) -> Optional[str]:
        """"""
        if self.__cec_project is None:
            print_warning("No project opened to look for a symbol in!")
            return None
        ref: Union[
            source_analyzer.Occurrence,
            source_analyzer.FileOccurrence,
            source_analyzer.SymbolOccurrence,
        ] = self.get_reference(absolute_file_path, offset)
        return self.get_entity_from_reference(ref)

    def get_reference(
        self,
        absolute_file_path: str,
        offset: int,
    ) -> Optional[
        Union[
            source_analyzer.Occurrence,
            source_analyzer.FileOccurrence,
            source_analyzer.SymbolOccurrence,
        ]
    ]:
        """"""
        if self.__cec_project is None:
            print_warning("No project opened to look for a reference in!")
            return None
        return self.__cec_project.find_occurrence(absolute_file_path, offset)

    def get_file_include_locations(self, path):
        if self.__cec_project is None:
            return None
        return self.__cec_project.get_file_include_locations(path)

    def get_entity_from_reference(
        self,
        reference: Optional[
            Union[
                source_analyzer.Occurrence,
                source_analyzer.FileOccurrence,
                source_analyzer.SymbolOccurrence,
            ]
        ],
    ) -> Optional[
        Union[
            str,
            source_analyzer.Symbol,
        ]
    ]:
        """"""
        if not reference:
            return None
        return reference.entity

    def get_corresponding_object_file(self, path: str) -> Optional[str]:
        """For the given source file, return the corresponding object file."""
        if self.__cec_project is None:
            return None
        if path is None:
            return None
        # Ask the SA for the object file location corresponding to the given source file.
        # This still needs to be implemented!
        object_path_location: Optional[str] = None

        # If the SA didn't find the object file, try to find it manually.
        if object_path_location is None:
            object_path_location = path.replace(
                "/source/", "/build/project/source/", 1
            )
            object_path_location += ".o"
            if not os.path.exists(object_path_location):
                object_path_location = None
        return object_path_location

    #! ==================================[ FILE INTERACTIONS ]=================================== !#
    #!                                                                                            !#
    #!                                                                                            !#

    #! CFILES !#

    def cfile_add(
        self,
        file_abspath: str,
        file_mode: int,
        file_python_obj: Any,
    ) -> None:
        """"""
        if self.__cec_project is None:
            purefunctions.printc(
                "ERROR: No SA Project opened to add CFILE to!",
                color="error",
            )
        self.__cec_project.add_file(
            file_abspath,
            file_mode,
            file_python_obj,
        )
        return

    def cfile_remove(
        self,
        file_path: str,
    ) -> None:
        """"""
        if self.__cec_project is None:
            purefunctions.printc(
                "ERROR: No SA Project opened to remove CFILE from!",
                color="error",
            )
        self.__cec_project.remove_file(file_path)
        return

    def status_change_cfile(
        self,
        file_abspath: str,
        state: bool,
        file_python_obj: Any,
    ) -> None:
        """
        I (Kristof) call this function if:
            - A new cfile was found/discovered (it got added to the harddisk).
              The state is None.
            - A manual state-change was invoked by the user.

        :param file_abspath:    Absolute path to the given cfile
        :param state:           State of the cfile (True, False or None)
        :param file_python_obj: [Optional] the File()-instance from the Filetree
        """
        if self.__cec_project is None:
            purefunctions.printc(
                "ERROR: No SA Project opened to change CFILE status in!",
                color="error",
            )
            raise RuntimeError()

        data.filechecker.check_line_endings(file_abspath)
        if state is None:
            file_mode = source_analyzer.file_mode_automatic
        elif state:
            file_mode = source_analyzer.file_mode_include
        else:
            file_mode = source_analyzer.file_mode_exclude
        self.cfile_add(
            file_abspath,
            file_mode,
            file_python_obj,
        )
        return

    def status_change_hdir(
        self,
        folder_abspath: str,
        state: Optional[bool],
        hdir_python_obj: Any,
    ) -> None:
        """"""
        if self.__cec_project is None:
            purefunctions.printc(
                "ERROR: No SA Project opened to change HDIR status in!",
                color="error",
            )
            raise RuntimeError()
        for item in os.listdir(folder_abspath):
            path = functions.unixify_path_join(folder_abspath, item)
            if os.path.isfile(path):
                data.filechecker.check_line_endings(path)

        if state is None:
            hdir_mode = source_analyzer.hdir_mode_automatic
        elif state:
            hdir_mode = source_analyzer.hdir_mode_include
        else:
            hdir_mode = source_analyzer.hdir_mode_exclude
        self.__cec_project.set_hdir_mode(
            folder_abspath,
            hdir_mode,
            hdir_python_obj,
        )
        return

    def hdir_remove(
        self,
        folder_abspath: str,
    ) -> None:
        """"""
        if self.__cec_project is None:
            purefunctions.printc(
                "ERROR: No SA Project opened to set HDIR mode!",
                color="error",
            )
            raise RuntimeError()
        self.__cec_project.set_hdir_mode(
            folder_abspath,
            source_analyzer.hdir_mode_exclude,
            None,
        )
        return

    #! RELOADS !#

    def edit_file(
        self,
        path,
        begin_offset,
        end_offset,
        new_content,
    ) -> None:
        """Called every time an CustomEditor text is edited."""
        if self.__cec_project is None:
            print_warning("No project opened to send a text-change to!")
            return
        self.__cec_project.edit_file(
            path, begin_offset, end_offset, new_content
        )
        return

    def reload_all_files(self) -> None:
        """Reload all files to the SA."""
        assert threading.current_thread() is threading.main_thread()
        self.__cec_project.reload_all()
        return

    def reload_file(self, path: str) -> None:
        """"""
        self.__cec_project.reload_file(path)
        return

    #! ======================================[ SA FEEDBACK ]===================================== !#
    #!                                                                                            !#
    #!                                                                                            !#

    def get_project_status(self) -> int:
        """"""
        return self.__project_status

    def get_linker_status(self) -> int:
        """"""
        return self.__linker_status

    @qt.pyqtSlot(int)
    def __project_status_changed_slot(self, newstate: int) -> None:
        """> project_status_ready = 0 > project_status_busy  = 1 >
        project_status_error = 2.

        project_status_busy  : SA is busy.

        project_status_ready : SA is ready.

        project_status_error : Error in makefile, SA cannot parse other source files.
        """
        # $ 1. Store new state
        assert (newstate == 0) or (newstate == 1) or (newstate == 2)
        self.__project_status = newstate

        # $ 2. Refresh SA Tab
        data.current_project.trigger_sa_tab_refresh(
            "project_status_changed_slot()"
        )

        # $ 3. Print new state to SA Tab
        css = purefunctions.get_dark_css_tags()
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]
        msg = None
        if newstate == 0:
            msg = f"project_status_changed: {green}0 [ready]{end}"
        elif newstate == 1:
            msg = f"project_status_changed: {blue}1 [busy]{end}"
        elif newstate == 2:
            msg = f"project_status_changed: {red}2 [error]{end}"
        if data.sa_tab is not None:
            data.sa_tab.display_message(msg, 1)

        # $ 4. Show alert bubble if needed, hide otherwise
        if newstate == 2:
            # The SA is blocked. Analysis of one or more files failed, probably
            # because the SA is unable to extract the flags from the makefile.
            if not self.__engine_on:
                # The engine is off. A bubble for this should normally already
                # be shown.
                pass
            else:
                data.alert_buttons["source-analyzer"].popup_show(
                    "source analyzer engine\n" "blocked!"
                )
        else:
            data.alert_buttons["source-analyzer"].popup_hide()
        return

    @qt.pyqtSlot(int)
    def __linker_status_changed_slot(self, newstate: int) -> None:
        """Provides the status of the internal linker inside the SA.

        > linker_status_waiting = 0
        > linker_status_busy    = 1
        > linker_status_done    = 2
        > linker_status_error   = 3

        linker_status_waiting : Source Analysis is busy, linker will have to run later. The include-
                                status of source files in automatic mode is not yet known.

        linker_status_busy    : All source fils have been analyzed. Linker is now running.

        linker_status_done    : Linker is ready, include-status of source files in automatic mode is
                                up-to-date. There are no undefined or multiply-defined globals.

        linker_status_error   : Linker is ready, include-status of source files in automatic mode is
                                up-to-date. There are some undefined or multiply-defined globals.
        """
        assert (newstate >= 0) and (newstate <= 3)
        self.__linker_status = newstate
        data.current_project.trigger_sa_tab_refresh(
            "linker_status_changed_slot()"
        )
        css = purefunctions.get_dark_css_tags()
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]
        msg = None
        if newstate == 0:
            msg = f"linker_status_changed: {blue}0 [waiting]{end}"
        elif newstate == 1:
            msg = f"linker_status_changed: {blue}1 [busy]{end}"
        elif newstate == 2:
            msg = f"linker_status_changed: {green}2 [done]{end}"
        elif newstate == 3:
            msg = f"linker_status_changed: {red}3 [error]{end}"
        if data.sa_tab is None:
            purefunctions.printc(
                f"\nWARNING: data.sa_tab is None in function "
                f"linker_status_changed_slot()\n",
                color="warning",
            )
        else:
            data.sa_tab.display_message(msg, 1)
        return

    #! ====================================[ HELP FUNCTIONS ]==================================== !#
    #!                                                                                            !#
    #!                                                                                            !#

    def has_internal_error(self) -> bool:
        """"""
        return self.__internal_error

    def __notify_about_internal_error_slot(self, *args, **kwargs) -> None:
        """Notify the SA about an internal error somewhere in Embeetle.

        Once this flag is set, it will shut down the engine and prevent it from
        launching again.
        """
        self.__internal_error = True
        return

    def __display_message(self, msg: str, indent: int) -> None:
        """The SA Tab in Embeetle has a black terminal-alike logging display at
        the bottom.

        Provide a string to be printed there. If it can't be printed
        immediately, it will be stored to print later.
        """
        if data.sa_tab is None:
            # The display is not yet available. Store the message to print it later.
            self.__log_text.append(msg)
        elif len(self.__log_text) > 0:
            # Print first old messages, without indentation.
            data.sa_tab.display_message(
                "\n".join(self.__log_text),
                0,
            )
            self.__log_text = []
            data.sa_tab.display_message(
                msg,
                indent,
            )
        else:
            data.sa_tab.display_message(
                msg,
                indent,
            )
        return

    def __set_build_path(self):
        """Set build directory."""
        treepath_seg = data.current_project.get_treepath_seg()
        build_path = treepath_seg.get_abspath("BUILD_DIR")
        if self.__cec_project is None:
            purefunctions.printc(
                f"\nWARNING: SourceAnalysisCommunicator().__cec_project "
                f"returned {q}None{q}.\n"
                f"Therefore, the function call:\n"
                f"{q}set_build_path(){q}\n"
                f"cannot be applied!\n",
                color="warning",
            )
            return
        if self.__build_path != build_path:
            self.__build_path = build_path
            self.__cec_project.set_build_path(self.__build_path)
            css = purefunctions.get_dark_css_tags()
            tab = css["tab"]
            blue = css["blue"]
            end = css["end"]
            self.__display_message(
                msg=str(
                    f"set build path:<br>"
                    f"{tab}{blue}{q}{self.__build_path}{q}{end}"
                ),
                indent=1,
            )
        else:
            pass
        return

    def __set_make_config(self) -> None:
        """Notify the clang engine that the make command has changed. This can
        be due to changes in:

        - GNU Make
        - Toolchain
        - makefile location
        """
        treepath_seg = data.current_project.get_treepath_seg()
        toolpath_seg = data.current_project.get_toolpath_seg()

        # & 1. Construct command-list
        cmd_list = project.makefile_target_executer.MakefileTargetExecuter().get_make_command_list(
            target=None,
            role="clang",
        )

        # & 2. Construct environment dictionary
        # $ 2.1 gcc binfolder
        gcc_exe = toolpath_seg.get_compiler_abspath()
        if (gcc_exe is None) or (gcc_exe.lower() == "none"):
            gcc_binfolder = "TOOLCHAIN_NOT_FOUND"
        else:
            gcc_binfolder = os.path.dirname(gcc_exe)
            gcc_binfolder = gcc_binfolder.replace("/", os.sep)

        # $ 2.2 make binfolder
        make_exe = toolpath_seg.get_abspath("BUILD_AUTOMATION")
        if (make_exe is None) or (make_exe.lower() == "none"):
            make_binfolder = "MAKE_NOT_FOUND"
        else:
            make_binfolder = os.path.dirname(make_exe)
            make_binfolder = make_binfolder.replace("/", os.sep)

        # $ 2.3 add to environment
        environ_dict = os.environ.copy()
        environ_dict["PATH"] = (
            gcc_binfolder
            + os.pathsep
            + make_binfolder
            + os.pathsep
            + environ_dict["PATH"]
        )

        #! Apply
        if self.__cec_project is None:
            purefunctions.printc(
                f"\nWARNING: SourceAnalysisCommunicator().__cec_project "
                f"returned {q}None{q}.\n"
                f"Therefore, the function call:\n"
                f"{q}set_make_config(){q}\n"
                f"cannot be applied!\n",
                color="warning",
            )
            return
        if (self.__make_config["cmd_list"] != cmd_list) or (
            self.__make_config["environ_dict"] != environ_dict
        ):
            self.__make_config["cmd_list"] = cmd_list
            self.__make_config["environ_dict"] = environ_dict
            self.__cec_project.set_make_config(
                self.__make_config["cmd_list"],
                self.__make_config["environ_dict"],
            )
            css = purefunctions.get_dark_css_tags()
            tab = css["tab"]
            blue = css["blue"]
            end = css["end"]
            n = "\n"
            temp1 = f'[{n}{tab}{tab}{blue}{q}{f"{q}{end}{n}{tab}{tab}{blue}{q}".join(self.__make_config["cmd_list"])}{q}{end}{n}{tab}]'
            temp2 = f"{{{n}{tab}{tab}&#60;local environment vars&#62;{n}{tab}}}"
            self.__display_message(
                msg=str(
                    f"set make config:{n}"
                    f"{tab}cmd_list = {temp1}{n}"
                    f"{tab}environ_dict = {temp2}{n}"
                ),
                indent=1,
            )
        else:
            pass
        return

    def set_number_of_workers(self, n: int) -> None:
        """"""
        source_analyzer.set_number_of_workers(n)
        return

    def get_number_of_workers(self) -> int:
        """"""
        return source_analyzer.get_number_of_workers()

    def check_empty_loop(self, path, offset):
        if self.__cec_project is None:
            return None
        return self.__cec_project.find_empty_loop(path, offset)

    def get_definitions(self, symbol_or_entity):
        return (
            symbol_or_entity.definitions
            + symbol_or_entity.weak_definitions
            + symbol_or_entity.tentative_definitions
        )


# ^                                            PROJECT                                             ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class Project(source_analyzer.Project):

    def __init__(
        self,
        project_rootpath: str,
        linker_status_changed_sig: qt.pyqtBoundSignal,
        project_status_changed_sig: qt.pyqtBoundSignal,
        internal_sa_err_sig: qt.pyqtBoundSignal,
    ) -> None:
        """"""
        self.__linker_status_changed_sig: qt.pyqtBoundSignal = (
            linker_status_changed_sig
        )
        self.__project_status_changed_sig: qt.pyqtBoundSignal = (
            project_status_changed_sig
        )
        self.__internal_sa_err_sig: qt.pyqtBoundSignal = internal_sa_err_sig
        super().__init__(
            project_rootpath,
            run_function=functions.subprocess_popen_sync,
            resource_path=data.sys_esa,
            lib_path=data.sys_lib,
        )
        self.__diagnostics = components.diagnostics.Diagnostics(self)
        self.__symbolhandler = components.symbolhandler.SymbolHandler(self)
        self.__memory_region_storage: Dict[str, Dict[str, Union[int, str]]] = {}
        self.__memory_section_storage: Dict[str, Dict[str, str]] = {}
        self.__alternage_content_storage: Dict[str, str] = {}

    def get_diagnostics(self) -> components.diagnostics.Diagnostics:
        """"""
        return self.__diagnostics

    def get_symbolhandler(self) -> components.symbolhandler.SymbolHandler:
        """"""
        return self.__symbolhandler

    def report_linker_status(
        self, status: source_analyzer.LinkerStatus
    ) -> None:
        """
        Callback from SA engine when the linker status changes. The initial status is 'error', be-
        cause initially no main function is defined (before files are added). This method then fires
        the signal:
            'linker_status_changed_sig'

        VALUES:
        =======
        > linker_status_waiting = 0
        > linker_status_busy    = 1
        > linker_status_done    = 2
        > linker_status_error   = 3

        linker_status_waiting : Source Analysis is busy, linker will have to run later. The include-
                                status of source files in automatic mode is not yet known.

        linker_status_busy    : All source fils have been analyzed. Linker is now running.

        linker_status_done    : Linker is ready, include-status of source files in automatic mode is
                                up-to-date. There are no undefined or multiply-defined globals.

        linker_status_error   : Linker is ready, include-status of source files in automatic mode is
                                up-to-date. There are some undefined or multiply-defined globals.
        """
        print_message(
            f"Change project linker status to "
            f"{source_analyzer.linker_status_name(status)}"
        )
        self.__linker_status_changed_sig.emit(status.value)
        return

    def report_project_status(
        self, status: source_analyzer.ProjectStatus
    ) -> None:
        """Callback from SA engine when the project status changes. This method
        then fires the signal: 'project_status_changed_sig'.

        VALUES:
        =======
        > project_status_ready = 0
        > project_status_busy  = 1
        > project_status_error = 2

        project_status_busy  : SA is busy.

        project_status_ready : SA is ready.

        project_status_error : Error in makefile, SA cannot parse other source files.
        """
        print_message(
            f"Change project status to "
            f"{source_analyzer.project_status_name(status)}"
        )
        self.__project_status_changed_sig.emit(status.value)
        return

    def report_hdir_usage(
        self,
        hdir_abspath_or_obj: Union[Any, str],
        used: bool,
    ) -> None:
        """Callback from SA when an hdir changes from being used to unused or
        vice versa.

        The SA as- sumes that all hdirs are initially unused and reports all
        changes.
        """
        # print("report_hdir_usage:", folder_abspath_or_obj, status)
        status = 1 if used else 0
        data.signal_dispatcher.source_analyzer.hdir_inclusion_change_sig.emit(
            hdir_abspath_or_obj, status
        )

        return

    def add_diagnostic(
        self,
        message: str,
        severity: source_analyzer.Severity,
        category: source_analyzer.Category,
        file_abspath_or_obj: Union[Any, str],
        offset: int,
        after: Optional[Diagnostic],
    ) -> Optional[Diagnostic]:
        """Callback from SA to add a diagnostic. The SA assumes that initially,
        there are no diagnos- tics. All changes are reported using callbacks to
        add and remove diagnostics. This 'add_ diagnostic()' callback should
        return a Python object (of any type) that uniquely identifies the
        diagnostic. The call to remove the diagnostic will get this object as a
        parameter.

        Diagnostics are ordered per severity such that handling an earlier
        diagnostic has a chance of also fixing a later diagnostic. 'After' is
        either a previously added diagnostic or None. If it is a previously
        added diagnostic, then the new diagnostic should be inserted after it.
        If it is None, then the new diagnostic should be first.

        :param message: Description for this diagnostic
        :param severity: Enum representing the severity
        :param category: Enum representing the category, e.g. Category.TOOLCHAIN
        :param file_abspath_or_obj: Absolute path to the offending file or a
            File()-instance from the Filetree
        :param offset: Zero-based byte offset of diagnostic location
        :param after: A previously added diagnostic (or None)
        """
        abspath = None
        if file_abspath_or_obj is None:
            abspath = None
        elif isinstance(file_abspath_or_obj, str):
            abspath = file_abspath_or_obj

        diagnostic = Diagnostic(
            message,
            severity,
            abspath,
            offset,
            after,
        )
        # print(f'add diagnostic {diagnostic} after {after}')
        self.__diagnostics.message_add(diagnostic)
        return diagnostic

    def remove_diagnostic(
        self,
        diagnostic: Diagnostic,
    ) -> None:
        """Callback from SA to remove a diagnostic previously added by the
        callback add_diagnostic(). The parameter is the Python object returned
        by that callback.

        :param diagnostic: Previously added Diagnostic()-instance
        """
        print_message(
            f"Remove {source_analyzer.severity_name(diagnostic.severity)}: "
            f"{diagnostic.message} at {q}{diagnostic.path}{q} "
            f"( {diagnostic.offset} )"
        )
        self.__diagnostics.message_remove(diagnostic)
        return

    def add_occurrence(
        self,
        occurrence: Union[
            source_analyzer.Occurrence,
            source_analyzer.FileOccurrence,
            source_analyzer.SymbolOccurrence,
        ],
        scope: Optional[Symbol],
    ) -> Symbol:
        """
        :param occurrence:   Occurrence()-instance, FileOccurrence() or SymbolOccurrence(). See de-
                            finitions in 'source_analyzer.py'.

        :param scope:       Symbol()-instance
        """
        symbol = Symbol(occurrence, scope)
        self.__symbolhandler.symbol_add(symbol)
        return symbol

    def remove_occurrence(
        self,
        symbol: Symbol,
    ) -> None:
        """Callback from source analyzer to remove a tracked occurrence
        previously added by the 'add_ occurrence()' callback. The parameter is
        the Python object returned by that callback.

        :param symbol: Previously tracked Occurrence()-instance
        """
        self.__symbolhandler.symbol_remove(symbol)
        return

    def report_file_link_status(
        self,
        file_abspath_or_obj: Union[Any, str],
        status: int,
    ) -> None:
        """Callback from SA when the link status of a file in this project
        changes.

        Only source files (C/C++/asm/object/archive) can be linked. A source
        file is linked when it is force-included or when it is in automatic mode
        and the source analyzer decides that it should be linked. Linked source
        files are added to filetree.mk.

        :param file_abspath_or_obj: Absolute path to the given file, or a File()
            instance from the Filetree.
        :param status: Zero if file is not linked. Non-zero if file is linked.
        """
        data.signal_dispatcher.source_analyzer.file_linking_change_sig.emit(
            file_abspath_or_obj, 1 if status else 0
        )
        return

    def report_file_inclusion_status(
        self,
        file_abspath_or_obj: Union[Any, str],
        status: int,
    ) -> None:
        """Callback from SA when the inclusion status of a file in this project
        changes.

        A file is included if there is an #include statement for it in a source
        file that is linked (see report_file_link_status),  or if it is
        mentioned on the linker command line, or if it is included implicitly by
        the toolchain. Included files are usually header files,  but can also be
        linker scripts, makefiles, or even source files that are #include'd.
        Although rare,  it is possible that a file is both included and linked.

        :param file_abspath_or_obj: Absolute path to the given file, or a File()
            instance from the Filetree.
        :param status: Zero if file is not included. Non-zero if file is
            included.
        """
        data.signal_dispatcher.source_analyzer.file_inclusion_change_sig.emit(
            file_abspath_or_obj, 1 if status else 0
        )
        return

    def report_file_utf8_valid(
        self,
        file_abspath_or_obj: Union[Any, str],
        valid: bool,
    ) -> None:
        """Callback from SA when the UTF-8 status of a file in this project
        changes.

        Non-UTF-8 characters are detected while analyzing any file. When a non-
        UTF-8 character is detected, this callback is called with valid=False.
        When the file is analyzed again and no non-UTF-8 characters are detected
        anymore, this callback is called again with valid=True.

        :param file_abspath_or_obj: Absolute path to the given file, or a File()
            instance from the Filetree.
        :param valid: True iff the file contains only valid UTF-8 characters.
        """
        print(f"UTF8 valid={valid} for {file_abspath_or_obj}")
        pass

    def report_progress(
        self,
        current: int,
        total: int,
    ) -> None:
        """Callback when the analysis progress of the project changes. Progress
        is 'current/total* 100%'. When 'current' is equal to 'total', 'current'
        and 'total' will be automatically reset before the next call.

        :param current: Number of files analyzed
        :param total: Total number of files to be analyzed
        """
        data.signal_dispatcher.source_analyzer.progress_report.emit(
            current, total
        )
        return

    def report_file_analysis_status(
        self,
        file_abspath_or_obj: Union[Any, str],
        status: source_analyzer.AnalysisStatus,
    ) -> None:
        """Callback from SA when the analysis status of a file in this project
        changes.

        :param file_abspath_or_obj: Absolute path to the given file, or a File() instance from the
                                    Filetree.

        :param status:              Enum representing the analysis status.

        VALUES:
        =======
        > analysis_status_none = 0    # Analysis not required
        > analysis_status_waiting = 1 # Analysis scheduled
        > analysis_status_busy = 2    # Analysis in progress
        > analysis_status_done = 3    # Analysis done
        > analysis_status_failed = 4  # Blocking error

        About the blocking error:
        -------------------------
        Analysis failed (file is unreadable or does not exist, analysis crashed, flag extraction
        failed). Note: an analysis that detects errors did not fail, it only fails when it cannot
        analyze the source files due to one of the above reasons.
        """
        data.signal_dispatcher.source_analyzer.file_analysis_change_sig.emit(
            file_abspath_or_obj, status.value
        )
        return

    def report_more_diagnostics(
        self,
        severity: source_analyzer.Severity,
        count: int,
    ) -> None:
        """"""
        self.__diagnostics.more_available_callback(severity.value, count)
        return

    def report_compilation_settings(
        self,
        file_abspath_or_obj: Union[Any, str],
        compiler: str,
        flags: List[str],
    ) -> None:
        """Callback to report compilation settings extracted from makefile.

        Called for source files - not header files - every time the compilation configuration for
        that file is successfully extracted.

        :param file_abspath_or_obj: The path of the source file

        :param compiler:            The compiler path

        :param flags:               A list of strings representing user flags for the compiler
        """
        pass

    def report_internal_error(self, message: str) -> None:
        """Callback called when an internal error occurs in the source analyzer.

        When this callback is called, the source analyzer will no longer work
        and cannot recover. It is advisable to save all edits and restart
        Embeetle.
        """
        print("FATAL: internal error - save changes and restart Embeetle")
        print(f"Details: {message}")
        self.__internal_sa_err_sig.emit(message)
        return

    def add_target(self, target: str) -> None:
        """Callback to report a new target found in the makefile.

        :param target: The name of the new target
        """
        return

    def remove_target(self, target: str) -> None:
        """Callback to report that a previously added target no longer exists in
        the makefile.

        :param target: The name of the removed target
        """
        pass

    def set_memory_region(
        self,
        name: str,
        present: bool,
        origin: int,
        size: int,
        attributes: str = "",  # NEW PARAMETER!
    ) -> None:
        """Callback to report memory regions as found in the linkerscript.

        Called whenever a new memory region is found, a memory region's origin
        or size change, or a memory region is removed. only the first time it is
        extracted and when the version changes.

        :param name: The memory region's name.
        :param present: True when the memory region is added or updated, False
            when it is removed.
        :param origin: Start address of the region; ignore if present is False.
        :param size: Size address of the region in bytes; ignore if present is
            False.
        :param attributes: The regions attributes, such as access rights, as a
            string; currently not used.
        """
        # print(
        #     f'set_memory_region({name.ljust(15)}, '
        #     f'present={str(present).ljust(6)}, '
        #     f'origin={str(origin).ljust(10)}, '
        #     f'size={str(size).ljust(10)}, '
        #     f'attributes={attributes})'
        # )
        if present:
            self.__memory_region_storage[name] = {
                "origin": origin,
                "size": size,
                "access_rights": attributes,
            }
        else:
            self.__memory_region_storage.pop(name, None)
        data.signal_dispatcher.source_analyzer.memory_regions_update.emit(
            self.__memory_region_storage
        )
        return

    def get_memory_regions(self) -> Dict[str, Dict[str, Union[int, str]]]:
        return self.__memory_region_storage

    def set_memory_section(
        self,
        name: str,
        present: bool,
        runtime_region: str,
        load_region: str,
    ) -> None:
        """Callback to report memory section as found in the linkerscript.

        Called whenever a new memory section is found or the region(s) it
        belongs to change.

        :param name: The memory section's name.
        :param runtime_region: The memory region this section belongs to, at
            runtime.
        :param load_region: The memory region this section is stored in.
        """
        #        print(f'set memory section {name} {present} {runtime_region} {load_region}')
        if present:
            self.__memory_section_storage[name] = {
                "runtime_region": runtime_region,
                "load_region": load_region,
            }
        else:
            self.__memory_section_storage.pop(name, None)
        data.signal_dispatcher.source_analyzer.memory_sections_update.emit(
            self.__memory_section_storage
        )
        return

    def get_memory_sections(self) -> Dict[str, Dict[str, str]]:
        return self.__memory_section_storage

    def set_alternative_content(
        self, file_abspath_or_obj: Union[Any, str], content: str
    ):
        """Callback to set alternative content for a binary file (type OBJECT or
        ARCHIVE). When alternative content is set, occurrence offsets refer to
        the alternative content instead of to the actual file content.

        This function is called when at least one occurrence kind is tracked and
        the content changes. Existing occurrences remain valid after this call,
        unless removed by remove_occurrence.

        :param file_abspath_or_obj: The binary file's abs path or filetree
            File() instance
        :param content: The alternative content of the file
        """
        self.__alternage_content_storage[file_abspath_or_obj] = content
        #        print(f'Set alternative content for {file_abspath_or_obj}: {content[:50]}')
        data.signal_dispatcher.source_analyzer.set_alternate_content.emit(
            file_abspath_or_obj, content
        )

    def get_alternative_content(self, file_abspath_or_obj):
        if file_abspath_or_obj in self.__alternage_content_storage.keys():
            return self.__alternage_content_storage[file_abspath_or_obj]
        else:
            return None


# ^                                              ITEM                                              ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class Item:
    id_counter = 0

    def __init__(self, arg_id=None) -> None:
        """"""
        if arg_id:
            self._id = arg_id
        else:
            self._id = self.generate_id()
        return

    def generate_id(self) -> int:
        """"""
        id_number = Item.id_counter
        Item.id_counter += 1
        return id_number


# ^                                           DIAGNOSTIC                                           ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class Diagnostic(Item):
    def __init__(
        self,
        message: str,
        severity: source_analyzer.Severity,
        path: str,
        offset: int,
        after: Optional[Diagnostic],
        arg_id=None,
    ) -> None:
        """Create a unique Diagnostic()-item to represent an error or warning.

        :param message: Description for this diagnostic
        :param severity: Integer representing the severity
        :param path: Absolute path to the offending file
        :param offset: Offset
        :param after: A previously added diagnostic (or None)
        :param arg_id: ?
        """
        super().__init__(arg_id)
        self.message: str = message
        self.severity: source_analyzer.Severity = severity
        self.path: str = path
        self.offset: int = offset
        self.after: Optional[Diagnostic] = after
        return

    def __str__(self):
        """"""
        return f"{dq}{self.message}{dq}"


# ^                                             SYMBOL                                             ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class Symbol(Item):
    def __init__(
        self,
        symbol_occurrence: source_analyzer.SymbolOccurrence,
        scope,
        arg_id=None,
    ) -> None:
        """
        @MATIC, WHAT ARE THE TYPES OF 'SCOPE' AND 'ARG_ID'?
        :param symbol_occurrence:
        :param scope:
        :param arg_id:
        """
        super().__init__(arg_id)
        self.file = symbol_occurrence.file.path
        self.begin_offset = symbol_occurrence.begin_offset
        self.end_offset = symbol_occurrence.end_offset
        self.scope = scope
        self.name: Optional[str] = None
        self.kind: Optional[int] = None
        self.kind_name: Optional[str] = None
        entity: Symbol = SourceAnalysisCommunicator().get_entity_from_reference(
            symbol_occurrence
        )
        self.name = entity.name
        self.kind = entity.kind
        self.kind_name = entity.kind_name
        return


# ^                                           INITIALIZE                                           ^#
# % ============================================================================================== %#
# % The SA gets initialized partly, along with the progressbar calls. However, the actual creation %#
# % of the engine does not happen here!                                                            %#
# %                                                                                                %#

# Functions for printing messages (MainWindow.Display.repl_display_message). Set functions to the
# standard Python 'print' command as fallback (otherwise my project creation scripts crash).
print_message: Callable[[str], None] = print
print_warning: Callable[[str], None] = print
print_error: Callable[[str], None] = print


def init(
    progress_widget: _progresswidget_.ProgressWidget,
    debug_mode: bool,
) -> SourceAnalysisCommunicator:
    """"""

    # Initialize the SA engine's dynamic library path
    so_path = functions.unixify_path_join(
        data.sys_lib,
        "libsource_analyzer.so",
    )

    # Print debug output from the SA
    def sa_debug_print(*args, file=sys.stdout, color="sa", **kwargs) -> None:
        purefunctions.printc(
            "SA:",
            *args,
            **kwargs,
            file=file,
            color=color,
        )

    source_analyzer.init(so_path, sa_debug_print, debug=debug_mode)
    cpu_count: Optional[int] = os.cpu_count()
    if (cpu_count is None) or (not isinstance(cpu_count, int)):
        source_analyzer.set_number_of_workers(1)
    elif cpu_count < 3:
        source_analyzer.set_number_of_workers(1)
    else:
        # Assign 60% of CPU power to SA
        source_analyzer.set_number_of_workers(int(0.6 * cpu_count))

    #! Starting the engine no longer happens here, but somewhere in the startup procedure of Matic's
    #! new Filetree.
    return SourceAnalysisCommunicator()
