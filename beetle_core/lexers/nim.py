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


class Nim(qt.QsciLexerCustom):
    """Custom lexer for the Nim programming languages."""

    styles = {
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "BasicKeyword": {
            "name": "basic_keyword",
            "index": 2,
        },
        "TopKeyword": {
            "name": "top_keyword",
            "index": 3,
        },
        "String": {
            "name": "string",
            "index": 4,
        },
        "LongString": {
            "name": "long_string",
            "index": 5,
        },
        "Number": {
            "name": "number",
            "index": 6,
        },
        "Pragma": {
            "name": "pragma",
            "index": 7,
        },
        "Operator": {
            "name": "operator",
            "index": 8,
        },
        "Unsafe": {
            "name": "unsafe",
            "index": 9,
        },
        "Type": {
            "name": "type",
            "index": 10,
        },
        "DocumentationComment": {
            "name": "documentation_comment",
            "index": 11,
        },
        "Definition": {
            "name": "definition",
            "index": 12,
        },
        "Class": {
            "name": "class",
            "index": 13,
        },
        "KeywordOperator": {
            "name": "keyword_operator",
            "index": 14,
        },
        "CharLiteral": {
            "name": "char_literal",
            "index": 15,
        },
        "CaseOf": {
            "name": "case_of",
            "index": 16,
        },
        "UserKeyword": {
            "name": "user_keyword",
            "index": 17,
        },
        "MultilineComment": {
            "name": "multiline_comment",
            "index": 18,
        },
        "MultilineDocumentation": {
            "name": "multiline_documentation",
            "index": 19,
        },
    }

    # Basic keywords and built-in procedures and templates
    basic_keyword_list = [
        "as",
        "atomic",
        "bind",
        "sizeof",
        "break",
        "case",
        "continue",
        "converter",
        "discard",
        "distinct",
        "do",
        "echo",
        "elif",
        "else",
        "end",
        "except",
        "finally",
        "for",
        "from",
        "defined",
        "if",
        "interface",
        "iterator",
        "macro",
        "method",
        "mixin",
        "of",
        "out",
        "proc",
        "func",
        "raise",
        "ref",
        "result",
        "return",
        "template",
        "try",
        "inc",
        "dec",
        "new",
        "quit",
        "while",
        "with",
        "without",
        "yield",
        "true",
        "false",
        "assert",
        "min",
        "max",
        "newseq",
        "len",
        "pred",
        "succ",
        "contains",
        "cmp",
        "add",
        "del",
        "deepcopy",
        "shallowcopy",
        "abs",
        "clamp",
        "isnil",
        "open",
        "reopen",
        "close",
        "readall",
        "readfile",
        "writefile",
        "endoffile",
        "readline",
        "writeline",
    ]
    # Custom keyword created with templates/macros
    user_keyword_list = [
        "class",
        "namespace",
        "property",
    ]
    # Keywords that define a proc-like definition
    def_keyword_list = [
        "proc",
        "method",
        "template",
        "macro",
        "converter",
        "iterator",
    ]
    # Keywords that can define blocks
    top_keyword_list = [
        "block",
        "const",
        "export",
        "import",
        "include",
        "let",
        "static",
        "type",
        "using",
        "var",
        "when",
    ]
    # Keywords that might be unsafe/dangerous
    unsafe_keyword_list = [
        "asm",
        "addr",
        "cast",
        "ptr",
        "pointer",
        "alloc",
        "alloc0",
        "allocshared0",
        "dealloc",
        "realloc",
        "nil",
        "gc_ref",
        "gc_unref",
        "copymem",
        "zeromem",
        "equalmem",
        "movemem",
        "gc_disable",
        "gc_enable",
    ]
    # Built-in types
    type_keyword_list = [
        "int",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "float",
        "float32",
        "float64",
        "bool",
        "char",
        "string",
        "cstring",
        "pointer",
        "ordinal",
        "ptr",
        "ref",
        "expr",
        "stmt",
        "typedesc",
        "void",
        "auto",
        "any",
        "untyped",
        "typed",
        "somesignedint",
        "someunsignedint",
        "someinteger",
        "someordinal",
        "somereal",
        "somenumber",
        "range",
        "array",
        "openarray",
        "varargs",
        "seq",
        "set",
        "slice",
        "shared",
        "guarded",
        "byte",
        "natural",
        "positive",
        "rootobj",
        "rootref",
        "rooteffect",
        "timeeffect",
        "ioeffect",
        "readioeffect",
        "writeioeffect",
        "execioeffect",
        "exception",
        "systemerror",
        "ioerror",
        "oserror",
        "libraryerror",
        "resourceexhaustederror",
        "arithmeticerror",
        "divbyzeroerror",
        "overflowerror",
        "accessviolationerror",
        "assertionerror",
        "valueerror",
        "keyerror",
        "outofmemerror",
        "indexerror",
        "fielderror",
        "rangeerror",
        "stackoverflowerror",
        "reraiseerror",
        "objectassignmenterror",
        "objectconversionerror",
        "floatingpointerror",
        "floatinvalidoperror",
        "floatdivbyzeroerror",
        "floatoverflowerror",
        "floatunderflowerror",
        "floatinexacterror",
        "deadthreaderror",
        "tresult",
        "endianness",
        "taintedstring",
        "libhandle",
        "procaddr",
        "byteaddress",
        "biggestint",
        "biggestfloat",
        "clong",
        "culong",
        "cchar",
        "cschar",
        "cshort",
        "cint",
        "csize",
        "clonglong",
        "cfloat",
        "cdouble",
        "clongdouble",
        "cuchar",
        "cushort",
        "cuint",
        "culonglong",
        "cstringarray",
        "pfloat32",
        "pfloat64",
        "pint64",
        "pint32",
        "gc_strategy",
        "pframe",
        "tframe",
        "file",
        "filemode",
        "filehandle",
        "thinstance",
        "aligntype",
        "refcount",
        "object",
        "tuple",
        "enum",
    ]
    # Sign operators
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
    ]
    # Keyword operators
    keyword_operator_list = [
        "and",
        "or",
        "not",
        "xor",
        "shl",
        "shr",
        "div",
        "mod",
        "in",
        "notin",
        "is",
        "isnot",
    ]
    splitter = re.compile(r"(\{\.|\.\}|\#|\'|\"\"\"|\n|\s+|\w+|\W)")
    # Characters that autoindent one level on pressing Return/Enter
    autoindent_characters = [":", "="]

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

    def language(self):
        return "Nim"

    def description(self, style):
        if style < len(self.styles):
            description = "Custom lexer for the Nim programming languages"
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
        text = bytearray(editor.text().lower(), "utf-8")[start:end].decode(
            "utf-8"
        )
        # Loop optimizations
        setStyling = self.setStyling
        basic_kw_list = self.basic_keyword_list
        user_kw_list = self.user_keyword_list
        def_kw_list = self.def_keyword_list
        top_kw_list = self.top_keyword_list
        unsafe_kw_list = self.unsafe_keyword_list
        operator_list = self.operator_list
        keyword_operator_list = self.keyword_operator_list
        type_kw_list = self.type_keyword_list
        DEF = self.styles["Default"]["index"]
        B_KWD = self.styles["BasicKeyword"]["index"]
        T_KWD = self.styles["TopKeyword"]["index"]
        COM = self.styles["Comment"]["index"]
        STR = self.styles["String"]["index"]
        L_STR = self.styles["LongString"]["index"]
        NUM = self.styles["Number"]["index"]
        MAC = self.styles["Pragma"]["index"]
        OPE = self.styles["Operator"]["index"]
        UNS = self.styles["Unsafe"]["index"]
        TYP = self.styles["Type"]["index"]
        D_COM = self.styles["DocumentationComment"]["index"]
        DEFIN = self.styles["Definition"]["index"]
        CLS = self.styles["Class"]["index"]
        KOP = self.styles["KeywordOperator"]["index"]
        CHAR = self.styles["CharLiteral"]["index"]
        OF = self.styles["CaseOf"]["index"]
        U_KWD = self.styles["UserKeyword"]["index"]
        M_COM = self.styles["MultilineComment"]["index"]
        M_DOC = self.styles["MultilineDocumentation"]["index"]
        # Initialize various states and split the text into tokens
        commenting = False
        doc_commenting = False
        multi_doc_commenting = False
        new_commenting = False
        stringing = False
        long_stringing = False
        char_literal = False
        pragmaing = False
        case_of = False
        cls_descrition = False
        tokens = [
            (token, len(bytearray(token, "utf-8")))
            for token in self.splitter.findall(text)
        ]
        # Check if there is a style(comment, string, ...) stretching on from the previous line
        if start != 0:
            previous_style = editor.SendScintilla(
                editor.SCI_GETSTYLEAT, start - 1
            )
            if previous_style == L_STR:
                long_stringing = True
            elif previous_style == MAC:
                pragmaing = True
            elif previous_style == M_COM:
                new_commenting = True
            elif previous_style == M_DOC:
                multi_doc_commenting = True
        # Style the tokens accordingly
        for i, token in enumerate(tokens):
            #                print(str(token) + "  " + str(i))
            if commenting == True:
                # Continuation of comment
                setStyling(token[1], COM)
                # Check if comment ends
                if "\n" in token[0]:
                    commenting = False
            elif doc_commenting == True:
                # Continuation of comment
                setStyling(token[1], D_COM)
                # Check if comment ends
                if "\n" in token[0]:
                    doc_commenting = False
            elif new_commenting == True:
                # Continuation of comment
                setStyling(token[1], M_COM)
                # Check if comment ends
                if "#" in token[0] and "]" in tokens[i - 1][0]:
                    new_commenting = False
            elif multi_doc_commenting == True:
                # Continuation of comment
                setStyling(token[1], M_DOC)
                # Check if comment ends
                if (
                    "#" in token[0]
                    and "#" in tokens[i - 1][0]
                    and "]" in tokens[i - 2][0]
                ):
                    multi_doc_commenting = False
            elif stringing == True:
                # Continuation of a string
                setStyling(token[1], STR)
                # Check if string ends
                if (
                    token[0] == '"'
                    and (tokens[i - 1][0] != "\\")
                    or "\n" in token[0]
                ):
                    stringing = False
            elif long_stringing == True:
                # Continuation of a string
                setStyling(token[1], L_STR)
                # Check if string ends
                if token[0] == '"""':
                    long_stringing = False
            elif char_literal == True:
                # Check if string ends
                if (
                    "\n" in token[0]
                    or " " in token[0]
                    or "(" in token[0]
                    or ")" in token[0]
                    or "," in token[0]
                    or token[0] in operator_list
                ):
                    # Do not color the separator
                    setStyling(token[1], DEF)
                    char_literal = False
                elif token[0] == "'":
                    # Continuation of a character
                    setStyling(token[1], CHAR)
                    char_literal = False
                else:
                    setStyling(token[1], CHAR)
            elif pragmaing == True:
                # Continuation of a string
                setStyling(token[1], MAC)
                # Check if string ends
                if token[0] == ".}":
                    pragmaing = False
            elif case_of == True:
                #'Case of' parameter
                if token[0] == ":" or "\n" in token[0]:
                    setStyling(token[1], DEF)
                    case_of = False
                else:
                    setStyling(token[1], OF)
            elif cls_descrition == True:
                # Class/namespace description
                if token[0] == ":" or "\n" in token[0]:
                    setStyling(token[1], DEF)
                    cls_descrition = False
                else:
                    setStyling(token[1], CLS)
            elif token[0] == '"""':
                # Start of a multi line (long) string
                setStyling(token[1], L_STR)
                long_stringing = True
            elif token[0] == "{.":
                # Start of a multi line (long) string
                setStyling(token[1], MAC)
                pragmaing = True
            elif token[0] == '"':
                # Start of a string
                setStyling(token[1], STR)
                stringing = True
            elif token[0] == "'":
                # Start of a string
                setStyling(token[1], CHAR)
                char_literal = True
            elif token[0] in basic_kw_list:
                # Basic keyword
                setStyling(token[1], B_KWD)
                try:
                    if (token[0] == "of" and "\n" in tokens[i - 2][0]) or (
                        (token[0] == "of" and "\n" in tokens[i - 1][0])
                    ):
                        # Start of a CASE
                        case_of = True
                except IndexError:
                    case_of = False
            elif token[0] in user_kw_list:
                # User keyword
                setStyling(token[1], U_KWD)
            elif token[0] in top_kw_list:
                # Top keyword
                setStyling(token[1], T_KWD)
            elif token[0] in unsafe_kw_list:
                # Unsafe/danger keyword
                setStyling(token[1], UNS)
            elif token[0] in operator_list:
                # Operator
                setStyling(token[1], OPE)
            elif token[0] in keyword_operator_list:
                # Operator
                setStyling(token[1], KOP)
            elif token[0] in type_kw_list:
                # Operator
                setStyling(token[1], TYP)
            elif token[0] == "#":
                # Start of a comment or documentation comment
                if (
                    len(tokens) > i + 2
                    and tokens[i + 1][0] == "#"
                    and tokens[i + 2][0] == "["
                ):
                    setStyling(token[1], M_DOC)
                    multi_doc_commenting = True
                elif len(tokens) > i + 1 and tokens[i + 1][0] == "#":
                    setStyling(token[1], D_COM)
                    doc_commenting = True
                elif len(tokens) > i + 1 and tokens[i + 1][0] == "[":
                    setStyling(token[1], M_COM)
                    new_commenting = True
                else:
                    setStyling(token[1], COM)
                    commenting = True
            elif (
                (i > 1)
                and (("\n" in tokens[i - 2][0]) or ("  " in tokens[i - 2][0]))
                and (tokens[i - 1][0] == "of")
            ):
                # Case of statement
                case_of = True
                setStyling(token[1], OF)
            elif functions.is_number(token[0][0]):
                # Number
                # Check only the first character, because Nim has those weird constants e.g.: 12u8, ...)
                setStyling(token[1], NUM)
            elif (
                (i > 1)
                and (tokens[i - 2][0] in user_kw_list)
                and token[0][0].isalpha()
            ):
                # Class-like definition
                setStyling(token[1], CLS)
                cls_descrition = True
            elif (
                (i > 1)
                and (
                    tokens[i - 2][0] in def_kw_list and tokens[i - 1][0] != "("
                )
                and token[0][0].isalpha()
            ) or (
                (i > 2)
                and (
                    tokens[i - 3][0] in def_kw_list and tokens[i - 1][0] == "`"
                )
                and token[0][0].isalpha()
            ):
                # Proc-like definition
                setStyling(token[1], DEFIN)
            else:
                setStyling(token[1], DEF)
