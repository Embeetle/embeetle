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

# ^                                       ADVANCED_LINE_EDIT                                       ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class AdvancedLineEdit(qt.QStackedWidget):
    """
    GOAL:
    =====
    This AdvancedLineEdit() class should behave like a real QLineEdit(). The only difference is that
    the AdvancedLineEdit() will resize itself according to the content, while an ordinary QLine-
    Edit() can hide part of the content.

    INTERNAL MECHANISM:
    ===================
    The AdvancedLineEdit() widget is actually a QStackedWidget() with two widgets inside:
        - a QLineEdit()
        - a QLabel()
    The QLabel() is shown by default. A QLabel() resizes itself according to its content. When
    clicked, the QLineEdit() is shown instead. The user can enter text and return to the QLabel()
    view when he presses enter or the widget loses focus.
    """

    clicked_sig = qt.pyqtSignal()
    enter_sig = qt.pyqtSignal()
    leave_sig = qt.pyqtSignal()
    returnPressed = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(parent)
        self.dead = False
        super().setStyleSheet(
            """
            QStackedWidget{
                color: transparent;
                background-color: transparent;
                border: none;
            }
        """
        )
        # Stick to the QLabel() view if not enabled.
        self.__is_enabled: bool = True
        self.__is_readonly: bool = False
        self.__stylesheet: Optional[str] = None

        # * QLineEdit()
        self.__lineedit: Optional[SpecialLineEdit] = SpecialLineEdit(self)
        # $ Relay signals
        self.__lineedit.clicked_sig.connect(self.clicked_sig)
        self.__lineedit.enter_sig.connect(self.enter_sig)
        self.__lineedit.leave_sig.connect(self.leave_sig)
        self.__lineedit.returnPressed.connect(self.returnPressed)  # type: ignore
        # $ Internal signal uses
        self.__lineedit.returnPressed.connect(self.show_label)  # type: ignore
        self.__lineedit.focus_out_sig.connect(self.show_label)

        # * QLabel()
        self.__lbl: Optional[SpecialLabel] = SpecialLabel(self)
        # $ Relay signals
        self.__lbl.clicked_sig.connect(self.clicked_sig)
        self.__lbl.enter_sig.connect(self.enter_sig)
        self.__lbl.leave_sig.connect(self.leave_sig)
        # $ Internal signal uses
        self.__lbl.clicked_sig.connect(self.show_lineedit)
        self.__lbl.focus_in_sig.connect(self.show_lineedit)

        self.addWidget(self.__lbl)
        self.addWidget(self.__lineedit)
        self.show_label()
        return

    @qt.pyqtSlot()
    def show_label(self) -> None:
        """Bring the QLabel() widget to the foreground."""
        self.__lbl.setText(self.__lineedit.text())
        self.setCurrentIndex(0)
        return

    @qt.pyqtSlot()
    def show_lineedit(self) -> None:
        """Bring the QLineEdit() widget to the foreground."""
        if self.__is_enabled and not self.__is_readonly:
            self.setCurrentIndex(1)
        return

    def setEnabled(self, en: bool) -> None:
        """Bring the QLabel() widget to the foreground and stick to it.

        Also grey out the text.
        """
        self.__is_enabled = en
        if not en:
            self.show_label()
        self.setStyleSheet()
        self.__lineedit.style().unpolish(self.__lineedit)
        self.__lineedit.style().polish(self.__lineedit)
        self.__lineedit.update()
        self.__lbl.style().unpolish(self.__lbl)
        self.__lbl.style().polish(self.__lbl)
        self.__lbl.update()
        return

    def setReadOnly(self, ro: bool) -> None:
        """Bring the QLabel() widget to the foreground and stick to it.

        Don't grey out the text (unless setEnabled(False) has been applied).
        """
        self.__is_readonly = ro
        if ro:
            self.show_label()
        return

    def isReadonly(self) -> bool:
        """True if QLineEdit() is readonly."""
        return self.__is_readonly

    def isEnabled(self) -> bool:
        """True if QLineEdit() is editable(*) and not greyed out.

        (*) Unless readonly is set.
        """
        return self.__is_enabled

    def text(self) -> str:
        """Return text in the QLineEdit()."""
        return self.__lineedit.text()

    def setText(self, text: str) -> None:
        """Set text in the QLineEdit()."""
        self.__lineedit.setText(text)
        self.__lbl.setText(text)
        return

    def setStyleSheet(self, stylesheet: Optional[str] = None) -> None:
        """Write your stylesheet as if it were for an ordinary QLineEdit()."""
        if stylesheet is not None:
            self.__stylesheet = stylesheet
        stylestr = self.__stylesheet
        assert isinstance(stylestr, str)
        if not self.__is_enabled:
            # Turn black in grey
            stylestr = stylestr.replace("#000000", "#babdb6")
            stylestr = stylestr.replace("#ff000000", "#babdb6")
            stylestr = stylestr.replace("#2e3436", "#babdb6")
            stylestr = stylestr.replace("#ff2e3436", "#babdb6")
        self.__lineedit.setStyleSheet(stylestr.replace("#ffffff", "#eeeeec"))
        self.__lbl.setStyleSheet(stylestr.replace("QLineEdit", "QLabel"))
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        """"""
        self.show_lineedit()
        self.__lineedit.setFocus()
        # $ Mouse clicks are already handled by either the QLabel() or the
        # $ QLineEdit(). No need to fire the 'clicked_sig' here!
        # self.clicked_sig.emit()
        # $ To be investigated if this is needed:
        # super().mousePressEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusInEvent(self, e: qt.QFocusEvent) -> None:
        """"""
        self.show_lineedit()
        self.__lineedit.setFocus()
        # $ To be investigated if this is needed:
        # super().focusInEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusOutEvent(self, e: qt.QFocusEvent) -> None:
        """"""
        self.show_label()
        self.__lbl.setFocus()
        # $ To be investigated if this is needed:
        # super().focusOutEvent(e)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill AdvancedLineEdit() twice!")
            self.dead = True

        for sig in (
            self.clicked_sig,
            self.enter_sig,
            self.leave_sig,
            self.returnPressed,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # Kill lineedit and lbl
        self.__lineedit.self_destruct()
        self.__lbl.self_destruct()
        self.removeWidget(self.__lbl)
        self.removeWidget(self.__lineedit)
        self.__lineedit.setParent(None)  # type: ignore
        self.__lbl.setParent(None)  # type: ignore
        self.__lbl = None
        self.__lineedit = None

        # Kill other variables
        # self.__is_enabled = None
        # self.__is_readonly = None
        self.__stylesheet = None

        # Deparent
        self.setParent(None)  # noqa
        return


# ^                                         SPECIAL_LABEL                                          ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class SpecialLabel(qt.QLabel):
    """A slightly modified QLabel() to be used in the AdvancedLineEdit()
    class."""

    clicked_sig = qt.pyqtSignal()
    focus_in_sig = qt.pyqtSignal()
    focus_out_sig = qt.pyqtSignal()
    enter_sig = qt.pyqtSignal()
    leave_sig = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        self.clicked_sig.emit()
        super().mousePressEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusInEvent(self, e: qt.QFocusEvent) -> None:
        self.focus_in_sig.emit()
        super().focusInEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusOutEvent(self, e: qt.QFocusEvent) -> None:
        self.focus_out_sig.emit()
        super().focusOutEvent(e)
        return

    @qt.pyqtSlot(qt.QEvent)
    def enterEvent(self, e: qt.QEnterEvent) -> None:
        self.enter_sig.emit()
        super().enterEvent(e)
        return

    @qt.pyqtSlot(qt.QEvent)
    def leaveEvent(self, e: qt.QEvent) -> None:
        self.leave_sig.emit()
        super().leaveEvent(e)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError("Trying to kill SpecialLabel() twice!")
            self.__dead = True
        for sig in (
            self.clicked_sig,
            self.focus_in_sig,
            self.focus_out_sig,
            self.enter_sig,
            self.leave_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass
        self.setParent(None)  # noqa
        return


# ^                                       SPECIAL_LINE_EDIT                                        ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class SpecialLineEdit(qt.QLineEdit):
    """A slightly modified QLineEdit() to be used in the AdvancedLineEdit()
    class."""

    focus_in_sig = qt.pyqtSignal()
    focus_out_sig = qt.pyqtSignal()
    enter_sig = qt.pyqtSignal()
    leave_sig = qt.pyqtSignal()
    clicked_sig = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        super().__init__(parent)
        self.__dead = False
        return

    @qt.pyqtSlot(qt.QMouseEvent)
    def mousePressEvent(self, e: qt.QMouseEvent) -> None:
        self.clicked_sig.emit()
        super().mousePressEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusInEvent(self, e: qt.QFocusEvent) -> None:
        self.focus_in_sig.emit()
        super().focusInEvent(e)
        return

    @qt.pyqtSlot(qt.QFocusEvent)
    def focusOutEvent(self, e: qt.QFocusEvent) -> None:
        self.focus_out_sig.emit()
        super().focusOutEvent(e)
        return

    @qt.pyqtSlot(qt.QEvent)
    def enterEvent(self, e: qt.QEnterEvent) -> None:
        self.enter_sig.emit()
        super().enterEvent(e)
        return

    @qt.pyqtSlot(qt.QEvent)
    def leaveEvent(self, e: qt.QEvent) -> None:
        self.leave_sig.emit()
        super().leaveEvent(e)
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.__dead:
                raise RuntimeError("Trying to kill SpecialLineEdit() twice!")
            self.__dead = True
        for sig in (
            self.focus_in_sig,
            self.focus_out_sig,
            self.enter_sig,
            self.leave_sig,
            self.clicked_sig,
        ):
            try:
                sig.disconnect()
            except:
                pass
        self.setParent(None)  # noqa
        return
