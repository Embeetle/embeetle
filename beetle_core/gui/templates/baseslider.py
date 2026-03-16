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

from typing import *
import qt
import gui
import gui.stylesheets

if TYPE_CHECKING:
    import gui.stylesheets.slider


# `BaseSlider` seems to be not in use right now
class BaseSlider(qt.QSlider):
    changed = qt.pyqtSignal(int)
    __value = 0

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        self.setStyleSheet(gui.stylesheets.slider.get_styled())
        self.sliderMoved.connect(self.__slider_moved)
        return

    def __slider_moved(self, value) -> None:
        """"""
        self.__value = value
        return

    def mouseReleaseEvent(self, event) -> None:
        """"""
        super().mouseReleaseEvent(event)
        self.changed.emit(self.__value)
        return


class TickedSlider(qt.QSlider):
    changed = qt.pyqtSignal(int)
    __value = 0

    def __init__(self, *args, **kwargs) -> None:
        """"""
        units_per_tick: int = kwargs.pop("units_per_tick", 10)
        super().__init__(*args, **kwargs)
        self.setStyleSheet(gui.stylesheets.slider.get_styled_ticked())
        # Setting tick interval and tick position
        self.setTickInterval(units_per_tick)
        self.setTickPosition(qt.QSlider.TickPosition.TicksBelow)
        self.setSingleStep(units_per_tick)

        # Connecting to sliderMoved signal
        self.sliderMoved.connect(self.__slider_moved)
        return

    def __slider_moved(self, value) -> None:
        """"""
        # Snap to nearest tick value
        snapped_value = round(value / self.tickInterval()) * self.tickInterval()
        self.setValue(snapped_value)
        self.__value = snapped_value
        return

    def mouseReleaseEvent(self, event) -> None:
        """"""
        super().mouseReleaseEvent(event)
        self.changed.emit(self.__value)
        return
