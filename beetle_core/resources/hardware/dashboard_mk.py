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
import os, traceback

q = "'"
dq = '"'
bsl = "\\"


def get_dashboard_mk(
    boardname: str,
    board_dict: Dict[str, Any],
    chipname: str,
    chip_dict: Dict[str, Any],
    probename: str,
    probe_dict: Dict[str, Any],
    filepaths: Dict[str, Optional[str]],
    resources_path: str,
    toolprefix: str,
    flashtool_exename: str,
    version: int,
    *args,
    **kwargs,
) -> str:
    """Return the content for 'dashboard.mk'. This file heavily depends on the
    kind of board, chip and probe you're using. Therefore, this function is
    provided not only their names, but also the en- tire dictionaries extracted
    from their respective json-files.

    The 'dashboard.mk' file also needs the paths of certain files - like the '.elf' executable, the
    linkerscript and so forth. Those are provided in the 'filepaths' parameter.

    :param boardname:   Name of the board, eg. 'nucleo-f303k8'
    :param board_dict:  Dictionary extracted from the 'board.json5' file

    :param chipname:    Name of the chip, eg. 'stm32f303k8'
    :param chip_dict:   Dictionary extracted from the 'chip.json5' file and modified by the board
                        file!

    :param probename:   Name of the probe, eg. 'stlink'
    :param probe_dict:  Dictionary extracted from the corresponding json-file

    :param filepaths:   A collection of absolute(!) paths to the files that are needed to build and
                        flash the chip. They are all listed in the Dashboard. For example:
                        filepaths = {
                            'SOURCE_DIR'          : 'C:/Users/krist/my_project',
                            'BUILD_DIR'           : 'C:/Users/krist/my_project/build',
                            'ELF_FILE'            : 'C:/Users/krist/my_project/build/application.elf',
                            'BOOTLOADER_FILE'     : None,
                            'BOOTSWITCH_FILE'     : None,
                            'PARTITIONS_CSV_FILE' : None,
                            'LINKERSCRIPT'        : 'C:/Users/krist/my_project/config/linkerscript.ld',
                            'GDB_FLASHFILE'       : None,
                            'OPENOCD_CHIPFILE'    : 'C:/Users/krist/my_project/config/openocd_chip.cfg',
                            'OPENOCD_PROBEFILE'   : 'C:/Users/krist/my_project/config/openocd_probe.cfg',
                        }

    :param resources_path: Absolute path to the 'beetle_core/resources' folder in the Embeetle in-
                           stallation. This path is important to locate the hardware database where
                           some important files need to be found.

    :param toolprefix:     The toolprefix like 'arm-none-eabi-', 'avr-', ... This depends on the
                           chosen compiler tool in the Dashboard.

    :param flashtool_exename: The flashtool executable name, like 'openocd', 'avrdude',
                              'bossac', ...
                              This depends on the chosen flashtool in the Dashboard.

    :param version:        Each makefile-based project in Embeetle has a makefile-version number.
    """
    content = __get_intro()
    content += __get_version_section(version)
    content += __get_tools_section(toolprefix, flashtool_exename)
    content += __get_project_layout_section(filepaths)
    content += __get_binaries_section(chip_dict, resources_path)
    content += __get_compilation_flags_section(chip_dict, version)
    content += __get_flash_rules_section(
        boardname, chipname, chip_dict, probename, probe_dict, resources_path
    )
    content += __get_addendum()
    return content


def __get_intro() -> str:
    """"""
    return """################################################################################
#                                 DASHBOARD.MK                                 #
################################################################################
# COPYRIGHT (c) 2020 Embeetle                                                  #
# This software component is licensed by Embeetle under the MIT license. Con-  #
# sult the license text at the bottom of this file.                            #
#                                                                              #
#------------------------------------------------------------------------------#
#                                   SUMMARY                                    #
#------------------------------------------------------------------------------#
# This file is intended to be included in the makefile. It contains all        #
# variables that depend on dashboard settings in Embeetle.                     #
#                                                                              #
# We suggest to include this file in your makefile like so:                    #
#                                                                              #
#     MAKEFILE := $(lastword $(MAKEFILE_LIST))                                 #
#     MAKEFILE_DIR := $(dir $(MAKEFILE))                                       #
#     include $(MAKEFILE_DIR)dashboard.mk                                      #
#                                                                              #
#------------------------------------------------------------------------------#
#                                    EDITS                                     #
#------------------------------------------------------------------------------#
# This file was automatically generated, but feel free to edit. When you chan- #
# ge something in the dashboard, Embeetle will ask your permission to modify   #
# this file accordingly. You'll be shown a proposal for a 3-way-merge in a     #
# diffing window. In other words, your manual edits won't be lost.             #
#                                                                              #
#------------------------------------------------------------------------------#
#                               MORE INFORMATION                               #
#------------------------------------------------------------------------------#
# Consult the Embeetle website for more info about this file:                  #
# https://embeetle.com/#embeetle-ide/manual/beetle-anatomy/dashboard           #
#                                                                              #
################################################################################
"""


