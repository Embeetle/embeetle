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


def get_flash_rules(
    boardname: str,
    chipname: str,
    probename: str,
    *args,
    **kwargs,
) -> str:
    """Return the flash rules to be inserted in 'dashboard.mk' for the given
    combination of board,

    chip and probe. Valid for the following chips:
        - atsam3x8e
    """
    boardname = boardname.lower().replace(" ", "-").replace("_", "-")
    chipname = chipname.lower().replace(" ", "-").replace("_", "-")
    probename = probename.lower().replace(" ", "-").replace("_", "-")
    flash_rules_lines: List[str] = []

    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .bin file to the target microcontroller. To",
            f"# achieve this it invokes the {q}bossac{q} program, pointed to by the FLASHTOOL",
            f"# variable (defined at the top of this file), and provides the right parame-",
            f"# ters to launch bossac properly.",
            f"",
        ]
    )

    # & ATSAM THROUGH COM-PORT
    if (probename == "usb-to-uart-converter") or (
        probename == "arduino-as-isp"
    ):
        flash_rules_lines.extend(
            __get_comport_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
            )
        )

    # & ATSAM THROUGH PROBE
    else:
        flash_rules_lines.extend(
            __get_probe_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
            )
        )
        flash_rules_lines.extend(
            __get_bootloader_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
            )
        )
    return "\n".join(flash_rules_lines)


def __get_comport_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    # $ Reset chip
    # Most Arduino boards can simply be flashed through the COM-port without requiring a reset.
    # But some do need a reset, which typically happens by connecting to the COM-port briefly at
    # 1200 baud.
    define_reset_cmds = ""
    reset_cmds = ""
    define_reset_cmds = str(
        f"# NOTE: Unlike other Arduino boards, the ATSAM3X8E microcontroller on this\n"
        f"#       board needs to be reset right before flashing the firmware through its\n"
        f"#       Flash Port (Serial Port). There is a trick to do this without pressing\n"
        f"#       the reset button: open the port briefly at 1200 baud to trigger the\n"
        f"#       chip to reset:\n"
        f"ifeq ($(SHELLSTYLE),cmd)\n"
        f"  # Windows\n"
        f"  RESET_CHIP = mode $(FLASH_PORT) baud=12 dtr=on & mode $(FLASH_PORT) baud=12 dtr=off\n"
        f"else\n"
        f"  # Linux\n"
        f"  RESET_CHIP = stty 1200 raw ignbrk hup < $(FLASH_PORT)\n"
        f"endif\n"
        f"\n"
    )
    reset_cmds = str(f"\n" f"\t$(RESET_CHIP)")

    if "due" in boardname:
        flash_rules_lines.extend(
            [
                f"# IMPORTANT:",
                f"# Make sure you connect to the Arduino DUE{q}s {q}Programming Port (USB2){q} (the",
                f"# one closest to the DC power connector)! Check this webpage for more info:",
                f"# https://embeetle.com/#supported-hardware/arduino/boards/due",
                f"",
            ]
        )

    flash_rules_lines.extend(
        [
            f"{define_reset_cmds}# Back to the flash-procedure. The flash-rule defined below launches bossac",
            f"# and instructs it to flash the firmware through a Serial Port.",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash{reset_cmds}",
            f'\t"$(FLASHTOOL)" --info {bsl}',
            f"               --port=$(FLASH_PORT) {bsl}",
            f"               --force_usb_port=false {bsl}",
            f"               --erase {bsl}",
            f"               --write {bsl}",
            f"               --verify {bsl}",
            f"               --boot=1 {bsl}",
            f"               --reset {bsl}",
            f"               $(ELF_FILE:.elf=.bin)",
            f"",
            f"# Let{q}s examine these flags one-by-one:",
            f"#",
            f"#   -i, --info          Display diagnostic information identifying the target",
            f"#                       device.",
            f"#",
            f"#   -d, --debug         Print verbose diagnostic messages for debug purposes.",
            f"#",
            f"#   -p, --port =<port>  Use the serial port <port> to communicate with the de-",
            f"#                       vice.",
            f"#",
            f"#   -U, --force_usb_port =<bool>  Enable automatic detection of the target{q}s",
            f"#                                 USB port if <bool> is false. Disable  USB",
            f"#                                 port autodetection if <bool> is true.",
            f"#",
            f"#   -e, --erase         Erase  the  target{q}s  entire  flash  memory  before",
            f"#                       performing  any  read or write operations.",
            f"#",
            f"#   -w, --write         Write FILE to the target{q}s flash memory. This operat-",
            f"#                       ion can be expedited  immensely if used in conjunction",
            f"#                       with the {q}--erase{q} option.",
            f"#",
            f"#   -v, --verify        Verify that FILE matches the contents of flash on the",
            f"#                       target, or vice-versa if you prefer.",
            f"#",
            f"#   -b, --boot =<val>   Boot from ROM if <val> is 0. Boot from FLASH if <val>",
            f"#                       is 1. (The latter is default.) This option is comp-",
            f"#                       letely disregarded on unsupported devices.",
            f"#",
            f"#   -R, --reset         Reset  the  CPU  after  writing  FILE  to  the  tar-",
            f"#                       get. This option is completely disregarded on unsup-",
            f"#                       ported devices.",
        ]
    )
    return flash_rules_lines


def __get_probe_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# At the moment, we don{q}t know yet how to flash firmware through an external",
            f"# probe to the {chipname}.",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f"\t$(error # WARNING: we don{q}t know yet how to flash through an external probe to this chip)",
            f"",
        ]
    )
    return flash_rules_lines


def __get_bootloader_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# At the moment, we don{q}t know yet how to flash the bootloader to the {chipname}.",
            f".PHONY: flash_bootloader",
            f"flash_bootloader: print_flash_bootloader",
            f"\t$(error # WARNING: we don{q}t know yet how to flash the bootloader to this chip)",
            f"",
        ]
    )
    return flash_rules_lines


def __get_probe_flag(probename: str) -> str:
    """Return the flag required by AVRDUDE to recognize the probe."""
    probeflag = ""
    if "avr-isp-mkii" in probename:
        probeflag = "-cstk500v2"
    elif "atmel-ice" in probename:
        probeflag = "-catmelice_isp"
    else:
        probeflag = "-c<none probe>"
    return probeflag
