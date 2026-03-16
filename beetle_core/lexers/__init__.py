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

import qt
import functools

from lexers.ada import *
from lexers.assembly import *
from lexers.c import *
from lexers.cython import *
from lexers.linkerscript import *
from lexers.functions import *
from lexers.nim import *
from lexers.oberon import *
from lexers.python import *
from lexers.routeros import *
from lexers.makefile import *
from lexers.text import *

"""
Lexers with theming added
"""


class AVS(qt.QsciLexerAVS):
    styles = {
        "BlockComment": {
            "name": "block_comment",
            "index": 1,
        },
        "ClipProperty": {
            "name": "clip_property",
            "index": 13,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Filter": {
            "name": "filter",
            "index": 10,
        },
        "Function": {
            "name": "function",
            "index": 12,
        },
        "Identifier": {
            "name": "identifier",
            "index": 6,
        },
        "Keyword": {
            "name": "keyword",
            "index": 9,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 14,
        },
        "LineComment": {
            "name": "line_comment",
            "index": 3,
        },
        "NestedBlockComment": {
            "name": "nested_block_comment",
            "index": 2,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 5,
        },
        "Plugin": {
            "name": "plugin",
            "index": 11,
        },
        "String": {
            "name": "string",
            "index": 7,
        },
        "TripleString": {
            "name": "triple_string",
            "index": 8,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Bash(qt.QsciLexerBash):
    styles = {
        "Backticks": {
            "name": "backticks",
            "index": 11,
        },
        "Comment": {
            "name": "comment",
            "index": 2,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 5,
        },
        "Error": {
            "name": "error",
            "index": 1,
        },
        "HereDocumentDelimiter": {
            "name": "here_document_delimiter",
            "index": 12,
        },
        "Identifier": {
            "name": "identifier",
            "index": 8,
        },
        "Keyword": {
            "name": "keyword",
            "index": 4,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 7,
        },
        "ParameterExpansion": {
            "name": "parameter_expansion",
            "index": 10,
        },
        "Scalar": {
            "name": "scalar",
            "index": 9,
        },
        "SingleQuotedHereDocument": {
            "name": "single_quoted_here_document",
            "index": 13,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 6,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Batch(qt.QsciLexerBatch):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "ExternalCommand": {
            "name": "external_command",
            "index": 5,
        },
        "HideCommandChar": {
            "name": "hide_command_char",
            "index": 4,
        },
        "Keyword": {
            "name": "keyword",
            "index": 2,
        },
        "Label": {
            "name": "label",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 7,
        },
        "Variable": {
            "name": "variable",
            "index": 6,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class CMake(qt.QsciLexerCMake):
    styles = {
        "BlockForeach": {
            "name": "block_foreach",
            "index": 10,
        },
        "BlockIf": {
            "name": "block_if",
            "index": 11,
        },
        "BlockMacro": {
            "name": "block_macro",
            "index": 12,
        },
        "BlockWhile": {
            "name": "block_while",
            "index": 9,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Function": {
            "name": "function",
            "index": 5,
        },
        "KeywordSet3": {
            "name": "keyword_set_3",
            "index": 8,
        },
        "Label": {
            "name": "label",
            "index": 7,
        },
        "Number": {
            "name": "number",
            "index": 14,
        },
        "String": {
            "name": "string",
            "index": 2,
        },
        "StringLeftQuote": {
            "name": "string_left_quote",
            "index": 3,
        },
        "StringRightQuote": {
            "name": "string_right_quote",
            "index": 4,
        },
        "StringVariable": {
            "name": "string_variable",
            "index": 13,
        },
        "Variable": {
            "name": "variable",
            "index": 6,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class CPP(qt.QsciLexerCPP):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 27,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "HashQuotedString": {
            "name": "hash_quoted_string",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentDoc": {
            "name": "inactive_comment_doc",
            "index": 67,
        },
        "InactiveCommentDocKeyword": {
            "name": "inactive_comment_doc_keyword",
            "index": 81,
        },
        "InactiveCommentDocKeywordError": {
            "name": "inactive_comment_doc_keyword_error",
            "index": 82,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveCommentLineDoc": {
            "name": "inactive_comment_line_doc",
            "index": 79,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveDoubleQuotedString": {
            "name": "inactive_double_quoted_string",
            "index": 70,
        },
        "InactiveEscapeSequence": {
            "name": "inactive_escape_sequence",
            "index": 91,
        },
        "InactiveGlobalClass": {
            "name": "inactive_global_class",
            "index": 83,
        },
        "InactiveHashQuotedString": {
            "name": "inactive_hash_quoted_string",
            "index": 86,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 80,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePreProcessor": {
            "name": "inactive_pre_processor",
            "index": 73,
        },
        "InactivePreProcessorComment": {
            "name": "inactive_pre_processor_comment",
            "index": 87,
        },
        "InactivePreProcessorCommentLineDoc": {
            "name": "inactive_pre_processor_comment_line_doc",
            "index": 88,
        },
        "InactiveRawString": {
            "name": "inactive_raw_string",
            "index": 84,
        },
        "InactiveRegex": {
            "name": "inactive_regex",
            "index": 78,
        },
        "InactiveSingleQuotedString": {
            "name": "inactive_single_quoted_string",
            "index": 71,
        },
        "InactiveTaskMarker": {
            "name": "inactive_task_marker",
            "index": 90,
        },
        "InactiveTripleQuotedVerbatimString": {
            "name": "inactive_triple_quoted_verbatim_string",
            "index": 85,
        },
        "InactiveUUID": {
            "name": "inactive_uuid",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserLiteral": {
            "name": "inactive_user_literal",
            "index": 89,
        },
        "InactiveVerbatimString": {
            "name": "inactive_verbatim_string",
            "index": 77,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "PreProcessorComment": {
            "name": "pre_processor_comment",
            "index": 23,
        },
        "PreProcessorCommentLineDoc": {
            "name": "pre_processor_comment_line_doc",
            "index": 24,
        },
        "RawString": {
            "name": "raw_string",
            "index": 20,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "TaskMarker": {
            "name": "task_marker",
            "index": 26,
        },
        "TripleQuotedVerbatimString": {
            "name": "triple_quoted_verbatim_string",
            "index": 21,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserLiteral": {
            "name": "user_literal",
            "index": 25,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class CSS(qt.QsciLexerCSS):
    styles = {
        "AtRule": {
            "name": "at_rule",
            "index": 12,
        },
        "Attribute": {
            "name": "attribute",
            "index": 16,
        },
        "CSS1Property": {
            "name": "css_1_property",
            "index": 6,
        },
        "CSS2Property": {
            "name": "css_2_property",
            "index": 15,
        },
        "CSS3Property": {
            "name": "css_3_property",
            "index": 17,
        },
        "ClassSelector": {
            "name": "class_selector",
            "index": 2,
        },
        "Comment": {
            "name": "comment",
            "index": 9,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 13,
        },
        "ExtendedCSSProperty": {
            "name": "extended_css_property",
            "index": 19,
        },
        "ExtendedPseudoClass": {
            "name": "extended_pseudo_class",
            "index": 20,
        },
        "ExtendedPseudoElement": {
            "name": "extended_pseudo_element",
            "index": 21,
        },
        "IDSelector": {
            "name": "id_selector",
            "index": 10,
        },
        "Important": {
            "name": "important",
            "index": 11,
        },
        "MediaRule": {
            "name": "media_rule",
            "index": 22,
        },
        "Operator": {
            "name": "operator",
            "index": 5,
        },
        "PseudoClass": {
            "name": "pseudo_class",
            "index": 3,
        },
        "PseudoElement": {
            "name": "pseudo_element",
            "index": 18,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 14,
        },
        "Tag": {
            "name": "tag",
            "index": 1,
        },
        "UnknownProperty": {
            "name": "unknown_property",
            "index": 7,
        },
        "UnknownPseudoClass": {
            "name": "unknown_pseudo_class",
            "index": 4,
        },
        "Value": {
            "name": "value",
            "index": 8,
        },
        "Variable": {
            "name": "variable",
            "index": 23,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class CSharp(qt.QsciLexerCSharp):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 27,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "HashQuotedString": {
            "name": "hash_quoted_string",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentDoc": {
            "name": "inactive_comment_doc",
            "index": 67,
        },
        "InactiveCommentDocKeyword": {
            "name": "inactive_comment_doc_keyword",
            "index": 81,
        },
        "InactiveCommentDocKeywordError": {
            "name": "inactive_comment_doc_keyword_error",
            "index": 82,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveCommentLineDoc": {
            "name": "inactive_comment_line_doc",
            "index": 79,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveDoubleQuotedString": {
            "name": "inactive_double_quoted_string",
            "index": 70,
        },
        "InactiveEscapeSequence": {
            "name": "inactive_escape_sequence",
            "index": 91,
        },
        "InactiveGlobalClass": {
            "name": "inactive_global_class",
            "index": 83,
        },
        "InactiveHashQuotedString": {
            "name": "inactive_hash_quoted_string",
            "index": 86,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 80,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePreProcessor": {
            "name": "inactive_pre_processor",
            "index": 73,
        },
        "InactivePreProcessorComment": {
            "name": "inactive_pre_processor_comment",
            "index": 87,
        },
        "InactivePreProcessorCommentLineDoc": {
            "name": "inactive_pre_processor_comment_line_doc",
            "index": 88,
        },
        "InactiveRawString": {
            "name": "inactive_raw_string",
            "index": 84,
        },
        "InactiveRegex": {
            "name": "inactive_regex",
            "index": 78,
        },
        "InactiveSingleQuotedString": {
            "name": "inactive_single_quoted_string",
            "index": 71,
        },
        "InactiveTaskMarker": {
            "name": "inactive_task_marker",
            "index": 90,
        },
        "InactiveTripleQuotedVerbatimString": {
            "name": "inactive_triple_quoted_verbatim_string",
            "index": 85,
        },
        "InactiveUUID": {
            "name": "inactive_uuid",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserLiteral": {
            "name": "inactive_user_literal",
            "index": 89,
        },
        "InactiveVerbatimString": {
            "name": "inactive_verbatim_string",
            "index": 77,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "PreProcessorComment": {
            "name": "pre_processor_comment",
            "index": 23,
        },
        "PreProcessorCommentLineDoc": {
            "name": "pre_processor_comment_line_doc",
            "index": 24,
        },
        "RawString": {
            "name": "raw_string",
            "index": 20,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "TaskMarker": {
            "name": "task_marker",
            "index": 26,
        },
        "TripleQuotedVerbatimString": {
            "name": "triple_quoted_verbatim_string",
            "index": 21,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserLiteral": {
            "name": "user_literal",
            "index": 25,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class CoffeeScript(qt.QsciLexerCoffeeScript):
    styles = {
        "BlockRegex": {
            "name": "block_regex",
            "index": 23,
        },
        "BlockRegexComment": {
            "name": "block_regex_comment",
            "index": 24,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentBlock": {
            "name": "comment_block",
            "index": 22,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InstanceProperty": {
            "name": "instance_property",
            "index": 25,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Custom(qt.QsciLexerCustom):
    styles = {}

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class D(qt.QsciLexerD):
    styles = {
        "BackquoteString": {
            "name": "backquote_string",
            "index": 18,
        },
        "Character": {
            "name": "character",
            "index": 12,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 16,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 17,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "CommentNested": {
            "name": "comment_nested",
            "index": 4,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Identifier": {
            "name": "identifier",
            "index": 14,
        },
        "Keyword": {
            "name": "keyword",
            "index": 6,
        },
        "KeywordDoc": {
            "name": "keyword_doc",
            "index": 8,
        },
        "KeywordSecondary": {
            "name": "keyword_secondary",
            "index": 7,
        },
        "KeywordSet5": {
            "name": "keyword_set_5",
            "index": 20,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 21,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 22,
        },
        "Number": {
            "name": "number",
            "index": 5,
        },
        "Operator": {
            "name": "operator",
            "index": 13,
        },
        "RawString": {
            "name": "raw_string",
            "index": 19,
        },
        "String": {
            "name": "string",
            "index": 10,
        },
        "Typedefs": {
            "name": "typedefs",
            "index": 9,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 11,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Diff(qt.QsciLexerDiff):
    styles = {
        "AddingPatchAdded": {
            "name": "adding_patch_added",
            "index": 8,
        },
        "AddingPatchRemoved": {
            "name": "adding_patch_removed",
            "index": 10,
        },
        "Command": {
            "name": "command",
            "index": 2,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Header": {
            "name": "header",
            "index": 3,
        },
        "LineAdded": {
            "name": "line_added",
            "index": 6,
        },
        "LineChanged": {
            "name": "line_changed",
            "index": 7,
        },
        "LineRemoved": {
            "name": "line_removed",
            "index": 5,
        },
        "Position": {
            "name": "position",
            "index": 4,
        },
        "RemovingPatchAdded": {
            "name": "removing_patch_added",
            "index": 9,
        },
        "RemovingPatchRemoved": {
            "name": "removing_patch_removed",
            "index": 11,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Fortran77(qt.QsciLexerFortran77):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Continuation": {
            "name": "continuation",
            "index": 14,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DottedOperator": {
            "name": "dotted_operator",
            "index": 12,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 4,
        },
        "ExtendedFunction": {
            "name": "extended_function",
            "index": 10,
        },
        "Identifier": {
            "name": "identifier",
            "index": 7,
        },
        "IntrinsicFunction": {
            "name": "intrinsic_function",
            "index": 9,
        },
        "Keyword": {
            "name": "keyword",
            "index": 8,
        },
        "Label": {
            "name": "label",
            "index": 13,
        },
        "Number": {
            "name": "number",
            "index": 2,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 11,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 3,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 5,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Fortran(qt.QsciLexerFortran):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Continuation": {
            "name": "continuation",
            "index": 14,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DottedOperator": {
            "name": "dotted_operator",
            "index": 12,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 4,
        },
        "ExtendedFunction": {
            "name": "extended_function",
            "index": 10,
        },
        "Identifier": {
            "name": "identifier",
            "index": 7,
        },
        "IntrinsicFunction": {
            "name": "intrinsic_function",
            "index": 9,
        },
        "Keyword": {
            "name": "keyword",
            "index": 8,
        },
        "Label": {
            "name": "label",
            "index": 13,
        },
        "Number": {
            "name": "number",
            "index": 2,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 11,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 3,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 5,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class HTML(qt.QsciLexerHTML):
    styles = {
        "ASPAtStart": {
            "name": "asp_at_start",
            "index": 15,
        },
        "ASPJavaScriptComment": {
            "name": "asp_java_script_comment",
            "index": 57,
        },
        "ASPJavaScriptCommentDoc": {
            "name": "asp_java_script_comment_doc",
            "index": 59,
        },
        "ASPJavaScriptCommentLine": {
            "name": "asp_java_script_comment_line",
            "index": 58,
        },
        "ASPJavaScriptDefault": {
            "name": "asp_java_script_default",
            "index": 56,
        },
        "ASPJavaScriptDoubleQuotedString": {
            "name": "asp_java_script_double_quoted_string",
            "index": 63,
        },
        "ASPJavaScriptKeyword": {
            "name": "asp_java_script_keyword",
            "index": 62,
        },
        "ASPJavaScriptNumber": {
            "name": "asp_java_script_number",
            "index": 60,
        },
        "ASPJavaScriptRegex": {
            "name": "asp_java_script_regex",
            "index": 67,
        },
        "ASPJavaScriptSingleQuotedString": {
            "name": "asp_java_script_single_quoted_string",
            "index": 64,
        },
        "ASPJavaScriptStart": {
            "name": "asp_java_script_start",
            "index": 55,
        },
        "ASPJavaScriptSymbol": {
            "name": "asp_java_script_symbol",
            "index": 65,
        },
        "ASPJavaScriptUnclosedString": {
            "name": "asp_java_script_unclosed_string",
            "index": 66,
        },
        "ASPJavaScriptWord": {
            "name": "asp_java_script_word",
            "index": 61,
        },
        "ASPPythonClassName": {
            "name": "asp_python_class_name",
            "index": 114,
        },
        "ASPPythonComment": {
            "name": "asp_python_comment",
            "index": 107,
        },
        "ASPPythonDefault": {
            "name": "asp_python_default",
            "index": 106,
        },
        "ASPPythonDoubleQuotedString": {
            "name": "asp_python_double_quoted_string",
            "index": 109,
        },
        "ASPPythonFunctionMethodName": {
            "name": "asp_python_function_method_name",
            "index": 115,
        },
        "ASPPythonIdentifier": {
            "name": "asp_python_identifier",
            "index": 117,
        },
        "ASPPythonKeyword": {
            "name": "asp_python_keyword",
            "index": 111,
        },
        "ASPPythonNumber": {
            "name": "asp_python_number",
            "index": 108,
        },
        "ASPPythonOperator": {
            "name": "asp_python_operator",
            "index": 116,
        },
        "ASPPythonSingleQuotedString": {
            "name": "asp_python_single_quoted_string",
            "index": 110,
        },
        "ASPPythonStart": {
            "name": "asp_python_start",
            "index": 105,
        },
        "ASPPythonTripleDoubleQuotedString": {
            "name": "asp_python_triple_double_quoted_string",
            "index": 113,
        },
        "ASPPythonTripleSingleQuotedString": {
            "name": "asp_python_triple_single_quoted_string",
            "index": 112,
        },
        "ASPStart": {
            "name": "asp_start",
            "index": 16,
        },
        "ASPVBScriptComment": {
            "name": "aspvb_script_comment",
            "index": 82,
        },
        "ASPVBScriptDefault": {
            "name": "aspvb_script_default",
            "index": 81,
        },
        "ASPVBScriptIdentifier": {
            "name": "aspvb_script_identifier",
            "index": 86,
        },
        "ASPVBScriptKeyword": {
            "name": "aspvb_script_keyword",
            "index": 84,
        },
        "ASPVBScriptNumber": {
            "name": "aspvb_script_number",
            "index": 83,
        },
        "ASPVBScriptStart": {
            "name": "aspvb_script_start",
            "index": 80,
        },
        "ASPVBScriptString": {
            "name": "aspvb_script_string",
            "index": 85,
        },
        "ASPVBScriptUnclosedString": {
            "name": "aspvb_script_unclosed_string",
            "index": 87,
        },
        "ASPXCComment": {
            "name": "aspxc_comment",
            "index": 20,
        },
        "Attribute": {
            "name": "attribute",
            "index": 3,
        },
        "CDATA": {
            "name": "cdata",
            "index": 17,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Entity": {
            "name": "entity",
            "index": 10,
        },
        "HTMLComment": {
            "name": "html_comment",
            "index": 9,
        },
        "HTMLDoubleQuotedString": {
            "name": "html_double_quoted_string",
            "index": 6,
        },
        "HTMLNumber": {
            "name": "html_number",
            "index": 5,
        },
        "HTMLSingleQuotedString": {
            "name": "html_single_quoted_string",
            "index": 7,
        },
        "HTMLValue": {
            "name": "html_value",
            "index": 19,
        },
        "JavaScriptComment": {
            "name": "java_script_comment",
            "index": 42,
        },
        "JavaScriptCommentDoc": {
            "name": "java_script_comment_doc",
            "index": 44,
        },
        "JavaScriptCommentLine": {
            "name": "java_script_comment_line",
            "index": 43,
        },
        "JavaScriptDefault": {
            "name": "java_script_default",
            "index": 41,
        },
        "JavaScriptDoubleQuotedString": {
            "name": "java_script_double_quoted_string",
            "index": 48,
        },
        "JavaScriptKeyword": {
            "name": "java_script_keyword",
            "index": 47,
        },
        "JavaScriptNumber": {
            "name": "java_script_number",
            "index": 45,
        },
        "JavaScriptRegex": {
            "name": "java_script_regex",
            "index": 52,
        },
        "JavaScriptSingleQuotedString": {
            "name": "java_script_single_quoted_string",
            "index": 49,
        },
        "JavaScriptStart": {
            "name": "java_script_start",
            "index": 40,
        },
        "JavaScriptSymbol": {
            "name": "java_script_symbol",
            "index": 50,
        },
        "JavaScriptUnclosedString": {
            "name": "java_script_unclosed_string",
            "index": 51,
        },
        "JavaScriptWord": {
            "name": "java_script_word",
            "index": 46,
        },
        "OtherInTag": {
            "name": "other_in_tag",
            "index": 8,
        },
        "PHPComment": {
            "name": "php_comment",
            "index": 124,
        },
        "PHPCommentLine": {
            "name": "php_comment_line",
            "index": 125,
        },
        "PHPDefault": {
            "name": "php_default",
            "index": 118,
        },
        "PHPDoubleQuotedString": {
            "name": "php_double_quoted_string",
            "index": 119,
        },
        "PHPDoubleQuotedVariable": {
            "name": "php_double_quoted_variable",
            "index": 126,
        },
        "PHPKeyword": {
            "name": "php_keyword",
            "index": 121,
        },
        "PHPNumber": {
            "name": "php_number",
            "index": 122,
        },
        "PHPOperator": {
            "name": "php_operator",
            "index": 127,
        },
        "PHPSingleQuotedString": {
            "name": "php_single_quoted_string",
            "index": 120,
        },
        "PHPStart": {
            "name": "php_start",
            "index": 18,
        },
        "PHPVariable": {
            "name": "php_variable",
            "index": 123,
        },
        "PythonClassName": {
            "name": "python_class_name",
            "index": 99,
        },
        "PythonComment": {
            "name": "python_comment",
            "index": 92,
        },
        "PythonDefault": {
            "name": "python_default",
            "index": 91,
        },
        "PythonDoubleQuotedString": {
            "name": "python_double_quoted_string",
            "index": 94,
        },
        "PythonFunctionMethodName": {
            "name": "python_function_method_name",
            "index": 100,
        },
        "PythonIdentifier": {
            "name": "python_identifier",
            "index": 102,
        },
        "PythonKeyword": {
            "name": "python_keyword",
            "index": 96,
        },
        "PythonNumber": {
            "name": "python_number",
            "index": 93,
        },
        "PythonOperator": {
            "name": "python_operator",
            "index": 101,
        },
        "PythonSingleQuotedString": {
            "name": "python_single_quoted_string",
            "index": 95,
        },
        "PythonStart": {
            "name": "python_start",
            "index": 90,
        },
        "PythonTripleDoubleQuotedString": {
            "name": "python_triple_double_quoted_string",
            "index": 98,
        },
        "PythonTripleSingleQuotedString": {
            "name": "python_triple_single_quoted_string",
            "index": 97,
        },
        "SGMLBlockDefault": {
            "name": "sgml_block_default",
            "index": 31,
        },
        "SGMLCommand": {
            "name": "sgml_command",
            "index": 22,
        },
        "SGMLComment": {
            "name": "sgml_comment",
            "index": 29,
        },
        "SGMLDefault": {
            "name": "sgml_default",
            "index": 21,
        },
        "SGMLDoubleQuotedString": {
            "name": "sgml_double_quoted_string",
            "index": 24,
        },
        "SGMLEntity": {
            "name": "sgml_entity",
            "index": 28,
        },
        "SGMLError": {
            "name": "sgml_error",
            "index": 26,
        },
        "SGMLParameter": {
            "name": "sgml_parameter",
            "index": 23,
        },
        "SGMLParameterComment": {
            "name": "sgml_parameter_comment",
            "index": 30,
        },
        "SGMLSingleQuotedString": {
            "name": "sgml_single_quoted_string",
            "index": 25,
        },
        "SGMLSpecial": {
            "name": "sgml_special",
            "index": 27,
        },
        "Script": {
            "name": "script",
            "index": 14,
        },
        "Tag": {
            "name": "tag",
            "index": 1,
        },
        "UnknownAttribute": {
            "name": "unknown_attribute",
            "index": 4,
        },
        "UnknownTag": {
            "name": "unknown_tag",
            "index": 2,
        },
        "VBScriptComment": {
            "name": "vb_script_comment",
            "index": 72,
        },
        "VBScriptDefault": {
            "name": "vb_script_default",
            "index": 71,
        },
        "VBScriptIdentifier": {
            "name": "vb_script_identifier",
            "index": 76,
        },
        "VBScriptKeyword": {
            "name": "vb_script_keyword",
            "index": 74,
        },
        "VBScriptNumber": {
            "name": "vb_script_number",
            "index": 73,
        },
        "VBScriptStart": {
            "name": "vb_script_start",
            "index": 70,
        },
        "VBScriptString": {
            "name": "vb_script_string",
            "index": 75,
        },
        "VBScriptUnclosedString": {
            "name": "vb_script_unclosed_string",
            "index": 77,
        },
        "XMLEnd": {
            "name": "xml_end",
            "index": 13,
        },
        "XMLStart": {
            "name": "xml_start",
            "index": 12,
        },
        "XMLTagEnd": {
            "name": "xml_tag_end",
            "index": 11,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class IDL(qt.QsciLexerIDL):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 27,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "HashQuotedString": {
            "name": "hash_quoted_string",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentDoc": {
            "name": "inactive_comment_doc",
            "index": 67,
        },
        "InactiveCommentDocKeyword": {
            "name": "inactive_comment_doc_keyword",
            "index": 81,
        },
        "InactiveCommentDocKeywordError": {
            "name": "inactive_comment_doc_keyword_error",
            "index": 82,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveCommentLineDoc": {
            "name": "inactive_comment_line_doc",
            "index": 79,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveDoubleQuotedString": {
            "name": "inactive_double_quoted_string",
            "index": 70,
        },
        "InactiveEscapeSequence": {
            "name": "inactive_escape_sequence",
            "index": 91,
        },
        "InactiveGlobalClass": {
            "name": "inactive_global_class",
            "index": 83,
        },
        "InactiveHashQuotedString": {
            "name": "inactive_hash_quoted_string",
            "index": 86,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 80,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePreProcessor": {
            "name": "inactive_pre_processor",
            "index": 73,
        },
        "InactivePreProcessorComment": {
            "name": "inactive_pre_processor_comment",
            "index": 87,
        },
        "InactivePreProcessorCommentLineDoc": {
            "name": "inactive_pre_processor_comment_line_doc",
            "index": 88,
        },
        "InactiveRawString": {
            "name": "inactive_raw_string",
            "index": 84,
        },
        "InactiveRegex": {
            "name": "inactive_regex",
            "index": 78,
        },
        "InactiveSingleQuotedString": {
            "name": "inactive_single_quoted_string",
            "index": 71,
        },
        "InactiveTaskMarker": {
            "name": "inactive_task_marker",
            "index": 90,
        },
        "InactiveTripleQuotedVerbatimString": {
            "name": "inactive_triple_quoted_verbatim_string",
            "index": 85,
        },
        "InactiveUUID": {
            "name": "inactive_uuid",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserLiteral": {
            "name": "inactive_user_literal",
            "index": 89,
        },
        "InactiveVerbatimString": {
            "name": "inactive_verbatim_string",
            "index": 77,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "PreProcessorComment": {
            "name": "pre_processor_comment",
            "index": 23,
        },
        "PreProcessorCommentLineDoc": {
            "name": "pre_processor_comment_line_doc",
            "index": 24,
        },
        "RawString": {
            "name": "raw_string",
            "index": 20,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "TaskMarker": {
            "name": "task_marker",
            "index": 26,
        },
        "TripleQuotedVerbatimString": {
            "name": "triple_quoted_verbatim_string",
            "index": 21,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserLiteral": {
            "name": "user_literal",
            "index": 25,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class JSON(qt.QsciLexerJSON):
    styles = {
        "CommentBlock": {
            "name": "comment_block",
            "index": 7,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 6,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Error": {
            "name": "error",
            "index": 13,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 5,
        },
        "IRI": {
            "name": "iri",
            "index": 9,
        },
        "IRICompact": {
            "name": "iri_compact",
            "index": 10,
        },
        "Keyword": {
            "name": "keyword",
            "index": 11,
        },
        "KeywordLD": {
            "name": "keyword_ld",
            "index": 12,
        },
        "Number": {
            "name": "number",
            "index": 1,
        },
        "Operator": {
            "name": "operator",
            "index": 8,
        },
        "Property": {
            "name": "property",
            "index": 4,
        },
        "String": {
            "name": "string",
            "index": 2,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 3,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Java(qt.QsciLexerJava):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 27,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "HashQuotedString": {
            "name": "hash_quoted_string",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentDoc": {
            "name": "inactive_comment_doc",
            "index": 67,
        },
        "InactiveCommentDocKeyword": {
            "name": "inactive_comment_doc_keyword",
            "index": 81,
        },
        "InactiveCommentDocKeywordError": {
            "name": "inactive_comment_doc_keyword_error",
            "index": 82,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveCommentLineDoc": {
            "name": "inactive_comment_line_doc",
            "index": 79,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveDoubleQuotedString": {
            "name": "inactive_double_quoted_string",
            "index": 70,
        },
        "InactiveEscapeSequence": {
            "name": "inactive_escape_sequence",
            "index": 91,
        },
        "InactiveGlobalClass": {
            "name": "inactive_global_class",
            "index": 83,
        },
        "InactiveHashQuotedString": {
            "name": "inactive_hash_quoted_string",
            "index": 86,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 80,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePreProcessor": {
            "name": "inactive_pre_processor",
            "index": 73,
        },
        "InactivePreProcessorComment": {
            "name": "inactive_pre_processor_comment",
            "index": 87,
        },
        "InactivePreProcessorCommentLineDoc": {
            "name": "inactive_pre_processor_comment_line_doc",
            "index": 88,
        },
        "InactiveRawString": {
            "name": "inactive_raw_string",
            "index": 84,
        },
        "InactiveRegex": {
            "name": "inactive_regex",
            "index": 78,
        },
        "InactiveSingleQuotedString": {
            "name": "inactive_single_quoted_string",
            "index": 71,
        },
        "InactiveTaskMarker": {
            "name": "inactive_task_marker",
            "index": 90,
        },
        "InactiveTripleQuotedVerbatimString": {
            "name": "inactive_triple_quoted_verbatim_string",
            "index": 85,
        },
        "InactiveUUID": {
            "name": "inactive_uuid",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserLiteral": {
            "name": "inactive_user_literal",
            "index": 89,
        },
        "InactiveVerbatimString": {
            "name": "inactive_verbatim_string",
            "index": 77,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "PreProcessorComment": {
            "name": "pre_processor_comment",
            "index": 23,
        },
        "PreProcessorCommentLineDoc": {
            "name": "pre_processor_comment_line_doc",
            "index": 24,
        },
        "RawString": {
            "name": "raw_string",
            "index": 20,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "TaskMarker": {
            "name": "task_marker",
            "index": 26,
        },
        "TripleQuotedVerbatimString": {
            "name": "triple_quoted_verbatim_string",
            "index": 21,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserLiteral": {
            "name": "user_literal",
            "index": 25,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class JavaScript(qt.QsciLexerJavaScript):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineDoc": {
            "name": "comment_line_doc",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "EscapeSequence": {
            "name": "escape_sequence",
            "index": 27,
        },
        "GlobalClass": {
            "name": "global_class",
            "index": 19,
        },
        "HashQuotedString": {
            "name": "hash_quoted_string",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentDoc": {
            "name": "inactive_comment_doc",
            "index": 67,
        },
        "InactiveCommentDocKeyword": {
            "name": "inactive_comment_doc_keyword",
            "index": 81,
        },
        "InactiveCommentDocKeywordError": {
            "name": "inactive_comment_doc_keyword_error",
            "index": 82,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveCommentLineDoc": {
            "name": "inactive_comment_line_doc",
            "index": 79,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveDoubleQuotedString": {
            "name": "inactive_double_quoted_string",
            "index": 70,
        },
        "InactiveEscapeSequence": {
            "name": "inactive_escape_sequence",
            "index": 91,
        },
        "InactiveGlobalClass": {
            "name": "inactive_global_class",
            "index": 83,
        },
        "InactiveHashQuotedString": {
            "name": "inactive_hash_quoted_string",
            "index": 86,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 80,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePreProcessor": {
            "name": "inactive_pre_processor",
            "index": 73,
        },
        "InactivePreProcessorComment": {
            "name": "inactive_pre_processor_comment",
            "index": 87,
        },
        "InactivePreProcessorCommentLineDoc": {
            "name": "inactive_pre_processor_comment_line_doc",
            "index": 88,
        },
        "InactiveRawString": {
            "name": "inactive_raw_string",
            "index": 84,
        },
        "InactiveRegex": {
            "name": "inactive_regex",
            "index": 78,
        },
        "InactiveSingleQuotedString": {
            "name": "inactive_single_quoted_string",
            "index": 71,
        },
        "InactiveTaskMarker": {
            "name": "inactive_task_marker",
            "index": 90,
        },
        "InactiveTripleQuotedVerbatimString": {
            "name": "inactive_triple_quoted_verbatim_string",
            "index": 85,
        },
        "InactiveUUID": {
            "name": "inactive_uuid",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserLiteral": {
            "name": "inactive_user_literal",
            "index": 89,
        },
        "InactiveVerbatimString": {
            "name": "inactive_verbatim_string",
            "index": 77,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 9,
        },
        "PreProcessorComment": {
            "name": "pre_processor_comment",
            "index": 23,
        },
        "PreProcessorCommentLineDoc": {
            "name": "pre_processor_comment_line_doc",
            "index": 24,
        },
        "RawString": {
            "name": "raw_string",
            "index": 20,
        },
        "Regex": {
            "name": "regex",
            "index": 14,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "TaskMarker": {
            "name": "task_marker",
            "index": 26,
        },
        "TripleQuotedVerbatimString": {
            "name": "triple_quoted_verbatim_string",
            "index": 21,
        },
        "UUID": {
            "name": "uuid",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserLiteral": {
            "name": "user_literal",
            "index": 25,
        },
        "VerbatimString": {
            "name": "verbatim_string",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Lua(qt.QsciLexerLua):
    styles = {
        "BasicFunctions": {
            "name": "basic_functions",
            "index": 13,
        },
        "Character": {
            "name": "character",
            "index": 7,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CoroutinesIOSystemFacilities": {
            "name": "coroutines_io_system_facilities",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet5": {
            "name": "keyword_set_5",
            "index": 16,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 17,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 18,
        },
        "KeywordSet8": {
            "name": "keyword_set_8",
            "index": 19,
        },
        "Label": {
            "name": "label",
            "index": 20,
        },
        "LineComment": {
            "name": "line_comment",
            "index": 2,
        },
        "LiteralString": {
            "name": "literal_string",
            "index": 8,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "Preprocessor": {
            "name": "preprocessor",
            "index": 9,
        },
        "String": {
            "name": "string",
            "index": 6,
        },
        "StringTableMathsFunctions": {
            "name": "string_table_maths_functions",
            "index": 14,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Makefile(qt.QsciLexerMakefile):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Error": {
            "name": "error",
            "index": 9,
        },
        "Operator": {
            "name": "operator",
            "index": 4,
        },
        "Preprocessor": {
            "name": "preprocessor",
            "index": 2,
        },
        "Target": {
            "name": "target",
            "index": 5,
        },
        "Variable": {
            "name": "variable",
            "index": 3,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Markdown(qt.QsciLexerMarkdown):
    styles = {
        "BlockQuote": {
            "name": "block_quote",
            "index": 15,
        },
        "CodeBackticks": {
            "name": "code_backticks",
            "index": 19,
        },
        "CodeBlock": {
            "name": "code_block",
            "index": 21,
        },
        "CodeDoubleBackticks": {
            "name": "code_double_backticks",
            "index": 20,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "EmphasisAsterisks": {
            "name": "emphasis_asterisks",
            "index": 4,
        },
        "EmphasisUnderscores": {
            "name": "emphasis_underscores",
            "index": 5,
        },
        "Header1": {
            "name": "header_1",
            "index": 6,
        },
        "Header2": {
            "name": "header_2",
            "index": 7,
        },
        "Header3": {
            "name": "header_3",
            "index": 8,
        },
        "Header4": {
            "name": "header_4",
            "index": 9,
        },
        "Header5": {
            "name": "header_5",
            "index": 10,
        },
        "Header6": {
            "name": "header_6",
            "index": 11,
        },
        "HorizontalRule": {
            "name": "horizontal_rule",
            "index": 17,
        },
        "Link": {
            "name": "link",
            "index": 18,
        },
        "OrderedListItem": {
            "name": "ordered_list_item",
            "index": 14,
        },
        "Prechar": {
            "name": "prechar",
            "index": 12,
        },
        "Special": {
            "name": "special",
            "index": 1,
        },
        "StrikeOut": {
            "name": "strike_out",
            "index": 16,
        },
        "StrongEmphasisAsterisks": {
            "name": "strong_emphasis_asterisks",
            "index": 2,
        },
        "StrongEmphasisUnderscores": {
            "name": "strong_emphasis_underscores",
            "index": 3,
        },
        "UnorderedListItem": {
            "name": "unordered_list_item",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Matlab(qt.QsciLexerMatlab):
    styles = {
        "Command": {
            "name": "command",
            "index": 2,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 8,
        },
        "Identifier": {
            "name": "identifier",
            "index": 7,
        },
        "Keyword": {
            "name": "keyword",
            "index": 4,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 5,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Octave(qt.QsciLexerOctave):
    styles = {
        "Command": {
            "name": "command",
            "index": 2,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 8,
        },
        "Identifier": {
            "name": "identifier",
            "index": 7,
        },
        "Keyword": {
            "name": "keyword",
            "index": 4,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 5,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class PO(qt.QsciLexerPO):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Flags": {
            "name": "flags",
            "index": 11,
        },
        "Fuzzy": {
            "name": "fuzzy",
            "index": 8,
        },
        "MessageContext": {
            "name": "message_context",
            "index": 6,
        },
        "MessageContextText": {
            "name": "message_context_text",
            "index": 7,
        },
        "MessageContextTextEOL": {
            "name": "message_context_text_eol",
            "index": 14,
        },
        "MessageId": {
            "name": "message_id",
            "index": 2,
        },
        "MessageIdText": {
            "name": "message_id_text",
            "index": 3,
        },
        "MessageIdTextEOL": {
            "name": "message_id_text_eol",
            "index": 12,
        },
        "MessageString": {
            "name": "message_string",
            "index": 4,
        },
        "MessageStringText": {
            "name": "message_string_text",
            "index": 5,
        },
        "MessageStringTextEOL": {
            "name": "message_string_text_eol",
            "index": 13,
        },
        "ProgrammerComment": {
            "name": "programmer_comment",
            "index": 9,
        },
        "Reference": {
            "name": "reference",
            "index": 10,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class POV(qt.QsciLexerPOV):
    styles = {
        "BadDirective": {
            "name": "bad_directive",
            "index": 9,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Directive": {
            "name": "directive",
            "index": 8,
        },
        "Identifier": {
            "name": "identifier",
            "index": 5,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 14,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 15,
        },
        "KeywordSet8": {
            "name": "keyword_set_8",
            "index": 16,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "ObjectsCSGAppearance": {
            "name": "objects_csg_appearance",
            "index": 10,
        },
        "Operator": {
            "name": "operator",
            "index": 4,
        },
        "PredefinedFunctions": {
            "name": "predefined_functions",
            "index": 13,
        },
        "PredefinedIdentifiers": {
            "name": "predefined_identifiers",
            "index": 12,
        },
        "String": {
            "name": "string",
            "index": 6,
        },
        "TypesModifiersItems": {
            "name": "types_modifiers_items",
            "index": 11,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 7,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Pascal(qt.QsciLexerPascal):
    styles = {
        "Asm": {
            "name": "asm",
            "index": 14,
        },
        "Character": {
            "name": "character",
            "index": 12,
        },
        "Comment": {
            "name": "comment",
            "index": 2,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 4,
        },
        "CommentParenthesis": {
            "name": "comment_parenthesis",
            "index": 3,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "HexNumber": {
            "name": "hex_number",
            "index": 8,
        },
        "Identifier": {
            "name": "identifier",
            "index": 1,
        },
        "Keyword": {
            "name": "keyword",
            "index": 9,
        },
        "Number": {
            "name": "number",
            "index": 7,
        },
        "Operator": {
            "name": "operator",
            "index": 13,
        },
        "PreProcessor": {
            "name": "pre_processor",
            "index": 5,
        },
        "PreProcessorParenthesis": {
            "name": "pre_processor_parenthesis",
            "index": 6,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 10,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 11,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Perl(qt.QsciLexerPerl):
    styles = {
        "Array": {
            "name": "array",
            "index": 13,
        },
        "BacktickHereDocument": {
            "name": "backtick_here_document",
            "index": 25,
        },
        "BacktickHereDocumentVar": {
            "name": "backtick_here_document_var",
            "index": 62,
        },
        "Backticks": {
            "name": "backticks",
            "index": 20,
        },
        "BackticksVar": {
            "name": "backticks_var",
            "index": 57,
        },
        "Comment": {
            "name": "comment",
            "index": 2,
        },
        "DataSection": {
            "name": "data_section",
            "index": 21,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedHereDocument": {
            "name": "double_quoted_here_document",
            "index": 24,
        },
        "DoubleQuotedHereDocumentVar": {
            "name": "double_quoted_here_document_var",
            "index": 61,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "DoubleQuotedStringVar": {
            "name": "double_quoted_string_var",
            "index": 43,
        },
        "Error": {
            "name": "error",
            "index": 1,
        },
        "FormatBody": {
            "name": "format_body",
            "index": 42,
        },
        "FormatIdentifier": {
            "name": "format_identifier",
            "index": 41,
        },
        "Hash": {
            "name": "hash",
            "index": 14,
        },
        "HereDocumentDelimiter": {
            "name": "here_document_delimiter",
            "index": 22,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "POD": {
            "name": "pod",
            "index": 3,
        },
        "PODVerbatim": {
            "name": "pod_verbatim",
            "index": 31,
        },
        "QuotedStringQ": {
            "name": "quoted_string_q",
            "index": 26,
        },
        "QuotedStringQQ": {
            "name": "quoted_string_qq",
            "index": 27,
        },
        "QuotedStringQQVar": {
            "name": "quoted_string_qq_var",
            "index": 64,
        },
        "QuotedStringQR": {
            "name": "quoted_string_qr",
            "index": 29,
        },
        "QuotedStringQRVar": {
            "name": "quoted_string_qr_var",
            "index": 66,
        },
        "QuotedStringQW": {
            "name": "quoted_string_qw",
            "index": 30,
        },
        "QuotedStringQX": {
            "name": "quoted_string_qx",
            "index": 28,
        },
        "QuotedStringQXVar": {
            "name": "quoted_string_qx_var",
            "index": 65,
        },
        "Regex": {
            "name": "regex",
            "index": 17,
        },
        "RegexVar": {
            "name": "regex_var",
            "index": 54,
        },
        "Scalar": {
            "name": "scalar",
            "index": 12,
        },
        "SingleQuotedHereDocument": {
            "name": "single_quoted_here_document",
            "index": 23,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "SubroutinePrototype": {
            "name": "subroutine_prototype",
            "index": 40,
        },
        "Substitution": {
            "name": "substitution",
            "index": 18,
        },
        "SubstitutionVar": {
            "name": "substitution_var",
            "index": 55,
        },
        "SymbolTable": {
            "name": "symbol_table",
            "index": 15,
        },
        "Translation": {
            "name": "translation",
            "index": 44,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class PostScript(qt.QsciLexerPostScript):
    styles = {
        "ArrayParenthesis": {
            "name": "array_parenthesis",
            "index": 9,
        },
        "BadStringCharacter": {
            "name": "bad_string_character",
            "index": 15,
        },
        "Base85String": {
            "name": "base_85_string",
            "index": 14,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "DSCComment": {
            "name": "dsc_comment",
            "index": 2,
        },
        "DSCCommentValue": {
            "name": "dsc_comment_value",
            "index": 3,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DictionaryParenthesis": {
            "name": "dictionary_parenthesis",
            "index": 10,
        },
        "HexString": {
            "name": "hex_string",
            "index": 13,
        },
        "ImmediateEvalLiteral": {
            "name": "immediate_eval_literal",
            "index": 8,
        },
        "Keyword": {
            "name": "keyword",
            "index": 6,
        },
        "Literal": {
            "name": "literal",
            "index": 7,
        },
        "Name": {
            "name": "name",
            "index": 5,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "ProcedureParenthesis": {
            "name": "procedure_parenthesis",
            "index": 11,
        },
        "Text": {
            "name": "text",
            "index": 12,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Properties(qt.QsciLexerProperties):
    styles = {
        "Assignment": {
            "name": "assignment",
            "index": 3,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DefaultValue": {
            "name": "default_value",
            "index": 4,
        },
        "Key": {
            "name": "key",
            "index": 5,
        },
        "Section": {
            "name": "section",
            "index": 2,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Properties(qt.QsciLexerProperties):
    styles = {
        "Assignment": {
            "name": "assignment",
            "index": 3,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DefaultValue": {
            "name": "default_value",
            "index": 4,
        },
        "Key": {
            "name": "key",
            "index": 5,
        },
        "Section": {
            "name": "section",
            "index": 2,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Ruby(qt.QsciLexerRuby):
    styles = {
        "Backticks": {
            "name": "backticks",
            "index": 18,
        },
        "ClassName": {
            "name": "class_name",
            "index": 8,
        },
        "ClassVariable": {
            "name": "class_variable",
            "index": 17,
        },
        "Comment": {
            "name": "comment",
            "index": 2,
        },
        "DataSection": {
            "name": "data_section",
            "index": 19,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DemotedKeyword": {
            "name": "demoted_keyword",
            "index": 29,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "Error": {
            "name": "error",
            "index": 1,
        },
        "FunctionMethodName": {
            "name": "function_method_name",
            "index": 9,
        },
        "Global": {
            "name": "global",
            "index": 13,
        },
        "HereDocument": {
            "name": "here_document",
            "index": 21,
        },
        "HereDocumentDelimiter": {
            "name": "here_document_delimiter",
            "index": 20,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InstanceVariable": {
            "name": "instance_variable",
            "index": 16,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "ModuleName": {
            "name": "module_name",
            "index": 15,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "POD": {
            "name": "pod",
            "index": 3,
        },
        "PercentStringQ": {
            "name": "percent_string_q",
            "index": 25,
        },
        "PercentStringq": {
            "name": "percent_stringq",
            "index": 24,
        },
        "PercentStringr": {
            "name": "percent_stringr",
            "index": 27,
        },
        "PercentStringw": {
            "name": "percent_stringw",
            "index": 28,
        },
        "PercentStringx": {
            "name": "percent_stringx",
            "index": 26,
        },
        "Regex": {
            "name": "regex",
            "index": 12,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
        "Stderr": {
            "name": "stderr",
            "index": 40,
        },
        "Stdin": {
            "name": "stdin",
            "index": 30,
        },
        "Stdout": {
            "name": "stdout",
            "index": 31,
        },
        "Symbol": {
            "name": "symbol",
            "index": 14,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class SQL(qt.QsciLexerSQL):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentDoc": {
            "name": "comment_doc",
            "index": 3,
        },
        "CommentDocKeyword": {
            "name": "comment_doc_keyword",
            "index": 17,
        },
        "CommentDocKeywordError": {
            "name": "comment_doc_keyword_error",
            "index": 18,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "CommentLineHash": {
            "name": "comment_line_hash",
            "index": 15,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DoubleQuotedString": {
            "name": "double_quoted_string",
            "index": 6,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet5": {
            "name": "keyword_set_5",
            "index": 19,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 20,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 21,
        },
        "KeywordSet8": {
            "name": "keyword_set_8",
            "index": 22,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PlusComment": {
            "name": "plus_comment",
            "index": 13,
        },
        "PlusKeyword": {
            "name": "plus_keyword",
            "index": 8,
        },
        "PlusPrompt": {
            "name": "plus_prompt",
            "index": 9,
        },
        "QuotedIdentifier": {
            "name": "quoted_identifier",
            "index": 23,
        },
        "QuotedOperator": {
            "name": "quoted_operator",
            "index": 24,
        },
        "SingleQuotedString": {
            "name": "single_quoted_string",
            "index": 7,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Spice(qt.QsciLexerSpice):
    styles = {
        "Command": {
            "name": "command",
            "index": 2,
        },
        "Comment": {
            "name": "comment",
            "index": 8,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Delimiter": {
            "name": "delimiter",
            "index": 6,
        },
        "Function": {
            "name": "function",
            "index": 3,
        },
        "Identifier": {
            "name": "identifier",
            "index": 1,
        },
        "Number": {
            "name": "number",
            "index": 5,
        },
        "Parameter": {
            "name": "parameter",
            "index": 4,
        },
        "Value": {
            "name": "value",
            "index": 7,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class TCL(qt.QsciLexerTCL):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentBlock": {
            "name": "comment_block",
            "index": 21,
        },
        "CommentBox": {
            "name": "comment_box",
            "index": 20,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "ExpandKeyword": {
            "name": "expand_keyword",
            "index": 11,
        },
        "ITCLKeyword": {
            "name": "itcl_keyword",
            "index": 14,
        },
        "Identifier": {
            "name": "identifier",
            "index": 7,
        },
        "KeywordSet6": {
            "name": "keyword_set_6",
            "index": 16,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 17,
        },
        "KeywordSet8": {
            "name": "keyword_set_8",
            "index": 18,
        },
        "KeywordSet9": {
            "name": "keyword_set_9",
            "index": 19,
        },
        "Modifier": {
            "name": "modifier",
            "index": 10,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 6,
        },
        "QuotedKeyword": {
            "name": "quoted_keyword",
            "index": 4,
        },
        "QuotedString": {
            "name": "quoted_string",
            "index": 5,
        },
        "Substitution": {
            "name": "substitution",
            "index": 8,
        },
        "SubstitutionBrace": {
            "name": "substitution_brace",
            "index": 9,
        },
        "TCLKeyword": {
            "name": "tcl_keyword",
            "index": 12,
        },
        "TkCommand": {
            "name": "tk_command",
            "index": 15,
        },
        "TkKeyword": {
            "name": "tk_keyword",
            "index": 13,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class TeX(qt.QsciLexerTeX):
    styles = {
        "Command": {
            "name": "command",
            "index": 4,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Group": {
            "name": "group",
            "index": 2,
        },
        "Special": {
            "name": "special",
            "index": 1,
        },
        "Symbol": {
            "name": "symbol",
            "index": 3,
        },
        "Text": {
            "name": "text",
            "index": 5,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class VHDL(qt.QsciLexerVHDL):
    styles = {
        "Attribute": {
            "name": "attribute",
            "index": 10,
        },
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentBlock": {
            "name": "comment_block",
            "index": 15,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Identifier": {
            "name": "identifier",
            "index": 6,
        },
        "Keyword": {
            "name": "keyword",
            "index": 8,
        },
        "KeywordSet7": {
            "name": "keyword_set_7",
            "index": 14,
        },
        "Number": {
            "name": "number",
            "index": 3,
        },
        "Operator": {
            "name": "operator",
            "index": 5,
        },
        "StandardFunction": {
            "name": "standard_function",
            "index": 11,
        },
        "StandardOperator": {
            "name": "standard_operator",
            "index": 9,
        },
        "StandardPackage": {
            "name": "standard_package",
            "index": 12,
        },
        "StandardType": {
            "name": "standard_type",
            "index": 13,
        },
        "String": {
            "name": "string",
            "index": 4,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 7,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class Verilog(qt.QsciLexerVerilog):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "CommentBang": {
            "name": "comment_bang",
            "index": 3,
        },
        "CommentKeyword": {
            "name": "comment_keyword",
            "index": 20,
        },
        "CommentLine": {
            "name": "comment_line",
            "index": 2,
        },
        "DeclareInputOutputPort": {
            "name": "declare_input_output_port",
            "index": 23,
        },
        "DeclareInputPort": {
            "name": "declare_input_port",
            "index": 21,
        },
        "DeclareOutputPort": {
            "name": "declare_output_port",
            "index": 22,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Identifier": {
            "name": "identifier",
            "index": 11,
        },
        "InactiveComment": {
            "name": "inactive_comment",
            "index": 65,
        },
        "InactiveCommentBang": {
            "name": "inactive_comment_bang",
            "index": 67,
        },
        "InactiveCommentKeyword": {
            "name": "inactive_comment_keyword",
            "index": 84,
        },
        "InactiveCommentLine": {
            "name": "inactive_comment_line",
            "index": 66,
        },
        "InactiveDeclareInputOutputPort": {
            "name": "inactive_declare_input_output_port",
            "index": 87,
        },
        "InactiveDeclareInputPort": {
            "name": "inactive_declare_input_port",
            "index": 85,
        },
        "InactiveDeclareOutputPort": {
            "name": "inactive_declare_output_port",
            "index": 86,
        },
        "InactiveDefault": {
            "name": "inactive_default",
            "index": 64,
        },
        "InactiveIdentifier": {
            "name": "inactive_identifier",
            "index": 75,
        },
        "InactiveKeyword": {
            "name": "inactive_keyword",
            "index": 69,
        },
        "InactiveKeywordSet2": {
            "name": "inactive_keyword_set_2",
            "index": 71,
        },
        "InactiveNumber": {
            "name": "inactive_number",
            "index": 68,
        },
        "InactiveOperator": {
            "name": "inactive_operator",
            "index": 74,
        },
        "InactivePortConnection": {
            "name": "inactive_port_connection",
            "index": 88,
        },
        "InactivePreprocessor": {
            "name": "inactive_preprocessor",
            "index": 73,
        },
        "InactiveString": {
            "name": "inactive_string",
            "index": 70,
        },
        "InactiveSystemTask": {
            "name": "inactive_system_task",
            "index": 72,
        },
        "InactiveUnclosedString": {
            "name": "inactive_unclosed_string",
            "index": 76,
        },
        "InactiveUserKeywordSet": {
            "name": "inactive_user_keyword_set",
            "index": 83,
        },
        "Keyword": {
            "name": "keyword",
            "index": 5,
        },
        "KeywordSet2": {
            "name": "keyword_set_2",
            "index": 7,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 10,
        },
        "PortConnection": {
            "name": "port_connection",
            "index": 24,
        },
        "Preprocessor": {
            "name": "preprocessor",
            "index": 9,
        },
        "String": {
            "name": "string",
            "index": 6,
        },
        "SystemTask": {
            "name": "system_task",
            "index": 8,
        },
        "UnclosedString": {
            "name": "unclosed_string",
            "index": 12,
        },
        "UserKeywordSet": {
            "name": "user_keyword_set",
            "index": 19,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class XML(qt.QsciLexerXML):
    styles = {
        "ASPAtStart": {
            "name": "asp_at_start",
            "index": 15,
        },
        "ASPJavaScriptComment": {
            "name": "asp_java_script_comment",
            "index": 57,
        },
        "ASPJavaScriptCommentDoc": {
            "name": "asp_java_script_comment_doc",
            "index": 59,
        },
        "ASPJavaScriptCommentLine": {
            "name": "asp_java_script_comment_line",
            "index": 58,
        },
        "ASPJavaScriptDefault": {
            "name": "asp_java_script_default",
            "index": 56,
        },
        "ASPJavaScriptDoubleQuotedString": {
            "name": "asp_java_script_double_quoted_string",
            "index": 63,
        },
        "ASPJavaScriptKeyword": {
            "name": "asp_java_script_keyword",
            "index": 62,
        },
        "ASPJavaScriptNumber": {
            "name": "asp_java_script_number",
            "index": 60,
        },
        "ASPJavaScriptRegex": {
            "name": "asp_java_script_regex",
            "index": 67,
        },
        "ASPJavaScriptSingleQuotedString": {
            "name": "asp_java_script_single_quoted_string",
            "index": 64,
        },
        "ASPJavaScriptStart": {
            "name": "asp_java_script_start",
            "index": 55,
        },
        "ASPJavaScriptSymbol": {
            "name": "asp_java_script_symbol",
            "index": 65,
        },
        "ASPJavaScriptUnclosedString": {
            "name": "asp_java_script_unclosed_string",
            "index": 66,
        },
        "ASPJavaScriptWord": {
            "name": "asp_java_script_word",
            "index": 61,
        },
        "ASPPythonClassName": {
            "name": "asp_python_class_name",
            "index": 114,
        },
        "ASPPythonComment": {
            "name": "asp_python_comment",
            "index": 107,
        },
        "ASPPythonDefault": {
            "name": "asp_python_default",
            "index": 106,
        },
        "ASPPythonDoubleQuotedString": {
            "name": "asp_python_double_quoted_string",
            "index": 109,
        },
        "ASPPythonFunctionMethodName": {
            "name": "asp_python_function_method_name",
            "index": 115,
        },
        "ASPPythonIdentifier": {
            "name": "asp_python_identifier",
            "index": 117,
        },
        "ASPPythonKeyword": {
            "name": "asp_python_keyword",
            "index": 111,
        },
        "ASPPythonNumber": {
            "name": "asp_python_number",
            "index": 108,
        },
        "ASPPythonOperator": {
            "name": "asp_python_operator",
            "index": 116,
        },
        "ASPPythonSingleQuotedString": {
            "name": "asp_python_single_quoted_string",
            "index": 110,
        },
        "ASPPythonStart": {
            "name": "asp_python_start",
            "index": 105,
        },
        "ASPPythonTripleDoubleQuotedString": {
            "name": "asp_python_triple_double_quoted_string",
            "index": 113,
        },
        "ASPPythonTripleSingleQuotedString": {
            "name": "asp_python_triple_single_quoted_string",
            "index": 112,
        },
        "ASPStart": {
            "name": "asp_start",
            "index": 16,
        },
        "ASPVBScriptComment": {
            "name": "aspvb_script_comment",
            "index": 82,
        },
        "ASPVBScriptDefault": {
            "name": "aspvb_script_default",
            "index": 81,
        },
        "ASPVBScriptIdentifier": {
            "name": "aspvb_script_identifier",
            "index": 86,
        },
        "ASPVBScriptKeyword": {
            "name": "aspvb_script_keyword",
            "index": 84,
        },
        "ASPVBScriptNumber": {
            "name": "aspvb_script_number",
            "index": 83,
        },
        "ASPVBScriptStart": {
            "name": "aspvb_script_start",
            "index": 80,
        },
        "ASPVBScriptString": {
            "name": "aspvb_script_string",
            "index": 85,
        },
        "ASPVBScriptUnclosedString": {
            "name": "aspvb_script_unclosed_string",
            "index": 87,
        },
        "ASPXCComment": {
            "name": "aspxc_comment",
            "index": 20,
        },
        "Attribute": {
            "name": "attribute",
            "index": 3,
        },
        "CDATA": {
            "name": "cdata",
            "index": 17,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "Entity": {
            "name": "entity",
            "index": 10,
        },
        "HTMLComment": {
            "name": "html_comment",
            "index": 9,
        },
        "HTMLDoubleQuotedString": {
            "name": "html_double_quoted_string",
            "index": 6,
        },
        "HTMLNumber": {
            "name": "html_number",
            "index": 5,
        },
        "HTMLSingleQuotedString": {
            "name": "html_single_quoted_string",
            "index": 7,
        },
        "HTMLValue": {
            "name": "html_value",
            "index": 19,
        },
        "JavaScriptComment": {
            "name": "java_script_comment",
            "index": 42,
        },
        "JavaScriptCommentDoc": {
            "name": "java_script_comment_doc",
            "index": 44,
        },
        "JavaScriptCommentLine": {
            "name": "java_script_comment_line",
            "index": 43,
        },
        "JavaScriptDefault": {
            "name": "java_script_default",
            "index": 41,
        },
        "JavaScriptDoubleQuotedString": {
            "name": "java_script_double_quoted_string",
            "index": 48,
        },
        "JavaScriptKeyword": {
            "name": "java_script_keyword",
            "index": 47,
        },
        "JavaScriptNumber": {
            "name": "java_script_number",
            "index": 45,
        },
        "JavaScriptRegex": {
            "name": "java_script_regex",
            "index": 52,
        },
        "JavaScriptSingleQuotedString": {
            "name": "java_script_single_quoted_string",
            "index": 49,
        },
        "JavaScriptStart": {
            "name": "java_script_start",
            "index": 40,
        },
        "JavaScriptSymbol": {
            "name": "java_script_symbol",
            "index": 50,
        },
        "JavaScriptUnclosedString": {
            "name": "java_script_unclosed_string",
            "index": 51,
        },
        "JavaScriptWord": {
            "name": "java_script_word",
            "index": 46,
        },
        "OtherInTag": {
            "name": "other_in_tag",
            "index": 8,
        },
        "PHPComment": {
            "name": "php_comment",
            "index": 124,
        },
        "PHPCommentLine": {
            "name": "php_comment_line",
            "index": 125,
        },
        "PHPDefault": {
            "name": "php_default",
            "index": 118,
        },
        "PHPDoubleQuotedString": {
            "name": "php_double_quoted_string",
            "index": 119,
        },
        "PHPDoubleQuotedVariable": {
            "name": "php_double_quoted_variable",
            "index": 126,
        },
        "PHPKeyword": {
            "name": "php_keyword",
            "index": 121,
        },
        "PHPNumber": {
            "name": "php_number",
            "index": 122,
        },
        "PHPOperator": {
            "name": "php_operator",
            "index": 127,
        },
        "PHPSingleQuotedString": {
            "name": "php_single_quoted_string",
            "index": 120,
        },
        "PHPStart": {
            "name": "php_start",
            "index": 18,
        },
        "PHPVariable": {
            "name": "php_variable",
            "index": 123,
        },
        "PythonClassName": {
            "name": "python_class_name",
            "index": 99,
        },
        "PythonComment": {
            "name": "python_comment",
            "index": 92,
        },
        "PythonDefault": {
            "name": "python_default",
            "index": 91,
        },
        "PythonDoubleQuotedString": {
            "name": "python_double_quoted_string",
            "index": 94,
        },
        "PythonFunctionMethodName": {
            "name": "python_function_method_name",
            "index": 100,
        },
        "PythonIdentifier": {
            "name": "python_identifier",
            "index": 102,
        },
        "PythonKeyword": {
            "name": "python_keyword",
            "index": 96,
        },
        "PythonNumber": {
            "name": "python_number",
            "index": 93,
        },
        "PythonOperator": {
            "name": "python_operator",
            "index": 101,
        },
        "PythonSingleQuotedString": {
            "name": "python_single_quoted_string",
            "index": 95,
        },
        "PythonStart": {
            "name": "python_start",
            "index": 90,
        },
        "PythonTripleDoubleQuotedString": {
            "name": "python_triple_double_quoted_string",
            "index": 98,
        },
        "PythonTripleSingleQuotedString": {
            "name": "python_triple_single_quoted_string",
            "index": 97,
        },
        "SGMLBlockDefault": {
            "name": "sgml_block_default",
            "index": 31,
        },
        "SGMLCommand": {
            "name": "sgml_command",
            "index": 22,
        },
        "SGMLComment": {
            "name": "sgml_comment",
            "index": 29,
        },
        "SGMLDefault": {
            "name": "sgml_default",
            "index": 21,
        },
        "SGMLDoubleQuotedString": {
            "name": "sgml_double_quoted_string",
            "index": 24,
        },
        "SGMLEntity": {
            "name": "sgml_entity",
            "index": 28,
        },
        "SGMLError": {
            "name": "sgml_error",
            "index": 26,
        },
        "SGMLParameter": {
            "name": "sgml_parameter",
            "index": 23,
        },
        "SGMLParameterComment": {
            "name": "sgml_parameter_comment",
            "index": 30,
        },
        "SGMLSingleQuotedString": {
            "name": "sgml_single_quoted_string",
            "index": 25,
        },
        "SGMLSpecial": {
            "name": "sgml_special",
            "index": 27,
        },
        "Script": {
            "name": "script",
            "index": 14,
        },
        "Tag": {
            "name": "tag",
            "index": 1,
        },
        "UnknownAttribute": {
            "name": "unknown_attribute",
            "index": 4,
        },
        "UnknownTag": {
            "name": "unknown_tag",
            "index": 2,
        },
        "VBScriptComment": {
            "name": "vb_script_comment",
            "index": 72,
        },
        "VBScriptDefault": {
            "name": "vb_script_default",
            "index": 71,
        },
        "VBScriptIdentifier": {
            "name": "vb_script_identifier",
            "index": 76,
        },
        "VBScriptKeyword": {
            "name": "vb_script_keyword",
            "index": 74,
        },
        "VBScriptNumber": {
            "name": "vb_script_number",
            "index": 73,
        },
        "VBScriptStart": {
            "name": "vb_script_start",
            "index": 70,
        },
        "VBScriptString": {
            "name": "vb_script_string",
            "index": 75,
        },
        "VBScriptUnclosedString": {
            "name": "vb_script_unclosed_string",
            "index": 77,
        },
        "XMLEnd": {
            "name": "xml_end",
            "index": 13,
        },
        "XMLStart": {
            "name": "xml_start",
            "index": 12,
        },
        "XMLTagEnd": {
            "name": "xml_tag_end",
            "index": 11,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)


class YAML(qt.QsciLexerYAML):
    styles = {
        "Comment": {
            "name": "comment",
            "index": 1,
        },
        "Default": {
            "name": "default",
            "index": 0,
        },
        "DocumentDelimiter": {
            "name": "document_delimiter",
            "index": 6,
        },
        "Identifier": {
            "name": "identifier",
            "index": 2,
        },
        "Keyword": {
            "name": "keyword",
            "index": 3,
        },
        "Number": {
            "name": "number",
            "index": 4,
        },
        "Operator": {
            "name": "operator",
            "index": 9,
        },
        "Reference": {
            "name": "reference",
            "index": 5,
        },
        "SyntaxErrorMarker": {
            "name": "syntax_error_marker",
            "index": 8,
        },
        "TextBlockMarker": {
            "name": "text_block_marker",
            "index": 7,
        },
    }

    def __init__(self, parent=None):
        super().__init__()
        # Add reference to 'set_theme' method
        self.__class__.set_theme = set_theme
        # Set the theme
        self.set_theme(data.theme)
