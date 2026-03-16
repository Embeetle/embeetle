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

# Standard library
from typing import *

# Local
import qt
import data
import gui.templates.widgetgenerator


class BaseBuilder(qt.QScrollArea):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Caches
        self.__widget_cache: Dict[str, Any] = {}

        # Initialize scroll-area properties
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.verticalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.horizontalScrollBar().setContextMenuPolicy(
            qt.Qt.ContextMenuPolicy.NoContextMenu
        )
        self.setFrameShape(qt.QFrame.Shape.NoFrame)

        # Create main groupbox
        self.main_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                name="MainGroupBox",
                parent=self,
                vertical=True,
                borderless=True,
                spacing=0,
                margins=(0, 0, 0, 0),
            )
        )
        self.setWidget(self.main_groupbox)

        # Set the layout alignment
        self.main_groupbox.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignTop
        )

    def add_box(
        self,
        name: str,
        vertical: bool = True,
        spacing: int = 0,
        margins: tuple = (0, 0, 0, 0),
    ) -> qt.QFrame:
        # Create the box
        new_box = gui.templates.widgetgenerator.create_frame(
            name=name,
            parent=self,
            layout_vertical=vertical,
            layout_spacing=spacing,
            layout_margins=margins,
        )
        # Add it to the layout
        self.main_groupbox.layout().addWidget(new_box)

        # Add new box to cache
        self.__widget_cache[name] = new_box

        return new_box
