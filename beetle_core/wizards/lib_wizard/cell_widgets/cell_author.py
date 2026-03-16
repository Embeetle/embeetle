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
import wizards.lib_wizard.cell_widgets.cell_widget as _cell_widget_

if TYPE_CHECKING:
    import qt
    import libmanager.libobj as _libobj_


class AuthorLabel(_cell_widget_.CellLabel):
    """"""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        gridlyt: qt.QGridLayout,
        parent: qt.QFrame,
        minwidth: int,
        maxwidth: int,
    ) -> None:
        """"""
        super().__init__(
            row=row,
            col=col,
            libobj=libobj,
            text=libobj.get_mod_author(),
            gridlyt=gridlyt,
            parent=parent,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        # self.destroyed.connect(lambda: print(f"[{libname}] destroyed col 1"))
        return

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill AuthorLabel() twice!")
            self.dead = True

        _cell_widget_.CellLabel.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