def __get_version_section(version: int) -> str:
    """"""
    return f"""
# 1. VERSION
# ==========
# Define the makefile interface version this 'dashboard.mk' file must be com-
# patible with.
EMBEETLE_MAKEFILE_INTERFACE_VERSION = {version}
"""


def __get_tools_section(
    toolprefix: str,
    flashtool_exename: str,
) -> str:
    """
    :param toolprefix:         Provide the toolprefix like 'arm-none-eabi-', 'avr-', ...
    :param flashtool_exename:  Provide the flashtool executable name, like 'openocd', 'avrdude',
                               'bossac', ...
    """
    content = """
# 2. TOOLS
# ========
# When invoking the makefile, Embeetle passes absolute paths to the toolchain
# (ARM, RISCV, ...) and the flash tool (OpenOCD, esptool, ...) on the command-
# line.
# Example:
#   > "TOOLPREFIX=C:/my_tools/gnu_arm_toolchain_9.2.1/bin/arm-none-eabi-"
#   > "FLASHTOOL=C:/my_tools/openocd_0.10.0_dev01138_32b/bin/openocd.exe"
# If you ever invoke the makefile without these commandline-arguments,
# you need a fallback mechanism. Therefore, we provide a default value
# for these variables here. Read more about the reasons in ADDENDUM 2.
"""
    # $ TOOLPREFIX
    content += f"TOOLPREFIX = {toolprefix}\n"
    # $ FLASHTOOL
    content += f"FLASHTOOL = {flashtool_exename}\n"
    return content


def __get_project_layout_section(filepaths: Dict[str, Optional[str]]) -> str:
    '''
    Return the PROJECT LAYOUT section for 'dashboard.mk'. This section defines the paths of certain
    files that GNU Make needs to properly execute the build and flash targets. Think about the lo-
    cation of the '.elf'-file, but also the linkerscript, openocd-files, ... Taken together, all
    these files - along with the source files - comprise your project. Hence the term 'PROJECT
    LAYOUT' for this section.

    Because Embeetle always invokes GNU Make from within the '<project>/build/' folder, the paths
    of these files should be defined *relative* to the build-folder.

    Note that Embeetle keeps the locations of each of these files in the Dashboard. So when this
    function gets invoked, the data from the dashboard flows towards this function. All the absolute
    paths of those files will be passed - this function then computes their *relative* paths.

    One special case is the 'SOURCE_DIR' parameter. This is no longer an entry in the Embeetle Dash-
    board. That's because Embeetle always considers the toplevel project folder to be your 'SOURCE_
    DIR'. In other words, the absolute path to the toplevel project directory will be passed for
    this parameter.

    Eventually, this function returns something like (comments omitted for brevity):

    :param filepaths:   Dictionary with absolute(!) filepaths

    """
    # 3. PROJECT LAYOUT
    # =================
    ELF_FILE = application.elf                       # Relative path to the elf-file
    SOURCE_DIR = ../                                 # Relative path to the toplevel project folder
    LINKERSCRIPT = ../config/linkerscript.ld         # Relative path to the linkerscript
    OPENOCD_CHIPFILE = ../config/openocd_chip.cfg    # Relative path to 'openocd_chip.cfg'
    OPENOCD_PROBEFILE = ../config/openocd_probe.cfg  # Relative path to 'openocd_probe.cfg'
    """

    '''
    content = """
# 3. PROJECT LAYOUT
# =================
# The PROJECT LAYOUT section in the dashboard points to all important config
# file locations (eg. linkerscript, openocd config files, ...). If you change
# any of those locations in the dashboard, Embeetle changes the variables be-
# low accordingly.
# NOTES:
#     - These paths are all relative to the build directory.
#     - Locations of 'dashboard.mk' and 'filetree.mk' are not
#       defined here. That's because they're always located in
#       the same folder with the makefile.
"""
    if filepaths.get("BUILD_DIR") is None:
        return f"$(error You forgot to specify the build directory in the Dashboard!)"

    def add_line(_name: str, _abspath: str) -> None:
        nonlocal content
        if (_abspath is None) or (_abspath.lower() == "none"):
            if _name == "SOURCE_DIR":
                content += f"{_name} = ../\n"
            return
        _relpath = os.path.relpath(
            path=_abspath,
            start=filepaths["BUILD_DIR"],
        ).replace("\\", "/")
        if (_name == "SOURCE_DIR") and (not _relpath.endswith("/")):
            _relpath += "/"
        content += f"{_name} = {_relpath}\n"
        return

    # Add one line to the PROJECT LAYOUT section, for each parameter. If the parameter is None, it
    # will be ignored.
    for name, abspath in filepaths.items():
        if name == "BUILD_DIR":
            continue
        add_line(name, abspath)
        continue
    return content


