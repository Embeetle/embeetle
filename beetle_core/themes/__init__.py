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

import os
import qt
import functools
import traceback
import purefunctions


def get_all():
    theme_files = []
    for item in os.listdir(__get_theme_directory()):
        if item.endswith(".json5"):
            try:
                theme = get(item)
                theme_files.append(theme)
            except:
                traceback.print_exc()
                print("[Themes] Invalid theme file:", item)
    return theme_files


def get(theme_name):
    file_name = theme_name
    if not theme_name.endswith(".json5"):
        file_name = file_name.replace(".json", "")
        file_name = f"{theme_name.lower()}.json5".replace(" ", "_")
    assert file_name.endswith(".json5")
    file_path = purefunctions.unixify_path_join(
        __get_theme_directory(), file_name
    )
    if not os.path.isfile(file_path):
        raise Exception(
            f"[Themes] Theme '{theme_name}' does not exist at '{file_path}'!"
        )
    try:
        theme = purefunctions.load_json_file_with_comments(file_path)
    except Exception as ex:
        print(f"[Themes] Cannot parse '{file_name}' theme file!")
        raise ex
    __check(theme)
    return theme


def __get_theme_directory() -> str:
    """"""
    return purefunctions.join_resources_dir_to_path("themes")


def __check_color(field, color_string, prior_keys) -> None:
    """"""
    try:
        qt.QColor(color_string)
    except Exception as ex:
        print(
            "[Themes] Color error: {} / '{}'!".format(
                "->".join(prior_keys + (field,)), color_string
            )
        )
        raise ex
    return


def __check_color_list(field, color_list, prior_keys):
    try:
        for color_string in color_list:
            qt.QColor(color_string)
    except Exception as ex:
        print(
            "[Themes] Color list error: {}!".format(
                "->".join(prior_keys + (field,))
            )
        )
        raise ex


def __check_string(field, string, prior_keys):
    if not isinstance(string, str):
        raise Exception(
            "[Themes] String error: {} / '{}'!".format(
                "->".join(prior_keys + (field,)), string
            )
        )


def __check_bool(field, boolean, prior_keys):
    if not isinstance(boolean, bool):
        raise Exception(
            "[Themes] Boolean error: {} / '{}'!".format(
                "->".join(prior_keys + (field,)), boolean
            )
        )


