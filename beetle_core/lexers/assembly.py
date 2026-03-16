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

from .baselexer import *


class Assembly(BaseLexer):
    """Custom lexer for the Assembly language."""

    # Characters that autoindent one level on pressing Return/Enter
    autoindent_characters = [":"]

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
        "Label": {
            "name": "label",
            "index": 3,
        },
        "String": {
            "name": "string",
            "index": 4,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 5,
        },
    }

    def __init__(self, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)
        return

    def language(self):
        return "Assembly"

    def description(self, style):
        if style < len(self.styles.keys()):
            description = "Custom lexer for the Assembly language"
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
        """Main styling function, called everytime text changes."""
        editor = self.editor()
        if editor is None:
            return
        # Initialize the styling
        self.startStyling(start)

        text = editor.text(start, end)
        text_length = len(bytearray(text, "utf-8"))
        # Loop optimizations
        setStyling = self.setStyling
        #        # Parse all tokens
        #        tokens = [(token, len(bytearray(token, "utf-8"))) for token in self.splitter.findall(text)]

        # Tokenizing
        pattern = re.compile(r"\n|[*]\/|\/[*]|//|\.\w+|#\s*\w+|\s+|\w+|\W")
        token_list = [
            (token, len(bytearray(token, "utf-8")))
            for token in pattern.findall(text)
        ]
        token_list_length = len(token_list)

        # Parsing
        line_item_count = 0
        singleline_comm_flag = False
        multiline_comm_flag = False
        string_flag = False
        triangle_flag = False

        # Check for previous comment
        if start > 0:
            previous_style_nr = editor.SendScintilla(
                editor.SCI_GETSTYLEAT, start - 1
            )
            if previous_style_nr == self.styles["Comment"]["index"]:
                multiline_comm_flag = True

        # Style the tokens accordingly
        for i, item in enumerate(token_list):
            token = item[0]
            length = item[1]

            previous_token = token_list[i - 1][0] if (i > 0) else ""
            if i < (token_list_length - 1):
                next_token = token_list[i + 1][0]
            else:
                next_token = ""

            if "\n" in token:
                line_item_count = 0
            #                print("'{}' '{}' '{}'".format(previous_token, token, next_token))

            if multiline_comm_flag:
                self.setStyling(length, self.styles["Comment"]["index"])
                if token == "*/":
                    multiline_comm_flag = False

            elif singleline_comm_flag:
                if "\n" in token:
                    setStyling(length, self.styles["Default"]["index"])
                    singleline_comm_flag = False
                else:
                    setStyling(length, self.styles["Comment"]["index"])

            elif string_flag:
                setStyling(length, self.styles["String"]["index"])
                if token == '"' and previous_token != "\\":
                    string_flag = False
            elif triangle_flag:
                setStyling(length, self.styles["String"]["index"])
                if token == ">":
                    triangle_flag = False

            else:
                if token == "/*":
                    multiline_comm_flag = True
                    setStyling(length, self.styles["Comment"]["index"])

                elif token in (";", "//"):
                    singleline_comm_flag = True
                    setStyling(length, self.styles["Comment"]["index"])

                elif (token == '"' or token == "<") and previous_token != "\\":
                    if token == "<":
                        triangle_flag = True
                    else:
                        string_flag = True
                    setStyling(length, self.styles["String"]["index"])

                elif next_token == ":":
                    setStyling(length, self.styles["Label"]["index"])

                elif re.match(r"#\s*\w+", token):
                    setStyling(length, self.styles["PreProcessor"]["index"])

                elif line_item_count == 0:
                    setStyling(length, self.styles["Keyword"]["index"])

                elif token.startswith("."):
                    setStyling(length, self.styles["Keyword"]["index"])

                else:
                    setStyling(length, self.styles["Default"]["index"])

            if "\n" not in token and token.strip() != "":
                line_item_count += 1
