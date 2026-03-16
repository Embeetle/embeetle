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
    content = f"""
# Dangerous Prototypes - Bus Blaster
# The Bus Blaster has a configurable buffer between the FTDI FT2232H and the
# JTAG header which allows it to emulate various debugger types. It comes
# configured as a JTAGkey device.
# http://dangerousprototypes.com/docs/Bus_Blaster
echo "Info : If you need SWD support, flash KT-Link buffer from https://github.com/bharrisau/busblaster
and use dp_busblaster_kt-link.cfg instead"

adapter driver ftdi
ftdi device_desc "Dual RS232-HS"
ftdi vid_pid 0x0403 0x6010

ftdi layout_init 0x0c08 0x0f1b
ftdi layout_signal nTRST -data 0x0100 -noe 0x0400
ftdi layout_signal nSRST -data 0x0200 -noe 0x0800

transport select {transport_protocol}
"""
    return content
