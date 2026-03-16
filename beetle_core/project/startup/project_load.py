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

import traceback
from typing import *
import sys, os
import qt, data
import hardware_api.hardware_api as _hardware_api_
import bpathlib.path_power as _pp_
import project.project as _project_
import project.segments.chip_seg.chip as _chip_
import project.segments.board_seg.board as _board_
import project.segments.probe_seg.probe as _probe_
import project.segments.path_seg.treepath_seg as _treepath_seg_
import project.segments.path_seg.toolpath_seg as _toolpath_seg_
import project.segments.lib_seg.lib_seg as _lib_seg_
import project.segments.version_seg.version_seg as _version_seg_
import toolmanager.toolmanager as _toolman_
import toolmanager.version_extractor as _toolman_v_
import project.startup.project_report as _project_report_
import hardware_api.file_generator as _file_generator_

if TYPE_CHECKING:
    import wizards.intro_wizard.intro_wizard as _wiz_


# ^                                              LOAD                                              ^#
# % ============================================================================================== %#
# % Load the Project()-instance from a given folder.                                               %#
# %                                                                                                %#

# Dictionary storing data about the project, all in string format.
raw_proj_data: Dict[str, Optional[str]] = {}

# Dictionary storing the actual Chip(), Board(), ... instances.
seg_proj_data: Dict[str, Any] = {}

# Report with errors per project segment, used by Intro Wizard to populate itself.
project_report: Dict = {}

# Callback data from the initial load() function.
load_callback: Optional[Callable] = None
load_callbackArg: Any = None


def load_01(
    proj_rootpath: str,
    callback: Optional[Callable],
    callbackArg: Any,
) -> None:
    """Store the callback data and initialize the Toolmanager()."""
    if data.startup_log_project_load:
        print("[startup] project_load.py -> load_01()")
    proj_rootpath = proj_rootpath.replace("\\", "/")

    # $ Create 'build/' subdir if needed
    if not os.path.isdir(f"{proj_rootpath}/build"):
        try:
            os.makedirs(f"{proj_rootpath}/build")
        except:
            traceback.print_exc()
    if not os.path.isfile(f"{proj_rootpath}/build/.build"):
        try:
            with open(
                f"{proj_rootpath}/build/.build",
                "w",
                encoding="utf-8",
                newline="\n",
            ) as f:
                f.write("")
        except:
            traceback.print_exc()

    # $ Initialize hardware database
    # The hardware database initializes itself automatically in its constructor. I also pass
    # potential 'board.json5', 'chip.json5' or 'probe.json5' override files.
    _hardware_api_.HardwareDB().parse_overrides_db(proj_rootpath)

    # $ Store callback data
    global load_callback, load_callbackArg
    load_callback = callback
    load_callbackArg = callbackArg

    # $ Initialize Toolmanager()
    assert data.toolman is None
    data.toolversion_extractor = _toolman_v_.VersionExtractor()
    data.toolman = _toolman_.Toolmanager("project")
    data.toolman.init_all(
        callback=load_02,
        callbackArg=proj_rootpath,
    )
    return


def load_02(
    proj_rootpath: str,
    *args,
) -> None:
    """Create an empty Project()-instance.

    Then extract data from the 'dashboard_config.btl' file and
    store it in 'raw_proj_data'. This dictionary contains NOT the the actual Board(), Chip(), ...
    instances, but strings to help making them.
    """
    if data.startup_log_project_load:
        print("[startup] project_load.py -> load_02()")

    # $ Create Project()-instance
    # Create an empty Project()-instance. It merely contains the project rootpath. The Project()-
    # instance creates an empty 'self.__proj_dict' data structure to contain the Board(), Chip() and
    # other project segments later on.
    assert data.current_project is None
    _project_.Project(
        proj_rootpath=proj_rootpath,
        with_engine=True,
    )
    assert isinstance(data.current_project, _project_.Project)

    # $ Extract project data
    # Dictionary containing NOT the actual Board(), Chip(), ... instances, but strings to help
    # making them.
    global raw_proj_data
    raw_proj_data = _file_generator_.read_dashboard_config(
        f"{proj_rootpath}/.beetle/dashboard_config.btl",
    )
    load_03()
    return


