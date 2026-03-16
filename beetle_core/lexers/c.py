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
import functions
import qt
import data
import time
import functools

from .functions import *


class CustomC(qt.QsciLexerCustom):
    ASYNC = False

    type_list = [
        "__int16",
        "__int32",
        "__int64",
        "__int8",
        "__far",
        "__far16",
        "__ptr32",
        "__ptr64",
        "__w64",
        "__wchar_t",
        "__int128",
        "_far",
        "_far16",
        "_int16",
        "_int32",
        "_int64",
        "_int8",
        "_int16",
        "_int32",
        "_int64",
        "_int8",
        "_ptr32",
        "_ptr64",
        "_w64",
        "auto",
        "bool",
        "char",
        "far",
        "float",
        "huge",
        "short",
        "int",
        "wchar_t",
        "void",
        "long",
        "double",
        "uint32_t",
        "uint16_t",
        "uint8_t",
    ]  # type: List[str]
    operator_list = [
        "=",
        "+",
        "-",
        "*",
        "/",
        "<",
        ">",
        "@",
        "$",
        ".",
        "~",
        "&",
        "%",
        "|",
        "!",
        "?",
        "^",
        ".",
        ":",
        '"',
    ]  # type: List[str]
    call_convention_list = [
        "__cdecl",
        "__clrcall",
        "__stdcall",
        "__fastcall",
        "__thiscall",
        "__vectorcall",
        "__declspec",
    ]  # type: List[str]
    dunder_list = [
        "__abstract",
        "__alignof",
        "__asm",
        "__assume",
        "__based",
        "__box",
        "__builtin_alignof",
        "__builtin_isfloat",
        "__delegate",
        "__event",
        "__except",
        "__export",
        "__feacpBreak",
        "__finally",
        "__forceinline",
        "__fortran",
        "__gc",
        "__hook",
        "__huge",
        "__identifier",
        "__if_exists",
        "__if_not_exists",
        "__inline",
        "__interface",
        "__leave",
        "__multiple_inheritance",
        "__near",
        "__nodefault",
        "__nogc",
        "__nontemporal",
        "__nounwind",
        "__novtordisp",
        "__pascal",
        "__pin",
        "__pragma",
        "__probability",
        "__property",
        "__raise",
        "__restrict",
        "__resume",
        "__sealed",
        "__serializable",
        "__single_inheritance",
        "__super",
        "__sysapi",
        "__syscall",
        "__transient",
        "__try",
        "__try_cast",
        "__typeof",
        "__unaligned",
        "__unhook",
        "__uuidof",
        "__value",
        "__virtual_inheritance",
        "__compileBreak",
        "__packed__",
    ]  # type: List[str]
    under_list = [
        "_alignof",
        "_asm",
        "_assume",
        "_uuidof",
        "_virtual_inheritance",
        "_based",
        "_builtin_alignof",
        "_cdecl",
        "_compileBreak",
        "_declspec",
        "_except",
        "_export",
        "_fastcall",
        "_inline",
        "_feacpBreak",
        "_finally",
        "_forceinline",
        "_fortran",
        "_huge",
        "_leave",
        "_multiple_inheritance",
        "_near",
        "_novtordisp",
        "_pascal",
        "_pragma",
        "_serializable",
        "_single_inheritance",
        "_stdcall",
        "_syscall",
        "_thiscall",
        "_transient",
        "_try",
    ]
    keyword_list = [
        "and",
        "and_eq",
        "asm",
        "bitand",
        "bitor",
        "break",
        "case",
        "catch",
        "cdecl",
        "class",
        "compl",
        "const",
        "const_cast",
        "continue",
        "default",
        "delete",
        "do",
        "dynamic_cast",
        "else",
        "enum",
        "explicit",
        "extern",
        "false",
        "for",
        "fortran",
        "friend",
        "goto",
        "if",
        "inline",
        "mutable",
        "namespace",
        "near",
        "new",
        "not",
        "not_eq",
        "operator",
        "or",
        "or_eq",
        "pascal",
        "private",
        "protected",
        "public",
        "register",
        "reinterpret_cast",
        "return",
        "signed",
        "sizeof",
        "static",
        "static_cast",
        "struct",
        "switch",
        "template",
        "this",
        "throw",
        "true",
        "try",
        "typedef",
        "typeid",
        "typename",
        "union",
        "unsigned",
        "using",
        "virtual",
        "volatile",
        "while",
    ]  # type: List[str]
    added_keyword_list = []  # type: List[str]

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
            "index": 3,
        },
        "Keyword": {
            "name": "keyword",
            "index": 4,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 5,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "Regex": {
            "name": "regex",
            "index": 7,
        },
        "String": {
            "name": "string",
            "index": 8,
        },
        "TriangularBracing": {
            "name": "triangular_bracing",
            "index": 9,
        },
        "Type": {
            "name": "type",
            "index": 10,
        },
        "CallConvention": {
            "name": "call_convention",
            "index": 11,
        },
        "UnderDunder": {
            "name": "under_dunder",
            "index": 12,
        },
        "AdvancedKeyword": {
            "name": "advanced_keyword",
            "index": 13,
        },
        "Whitespace": {
            "name": "whitespace",
            "index": 14,
        },
        "Tab": {
            "name": "tab",
            "index": 15,
        },
    }

    def __del__(self):
        if self.ASYNC:
            self.terminate_parsing_thread()

    def self_destruct(self) -> None:
        """"""
        return

    def __init__(self, parent=None) -> None:
        """"""
        super().__init__(parent)
        # Auto indent style '0' is needed for the blockStart/blockEnd to work!
        self.setAutoIndentStyle(0)
        # Initialize the keyword list
        self.added_keyword_list = []
        self._create_keyword_list()
        # Set the theme
        self.__class__.set_theme = set_theme
        self.set_theme(data.theme)
        # Misc
        self.open_close_comment_style: Optional[bool] = None
        self.comment_string: Optional[str] = None
        self.end_comment_string: Optional[str] = None
        return

    def _create_keyword_list(self):
        # Initialize list with keywords
        self._kwrds_list = list(self.keyword_list)
        self._kwrds_list.sort()
        # Transform list into a single string with spaces between list items
        self._kwrds = " ".join(self._kwrds_list)

    def setParent(self, parent):
        super().setParent(parent)

    def language(self):
        return "C/C++"

    def keywords(self, state):
        """Overridden method for determining keywords, read the QScintilla
        QsciLexer class documentation on the Riverbank website."""
        return self._kwrds

    def description(self, style):
        for k, v in self.styles.items():
            if v["index"] == style:
                return k
        return ""

    def defaultStyle(self):
        return self.styles["Default"]["index"]

    def braceStyle(self):
        return self.styles["Default"]["index"]

    def defaultFont(self, style):
        return data.get_toplevel_font()

    def blockStart(self, style=0):
        return (bytes("{", encoding="utf-8"), 0)

    def blockEnd(self, style=0):
        return (bytes("}", encoding="utf-8"), 0)

    def styleText(self, start, end):
        if self.ASYNC:
            # Asynchronous
            self.terminate_parsing_thread()
            editor = self.parent()
            text = self.parent().text()[start:end]
            self.lexer_worker = LexingThreadWorker(
                editor, text, start, self.added_keyword_list
            )
            self.parsing_thread = qt.QThread(self)
            self.parsing_thread.setTerminationEnabled(True)
            self.lexer_worker.moveToThread(self.parsing_thread)
            self.lexer_worker.finished.connect(self.paint_text)
            self.parsing_thread.started.connect(self.lexer_worker.work)
            self.parsing_thread.start()
        else:
            # Synchronous
            self.styleText_synchronous(start, end)

    def styleText_synchronous(self, start, end):
        result = []
        editor = self.parent()
        text = editor.text(start, end)
        self.startStyling(start)

        def add_parse_item(length, style):
            self.setStyling(length, self.styles[style]["index"])

        text_length = len(bytearray(text, "utf-8"))
        # Tokenizing
        pattern = re.compile(r"[*]\/|\/[*]|//|#[ ]*\w+|\s+|\w+|\W")
        token_list = [
            (token, len(bytearray(token, "utf-8")))
            for token in pattern.findall(text)
        ]
        # Parsing
        singleline_comm_flag = False
        multiline_comm_flag = False
        string_flag = False

        if start > 0:
            previous_style_nr = editor.SendScintilla(
                editor.SCI_GETSTYLEAT, start - 1
            )
            if previous_style_nr == self.styles["Comment"]["index"]:
                multiline_comm_flag = True

        for i, item in enumerate(token_list):
            if LexingThreadWorker.ABORT:
                return
            token = item[0]
            length = item[1]

            previous_token = token_list[i - 1][0] if (i > 0) else ""
            if multiline_comm_flag:
                add_parse_item(length, "Comment")
                if token == "*/":
                    multiline_comm_flag = False

            elif singleline_comm_flag:
                if "\n" in token:
                    add_parse_item(length, "Default")
                    singleline_comm_flag = False
                else:
                    add_parse_item(length, "Comment")

            elif string_flag:
                add_parse_item(length, "String")
                if token == '"' and previous_token != "\\":
                    string_flag = False

            else:
                if token == "/*":
                    multiline_comm_flag = True
                    add_parse_item(length, "Comment")

                elif token == "//":
                    singleline_comm_flag = True
                    add_parse_item(length, "Comment")

                elif token == '"' and previous_token != "\\":
                    string_flag = True
                    add_parse_item(length, "String")

                elif token in self.operator_list:
                    add_parse_item(length, "Operator")

                elif token in self.keyword_list:
                    add_parse_item(length, "Keyword")

                elif token in self.type_list:
                    add_parse_item(length, "Type")

                elif token in self.call_convention_list:
                    add_parse_item(length, "CallConvention")

                elif token in self.dunder_list or token in self.under_list:
                    add_parse_item(length, "UnderDunder")

                elif re.match(r"#\s*\w+", token):
                    add_parse_item(length, "PreProcessor")

                else:
                    if token.strip().isidentifier():
                        add_parse_item(length, "Default")
                    else:
                        add_parse_item(length, "Default")

        # Folding
        lines = editor.text().splitlines()
        # Initialize the folding variables

    #        fold_level = 0
    #        folding = False
    #        # Folding loop
    #        for line_number, line in enumerate(lines):
    #            # Add folding points as needed
    #            open_count = line.count('{')
    #            close_count = line.count('}')
    #            if close_count > 0:
    #                # Set the line's folding level first,
    #                # so that the closing curly brace is added to the fold
    #                editor.SendScintilla(
    #                    qt.QsciScintilla.SCI_SETFOLDLEVEL,
    #                    line_number,
    #                    fold_level #| qt.QsciScintilla.SC_FOLDLEVELHEADERFLAG
    #                )
    #                # Adjust the folding level
    #                fold_level += open_count
    #                fold_level -= close_count
    #            else:
    #                # Adjust the folding level first
    #                fold_level += open_count
    #                fold_level -= close_count
    #                if fold_level < 0:
    #                    fold_level = 0
    #                fold_number = line_number
    #                if '{' in line and line[ : line.find('{')].strip() != '':
    #                    fold_number = line_number + 1
    #                # Set the line's adjusted folding level
    #                editor.SendScintilla(
    #                    qt.QsciScintilla.SCI_SETFOLDLEVEL,
    #                    fold_number,
    #                    fold_level | qt.QsciScintilla.SC_FOLDLEVELHEADERFLAG
    #                )
    #        # Reset the fold level of the last line
    #        editor.SendScintilla(qt.QsciScintilla.SCI_SETFOLDLEVEL, len(lines), 0)

    def terminate_parsing_thread(self):
        if hasattr(self, "parsing_thread") and self.parsing_thread is not None:
            self.lexer_worker.abort()
            self.lexer_worker._isRunning = False
            if not qt.sip.isdeleted(self.lexer_worker):
                self.lexer_worker.setParent(None)
                self.lexer_worker.deleteLater()
            self.lexer_worker = None
            self.parsing_thread.quit()
            self.parsing_thread.wait()
            if not qt.sip.isdeleted(self.parsing_thread):
                self.parsing_thread.setParent(None)
                self.parsing_thread.deleteLater()
            self.parsing_thread = None

    def add_new_keywords(self, new_keywords):
        self.added_keyword_list.extend(new_keywords)
        self.added_keyword_list = list(set(self.added_keyword_list))
        self.styleText(0, len(self.parent().text()))

    def paint_text(self, start, parse_tuple_list):
        editor = self.parent()
        self.startStyling(start)
        for pt in parse_tuple_list:
            index = pt[0]
            length = pt[1]
            style = pt[2]
            self.setStyling(length, style)


