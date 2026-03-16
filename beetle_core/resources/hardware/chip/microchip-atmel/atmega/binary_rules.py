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


def get_binary_rules(*args, **kwargs) -> str:
    """Return the binary rules to be inserted in 'dashboard.mk'."""
    binary_rules_lines: List[str] = []
    binary_rules_lines.extend(
        [
            "# Define the binaries that must be built.",
            "BINARIES = \\",
            "  $(ELF_FILE) \\",
            "  $(ELF_FILE:.elf=.bin) \\",
            "  $(ELF_FILE:.elf=.hex) \\",
            "  $(ELF_FILE:.elf=.eep)",
            "",
            "# Define the rules to build these binaries from the .elf file.",
            "%.bin: %.elf",
            "\t$(info )",
            "\t$(info )",
            "\t$(info Preparing: $@)",
            "\t$(OBJCOPY) -O binary $< $@",
            "",
            "%.hex: %.elf %.eep",
            "\t$(info )",
            "\t$(info )",
            "\t$(info Preparing: $@)",
            "\t$(OBJCOPY) -O ihex -R .eeprom $< $@",
            "",
            "%.eep: %.elf",
            "\t$(info )",
            "\t$(info )",
            "\t$(info Preparing: $@)",
            "\t$(OBJCOPY) -O ihex \\",
            "             -j .eeprom \\",
            "             --set-section-flags=.eeprom=alloc,load \\",
            "             --no-change-warnings \\",
            "             --change-section-lma .eeprom=0 \\",
            "             $< $@",
        ]
    )
    return "\n".join(binary_rules_lines)
