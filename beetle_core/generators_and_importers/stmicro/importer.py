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
import os, re, traceback
import purefunctions, functions, filefunctions
import fnmatch as _fn_
import beetlifyer as _beetlifyer_
import hardware_api.hardware_api as _hardware_api_
import hardware_api.chip_unicum as _chip_unicum_
import hardware_api.board_unicum as _board_unicum_
import hardware_api.probe_unicum as _probe_unicum_
from various.kristofstuff import *


def import_cubemx_project(
    src_abspath: str,
    dst_abspath: str,
    convert_line_endings: bool = True,
    convert_encoding: bool = True,
) -> bool:
    """If this function runs for a sample project, the 'src_abspath' will be the
    temporary directory created by the cubemx project generator function."""
    # & Extract hardware data
    # $ Find '.ioc' file and/or 'hardware.json5'
    ioc_abspath: Optional[str] = None
    hardware_json5: Optional[str] = None
    for dirpath, dirs, files in os.walk(src_abspath):
        # Skip the `.git` directory
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f.endswith(".ioc"):
                ioc_abspath = f"{dirpath}/{f}"
                break
            continue
        if ioc_abspath is not None:
            break
        continue
    for dirpath, dirs, files in os.walk(src_abspath):
        # Skip the `.git` directory
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f == "hardware.json5":
                hardware_json5 = f"{dirpath}/{f}"
                break
            continue
        if hardware_json5 is not None:
            break
        continue
    # $ Extract data
    board_unicum: Optional[_board_unicum_.BOARD] = None
    chip_unicum: Optional[_chip_unicum_.CHIP] = None
    probe_unicum: Optional[_probe_unicum_.PROBE] = None
    if hardware_json5 is not None:
        hardware_dict = purefunctions.load_json_file_with_comments(
            hardware_json5
        )
        board_unicum = _board_unicum_.BOARD(hardware_dict["board_name"])
        chip_unicum = _chip_unicum_.CHIP(hardware_dict["chip_name"])
        probe_unicum = _probe_unicum_.PROBE(hardware_dict["probe_name"])
    elif ioc_abspath is not None:
        try:
            board_unicum, chip_unicum, probe_unicum = (
                extract_data_from_ioc_file(ioc_abspath)
            )
            functions.importer_printfunc(
                f"board = {q}{board_unicum.get_name()}{q}\n"
                f"chip  = {q}{chip_unicum.get_name()}{q}\n"
                f"probe = {q}{probe_unicum.get_name()}{q}\n"
            )
        except:
            functions.importer_printfunc(
                f"{traceback.format_exc()}\n",
                color="error",
            )
            functions.importer_printfunc(
                f"ERROR: The board, microcontroller and probe could not be defined from this .ioc file:\n"
                f"{q}{ioc_abspath}{q}\n"
                f"Most probably it{q}s a board or microcontroller that is not yet supported in Embeetle.\n",
                color="error",
            )
            input("Press any key to continue...")
            raise RuntimeError()
    else:
        functions.importer_printfunc(
            f"ERROR: The .ioc file for this CubeMX project could not be found. Therefore, Embeetle\n"
            f"cannot determine which board or microcontroller this project is based on.\n",
            color="error",
        )
        input("Press any key to continue...")
        raise RuntimeError()

    # & Beetlify the project
    _beetlifyer_.beetlify_project(
        src_abspath=src_abspath,
        dst_abspath=dst_abspath,
        boardname=board_unicum.get_name(),
        chipname=chip_unicum.get_name(),
        probename=probe_unicum.get_name(),
    )

    # & Move stuff to 'template/' folder
    __move_to_template_folder(
        board_unicum=board_unicum,
        chip_unicum=chip_unicum,
        probe_unicum=probe_unicum,
        proj_rootpath=dst_abspath,
    )
    return True


