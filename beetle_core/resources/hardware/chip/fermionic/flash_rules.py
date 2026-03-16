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


def get_flash_rules(
    boardname: str,
    chipname: str,
    probename: str,
    mmcu: str,
    *args,
    **kwargs,
) -> str:
    """Return the flash rules to be inserted in 'dashboard.mk' for the given
    combination of board,

    chip and probe. Valid for the following chips:
        - fd5mlm01032n
    """
    boardname = boardname.lower().replace(" ", "-").replace("_", "-")
    chipname = chipname.lower().replace(" ", "-").replace("_", "-")
    probename = probename.lower().replace(" ", "-").replace("_", "-")
    flash_rules_lines: List[str] = []

    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .bin file to the target microcontroller. To",
            f"# achieve this it invokes the {q}fermionic-flash-prog{q} program, pointed to by the",
            f"# FLASHTOOL variable (defined at the top of this file), and provides the right",
            f"# parameters to launch properly.",
        ]
    )

    # & THROUGH COM-PORT
    if probename == "fermionic-uart-converter":
        flash_rules_lines.extend(
            __get_comport_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
                mmcu=mmcu,
            )
        )

    # & THROUGH PROBE
    else:
        flash_rules_lines.extend(
            __get_probe_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
                mmcu=mmcu,
            )
        )
    return "\n".join(flash_rules_lines)


def __get_comport_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
    mmcu: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    flash_rules_lines.extend(
        [
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f'\t"$(FLASHTOOL)" -b $(ELF_FILE:.elf=.bin) {bsl}',
            f"                   -p 0 {bsl}",
            f"                   -c $(FLASH_PORT) {bsl}",
            f"                   -r 57600",
            f"",
        ]
    )
    return flash_rules_lines


def __get_probe_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
    mmcu: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    flash_rules_lines.extend(
        [
            f"# Not implemented yet.",
        ]
    )
    return flash_rules_lines
