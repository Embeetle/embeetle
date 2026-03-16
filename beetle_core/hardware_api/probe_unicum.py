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
from components.singleton import Unicum
import hardware_api.hardware_api as _hardware_api_
import hardware_api.segment_unicum as _segment_unicum_

if TYPE_CHECKING:
    pass


class PROBE(_segment_unicum_.SEGMENT, metaclass=Unicum):
    @classmethod
    def get_unicum_from_name(cls, name: str) -> Optional[PROBE]:
        """"""
        return PROBE(name)

    def __init__(self, name: str) -> None:
        """Create/get a PROBE()-instance with the given name. If the instance
        already exists somewhere, it won't be recreated. You'll get the
        'pointer' to the existing one. (see @Unicum)

        NOTE:
        Name 'none' accepted.
        """
        self._name_ = _hardware_api_.HardwareDB().standardize_probe_name(name)
        return

    def get_name(self) -> str:
        """"""
        return self._name_

    def get_probe_dict(self) -> Dict[str, Any]:
        """"""
        return _hardware_api_.HardwareDB().get_probe_dict(self._name_)


class TRANSPORT_PROTOCOL(_segment_unicum_.SEGMENT, metaclass=Unicum):
    @classmethod
    def get_unicum_from_name(cls, name: str) -> Optional[TRANSPORT_PROTOCOL]:
        """"""
        return TRANSPORT_PROTOCOL(name)

    def __init__(self, name: str) -> None:
        """Create/get a TRANSPORT_PROTOCOL()-instance with the given name. If
        the instance already.

        exists somewhere, it won't be recreated. You'll get the 'pointer' to the existing one. (see
        @Unicum)
        """
        self._name_ = _hardware_api_.HardwareDB().standardize_tp_name(name)
        return

    def get_name(self) -> str:
        """"""
        return self._name_
