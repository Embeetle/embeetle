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
import data
import contextmenu.contextmenu as _contextmenu_
import project.segments.chip_seg.chip as _chip_
import hardware_api.chip_unicum as _chip_unicum_
import gui.stylesheets.menu as popupStyle

if TYPE_CHECKING:
    import dashboard.items.chip_items.chip_items as _chip_items_
from various.kristofstuff import *


class MemsectionContextMenu(_contextmenu_.ContextMenuLeaf):
    def __init__(
        self,
        contextmenu_root: _contextmenu_.ContextMenuRoot,
        parent: _contextmenu_.ContextMenuNode,
        text: str,
        key: str,
        iconpath: Optional[str],
    ) -> None:
        """"""
        super().__init__(
            contextmenu_root,
            parent,
            text,
            key,
            iconpath,
        )
        chip_memory_item: _chip_items_.ChipMemoryItem = cast(
            "_chip_items_.ChipMemoryItem",
            self.get_item(),
        )
        memregion: _chip_.MemRegion = chip_memory_item.get_projSegment()
        assert isinstance(memregion, _chip_.MemRegion)
        if memregion.get_memtype() is _chip_unicum_.MEMTYPE.RAM:
            (
                self._lbl.setStyleSheet(
                    popupStyle.get_menuFileLbl_stylesheet(
                        color=data.theme["fonts"]["green"]["color"]
                    )
                )
                if self._lbl is not None
                else nop()
            )
        else:
            assert memregion.get_memtype() is _chip_unicum_.MEMTYPE.FLASH
            (
                self._lbl.setStyleSheet(
                    popupStyle.get_menuFileLbl_stylesheet(
                        color=data.theme["fonts"]["red"]["color"]
                    )
                )
                if self._lbl is not None
                else nop()
            )
        return
