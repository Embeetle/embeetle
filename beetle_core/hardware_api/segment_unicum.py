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


class SEGMENT(object):
    def get_name(self) -> str:
        """"""
        raise NotImplementedError()

    def __eq__(self, other: Any) -> bool:
        """Although SEGMENT()-instances are Unicum's, they should be compared by
        their (extended) names.

        The 'push()' and 'pop()' from the 'history.py' module still use the
        'copy.deepcopy()' function.
        """
        if other is None:
            return False
        if isinstance(other, str):
            if other.lower() == "none":
                return False
        if not isinstance(other, SEGMENT):
            raise ValueError(f"Cannot compare {self} to {other}")
        return (
            f"{self.get_name()}_{self.__class__}"
            == f"{other.get_name()}_{other.__class__}"
        )

    def __ne__(self, other: Any) -> bool:
        """Although SEGMENT()-instances are Unicum's, they should be compared by
        their (extended) names.

        The 'push()' and 'pop()' from the 'history.py' module still use the
        'copy.deepcopy()' function.
        """
        if other is None:
            return True
        if isinstance(other, str):
            if other.lower() == "none":
                return True
        if not isinstance(other, SEGMENT):
            raise ValueError(f"Cannot compare {self} to {other}")
        return (
            f"{self.get_name()}_{self.__class__}"
            != f"{other.get_name()}_{other.__class__}"
        )
