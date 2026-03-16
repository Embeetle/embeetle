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


def get_openocd_probe_cfg(
    boardname: Optional[str],
    chipname: Optional[str],
    probename: Optional[str],
    target_file: Optional[str],
    transport_protocol: Optional[str],
    *args,
    **kwargs,
) -> str:
    """"""
    if transport_protocol is None:
        transport_protocol = "sdi"

    # $ Intro
    content_list = [
        f"# OpenOCD config file for {q}{probename}{q}",
        f"# Must be applied before the chip config file!",
        f"adapter driver wlinke",
        f"adapter speed 6000",
    ]

    # $ Transport protocol selection
    transport_protocol = transport_protocol.lower().replace("-", "_")
    content_list.append(f"transport select {transport_protocol}")
    return "\n".join(content_list)
