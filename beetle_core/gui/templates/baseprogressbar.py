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
import os, weakref
import qt
import data
import functions
import gui
import gui.stylesheets.progressbar
import functools


class BaseProgressBar(qt.QProgressBar):
    all_references = []

    @classmethod
    def add_ref(cls, progbar: BaseProgressBar) -> None:
        """"""
        cls.all_references.append(weakref.ref(progbar))
        return

    @classmethod
    def remove_ref(cls, progbar: BaseProgressBar) -> None:
        """"""
        for ref in cls.all_references:
            if ref() is progbar:
                cls.all_references.remove(ref)
                return
        return

    @classmethod
    def get_ref_iter(cls) -> Iterator[BaseProgressBar]:
        """"""
        return [ref() for ref in cls.all_references if ref() is not None]

    """
    Overridden functions
    """

    def __init__(
        self,
        color: str,
        parent: Optional[qt.QWidget] = None,
        height: Optional[int] = None,
        thin: bool = False,
        faded: bool = True,
    ) -> None:
        """Get basic progressbar.

        :param color: One of these: ['blue', 'yellow', 'orange', 'green',
            'gray'].
        :param parent: A QWidget, gets passed on to QProgressBar().
        :param height: Fixed height for this progressbar. If None, value will be
            'data.get_general_font_pointsize()'.
        :param thin: If True, the stylesheet gets adapted for an extra thin
            progressbar.
        """
        super().__init__(parent)
        BaseProgressBar.add_ref(self)
        self.dead = False
        self.__color = color
        self.__height = height
        self.__thin = thin
        self.__faded = faded
        return

    def setColor(self, color: str) -> None:
        self.__color = color
        return

    def setValue(self, value: int) -> None:
        super().setValue(value)
        return

    def setMinimum(self, minimum: int) -> None:
        super().setMinimum(minimum)
        self.choose_style()
        return

    def setMaximum(self, maximum: int) -> None:
        super().setMaximum(maximum)
        self.choose_style()
        return

    def showEvent(self, event: qt.QShowEvent) -> None:
        super().showEvent(event)
        self.restyle()
        return

    """
    Custom functionality
    """

    def choose_style(self) -> None:
        """"""
        minimum = self.minimum()
        maximum = self.maximum()
        if minimum == maximum:
            if self.__faded:
                if self.__thin:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_faded_thin_style(
                            self.__color
                        )
                    )
                else:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_faded_style(
                            self.__color
                        )
                    )
            else:
                if self.__thin:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_unfaded_thin_style(
                            self.__color
                        )
                    )
                else:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_unfaded_style(
                            self.__color
                        )
                    )
        else:
            if self.__faded:
                if self.__thin:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_unfaded_thin_style(
                            self.__color
                        )
                    )
                else:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_faded_style(
                            self.__color
                        )
                    )
            else:
                if self.__thin:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_unfaded_thin_style(
                            self.__color
                        )
                    )
                else:
                    self.setStyleSheet(
                        gui.stylesheets.progressbar.get_unfaded_style(
                            self.__color
                        )
                    )
        return

    def restyle(self) -> None:
        """"""
        if self.__height is None:
            height = data.get_progressbar_zoom_pixelsize()
        else:
            height = self.__height
        #        # Qt bug, smaller size paint the waiting animation wrong
        #        if height < 14:
        #            height = 14
        self.setFixedHeight(int(height))
        self.choose_style()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        return

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError("Trying to kill BaseProgressBar() twice!")
            self.dead = True
        BaseProgressBar.remove_ref(self)

        # $ Disconnect signals
        # No signals

        # $ Remove child widgets
        # No child widgets

        # $ Kill and deparent children
        # No child widgets

        # $ Kill leftovers
        # Not applicable

        # $ Reset variables
        self.__color = None
        self.__height = None
        self.__thin = None
        self.__faded = None

        # $ Deparent oneself
        self.setParent(None)  # noqa
        return
