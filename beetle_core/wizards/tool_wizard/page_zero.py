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
import qt
import helpdocs.help_texts as _ht_
import wizards.tool_wizard.new_tool_wizard as _wiz_


def init_p0(self: _wiz_.NewToolWizard) -> None:
    """Initialize page 0.

    ╔══_groupbox_p0═════════╗ ║ ┌─_groupbox_p0r0──┐   ║ ║ │                 │ ║
    ║ └─────────────────┘   ║ ║                       ║ ║ ║ ║
    ║ ╚═══════════════════════╝
    """

    def create_groupbox_p0r0():
        self._groupbox_p0r0 = self.create_info_groupbox(
            parent=self._groupbox_p0,
            text="Tool source:",
            vertical=True,
            info_func=_ht_.tool_source_help,
            spacing=5,
            margins=(5, 5, 5, 5),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Expanding,
        )
        self._groupbox_p0r0.layout().setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self._groupbox_p0.layout().addWidget(self._groupbox_p0r0)
        self._groupbox_p0.layout().addStretch(10)

        # * Selection line 1: download
        hlyt, checkdot, button, lbl = self.create_checkdot_btn_lbl(
            parent=self._groupbox_p0r0,
            icon_path="icons/gen/download.png",
            tool_tip="Download a tool from our server",
            text="Download from Embeetle Server",
            click_func=lambda *args: update_p0(self, "download"),
        )
        self._groupbox_p0r0.layout().addLayout(hlyt)
        self._widgets_p0r0["download"]["checkdot"] = checkdot
        self._widgets_p0r0["download"]["button"] = button
        self._widgets_p0r0["download"]["label"] = lbl

        # * Selection line 2: local
        hlyt, checkdot, button, lbl = self.create_checkdot_btn_lbl(
            parent=self._groupbox_p0r0,
            icon_path="icons/gen/computer_local.png",
            tool_tip="Locate an existing tool on your harddrive",
            text="Locate on my computer",
            click_func=lambda *args: update_p0(self, "local"),
        )
        self._groupbox_p0r0.layout().addLayout(hlyt)
        self._widgets_p0r0["local"]["checkdot"] = checkdot
        self._widgets_p0r0["local"]["button"] = button
        self._widgets_p0r0["local"]["label"] = lbl
        return

    create_groupbox_p0r0()
    return


def update_p0(self: _wiz_.NewToolWizard, name: str) -> None:
    """Update page 0 based on clicked checkdot."""

    def refresh_next(*args):
        self._widgets_p0r0["local"]["checkdot"].sync_widg(
            refreshlock=False,
            force_stylesheet=False,
            callback=finish,
            callbackArg=None,
        )

    def finish(*args):
        return

    self.next_button.setEnabled(True)
    if name == "download":
        self._widgets_p0r0["download"]["checkdot"].set_on(True)
        self._widgets_p0r0["local"]["checkdot"].set_on(False)
    else:
        self._widgets_p0r0["download"]["checkdot"].set_on(False)
        self._widgets_p0r0["local"]["checkdot"].set_on(True)
    self._widgets_p0r0["download"]["checkdot"].sync_widg(
        refreshlock=False,
        force_stylesheet=False,
        callback=refresh_next,
        callbackArg=None,
    )
    return
