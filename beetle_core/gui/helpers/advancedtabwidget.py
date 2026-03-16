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

import os
import sys
import qt
import data
import iconfunctions


class AdvancedTabBar(qt.QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        widget = qt.QWidget()
        layout = qt.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetNoConstraint)
        widget.setLayout(layout)
        self.setWidget(widget)
        style_sheet = """
            border: 1px solid black;
            margin: 0px;
            spacing: 0px;
            padding: 0px;
        """
        self.widget().setStyleSheet(style_sheet)
        self.setStyleSheet(style_sheet)

        self.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(
            qt.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

    def add_tab(self, name, icon):
        new_tab = qt.QPushButton(iconfunctions.get_qicon(icon), name)
        new_tab.clicked.connect(lambda *args: print(name))
        new_tab.setFixedSize(qt.create_qsize(100, 50))
        self.widget().layout().addWidget(new_tab)


class AdvancedTabWidget(qt.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # Containers
        self.__init_containers()

    def __init_containers(self):
        # Main layout
        layout = qt.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # Tab-bar equivalent widget
        self.tabbar = AdvancedTabBar(self)
        self.layout().addWidget(self.tabbar)
        self.layout().setSizeConstraint(
            qt.QLayout.SizeConstraint.SetNoConstraint
        )
        self.layout().setAlignment(
            self.tabbar,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )

    def add_widget(self, name, icon, widget):
        self.tabbar.add_tab(name, icon)


class Window(qt.QWidget):
    def __init__(self):
        super().__init__()

        layout = qt.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(qt.QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(layout)
        tabs = AdvancedTabWidget(self)
        layout.addWidget(tabs)

        tabs.add_widget(
            "TEST1",
            "D:/embedoffice_stuff/embedoffice/beetle_core/resources/icons/chip/chip.png",
            None,
        )
        tabs.add_widget(
            "TEST2",
            "D:/embedoffice_stuff/embedoffice/beetle_core/resources/icons/chip/chip.png",
            None,
        )
        tabs.add_widget(
            "TEST3",
            "D:/embedoffice_stuff/embedoffice/beetle_core/resources/icons/chip/chip.png",
            None,
        )


def test_atw(app):
    window = Window()
    window.show()
    sys.exit(app.exec())
