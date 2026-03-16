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
    content = """# OpenOCD config file for 'rp2040'
set CHIPNAME rp2040
# source [find target/rp2040-core0.cfg] # <- !! this is the wrong one !!
source [find target/rp2040.cfg]  
"""
    return content
