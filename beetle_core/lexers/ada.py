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


class Ada(qt.QsciLexerCustom):
    """Custom lexer for the Ada programming language."""

    styles = {
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Keyword": {
            "name": "keyword",
            "index": 2,
        },
        "String": {
            "name": "string",
            "index": 3,
        },
        "Procedure": {
            "name": "procedure",
            "index": 4,
        },
        "Number": {
            "name": "number",
            "index": 5,
        },
        "Type": {
            "name": "type",
            "index": 6,
        },
        "Package": {
            "name": "package",
            "index": 7,
        },
    }

    # Class variables
    keyword_list = [
        "abort",
        "else",
        "new",
        "return",
        "abs",
        "elsif",
        "not",
        "reverse",
        "abstract",
        "end",
        "null",
        "accept",
        "entry",
        "select",
        "access",
        "exception",
        "of",
        "separate",
        "aliased",
        "exit",
        "or",
        "some",
        "all",
        "others",
        "subtype",
        "and",
        "for",
        "out",
        "synchronized",
        "array",
        "function",
        "overriding",
        "at",
        "tagged",
        "generic",
        "package",
        "task",
        "begin",
        "goto",
        "pragma",
        "terminate",
        "body",
        "private",
        "then",
        "if",
        "procedure",
        "type",
        "case",
        "in",
        "protected",
        "constant",
        "interface",
        "until",
        "is",
        "raise",
        "use",
        "declare",
        "range",
        "delay",
        "limited",
        "record",
        "when",
        "delta",
        "loop",
        "rem",
        "while",
        "digits",
        "renames",
        "with",
        "do",
        "mod",
        "requeue",
        "xor",
    ]
    splitter = re.compile(r"(\-\-|\s+|\w+|\W)")

    def __init__(self, parent=None) -> None:
        """Overridden initialization."""
        # Initialize superclass
        super().__init__()
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
        return "Ada"

    def description(self, style):
        if style <= len(self.styles):
            description = "Custom lexer for the Ada programming languages"
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
        """Overloaded method for styling text.

        NOTE:
            Very slow if done in Python!
            Using the Cython version is better.
            The fastest would probably be adding the lexer directly into
            the QScintilla source. Maybe never :-)
        """
        # Style in pure Python, VERY SLOW!
        editor = self.editor()
        if editor is None:
            return
        # Initialize the procedure/package counter
        pp_counter = []
        # Initialize the styling
        self.startStyling(0)
        # Scintilla works with bytes, so we have to adjust the start and end boundaries
        text = bytearray(editor.text().lower(), "utf-8").decode("utf-8")
        # Loop optimizations
        setStyling = self.setStyling
        kw_list = self.keyword_list
        DEF = self.styles["Default"]["index"]
        KWD = self.styles["Keyword"]["index"]
        COM = self.styles["Comment"]["index"]
        STR = self.styles["String"]["index"]
        PRO = self.styles["Procedure"]["index"]
        NUM = self.styles["Number"]["index"]
        PAC = self.styles["Package"]["index"]
        #        TYP = self.styles["Type"]
        # Initialize comment state and split the text into tokens
        commenting = False
        stringing = False
        tokens = [
            (token, len(bytearray(token, "utf-8")))
            for token in self.splitter.findall(text)
        ]
        # Style the tokens accordingly
        for i, token in enumerate(tokens):
            if commenting == True:
                # Continuation of comment
                setStyling(token[1], COM)
                # Check if comment ends
                if "\n" in token[0]:
                    commenting = False
            elif stringing == True:
                # Continuation of a string
                setStyling(token[1], STR)
                # Check if string ends
                if token[0] == '"' or "\n" in token[0]:
                    stringing = False
            elif token[0] == '"':
                # Start of a string
                setStyling(token[1], STR)
                stringing = True
            elif token[0] in kw_list:
                # Keyword
                setStyling(token[1], KWD)
            elif token[0] == "--":
                # Start of a comment
                setStyling(token[1], COM)
                commenting = True
            elif i > 1 and tokens[i - 2][0] == "procedure":
                # Procedure name
                setStyling(token[1], PRO)
                # Mark the procedure
                if tokens[i + 1][0] != ";":
                    pp_counter.append("PROCEDURE")
            elif i > 1 and (
                tokens[i - 2][0] == "package" or tokens[i - 2][0] == "body"
            ):
                # Package name
                setStyling(token[1], PAC)
                # Mark the package
                pp_counter.append("PACKAGE")
            elif (i > 1 and tokens[i - 2][0] == "end") and (
                len(tokens) - 1 >= i + 1
            ):
                # Package or procedure name end
                if len(pp_counter) > 0:
                    if pp_counter.pop() == "PACKAGE":
                        setStyling(token[1], PAC)
                    else:
                        setStyling(token[1], PRO)
                else:
                    setStyling(token[1], DEF)
            elif functions.is_number(token[0]):
                # Number
                setStyling(token[1], NUM)
            else:
                setStyling(token[1], DEF)
