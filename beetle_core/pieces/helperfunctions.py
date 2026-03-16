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
import traceback
import markdown
import pygments
import pygments.lexers
import pygments.formatters
import pygments.util
import data

# Define a list of light and dark styles
light_styles = [
    "default",
    "friendly",
    "manni",
    "perldoc",
    "pastie",
    "borland",
    "trac",
    "bw",
    "algol",
    "algol_nu",
    "arduino",
    "rainbow_dash",
]
dark_styles = [
    "monokai",
    "vim",
    "autumn",
    "vs",
    "fruity",
    "bw",
    "emacs",
    "igor",
    "lovelace",
    "paraiso-dark",
    "native",
]


def __split_triple_backtick_strings(
    _text: str,
) -> list[Union[tuple[str, str], tuple[str, str, str]]]:
    """Split the input string into a list of tuples. Each tuple represents a
    part of the input string that is either inside or outside of the triple
    backtick blocks.

    For each part, it determines if it is inside a triple backtick block
    ('ticked') or outside ('unticked'). If it is inside, it also captures the
    first word (used to denote the language of the code block in Markdown) and
    removes non-whitespace characters following it.
    """
    # Define the regex pattern for triple backtick strings
    pattern = r"(```(.*?)```)"  # This captures the triple backtick content

    # Split the text using the pattern
    matches = re.split(pattern, _text, flags=re.DOTALL)

    # Initialize a list to hold parts with their type (inside or outside backticks)
    _parts = []

    # Iterate over the matches
    for i, match in enumerate(matches):
        if i % 3 == 0:
            # Parts outside triple backticks (every 3rd element starting from 0)
            if match:
                _parts.append(("unticked", match))
        elif i % 3 == 2:
            # Parts inside triple backticks (non-empty, every 3rd element starting from 1)
            if match:
                # Remove all non-whitespace characters after the starting triple backticks
                cleaned_match = re.sub(r"^\S+\s*", "", match)
                # Extract the first word if present
                if match[0] in ("\n", "\t", " "):
                    first_word = ""
                else:
                    first_word_match = re.match(r"^\s*(\S+)", match)
                    first_word = (
                        first_word_match.group(1) if first_word_match else ""
                    )
                _parts.append(("ticked", cleaned_match, first_word))

    return _parts


def get_default_formatter() -> pygments.formatters.HtmlFormatter:
    """"""
    # Choose Pygments style in regards to icon style
    if data.icon_style == "plump_color_light":
        style_name = "monokai"
    else:
        style_name = "default"

    # Create the formatter
    formatter = pygments.formatters.HtmlFormatter(
        linenos=True,
        cssclass="source",
        style=style_name,
    )
    return formatter


def get_html_page(
    input_text: str,
    div_class: str,
) -> tuple[str, list[str]]:
    """Take the `input_text` and convert that into an html-page, according to
    the given div class ("question", "answer" or "server-error").

    :return: str: The html-page list[str]: List of code snippets, to be used for
        copy-to-clipboard functionality. Can be empty list.
    """
    assert div_class in ("question", "answer", "server-error")

    # Get the CSS code for the specified style
    pygments_css = get_default_formatter().get_style_defs("")
    parsed_output = __parse_languages_in_string(input_text)
    parsed_output_str = parsed_output[0]
    code_list = parsed_output[1]

    pygments_css += f"""
td.linenos .normal {{
    color: {data.theme["fonts"]["grey"]["color"]};
    padding-left: 5px;
    padding-right: 5px;
}}
span.linenos {{
    color: {data.theme["fonts"]["default"]["color"]};
    padding-left: 5px;
    padding-right: 5px;
}}
td.linenos {{
    color: {data.theme["fonts"]["default"]["color"]};
    padding-left: 5px;
    padding-right: 5px;
    border-right: 1px solid {data.theme["fonts"]["lightgrey"]["color"]};
}}
span.linenos {{
    color: {data.theme["fonts"]["default"]["color"]};
    padding-left: 5px;
    padding-right: 5px;
}}
    """

    return (
        f"""
<html>
<head>
    <style>
        {pygments_css}
    </style>
</head>
<body style='color: {data.theme["fonts"]["default"]["color"]};'>
    <div class=\"{div_class}\">{parsed_output_str}</div>
</body>
</html>
""",
        code_list,
    )


def lexer_exists(short_name) -> bool:
    """"""
    try:
        # Try to get the lexer by its short name
        lexer = pygments.lexers.get_lexer_by_name(short_name)
        return True
    except pygments.util.ClassNotFound:
        # If the lexer is not found, return False
        return False


def __parse_languages_in_string(_text) -> tuple[str, list[str]]:
    """Parse the given text and output an html-styled string as well as a list
    of all the code snippets (for copy-to-clipboard later on)."""
    _parts = __split_triple_backtick_strings(_text)
    out_string_list: list[str] = []
    code_list: list[str] = []
    for _idx, _part in enumerate(_parts):
        if _part[0] == "ticked":
            try:
                code = _part[1]
                lexer_name = _part[2]
                if lexer_name == "" or not lexer_exists(lexer_name):
                    lexer = pygments.lexers.TextLexer()
                else:
                    lexer = pygments.lexers.get_lexer_by_name(
                        lexer_name, stripall=True
                    )
                formatter = get_default_formatter()
                html_result = pygments.highlight(code, lexer, formatter)
                out_string_list.append(html_result)
                out_string_list.append(
                    f"""<p><a href="copy_code[{len(code_list)}]">[COPY CODE]</a></p>"""
                )
                code_list.append(code)
            except:
                traceback.print_exc()
                out_string_list.append(_part[1])
        else:
            out_string_list.append(markdown.markdown(_part[1]))
        continue
    return "".join(out_string_list), code_list


