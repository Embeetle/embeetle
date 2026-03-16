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

    These flash rules are valid for the wchisp probe.
    """
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .elf file to the target microcontroller. To",
            f"# achieve this it invokes {q}wchisp{q}:",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f'\t"$(FLASHTOOL)" flash $(ELF_FILE)',
            f"",
        ]
    )
    return "\n".join(flash_rules_lines)
