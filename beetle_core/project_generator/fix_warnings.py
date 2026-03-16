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
import purefunctions
from typing import *
import re
import os

q = "'"


def __print_msg(
    msg: str, color: Optional[str] = None, printfunc: Optional[Callable] = None
) -> None:
    """"""
    if (printfunc is None) or (printfunc is print):
        purefunctions.printc(
            msg,
            color=color,
        )
        return
    if color == "error":
        printfunc(msg, "#ef2929")
    else:
        printfunc(msg)
    return


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
    filepath: str, printfunc: Optional[Callable] = None
) -> bool:
    """Fix source file.

    Return True if success, False if error occured.
    """
    try:
        total = 0
        data = open(filepath, "rb").read()
        for p, p_func in fixes:

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
                __print_msg(f"replace:{m}{group_zero}{m}\n", None, printfunc)
                fixed: Union[str, bytes] = p_func(match)
                fixed_str = None
                if isinstance(fixed, str):
                    fixed_str = fixed
                else:
                    try:
                        fixed_str = fixed.decode("utf-8")
                    except:
                        fixed_str = str(fixed)
                __print_msg(f"by:{m}{fixed_str}{m}\n", None, printfunc)
                return fixed_str

            def fixit_bytes(match: re.Match) -> bytes:
                return fixit(match).encode("utf-8")

            try:
                data, count = p.subn(fixit, data)
            except:
                data, count = p.subn(fixit_bytes, data)
            total = total + count
        if total:
            open(filepath, "wb").write(data)
            __print_msg(
                f"Fixed {total} warnings in {q}{filepath}{q}\n", None, printfunc
            )
    except:
        __print_msg(
            f"ERROR: Error fixing {q}{filepath}{q}\n", "error", printfunc
        )
        __print_msg(f"{traceback.format_exc()}\n", "error", printfunc)
        return False
    return True


def fix_source_tree(
    rootpath: str, printfunc: Optional[Callable] = None
) -> bool:
    """Fix files in source tree.

    Return True if success, False if error occured.
    """
    total = 0
    error_occured = False
    if os.path.isdir(rootpath):

        def report_walk_error(os_error: OSError) -> None:
            __print_msg(
                f"ERROR: Error scanning {rootpath}: {os_error}",
                "error",
                printfunc,
            )
            return

        for _root, _dirs, _files in os.walk(
            rootpath, onerror=report_walk_error
        ):
            for f in _files:
                if is_source_file(f):
                    __print_msg(f"Check source file: {f}", None, printfunc)
                    success = fix_source_file(os.path.join(_root, f), printfunc)
                    if not success:
                        error_occured = True
                continue
            continue
    else:
        if is_source_file(rootpath):
            success = fix_source_file(rootpath)
            if not success:
                error_occured = True
    return not error_occured


if __name__ == "__main__":
    import sys

    for root in sys.argv[1:]:
        print(f"Fixing compiler warnings in {root}")
        fix_source_tree(root)
    exit(0)
