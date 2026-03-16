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

q = "'"
dq = '"'
bsl = "\\"


def get_flash_rules(*args, **kwargs) -> str:
    """Return the flash rules to be inserted in 'dashboard.mk'.

    These flash rules are valid for the blackmagic probe.
    """
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .hex file to the target microcontroller. To",
            f"# achieve this, it invokes the {q}GDB{q} tool, pointed to by the GDB variable (de-",
            f"# fined in the makefile) and provides the right parameters for the flash-",
            f"# operation through the Blackmagic probe. GDB is invoked with the following",
            f"# parameters:",
            f"#",
            f"#   -n                Do not execute commands from any {q}.gdbinit{q} initializat-",
            f"#                     ion file (unless one is passed explicitely with {q}-x{q}).",
            f"#                     We add this flag to ensure complete control over which",
            f"#                     files are passed to GDB.",
            f"#",
            f"#   -batch            Run in batch mode. Exit with status 0 after processing",
            f"#                     the command files specified with {q}-x{q}. Exit with",
            f"#                     nonzero status if an error occurs while executing the",
            f"#                     GDB commands in the command files.",
            f"#",
            f"#   -x <file>         The {q}-x{q} flag instructs GDB to execute/evaluate the com-",
            f"#                     mands in the given file. In this case, the file we pass",
            f"#                     to GDB is a specific {q}.gdbinit{q} file.",
            f"#",
            f"#   -ex {dq}<command> <arg0> <arg1> .. <argn>{dq}     The {q}-ex{q} flag instructs GDB",
            f"#                                           to execute a specific command,",
            f"#                                           potentially with some arguments.",
            f"#                                           In this case, the command is",
            f"#                                           {q}flash-remote{q}, a user-defined",
            f"#                                           command you can find in the",
            f"#                                           {q}.gdbinit{q} file.",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f"\t$(GDB) -n {bsl}",
            f"         -batch {bsl}",
            f"         -x $(GDB_FLASHFILE) {bsl}",
            f"         -ex {dq}flash-remote $(ELF_FILE) $(FLASH_PORT){dq}",
            f"",
            f"# The flags given to GDB contain quite a lot of variables. Let{q}s figure out",
            f"# what they mean:",
            f"#",
            f"#   $(GDB_FLASHFILE):  Relative path to the {q}.gdbinit{q} file (with respect to",
            f"#                      the build folder). This file contains the commands to",
            f"#                      connect to the GDB-server on the Blackmagic probe and",
            f"#                      flash the microcontroller.",
            f"#",
            f"#   $(ELF_FILE):       Relative path to the {q}.elf{q} file (with respect to the",
            f"#                      build folder). This file is the binary output from the",
            f"#                      build and contains some extra debug info.",
            f"#",
            f"#   $(FLASH_PORT):     The Serial Port connection to the blackmagic probe.",
            f"#",
            f"# Flash mechanism",
            f"# ---------------",
            f"# Let{q}s go through the whole flash process:",
            f"# The {q}flash{q} target starts GDB (Gnu Debugger) and passes it a {q}.gdbinit{q}",
            f"# file. This file contains the commands to flash the .elf file to the micro-",
            f"# controller, which are grouped into a user-defined function named",
            f"# {q}flash-remote{q}.",
            f"# The {q}-ex{q} flag instructs GDB to execute this {q}flash-remote{q} function, and",
            f"# passes it two parameters:",
            f"#     - $(ELF_FILE): where to find the .elf file",
            f"#     - $(FLASH_PORT): where to find the blackmagic probe",
            f"#",
            f"# With this information, the user-defined {q}flash-remote{q} function is able to",
            f"# flash the microcontroller!",
        ]
    )
    return "\n".join(flash_rules_lines)
