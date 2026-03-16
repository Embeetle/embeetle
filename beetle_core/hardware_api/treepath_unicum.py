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

# WARNING
# THIS FILE GETS OFTEN R-SYNCED FROM <BEETLE_CORE> TO <BEETLE_PROJECT_GENERATOR>. ONLY EDIT THIS
# FILE FROM WITHIN THE <BEETLE_CORE> FOLDER. OTHERWISE, YOUR CHANGES GET LOST.
from __future__ import annotations
from typing import *
import data
from components.singleton import Unicum
import hardware_api.segment_unicum as _segment_unicum_
import hardware_api.hardware_api as _hardware_api_

if TYPE_CHECKING:
    import hardware_api.chip_unicum as _chip_unicum_
    import hardware_api.board_unicum as _board_unicum_


class TREEPATH_UNIC(_segment_unicum_.SEGMENT, metaclass=Unicum):
    @classmethod
    def get_unicum_from_name(cls, name: str) -> Optional[TREEPATH_UNIC]:
        """"""
        return TREEPATH_UNIC(name)

    def __init__(self, name: str) -> None:
        """Create/get an TREEPATH_UNIC()-instance with the given name.

        If the instance already exists somewhere, it won't be recreated. You'll
        get the 'pointer' to the existing one. (see @Unicum)
        """
        self._name_ = _hardware_api_.HardwareDB().standardize_treepath_name(
            name
        )
        return

    def get_name(self) -> str:
        """"""
        return self._name_

    def get_dict(self) -> Dict[str, Any]:
        """"""
        return _hardware_api_.HardwareDB().get_project_layout_dict(self._name_)

    def get_default_relpath(
        self,
        chip_unicum: Optional[_chip_unicum_.CHIP] = None,
        board_unicum: Optional[_board_unicum_.BOARD] = None,
    ) -> Optional[str]:
        """ATTENTION This function gets called also before the
        Project()-instance is fully initialized to know where the default '.btl'
        files can be found.

        Both the chip and board are unknown at that point.
        """
        # $ Define CHIP()- and BOARD()-unicums
        if chip_unicum is None:
            try:
                chip_unicum = data.current_project.get_chip().get_chip_unicum()
            except:
                pass
        if board_unicum is None:
            try:
                board_unicum = (
                    data.current_project.get_board().get_board_unicum()
                )
            except:
                pass
        chip_dict: Optional[Dict[str, Any]] = None
        if (chip_unicum is not None) and (board_unicum is not None):
            chip_dict = chip_unicum.get_chip_dict(board=board_unicum.get_name())
        elif chip_unicum is not None:
            chip_dict = chip_unicum.get_chip_dict(board=None)
        else:
            chip_dict = None

        # $ Obtain default project layout for general project
        relpath = _hardware_api_.HardwareDB().get_project_layout_dict(
            self._name_
        )["default_relpath"]
        if chip_dict is None:
            return relpath

        # $ Special case for linkerscript
        if "linkerscript" in relpath:
            linkerscript_generators = chip_dict["linkerscript"].get(
                "linkerscript_generators"
            )
            if (linkerscript_generators is None) or (
                len(linkerscript_generators) == 0
            ):
                return "config/linkerscript.ld"
            main_generator = linkerscript_generators[0]
            main_generator_name = main_generator.split("/")[-1].replace(
                ".py", ".ld"
            )
            return f"config/{main_generator_name}"

        # $ Special case for bootloaders
        if (
            ("{bootloader}" in relpath)
            or ("{bootswitch}" in relpath)
            or ("{partitions_csv}" in relpath)
        ):
            bootloaders: Optional[List[str]] = chip_dict["boot"].get(
                "bootloaders"
            )
            partitions: Optional[List[str]] = chip_dict["boot"].get(
                "partitions"
            )
            bootswitches: Optional[List[str]] = chip_dict["boot"].get(
                "bootswitches"
            )
            default_bootloader_name = "bootloader.hex"
            if (bootloaders is not None) and (len(bootloaders) > 0):
                default_bootloader_name = bootloaders[0].split("/")[-1]
            default_partitions_name = "partitions.csv"
            if (partitions is not None) and (len(partitions) > 0):
                default_partitions_name = partitions[0].split("/")[-1]
            default_bootswitches_name = "bootswitch.bin"
            if (bootswitches is not None) and (len(bootswitches) > 0):
                default_bootswitches_name = bootswitches[0].split("/")[-1]
            relpath = relpath.replace("{bootloader}", default_bootloader_name)
            relpath = relpath.replace("{bootswitch}", default_bootswitches_name)
            relpath = relpath.replace(
                "{partitions_csv}", default_partitions_name
            )

        # $ Return obtained relpath
        return relpath
