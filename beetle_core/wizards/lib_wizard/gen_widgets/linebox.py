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
import gui.helpers.advancedlineedit as _advancedlineedit_
import gui.stylesheets.button as _btn_style_

if TYPE_CHECKING:
    pass


class LineBox(qt.QFrame):
    """┌── self [QFrame()] ──────────────────────────────────┐ │ ┌───┐
    ┌─────────────────────────────────────────┐  │ │ └───┘
    └─────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────┘

    QFrame() container class to hold a QPushButton() and a QLineEdit().
    """

    btn_clicked_sig = qt.pyqtSignal()
    lineedit_clicked_sig = qt.pyqtSignal()
    lineedit_return_pressed_sig = qt.pyqtSignal()
    lineedit_tab_pressed_sig = qt.pyqtSignal()

    def __init__(
        self,
        parent: qt.QWidget,
        iconpath: str,
        thin: bool,
    ) -> None:
        """"""
        super().__init__(parent)
        self.dead = False

        # & QFrame() style
        self.setStyleSheet(
            """
            QFrame{
                background-color: transparent;
                border: none;
            }    
        """
        )
        self.setContentsMargins(0, 0, 0, 0)

        # & Layout
        self.__lyt = qt.QHBoxLayout(self)
        self.__lyt.setContentsMargins(0, 0, 0, 0)
        self.__lyt.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.__lyt.setSpacing(0)

        # & QPushButton()
        size = data.get_libtable_icon_pixelsize()
        if thin:
            size = int(0.8 * size)
        self.__icon_btn: qt.QPushButton = qt.QPushButton(self)
        self.__icon_btn.setStyleSheet(_btn_style_.get_btn_stylesheet())
        self.__icon_btn.setFixedSize(size, size)
        self.__icon_btn.setIconSize(qt.create_qsize(size, size))
        self.__icon_btn.setIcon(iconfunctions.get_qicon(iconpath))
        self.__icon_btn.clicked.connect(self.btn_clicked_sig)  # type: ignore

        # & LineEdit()
        self.__lineedit: Optional[Union[LineEdit, ThinLineEdit]] = None
        if thin:
            self.__lineedit = ThinLineEdit(parent)
        else:
            self.__lineedit = LineEdit(parent)
        self.__lineedit.clicked_sig.connect(self.lineedit_clicked_sig)
        self.__lineedit.return_pressed_sig.connect(
            self.lineedit_return_pressed_sig
        )
        self.__lineedit.tab_pressed_sig.connect(self.lineedit_tab_pressed_sig)

        # & Add to layout
        self.__lyt.addWidget(self.__icon_btn)
        self.__lyt.addSpacing(5)
        self.__lyt.addWidget(self.__lineedit)
        return

    def get_text(self) -> str:
        return self.__lineedit.text()

    def get_lineedit(self) -> Union[ThinLineEdit, LineEdit]:
        return self.__lineedit

    def set_icon(self, iconpath: str) -> None:
        self.__icon_btn.setIcon(iconfunctions.get_qicon(iconpath))
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill LineBox() twice!")
            self.dead = True

        # $ Disconnect signals
        for sig in (
            self.btn_clicked_sig,
            self.lineedit_clicked_sig,
            self.lineedit_return_pressed_sig,
            self.lineedit_tab_pressed_sig,
            self.__icon_btn.clicked,
        ):
            # Signals from 'self.__lineedit' don't need to be disconnected here, because that hap-
            # pens already in its self_destruct() method.
            try:
                sig.disconnect()  # type: ignore
            except:
                pass

        # $ Remove child widgets
        self.__lyt.removeWidget(self.__icon_btn)
        self.__lyt.removeWidget(self.__lineedit)

        # $ Kill and deparent children
        self.__icon_btn.setParent(None)  # noqa
        self.__lineedit.self_destruct()

        # $ Kill leftovers
        functions.clean_layout(self.__lyt)

        # $ Reset variables
        self.__lyt = None
        self.__icon_btn = None
        self.__lineedit = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return