def __move_to_template_folder(
    board_unicum: _board_unicum_.BOARD,
    chip_unicum: _chip_unicum_.CHIP,
    probe_unicum: _probe_unicum_.PROBE,
    proj_rootpath: str,
) -> None:
    """"""
    template_folderpath = f"{proj_rootpath}/template"
    source_folderpath = f"{proj_rootpath}/source"
    if not os.path.isdir(template_folderpath):
        filefunctions.makedirs(
            template_folderpath, printfunc=functions.importer_printfunc
        )

    # & Create 'notok_list'
    # We'll use this list to match file- and foldernames that should be moved to the 'template/'
    # folder.
    # $ Initialize the 'notok_list'
    # I recently modified something in the code that processes this 'notok_list', such that LVGL
    # stuff is not affected by this.
    notok_list = [
        "*template*",
        "*example*",
        "*test*",  # General
        "*heap_1.c",
        "*heap_2.c",
        "*heap_3.c",
        "*heap_5.c",  # FreeRTOS
        "*cmsis_armcc.h",
        "*cmsis_armcc_v6.h",  # non-GCC compilers
        "*cmsis_armclang.h",
        "*cmsis_iccarm.h",  # non-GCC compilers
        "*drivers/cmsis/core*",
        "*drivers/cmsis/core_a*",
        "*drivers/cmsis/lib/arm*",
        "*drivers/cmsis/lib/iar*",
        "*drivers/cmsis/rtos*",
        "*drivers/cmsis/rtos2*",
        "*drivers/cmsis/dsp*",
        "*drivers/cmsis/nn*",
        "*drivers/cmsis/dap*",
    ]
    # $ Add incompatible families
    incompatible_familynames = []
    chip_dict = chip_unicum.get_chip_dict(board=board_unicum.get_name())
    chipfam_name = chip_dict["chipfamily"]
    if chipfam_name.lower() != "custom":
        for name in _hardware_api_.HardwareDB().list_chipfamilies(
            manufacturer_list=[chip_dict["manufacturer"]]
        ):
            if name != chipfam_name:
                incompatible_familynames.append(name)
            continue
    for name in incompatible_familynames:
        notok_list.append(f"*{name}*")
        continue
    # $ Add rejected srcfiles
    rejected_srcfiles = chip_dict["heuristics"]["rejected_srcfiles"]
    rejected_srcfiles = [] if rejected_srcfiles is None else rejected_srcfiles
    notok_list.extend(list(rejected_srcfiles))
    # $ Add rejected hdirs
    rejected_hdirs = chip_dict["heuristics"]["rejected_hdirs"]
    rejected_hdirs = [] if rejected_hdirs is None else rejected_hdirs
    notok_list.extend(list(rejected_hdirs))
    # $ Check 'notok_list'
    for p in notok_list:
        assert p.startswith("*")

    # & Move stuff
    for dirpath, dirs, files in os.walk(source_folderpath):
        dirpath = dirpath.replace("\\", "/")
        dirpath_rel = dirpath.replace(source_folderpath, "", 1)
        dirname = dirpath.split("/")[-1]
        assert not dirpath.endswith("/")
        if any(
            _fn_.fnmatch(name=dirpath_rel.lower(), pat=p.lower())
            for p in notok_list
        ) or (not __is_compatible(chip_unicum, dirname)):
            if "lvgl" in dirpath_rel.lower():
                pass
            else:
                filefunctions.move(
                    src=dirpath,
                    dst=dirpath.replace(
                        source_folderpath, template_folderpath, 1
                    ),
                    printfunc=functions.importer_printfunc,
                )
            dirs[:] = []  # Prevent os.walk to go further in this branch.
            continue
        for f in files:
            if any(
                _fn_.fnmatch(name=f.lower(), pat=p.lower()) for p in notok_list
            ) or (not __is_compatible(chip_unicum, f)):
                filepath = f"{dirpath}/{f}"
                filepath_rel = f"{dirpath_rel}/{f}"
                if "lvgl" in filepath_rel.lower():
                    pass
                else:
                    filefunctions.move(
                        src=filepath,
                        dst=filepath.replace(
                            source_folderpath, template_folderpath, 1
                        ),
                        printfunc=functions.importer_printfunc,
                    )
            continue
        continue
    return


