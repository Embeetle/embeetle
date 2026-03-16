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

import traceback
from typing import *
import itertools

q = "'"
dq = '"'
bsl = "\\"


def get_gdbinit(
    chipname: str,
    chip_dict: Dict[str, Any],
    *args,
    **kwargs,
) -> str:
    """The 'chip_dict' is already overridden by the board dictionary at this
    point."""
    # $ Obtain flash data
    mem_data = chip_dict["linkerscript"]["memory"]
    main_flash_name: Optional[str] = None
    for name in mem_data.keys():
        if "flash" in name.lower():
            main_flash_name = name
            break
        continue

    # $ Determine 'flash_origin_hex' and 'flash_size_hex'
    flash_origin: str = "<FLASH_ORIGIN>"
    flash_origin_hex: str = "<FLASH_ORIGIN_HEX>"
    flash_size: str = "<FLASH_SIZE>"
    flash_size_hex: str = "<FLASH_SIZE_HEX>"
    if main_flash_name is not None:
        flash_origin = mem_data[main_flash_name]["origin"]
        flash_origin_hex = __convert_size_to_hex(flash_origin)
        flash_size = mem_data[main_flash_name]["length"]
        flash_size_hex = __convert_size_to_hex(flash_size)

    content = f"""# ------------------------------------------- #
#                                             #
#              GDB commands                   #
#              FOR {q}{chipname}{q}
#                                             #
# ------------------------------------------- #
# {flash_size}Byte FLASH
# GDB flash commands. Feel free to edit.
define flash-remote
  echo {bsl}n
  echo {bsl}n--------------------------------------------------------------------------------
  echo {bsl}n  Run flash-remote function:
  echo {bsl}n  ==========================
  echo {bsl}n  flash-remote(
  echo {bsl}n      elf_file = $arg0,
  echo {bsl}n      openocd_path = $arg1,
  echo {bsl}n      probe_file = $arg2,
  echo {bsl}n      chip_file = $arg3,
  echo {bsl}n  )
  echo {bsl}n--------------------------------------------------------------------------------
  echo {bsl}n
  file $arg0
  target extended-remote | $arg1 -f $arg2 -f $arg3 -c "gdb_port pipe; log_output openocd.log"
  monitor init
  monitor reset halt
  monitor flash erase_address {flash_origin_hex} {flash_size_hex}
  monitor reset halt
  monitor program $arg0
  monitor reset run
  monitor shutdown
  quit
end"""
    return content


def __convert_size_to_hex(size: str) -> str:
    """"""
    try:
        if isinstance(size, int):
            size = str(size)
        size = size.lower()
        if size.startswith("0x"):
            return size
        nr_of_bytes = 0
        if ("kb" in size) or ("k" in size):
            nr_of_bytes = 1024 * int(size.replace("kb", "").replace("k", ""))
        elif ("mb" in size) or ("m" in size):
            nr_of_bytes = 1048576 * int(size.replace("mb", "").replace("m", ""))
        elif "b" in size:
            nr_of_bytes = int(size)
        return hex(nr_of_bytes)
    except:
        traceback.print_exc()
    return hex(0)
