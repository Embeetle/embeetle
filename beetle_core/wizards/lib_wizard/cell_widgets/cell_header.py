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
import qt
import wizards.lib_wizard.lib_const as _lib_const_

if TYPE_CHECKING:
    pass


class HeaderLabel(qt.QLabel):
    """"""

    def __init__(
        self,
        parent: qt.QFrame,
        text: str,
    ) -> None:
        """"""
        qt.QLabel.__init__(
            self,
            parent=parent,
            text=text,
        )
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: #d3d7cf;
                color: #2e3436;
                font-weight: bold;
                border-left:   1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-top:    1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-right:  1px solid {_lib_const_.CELL_FRAME_COL};
                border-bottom: 1px solid {_lib_const_.CELL_FRAME_COL};
            }}
        """
        )
        self.setAlignment(qt.Qt.AlignmentFlag.AlignCenter)
        return
