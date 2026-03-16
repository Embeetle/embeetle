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


class LinkerScript(qt.QsciLexerCustom):
    """Custom lexer for the LinkerScript."""

    splitter = re.compile(
        r"\]|\}|\)|\[|\{|\(|[*]\/|\/[*]|//|#\s*\w+|\s+|\w+|\W"
    )
    sequence_end_characters = [
        " ",
        "\n",
        "\t",
        "(",
        "{",
        "[",
        ")",
        "}",
        "]",
        ":",
        "*",
        "/",
        "\\",
        "+",
        "-",
        "'",
        "&",
        "%",
        "!",
        "$",
        "%",
        "&",
        "=",
        "?",
        "|",
        "<",
        ">",
        "_",
        ",",
        ";",
    ]

    def _parse_styles(self):
        name = data.get_global_font_family()
        size = data.get_general_font_pointsize()
        _number = -1

        def get_number():
            nonlocal _number
            _number += 1
            return _number

        self.styles = {
            "default": {
                "name": "default",
                "index": get_number(),
                "keywords": None,
                "start_char": None,
                "end_char": None,
                "paint_end_char": False,
            },
            "comment": {
                "name": "comment",
                "index": get_number(),
                "keywords": None,
                "start_char": ["/*"],
                "end_char": ["*/"],
                "paint_end_char": True,
            },
            "hex_number": {
                "name": "hex_number",
                "index": get_number(),
                "keywords": None,
                "start_char": ["0x"],
                "end_char": self.sequence_end_characters,
                "paint_end_char": False,
                "font": (name, 0xFF000000, size, True),
                "paper": 0xFFFFFFFF,
            },
            "number": {
                "name": "number",
                "index": get_number(),
                "keywords": None,
                "start_char": [
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                ],
                "end_char": self.sequence_end_characters,
                "paint_end_char": False,
            },
            "standard": {
                "name": "standard",
                "index": get_number(),
                "keywords": [
                    "OUTPUT_FORMAT",
                    "OUTPUT_ARCH",
                    "ENTRY",
                    "KEEP",
                    "PROVIDE",
                    "ALIGN",
                    "DEFINED",
                    "ORIGIN",
                    "LENGTH",
                    "LONG",
                    "SEARCH_DIR",
                    "GROUP",
                    "EXTERN",
                    "ASSERT",
                    "PROVIDE_HIDDEN",
                ],
                "start_char": None,
                "end_char": None,
                "paint_end_char": False,
            },
            "extra": {
                "name": "extra",
                "index": get_number(),
                "keywords": [
                    "MEMORY",
                    "INCLUDE",
                    "SECTIONS",
                ],
                "start_char": None,
                "end_char": None,
                "paint_end_char": False,
            },
            "dunder": {
                "name": "dunder",
                "index": get_number(),
                "keywords": None,
                "start_char": ["__"],
                "end_char": self.sequence_end_characters,
                "paint_end_char": False,
            },
            "dot": {
                "name": "dot",
                "index": get_number(),
                "keywords": None,
                "start_char": ["."],
                "end_char": self.sequence_end_characters,
                "paint_end_char": False,
            },
        }
        self._optimize_sequences()
        self.styles_numbered = {}
        for k, v in self.styles.items():
            self.styles_numbered[v["index"]] = k

    def _optimize_sequences(self):
        self.keyword_list = []
        self.keyword_dict = {}
        self.start_seqs = []
        self.end_seqs = {}
        for k, v in self.styles.items():
            if v["keywords"] is None and v["start_char"] is not None:
                for c in v["start_char"]:
                    self.start_seqs.append((c, v["index"], k))
                self.end_seqs[v["index"]] = tuple(v["end_char"])
            else:
                if v["start_char"] is not None:
                    message = (
                        "{} lexer error: keywords and start_chars cannot "
                        + "both be defined for style '{}'!"
                    ).format(self.language(), k)
                    raise Exception(message)
                else:
                    if v["keywords"] is not None:
                        for kw in v["keywords"]:
                            self.keyword_list.append(kw)
                            self.keyword_dict[kw] = v["index"]

    def __init__(self, parent=None) -> None:
        """Overridden initialization."""
        # Initialize superclass
        super().__init__()
        # Reset autoindentation style
        self.setAutoIndentStyle(0)
        # Set the theme
        self.set_theme(data.theme)
        # Misc
        self.open_close_comment_style: Optional[bool] = None
        self.comment_string: Optional[str] = None
        self.end_comment_string: Optional[str] = None
        return

    def language(self):
        return "LinkerScript"

    def description(self, style):
        if style <= len(self.styles.keys()):
            description = "LinkerScript"
        else:
            description = ""
        return description

    def defaultStyle(self):
        return self.styles["default"]["index"]

    def braceStyle(self):
        return self.styles["default"]["index"]

    def defaultFont(self, style):
        return data.get_toplevel_font()

    def blockStart(self, style=0):
        return (bytes("{", encoding="utf-8"), 0)

    def blockEnd(self, style=0):
        return (bytes("}", encoding="utf-8"), 0)

    def set_theme(self, theme):
        self._parse_styles()
        set_theme(self, data.theme)

    def styleText(self, start, end):
        editor = self.editor()
        if editor is None:
            return
        # References
        setStyling = self.setStyling
        start_seqs = self.start_seqs
        end_seqs = self.end_seqs
        # Initialize the styling
        self.startStyling(0)
        # Scintilla works with bytes, so we have to adjust the start and end boundaries
        text = bytearray(editor.text(), "utf-8").decode("utf-8")
        # Initialize comment state and split the text into tokens
        tokens = [
            (token, len(bytearray(token, "utf-8")))
            for token in self.splitter.findall(text)
        ]
        # Multi token flag
        sequence_style = -1
        sequence_name = None
        # Check previous style
        if start > 0:
            previous_style_nr = editor.SendScintilla(
                editor.SCI_GETSTYLEAT, start - 1
            )
            for x in end_seqs.keys():
                if previous_style_nr == x:
                    sequence_style = previous_style_nr
                    sequence_name = self.styles_numbered[sequence_style]
                    break
        # Style the tokens
        for i, token in enumerate(tokens):
            token_text = token[0]
            token_length = token[1]
            # Continuation of sequence
            if sequence_style != -1:
                # Check if sequence ends
                token_sequence = "".join([x[0] for x in tokens[i - 4 : i + 1]])
                for x in end_seqs[sequence_style]:
                    if token_sequence.endswith(x):
                        if self.styles[sequence_name]["paint_end_char"] == True:
                            setStyling(token_length, sequence_style)
                        else:
                            setStyling(
                                token_length, self.styles["default"]["index"]
                            )
                        sequence_style = -1
                        break
                else:
                    setStyling(token_length, sequence_style)
            elif token_text.strip() in self.keyword_list:
                setStyling(token_length, self.keyword_dict[token_text])
            else:
                token_sequence = "".join([x[0] for x in tokens[i : i + 4]])
                for ss in start_seqs:
                    chars = ss[0]
                    if token_sequence.startswith(chars):
                        sequence_style = ss[1]
                        sequence_name = ss[2]
                        setStyling(token_length, sequence_style)
                        break
                else:
                    setStyling(token_length, self.styles["default"]["index"])
