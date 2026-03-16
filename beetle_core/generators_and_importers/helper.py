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

# WARNING
# THIS FILE GETS OFTEN R-SYNCED FROM <BEETLE_CORE> TO <BEETLE_PROJECT_GENERATOR>. ONLY EDIT THIS
# FILE FROM WITHIN THE <BEETLE_CORE> FOLDER. OTHERWISE, YOUR CHANGES GET LOST.
import traceback
from typing import *
import sys
import data, purefunctions, functions
import hardware_api.hardware_api as _hardware_api_

q = "'"


def read_hardware_from_src(src_abspath: str) -> Tuple[str, str, str]:
    """"""
    hardware_dict = purefunctions.load_json_file_with_comments(
        f"{src_abspath}/hardware.json5"
    )
    if hardware_dict is None:
        raise RuntimeError(
            f"Cannot load json file: {q}{src_abspath}/hardware.json5{q}"
        )
    boardname = hardware_dict["board_name"]
    chipname = hardware_dict["chip_name"]
    probename = hardware_dict["probe_name"]
    return boardname, chipname, probename


def print_project_info(
    project_name: str,
    boardname: str,
    chipname: str,
    probename: str,
) -> None:
    """"""
    functions.importer_printfunc(
        f"Import project {q}{project_name}{q}", color="yellow"
    )
    functions.importer_printfunc(f"board_name = ", color="yellow", end="")
    functions.importer_printfunc(boardname)
    functions.importer_printfunc(f"chip_name  = ", color="yellow", end="")
    functions.importer_printfunc(chipname)
    functions.importer_printfunc(f"probe_name = ", color="yellow", end="")
    functions.importer_printfunc(probename)
    return


def skip_project(boardname: str, chipname: str) -> bool:
    """"""
    # Not all hardware is activated in the database
    try:
        boardname = _hardware_api_.HardwareDB().standardize_board_name(
            boardname
        )
        chipname = _hardware_api_.HardwareDB().standardize_chip_name(chipname)
    except:
        functions.importer_printfunc(
            f"Import success: ", color="yellow", end=""
        )
        functions.importer_printfunc(f"skipped", color="blue", bright=True)
        functions.importer_printfunc("")
        return True
    if (boardname is None) or (chipname is None):
        functions.importer_printfunc(
            f"Import success: ", color="yellow", end=""
        )
        functions.importer_printfunc(f"skipped", color="blue", bright=True)
        functions.importer_printfunc("")
        return True
    return False


def import_project(
    manufacturer: str,
    src_abspath: str,
    dst_abspath: str,
    boardname: Optional[str] = None,
    chipname: Optional[str] = None,
    probename: Optional[str] = None,
) -> None:
    """Hardware names must be given for all manufacturers, except stmicro."""
    functions.importer_printfunc(f"Import success: ", color="yellow", end="")
    try:
        if manufacturer == "stmicro":
            argv = [
                "--manufacturer",
                manufacturer,
                "--src",
                src_abspath,
                "--dst",
                dst_abspath,
            ]
            assert boardname is None
            assert chipname is None
            assert probename is None
        else:
            argv = [
                "--manufacturer",
                manufacturer,
                "--src",
                src_abspath,
                "--dst",
                dst_abspath,
                "--board",
                boardname,
                "--chip",
                chipname,
                "--probe",
                probename,
            ]
            assert boardname is not None
            assert chipname is not None
            assert probename is not None

        wait_func = purefunctions.spawn_new_terminal(
            script_or_exe_path=f"{data.beetle_project_generator_folder}/importer.py",
            argv=argv,
        )
        result = wait_func()
    except:
        traceback.print_exc()
        functions.importer_printfunc(f"false", color="red")
        functions.importer_printfunc("")
        functions.fail_exit(f"\nFailed to import project {q}{src_abspath}{q}\n")
        return
    if result == 0:
        functions.importer_printfunc(f"true", color="green")
        functions.importer_printfunc("")
        return
    functions.importer_printfunc(f"false", color="red")
    functions.importer_printfunc("")
    functions.fail_exit(f"\nFailed to import project {q}{src_abspath}{q}\n")
    return
