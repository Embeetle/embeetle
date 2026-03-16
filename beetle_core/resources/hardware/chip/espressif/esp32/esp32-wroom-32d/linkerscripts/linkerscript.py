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
import os, traceback

q = "'"
dq = '"'
bsl = "\\"


def get_linkerscript(
    chipname: str,
    chip_dict: Dict[str, Any],
    *args,
    **kwargs,
) -> str:
    """The 'chip_dict' passed here is already overridden by the board
    dictionary."""
    content = f"""/*
********************************************************************************
**                                                                            **
**                    LINKERSCRIPT FOR {q}{chipname}{q}
**                                                                            **
********************************************************************************
**
*/

/* The linkerscript for Espressif chips is distributed over several files,    */
/* such as:                                                                   */
/* - esp32_out.ld                                                             */
/* - esp32.project.ld                                                         */
/* - esp32.rom.ld                                                             */
/* - esp32.peripherals.ld                                                     */
/* - esp32.rom.libgcc.ld                                                      */
/* - esp32.rom.spiram_incompatible_fns.ld                                     */
/*                                                                            */
/* These linkerscripts are included for the linking stage in 'dashboard.mk'.  */"""
    return content
