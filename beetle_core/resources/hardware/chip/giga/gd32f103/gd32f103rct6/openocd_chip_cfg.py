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

    content = """# OpenOCD config file for gd32f103rct6

# gd32 devices support both JTAG and SWD transports.
source [find target/swj-dp.tcl]
source [find mem_helper.tcl]

if { [info exists CHIPNAME] } {
    set _CHIPNAME $CHIPNAME
} else {
    set _CHIPNAME gd32f1x
}

set _ENDIAN little

# Work-area is a space in RAM used for flash programming
# By default use 4kB (as found on some )
if { [info exists WORKAREASIZE] } {
    set _WORKAREASIZE $WORKAREASIZE
} else {
    set _WORKAREASIZE 0x1000
}

# Allow overriding the Flash bank size
if { [info exists FLASH_SIZE] } {
    set _FLASH_SIZE $FLASH_SIZE
} else {
    # autodetect size
    set _FLASH_SIZE 0
}

#jtag scan chain
if { [info exists CPUTAPID] } {
    set _CPUTAPID $CPUTAPID
} else {
    if { [using_jtag] } {
        # See  Document RM0008 Section 26.6.3
        set _CPUTAPID 0x3ba00477
    } {
        # this is the SW-DP tap id not the jtag tap id
        set _CPUTAPID 0x1ba01477
    }
}

swj_newdap $_CHIPNAME cpu -irlen 4 -ircapture 0x1 -irmask 0xf -expected-id $_CPUTAPID
dap create $_CHIPNAME.dap -chain-position $_CHIPNAME.cpu

if { [info exists BSTAPID] } {
    # FIXME this never gets used to override defaults...
    set _BSTAPID $BSTAPID
} else {
    # See Document RM0008
    # Section 29.6.2
    # Low density devices, Rev A
    set _BSTAPID1 0x06412041
    # Medium density devices, Rev A
    set _BSTAPID2 0x06410041
    # Medium density devices, Rev B and Rev Z
    set _BSTAPID3 0x16410041
    set _BSTAPID4 0x06420041
    # High density devices, Rev A
    set _BSTAPID5 0x06414041
    # Connectivity line devices, Rev A and Rev Z
    set _BSTAPID6 0x06418041
    # XL line devices, Rev A
    set _BSTAPID7 0x06430041
    # VL line devices, Rev A and Z In medium-density and high-density value line devices
    set _BSTAPID8 0x06420041
    # VL line devices, Rev A
    set _BSTAPID9 0x06428041
}

if {[using_jtag]} {
    swj_newdap $_CHIPNAME bs -irlen 5 -expected-id $_BSTAPID1 \
        -expected-id $_BSTAPID2 -expected-id $_BSTAPID3 \
        -expected-id $_BSTAPID4 -expected-id $_BSTAPID5 \
        -expected-id $_BSTAPID6 -expected-id $_BSTAPID7 \
        -expected-id $_BSTAPID8 -expected-id $_BSTAPID9
}

set _TARGETNAME $_CHIPNAME.cpu
target create $_TARGETNAME cortex_m -endian $_ENDIAN -dap $_CHIPNAME.dap

$_TARGETNAME configure -work-area-phys 0x20000000 -work-area-size $_WORKAREASIZE -work-area-backup 0

# flash size will be probed
set _FLASHNAME $_CHIPNAME.flash
flash bank $_FLASHNAME stm32f1x 0x08000000 0 0 0 $_TARGETNAME

# JTAG speed should be <= F_CPU/6. F_CPU after reset is 8MHz, so use F_JTAG = 1MHz
adapter_khz 1000

adapter_nsrst_delay 100
if {[using_jtag]} {
    jtag_ntrst_delay 100
}

reset_config srst_nogate

if {![using_hla]} {
    # if srst is not fitted use SYSRESETREQ to
    # perform a soft reset
    cortex_m reset_config sysresetreq
}

$_TARGETNAME configure -event examine-end {
    # DBGMCU_CR |= DBG_WWDG_STOP | DBG_IWDG_STOP |
    #              DBG_STANDBY | DBG_STOP | DBG_SLEEP
    mmw 0xE0042004 0x00000307 0
}

$_TARGETNAME configure -event trace-config {
    # Set TRACE_IOEN; TRACE_MODE is set to async; when using sync
    # change this value accordingly to configure trace pins
    # assignment
    mmw 0xE0042004 0x00000020 0
}
"""
    return content
