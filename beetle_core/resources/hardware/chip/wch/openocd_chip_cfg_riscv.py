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


def get_openocd_chip_cfg(
    chipname: Optional[str],
    target_file: Optional[str],
    *args,
    **kwargs,
) -> str:
    """The parameters passed here are extracted from a 'chip_dict' which is
    already overridden by the board dictionary."""
    if chipname is None:
        return "# Cannot generate OpenOCD config file"

    # $ Intro
    content_list = [
        f"# OpenOCD config file for {q}{chipname}{q}",
        f"wlink_set_address 0x00000000",
        f"set _CHIPNAME wch_riscv",
        f"sdi newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x00001",
        f"",
        f"set _TARGETNAME $_CHIPNAME.cpu",
        f"",
        f"target create $_TARGETNAME.0 wch_riscv -chain-position $_TARGETNAME",
        f"$_TARGETNAME.0 configure  -work-area-phys 0x20000000 -work-area-size 10000 -work-area-backup 1",
        f"set _FLASHNAME $_CHIPNAME.flash",
        f"",
        f"flash bank $_FLASHNAME wch_riscv 0x00000000 0 0 0 $_TARGETNAME.0",
        f"",
        f"echo {dq}Ready for Remote Connections{dq}",
    ]
    return "\n".join(content_list)
