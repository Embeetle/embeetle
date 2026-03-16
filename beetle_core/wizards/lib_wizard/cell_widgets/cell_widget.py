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
from components.decorators import ref
import weakref
import qt, data, purefunctions, iconfunctions
import wizards.lib_wizard.lib_const as _lib_const_

if TYPE_CHECKING:
    import libmanager.libobj as _libobj_
from various.kristofstuff import *


class CellWidget(object):
    """Common implementation for custom widgets that are inserted into the
    library table."""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        gridlyt: qt.QGridLayout,
        minwidth: Optional[int],
        maxwidth: Optional[int],
    ) -> None:
        """"""
        self.dead: bool = False
        self.__row: int = row
        self.__col: int = col
        self.__libobj_ref = weakref.ref(libobj)
        self.__gridlyt_ref: weakref.ReferenceType[qt.QGridLayout] = weakref.ref(
            gridlyt
        )
        self.__minwidth: int = minwidth
        self.__maxwidth: int = maxwidth
        self.__neighbor_refs: List[weakref.ReferenceType[Any]] = []
        return

    @ref
    def get_libobj(self) -> _libobj_.LibObj:
        """
        :return:
        """
        return self.__libobj_ref  # type: ignore

    def fill_neighbors(self) -> None:
        """Fill a list with references to all the neighbor widgets left and
        right."""
        assert len(self.__neighbor_refs) == 0
        widgs = [
            self.__gridlyt_ref().itemAtPosition(self.__row, i)
            for i in range(_lib_const_.NR_OF_COLUMNS)
        ]
        for i, widg in enumerate(widgs):
            if (widg is None) or (qt.sip.isdeleted(widg)):
                purefunctions.printc(
                    f"WARNING: Cannot handle col = {i}",
                    color="warning",
                )
                continue
            w = widg.widget()
            self.__neighbor_refs.append(weakref.ref(w))
            continue
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        """Set 'darkblue' property True for all neighbors (self is also in the
        neighbor list)."""
        if self.__neighbor_refs is None:
            return
        if len(self.__neighbor_refs) == 0:
            self.fill_neighbors()
        for r in self.__neighbor_refs:
            w = r()
            if (w is None) or (qt.sip.isdeleted(w)):
                return
            if hasattr(w, "toggle"):
                w.toggle()
            w.setProperty("darkblue", True)
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()
        if e is not None:
            cast(qt.QWidget, super()).mousePressEvent(e)
        print(f"clicked on library {q}{self.get_libobj().get_name()}{q}")
        return

    @qt.pyqtSlot(qt.QEvent)
    def enterEvent(self, e: qt.QEnterEvent) -> None:
        """Set 'lightblue' property True for all neighbors (self is also in the
        neighbor list)."""
        if self.__neighbor_refs is None:
            return
        if len(self.__neighbor_refs) == 0:
            self.fill_neighbors()
        for r in self.__neighbor_refs:
            w = r()
            if (w is None) or (qt.sip.isdeleted(w)):
                return
            w.setProperty("lightblue", True)
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()
        if e is not None:
            cast(qt.QWidget, super()).enterEvent(e)
        return

    @qt.pyqtSlot(qt.QEvent)
    def leaveEvent(self, e: qt.QEvent) -> None:
        """Set 'lightblue' and 'darkblue' properties False for all neighbors
        (self is also in the neighbor list)."""
        if self.__neighbor_refs is None:
            return
        if len(self.__neighbor_refs) == 0:
            self.fill_neighbors()
        for r in self.__neighbor_refs:
            w = r()
            if (w is None) or (qt.sip.isdeleted(w)):
                return
            w.setProperty("lightblue", False)
            w.setProperty("darkblue", False)
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()
        if e is None:
            return
        cast(qt.QWidget, super()).leaveEvent(e)
        return

    def sizeHint(self) -> qt.QSize:
        """Apply the given 'minwidth' and 'maxwidth' parameters on the returned
        size hint.

        NOTE:
        This method is overridden in sub-sub-class ComboBoxVersionFrm(), because the Advanced-
        ComboBox() doesn't provide a sufficient size hint.
        """
        size = cast(qt.QWidget, super()).sizeHint()
        w = size.width()
        h = size.height()
        # Apply minimal width
        if self.__minwidth is not None:
            w = max(w, self.__minwidth)
        # Apply maximal width
        if self.__maxwidth is not None:
            w = min(w, self.__maxwidth)
        return qt.create_qsize(w, h)

    def get_row(self) -> int:
        return self.__row

    def get_col(self) -> int:
        return self.__col

    def get_libname(self) -> str:
        return self.__libobj_ref().get_name()

    def get_libversion(self) -> str:
        """Online library => Get currently selected libversion from the combobox
        widget.

        Offline library => Get the (constant) libversion.
        """
        if len(self.__neighbor_refs) == 0:
            self.fill_neighbors()
        r = self.__neighbor_refs[2]
        w = r()
        return w.get_libversion()

    def assign_new_libobj(self, new_libobj: _libobj_.LibObj) -> None:
        """Assign new libobj to oneself and all neighbors."""
        if self.__neighbor_refs is None:
            return
        if len(self.__neighbor_refs) == 0:
            self.fill_neighbors()
        for r in self.__neighbor_refs:
            w = r()
            if (w is None) or (qt.sip.isdeleted(w)):
                return
            w.accept_new_libobj(new_libobj)
        return

    def accept_new_libobj(self, new_libobj: _libobj_.LibObj) -> None:
        """Accept new libobj for oneself.

        Repoint the reference and make modifications if needed.
        """
        self.__libobj_ref = weakref.ref(new_libobj)
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
                raise RuntimeError(f"Trying to kill CellWidget() twice!")
            self.dead = True

        self.__row = None
        self.__col = None
        self.__libobj_ref = None
        self.__gridlyt_ref = None
        self.__minwidth = None
        self.__maxwidth = None
        self.__neighbor_refs = None
        try:
            self.hide()  # type: ignore
            self.setParent(None)  # type: ignore
            self.deleteLater()  # type: ignore
        except:
            # The 'self_destruct()' function from 'AdvancedComboBox()' already takes
            # care of deparenting and 'deleteLater()', so doing it twice might
            # cause this exception to fire.
            pass
        if callback is not None:
            callback(callbackArg)
        return