class LexingThreadWorker(qt.QObject):
    finished = qt.pyqtSignal(int, list)

    dunder_list = CustomC.dunder_list
    under_list = CustomC.under_list
    call_convention_list = CustomC.call_convention_list
    operator_list = CustomC.operator_list
    type_list = CustomC.type_list
    keyword_list = CustomC.keyword_list
    added_keyword_list = None
    styles = CustomC.styles

    ABORT = False

    def __del__(self):
        LexingThreadWorker.ABORT = False

    def abort(self):
        LexingThreadWorker.ABORT = True

    @qt.pyqtSlot()
    def work(self):
        result = self.parse(self.text, self.start)
        if result is None:
            return
        self.finished.emit(self.start, result)

    def __init__(self, editor, text, start, additional_keywords=[]):
        super().__init__()
        self.editor = editor
        self.text = text
        self.start = start
        self.added_keyword_list = additional_keywords

    def get_symbol(self, name):
        if data.tag_database is None:
            return (None, None)
        return data.tag_database.get_tag_for_styling(name)

    def parse(self, text, start):
        # Initialization
        result = []
        index = start

        def add_parse_item(length, style, indication=None):
            nonlocal index
            if indication == True:
                indication = data.CLICK_AND_JUMP_INDICATOR
            result.append(
                (index, length, self.styles[style]["index"], indication)
            )
            index += length

        text_length = len(bytearray(text, "utf-8"))
        # Tokenizing
        pattern = re.compile(r"[*]\/|\/[*]|//|#\s*\w+|\s+|\w+|\W")
        token_list = [
            (token, len(bytearray(token, "utf-8")))
            for token in pattern.findall(text)
        ]
        # Parsing
        singleline_comm_flag = False
        multiline_comm_flag = False
        string_flag = False
        header_flag = False

        if start > 0:
            previous_style_nr = self.editor.SendScintilla(
                self.editor.SCI_GETSTYLEAT, start - 1
            )
            if previous_style_nr == self.styles["Comment"]["index"]:
                multiline_comm_flag = True

        for i, token in enumerate(token_list):
            if LexingThreadWorker.ABORT:
                return
            token_name = token[0]
            token_length = token[1]

            previous_token = token_list[i - 1][0] if (i > 0) else ""
            next_token = token_list[i - 1][0] if (i < text_length) else ""
            if multiline_comm_flag:
                add_parse_item(token_length, "Comment")
                if token_name == "*/":
                    multiline_comm_flag = False

            elif singleline_comm_flag:
                if "\n" in token_name:
                    add_parse_item(token_length, "Default")
                    singleline_comm_flag = False
                else:
                    add_parse_item(token_length, "Comment")

            elif string_flag:
                add_parse_item(token_length, "String")
                if token_name == '"' and previous_token != "\\":
                    string_flag = False

            #            elif header_flag:
            #                add_parse_item(token_length, "TriangularBracing")
            #                if token_name == ">":
            #                    header_flag = False

            else:
                if token_name == "/*":
                    multiline_comm_flag = True
                    add_parse_item(token_length, "Comment")

                elif token_name == "//":
                    singleline_comm_flag = True
                    add_parse_item(token_length, "Comment")

                elif token_name == '"' and previous_token != "\\":
                    string_flag = True
                    add_parse_item(token_length, "String")

                #                elif token_name == "<":
                #                    header_flag = True
                #                    add_parse_item(token_length, "TriangularBracing")

                elif token_name in self.operator_list:
                    add_parse_item(token_length, "Operator")

                elif token_name in self.keyword_list:
                    add_parse_item(token_length, "Keyword")

                elif token_name in self.type_list:
                    add_parse_item(token_length, "Type")

                elif token_name in self.call_convention_list:
                    add_parse_item(token_length, "CallConvention")

                elif (
                    token_name in self.dunder_list
                    or token_name in self.under_list
                ):
                    add_parse_item(token_length, "UnderDunder")

                elif re.match(r"#\s*\w+", token_name):
                    add_parse_item(token_length, "PreProcessor")

                else:
                    #                    print("'" + token_name + "'")
                    if token_name.strip().isidentifier():
                        add_parse_item(token_length, "Default")
                    else:
                        add_parse_item(token_length, "Default")

        # Return the result
        return result
