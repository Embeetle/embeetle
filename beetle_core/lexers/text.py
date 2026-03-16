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
import keyword
import builtins
import re
import functions
import qt
import data
import time
from .functions import *


class Text(qt.QsciLexerCustom):
    """Lexer for styling normal text documents."""

    # Class variables
    styles = {
        "Default": {
            "name": "default",
            "index": 0,
        }
    }

    def __init__(self, parent=None) -> None:
        """Overridden initialization."""
        # Initialize superclass
        super().__init__()
        # Set the font colors
        self.setDefaultFont(data.get_general_font())
        self.setFont(data.get_general_font(), 0)
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

    def language(self):
        return "Plain text"

    def description(self, style):
        if style == 0:
            description = "Text"
        else:
            description = ""
        return description

    def defaultStyle(self):
        return self.styles["Default"]["index"]

    def braceStyle(self):
        return self.styles["Default"]["index"]

    def defaultFont(self, style):
        return data.get_toplevel_font()

    def styleText(self, start, end):
        self.startStyling(start)
        self.setStyling(end - start, 0)
