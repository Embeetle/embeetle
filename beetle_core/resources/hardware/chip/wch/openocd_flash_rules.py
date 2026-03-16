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

    These flash rules are valid for a ma- jority of chips that use OpenOCD.
    """
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The WCH microcontrollers need a modified OpenOCD (distributed by WCH). This",
            f"# OpenOCD tool needs to load a few libraries that are in the executable-folder.",
            f"# On Windows that happens automatically. On Linux, one needs to set the",
            f"# LD_LIBRARY_PATH environment variable.",
            f"",
            f"# First, define the {q}flash{q} target:",
            f".PHONY: flash",
            f"",
            f"# Set the LD_LIBRARY_PATH environment variable to point to the executable-",
            f"# folder:",
            f"flash: export LD_LIBRARY_PATH=$(dir $(FLASHTOOL))",
            f"",
            f"# Finally, launch OpenOCD:",
            f"flash: $(BINARIES) print_flash",
            f'\t"$(FLASHTOOL)" -f $(OPENOCD_PROBEFILE) {bsl}',
            f"               -f $(OPENOCD_CHIPFILE) {bsl}",
            f"               -c {dq}program {{$(ELF_FILE)}} verify reset; shutdown;{dq}",
            f"",
            f"# Let{q}s figure out what the flags mean:",
            f"#",
            f"#   -f: Specify a config file for OpenOCD to use. We pass this flag",
            f"#       twice: once for the config file that defines the probe and",
            f"#       once to define the chip (microcontroller).",
            f"#",
            f"#   -c: Run the specified commands. The ones we pass are:",
            f"#         1) program {{file}} verify reset;",
            f"#            Upload the firmware to the flash memory and verify",
            f"#            if it was successful.",
            f"#         2) shutdown;",
            f"#            Quit OpenOCD.",
        ]
    )
    return "\n".join(flash_rules_lines)
