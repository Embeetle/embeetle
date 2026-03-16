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
    content = """
if { [info exists CHIPNAME] } {
    set _CHIPNAME $CHIPNAME
} else {
    set _CHIPNAME pic32mz
}

if { [info exists ENDIAN] } {
    set _ENDIAN $ENDIAN
} else {
    set _ENDIAN little
}

if { [info exists CPUTAPID] } {
    set _CPUTAPID $CPUTAPID
} else {
    set _CPUTAPID 0x25127053
}

# default working area is 16384
if { [info exists WORKAREASIZE] } {
    set _WORKAREASIZE $WORKAREASIZE
} else {
    set _WORKAREASIZE 0x4000
}

adapter srst delay 500
jtag_ntrst_delay 500
reset_config none

#jtag scan chain
#format L IRC IRCM IDCODE (Length, IR Capture, IR Capture Mask, IDCODE)
jtag newtap $_CHIPNAME cpu -irlen 5 -ircapture 0x1 -irmask 0x1f -expected-id $_CPUTAPID

set _TARGETNAME $_CHIPNAME.cpu
target create $_TARGETNAME mips_mAptiv -endian $_ENDIAN -chain-position $_TARGETNAME

mips32 scan_delay 5000
# On PIC32MZ devices, a new System Bus is utilized that supports
# using RAM memory for program or data without the need for
# special configuration. Therefore, no special registers are
# associated with the System Bus to configure these features.
global _PIC32MZ_DATASIZE
global _WORKAREASIZE
set _PIC32MZ_DATASIZE 0x800
set _PIC32MZ_PROGSIZE [expr {($_WORKAREASIZE - $_PIC32MZ_DATASIZE)}]

$_TARGETNAME configure -work-area-phys 0x80018000 -work-area-size 0x1000 -work-area-backup 0

$_TARGETNAME configure -event reset-init {
    global _PIC32MZ_DATASIZE
    global _WORKAREASIZE
    # Set system clock to 8MHz if the default clock configuration is set
    # SYSKEY register, make sure OSCCON is locked
    mww 0xbf800030 0x0
    # SYSKEY register, write unlock sequence
    mww 0xbf800030 0xaa996655
    mww 0xbf800030 0x556699aa
    # OSCCON register + 4, clear OSCCON FRCDIV bits: 24, 25 and 26, divided by 1
    mww 0xbf801204 0x07000000
    # SYSKEY register, relock OSCCON
    mww 0xbf800030 0x0
}

set _FLASHNAME $_CHIPNAME.flash0
flash bank $_FLASHNAME pic32mz 0x1fc00000 0 0 0 $_TARGETNAME

# add virtual banks for kseg0 and kseg1
flash bank vbank0 virtual 0xbfc00000 0 0 0 $_TARGETNAME $_FLASHNAME
flash bank vbank1 virtual 0x9fc00000 0 0 0 $_TARGETNAME $_FLASHNAME

set _FLASHNAME $_CHIPNAME.flash0_upper
flash bank $_FLASHNAME pic32mz 0x1fc20000 0 0 0 $_TARGETNAME

# add virtual banks for kseg0 and kseg1
flash bank vbank0_upper virtual 0xbfc20000 0 0 0 $_TARGETNAME $_FLASHNAME
flash bank vbank1_upper virtual 0x9fc20000 0 0 0 $_TARGETNAME $_FLASHNAME

set _FLASHNAME $_CHIPNAME.flash1
flash bank $_FLASHNAME pic32mz 0x1d000000 0 0 0 $_TARGETNAME

# add virtual banks for kseg0 and kseg1
flash bank vbank2 virtual 0xbd000000 0 0 0 $_TARGETNAME $_FLASHNAME
flash bank vbank3 virtual 0x9d000000 0 0 0 $_TARGETNAME $_FLASHNAME

adapter speed 2000
init
halt
"""
    return content
