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
import data, purefunctions, gui

q = "'"
dq = '"'


def warning_for_external_folders(
    ext_folder_data: Dict[str, Dict[str, Optional[str]]],
) -> bool:
    """
    This function gets a data structure like:

    ext_folder_data = {
        # CASE 1:
        # Original and extracted abspaths match, so the hash value doesn't need
        # to be computed.
        'my_ext_folder_2' : {
            'orig_abspath'         : 'C:/Users/Kristof/my_ext_folder_2',
            'orig_hash_value'      : '3b1a4682a4b41deb74ba542bbd63ed60',
            'extracted_abspath'    : 'C:/Users/Kristof/my_ext_folder_2',
            'extracted_hash_value' : None, # <- Not computed
        },

        # CASE 2:
        # Original and extracted abspaths differ, so the hash value needs to be
        # computed.
        'my_ext_folder_1' : {
            'orig_abspath'         : 'C:/Users/Kristof/my_ext_folder_1',
            'orig_hash_value'      : '3b1a4682a4b41deb74ba542bbd63ed60',
            'extracted_abspath'    : 'C:/Users/Jean/my_ext_folder_1',
            'extracted_hash_value' : '7a44314deaa43deb74ba542bbd800344', # <- computed
        },

        # CASE 3:
        # Extracted abspath is None (nothing found), so there is nothing to com-
        # pute either!
        'my_ext_folder_2' : {
            'orig_abspath'         : 'C:/Users/Kristof/my_ext_folder_2',
            'orig_hash_value'      : '3b1a4682a4b41deb74ba542bbd63ed60',
            'extracted_abspath'    : None,
            'extracted_hash_value' : None,
        },
    }

    Based on this data, this function will either:
     - Do nothing, return True

     - Warn user about missing or mismatching external folders. If the user
       wants to continue nonetheless, return True. Otherwise, return False.

    """
    h = data.get_general_font_height()
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    # * Missing folders
    # These folders could not be found.
    missing_foldernames = [
        foldername
        for foldername in ext_folder_data.keys()
        if ext_folder_data[foldername]["extracted_abspath"] is None
    ]

    # * Mismatching folders
    # These folders don't have a matching hash value.
    mismatching_foldernames = [
        foldername
        for foldername in ext_folder_data.keys()
        if (ext_folder_data[foldername]["extracted_hash_value"] is not None)
        and (
            ext_folder_data[foldername]["extracted_hash_value"]
            != ext_folder_data[foldername]["orig_hash_value"]
        )
    ]

    if len(missing_foldernames) + len(mismatching_foldernames) == 0:
        return True

    # * Construct warning
    text = f"""
    <p align="left">
        Embeetle discovered a few issues in these external folders (they are<br>
        registered as part of the project you're trying to open):<br>
        <br>
    """
    for foldername in ext_folder_data.keys():
        if (foldername not in missing_foldernames) and (
            foldername not in mismatching_foldernames
        ):
            # This folder is okay
            continue
        orig_abspath = ext_folder_data[foldername]["orig_abspath"]
        extracted_abspath = ext_folder_data[foldername]["extracted_abspath"]

        # $ Missing folder
        if foldername in missing_foldernames:
            text += str(
                f"&nbsp;&nbsp;- {green}{foldername}{end}:<br>"
                f"{tab}&nbsp;&nbsp;original path:&nbsp;{blue}{q}{orig_abspath}{q}{end}<br>"
                f"{tab}&nbsp;&nbsp;found path:{tab}{red}None{end}<br>"
            )
            continue

        # $ Mismatching folder
        assert foldername in mismatching_foldernames
        text += str(
            f"&nbsp;&nbsp;- {green}{foldername}{end}:<br>"
            f"{tab}&nbsp;&nbsp;original path:{tab}&nbsp;{blue}{q}{orig_abspath}{q}{end}<br>"
            f"{tab}&nbsp;&nbsp;found path:{tab}{tab}{blue}{q}{extracted_abspath}{q}{end}<br>"
            f"{tab}&nbsp;&nbsp;hash values match:&nbsp;{red}No{end}<br>"
        )
        continue

    # Add some extra info in case there are mismatching folders.
    if len(mismatching_foldernames) > 0:
        text += """
        <br>
        A mismatch in hash values means that the content of the original folder<br>
        differs from the content in the corresponding folder on your computer.<br>
        """

    # Tell the user what to do.
    text += f"""
    <br>
    If you continue now, your project {red}will probably not work!{end} Therefore,<br>
    Embeetle strongly advises to:<br>
    <br>
    {tab}1. Click {q}GO BACK{q}<br>
    <br>
    {tab}2. Contact the person who created this project and<br>
    {tab}&nbsp;&nbsp;&nbsp;obtain the original external folders.<br>
    <br>
    {tab}3. Make sure to put them in the right location on<br>
    {tab}&nbsp;&nbsp;&nbsp;this computer, then restart the project.<br>
    """

    # * Ask the user
    result = gui.dialogs.popupdialog.PopupDialog.go_back_or_continue(
        icon_path="icons/dialog/stop.png",
        title_text="External folder issues",
        text=text,
    )
    if result[0] == "go_back":
        return False
    return True
