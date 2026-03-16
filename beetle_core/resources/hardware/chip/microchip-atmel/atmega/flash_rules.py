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
    mmcu: str,
    *args,
    **kwargs,
) -> str:
    """Return the flash rules to be inserted in 'dashboard.mk' for the given
    combination of board,

    chip and probe. Valid for the following chips:
        - atmega32u4
        - atmega328p-mu
        - atmega328p-pu
        - atmega2560
        - atmega4809
    """
    boardname = boardname.lower().replace(" ", "-").replace("_", "-")
    chipname = chipname.lower().replace(" ", "-").replace("_", "-")
    probename = probename.lower().replace(" ", "-").replace("_", "-")
    flash_rules_lines: List[str] = []

    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .hex file to the target microcontroller. To",
            f"# achieve this it invokes the {q}avrdude{q} program, pointed to by the FLASHTOOL",
            f"# variable (defined at the top of this file), and provides the right parame-",
            f"# ters to launch avrdude properly.",
            f"#",
            f"# NOTE: To function properly, avrdude needs the {q}avrdude.conf{q} file, which is in-",
            f"#       side the avrdude installation folder. Before avrdude v6.99.0, avrdude was",
            f"#       unable to locate this file by itself. You then had to provide the absolute",
            f"#       path to the file with the {q}-C{q} argument, or copy the file to some location",
            f"#       location in your $USER directory. Make sure your avrdude version is higher",
            f"#       than v6.99.0 such that it just works.",
            f"",
        ]
    )

    # & ATMEGA THROUGH COM-PORT
    if (probename == "usb-to-uart-converter") or (
        probename == "arduino-as-isp"
    ):
        flash_rules_lines.extend(
            __get_comport_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
                mmcu=mmcu,
            )
        )

    # & ATMEGA THROUGH PROBE
    else:
        flash_rules_lines.extend(
            __get_probe_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
                mmcu=mmcu,
            )
        )
        flash_rules_lines.extend(
            __get_bootloader_flash_rule(
                boardname=boardname,
                chipname=chipname,
                probename=probename,
                mmcu=mmcu,
            )
        )
    return "\n".join(flash_rules_lines)