def __is_compatible(chip_unicum: _chip_unicum_.CHIP, item_name: str) -> bool:
    """"""
    if chip_unicum.get_name().lower() == "custom":
        functions.importer_printfunc(
            f"ERROR: Importer running with chip {q}custom{q}!",
            color="error",
        )
        return False
    item_name = item_name.lower()

    # & Define special part
    # If the given 'item_name' is special (it represents a certain chip family or core), then the
    # variable 'specpart' must become a stripped version of 'item_name' representing that special
    # part. Else, the variable 'specpart' must remain None.
    specpart: Optional[str] = None

    # $ 1. Family name
    # Loop over all the chip families, and check if any of them is mentioned in the given
    # 'item_name'.
    for chipfam_name in _hardware_api_.HardwareDB().list_chipfamilies(
        manufacturer_list=[
            "stmicro",
        ]
    ):
        p = re.compile(chipfam_name + r"[a-z|0-9]*")
        m = p.search(item_name)
        if m is not None:
            specpart = m.group(0)
            break
        continue

    # $ 2. Core name
    if specpart is None:
        # First make a 'cpu_list' of all the cpu's that are available. Then loop over all these
        # cpu's and check if any of them is mentioned in the given 'item_name'. If so, then that
        # cpu will become the 'specpart'.
        cpu_list = []
        for c_name in _hardware_api_.HardwareDB().list_chips(
            chipmf_list=[
                "stmicro",
            ]
        ):
            c_dict = _hardware_api_.HardwareDB().get_chip_dict(c_name, None)
            mcpu = c_dict["cpu_flags"].get("mcpu")
            if mcpu is None:
                continue
            mcpu = mcpu.lower().replace("cortex-m", "cm")
            cpu_list.append(f"core_{mcpu}")
            continue
        cpu_list.extend(
            [
                "core_cm0",
                "core_cm0plus",
                "core_cm1",
                "core_cm3",
                "core_cm4",
                "core_cm7",
                "core_cm23",
                "core_armv8mbl",
                "core_armv8mml",
                "core_cm33",
                "core_sc000",
                "core_sc300",
            ]
        )
        cpu_list = list(set(cpu_list))
        # Loop through the 'cpu_list' and check if any of them is mentioned in the 'item_name', then
        # fill in the variable 'specpart' if it's the case.
        for cpu in cpu_list:
            p = re.compile(cpu + r"[a-z|0-9]*")
            m = p.search(item_name)
            if m is not None:
                specpart = m.group(0)
                break
            continue

    # & Compare special part
    if specpart is None:
        # The given 'item_name' is not representing any chip family or core. Therefore, it is com-
        # patible with any given chip. Just return True.
        return True
    # The given 'item_name' does have a *special part* at this point. The 'specpart' variable re-
    # presents a chip family name or core that appears in the 'item_name'. Make the necessary com-
    # parisons to decide if the given 'item_name' and chip are compatible.

    # $ 1. Core name
    cpu_flags_dict = chip_unicum.get_chip_dict(board=None)["cpu_flags"]
    mcpu = cpu_flags_dict.get("mcpu", None)
    if mcpu is None:
        return True
    cpu = f'core_{mcpu.lower().replace("cortex-m", "cm")}'
    if cpu == specpart:
        return True
    if "stm32f1" in chip_unicum.get_name().lower() and "core_cm1" in specpart:
        return True

    # $ 2. Chipname
    chipname = chip_unicum.get_name().lower()
    # Exceptions
    if ("stm32f429zi" in chipname) and ("stm32f429i" in specpart):
        return True
    if ("stm32f103c8" in chipname) and ("stm32f103xb" in specpart):
        return True
    success = True
    for i in range(len(chipname)):
        try:
            if chipname[i] == specpart[i]:
                pass
            elif (chipname[i] == "x") or (specpart[i] == "x"):
                pass
            else:
                success = False
        except:
            pass
    return success


def extract_data_from_ioc_file(
    ioc_abspath: str,
) -> Tuple[_board_unicum_.BOARD, _chip_unicum_.CHIP, _probe_unicum_.PROBE]:
    """Determine the BOARD(), CHIP() and PROBE() unicums based on the given .ioc
    file.

    ERROR:
    Throws RuntimeError() if the chip and board cannot be determined from this IOC file - either
    because the IOC file is corrupted (regexes don't work) or because the found chip and board
    names are unknown to the Embeetle hardware database.
    """
    assert os.path.isfile(ioc_abspath)
    ioc_abspath = find_original_ioc_file(ioc_abspath)
    content: Optional[str] = None
    with open(ioc_abspath, "r", encoding="utf-8", newline="\n") as f:
        content = f.read().lower()

    # $ Prepare results
    chip_unicum: Optional[_chip_unicum_.CHIP] = None
    board_unicum: Optional[_board_unicum_.BOARD] = None
    probe_unicum: Optional[_probe_unicum_.PROBE] = None
    boardfam_unicum: Optional[_board_unicum_.BOARDFAMILY] = None

    # & Find CHIP()
    found_chip_names: List[str] = []
    patterns: Tuple[Pattern[AnyStr], ...] = (
        re.compile(r"(deviceid)\s*=\s*(.*)"),
        re.compile(r"(mcu.username)\s*=\s*(.*)"),
        re.compile(r"(pcc.partnumber)\s*=\s*(.*)"),
    )
    for p in patterns:
        for m in p.finditer(content):
            try:
                name = m.group(2).strip(" \"'").lower()
            except:
                continue
            found_chip_names.append(name)
            continue
        continue
    for name in found_chip_names:
        try:
            chip_unicum = _chip_unicum_.CHIP(name)
            break
        except:
            pass
        continue
    if chip_unicum is None:
        raise RuntimeError(f"Cannot find chip in {q}{ioc_abspath}{q}")

    # & Find BOARD()
    # $ First try to find the board directly from the .ioc file
    found_board_names: List[str] = []
    patterns: Tuple[Pattern[AnyStr], ...] = (re.compile(r"(board)\s*=\s*(.*)"),)
    for p in patterns:
        for m in p.finditer(content):
            try:
                name = m.group(2).strip(" \"'").lower()
            except:
                continue
            found_board_names.append(name)
            continue
        continue
    for name in found_board_names:
        try:
            board_unicum = _board_unicum_.BOARD(name)
            break
        except:
            pass
        continue
    if board_unicum is None:
        # $ Try to derive the board from the chip
        boardfam_name = "custom"
        keywords = ("custom", "nucleo", "disco", "eval", "beetle")
        for name in found_board_names:
            for k in keywords:
                if k in name:
                    boardfam_name = k
                    break
            else:
                continue
            break
        boardfam_unicum = _board_unicum_.BOARDFAMILY(boardfam_name)
        board_unicum_list: List[
            _board_unicum_.BOARD
        ] = _hardware_api_.HardwareDB().list_boards(
            boardfam_list=[
                boardfam_unicum.get_name(),
            ],
            chip_list=[
                chip_unicum.get_name(),
            ],
            return_unicums=True,
        )
        board_unicum = board_unicum_list[0]
    if board_unicum is None:
        raise RuntimeError(f"Cannot find board in {q}{ioc_abspath}{q}")

    # & Find PROBE()
    probe_unicum = _probe_unicum_.PROBE("stlink-v2")
    if any(
        p in board_unicum.get_name().lower()
        for p in ("nucleo", "disco", "eval")
    ):
        probe_unicum = _probe_unicum_.PROBE("stlink-v2-1")
    if probe_unicum is None:
        raise RuntimeError(f"Cannot find probe in {q}{ioc_abspath}{q}")

    # Return result
    return board_unicum, chip_unicum, probe_unicum


