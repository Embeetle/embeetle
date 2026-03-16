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
import gui, functions
import gui.helpers.various
import purefunctions
import serverfunctions

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog


def show_model_download_help(*args, **kwargs) -> None:
    """Help text shown for the dashboard cogging wheel context menu."""
    pieces_ai_link = (
        f"{serverfunctions.get_base_url_wfb()}/#embeetle-ide/manual/pieces-ai"
    )
    css = purefunctions.get_css_tags()

    text = f"""
    <p align="left">
        This model has not been downloaded yet to your harddrive.<br>
        Check out here how to get it:<br>
        <a href="{pieces_ai_link}">https://embeetle.com/#embeetle-ide/manual/pieces-ai</a><br>
    </p>
    <p align="left">
        Restart Embeetle after the download.
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/warning.png",
        title_text="DOWNLOAD AI MODEL",
        text=text,
        text_click_func=functions.open_url,
    )
    return
