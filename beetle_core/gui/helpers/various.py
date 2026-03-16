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
import types
from typing import (
    Optional,
)

import iconfunctions
import gui.helpers.standalonetextdiffer


class DiffDialog(qt.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = "Standalone Diff Dialog"

        empty_function = lambda *args, **kwargs: None

        self.view = types.SimpleNamespace()
        self.view.editor_control_press = empty_function
        self.view.editor_control_release = empty_function
        self.view.hide_all_overlay_widgets = empty_function

        self._set_save_status = empty_function

        self.bookmarks = types.SimpleNamespace()
        self.bookmarks.marks = []
        self.bookmarks.check = empty_function

        self.display = types.SimpleNamespace()
        self.display.update_cursor_position = empty_function

    def update_editor_diagnostics(self):
        pass


def create_standalone_diff(
    title,
    icon,
    text_1,
    text_2,
    text_name_1,
    text_name_2,
    initial_size=(640, 480),
    parent: Optional[qt.QObject] = None,
) -> DiffDialog:
    """"""
    # Compute initial width
    longest_line = 0
    for line in text_1.split("\n"):
        if len(line) > longest_line:
            longest_line = len(line)
    for line in text_2.split("\n"):
        if len(line) > longest_line:
            longest_line = len(line)
    # width = get_text_width(longest_line*"B")
    # width += 50
    # width *= 2
    # initial_size = (width, initial_size[1])

    # Dialog
    diff_dialog: DiffDialog = DiffDialog(parent=parent)
    diff_dialog.resize(qt.create_qsize(*initial_size))
    diff_dialog.setWindowTitle(title)
    diff_dialog.setWindowIcon(iconfunctions.get_qicon(icon))
    diff_dialog.setWindowIcon(
        iconfunctions.get_qicon(data.application_icon_relpath)
    )
    diff_dialog.setWindowFlags(
        qt.Qt.WindowType.Window
        | qt.Qt.WindowType.WindowTitleHint
        | qt.Qt.WindowType.WindowSystemMenuHint
        | qt.Qt.WindowType.WindowCloseButtonHint
    )
    diff_dialog.setWindowOpacity(1.0)
    diff_dialog.setSizePolicy(
        qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding
    )
    scroll_layout = qt.QVBoxLayout()
    scroll_layout.setSpacing(0)
    scroll_layout.setContentsMargins(0, 0, 0, 0)
    diff_dialog.setLayout(scroll_layout)

    # Text differ
    text_differ = gui.helpers.standalonetextdiffer.StandaloneTextDiffer(
        diff_dialog, text_1, text_2, text_name_1, text_name_2
    )
    scroll_layout.addWidget(text_differ)
    diff_dialog.show()
    return diff_dialog
