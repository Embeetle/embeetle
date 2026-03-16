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
import weakref
import qt
import components.decorators as _dec_

if TYPE_CHECKING:
    import tree_widget.chassis.chassis as _chassis_


class ChassisHead(qt.QFrame):
    def __init__(
        self,
        chassis: _chassis_.Chassis,
        tabname: str = "default",
    ) -> None:
        """The ChassisHead() belongs to a specific 'tabname'."""
        super().__init__()
        self._chassisRef: weakref.ReferenceType[_chassis_.Chassis] = (
            weakref.ref(chassis)
        )
        self.__tabname = tabname
        return

    @_dec_.ref
    def get_chassis(self) -> _chassis_.Chassis:
        return self._chassisRef  # type: ignore

    def get_tabname(self) -> str:
        return self.__tabname

    def set_tabname(self, tabname: str) -> None:
        self.__tabname = tabname
        return

    def show_activate_banner(self) -> None:
        """"""
        raise NotImplementedError()

    def hide_activate_banner(self) -> None:
        """"""
        raise NotImplementedError()

    def head_self_destruct(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Kill all GUI elements from this ChassisHead()-instance and delete all
        the attributes.

        Must be implemented in subclass.
        """
        raise NotImplementedError()