def __check(theme_data):
    schema = {
        "name": __check_string,
        "is_dark": __check_bool,
        "tooltip": __check_string,
        "image_file": __check_string,
        "form_background_file": __check_string,
        "home_window_logo_image": __check_string,
        "dock_point_color_active": __check_color,
        "dock_point_color_passive": __check_color,
        "form_background": __check_color,
        "cursor": __check_color,
        "cursor_line_overlay": __check_color,
        "cursor_line_frame": __check_bool,
        "general_background": __check_color,
        "dark_background": __check_color,
        "tool_tip_font": __check_color,
        "tool_tip_background": __check_color,
        "tool_tip_border": __check_color,
        "splitter_handle_background": __check_color,
        "splitter_handle_hover": __check_color,
        "splitter_handle_pressed": __check_color,
        "pieces_question_background": __check_color,
        "pieces_question_border": __check_color,
        "pieces_answer_background": __check_color,
        "pieces_answer_border": __check_color,
        "dropdown_border": __check_color,
        "button_border": __check_color,
        "menu_background": __check_color,
        "menubar_background": __check_color,
        "button_unchecked": __check_color,
        "button_unchecked_hover": __check_color,
        "button_unchecked_font": __check_color,
        "button_checked": __check_color,
        "button_checked_hover": __check_color,
        "button_checked_font": __check_color,
        "button_good_border": __check_color,
        "button_good_unchecked": __check_color,
        "button_good_unchecked_font": __check_color,
        "button_good_checked_font": __check_color,
        "button_error_border": __check_color,
        "button_error_unchecked": __check_color,
        "button_error_unchecked_font": __check_color,
        "button_error_checked_font": __check_color,
        "button_warning_border": __check_color,
        "button_warning_unchecked": __check_color,
        "button_warning_unchecked_font": __check_color,
        "button_warning_checked_font": __check_color,
        "table_header": __check_color,
        "table_grid": __check_color,
        "ribbon_item_background_pressed": __check_color,
        "ribbon_item_background_pressed_entered": __check_color,
        "editor_background": __check_color,
        "fold_margin": {
            "foreground": __check_color,
            "background": __check_color,
        },
        "line_margin": {
            "foreground": __check_color,
            "background": __check_color,
        },
        "scroll_bar": {
            "background": __check_color,
            "handle": __check_color,
            "handle_hover": __check_color,
            "show_arrows": __check_bool,
            "arrow_up": __check_string,
            "arrow_down": __check_string,
            "arrow_left": __check_string,
            "arrow_right": __check_string,
        },
        "console": {
            "background": __check_color,
            "border": __check_color,
            "fonts": {
                "default": __check_color,
                "black": __check_color,
                "red": __check_color,
                "green": __check_color,
                "yellow": __check_color,
                "blue": __check_color,
                "magenta": __check_color,
                "cyan": __check_color,
                "white": __check_color,
                "purple": __check_color,
                "info": __check_color,
                "warning": __check_color,
                "error": __check_color,
                "sa": __check_color,
                "teal": __check_color,
                "path": __check_color,
            },
        },
        "indication": {
            "highlight": __check_color,
            "selection": __check_color,
            "replace": __check_color,
            "symbol": __check_color,
            "blink": __check_color,
            "error": __check_color,
            "warning": __check_color,
            "hover": __check_color,
            "background_selection": __check_color,
        },
        "text_differ": {
            "indicator_unique_1_color": __check_color,
            "indicator_unique_2_color": __check_color,
            "indicator_similar_color": __check_color,
        },
        "tab_headers": {
            "standard": {
                "current_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
                "other_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
            },
            "standard_indicated": {
                "current_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
                "other_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
            },
            "inside_compiler": {
                "current_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
                "other_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
            },
            "excluded_from_project": {
                "current_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
                "other_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
            },
            "outside_project": {
                "current_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
                "other_index": {
                    "color": __check_color,
                    "background": __check_color,
                    "border": __check_color,
                },
            },
            "close_button": {
                "passive": {
                    "standard": __check_string,
                    "hover": __check_string,
                    "press": __check_string,
                },
                "active": {
                    "standard": __check_string,
                    "hover": __check_string,
                    "press": __check_string,
                },
            },
        },
        "shade": __check_color_list,
        "tree_widget_branch_images": {
            "node_open_first_with_siblings": __check_string,
            "node_closed_first_with_siblings": __check_string,
            "f": __check_string,
            "node_closed_only": __check_string,
            "node_closed_middle": __check_string,
            "node_closed_last": __check_string,
            "node_open_only": __check_string,
            "node_open_middle": __check_string,
            "node_open_last": __check_string,
            "t": __check_string,
            "t-add": __check_string,
            "l": __check_string,
            "l-add": __check_string,
            "line": __check_string,
            "expand_arrow": __check_string,
        },
        "fonts": {
            "default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "selection": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "red": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "green": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "blue": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "purple": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "grey": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "lightgrey": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "advanced_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "array": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "array_parenthesis": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asm": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_at_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_comment_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_comment_line": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_regex": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_symbol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_java_script_word": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_class_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_function_method_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_triple_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_python_triple_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "asp_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspvb_script_unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "aspxc_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "assignment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "at_rule": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "attribute": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "backquote_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "backtick_here_document": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "backtick_here_document_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "backticks": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "backticks_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "bad_directive": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "bad_string_character": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "base_85_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "basic_functions": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "basic_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_foreach": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_if": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_macro": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_regex": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_regex_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "block_while": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "call_convention": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "case_of": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "cdata": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "char_literal": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "character": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "class_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "class_selector": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "class_variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "clip_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "command": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_bang": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_block": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_box": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_doc_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_doc_keyword_error": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_line": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_line_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_line_hash": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_nested": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "comment_parenthesis": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "continuation": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "coroutines_io_system_facilities": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "css_1_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "css_2_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "css_3_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "custom_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "data_section": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "declare_input_output_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "declare_input_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "declare_output_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "decorator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "default_value": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "definition": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "delimiter": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "demoted_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dictionary_parenthesis": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "diff_similar": {
                "color": __check_color,
                "bold": __check_bool,
            },
            "diff_unique_1": {
                "color": __check_color,
                "bold": __check_bool,
            },
            "diff_unique_2": {
                "color": __check_color,
                "bold": __check_bool,
            },
            "directive": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "disabled": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "doccomment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "documentation_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dot": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dotted_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "double_quoted_here_document": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "double_quoted_here_document_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "double_quoted_string_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dunder": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dsc_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "dsc_comment_value": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "entity": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "error": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "escape_sequence": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "expand_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "extra": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "extended_css_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "extended_function": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "extended_pseudo_class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "extended_pseudo_element": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "external_command": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "filter": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "flags": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "format_body": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "format_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "function": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "function_method_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "fuzzy": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "global": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "global_class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "group": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "hash": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "hash_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "header": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "here_document": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "here_document_delimiter": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "hex_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "hex_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "hide_command_char": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "highlighted_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "html_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "html_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "html_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "html_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "html_value": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "id_selector": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "immediate_eval_literal": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "important": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "iri": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "iri_compact": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_bang": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_doc_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_doc_keyword_error": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_line": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_comment_line_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_declare_input_output_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_declare_input_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_declare_output_port": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_escape_sequence": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_global_class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_hash_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_keyword_set_2": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_port_connection": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_pre_processor": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_pre_processor_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_pre_processor_comment_line_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_preprocessor": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_raw_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_regex": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_system_task": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_task_marker": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_triple_quoted_verbatim_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_user_keyword_set": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_user_literal": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_uuid": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inactive_verbatim_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "inconsistent": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "instance_variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "intrinsic_function": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "itcl_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_comment_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_comment_line": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_regex": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_symbol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "java_script_word": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "key": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_1": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_2": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_3": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_secondary": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_2": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_3": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_5": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_6": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_7": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_8": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_set_9": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "keyword_ld": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "label": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "line_added": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "line_changed": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "line_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "line_removed": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "literal": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "literal_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "long_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "longstring": {
                "color": __check_color,
                "background": __check_color,
            },
            "media_rule": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_context": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_context_text": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_context_text_eol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_id": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_id_text": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_id_text_eol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_string_text": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "message_string_text_eol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "modifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "module": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "module_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "multiline_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "multiline_documentation": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "nested_block_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "no_warning": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "objects_csg_appearance": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "other_in_tag": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "package": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "parameter": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "parameter_expansion": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "percent_string_q": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "percent_stringq": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "percent_stringr": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "percent_stringw": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "percent_stringx": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_comment_line": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_double_quoted_variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "php_variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "plugin": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "plus_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "plus_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "plus_prompt": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pod": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pod_verbatim": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "port_connection": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "position": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pragma": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pre_processor": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pre_processor_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pre_processor_comment_line_doc": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pre_processor_parenthesis": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "predefined_functions": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "predefined_identifiers": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "preprocessor": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "procedure": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "procedure_parenthesis": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "programmer_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pseudo_class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "pseudo_element": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_class_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_function_method_name": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_triple_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "python_triple_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_q": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qq": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qq_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qr": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qr_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qw": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qx": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "quoted_string_qx_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "raw_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "reference": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "regex": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "regex_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "scalar": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "script": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "section": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_block_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_command": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_entity": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_error": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_parameter": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_parameter_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "sgml_special": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "single_quoted_here_document": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "spaces": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "special": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "standard_function": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "standard_operator": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "standard_package": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "standard_type": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "stderr": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "stdin": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "stdout": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "standard": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "string_left_quote": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "string_right_quote": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "string_table_maths_functions": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "string_variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "subroutine_prototype": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "substitution": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "substitution_brace": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "substitution_var": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "success": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "symbol": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "symbol_table": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "system_task": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tab": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tabs": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tabs_after_spaces": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tag": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "target": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "task_marker": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tcl_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "text": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tk_command": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "tk_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "top-keyword": {
                "color": __check_color,
                "background": __check_color,
                "bold": __check_bool,
            },
            "top_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "translation": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "triangular_bracing": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "triple_double_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "triple_quoted_verbatim_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "triple_single_quoted_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "triple_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "type": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "typedefs": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "types_modifiers_items": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "under_dunder": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unknown_attribute": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unknown_property": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unknown_pseudo_class": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unknown_tag": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "unsafe": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "user_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "user_keyword_set": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "user_literal": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "uuid": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "value": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "variable": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_comment": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_default": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_identifier": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_keyword": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_number": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "vb_script_unclosed_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "verbatim_string": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "warning": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "whitespace": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "xml_end": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "xml_start": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
            "xml_tag_end": {
                "color": __check_color,
                "bold": __check_bool,
                "background": __check_color,
            },
        },
    }

    def get_nested_item(dictionary, keys):
        return functools.reduce(lambda seq, key: seq[key], keys, dictionary)

    def check_fields(dictionary, prior_keys=()):
        for k, v in dictionary.items():
            try:
                nested_schema_item = get_nested_item(schema, prior_keys)
            except:
                raise Exception(
                    "[Themes] Unknown schema key: {} / '{}'!".format(
                        "->".join(prior_keys + (k,)), v
                    )
                )
            if isinstance(v, dict):
                check_fields(v, (*prior_keys, k))
            elif isinstance(v, int) and not isinstance(v, bool):
                if dictionary[k] != nested_schema_item[k]:
                    raise Exception(
                        "[Themes] Integer error: {} / '{}'!".format(
                            "->".join(prior_keys + (k,)), v
                        )
                    )
            else:
                try:
                    if k not in nested_schema_item:
                        raise Exception(
                            "[Themes] Key is missing: {}!".format(
                                "->".join(prior_keys + (k,)),
                            )
                        )
                    func = nested_schema_item[k]
                    func(k, v, prior_keys)
                except Exception as ex:
                    print("key:", k)
                    print("value:", v)
                    print("prior-keys:", prior_keys)
                    print("nested_schema_item:", nested_schema_item)
                    raise ex

    check_fields(theme_data)
