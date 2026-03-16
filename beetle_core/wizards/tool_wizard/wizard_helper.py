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
import wizards.tool_wizard.new_tool_wizard as _wiz_


def init_pages(self: _wiz_.NewToolWizard) -> None:
    """Initialize all pages."""
    self.main_groupbox = self.create_groupbox(
        text="",
        borderless=True,
        vertical="stack",
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    cast(qt.QStackedLayout, self.main_groupbox.layout()).setAlignment(
        qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
    )
    self.main_layout.addWidget(self.main_groupbox)

    #! Page 0
    self._groupbox_p0 = self.create_groupbox(
        text="",
        borderless=True,
        vertical=True,
        spacing=5,
        margins=(10, 15, 10, 10),
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    cast(qt.QVBoxLayout, self._groupbox_p0.layout()).setAlignment(
        qt.Qt.AlignmentFlag.AlignTop
    )
    cast(qt.QStackedLayout, self.main_groupbox.layout()).addWidget(
        self._groupbox_p0
    )

    #! Page 1
    self._groupbox_p1 = self.create_groupbox(
        text="",
        borderless=True,
        vertical=True,
        spacing=5,
        margins=(10, 15, 10, 10),
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    cast(qt.QVBoxLayout, self._groupbox_p1.layout()).setAlignment(
        qt.Qt.AlignmentFlag.AlignTop
    )
    cast(qt.QStackedLayout, self.main_groupbox.layout()).addWidget(
        self._groupbox_p1
    )

    #! Page 2
    self._groupbox_p2 = self.create_groupbox(
        text="",
        borderless=True,
        vertical=True,
        spacing=5,
        margins=(10, 15, 10, 10),
        h_size_policy=qt.QSizePolicy.Policy.Expanding,
        v_size_policy=qt.QSizePolicy.Policy.Expanding,
    )
    cast(qt.QVBoxLayout, self._groupbox_p2.layout()).setAlignment(
        qt.Qt.AlignmentFlag.AlignTop
    )
    cast(qt.QStackedLayout, self.main_groupbox.layout()).addWidget(
        self._groupbox_p2
    )
    cast(qt.QStackedLayout, self.main_groupbox.layout()).setCurrentIndex(0)
    return
