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
import wizards.lib_wizard.gen_widgets.linebox as _linebox_

if TYPE_CHECKING:
    import qt


class CheckLineBox(_linebox_.LineBox):
    """"""

    def __init__(
        self,
        parent: Optional[qt.QWidget] = None,
        thin: bool = True,
    ) -> None:
        """"""
        super().__init__(
            parent=parent,
            iconpath="icons/checkbox/checked.png",
            thin=thin,
        )
        self.__on: bool = False
        return

    def set_on(self, on: bool) -> None:
        """Set icon button checked/unchecked."""
        self.__on = on
        if on:
            self.set_icon("icons/checkbox/checked.png")
            return
        self.set_icon("icons/checkbox/grey.png")
        return

    def is_on(self) -> bool:
        """Is icon button checked?"""
        return self.__on

    def toggle(self) -> None:
        """Toggle the icon."""
        self.set_on(not self.__on)
        return

    def set_text(self, text: str) -> None:
        """Set text in the enclosed AdvancedLineEdit()"""
        self.get_lineedit().setText(text)

    def get_text(self) -> str:
        """Get text from the enclosed AdvancedLineEdit()"""
        return self.get_lineedit().text()

    def self_destruct(self, death_already_checked: bool = False) -> None:
        """"""
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill CheckLineBox() twice!")
            self.dead = True

        self.__on = None
        super().self_destruct(death_already_checked=True)
        return
