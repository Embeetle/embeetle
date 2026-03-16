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
from __future__ import annotations
from typing import *
import sys, os, argparse
import data, purefunctions, functions

q = "'"
dq = '"'


def __help() -> None:
    """Help message in console."""
    header = (
        "\n"
        + "=" * 80
        + "\n"
        + "|"
        + " " * 24
        + "EMBEETLE PROJECT IMPORTER TOOL"
        + " " * 24
        + "|"
        + "\n"
        + "=" * 80
    )
    functions.importer_printfunc(header, color="yellow")
    functions.importer_printfunc(
        f"This tool can transform a project into an Embeetle project (aka {q}import{q}).\n"
        f"The import procedure is the same for most projects, although it can be a bit\n"
        f"different for {q}stmicro{q} and {q}arduino{q} projects. Therefore, you should pass the\n"
        f"{q}--manufacturer{q} argument for these.\n"
    )
    functions.importer_printfunc("--manufacturer  ", end="", color="yellow")
    functions.importer_printfunc(
        f"Choose: {q}arduino{q}, {q}stmicro{q} or {q}other{q}. Defaults to"
    )
    functions.importer_printfunc("                ", end="")
    functions.importer_printfunc(f"{q}other{q} if not provided.")
    functions.importer_printfunc("")
    functions.importer_printfunc("--src           ", end="", color="yellow")
    functions.importer_printfunc(
        "Provide the absolute path to the orginal project folder."
    )
    functions.importer_printfunc("")
    functions.importer_printfunc("--dst           ", end="", color="yellow")
    functions.importer_printfunc(
        "Provide the absolute path to the target project folder."
    )
    functions.importer_printfunc("                ", end="")
    functions.importer_printfunc(
        "This can be the same as the --src argument, in which"
    )
    functions.importer_printfunc("                ", end="")
    functions.importer_printfunc(
        "case the project will be replaced at its original lo-"
    )
    functions.importer_printfunc("                ", end="")
    functions.importer_printfunc("cation.")
    functions.importer_printfunc("")
    functions.importer_printfunc("--board         ", end="", color="yellow")
    functions.importer_printfunc(
        f"Provide the board{q}s name. Not needed for {q}stmicro{q}."
    )
    functions.importer_printfunc("")
    functions.importer_printfunc("--chip          ", end="", color="yellow")
    functions.importer_printfunc(
        f"Provide the chip{q}s name. Not needed for {q}stmicro{q}."
    )
    functions.importer_printfunc("")
    purefunctions.printc("--probe         ", end="", color="yellow")
    purefunctions.printc(
        f"Provide the probe{q}s name. Not needed for {q}stmicro{q}."
    )
    print("")
    purefunctions.printc(
        f"Example:\n"
        f"python importer.py "
        f'--manufacturer "arduino" '
        f'--src "C:/sample_proj_resources/arduino/projects/arduino/arduino-due-blinky" '
        f'--dst "C:/Users/krist/.embeetle/test" '
        f'--board "arduino-due" '
        f'--chip "atsam3x8e" '
        f'--probe "usb-to-uart-converter"'
    )
    return