class CellFrm(CellWidget, qt.QFrame):
    """
    WARNING: This class doesn't provide the layout yet!
    """

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
        qt.QFrame.__init__(
            self,
            parent=parent,
        )
        CellWidget.__init__(
            self,
            row=row,
            col=col,
            libobj=libobj,
            gridlyt=gridlyt,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {data.theme['shade'][0]};
                border-left:   1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-top:    1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-right:  1px solid {_lib_const_.CELL_FRAME_COL};
                border-bottom: 1px solid {_lib_const_.CELL_FRAME_COL};
                padding: 0px;
                margin: 0px;
            }}
            QFrame[lightblue = true] {{
                background: {data.theme['indication']['hover']};
            }}
            """
        )
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
                raise RuntimeError(f"Trying to kill CellFrm() twice!")
            self.dead = True

        if self.layout().count() != 0:
            raise RuntimeError(
                "ERROR: failed to kill the widgets in the layout!"
            )
        # Delete own layout.
        self.layout().deleteLater()
        # Deparent and kill the self, happens
        # in the CellWidget.self_destruct() function.
        CellWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return


class CellLabel(CellWidget, qt.QLabel):
    """"""

    def __init__(
        self,
        row: int,
        col: int,
        libobj: _libobj_.LibObj,
        text: str,
        gridlyt: qt.QGridLayout,
        parent: qt.QFrame,
        minwidth: int,
        maxwidth: int,
    ) -> None:
        """"""
        qt.QLabel.__init__(
            self,
            parent=parent,
            text=text,
        )
        CellWidget.__init__(
            self,
            row=row,
            col=col,
            libobj=libobj,
            gridlyt=gridlyt,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {data.theme['shade'][0]};
                color: {data.theme['fonts']['default']['color']};
                border-left:   1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-top:    1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-right:  1px solid {_lib_const_.CELL_FRAME_COL};
                border-bottom: 1px solid {_lib_const_.CELL_FRAME_COL};
            }}
            QLabel[lightblue = true] {{
                background: {data.theme['indication']['hover']};
            }}
        """
        )
        super().setWordWrap(True)
        self.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.Preferred,
        )
        self.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
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
                raise RuntimeError(f"Trying to kill CellLabel() twice!")
            self.dead = True

        # Deparent and kill the self, happens in the CellWidget.self_destruct() function.
        CellWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return


class CellButton(CellWidget, qt.QPushButton):
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
        iconpath: Optional[str],
    ) -> None:
        """"""
        # $ Constructors
        qt.QPushButton.__init__(
            self,
            parent=parent,
        )
        CellWidget.__init__(
            self,
            row=row,
            col=col,
            libobj=libobj,
            gridlyt=gridlyt,
            minwidth=minwidth,
            maxwidth=maxwidth,
        )
        # $ Look and feel
        self.setMouseTracking(True)
        self.setStyleSheet(
            f"""
            QPushButton {{
                border-left:   1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-top:    1px solid {_lib_const_.CELL_FRAME_SHADOW};
                border-right:  1px solid {_lib_const_.CELL_FRAME_COL};
                border-bottom: 1px solid {_lib_const_.CELL_FRAME_COL};
                margin: 0px;
                padding: 0px;      
                background: {data.theme['shade'][0]};
            }}
            QPushButton[lightblue = true] {{
                background: {data.theme['indication']['hover']};
            }}
        """
        )
        size = data.get_libtable_icon_pixelsize()
        self.setIconSize(qt.create_qsize(size, size))
        self.setSizePolicy(
            qt.QSizePolicy.Policy.MinimumExpanding,
            qt.QSizePolicy.Policy.MinimumExpanding,
        )
        # $ Icon
        if iconpath is not None:
            self.setIcon(iconfunctions.get_qicon(iconpath))
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
                raise RuntimeError(f"Trying to kill CellButton() twice!")
            self.dead = True

        # Deparent and kill the self. That happens in the CellWidget.self_destruct() function.
        CellWidget.self_destruct(
            self,
            callback=callback,
            callbackArg=callbackArg,
            death_already_checked=True,
        )
        return
