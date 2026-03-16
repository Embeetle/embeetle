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


class Oberon(qt.QsciLexerCustom):
    """Custom lexer for the Oberon/Oberon-2/Modula/Modula-2 programming
    languages."""

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
        "Module": {
            "name": "module",
            "index": 5,
        },
        "Number": {
            "name": "number",
            "index": 6,
        },
        "Type": {
            "name": "type",
            "index": 7,
        },
    }

    # Class variables
    keyword_list = [
        "ARRAY",
        "IMPORT",
        "RETURN",
        "BEGIN",
        "IN",
        "THEN",
        "BY",
        "IS",
        "TO",
        "CASE",
        "LOOP",
        "Type",
        "CONST",
        "MOD",
        "UNTIL",
        "DIV",
        "MODULE",
        "VAR",
        "DO",
        "NIL",
        "WHILE",
        "ELSE",
        "OF",
        "WITH",
        "ELSIF",
        "OR",
        "END",
        "POINTER",
        "EXIT",
        "PROCEDURE",
        "FOR",
        "RECORD",
        "IF",
        "REPEAT",
    ]
    types_list = [
        "BOOLEAN",
        "CHAR",
        "SHORTINT",
        "INTEGER",
        "LONGINT",
        "REAL",
        "LONGREAL",
        "SET",
    ]
    splitter = re.compile(r"(\(\*|\*\)|\s+|\w+|\W)")

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
        return "Oberon/Modula-2/Component Pascal"

    def description(self, style):
        if style <= 7:
            description = "Custom lexer for the Oberon/Oberon-2/Modula/Modula-2/Component Pascal programming languages"
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
        # Initialize the styling
        self.startStyling(start)
        # Scintilla works with bytes, so we have to adjust the start and end boundaries
        text = bytearray(editor.text(), "utf-8")[start:end].decode("utf-8")
        # Loop optimizations
        setStyling = self.setStyling
        kw_list = self.keyword_list
        types_list = self.types_list
        DEF = self.styles["Default"]["index"]
        KWD = self.styles["Keyword"]["index"]
        COM = self.styles["Comment"]["index"]
        STR = self.styles["String"]["index"]
        PRO = self.styles["Procedure"]["index"]
        MOD = self.styles["Module"]["index"]
        NUM = self.styles["Number"]["index"]
        TYP = self.styles["Type"]["index"]
        # Initialize comment state and split the text into tokens
        commenting = False
        stringing = False
        tokens = [
            (token, len(bytearray(token, "utf-8")))
            for token in self.splitter.findall(text)
        ]
        # Check if there is a style(comment, string, ...) stretching on from the previous line
        if start != 0:
            previous_style = editor.SendScintilla(
                editor.SCI_GETSTYLEAT, start - 1
            )
            if previous_style == COM:
                commenting = True
        # Style the tokens accordingly
        for i, token in enumerate(tokens):
            if commenting == True:
                # Continuation of comment
                setStyling(token[1], COM)
                # Check if comment ends
                if token[0] == "*)":
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
            elif token[0] in types_list:
                # Keyword
                setStyling(token[1], TYP)
            elif token[0] == "(*":
                # Start of a comment
                setStyling(token[1], COM)
                commenting = True
            elif i > 1 and tokens[i - 2][0] == "PROCEDURE":
                # Procedure name
                setStyling(token[1], PRO)
            elif i > 1 and tokens[i - 2][0] == "MODULE":
                # Module name (beginning)
                setStyling(token[1], MOD)
            elif (i > 1 and tokens[i - 2][0] == "END") and (
                len(tokens) - 1 >= i + 1
            ):
                # Module or procedure name (name)
                if ";" in tokens[i + 1][0]:
                    # Procedure end
                    setStyling(token[1], PRO)
                elif "." in tokens[i + 1][0]:
                    # Module end
                    setStyling(token[1], MOD)
                else:
                    setStyling(token[1], DEF)
            elif functions.is_number(token[0]):
                # Number
                setStyling(token[1], NUM)
            else:
                setStyling(token[1], DEF)