def generate_item_list_for_conversation_advanced_combobox(
    cur_conv_name: Optional[str],
    cur_conv_id: Optional[str],
    all_convs_dict: dict[str, dict[str, str]],
) -> Optional[tuple[Optional[str], list[dict[str, Any]]]]:
    """"""
    items = []
    for conv_id, conv_dict in all_convs_dict.items():
        assert conv_id == conv_dict["id"]
        icon_path = "icons/dialog/message_clear.png"
        text_color = "default"
        if conv_id == cur_conv_id:
            icon_path = "icons/dialog/message.png"
            text_color = "default"
        items.append(
            {
                "name": conv_id,
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": icon_path,
                    },
                    {
                        "type": "text",
                        "text": conv_dict["name"],
                        "color": text_color,
                    },
                ],
            }
        )
        continue
    items.append(
        {
            "name": "add_conversation",
            "widgets": [
                {
                    "type": "image",
                    "icon-path": "icons/dialog/add.png",
                },
                {
                    "type": "text",
                    "text": "Create New",
                    "color": "default",
                },
            ],
        }
    )

    return cur_conv_id, items


def generate_item_list_for_models_advanced_combobox(
    cur_model_name: Optional[str],
    cur_model_id: Optional[str],
    all_models_dict: dict[str, dict[str, str]],
) -> Optional[tuple[Optional[str], list[dict[str, Any]]]]:
    """"""
    items = []
    online_models_dict = {}
    offline_downloaded_models_dict = {}
    offline_downloading_models_dict = {}
    offline_not_yet_downloaded_models_dict = {}

    for model_id, model_dict in all_models_dict.items():
        if model_dict["cloud"]:
            online_models_dict[model_id] = model_dict
            continue
        if model_dict["downloaded"]:
            offline_downloaded_models_dict[model_id] = model_dict
            continue
        if model_dict["downloading"]:
            offline_downloading_models_dict[model_id] = model_dict
            continue
        offline_not_yet_downloaded_models_dict[model_id] = model_dict
        continue

    # $ ONLINE MODELS
    items.append(
        {
            "name": "online_models",
            "widgets": [
                {
                    "type": "text",
                    "text": "ONLINE MODELS",
                    "color": "default",
                },
            ],
        }
    )
    subitems = []
    for model_id, model_dict in online_models_dict.items():
        assert model_id == model_dict["id"]
        subitems.append(
            {
                "name": f"online_models/{model_id}",
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": "icons/gen/cloud.png",
                    },
                    {
                        "type": "text",
                        "text": model_dict["name"],
                        "color": "default",
                    },
                ],
            }
        )
        continue
    if len(subitems):
        items[-1]["subitems"] = subitems

    # $ OFFLINE DOWNLOADED MODELS
    items.append(
        {
            "name": "offline_downloaded_models",
            "widgets": [
                {
                    "type": "text",
                    "text": "OFFLINE MODELS (DOWNLOADED)",
                    "color": "default",
                },
            ],
        }
    )
    subitems = []
    for model_id, model_dict in offline_downloaded_models_dict.items():
        assert model_id == model_dict["id"]
        subitems.append(
            {
                "name": f"offline_downloaded_models/{model_id}",
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": "icons/gen/computer.png",
                    },
                    {
                        "type": "text",
                        "text": model_dict["name"],
                        "color": "default",
                    },
                ],
            }
        )
        continue
    if len(subitems):
        items[-1]["subitems"] = subitems

    # $ OFFLINE DOWNLOADING MODELS
    items.append(
        {
            "name": "offline_downloading_models",
            "widgets": [
                {
                    "type": "text",
                    "text": "OFFLINE MODELS (DOWNLOADING...)",
                    "color": "default",
                },
            ],
        }
    )
    subitems = []
    for model_id, model_dict in offline_downloading_models_dict.items():
        assert model_id == model_dict["id"]
        subitems.append(
            {
                "name": f"offline_downloading_models/{model_id}",
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": "icons/gen/computer(hid).png",
                    },
                    {
                        "type": "text",
                        "text": model_dict["name"],
                        "color": "default",
                    },
                ],
            }
        )
        continue
    if len(subitems):
        items[-1]["subitems"] = subitems

    # $ OFFLINE NOT YET DOWNLOADED MODELS
    items.append(
        {
            "name": "offline_not_yet_downloaded_models",
            "widgets": [
                {
                    "type": "text",
                    "text": "OFFLINE MODELS (NOT YET DOWNLOADED)",
                    "color": "default",
                },
            ],
        }
    )
    subitems = []
    for model_id, model_dict in offline_not_yet_downloaded_models_dict.items():
        assert model_id == model_dict["id"]
        subitems.append(
            {
                "name": f"offline_not_yet_downloaded_models/{model_id}",
                "widgets": [
                    {
                        "type": "image",
                        "icon-path": "icons/gen/computer(hid).png",
                    },
                    {
                        "type": "text",
                        "text": model_dict["name"],
                        "color": "default",
                    },
                ],
            }
        )
        continue
    if len(subitems):
        items[-1]["subitems"] = subitems

    # SET CURRENT SELECTION
    if cur_model_id in online_models_dict.keys():
        return f"online_models/{cur_model_id}", items
    if cur_model_id in offline_downloaded_models_dict.keys():
        return f"offline_downloaded_models/{cur_model_id}", items
    if cur_model_id in offline_downloading_models_dict.keys():
        return f"offline_downloading_models/{cur_model_id}", items
    if cur_model_id in offline_not_yet_downloaded_models_dict.keys():
        return f"offline_not_yet_downloaded_models/{cur_model_id}", items
    return None, items
