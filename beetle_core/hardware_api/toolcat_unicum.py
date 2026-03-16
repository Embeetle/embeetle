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
import purefunctions
from components.singleton import Unicum
import hardware_api.segment_unicum as _segment_unicum_
import fnmatch as _fn_
import hardware_api.hardware_api as _hardware_api_

if TYPE_CHECKING:
    pass
from various.kristofstuff import *


class TOOLCAT_UNIC(_segment_unicum_.SEGMENT, metaclass=Unicum):
    @classmethod
    def get_unicum_from_name(cls, name: str) -> Optional[TOOLCAT_UNIC]:
        """"""
        return TOOLCAT_UNIC(name)

    def __init__(self, name: str) -> None:
        """Create/get a TOOLCAT_UNIC()-instance with the given name:

            - 'COMPILER_TOOLCHAIN'
            - 'BUILD_AUTOMATION'
            - 'FLASHTOOL'
        If the instance already exists somewhere, it won't be recreated. You'll get the 'pointer' to
        the existing one (see @Unicum).
        """
        assert name.upper() in (
            "COMPILER_TOOLCHAIN",
            "BUILD_AUTOMATION",
            "FLASHTOOL",
        )
        self._name_ = _hardware_api_.HardwareDB().standardize_toolcat_name(name)
        return

    def get_name(self) -> str:
        """"""
        return self._name_

    def get_dict(self) -> Dict[str, Any]:
        """"""
        return _hardware_api_.HardwareDB().get_toolcat_dict(self._name_)

    def get_unique_id_iconpath(self, unique_id: str) -> str:
        """Given the unique_id, return the iconpath."""
        if unique_id is None:
            unique_id = "none"

        # $ Check for a match in the 'uid_pattern' from the correct tool category
        toolcat_dict = _hardware_api_.HardwareDB().get_toolcat_dict(self._name_)
        for p in toolcat_dict["uid_pattern"].keys():
            if _fn_.fnmatch(name=unique_id.lower(), pat=p):
                return toolcat_dict["uid_pattern"][p]["icon"]

        # $ No match
        purefunctions.printc(
            f"WARNING: TOOLCAT_UNIC({q}{self._name_}{q}).get_unique_id_iconpath({q}{unique_id}{q}) "
            f"failed!",
            color="warning",
        )
        return "icons/dialog/help.png"

    def get_unique_id_shortname(self, unique_id: str) -> str:
        """Extract a short name like 'OPENOCD' or 'OPENOCD GIGADEVICE' from the
        given unique ID.

        This is only used in the Home Window 'TOOLBOX' tab to list the different
        tools.
        """
        if unique_id is None:
            unique_id = "none"

        # $ Check for a match in the 'uid_pattern' from the correct tool category
        toolcat_dict = _hardware_api_.HardwareDB().get_toolcat_dict(self._name_)
        for p in toolcat_dict["uid_pattern"].keys():
            if _fn_.fnmatch(name=unique_id.lower(), pat=p):
                return toolcat_dict["uid_pattern"][p]["uid_shortname"]

        # $ No match
        purefunctions.printc(
            f"WARNING: TOOLCAT_UNIC({q}{self._name_}{q}).get_unique_id_shortname({q}{unique_id}{q}) "
            f"failed!",
            color="warning",
        )
        return "NONE"

    def get_flashtool_exename(self, unique_id: Optional[str]) -> str:
        """Extract the flashtool executable name (eg.

        'avrdude', 'openocd', ...) from the given unique
        ID. This can be done for flashtools, but not for compiler toolchains, where the toolprefixes
        can vary wildly.
        No '.exe' extension is given.
        """
        assert self._name_ == "FLASHTOOL"
        if unique_id is None:
            return "none"
        if "avrdude" in unique_id.lower():
            return "avrdude"
        if "bossac" in unique_id.lower():
            return "bossac"
        if "openocd" in unique_id.lower():
            return "openocd"
        if "esptool" in unique_id.lower():
            return "esptool"
        if "pymcuprog" in unique_id.lower():
            return "pymcuprog"
        if "wchisp" in unique_id.lower():
            return "wchisp"
        if "built-in" in unique_id.lower().replace("_", "-"):
            return "none"
        return unique_id.lower().replace("_", "-").split("-")[0]

    def get_relevant_treepaths(self, unique_id: str) -> List[str]:
        """Given the unique_id, return a list of relevant treepaths."""
        if unique_id is None:
            unique_id = "none"

        # $ Check for a match in the 'uid_pattern' from the correct tool category
        toolcat_dict = _hardware_api_.HardwareDB().get_toolcat_dict(self._name_)
        for p in toolcat_dict["uid_pattern"].keys():
            if _fn_.fnmatch(name=unique_id.lower(), pat=p):
                return toolcat_dict["uid_pattern"][p]["relevant_treepaths"]

        # $ No match
        purefunctions.printc(
            f"WARNING: TOOLCAT_UNIC({q}{self._name_}{q}).get_relevant_treepaths({q}{unique_id}{q}) "
            f"failed!",
            color="warning",
        )
        return []

    def get_default_unique_id(
        self,
        boardname: Optional[str],
        chipname: Optional[str],
        probename: Optional[str],
    ) -> Optional[str]:
        """"""
        chip_dict: Optional[Dict] = None
        probe_dict: Optional[Dict] = None
        if chipname is not None:
            chip_dict = _hardware_api_.HardwareDB().get_chip_dict(
                chipname, boardname
            )
        if probename is not None:
            probe_dict = _hardware_api_.HardwareDB().get_probe_dict(probename)

        # $ COMPILER_TOOLCHAIN
        if self._name_.upper() == "COMPILER_TOOLCHAIN":
            if chip_dict is not None:
                return chip_dict.get("default_compiler_uid")

        # $ FLASHTOOL
        if self._name_.upper() == "FLASHTOOL":
            if chip_dict is not None:
                return chip_dict.get("default_flashtool_uid")
            if probe_dict is not None:
                return probe_dict.get("default_flashtool_uid")

        # $ BUILD_AUTOMATION
        if self._name_.upper() == "BUILD_AUTOMATION":
            return "gnu_make_4.2.1_64b"

        return None
