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


def get_linkerscript(
    chipname: str,
    chip_dict: Dict[str, Any],
    *args,
    **kwargs,
) -> str:
    """The 'chip_dict' passed here is already overridden by the board
    dictionary."""
    mem_data = chip_dict["linkerscript"]["memory"]

    # $ Construct MEMORY regions
    memlines = [
        f'{memname} ({mem_data[memname]["rights"]}): '
        f'ORIGIN = {mem_data[memname]["origin"]}, '
        f'LENGTH = {mem_data[memname]["length"]}\n'
        for memname in mem_data.keys()
    ]
    memory = "    " + "    ".join(memlines)

    content = f'''/*
********************************************************************************
**                                                                            **
**                    LINKERSCRIPT FOR {q}{chipname}{q}
**                                                                            **
********************************************************************************
**
*/
SEARCH_DIR(.)
GROUP(-lgcc -lc -lnosys)

/* Define memory regions. */
MEMORY
{{
{memory}
}}

SECTIONS
{{
}}

SECTIONS
{{
    . = ALIGN(4);
    .mem_section_dummy_ram :
    {{
    }}
    .log_dynamic_data :
    {{
        PROVIDE(__start_log_dynamic_data = .);
        KEEP(*(SORT(.log_dynamic_data*)))
        PROVIDE(__stop_log_dynamic_data = .);
    }} > RAM
    .log_filter_data :
    {{
        PROVIDE(__start_log_filter_data = .);
        KEEP(*(SORT(.log_filter_data*)))
        PROVIDE(__stop_log_filter_data = .);
    }} > RAM
}} INSERT AFTER .data;

SECTIONS
{{
    .mem_section_dummy_rom :
    {{
    }}
    .log_const_data :
    {{
        PROVIDE(__start_log_const_data = .);
        KEEP(*(SORT(.log_const_data*)))
        PROVIDE(__stop_log_const_data = .);
    }} > FLASH
    .log_backends :
    {{
        PROVIDE(__start_log_backends = .);
        KEEP(*(SORT(.log_backends*)))
        PROVIDE(__stop_log_backends = .);
    }} > FLASH
      .nrf_balloc :
    {{
        PROVIDE(__start_nrf_balloc = .);
        KEEP(*(.nrf_balloc))
        PROVIDE(__stop_nrf_balloc = .);
    }} > FLASH
}} INSERT AFTER .text

INCLUDE "nrf_common.ld"'''
    return content
