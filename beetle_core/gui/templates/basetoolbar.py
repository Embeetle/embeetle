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
import qt
import data
import gui.stylesheets.toolbar


class BaseToolBar(qt.QToolBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(qt.Qt.ContextMenuPolicy.CustomContextMenu)
        self.update_style()
        data.signal_dispatcher.update_styles.connect(self.update_style)

    def contextMenuEvent(self, event):
        event.accept()

    def update_style(self, *args):
        self.setStyleSheet(gui.stylesheets.toolbar.get_default())
