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
import qt, data, functions, iconfunctions
import wizards.lib_wizard.cell_widgets.cell_widget as _cell_widget_
import libmanager.libmanager as _libmanager_

if TYPE_CHECKING:
    import libmanager.libobj as _libobj_


class NameFrm(_cell_widget_.CellFrm):
    """"""

    row_checked_sig = qt.pyqtSignal(int, str)
    row_cleared_sig = qt.pyqtSignal(int, str)

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
        )
        self.__lyt = qt.QHBoxLayout(self)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setSpacing(0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        size = int(0.8 * data.get_libtable_icon_pixelsize())

        # * Checkbox
        self.__checked = False
        self.__checkbox = qt.QPushButton(self)
        self.__checkbox.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """
        )

        self.__checkbox.setIconSize(qt.create_qsize(size, size))
        self.__checkbox.setFixedSize(size, size)
        self.__checkbox.clicked.connect(  # type: ignore
            lambda *args, **kwargs: self.mousePressEvent(None)  # type: ignore
        )
        self.clear()
        self.__lyt.addWidget(self.__checkbox)

        # * Name Label
        self.__namelbl = qt.QLabel(
            parent=self,
            text=libobj.get_mod_name(),
        )
        self.__namelbl.setWordWrap(True)
        self.__namelbl.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.Maximum,
        )
        d = int(size / 2)
        self.__namelbl.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                color: {data.theme['fonts']['default']['color']};
                border: none;
                margin: 0px;
                padding: 0px {d}px 0px {d}px;
            }}
        """
        )
        self.__lyt.addWidget(self.__namelbl)
        return

    def toggle(self) -> None:
        """Emit signal with a request to check or clear the checkbox."""
        if self.__checked:
            # Request to clear
            self.row_cleared_sig.emit(
                self.get_row(),
                self.get_libobj().get_name(),
            )
        else:
            # Request to check
            self.row_checked_sig.emit(
                self.get_row(),
                self.get_libobj().get_name(),
            )
        return

    def clear(self, just_downloaded: bool = False) -> None:
        """
        :param just_downloaded: If True, the checkbox will be as if the library
                                already exists in the project.

        TODO: Check if given library already exists in project
        """
        self.__checked = False
        if just_downloaded:
            self.__checkbox.setIcon(
                iconfunctions.get_qicon("icons/include_chbx/c_files/green.png")
            )
            return
        # $ HOME WINDOW
        if data.is_home:
            cache_libs = _libmanager_.LibManager().list_cached_libs_names()
            if cache_libs is not None:
                if self.get_libobj().get_name() in cache_libs:
                    self.__checkbox.setIcon(
                        iconfunctions.get_qicon(
                            "icons/include_chbx/c_files/green.png"
                        )
                    )
                    return
        # $ PROJECT WINDOW
        else:
            proj_libs = _libmanager_.LibManager().list_proj_libs_names()
            if proj_libs is not None:
                if self.get_libobj().get_name() in proj_libs:
                    self.__checkbox.setIcon(
                        iconfunctions.get_qicon(
                            "icons/include_chbx/c_files/green.png"
                        )
                    )
                    return
        # $ LIB NOT FOUND
        # The library wasn't found in the project (project mode) or in the cache
        # (home mode).
        self.__checkbox.setIcon(
            iconfunctions.get_qicon("icons/checkbox/grey.png")
        )
        return

    def check(self) -> None:
        """"""
        self.__checked = True
        self.__checkbox.setIcon(
            iconfunctions.get_qicon("icons/checkbox/checked.png")
        )
        return

    def is_checked(self) -> bool:
        """"""
        return self.__checked

    def self_destruct(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
        death_already_checked: bool = False,
    ) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill NameFrm() twice!")
            self.dead = True

        # $ Disconnect signals
        for sig in (
            self.row_checked_sig,
            self.row_cleared_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        self.__lyt.removeWidget(self.__checkbox)
        self.__lyt.removeWidget(self.__namelbl)

        # $ Kill and deparent children
        self.__checkbox.setParent(None)  # noqa
        self.__namelbl.setParent(None)  # noqa

        # $ Kill leftovers
        functions.clean_layout(self.__lyt)

        # $ Reset variables
        self.__checkbox = None
        self.__namelbl = None
        self.__lyt = None
        super().self_destruct(
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