def load_03(*args) -> None:
    """Based on the 'raw_proj_data' dictionary, create the Board(), Chip(), ...
    instances and store them in 'seg_proj_data' for now.

    'project_report':   Report with errors per project segment. Will be used by
    Intro Wizard.
    """
    if data.startup_log_project_load:
        print(f"[startup] project_load.py -> load_03()")
    seg_proj_data["chip"] = None
    seg_proj_data["lib_seg"] = None
    seg_proj_data["version_seg"] = None
    seg_proj_data["board"] = None
    seg_proj_data["probe"] = None
    seg_proj_data["treepath_seg"] = None
    seg_proj_data["toolpath_seg"] = None

    # Keep a report with errors per project segment. It will be used by the Intro Wizard to populate
    # itself later on.
    temp_report = _project_report_.create_default_project_report()
    for key in temp_report.keys():
        project_report[key] = temp_report[key]
    del temp_report

    def create_libseg(prev_obj: _chip_.Chip, *_args) -> None:
        if data.startup_log_project_load:
            print(f"[startup] project_load.py -> load_03().create_lib()")
        seg_proj_data["chip"] = prev_obj
        _lib_seg_.LibSeg.load(
            configcode=raw_proj_data,
            rootpath=data.current_project.get_proj_rootpath(),
            project_report=project_report,
            callback=create_board,
            callbackArg=None,
        )
        return

    def create_board(prev_obj: _lib_seg_.LibSeg, *_args) -> None:
        if data.startup_log_project_load:
            print(f"[startup] project_load.py -> load_03().create_board()")
        seg_proj_data["lib_seg"] = prev_obj
        _board_.Board.load(
            configcode=raw_proj_data,
            project_report=project_report,
            callback=create_probe,
            callbackArg=None,
        )
        return

    def create_probe(prev_obj: _board_.Board, *_args) -> None:
        if data.startup_log_project_load:
            print(f"[startup] project_load.py -> load_03().create_probe()")
        seg_proj_data["board"] = prev_obj
        _probe_.Probe.load(
            configcode=raw_proj_data,
            project_report=project_report,
            callback=create_treepath_seg,
            callbackArg=None,
        )
        return

    def create_treepath_seg(prev_obj: _probe_.Probe, *_args) -> None:
        if data.startup_log_project_load:
            print(
                f"[startup] project_load.py -> load_03().create_treepath_seg()"
            )
        seg_proj_data["probe"] = prev_obj
        _treepath_seg_.TreepathSeg.load(
            configcode=raw_proj_data,
            project_report=project_report,
            callback=create_toolpath_seg,
            callbackArg=None,
        )
        return

    def create_toolpath_seg(
        prev_obj: _treepath_seg_.TreepathSeg, *_args
    ) -> None:
        if data.startup_log_project_load:
            print(
                f"[startup] project_load.py -> load_03().create_toolpath_seg()"
            )
        seg_proj_data["treepath_seg"] = prev_obj
        _toolpath_seg_.ToolpathSeg.load(
            configcode=raw_proj_data,
            beetle_tools_abspath=data.beetle_tools_directory,
            project_report=project_report,
            callback=create_version_seg,
            callbackArg=None,
        )
        return

    def create_version_seg(
        prev_obj: _toolpath_seg_.ToolpathSeg, *_args
    ) -> None:
        if data.startup_log_project_load:
            print(
                f"[startup] project_load.py -> load_03().create_version_seg()"
            )
        seg_proj_data["toolpath_seg"] = prev_obj
        treepath_seg: _treepath_seg_.TreepathSeg = seg_proj_data["treepath_seg"]
        _version_seg_.VersionSeg.load(
            relevant_filepaths={
                "proj_rootpath": data.current_project.get_proj_rootpath(),
                "makefile_abspath": treepath_seg.get_abspath("MAKEFILE"),
                "dashboard_mk_abspath": treepath_seg.get_abspath(
                    "DASHBOARD_MK"
                ),
                "filetree_mk_abspath": treepath_seg.get_abspath("FILETREE_MK"),
            },
            with_engine=True,
            callback=finish,
            callbackArg=None,
        )
        return

    def finish(prev_obj: _version_seg_.VersionSeg, *_args) -> None:
        if data.startup_log_project_load:
            print(f"[startup] project_load.py -> load_03().finish()")
        seg_proj_data["version_seg"] = prev_obj
        load_04()
        return

    # * Create Chip()
    if data.startup_log_project_load:
        print(f"[startup] project_load.py -> load_03().create_chip()")
    _chip_.Chip.load(
        configcode=raw_proj_data,
        rootpath=data.current_project.get_proj_rootpath(),
        project_report=project_report,
        callback=create_libseg,
        callbackArg=None,
    )
    return


