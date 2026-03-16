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
import qt
import data
import time
import functions
import lexers


def set_font(lexer, style_name, color, bold):
    font = data.editor_font_name
    size = data.get_general_font_pointsize()
    lexer.setColor(qt.QColor(color), lexer.styles[style_name]["index"])
    weight = qt.QFont.Weight.Normal
    if bold == 1 or bold == True:
        weight = qt.QFont.Weight.Bold
    elif bold == 2:
        weight = qt.QFont.Weight.Black
    lexer.setFont(
        qt.QFont(font, size, weight=weight), lexer.styles[style_name]["index"]
    )


def set_theme(lexer, theme):
    font = theme["fonts"]["default"]
    lexer.setDefaultColor(qt.QColor(font["color"]))
    lexer.setDefaultFont(
        qt.QFont(data.editor_font_name, data.get_general_font_pointsize())
    )
    lexer.setDefaultPaper(qt.QColor(font["background"]))
    missing_themes = []
    for k, v in lexer.styles.items():
        try:
            font: Dict[str, str | bool] = theme["fonts"][v["name"]]
            paper = qt.QColor(font["background"])
            lexer.setPaper(paper, lexer.styles[k]["index"])
            set_font(lexer, k, font["color"], font["bold"])
        except:
            if not (k in missing_themes):
                missing_themes.append(k)
    if len(missing_themes) != 0:
        print("Lexer '{}' missing themes:".format(lexer.__class__.__name__))
        for mt in missing_themes:
            print("    - " + mt)
        raise Exception(
            "Lexer '{}' has missing themes!".format(lexer.__class__.__name__)
        )


def get_lexer_from_file_type(file_type):
    current_file_type = file_type
    lexer = None
    if file_type == "python":
        lexer = lexers.Python()
    elif file_type == "cython":
        lexer = lexers.Cython()
    elif file_type == "c" or file_type == "h":
        lexer = lexers.CustomC()
    elif file_type == "c++" or file_type == "h++":
        lexer = lexers.CustomC()
    elif file_type == "assembly":
        lexer = lexers.Assembly()
    elif file_type == "pascal":
        lexer = lexers.Pascal()
    elif file_type == "oberon/modula":
        lexer = lexers.Oberon()
    elif file_type == "ada":
        lexer = lexers.Ada()
    elif file_type == "d":
        lexer = lexers.D()
    elif file_type == "nim":
        lexer = lexers.Nim()
    elif file_type == "makefile":
        lexer = lexers.Makefile()
        # lexer = lexers.CustomMakefile()
    elif file_type == "xml":
        lexer = lexers.XML()
    elif file_type == "batch":
        lexer = lexers.Batch()
    elif file_type == "bash":
        lexer = lexers.Bash()
    elif file_type == "lua":
        lexer = lexers.Lua()
    elif file_type == "coffeescript":
        lexer = lexers.CoffeeScript()
    elif file_type == "c#":
        lexer = lexers.CPP()
    elif file_type == "java":
        lexer = lexers.Java()
    elif file_type == "javascript":
        lexer = lexers.JavaScript()
    elif file_type == "octave":
        lexer = lexers.Octave()
    elif file_type == "routeros":
        lexer = lexers.RouterOS()
    elif file_type == "sql":
        lexer = lexers.SQL()
    elif file_type == "postscript":
        lexer = lexers.PostScript()
    elif file_type == "fortran":
        lexer = lexers.Fortran()
    elif file_type == "fortran77":
        lexer = lexers.Fortran77()
    elif file_type == "idl":
        lexer = lexers.IDL()
    elif file_type == "ruby":
        lexer = lexers.Ruby()
    elif file_type == "html":
        lexer = lexers.HTML()
    elif file_type == "css":
        lexer = lexers.CSS()
    elif file_type == "linkerscript":
        lexer = lexers.LinkerScript()
    elif file_type == "json":
        lexer = lexers.JSON()
    elif file_type == "beetle":
        lexer = lexers.JSON()
    else:
        # No lexer was chosen, set file type to text and lexer to plain text
        current_file_type = "TEXT"
        lexer = lexers.Text()
    return current_file_type, lexer


