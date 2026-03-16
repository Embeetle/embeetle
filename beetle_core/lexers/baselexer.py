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
import re
import time
import keyword
import builtins
import qt
import data
import functions

from .functions import *


class BaseLexer(qt.QsciLexerCustom):
    """Base lexer for the new style lexers."""

    name = "UNKNOWN"
    styles = None

    def __init__(self, parent=None) -> None:
        """"""
        # Initialize superclass
        super().__init__()
        # Set the default style values
        self.setDefaultColor(qt.QColor(data.theme["fonts"]["default"]["color"]))
        self.setDefaultFont(data.get_editor_font())
        self.setDefaultPaper(
            qt.QColor(data.theme["fonts"]["default"]["background"])
        )
        # Reset autoindentation style
        self.setAutoIndentStyle(0)
        # Set the theme
        self.__class__.set_theme = set_theme
        self.set_theme(data.theme)
        # Misc
        self.open_close_comment_style: Optional[bool] = None
        self.comment_string: Optional[str] = None
        self.end_comment_string: Optional[str] = None
        return

    def defaultStyle(self):
        return self.styles["default"]["index"]

    def braceStyle(self):
        return self.styles["default"]["index"]

    def defaultFont(self, style):
        return data.get_toplevel_font()

    def description(self, style):
        if style < len(data.theme["fonts"].keys()):
            description = "Custom lexer for the {} language".format(self.name)
        else:
            description = ""
        return description

    def language(self):
        return self.name

    def styleText(self, start, end):
        raise Exception("[BaseLexer] Unimplemented!")