def find_original_ioc_file(ioc_abspath: str) -> str:
    """The original '.ioc' file should be in the sample project, stored as
    'cubemx.ioc'.

    It can contain the actual '.ioc' code, or it can contain a pointer to the
    file in the CubeMX database.
    """
    ioc_abspath = ioc_abspath.replace("\\", "/")
    assert os.path.isfile(ioc_abspath)
    cubemx_executable_path: str = __get_cubemx_abspath()
    if cubemx_executable_path is None:
        return ioc_abspath
    cubemx_installation_path: str = os.path.dirname(
        cubemx_executable_path
    ).replace("\\", "/")
    boardmanager_path: str = (
        f"{cubemx_installation_path}/db/plugins/boardmanager/boards"
    )
    with open(
        ioc_abspath, "r", encoding="utf-8", newline="\n", errors="replace"
    ) as f:
        ioc_content = f.read()
    first_line = ioc_content.splitlines()[0]
    if first_line.endswith(".ioc"):
        # It's a pointer to a '.ioc' file in the CubeMX database
        return f"{boardmanager_path}/{first_line}"
    if "autodetect" in first_line:
        # It's a sign that the '.ioc' file must be determined automatically
        boardname: Optional[str] = None
        p = re.compile(r"nucleo-\w*")
        m = p.search(ioc_abspath)
        if m:
            boardname = m.group(0)
        else:
            p = re.compile(r"\w*-disco")
            m = p.search(ioc_abspath)
            if m:
                boardname = m.group(0)
            else:
                raise RuntimeError()
        assert boardname
        candidates = []
        for name in os.listdir(boardmanager_path):
            if not name.endswith(".ioc"):
                continue
            if ("nucleo" in boardname) and ("nucleo" not in name.lower()):
                continue
            if ("disco" in boardname) and ("disco" not in name.lower()):
                continue
            shortname = (
                boardname.replace("nucleo", "")
                .replace("disco", "")
                .replace("-", "")
            )
            if shortname not in name.lower():
                continue
            if "allconfig" not in name.lower():
                continue
            candidates.append(name)
            continue
        if len(candidates) == 0:
            raise RuntimeError(f"No '.ioc' file found for '{ioc_abspath}'")
        if len(candidates) == 1:
            print(f"Choose IOC file: '{candidates[0]}'")
            return f"{boardmanager_path}/{candidates[0]}"
        print(f"WARNING: Not sure which candidate to choose: {candidates}")
        print(f"Choose IOC file: '{candidates[0]}'")
        return f"{boardmanager_path}/{candidates[0]}"
    # It's the actual '.ioc' file
    return ioc_abspath


def __get_cubemx_abspath() -> Optional[str]:
    """Return path to CubeMX executable."""
    if os.path.isfile(
        "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    ):
        return "C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    if os.path.isfile(
        "C:/Program Files (x86)/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    ):
        return "C:/Program Files (x86)/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe"
    return None