def get_comment_style_for_lexer(lexer) -> Tuple[bool, str, str]:
    open_close_comment_style = False
    comment_string = None
    end_comment_string = None
    if isinstance(lexer, lexers.Python):
        comment_string = "#"
    elif isinstance(lexer, lexers.Cython):
        comment_string = "#"
    elif isinstance(lexer, lexers.CPP):
        comment_string = "//"
    elif isinstance(lexer, lexers.CustomC):
        comment_string = "//"
    elif isinstance(lexer, lexers.LinkerScript):
        open_close_comment_style = True
        comment_string = "/*"
        end_comment_string = "*/"
    elif isinstance(lexer, lexers.Pascal):
        comment_string = "//"
    elif isinstance(lexer, lexers.Oberon):
        open_close_comment_style = True
        comment_string = "(*"
        end_comment_string = "*)"
    elif isinstance(lexer, lexers.Ada):
        comment_string = "--"
    elif isinstance(lexer, lexers.D):
        comment_string = "//"
    elif isinstance(lexer, lexers.Nim):
        comment_string = "#"
    elif isinstance(lexer, lexers.Makefile):
        comment_string = "#"
    elif isinstance(lexer, lexers.XML):
        comment_string = None
    elif isinstance(lexer, lexers.Batch):
        comment_string = "::"
    elif isinstance(lexer, lexers.Bash):
        comment_string = "#"
    elif isinstance(lexer, lexers.Lua):
        comment_string = "--"
    elif isinstance(lexer, lexers.CoffeeScript):
        comment_string = "#"
    elif isinstance(lexer, lexers.Java):
        comment_string = "//"
    elif isinstance(lexer, lexers.JavaScript):
        comment_string = "//"
    elif isinstance(lexer, lexers.Octave):
        comment_string = "#"
    elif isinstance(lexer, lexers.RouterOS):
        comment_string = "#"
    elif isinstance(lexer, lexers.SQL):
        comment_string = "#"
    elif isinstance(lexer, lexers.PostScript):
        comment_string = "%"
    elif isinstance(lexer, lexers.Fortran):
        comment_string = "c "
    elif isinstance(lexer, lexers.Fortran77):
        comment_string = "c "
    elif isinstance(lexer, lexers.IDL):
        comment_string = "//"
    elif isinstance(lexer, lexers.Ruby):
        comment_string = "#"
    elif isinstance(lexer, lexers.HTML):
        open_close_comment_style = True
        comment_string = "<!--"
        end_comment_string = "-->"
    elif isinstance(lexer, lexers.CSS):
        open_close_comment_style = True
        comment_string = "/*"
        end_comment_string = "*/"
    elif isinstance(lexer, lexers.Assembly):
        comment_string = ";"
    # Save the comment options to the lexer
    return open_close_comment_style, comment_string, end_comment_string


def treesiter_traverse_tree_old(tree):
    cursor = tree.walk()
    cursor.goto_first_child()

    reached_root = False
    while reached_root == False:
        yield cursor.node

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            while cursor.goto_first_child():
                pass
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                while cursor.goto_first_child():
                    pass
                retracing = False


def treesiter_traverse_tree(tree):
    cursor = tree.walk()
    nodes = []

    reached_root = False
    while reached_root == False:
        if len(nodes) > 0:
            if nodes[-1].start_byte == cursor.node.start_byte:
                nodes[-1] = cursor.node
            else:
                nodes.append(cursor.node)
        else:
            nodes.append(cursor.node)

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            #            while cursor.goto_first_child():
            #                pass
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                #                while cursor.goto_first_child():
                #                    pass
                retracing = False

    return nodes
