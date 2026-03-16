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

import qt
import data
import functions
import iconfunctions


class IconManipulator:
    """Icon manipulator for a widget inside a basic widget."""

    _parent = None
    _tab_widget = None
    corner_groupbox = None

    def __init__(self, parent=None, tab_widget=None):
        self._parent = parent
        self._tab_widget = tab_widget

    def __del__(self):
        self.remove_corner_groupbox()

    def set_icon(self, obj, icon):
        """Set the current icon and update it by sending the signal to the
        parent basic widget."""
        obj.current_icon = icon
        self.update_icon(obj)

    def update_tab_widget(self, new_tab_widget):
        self._tab_widget = new_tab_widget

    def update_icon(self, obj):
        """Update the current icon and update it by sending the signal to the
        parent basic widget."""
        tab_widget = self._tab_widget
        if hasattr(tab_widget, "_parent") and hasattr(
            tab_widget._parent, "update_tab_icon"
        ):
            tab_widget._parent.update_tab_icon(obj)
        elif hasattr(tab_widget, "update_tab_icon"):
            tab_widget.update_tab_icon(obj)
            self.update_corner_widget(obj)
        elif (
            hasattr(obj, "_parent")
            and hasattr(tab_widget._parent, "update_tab_icon")
            and obj.current_icon is not None
        ):
            obj._parent.update_tab_icon(obj)

    def update_corner_widget(self, obj):
        if self.corner_groupbox is not None:
            tab_widget = self._tab_widget
            self.show_corner_groupbox(tab_widget)
            return True
        else:
            return False

    def remove_corner_groupbox(self):
        if self.corner_groupbox is None:
            return
        self.corner_groupbox.setParent(None)
        if qt.sip.isdeleted(self.corner_groupbox):
            return
        self.corner_groupbox.deleteLater()

    def create_corner_button(self, icon, tooltip, function):
        button = qt.QToolButton()
        if isinstance(icon, qt.QIcon):
            button.setIcon(icon)
        else:
            button.setIcon(iconfunctions.get_qicon(icon))
        button.setPopupMode(qt.QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setToolTip(tooltip)
        button.clicked.connect(function)
        return button

    def add_corner_button(self, icon, tooltip, function):
        # Create the group box for buttons if needed
        if self.corner_groupbox is None:
            self.corner_groupbox = qt.QGroupBox(self._tab_widget)
            corner_layout = qt.QHBoxLayout()
            corner_layout.setSpacing(0)
            corner_layout.setContentsMargins(0, 0, 0, 0)
            self.corner_groupbox.setLayout(corner_layout)
            self.corner_groupbox.setStyleSheet("QGroupBox{border: 0px;}")
            self.corner_groupbox.show()
        # Add the button
        button = self.create_corner_button(icon, tooltip, function)
        layout = self.corner_groupbox.layout()
        layout.addWidget(button)
        for i in range(layout.count()):
            if data.custom_tab_scale is not None:
                layout.itemAt(i).widget().setIconSize(
                    qt.create_qsize(
                        data.custom_tab_scale, data.custom_tab_scale
                    )
                )

    def restyle_corner_button_icons(self):
        #        print(self.corner_groupbox)
        if self.corner_groupbox is None:
            return
        layout = self.corner_groupbox.layout()
        for i in range(layout.count()):
            if data.custom_tab_scale is not None:
                layout.itemAt(i).widget().setIconSize(
                    qt.create_qsize(
                        data.custom_tab_scale, data.custom_tab_scale
                    )
                )

    def update_corner_button_icon(self, icon, index=0):
        if self.corner_groupbox is None:
            return
        layout = self.corner_groupbox.layout()
        if isinstance(icon, qt.QIcon):
            layout.itemAt(index).widget().setIcon(icon)
        else:
            layout.itemAt(index).widget().setIcon(iconfunctions.get_qicon(icon))

    def show_corner_groupbox(self, tab_widget):
        if self.corner_groupbox is None:
            return
        tab_widget.setCornerWidget(self.corner_groupbox)
        self.corner_groupbox.show()