def __get_comport_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
    mmcu: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    # $ progid
    # For Arduino Uno and Nano, the parameter '-carduino' must be passed. For Arduino Mega, it
    # should be '-cwiring' instead.
    progid = "arduino"
    if "atmega2560" in chipname:
        progid = "wiring"
    elif "atmega32u4" in chipname:
        progid = "avr109"
    elif "atmega4809" in chipname:
        progid = "jtag2updi"
    # $ baudrate
    # For most Arduino boards, the baudrate should be 115200, but for the Arduino Leonardo, it
    # should be 57600.
    baud = "115200"
    if "atmega32u4" in chipname:
        baud = "57600"
    # $ COM-port placeholder
    # Most Arduino boards simply flash the firmware through the COM-port the board identifies
    # itself through. However, the Arduino Leonardo has a boot-related COM-port after reset (eg.
    # COM10) for just a couple of seconds, then it displays the 'normal' COM-port.
    comport_placeholder = "$(FLASH_PORT)"
    if "atmega32u4" in chipname:
        comport_placeholder = "$(BOOT_FLASH_PORT)"
    # $ Erase settings
    erase = f"               -D {bsl}"
    if "atmega4809" in chipname:
        erase = str(f"               -e {bsl}\n" f"               -D {bsl}")
    # $ Flash settings
    flash = f"               -Uflash:w:$(ELF_FILE:.elf=.hex):i"
    if "atmega4809" in chipname:
        flash = str(
            f"               -Uflash:w:$(ELF_FILE:.elf=.hex):i {bsl}\n"
            f"               -Ufuse2:w:0x01:m {bsl}\n"
            f"               -Ufuse5:w:0xC9:m {bsl}\n"
            f"               -Ufuse8:w:0x00:m {{upload.extra_files}}"
        )
    # $ Reset chip
    # Most Arduino boards can simply be flashed through the COM-port without requiring a reset.
    # But some do need a reset, which typically happens by connecting to the COM-port briefly at
    # 1200 baud.
    define_reset_cmds = ""
    reset_cmds = ""
    if "atmega4809" in chipname:
        define_reset_cmds = str(
            f"# NOTE: Unlike other Arduino boards, the ATMega4809 microcontroller on this\n"
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
    # $ Bootloader comment
    bootloader_comment = str(
        f" It will only\n"
        f"# work if your microcontroller has a bootloader! Arduino boards are shipped with\n"
        f"# such a bootloader pre-installed. If your chip has no bootloader yet, or it is\n"
        f"# corrupted, you need to flash it again. Select a probe in the dashboard (eg. AVR\n"
        f"# ISP mkII or Atmel ICE) to do that."
    )
    if "nano-every" in boardname:
        bootloader_comment = str(
            f"\n"
            f"# The {boardname} board has a SAMD11 auxiliary microcontroller next to\n"
            f"# the ATMega4809 target. This auxiliary chip takes care of the USB-to-UART\n"
            f"# conversion and can even flash new firmware to the target chip. That{q}s exact-\n"
            f"# ly what we{q}ll do here:"
        )

    flash_rules_lines.extend(
        [
            f"{define_reset_cmds}# Back to the flash-procedure. The flash-rule defined below launches avrdude",
            f"# and instructs it to flash the firmware through a Serial Port.{bootloader_comment}",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash{reset_cmds}",
            f'\t"$(FLASHTOOL)" -v {bsl}',
            f"               -p{mmcu} {bsl}",
            f"               -c{progid} {bsl}",
            f"               -P{comport_placeholder} {bsl}",
            f"               -b{baud} {bsl}",
            f"{erase}",
            f"{flash}",
            f"",
            f"# Let{q}s examine these flags one-by-one:",
            f"#",
            f"#   -v                  Enable verbose output.",
            f"#",
            f"#   -p <partno>         Specify what type of part (MCU) that is connected to",
            f"#                       the programmer.",
            f"#",
            f"#   -c <programmer-id>  Specify the programmer to be used.",
            f"#",
            f"#   -P <port>           Identify the device to which the programmer is attach-",
            f"#                       ed. We use this parameter to define the Flash Port",
            f"#                       (Serial Port), which should be passed on the commandline",
            f"#                       when invoking gnu make.",
            f"#",
            f"#   -b <baudrate>       Override the RS-232 connection baud rate specified in",
            f"#                       the respective programmer{q}s entry of the configuration",
            f"#                       file.",
            f"#",
            f"#   -D                  Disable auto erase for flash.",
            f"#",
            f"#   -e                  Erase chip before programming.",
            f"#",
            f"#",
            f"#   -U <memtype>:<op>:<filename>:<format>   Perform a memory operation.",
            f"#",
            f"#                       <memtype>  specifies the memory type to operate on,",
            f"#                                  such as {q}flash{q}, {q}eeprom{q}, {q}fuse{q}, {q}lock{q},",
            f"#                                  ...",
            f"#",
            f"#                       <op>       specifies what operation to perform, such",
            f"#                                  as {q}r{q} for read, {q}w{q} for write and {q}v{q} for",
            f"#                                  verify.",
            f"#",
            f"#                       <filename> indicates the name of the file to read or",
            f"#                                  write.",
            f"#",
            f"#                       <format>   contains the format of the file to read or",
            f"#                                  write, such as {q}i{q} for Intel Hex, {q}s{q} for",
            f"#                                  Motorola S-record, {q}r{q} for raw binary, {q}e{q}",
            f"#                                  for elf and {q}a{q} for autodetect.",
        ]
    )
    return flash_rules_lines


def __get_probe_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
    mmcu: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    # $ The Arduino Nano-Every cannot be flashed through probe (currently)
    if "atmega4809" in chipname:
        flash_rules_lines.extend(
            [
                f"# The {boardname} board has a SAMD11 auxiliary microcontroller next to",
                f"# the ATMega4809 target. This auxiliary chip takes care of the USB-to-UART",
                f"# conversion and can even flash new firmware to the target. At the moment, we",
                f"# don{q}t know how to flash firmware to the ATMega4809 target through an exter-",
                f"# nal probe.",
                f".PHONY: flash",
                f"flash: $(BINARIES) print_flash",
                f"\t$(error # WARNING: we don{q}t know yet how to flash through an external probe for this board)",
                f"",
            ]
        )
    else:
        flash_rules_lines.extend(
            [
                f"# Back to the flash-procedure. The flash-rule defined below launches avrdude",
                f"# and instructs it to flash the firmware through an external probe.",
                f".PHONY: flash",
                f"flash: $(BINARIES) print_flash",
                f'\t"$(FLASHTOOL)" -v {bsl}',
                f"               -p{mmcu} {bsl}",
                f"               {__get_probe_flag(probename)} {bsl}",
                f"               -Pusb {bsl}",
                f"               -Uflash:w:$(ELF_FILE:.elf=.hex):i",
                f"",
                f"# Let{q}s examine these flags one-by-one:",
                f"#",
                f"#   -v                  Enable verbose output.",
                f"#",
                f"#   -p <partno>         Specify what type of part (MCU) that is connected to",
                f"#                       the programmer.",
                f"#",
                f"#   -c <programmer-id>  Specify the programmer to be used.",
                f"#",
                f"#   -P <port>           Identify the device to which the programmer is attach-",
                f"#                       ed.",
                f"#",
                f"#   -U <memtype>:<op>:<filename>:<format>   Perform a memory operation.",
                f"#",
                f"#                       <memtype>  specifies the memory type to operate on,",
                f"#                                  such as {q}flash{q}, {q}eeprom{q}, {q}fuse{q}, {q}lock{q},",
                f"#                                  ...",
                f"#",
                f"#                       <op>       specifies what operation to perform, such",
                f"#                                  as {q}r{q} for read, {q}w{q} for write and {q}v{q} for",
                f"#                                  verify.",
                f"#",
                f"#                       <filename> indicates the name of the file to read or",
                f"#                                  write.",
                f"#",
                f"#                       <format>   contains the format of the file to read or",
                f"#                                  write, such as {q}i{q} for Intel Hex, {q}s{q} for",
                f"#                                  Motorola S-record, {q}r{q} for raw binary, {q}e{q}",
                f"#                                  for elf and {q}a{q} for autodetect.",
            ]
        )
    return flash_rules_lines


def __get_bootloader_flash_rule(
    chipname: str,
    boardname: str,
    probename: str,
    mmcu: str,
) -> List[str]:
    """"""
    flash_rules_lines: List[str] = []

    # $ Fuses for 1st command
    Ulock_1 = "None"
    Uefuse_1 = "None"
    Uhfuse_1 = "None"
    Ulfuse_1 = "None"
    # $ Fuses for 2nd command
    Ulock_2 = "None"
    if "atmega328p" in chipname:
        Ulock_1 = "Ulock:w:0x3F:m"
        Uefuse_1 = "Uefuse:w:0xFD:m"
        Uhfuse_1 = "Uhfuse:w:0xDE:m"
        Ulfuse_1 = "Ulfuse:w:0xFF:m"
        Ulock_2 = "Ulock:w:0xCF:m"
    elif "atmega2560" in chipname:
        Ulock_1 = "Ulock:w:0x3F:m"
        Uefuse_1 = "Uefuse:w:0xFD:m"
        Uhfuse_1 = "Uhfuse:w:0xD8:m"
        Ulfuse_1 = "Ulfuse:w:0xFF:m"
        Ulock_2 = "Ulock:w:0x0F:m"
    elif "atmega32u4" in chipname:
        Ulock_1 = "Ulock:w:0x3F:m"
        Uefuse_1 = "Uefuse:w:0xcb:m"
        Uhfuse_1 = "Uhfuse:w:0xd8:m"
        Ulfuse_1 = "Ulfuse:w:0xff:m"
        Ulock_2 = "Ulock:w:0x2F:m"

    # $ The Arduino Nano-Every has no bootloader
    if "atmega4809" in chipname:
        flash_rules_lines.extend(
            [
                f"",
                f"# Microcontrollers on Arduino boards are preloaded with a bootloader to enable",
                f"# flashing over a UART connection (Serial Port). However, the",
                f"# {boardname} has no such bootloader. Instead, it relies on an auxili-",
                f"# ary chip, the SAMD11, to flash firmware to the target chip.",
                f".PHONY: flash_bootloader",
                f"flash_bootloader: print_flash_bootloader",
                f"\t$(error # WARNING: the {chipname} has no bootloader!)",
                f"",
            ]
        )
    # $ Other Arduino boards have a bootloader
    else:
        flash_rules_lines.extend(
            [
                f"",
                f"# Microcontrollers on Arduino boards are preloaded with a bootloader to enable",
                f"# flashing over a UART connection (Serial Port). In case the bootloader",
                f"# itself gets corrupted, you need to reflash it with a probe. The target",
                f"# {q}flash_bootloader{q} is intended for this operation.",
                f".PHONY: flash_bootloader",
                f"flash_bootloader: print_flash_bootloader",
                f'\t"$(FLASHTOOL)" -v {bsl}',
                f"               -p{mmcu} {bsl}",
                f"               {__get_probe_flag(probename)} {bsl}",
                f"               -Pusb {bsl}",
                f"               -e {bsl}",
                f"               -{Ulock_1} {bsl}",
                f"               -{Uefuse_1} {bsl}",
                f"               -{Uhfuse_1} {bsl}",
                f"               -{Ulfuse_1}",
                f'\t"$(FLASHTOOL)" -v {bsl}',
                f"               -p{mmcu} {bsl}",
                f"               {__get_probe_flag(probename)} {bsl}",
                f"               -Pusb {bsl}",
                f"               -Uflash:w:$(BOOTLOADER_FILE):i {bsl}",
                f"               -{Ulock_2}",
                f"",
                f"# The bootloader file being flashed is defined by the BOOTLOADER_FILE var-",
                f"# iable, see the top of this file.",
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
