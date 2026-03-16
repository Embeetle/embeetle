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

from typing import *
import os
import os.path
import qt
import data
import purefunctions
from various.kristofstuff import *


def __get_fonts_from_resources() -> List[str]:
    """"""
    directory = purefunctions.join_resources_dir_to_path("fonts/")
    font_file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            item = purefunctions.unixify_path_join(root, file)
            if item.lower().endswith(".ttf") or item.lower().endswith(".otf"):
                font_file_list.append(
                    purefunctions.unixify_path_join(directory, item)
                )
    return font_file_list


def set_application_font() -> None:
    """"""
    name = data.current_font_name
    # Load the fonts from 'resources/fonts'
    font_file_list = __get_fonts_from_resources()
    for file in font_file_list:
        qt.QFontDatabase.addApplicationFont(file)

    # Check if font is properly loaded
    search_font_name = name.lower()
    font_found = False
    # The QFontDatabase class has now only static member functions. The constructor has been
    # deprecated.
    for fontname in qt.QFontDatabase.families():
        if search_font_name in fontname.lower():
            font_found = True
            break
    if not font_found:
        purefunctions.printc(
            f"ERROR: Cannot load the {q}{search_font_name.title()}{q} font!",
            color="error",
        )

    # Apply the font for the whole application
    font = data.get_general_font()
    data.application.setFont(font)
    return


def get_all_fonts() -> Tuple[str]:
    return tuple(fontname for fontname in qt.QFontDatabase.families())