def load_04(*args) -> None:
    """Fill the Project()-instance with its segments.

    Also update all states of the Chip(), Board(),
    ... instances with a report.
    """
    if data.startup_log_project_load:
        print(f"[startup] project_load.py -> load_04()")

    data.current_project.fill_project(
        chip=seg_proj_data["chip"],
        lib_seg=seg_proj_data["lib_seg"],
        version_seg=seg_proj_data["version_seg"],
        board=seg_proj_data["board"],
        probe=seg_proj_data["probe"],
        treepath_seg=seg_proj_data["treepath_seg"],
        toolpath_seg=seg_proj_data["toolpath_seg"],
    )

    # & Update states in Project()-instance
    # Note: showing on the dashboard doesn't happen here yet. That's for the method 'projObj.
    # show_on_dashboard()', invoked by Matic.
    data.current_project.update_all_states_with_report(
        project_report=project_report,
        delete_nonexisting_paths=True,
        callback=load_05,
        callbackArg=None,
    )
    return


def load_05(*args) -> None:
    """Initialize the Intro Wizard."""
    if data.startup_log_project_load:
        print("[startup] project_load.py -> load_05()")

    # Skip intro wizard alltogether if this is an automated test.
    if data.source_analysis_only:
        if data.startup_log_project_load:
            print(
                "[startup] project_load.py -> load_05() and load_06() skipped"
            )
        load_07()
        return

    # Create the IntroWizard() and initialize it from the report. The next function will decide if
    # the wizard should be shown or not, and how it will be destroyed eventually.
    assert not data.source_analysis_only
    import wizards.intro_wizard.intro_wizard as _wiz_  # noqa

    data.current_project.intro_wiz = _wiz_.IntroWizard(
        parent=None,
        report=project_report,
        callback=None,
        callbackArg=None,
    )
    data.current_project.intro_wiz.initialize_from_report(
        callback=load_06,
        callbackArg=None,
    )
    return


def load_06(*args) -> None:
    """Show Intro Wizard if needed, then destroy it."""
    if data.startup_log_project_load:
        print("[startup] project_load.py -> load_06()")
    assert not data.source_analysis_only

    # & CASE 1: Errors detected
    # Tie a callback to the intro wizard. It gets invoked after the intro wizard has destroyed it-
    # self. The wizard destroys itself once it completed its purpose (or if it's canceled).
    if data.current_project.intro_wiz.has_err_warn():
        data.current_project.intro_wiz.set_callback(
            callback=load_07,
            callbackArg=None,
        )
        data.current_project.intro_wiz.show()

        def _activate_window_(*_args) -> None:
            if data.current_project.intro_wiz is None:
                return
            if data.current_project.intro_wiz.dead:
                return
            if qt.sip.isdeleted(data.current_project.intro_wiz):
                return
            data.current_project.intro_wiz.activateWindow()
            return

        def _raise_(*_args) -> None:
            if data.current_project.intro_wiz is None:
                return
            if data.current_project.intro_wiz.dead:
                return
            if qt.sip.isdeleted(data.current_project.intro_wiz):
                return
            data.current_project.intro_wiz.raise_()
            return

        qt.QTimer.singleShot(1500, _activate_window_)
        qt.QTimer.singleShot(2000, _raise_)
        return

    # & CASE 2: No errors
    # The intro wizard has been initialized and it checked the project on errors. None were found,
    # so the intro wizard should not be shown. It should be destroyed.
    data.current_project.intro_wiz.self_destruct(
        callback=load_07,
        callbackArg=None,
    )
    return


def load_07(*args) -> None:
    """Finish and return Project()-instance."""
    if data.startup_log_project_load:
        print("[startup] project_load.py -> load_07()")

    # $ Remove intro wizard shell
    # The intro wizard has destroyed itself at this point. However, an empty shell might still be
    # present. Throw it away.
    data.current_project.intro_wiz = None

    # $ Clear globals
    # Clear all the global variables used throughout the load procedure. Just keep the callback in
    # a local variable.
    global raw_proj_data, seg_proj_data, project_report, load_callback, load_callbackArg
    callback: Optional[Callable] = load_callback
    callbackArg: Any = load_callbackArg
    raw_proj_data = None
    seg_proj_data = None
    project_report = None
    load_callback = None
    load_callbackArg = None

    # $ Invoke callback
    if callback is not None:
        callback(
            data.current_project,
            callbackArg,
        )
    return
