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


def get_gdbinit(
    chipname: str,
    chip_dict: Dict[str, Any],
    *args,
    **kwargs,
) -> str:
    """The 'chip_dict' is already overridden by the board dictionary at this
    point."""
    content = f"""# ------------------------------------------- #
#                                             #
#              GDB commands                   #
#              FOR {q}{chipname}{q}
#                                             #
# ------------------------------------------- #
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
  load
  monitor reset run
  monitor shutdown
  quit
end"""
    return content