def __get_binaries_section(
    chip_dict: Dict[str, Any],
    resources_path: str,
) -> str:
    """The BINARIES section in 'dashboard.mk' lists all the binary files that
    must be built. This can vary wildly from one chip/board to another.
    Therefore, I decided to have these "binary rules" generated by dedicated
    'binary_rules.py' files.

    If you look at a 'chip.json5' file, you'll find it has an entry like:
        "binary_rules": "hardware/binary_rules.py",

    In other words, each chip/board file points to a specific 'binary_rules.py' file, which must be
    used to extract the binary rules from. That's exactly what this '__get_binaries_section()'
    function accomplishes: it checks the location of this 'binary_rules.py' file from the board and
    chip dictionaries (board gets priority) and then invokes the main function of that file.
    """
    # NOTE: The given 'chip_dict' is already overridden by 'board_dict' at this point!
    content = """
# 4. BINARIES
# ===========
"""
    relpath: Optional[str] = chip_dict["binary_rules_generator"]
    if relpath is None:
        return "\n# NO BINARY RULES DEFINED\n"
    abspath = f"{resources_path}/{relpath}"
    try:
        my_module = __load_module(abspath)
        return content + my_module["get_binary_rules"]() + "\n"
    except:
        traceback.print_exc()
    return content + "\n# NO BINARY RULES DEFINED\n\n"