class KeyPressEater(qt.QObject):
    """"""

    tab_pressed_sig = qt.pyqtSignal()

    def __init__(self) -> None:
        """"""
        super().__init__()
        self.__dead = False
        return

    def eventFilter(self, obj: qt.QObject, e: qt.QEvent) -> bool:
        """"""
        if e.type() == qt.QEvent.Type.KeyPress:
            assert isinstance(e, qt.QKeyEvent)
            if e.key() == qt.Qt.Key.Key_Tab:
                self.tab_pressed_sig.emit()
                return True
        return super().eventFilter(obj, e)

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill KeyPressEater() twice!")
            self.__dead = True

        try:
            self.tab_pressed_sig.disconnect()
        except:
            pass
        # Deparenting is not applicable here
        return


class LineEdit(qt.QLineEdit):
    """Used for the filter boxes."""

    return_pressed_sig = qt.pyqtSignal()
    tab_pressed_sig = qt.pyqtSignal()
    clicked_sig = qt.pyqtSignal()

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        size = data.get_libtable_icon_pixelsize()
        self.setMinimumHeight(size)
        text_default_color = data.theme["fonts"]["default"]["color"]
        self.setStyleSheet(
            f"""
            QLineEdit{{
                color: {text_default_color};
                background-color: transparent;
                border-color: #9ebdde;
                border-width: 1px;
                border-style: solid;
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize()}pt;
            }}
        """
        )
        self.setContentsMargins(0, 0, 0, 0)

        # * Relay signals
        self.returnPressed.connect(self.return_pressed_sig)  # type: ignore
        self.__my_eater: KeyPressEater = KeyPressEater()
        self.installEventFilter(cast(qt.QObject, self.__my_eater))
        self.__my_eater.tab_pressed_sig.connect(self.tab_pressed_sig)
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        """"""
        self.clicked_sig.emit()
        super().mousePressEvent(e)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError(f"Trying to kill LineEdit() twice!")
            self.__dead = True

        # $ Disconnect signals
        self.__my_eater.self_destruct()
        for sig in (
            self.return_pressed_sig,
            self.tab_pressed_sig,
            self.clicked_sig,
            self.returnPressed,
        ):
            try:
                sig.disconnect()  # type: ignore
            except:
                pass

        # $ Remove child widgets
        # There are no child widgets

        # $ Kill and deparent children
        # There are no child widgets

        # $ Kill leftovers
        # Not applicable

        # $ Reset variables
        self.__my_eater = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return


class ThinLineEdit(_advancedlineedit_.AdvancedLineEdit):
    """Used for the searchpath boxes."""

    return_pressed_sig = qt.pyqtSignal()
    tab_pressed_sig = qt.pyqtSignal()

    def __init__(self, parent: qt.QWidget) -> None:
        """"""
        super().__init__(parent)
        size = data.get_libtable_icon_pixelsize()
        size = int(0.8 * size)
        self.setFixedHeight(size)
        text_default_color = data.theme["fonts"]["default"]["color"]
        text_green_color = data.theme["fonts"]["green"]["color"]
        self.setStyleSheet(
            f"""
            QLineEdit {{
                color: {text_default_color};
                background-color: transparent;
                border: none;
                font-family: {data.get_global_font_family()};
                font-size: {data.get_general_font_pointsize()}pt;
            }}
            QLineEdit:hover {{
                color: {text_green_color};
            }}
        """
        )

        # * Relay signals
        self.returnPressed.connect(self.return_pressed_sig)
        self.__my_eater = KeyPressEater()
        self.installEventFilter(self.__my_eater)
        self.__my_eater.tab_pressed_sig.connect(self.tab_pressed_sig)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill ThinLineEdit() twice!")
            self.dead = True

        # $ Disconnect signals
        self.__my_eater.self_destruct()
        for sig in (
            self.return_pressed_sig,
            self.tab_pressed_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Remove child widgets
        # There are no child widgets

        # $ Kill and deparent children
        # There are no child widgets

        # $ Kill leftovers
        # Not applicable

        # $ Reset variables
        self.__my_eater = None

        # $ Deparent oneself
        super().self_destruct(death_already_checked=True)
        return
