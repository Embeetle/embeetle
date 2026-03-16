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
        - esp32-pico-d4
        - esp32-wroom-32d
    """
    boardname = boardname.lower().replace(" ", "-").replace("_", "-")
    chipname = chipname.lower().replace(" ", "-").replace("_", "-")
    probename = probename.lower().replace(" ", "-").replace("_", "-")
    flash_rules_lines: List[str] = []
    flash_rules_lines.extend(
        [
            f"# The {q}flash{q} target flashes the .hex file to the target microcontroller. To",
            f"# achieve this, it invokes the {q}esptool{q} tool, pointed to by the FLASHTOOL",
            f"# variable (see top of this file) and provides the right parameters for the",
            f"# flash-operation.",
            f"#",
            f"# esptool is invoked with the following parameters:",
            f"#",
            f"#   --chip <chip>     Target chip type {{auto, esp8266, esp32, esp32s2,",
            f"#                     esp32s3beta2, esp32c3}}.",
            f"#",
            f"#   --port <port>     Serial port device.",
            f"#",
            f"#   --baud <baud>     Serial port baud rate used when flashing/reading.",
            f"#",
            f"#   --before <action> What to do before connecting to the chip {{default_reset,",
            f"#                     no_reset, no_reset_no_sync}}.",
            f"#",
            f"#   --after <action>  What to do after esptool is finished {{hard_reset,",
            f"#                     soft_reset, no_reset}}.",
            f"#",
            f"#   write_flash       Write a binary blob to flash.",
            f"#",
            f"#   -z                Compress the firmware while flashing.",
            f"#",
            f"#   --flash_mode      SPI Flash mode {{qio, qout, dio, dout}}.",
            f"#",
            f"#   --flash_size      SPI Flash size in MegaBytes {{1MB, 2MB, 4MB, 8MB, 16M}}",
            f"#                     plus ESP8266-only {{256KB, 512KB, 2MB-c1, 4MB-c1}}",
            f"#",
            f"#   --flash_freq      SPI Flash frequency {{40m, 26m, 20m, 80m}}",
            f"#",
            f".PHONY: flash",
            f"flash: $(BINARIES) print_flash",
            f'\t"$(FLASHTOOL)" --chip esp32 {bsl}',
            f"               --port $(FLASH_PORT) {bsl}",
            f"               --baud 921600 {bsl}",
            f"               --before default_reset {bsl}",
            f"               --after hard_reset {bsl}",
            f"               write_flash {bsl}",
            f"               -z {bsl}",
            f"               --flash_mode dio {bsl}",
            f"               --flash_freq 80m {bsl}",
            f"               --flash_size detect {bsl}",
            f"               0xe000 $(BOOTSWITCH_FILE) {bsl}",
            f"               0x1000 $(BOOTLOADER_FILE) {bsl}",
            f"               0x10000 $(ELF_FILE:.elf=.bin) {bsl}",
            f"               0x8000 $(PARTITIONS_CSV_FILE:.csv=.bin)",
            f"",
            f"# The flags given to esptool contain some variables. Let{q}s figure out what",
            f"# they mean:",
            f"#",
            f"#   $(FLASH_PORT):      The Serial Port connection to the USB-to-UART chip (eg.",
            f"#                       CP2102N).",
            f"#",
            f"#   $(BOOTSWITCH_FILE): Relative path to the {q}boot_app0.bin{q} file (with",
            f"#                       respect to the build folder). This is known as the",
            f"#                       {q}ota_data{q} section in the partition table, and can be",
            f"#                       considered as a switch. It determines if either app0",
            f"#                       or app1 should boot.",
            f"#                       The {q}ota_data{q} partition is two flash sectors (0x2000",
            f"#                       bytes) in size, because (aside from being a switch)",
            f"#                       this memory is also used to take notes during OTA",
            f"#                       flashing. About the size, the manual explains:",
            f"#                            {dq}The OTA data partition is two flash sectors",
            f"#                            (0x2000 bytes) in size, to prevent problems if",
            f"#                            there is a power failure while it is being writ-",
            f"#                            ten. Sectors are independently erased and written",
            f"#                            with matching data, and if they disagree a coun-",
            f"#                            ter field is used to determine which sector was",
            f"#                            written more recently.{dq}",
            f"#",
            f"#   $(BOOTLOADER_FILE): Relative path to the {q}bootloader_dio_80m.bin{q} file",
            f"#                       (with respect to the build folder). This is known as",
            f"#                       the {q}secondstage bootloader{q}. The second stage boot-",
            f"#                       loader reads the partition table found by default at",
            f"#                       offset 0x8000. Then the bootloader consults the",
            f"#                       {q}ota_data{q} partition (the boot-switch) to determine",
            f"#                       which OTA app to launch (eg. app0 or app1).",
            f"#",
            f"#   $(ELF_FILE):        Relative path to the {q}.elf{q} file (with respect to the",
            f"#                       build folder). This file is the binary output from",
            f"#                       the build and contains some extra debug info.",
            f"#",
            f"#   $(PARTITIONS_CSV_FILE):  The .csv file that defines the partitions table",
            f"#                            for the target microcontroller.",
            f"#",
        ]
    )
    return "\n".join(flash_rules_lines)
