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


class Cython(qt.QsciLexerPython):
    """Cython - basically Python with added keywords"""

    # Class variables
    _kwrds = None
    styles = {
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Number": {
            "name": "number",
            "index": 2,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 3,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 4,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "TripleSingleQuotedString": {
            "name": "triple_single_quoted_string",
            "index": 6,
        },
        "TripleDoubleQuotedString": {
            "name": "triple_double_quoted_string",
            "index": 7,
        },
        "ClassName": {
            "name": "class_name",
            "index": 8,
        },
        "FunctionMethodName": {
            "name": "function_method_name",
            "index": 9,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "CommentBlock": {
            "name": "comment_block",
            "index": 12,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 13,
        },
        "HighlightedIdentifier": {
            "name": "highlighted_identifier",
            "index": 14,
        },
        "Decorator": {
            "name": "decorator",
            "index": 15,
        },
    }
    _c_kwrds = [
        "void",
        "char",
        "int",
        "long",
        "short",
        "double",
        "float",
        "const",
        "unsigned",
        "inline",
    ]
    _cython_kwrds = [
        "by",
        "cdef",
        "cimport",
        "cpdef",
        "ctypedef",
        "enum",
        "except?",
        "extern",
        "gil",
        "include",
        "nogil",
        "property",
        "public",
        "readonly",
        "struct",
        "union",
        "DEF",
        "IF",
        "ELIF",
        "ELSE",
    ]

    def __init__(self, parent=None) -> None:
        """Overridden initialization."""
        # Initialize superclass
        super().__init__()
        # Initialize list with keywords
        # Initialize list with keywords
        built_ins = keyword.kwlist
        for i in builtins.__dict__.keys():
            if not (i in built_ins):
                built_ins.append(i)
        self._kwrds = list(set(built_ins))
        # Transform list into a single string with spaces between list items
        # Add the C keywords supported by Cython
        self._kwrds.extend(self._c_kwrds)
        # Add the Cython keywords
        self._kwrds.extend(self._cython_kwrds)
        # Transform list into a single string with spaces between list items
        self._kwrds.sort()
        self._kwrds = " ".join(self._kwrds)
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

    def keywords(self, state):
        """Overridden method for determining keywords, read the QScintilla
        QsciLexer class documentation on the Riverbank website."""
        keywrds = None
        # Only state 1 returns keywords, don't know why? Check the C++ Scintilla lexer source files.
        if state == 1:
            keywrds = self._kwrds
        return keywrds
