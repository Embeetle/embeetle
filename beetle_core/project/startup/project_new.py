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
import qt, data, functions
import project.project as _project_
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
import toolmanager.toolmanager as _toolman_
import toolmanager.version_extractor as _toolman_v_
import project.startup.project_report as _project_report_

# ^                                     CREATE DEFAULT PROJECT                                     ^#
# % ============================================================================================== %#
# % Create a default Project()-instance from Unicum()s.                                            %#
# %                                                                                                %#


def create_default_project(
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

    Only used in project generators and importers!
    """
    if makefile_interface_version == "latest":
        makefile_interface_version = (
            functions.get_latest_makefile_interface_version()
        )
    projObj: Optional[_project_.Project] = None
    report = _project_report_.create_default_project_report()

    def start(*args) -> None:
        __create_default_segments(
            chip_unicum=chip_unicum,
            board_unicum=board_unicum,
            probe_unicum=probe_unicum,
            version_nr=makefile_interface_version,
            rootpath=rootpath,
            callback=create_projObj,
        )
        return

    def create_projObj(seg_dict: Dict[str, Any], *args) -> None:
        nonlocal projObj
        projObj = _project_.Project(
            proj_rootpath=rootpath,
            with_engine=with_engine,
        )
        projObj.fill_project(
            chip=seg_dict["chip"],
            lib_seg=seg_dict["lib_seg"],
            version_seg=seg_dict["version_seg"],
            board=seg_dict["board"],
            probe=seg_dict["probe"],
            treepath_seg=seg_dict["treepath_seg"],
            toolpath_seg=seg_dict["toolpath_seg"],
        )
        update_project()
        return

    def update_project(*args) -> None:
        "Update states in Project()-instance"
        # NOTE 1:
        # Showing on the dashboard doesn't happen here yet. That's for the 'projObj.show_on_
        # dashboard()' method, invoked by Matic.
        # NOTE 2:
        # The 'report' passed to this update function will not be completely filled. The 'toolpath_
        # report' section has most of its elements filled in the 'load()' function from 'toolpath_
        # seg.py', not in the method 'update_states()'. Anyhow, we don't actually use the report
        # here.
        projObj.update_all_states_with_report(
            project_report=report,
            delete_nonexisting_paths=False,
            callback=finish,
            callbackArg=projObj,
        )
        return

    def finish(*args) -> None:
        callback(projObj, callbackArg)
        return

    # First create Toolmanager
    if data.toolman is None:
        data.toolversion_extractor = _toolman_v_.VersionExtractor()
        data.toolman = _toolman_.Toolmanager(
            mode="project",
        )
        data.toolman.init_all(
            callback=start,
            callbackArg=None,
        )
        return
    start()
    return


# ^                                    CREATE DEFAULT SEGMENTS                                     ^#
# % ============================================================================================== %#
# % Create a default segments from a few Unicum()s.                                                %#
# %                                                                                                %#


def __create_default_segments(
    chip_unicum: Optional[_chip_unicum_.CHIP],
    board_unicum: Optional[_board_unicum_.BOARD],
    probe_unicum: Optional[_probe_unicum_.PROBE],
    version_nr: Optional[Union[str, int]],
    rootpath: str,
    callback: Optional[Callable],
) -> None:
    """Create default segments, consisting of a Chip(), Board(), LibSeg(),
    Probe(), TreepathSeg() and ToolpathSeg() instances.

    They're packed into a dictionary and returned in the callback.
    """
    origthread: qt.QThread = qt.QThread.currentThread()

    # & Unicums
    if not chip_unicum:
        chip_unicum = _chip_unicum_.CHIP("none")
    if not board_unicum:
        board_unicum = _board_unicum_.BOARD("custom")
    if not probe_unicum:
        probe_unicum = _probe_unicum_.PROBE("none")

    # & Segments
    chip: Optional[_chip_.Chip] = None
    board: Optional[_board_.Board] = None
    probe: Optional[_probe_.Probe] = None
    treepath_seg: Optional[_treepath_seg_.TreepathSeg] = None
    toolpath_seg: Optional[_toolpath_seg_.ToolpathSeg] = None
    lib_seg: Optional[_lib_seg_.LibSeg] = None
    version_seg: Optional[_version_seg_.VersionSeg] = None

    # & Define
    assert data.toolman is not None
    chip = _chip_.Chip.create_default_Chip(chip_unicum)
    lib_seg = _lib_seg_.LibSeg.create_default_LibSeg()
    version_seg = _version_seg_.VersionSeg.create_default_Version(version_nr)
    board = _board_.Board.create_default_Board(board_unicum)
    probe = _probe_.Probe.create_default_Probe(probe_unicum)
    treepath_seg = _treepath_seg_.TreepathSeg.create_default_TreepathSeg(
        rootpath
    )
    toolpath_seg = _toolpath_seg_.ToolpathSeg.create_default_ToolpathSeg(chip)

    chip_dict = chip.get_chip_dict(board=board_unicum.get_name())
    # Extract the paths of the bootloaders, partitions and bootswitches files as they appear in the
    # '<resources>/hardware/' database. Then, extract their names from these paths. Finally, con-
    # struct the relative paths as they will appear in the new project.
    bootloaders = chip_dict["boot"]["bootloaders"]
    partitions = chip_dict["boot"]["partitions"]
    bootswitches = chip_dict["boot"]["bootswitches"]

    default_bootloader_name = "bootloader.hex"
    if (bootloaders is not None) and (len(bootloaders) > 0):
        default_bootloader_name = bootloaders[0].split("/")[-1]
    default_partitions_name = "partitions.csv"
    if (partitions is not None) and (len(partitions) > 0):
        default_partitions_name = partitions[0].split("/")[-1]
    default_bootswitches_name = "bootswitch.bin"
    if (bootswitches is not None) and (len(bootswitches) > 0):
        default_bootswitches_name = bootswitches[0].split("/")[-1]

    default_bootloader_relpath = f"config/bootloaders/{default_bootloader_name}"
    default_partitions_relpath = f"config/partitions/{default_partitions_name}"
    default_bootswitches_relpath = (
        f"config/bootswitches/{default_bootswitches_name}"
    )

    bootloader_treepath_obj = treepath_seg.get_treepathObj("BOOTLOADER_FILE")
    partitions_csv_treepath_obj = treepath_seg.get_treepathObj(
        "PARTITIONS_CSV_FILE"
    )
    bootswitch_treepath_obj = treepath_seg.get_treepathObj("BOOTSWITCH_FILE")

    bootloader_treepath_obj.set_doublepath(
        (
            bootloader_treepath_obj.get_rootid(),
            default_bootloader_relpath,
        )
    )
    partitions_csv_treepath_obj.set_doublepath(
        (
            partitions_csv_treepath_obj.get_rootid(),
            default_partitions_relpath,
        )
    )
    bootswitch_treepath_obj.set_doublepath(
        (
            bootswitch_treepath_obj.get_rootid(),
            default_bootswitches_relpath,
        )
    )
    # & Organize
    seg_dict = {
        "chip": chip,
        "board": board,
        "probe": probe,
        "treepath_seg": treepath_seg,
        "toolpath_seg": toolpath_seg,
        "lib_seg": lib_seg,
        "version_seg": version_seg,
    }
    callback(seg_dict)
    return
