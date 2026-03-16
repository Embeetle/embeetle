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
    """Return the flash rules to be inserted in 'dashboard.mk'."""
    CHIP_TYPE = None
    if chipname == "n32g430c8l7":
        CHIP_TYPE = "N32G430C8"
    elif chipname == "n32g457vel7":
        CHIP_TYPE = "N32G457QE"
    elif chipname == "n32l406mbl7":
        CHIP_TYPE = "N32L406MB"

    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the binary to the target microcontroller. The",
            f"# Nations Tech chips are not yet integrated in OpenOCD. Therefore, we{q}ll use",
            f"# the JLink software instead. Embeetle is not allowed to distribute the JLink",
            f"# software via its server. You{q}ll have to download and install the JLink soft-",
            f"# ware yourself and point at it here. For more information and installation in-",
            f"# structions, refer to:",
            f"# https://embeetle.com/#supported-hardware/nations-tech/boards/{boardname}",
            f"# and",
            f"# https://embeetle.com/#supported-hardware/probes/jlink" f"",
            f"# JLINK PATH",
            f"# ----------",
            f"# Assign the location of your J-Link executable to the variable JLINK_EXE_PATH.",
            f"# Spaces must be escaped with a backslash {q}{bsl}{q} character.",
            f"# JLINK_EXE_PATH = C:/Program{bsl} Files{bsl} (x86)/SEGGER/JLink_V690a/JLink.exe",
            f"JLINK_EXE_PATH = C:/Program{bsl} Files/SEGGER/JLink/JLink.exe",
            f"# JLINK_EXE_PATH = /opt/SEGGER/JLink/JLinkExe",
            f"",
            f"# CHIP TYPE",
            f"# ---------",
            f"CHIP_TYPE = {CHIP_TYPE}",
            f"",
            f"# FLASH COMMAND",
            f"# -------------",
            f'ifneq ("$(wildcard $(JLINK_EXE_PATH))","")',
            f"  .PHONY: flash",
            f"  flash: $(BINARIES) print_flash",
            f"\t$(info # )",
            f"\t$(info # SEGGER J-Link software found at:)",
            f'\t$(info # "$(subst {bsl},,$(JLINK_EXE_PATH))")',
            f"\t$(info # )",
            f"\t$(file >flash.jlink,r)",
            f"\t$(file >>flash.jlink,loadfile $(ELF_FILE))",
            f"\t$(file >>flash.jlink,r)",
            f"\t$(file >>flash.jlink,g)",
            f"\t$(file >>flash.jlink,qc)",
            f'\t"$(subst {bsl},,$(JLINK_EXE_PATH))" {bsl}',
            f"        -device $(CHIP_TYPE) {bsl}",
            f"        -if SWD {bsl}",
            f"        -speed 4000 {bsl}",
            f"        -autoconnect 1 {bsl}",
            f"        -CommanderScript flash.jlink",
            f"else",
            f"  .PHONY: flash",
            f"  flash:",
            f"\t$(info # )",
            f"\t$(info # SEGGER J-Link software cannot be found at:)",
            f'\t$(info # "$(subst {bsl},,$(JLINK_EXE_PATH))")',
            f"\t$(info # Make sure you have installed the J-Link software and modify the)",
            f"\t$(info # JLINK_EXE_PATH variable in {q}config/dashboard.mk{q} accordingly.)",
            f"\t$(info # )",
            f"\t$(info # Consult the following webpage for detailed instructions:)",
            f"\t$(info # https://embeetle.com/#supported-hardware/nations-tech/boards/{boardname}#j-link-executable)",
            f"\t$(info # )",
            f'\t$(error "$(subst {bsl},,$(JLINK_EXE_PATH))" not found!)',
            f"endif",
            f"",
        ]
    )
    return "\n".join(flash_rules_lines)
