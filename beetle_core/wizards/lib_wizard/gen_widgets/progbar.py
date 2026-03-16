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
import threading
import qt, data, purefunctions
import gui.templates.baseprogressbar as _baseprogressbar_
from typing import Optional


class TableProgbar(_baseprogressbar_.BaseProgressBar):
    """"""

    set_progbar_value_signal = qt.pyqtSignal()
    set_progbar_max_signal = qt.pyqtSignal()

    def __init__(self, parent: Optional[qt.QWidget] = None) -> None:
        """"""
        assert threading.current_thread() is threading.main_thread()
        height = min(data.get_general_icon_pixelsize(), 20)
        super().__init__(
            color="blue",
            parent=parent,
            height=height,
            thin=True,
            faded=False,
        )

        # $ Value and maximum
        self.__progbarval: int = 0
        self.__progbarmax: int = 100

        # $ Look and feel
        self.setTextVisible(False)
        # self.setFormat(f'loading: %v/%m')
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Expanding,
            qt.QSizePolicy.Policy.Fixed,
        )
        self.setMaximumWidth(height * 15)
        font: qt.QFont = self.font()
        font.setPixelSize(height - 4)
        self.setFont(font)

        # $ Signals
        self.set_progbar_value_signal.connect(self.set_progbar_value_slot)
        self.set_progbar_max_signal.connect(self.set_progbar_max_slot)
        return

    def set_progbar_value(self, value: int) -> None:
        """Save value, to be applied when signal hits slot."""
        if self.__progbarval == value:
            return
        self.__progbarval = value
        self.set_progbar_value_signal.emit()
        return

    def inc_progbar_value(self, value: int = 1) -> None:
        """Save incremented value, to be applied when signal hits slot."""
        self.__progbarval += value
        self.set_progbar_value_signal.emit()
        return

    @qt.pyqtSlot()
    def set_progbar_value_slot(self) -> None:
        """Apply saved value."""
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        if self.__progbarval > self.__progbarmax:
            purefunctions.printc(
                f"ERROR: PROGBAR has value "
                f"{self.__progbarval}/{self.__progbarmax}",
                color="error",
            )
            return
        self.setValue(self.__progbarval)
        return

    def set_progbar_max(self, maximum: int) -> None:
        """Save maximum, to be applied when signal hits slot."""
        if self.__progbarmax == maximum:
            return
        self.__progbarmax = maximum
        self.set_progbar_max_signal.emit()
        return

    @qt.pyqtSlot()
    def set_progbar_max_slot(self) -> None:
        """Apply saved maximum."""
        assert threading.current_thread() is threading.main_thread()
        if qt.sip.isdeleted(self):
            return
        if self.__progbarval > self.__progbarmax:
            print(
                f"ERROR: PROGBAR has value {self.__progbarval}/{self.__progbarmax}"
            )
            return
        self.setMaximum(self.__progbarmax)
        return

    def is_dead(self) -> bool:
        """"""
        return self.dead

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill TableProgbar() twice!")
            self.dead = True

        # $ Disconnect signals
        for sig in (
            self.set_progbar_value_signal,
            self.set_progbar_max_signal,
        ):
            try:
                sig.disconnect()
            except:
                pass

        # $ Other
        # All other actions happen in the parent method
        super().self_destruct(death_already_checked=True)
        return