def __get_compilation_flags_section(
    chip_dict: Dict[str, Any],
    version: int,
) -> str:
    """"""
    # NOTE: The given 'chip_dict' is already overridden by 'board_dict' at this point!
    content = """
# 5. COMPILATION FLAGS
# ====================
"""

    # $ CPU_FLAGS
    # List all the CPU flags. They'll get added to the TARGET_COMMONFLAGS variable.
    cpu_flags_list = []
    cpu_flags_dict = chip_dict["cpu_flags"]
    for k, v in cpu_flags_dict.items():
        if (v is None) or (v.lower() == "none") or (v.lower() == "null"):
            continue
        cpu_flags_list.append(f"-{k}={v}")
        continue

    # $ TARGET_COMMONFLAGS
    TARGET_COMMONFLAGS = ""
    tab = len("TARGET_COMMONFLAGS = ") * " "
    # First CPU flags, then chip flags, then board flags. Do not switch this order, as some board
    # flags have a '#' preceded to be commented out!.
    flaglist = (
        cpu_flags_list + chip_dict["compiler_flags"]["target_commonflags"]
    )
    if len(flaglist) > 0:
        for flag in flaglist:
            TARGET_COMMONFLAGS += f"{tab}{flag} \\\n"
        TARGET_COMMONFLAGS = TARGET_COMMONFLAGS[len(tab) :]
    if TARGET_COMMONFLAGS.endswith("\n"):
        TARGET_COMMONFLAGS = TARGET_COMMONFLAGS[0:-1]

    # $ TARGET_CFLAGS
    TARGET_CFLAGS = ""
    tab = len("TARGET_CFLAGS = ") * " "
    flaglist = chip_dict["compiler_flags"]["target_cflags"]
    if len(flaglist) > 0:
        for flag in flaglist:
            TARGET_CFLAGS += f"{tab}{flag} \\\n"
        TARGET_CFLAGS = TARGET_CFLAGS[len(tab) :]
    if TARGET_CFLAGS.endswith("\n"):
        TARGET_CFLAGS = TARGET_CFLAGS[0:-1]

    # $ TARGET_CXXFLAGS
    TARGET_CXXFLAGS = ""
    tab = len("TARGET_CXXFLAGS = ") * " "
    flaglist = chip_dict["compiler_flags"]["target_cxxflags"]
    if len(flaglist) > 0:
        for flag in flaglist:
            TARGET_CXXFLAGS += f"{tab}{flag} \\\n"
        TARGET_CXXFLAGS = TARGET_CXXFLAGS[len(tab) :]
    if TARGET_CXXFLAGS.endswith("\n"):
        TARGET_CXXFLAGS = TARGET_CXXFLAGS[0:-1]

    # $ TARGET_SFLAGS
    TARGET_SFLAGS = ""
    tab = len("TARGET_SFLAGS = ") * " "
    flaglist = chip_dict["compiler_flags"]["target_sflags"]
    if len(flaglist) > 0:
        for flag in flaglist:
            TARGET_SFLAGS += f"{tab}{flag} \\\n"
        TARGET_SFLAGS = TARGET_SFLAGS[len(tab) :]
    if TARGET_SFLAGS.endswith("\n"):
        TARGET_SFLAGS = TARGET_SFLAGS[0:-1]

    # $ TARGET_LDFLAGS
    TARGET_LDFLAGS = ""
    tab = len("TARGET_LDFLAGS = ") * " "
    flaglist = chip_dict["compiler_flags"]["target_ldflags"]
    flaglist.append("-T $(LINKERSCRIPT)")
    flaglist.append("-L $(dir $(LINKERSCRIPT))")
    if len(flaglist) > 0:
        for flag in flaglist:
            TARGET_LDFLAGS += f"{tab}{flag} \\\n"
        TARGET_LDFLAGS = TARGET_LDFLAGS[len(tab) :]
    if TARGET_LDFLAGS.endswith("\n"):
        TARGET_LDFLAGS = TARGET_LDFLAGS[0:-1]

    # $ TOOLCHAIN_LDLIBS
    TOOLCHAIN_LDLIBS = ""
    if version > 5:
        tab = len("TOOLCHAIN_LDLIBS = ") * " "
    else:
        tab = len("TOOLCHAIN_LOADLIBES = ") * " "
    flaglist = chip_dict["compiler_flags"]["toolchain_ldlibs"]
    if len(flaglist) > 0:
        for flag in flaglist:
            TOOLCHAIN_LDLIBS += f"{tab}{flag} \\\n"
        TOOLCHAIN_LDLIBS = TOOLCHAIN_LDLIBS[len(tab) :]
    if TOOLCHAIN_LDLIBS.endswith("\n"):
        TOOLCHAIN_LDLIBS = TOOLCHAIN_LDLIBS[0:-1]

    # $ DARM_MATH_XX_NOTE
    DARM_MATH_XX_NOTE = ""
    if (
        ("ARM_MATH" in TARGET_COMMONFLAGS)
        or ("ARM_MATH" in TARGET_CFLAGS)
        or ("ARM_MATH" in TARGET_CXXFLAGS)
        or ("ARM_MATH" in TARGET_SFLAGS)
        or ("ARM_MATH" in TARGET_LDFLAGS)
    ):
        DARM_MATH_XX_NOTE = str(
            "\n# NOTE:\n"
            "# The -DARM_MATH_XX flag can be:\n"
            "#     ARM_MATH_CM7\n"
            "#     ARM_MATH_CM4\n"
            "#     ARM_MATH_CM3\n"
            "#     ARM_MATH_CM0PLUS\n"
            "#     ARM_MATH_CM0\n"
            "#     ARM_MATH_ARMV8MBL\n"
            "#     ARM_MATH_ARMV8MML"
        )

    # $ Construct the content
    content += str(
        f"# CPU specific flags for C++, C and assembly compilation and linking.\n"
        f"TARGET_COMMONFLAGS = {TARGET_COMMONFLAGS}\n"
        f"\n"
        f"# CPU specific C compilation flags\n"
        f"TARGET_CFLAGS = {TARGET_CFLAGS}\n"
        f"\n"
        f"# CPU specific C++ compilation flags\n"
        f"TARGET_CXXFLAGS = {TARGET_CXXFLAGS}\n"
        f"\n"
        f"# CPU specific assembler flags\n"
        f"TARGET_SFLAGS = {TARGET_SFLAGS}\n"
        f"\n"
        f"# CPU specific linker flags\n"
        f"TARGET_LDFLAGS = {TARGET_LDFLAGS}\n"
        f"\n"
        f"# Libraries from the toolchain\n"
    )
    if version > 5:
        content += str(f"TOOLCHAIN_LDLIBS = {TOOLCHAIN_LDLIBS}")
    else:
        content += str(f"TOOLCHAIN_LOADLIBES = {TOOLCHAIN_LDLIBS}")
    content += "\n"
    if DARM_MATH_XX_NOTE != "":
        content += DARM_MATH_XX_NOTE
        content += "\n"
    return content


