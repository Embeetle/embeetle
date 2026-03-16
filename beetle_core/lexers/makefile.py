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
import data
import time

# import tree_sitter
from .baselexer import *
from .functions import *


class CustomMakefile(BaseLexer):
    """Custom lexer for the Makefile language."""

    name = "Makefile"
    styles = {
        "default": {
            "name": "default",
            "index": 0,
        },
        "comment": {
            "name": "comment",
            "index": 1,
        },
        "string": {
            "name": "string",
            "index": 2,
        },
        "keyword": {
            "name": "keyword",
            "index": 3,
        },
        "top-keyword": {
            "name": "top-keyword",
            "index": 4,
        },
        "error": {
            "name": "error",
            "index": 5,
        },
    }
    # Symbol names
    keyword_nodes = (
        "abspath",
        "call",
        "define",
        "dir",
        "else",
        "endef",
        "endif",
        "error" "filter",
        "firstword",
        "if",
        "ifeq",
        "ifneq",
        "include",
        "info",
        "lastword",
        "patsubst",
        "shell",
        "sort",
        "subst",
        "vpath",
        "warning",
        "wildcard",
        #        "word",
    )
    top_keyword_nodes = "$"
    string_nodes = (
        "raw_text",
        "realpath",
        "text",
    )
    # Characters that autoindent one level on pressing Return/Enter
    autoindent_characters = [":"]

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        make_language = tree_sitter.Language(
            functions.unixify_path_join(
                data.beetle_core_directory, "lexers/treesitter_parsers.so"
            ),
            "make",
        )
        self.parser = tree_sitter.Parser()
        self.parser.set_language(make_language)

    def styleText(self, start, end):
        """Main styling function, called everytime text changes."""
        editor = self.editor()
        if editor is None:
            return
        # Initialize the styling
        self.startStyling(0)
        end_position = 0
        # Tree-sitter works with bytes, so we have to adjust the start and end boundaries
        text_bytes = editor.text().encode("utf-8")
        # Loop optimizations
        setStyling = self.setStyling
        # Parse all tokens
        tree = self.parser.parse(text_bytes)
        # Style the tokens accordingly
        for node in treesiter_traverse_tree(tree):
            if end_position != node.start_byte:
                length = node.start_byte - end_position
                if length < 0:
                    self.startStyling(node.start_byte)
                else:
                    setStyling(length, self.styles["default"]["index"])

            length = node.end_byte - node.start_byte
            end_position = node.end_byte
            if node.type == "comment":
                setStyling(length, self.styles["comment"]["index"])
            elif node.type in self.string_nodes:
                setStyling(length, self.styles["string"]["index"])
            elif node.type in self.keyword_nodes:
                setStyling(length, self.styles["keyword"]["index"])
            elif node.type in self.top_keyword_nodes:
                setStyling(length, self.styles["top-keyword"]["index"])
            else:
                setStyling(length, self.styles["default"]["index"])
