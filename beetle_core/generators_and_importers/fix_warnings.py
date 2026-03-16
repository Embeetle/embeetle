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
import traceback
import purefunctions, functions
from typing import *
import re
import os

q = "'"


def is_source_file(filename: str) -> bool:
    """"""
    if filename.lower().endswith(
        (".c", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".s", ".asm")
    ):
        return True
    return False


fixes = [
    (
        # Warning: equality comparison with extraneous parentheses
        re.compile(rb"\( *(\([^()]+==[^()]+\)) *\)"),
        lambda match: match.group(1),
    ),
    (
        # Warning: '__packed__' attribute ignored when parsing type
        re.compile(rb"\(__packed (uint32_t +\*?)\)"),
        lambda match: b"(" + match.group(1) + b")",
    ),
    (
        # Warning: invalid reassignment of non-absolute variable 'DMA2_Stream4_IRQHandler'
        re.compile(
            rb"(\.weak\s+DMA\d_Stream\d_IRQHandler\s+\.thumb_set\s+DMA\d_Stream\d_IRQHandler,Default_Handler)\s+\1"
        ),
        lambda match: match.group(1),
    ),
]
hardware_serial_fixes = [
    (
        # https://forum.embeetle.com/t/arduino-due-blinky-doesnt-build/676
        re.compile(rb"(virtual\s+void\s+begin\(unsigned\s+long\));"),
        lambda match: match.group(1) + b" = 0;",
    ),
    (
        # https://forum.embeetle.com/t/arduino-due-blinky-doesnt-build/676
        re.compile(rb"(virtual\s+void\s+end\(\));"),
        lambda match: match.group(1) + b" = 0;",
    ),
]


def fix_source_file(
    filepath: str,
    verbose: bool = False,
    miniverbose: bool = False,
    printfunc: Optional[Callable] = None,
) -> bool:
    """
    :param filepath:    Path to source file.
    :param verbose:     Print verbose output.
    :param miniverbose: Print only something when the file gets changed.
    :param printfunc:   Function to print with.

    Fix source file. Return True if success, False if error occured.
    """
    if verbose or miniverbose:
        if printfunc is None:
            printfunc = purefunctions.printc
    if verbose:
        printfunc(f"Check source file: {filepath}")
    elif miniverbose:
        printfunc(".", end="")
    try:
        total = 0
        content = open(filepath, "rb").read()
        _fixes = fixes
        if "hardwareserial" in filepath.lower():
            _fixes += hardware_serial_fixes
        for p, p_func in _fixes:

            def fixit(match: re.Match) -> str:
                # Print on multiple lines if there is a newline in the match. Otherwise, just print
                # the replacement on a single line.
                group_zero: Union[str, bytes] = match.group(0)
                if isinstance(group_zero, str):
                    pass
                else:
                    # match.group(0) returned a 'bytes-like-object', not a string.
                    group_zero = group_zero.decode("utf-8")
                m = " "
                if "\n" in group_zero:
                    m = "\n"
                if verbose or miniverbose:
                    if miniverbose:
                        printfunc("]")
                    printfunc(f"replace:{m}{group_zero}{m}\n")
                fixed: Union[str, bytes] = p_func(match)
                fixed_str = None
                if isinstance(fixed, str):
                    fixed_str = fixed
                else:
                    try:
                        fixed_str = fixed.decode("utf-8")
                    except:
                        fixed_str = str(fixed)
                if verbose or miniverbose:
                    printfunc(f"by:{m}{fixed_str}{m}\n")
                    if miniverbose:
                        printfunc("[", end="")
                return fixed_str

            def fixit_bytes(match: re.Match) -> bytes:
                return fixit(match).encode("utf-8")

            try:
                content, count = p.subn(fixit, content)
            except:
                content, count = p.subn(fixit_bytes, content)
            total = total + count
            continue

        if total:
            open(filepath, "wb").write(content)
            if verbose or miniverbose:
                if miniverbose:
                    printfunc("]")
                printfunc(f"Fixed {total} warnings in {q}{filepath}{q}\n")
                if miniverbose:
                    printfunc("[", end="")
    except:
        if verbose or miniverbose:
            printfunc(f"ERROR: Error fixing {q}{filepath}{q}\n", color="error")
            printfunc(f"{traceback.format_exc()}\n", color="error")
        return False
    return True


def fix_source_tree(
    rootpath: str,
    verbose: bool = False,
    miniverbose: bool = False,
    printfunc: Optional[Callable] = None,
    *args,
    **kwargs,
) -> bool:
    """
    :param rootpath:    Path to source tree.
    :param verbose:     Print verbose output.
    :param miniverbose: Print only a dot per file, and something more when the file gets changed.
    :param printfunc:   Function to print with.

    Fix files in source tree.
    Return True if success, False if error occured.
    """
    if printfunc is None:
        printfunc = purefunctions.printc
    total = 0
    error_occured = False
    if os.path.isdir(rootpath):

        def report_walk_error(os_error: OSError) -> None:
            printfunc(
                f"ERROR: Error scanning {rootpath}: {os_error}",
                color="error",
            )
            return

        for _root, _dirs, _files in os.walk(
            rootpath, onerror=report_walk_error
        ):
            # $ Skip the `.git` directory
            _dirs[:] = [d for d in _dirs if d != ".git"]
            for f in _files:
                if is_source_file(f):
                    # The '.' gets printed inside fix_source_file().
                    success = fix_source_file(
                        filepath=os.path.join(_root, f),
                        verbose=verbose,
                        miniverbose=miniverbose,
                        printfunc=printfunc,
                    )
                    if not success:
                        error_occured = True
                continue
            continue
    else:
        if is_source_file(rootpath):
            # The '.' gets printed inside fix_source_file().
            success = fix_source_file(
                filepath=rootpath,
                verbose=verbose,
                miniverbose=miniverbose,
                printfunc=printfunc,
            )
            if not success:
                error_occured = True
    return not error_occured