def __get_flash_rules_section(
    boardname: str,
    chipname: str,
    chip_dict: Dict[str, Any],
    probename: str,
    probe_dict: Dict[str, Any],
    resources_path: str,
) -> str:
    """The FLASH RULES section in 'dashboard.mk' provides one or more rules for
    the flash target. They can vary wildly from one chip/board to another.
    Therefore, I decided to have these "flash rules" generated by dedicated
    'flash_rules.py' files.

    If you look at a 'chip.json5' file, you'll find it has an entry like:
        "flash_rules": "hardware/openocd_flash_rules.py",

    In other words, each chip/board file points to a specific 'flash_rules.py' file, which must be
    used to generate the flash rules. That's exactly what this '__get_flash_rules_section()' func-
    tion accomplishes: it checks the location of said 'flash_rules.py' file from the board and chip
    dictionaries (board gets priority) and then invokes the main function of that file.

    NOTE:
    Also the json-file for the probe can point to a 'flash_rules.py' file. For example, if the user
    chooses the blackmagic probe, it points to 'hardware/probe/device/blackmagic_flash_rules.py' for
    the flash rules. In that case, this python module gets priority to generate the flash rules.
    """
    # NOTE: The given 'chip_dict' is already overridden by 'board_dict' at this point!
    content = """
# 6. FLASH RULES
# ==============
"""
    # $ Locate the 'flash_rules.py' file
    relpath: Optional[str] = None
    # PROBE
    if relpath is None:
        relpath = probe_dict["flash_rules_generator"]
    # CHIP
    if relpath is None:
        relpath = chip_dict["flash_rules_generator"]
    if relpath is None:
        return "\n# NO FLASH RULES DEFINED\n\n"
    abspath = f"{resources_path}/{relpath}"
    print(f"flash rules found at: {abspath}")
    print(f"file exists: {os.path.isfile(abspath)}")
    # $ Invoke 'flash_rules.py'
    # Invoke the main function from 'flash_rules.py'. It needs a few parameters to run properly.
    try:
        my_module = __load_module(abspath)
        return (
            content
            + my_module["get_flash_rules"](
                boardname,
                chipname,
                probename,
                chip_dict["cpu_flags"].get("mmcu"),
            )
            + "\n\n"
        )
    except:
        traceback.print_exc()
    return content + "\n# NO FLASH RULES DEFINED\n\n"


def __get_addendum() -> str:
    """"""
    return """
# ADDENDUM 1. MIT LICENSE
# =======================
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furn-
# ished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ADDENDUM 2. WHY THE FALLBACK MECHANISM FOR TOOLS?
# =================================================
# You might wonder: why bother with a default value? Embeetle could simply
# insert the actual paths (as selected in the dashboard) here, like:
# TOOLPREFIX = C:/my_tools/gnu_arm_toolchain_9.2.1/bin/arm-none-eabi-
# FLASHTOOL  = C:/my_tools/openocd_0.10.0_dev01138_32b/bin/openocd.exe
# However, that would make this dashboard.mk file location dependent: the
# location of the tool would be hardcoded. That's a problem if you access
# this project from two computers where the same tool is stored in different
# locations."""


def __load_module(filepath: str) -> Dict[str, Any]:
    """Load the python module at the given location."""
    assert os.path.isfile(filepath)
    assert filepath.endswith(".py")
    code = ""
    with open(filepath, "r", encoding="utf-8", newline="\n") as f:
        code = f.read()
    module = {}
    exec(code, module)
    return module
