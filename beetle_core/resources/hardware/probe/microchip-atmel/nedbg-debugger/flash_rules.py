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

    These flash rules are valid for the nedbg probe.
    """
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .hex file to the target microcontroller. To",
            f"# achieve this it invokes {q}pymcuprog{q}:",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f'\t"$(FLASHTOOL)" write -f $(ELF_FILE:.elf=.hex) {bsl}',
            f"               -p $(PACKPATH) {bsl}",
            f"",
            f"# Let{q}s examine these flags one-by-one:",
            f"#",
            f"#   -f                  Specify the hex file to be flashed.",
            f"#",
            f"#   -p <PACKPATH>       Specify the path to the DFP for PIC devices.",
            f"#",
            f"# NOTE:",
            f"# While pymcuprog itself contains sufficient information to program AVR devices (",
            f"# with UPDI interface), it is unable to program a PIC device without access to",
            f"# programming scripts for that device. These scripts are deployed in Device Family",
            f"# Packs (DFP) on https://packs.download.microchip.com and are only provided for",
            f"# PIC devices mounted on Curiosity Nano boards or other boards with the PKOB nano",
            f"# (nEDBG) debugger.",
            f"# In Embeetle projects, it is customary to put the DFP in the {q}config/{q} folder.",
        ]
    )
    return "\n".join(flash_rules_lines)
