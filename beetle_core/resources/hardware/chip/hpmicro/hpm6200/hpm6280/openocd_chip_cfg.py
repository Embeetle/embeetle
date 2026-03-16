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

    content = """
# CHIP HPM6280 SINGLE-CORE MODE
# =============================
# The following OpenOCD statements define the HPM6280 chip in single-core mode. Comment or delete
# these statements if you want to work in dual-core mode.
set _CHIP hpm6280
set _CPUTAPID 0x1000563D
jtag newtap $_CHIP cpu -irlen 5 -expected-id $_CPUTAPID
set _TARGET0 $_CHIP.cpu0
target create $_TARGET0 riscv -chain-position $_CHIP.cpu -coreid 0
$_TARGET0 configure -work-area-phys 0x00000000 -work-area-size 0x20000 -work-area-backup 0
targets $_TARGET0

# CHIP HPM6280 DUAL-CORE MODE
# ===========================
# The following OpenOCD statements define the HPM6280 chip in dual-core mode. They are commented
# out right now. If you want to work in dual-core mode, uncomment these statements and comment or
# delete the single-core mode statements.
# set _CHIP hpm6280
# set _CPUTAPID 0x1000563D
# jtag newtap $_CHIP cpu -irlen 5 -expected-id $_CPUTAPID
# set _TARGET0 $_CHIP.cpu0
# target create $_TARGET0 riscv -chain-position $_CHIP.cpu -coreid 0
# $_TARGET0 configure -work-area-phys 0x00000000 -work-area-size 0x20000 -work-area-backup 0
# targets $_TARGET0
# proc dmi_write {reg value} {
#     $::_TARGET0 riscv dmi_write ${reg} ${value}
# }
# proc dmi_read {reg} {
#     set v [$::_TARGET0 riscv dmi_read ${reg}]
#     return ${v}
# }
# proc dmi_write_memory {addr value} {
#     dmi_write 0x39 ${addr}
#     dmi_write 0x3C ${value}
# }
# proc dmi_read_memory {addr} {
#     set sbcs [expr { 0x100000 | [dmi_read 0x38] }]
#     dmi_write 0x38 ${sbcs}
#     dmi_write 0x39 ${addr}
#     set value [dmi_read 0x3C]
#     return ${value}
# }
# proc release_core1 {} {
#     # set start point for core1
#     dmi_write_memory 0xF4002C08 0x20012588
#     # set boot flag for core1
#     dmi_write_memory 0xF4002C0C 0xC1BEF1A9
#     # release core1
#     dmi_write_memory 0xF4002C00 0x1000
# }
# set _TARGET1 $_CHIP.cpu1
# target create $_TARGET1 riscv -chain-position $_CHIP.cpu -coreid 1
# $_TARGET1 configure -work-area-phys 0x00000000 -work-area-size 0x20000 -work-area-backup 0
# $_TARGET1 configure -event examine-start {
#     release_core1
# }
# $_TARGET1 configure -event reset-deassert-pre {
#     $::_TARGET0 arp_poll
#     release_core1
# }

# BOARD HPM6200EVK_RevB
# =====================
# The following OpenOCD statements define the HPM6200EVK_RevB board.
flash bank xpi0 hpm_xpi 0x80000000 0x1000000 1 1 $_TARGET0 0xF3040000
proc init_clock {} {
    $::_TARGET0 riscv dmi_write 0x39 0xF4002000
    $::_TARGET0 riscv dmi_write 0x3C 0x1

    $::_TARGET0 riscv dmi_write 0x39 0xF4002000
    $::_TARGET0 riscv dmi_write 0x3C 0x2

    $::_TARGET0 riscv dmi_write 0x39 0xF4000800
    $::_TARGET0 riscv dmi_write 0x3C 0xFFFFFFFF

    $::_TARGET0 riscv dmi_write 0x39 0xF4000810
    $::_TARGET0 riscv dmi_write 0x3C 0xFFFFFFFF

    $::_TARGET0 riscv dmi_write 0x39 0xF4000820
    $::_TARGET0 riscv dmi_write 0x3C 0xFFFFFFFF

    $::_TARGET0 riscv dmi_write 0x39 0xF4000830
    $::_TARGET0 riscv dmi_write 0x3C 0xFFFFFFFF
    echo "clocks has been enabled!"
}
$_TARGET0 configure -event reset-init {
    init_clock
}
$_TARGET0 configure -event gdb-attach {
    reset halt
}
"""
    return content
