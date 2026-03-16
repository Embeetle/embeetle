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
    *args,
    **kwargs,
) -> str:
    """Return the flash rules to be inserted in 'dashboard.mk' for the given
    combination of board,

    chip and probe. Valid for the following chips:
        - esp32-pico-d4
        - esp32-wroom-32d
    """
    boardname = boardname.lower().replace(" ", "-").replace("_", "-")
    chipname = chipname.lower().replace(" ", "-").replace("_", "-")
    probename = probename.lower().replace(" ", "-").replace("_", "-")
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the binary to the target microcontroller. To",
            f"# achieve this, it invokes the OpenOCD tool:",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash flash_prepare flash_nvds",
            f'\t"$(FLASHTOOL)" -f $(OPENOCD_PROBEFILE){bsl}',
            f"               -f $(OPENOCD_CHIPFILE){bsl}",
            f"               -s {dq}$(subst bin/openocd,tcl,$(subst openocd.exe,openocd,$(FLASHTOOL))){dq}{bsl}",
            f"               -s ../config/openocd{bsl}",
            f"               -c {dq}init; verify_rom_version; sydney_load_flash $(ELF_FILE); set _RESET_HARD_ON_EXIT 1; exit;{dq}",
            f"",
            f"flash_prepare: export FTDI_BENIGN_BOOT=1",
            f"flash_prepare: export FTDI_HARD_RESET=1",
            f".PHONY: flash_prepare",
            f"flash_prepare:",
            f'\t"$(FLASHTOOL)" -f $(OPENOCD_PROBEFILE){bsl}',
            f"               -f $(OPENOCD_CHIPFILE){bsl}",
            f"               -s {dq}$(subst bin/openocd,tcl,$(subst openocd.exe,openocd,$(FLASHTOOL))){dq}{bsl}",
            f"               -s ../config/openocd{bsl}",
            f"               -c {dq}init; release_reset; sleep 100; set_normal_boot; exit;{dq}",
            f"",
            f".PHONY: flash_nvds",
            f"flash_nvds:",
            f'\t"$(FLASHTOOL)" -f $(OPENOCD_PROBEFILE){bsl}',
            f"               -f $(OPENOCD_CHIPFILE){bsl}",
            f"               -s {dq}$(subst bin/openocd,tcl,$(subst openocd.exe,openocd,$(FLASHTOOL))){dq}{bsl}",
            f"               -s ../config/openocd{bsl}",
            f"               -c {dq}init; verify_rom_version; sydney_load_nvds ../tag_data/flash_nvds.bin; exit;{dq}",
            f"",
        ]
    )
    return "\n".join(flash_rules_lines)
