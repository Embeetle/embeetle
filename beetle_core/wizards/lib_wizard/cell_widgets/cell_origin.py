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
import os
import qt, functions, gui, iconfunctions
import wizards.lib_wizard.cell_widgets.cell_widget as _cell_widget_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import libmanager.libobj as _libobj_
from various.kristofstuff import *


class OriginButton(_cell_widget_.CellButton):
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
            gridlyt=gridlyt,
            parent=parent,
            minwidth=minwidth,
            maxwidth=maxwidth,
            iconpath=None,
        )
        # * Sanitize input
        self.__locally_stored: bool = libobj.get_origin() == "local_abspath"
        self.__libpath: str = libobj.get_local_abspath()
        if self.__locally_stored:
            self.setIcon(
                iconfunctions.get_qicon("icons/folder/closed/folder.png")
            )
            self.setToolTip(self.__libpath)
        else:
            self.setIcon(iconfunctions.get_qicon("icons/gen/world.png"))
        # self.destroyed.connect(lambda: print(f"[{libname}] destroyed col 3"))
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        """We don't want to check the checkbox for this click, so we need to
        override this method."""
        if self.__locally_stored:
            self.setIcon(
                iconfunctions.get_qicon("icons/folder/open/folder.png")
            )
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mouseReleaseEvent(self, e: qt.QMouseEvent) -> None:
        """On a mouseclick => either open the existing library in a file
        explorer, or download it."""
        # * Open local folder
        if self.__locally_stored:
            self.setIcon(
                iconfunctions.get_qicon("icons/folder/closed/folder.png")
            )
            self.__open_library()
            return

        # * Open web url
        web_url = self.get_libobj().get_web_url()
        if (web_url is not None) and (web_url.lower() != "none"):
            functions.open_url(web_url)
        print(f"web_url = {web_url}")
        return

    def __open_library(self, *args) -> bool:
        """Open library referred to by leftmost neighbor."""
        assert self.__locally_stored
        if os.path.isfile(self.__libpath) or os.path.isdir(self.__libpath):
            success = functions.open_file_folder_in_explorer(self.__libpath)
            if success:
                return True
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="Problem",
                text=str(f"Failed to open:<br> " f"{q}{self.__libpath}{q}"),
            )
            return False
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/dialog/stop.png",
            title_text="Problem",
            text=str(
                f"The file/folder you look for doesn{q}t exist:<br> "
                f"{q}{self.__libpath}{q}"
            ),
        )
        return False

    def get_libpath(self) -> str:
        """Online library => None Offline library => Absolute path to library
        folder."""
        return self.__libpath

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill OriginButton() twice!")
            self.dead = True

        self.__locally_stored = None
        _cell_widget_.CellButton.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