def import_project(
    manufacturer: Optional[str],
    src: str,
    dst: str,
    boardname: Optional[str],
    chipname: Optional[str],
    probename: Optional[str],
    convert_line_endings: bool = True,
    convert_encoding: bool = True,
) -> bool:
    """
    :param manufacturer: [Optional] Choose: 'arduino', 'stmicro' or 'other'. Defaults to 'other' if
                         not provided.

    :param src:          Provide the absolute path to the orginal project folder.

    :param dst:          Provide the absolute path to the target project folder. This can be the
                         same as the --src argument, in which case the project will be replaced at
                         its original location.

    :param boardname:    [Optional] Provide the board's name. Not needed for 'stmicro'.

    :param chipname:     [Optional] Provide the chip's name. Not needed for 'stmicro'.

    :param probename:    [Optional] Provide the probe's name. Not needed for 'stmicro'.

    :return: success
    """

    def remove_quotes(arg: Optional[str]) -> Optional[str]:
        if arg is None:
            return arg
        return arg.replace(q, "").replace(dq, "").strip()

    def invalid_args(msg: Optional[str] = None) -> None:
        if msg is None:
            purefunctions.printc(
                f"ERROR: Some arguments are invalid or missing!", color="error"
            )
        else:
            purefunctions.printc(f"ERROR: {msg}", color="error")
        __help()
        print("")
        input("Press any key to quit...")
        sys.exit(0)
        return

    # & Validity check
    remove_quotes(manufacturer)
    remove_quotes(src)
    remove_quotes(dst)
    remove_quotes(boardname)
    remove_quotes(chipname)
    remove_quotes(probename)
    if (src is None) or (dst is None):
        invalid_args()
        return False
    if not os.path.exists(src):
        invalid_args(f"Cannot find --src project: {q}{src}{q}")
        return False
    if manufacturer is None:
        manufacturer = "other"
    if manufacturer.lower() != "stmicro":
        # Hardware names must be given for all manufacturers, except stmicro
        if (boardname is None) or (chipname is None) or (probename is None):
            invalid_args()
            return False

    # & Do the import
    # $ STMicro
    if manufacturer.lower() == "stmicro":
        import generators_and_importers.stmicro.importer as _stmicro_importer_

        return _stmicro_importer_.import_cubemx_project(
            src_abspath=src,
            dst_abspath=dst,
            convert_line_endings=convert_line_endings,
            convert_encoding=convert_encoding,
        )
    # $ Arduino
    if manufacturer.lower() == "arduino":
        import generators_and_importers.arduino.importer as _arduino_importer_

        return _arduino_importer_.import_arduino_project(
            arduinosketch_filepath=src,
            dst_abspath=dst,
            boardname=boardname,
            chipname=chipname,
            probename=probename,
            convert_line_endings=convert_line_endings,
            convert_encoding=convert_encoding,
        )
    # $ Other
    import beetlifyer as _beetlifyer_

    return _beetlifyer_.beetlify_project(
        src_abspath=src,
        dst_abspath=dst,
        boardname=boardname,
        chipname=chipname,
        probename=probename,
        convert_line_endings=convert_line_endings,
        convert_encoding=convert_encoding,
    )


if __name__ == "__main__":
    # & SET LOCAL FOLDERS
    # This script should *never* run from sources. Therefore, it is important to create missing
    # folders in a user's installation.
    local_paths = functions.get_local_paths(create_if_not_found=False)
    data.beetle_core_directory = local_paths["beetle_core_directory"]
    data.beetle_tools_directory = local_paths["beetle_tools_directory"]
    data.beetle_project_generator_folder = local_paths[
        "beetle_project_generator_folder"
    ]
    data.beetle_licenses_directory = local_paths["beetle_licenses_directory"]
    data.sys_directory = local_paths["sys_directory"]
    data.sys_bin = local_paths["sys_bin"]
    data.sys_lib = local_paths["sys_lib"]
    data.local_keypath = local_paths["local_keypath"]
    data.resources_directory = local_paths["resources_directory"]
    data.embeetle_toplevel_folder = local_paths["embeetle_toplevel_folder"]
    functions.verify_local_paths()

    # & PARSE ARGUMENTS
    parser = argparse.ArgumentParser(
        description="Import Embeetle project", add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-n", "--new", action="store_true")
    parser.add_argument("--manufacturer", action="store")
    parser.add_argument("--src", action="store")
    parser.add_argument("--dst", action="store")
    parser.add_argument("--board", action="store")
    parser.add_argument("--chip", action="store")
    parser.add_argument("--probe", action="store")
    args = parser.parse_args()
    if args.help:
        __help()
        print("")
        input("Press any key to quit...")
        sys.exit(0)
    if args.new:
        data.new_mode = True

    # & CHECK IF RUNNING FROM SOURCES
    if (
        os.path.exists(
            os.path.join(data.beetle_core_directory, "embeetle.py").replace(
                "\\", "/"
            )
        )
        or os.path.exists(
            os.path.join(data.beetle_core_directory, "data.py").replace(
                "\\", "/"
            )
        )
        or os.path.exists(
            os.path.join(data.beetle_core_directory, "functions.py").replace(
                "\\", "/"
            )
        )
    ):
        data.running_from_sources = True

    # & IMPORT PROJECT
    _manufacturer: Optional[str] = None
    _src: Optional[str] = None
    _dst: Optional[str] = None
    _boardname: Optional[str] = None
    _chipname: Optional[str] = None
    _probename: Optional[str] = None
    try:
        _manufacturer = args.manufacturer
    except:
        pass
    try:
        _src = args.src
        _dst = args.dst
    except:
        pass
    try:
        _boardname = args.board
        _chipname = args.chip
        _probename = args.probe
    except:
        pass
    import_project(
        manufacturer=_manufacturer,
        src=_src,
        dst=_dst,
        boardname=_boardname,
        chipname=_chipname,
        probename=_probename,
    )

    # & EXIT
    # On Linux, the following line crashes:
    #     input('Press any key to quit...')
    # It throws a 'EOFError'.
    sys.exit(0)
