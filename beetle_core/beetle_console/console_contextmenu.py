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
import contextmenu.contextmenu as _contextmenu_

if TYPE_CHECKING:
    pass
nop = lambda *a, **k: None


class ConsoleBodyContextMenu(_contextmenu_.ContextMenuRoot):
    def __init__(
        self,
        toplvl_key: str,
        clickfunc: Callable,
    ) -> None:
        super().__init__(
            widg=None,
            item=None,
            toplvl_key=toplvl_key,
            clickfunc=clickfunc,
        )
        #! CLEAN CONSOLE
        menuClean = _contextmenu_.ContextMenuTopleaf(
            contextmenu_root=self,
            parent=self,
            text="Clean Console",
            key="clean",
            iconpath=f"icons/gen/clean.png",
        )
        self.add_child(menuClean)

        #! ABORT PROCESS
        menuAbort = _contextmenu_.ContextMenuTopleaf(
            contextmenu_root=self,
            parent=self,
            text="Abort Process",
            key="abort",
            iconpath=f"icons/dialog/stop.png",
        )
        self.add_child(menuAbort)
        self.addSeparator()

        # #! UNDO
        # menuUndo = _contextmenu_.ContextMenuTopleaf(
        #     contextmenu_root = self,
        #     parent           = self,
        #     text             = 'Undo         Ctrl+Z',
        #     key              = 'undo',
        #     iconpath         = f'icons/menu_edit/undo.png',
        # )
        # self.add_child(menuUndo)

        # #! REDO
        # menuRedo = _contextmenu_.ContextMenuTopleaf(
        #     contextmenu_root = self,
        #     parent           = self,
        #     text             = 'Redo         Ctrl+Y',
        #     key              = 'redo',
        #     iconpath         = f'icons/menu_edit/redo.png',
        # )
        # self.add_child(menuRedo)
        # self.addSeparator()

        # #! CUT
        # menuCut = _contextmenu_.ContextMenuTopleaf(
        #     contextmenu_root = self,
        #     parent           = self,
        #     text             = 'Cut          Ctrl+X',
        #     key              = 'cut',
        #     iconpath         = f'icons/menu_edit/line_cut.png',
        # )
        # self.add_child(menuCut)

        #! COPY
        menuCopy = _contextmenu_.ContextMenuTopleaf(
            contextmenu_root=self,
            parent=self,
            text="Copy         Ctrl+C",
            key="copy",
            iconpath=f"icons/menu_edit/line_copy.png",
        )
        self.add_child(menuCopy)

        #! PASTE
        menuPaste = _contextmenu_.ContextMenuTopleaf(
            contextmenu_root=self,
            parent=self,
            text="Paste        Ctrl+V",
            key="paste",
            iconpath=f"icons/menu_edit/line_paste.png",
        )
        self.add_child(menuPaste)

        # #! DELETE
        # menuDel = _contextmenu_.ContextMenuTopleaf(
        #     contextmenu_root = self,
        #     parent           = self,
        #     text             = 'Delete       Del',
        #     key              = 'delete',
        #     iconpath         = f'icons/menu_edit/line_delete.png',
        # )
        # self.add_child(menuDel)
        # self.addSeparator()

        #! SELECT ALL
        menuSelectAll = _contextmenu_.ContextMenuTopleaf(
            contextmenu_root=self,
            parent=self,
            text="Select All   Ctrl+A",
            key="select_all",
            iconpath=f"icons/menu_edit/select_all.png",
        )
        self.add_child(menuSelectAll)
        return
