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

from __future__ import annotations
from typing import *
import data, os, traceback
import purefunctions, functions, iconfunctions
import bpathlib.path_power as _pp_
import gui.stylesheets.tooltip
from various.kristofstuff import *


def get_btn_stylesheet() -> str:
    """# QPushButton:focus:!hover {{ #     background-color: #ecf2f9; # }} #
    QPushButton:checked, # QPushButton:checked:hover, #
    QPushButton:checked:focus {{ #     background-color: #4e9a06; # }}"""
    return f"""
        QPushButton {{
            margin: 0px;
            padding: 0px;      
            background-color: transparent;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {data.theme['indication']['hover']};
        }}
        QPushButton[_hover = true] {{
            background-color: {data.theme['indication']['hover']};
        }}
    """


def get_action_btn_stylesheet() -> str:
    """
    WARNING:
    The button this stylesheet is applied on sits in a QFrame() that changes its background color
    according to the theme.
    """
    return f"""
        QPushButton {{
            margin: 0px;
            padding: 0px;      
            background-color: {data.theme['button_unchecked']};
            border: 1px solid {data.theme['button_border']};
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            color: {data.theme['fonts']['default']['color']};
        }}
        QPushButton:hover {{
            background-color: {data.theme['button_unchecked_hover']};
        }}
    """


def get_action_btn_blink_stylesheet() -> str:
    """"""
    return f"""
        QPushButton {{
            margin: 0px;
            padding: 0px;      
            background-color: {data.theme['button_unchecked']};
            border: 1px solid {data.theme['button_border']};
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            color: #2e3436;
        }}
        QPushButton[blink_01 = true] {{
            background-color: #fefefe;
        }}
        QPushButton[blink_02 = true] {{
            background-color: #8ae234;
        }}
    """


def get_text_btn_stylesheet(font_pointsize: Optional[int] = None) -> str:
    """"""
    if not font_pointsize:
        font_pointsize = data.get_general_font_pointsize()
    return f"""
        QPushButton {{
            margin: 0px;
            padding: 0px;      
            background-color: transparent;
            border: none;
            font-family: {data.get_global_font_family()};
            font-size: {font_pointsize}pt;
            color: {data.theme['fonts']['default']['color']};
        }}
        QPushButton:hover {{
            background-color: {data.theme['button_unchecked_hover']};
        }}
        QPushButton:pressed {{
            background-color: {data.theme['button_checked_hover']};
        }}
        QPushButton:checked,
        QPushButton:checked:hover,
        QPushButton:checked:focus {{
            background-color: {data.theme['button_checked']};
        }}
    """


def get_blink_btn_stylesheet(*args) -> str:
    """Stylesheet for blinking buttons, eg.

    blinking buttons in the Filetree.
    """
    stylestr = get_btn_stylesheet()
    stylestr += f"""
        QPushButton[blink_01 = true] {{
            background-color: #fefefe;
        }}
        QPushButton[blink_02 = true] {{
            background-color: #8ae234;
        }}
    """
    return stylestr


def get_simple_toggle_stylesheet(
    style: Optional[str] = None,
    bold: bool = False,
    no_border: bool = False,
    in_padding: int = 0,
    font_size_factor: Optional[float] = None,
) -> str:
    """"""
    border_color = data.theme["button_border"]
    border_width = 1
    border_radius = 0
    padding = in_padding
    padding_right = 0
    spacing = 0
    margin = 0
    if style == "tree-widget":
        padding_right = 1 * (data.general_font_scale / 100)
    font_family = data.get_global_font_family()
    if font_size_factor is None:
        font_size_factor = 1.00
    font_pointsize = data.get_general_font_pointsize() * font_size_factor

    color_unchecked = data.theme["button_unchecked"]
    color_unchecked_font = data.theme["button_unchecked_font"]
    color_unchecked_hover = data.theme["button_unchecked_hover"]
    color_checked = data.theme["button_checked"]
    color_checked_font = data.theme["button_checked_font"]
    color_checked_hover = data.theme["button_checked_hover"]
    color_disabled_background = (
        "transparent"  # data.theme["fonts"]["disabled"]["background"]
    )
    color_disabled_font = data.theme["fonts"]["disabled"]["color"]

    if style == "good":
        color_unchecked = data.theme["button_good_unchecked"]
        color_unchecked_font = data.theme["button_good_unchecked_font"]
        color_unchecked_hover = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked_font = data.theme["button_good_checked_font"]
        color_checked_hover = iconfunctions.color_change_brightness(
            color_checked, 30
        )

    elif style == "light":
        color_unchecked = data.theme["shade"][0]

    elif style == "warning":
        color_unchecked = data.theme["button_warning_unchecked"]
        color_unchecked_font = data.theme["button_warning_unchecked_font"]
        color_unchecked_hover = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked_font = data.theme["button_warning_checked_font"]
        color_checked_hover = iconfunctions.color_change_brightness(
            color_checked, 30
        )

    elif style == "error":
        color_unchecked = data.theme["button_error_unchecked"]
        color_unchecked_font = data.theme["button_error_unchecked_font"]
        color_unchecked_hover = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked = iconfunctions.color_change_brightness(
            color_unchecked, 30
        )
        color_checked_font = data.theme["button_error_checked_font"]
        color_checked_hover = iconfunctions.color_change_brightness(
            color_checked, 30
        )

    elif style == "save-banner":
        text_color = data.theme["fonts"]["default"]["color"]
        return f"""
QPushButton {{
    text-align: center;
    background-color: #50ef2929;
    color: {text_color};
    border: 1px solid #ef2929;
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
}}
QPushButton:hover {{
    background-color: #90ef2929;
    border-color: #55d3d7cf;
}}
        """

    elif style == "transparent":
        color_unchecked = "transparent"

    elif style == "debugger":
        padding = 2
        padding_right = 2

    if no_border:
        border_string = "border: none;"
    else:
        border_string = (
            f"border-color: {border_color};"
            + f"border-width: {border_width}px;"
            + f"border-style: solid;"
            + f"border-radius: {border_radius}px;"
        )
    string_bold_font = ""
    if bold:
        string_bold_font = "font-weight: bold;"

    style_sheet = f"""
QPushButton {{
    background: {color_unchecked};
    {border_string}
    padding: {padding}px;
    spacing: {spacing}px;
    margin: {margin}px;
    font-family: {font_family};
    font-size: {font_pointsize}pt;
    {string_bold_font}
    color: {color_unchecked_font};
    text-align: center;
    alignment: center;
}}
QPushButton:hover {{
    background: {color_unchecked_hover};
    color: {color_unchecked_font};
}}
QPushButton:checked {{
    background: {color_checked};
    color: {color_checked_font};
}}
QPushButton:checked:hover {{
    background: {color_checked_hover};
    color: {color_checked_font};
}}
QPushButton:disabled {{
    background: {color_disabled_background};
    color: {color_disabled_font};
}}
{gui.stylesheets.tooltip.get_default()}
    """
    return style_sheet


def get_icon_only_stylesheet() -> str:
    """"""
    border_radius = 2
    border_width = 0
    padding = 0
    spacing = 0
    font_family = data.get_global_font_family()
    font_pointsize = data.get_general_font_pointsize()
    color_unchecked = data.theme["button_unchecked"]
    color_unchecked_font = data.theme["button_unchecked_font"]
    color_unchecked_hover = data.theme["button_unchecked_hover"]
    color_checked = data.theme["button_checked"]
    color_checked_font = data.theme["button_checked_font"]
    color_checked_hover = data.theme["button_checked_hover"]
    color_disabled_background = (
        "transparent"  # data.theme["fonts"]["disabled"]["background"]
    )
    color_disabled_font = data.theme["fonts"]["disabled"]["color"]
    return f"""
QPushButton {{
    border-radius: {border_radius}px;
    border-width: {border_width}px;
    padding: {padding};
    spacing: {spacing};
    background: transparent;
    margin: 0px;
    font-family: {font_family};
    font-size: {font_pointsize}pt;
    color: {color_unchecked_font};
}}
QPushButton:hover {{
    background: {color_unchecked_hover};
    color: {color_unchecked_font};
}}
QPushButton:checked {{
    background: {color_checked};
    color: {color_checked_font};
}}
QPushButton:checked:hover {{
    background: {color_checked_hover};
    color: {color_checked_font};
}}
QPushButton:disabled {{
    background: {color_disabled_background};
    color: {color_disabled_font};
}}
    """


def get_dropdown_stylesheet() -> str:
    """"""
    border_color = data.theme["button_border"]
    border_width = 1
    padding = 0
    spacing = 0
    color_unchecked = data.theme["button_unchecked"]
    color_unchecked_font = data.theme["button_unchecked_font"]
    color_unchecked_hover = data.theme["button_unchecked_hover"]
    color_checked = data.theme["button_checked"]
    color_checked_font = data.theme["button_checked_font"]
    color_checked_hover = data.theme["button_checked_hover"]
    return f"""
        QPushButton {{
            border-color: {border_color};
            border-width: {border_width}px;
            border-style: solid;
            padding: {padding};
            spacing: {spacing};
            background: {color_unchecked};
            margin: 0px 0px 0px 0px;
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()};
            color: {color_unchecked_font};
            text-align: left;
        }}
        QPushButton:hover {{
            background: {color_unchecked_hover};
            color: {color_unchecked_font};
        }}
        QPushButton:checked {{
            background: {color_checked};
            color: {color_checked_font};
        }}
        QPushButton:checked:hover {{
            background: {color_checked_hover};
            color: {color_checked_font};
        }}
    """


def get_tab_scroll_stylesheet(
    name: str,
    icon_path_off: str,
    icon_path_on: str,
    border: bool = False,
    transparent_background: bool = False,
) -> str:
    """

    :param icon_path_off:
    :param icon_path_on:
    :param border:
    :param transparent_background:
    :return:
    """
    if border:
        border_color = data.theme["button_border"]
        border_width = 1
        border_string = f"""
            border-color: {border_color};
            border-width: {border_width}px;
            border-style: solid;
        """
    else:
        border_string = f"""
            border: none;
        """
    padding = 0
    spacing = 0
    font_family = data.get_global_font_family()
    font_pointsize = data.get_general_font_pointsize()
    if transparent_background:
        color_unchecked = "transparent"
    else:
        color_unchecked = data.theme["button_unchecked"]
    color_unchecked_font = data.theme["button_unchecked_font"]
    color_unchecked_hover = data.theme["button_unchecked_hover"]
    color_checked = data.theme["button_checked"]
    color_checked_font = data.theme["button_checked_font"]
    color_checked_hover = data.theme["button_checked_hover"]
    color_disabled_background = (
        "transparent"  # data.theme["fonts"]["disabled"]["background"]
    )
    color_disabled_font = data.theme["fonts"]["disabled"]["color"]
    image_off = iconfunctions.get_icon_abspath(icon_path_off)
    image_on = iconfunctions.get_icon_abspath(icon_path_on)
    return f"""
        {name} {{
            {border_string}
            padding: {padding};
            spacing: {spacing};
            background: {color_unchecked};
            margin: 0px;
            font-family: {font_family};
            font-size: {font_pointsize}pt;
            color: {color_unchecked_font};
            icon: url({image_off});
        }}
        {name}:hover {{
            background: {color_unchecked_hover};
            color: {color_unchecked_font};
            icon: url({image_on});
        }}
        {name}:pressed {{
            background: {data.theme["dark_background"]};
        }}
        {name}:checked {{
            color: {color_checked_font};
        }}
        {name}:checked:hover {{
            color: {color_checked_font};
        }}
        {name}:disabled {{
            color: {color_disabled_font};
        }}
    """


def get_tab_btn_stylesheet(
    icon: Optional[str] = None,
    icon_hover: Optional[str] = None,
    icon_pressed: Optional[str] = None,
    icon_focused: Optional[str] = None,
    icon_active: Optional[str] = None,
    icon_active_hover: Optional[str] = None,
    icon_active_pressed: Optional[str] = None,
    icon_active_focused: Optional[str] = None,
    icon_disabled: Optional[str] = None,
    border=False,
) -> str:
    """Default stylesheet for tab buttons in Embeetle.

    Notes:
        - Icon parameters are optional.

        - If provided, the icon parameters must be paths to icons,
          either relative to the 'resources' directory or absolute.
    """
    icon = __get_icon(icon)
    icon_hover = __get_icon(icon_hover)
    icon_pressed = __get_icon(icon_pressed)
    icon_focused = __get_icon(icon_focused)

    icon_active = __get_icon(icon_active)
    icon_active_hover = __get_icon(icon_active_hover)
    icon_active_pressed = __get_icon(icon_active_pressed)
    icon_active_focused = __get_icon(icon_active_focused)

    icon_disabled = __get_icon(icon_disabled)

    background = "transparent"
    background_checked = data.theme["shade"][4]

    border_string = "none"
    if border:
        border_string = "1px solid {}".format(data.theme["button_border"])

    # * DEFAULT BUTTON STYLESHEET
    stylestr = f"""
        QPushButton {{ 
            margin: 0px 0px 0px 0px;
            padding: 0px 0px 0px 0px;      
            background-color: {background};
            border: {border_string};
            {icon}
        }}
        QPushButton:hover {{
            background-color: {background};
            {icon_hover}
        }}
        QPushButton:pressed {{
            background-color: {background};
            {icon_pressed}
        }}
        QPushButton:focus:!hover {{
            background-color: {background};
            {icon_focused}
        }}
        QPushButton:checked,
        QPushButton:checked:hover,
        QPushButton:checked:focus {{
            background-color: {background_checked};
            {icon}
        }}
    """

    stylestr += f"""
        QPushButton[active = true] {{
            background-color: {background};
            {icon_active}
        }}
        QPushButton[active = true]:hover {{
            background-color: {background};
            {icon_active_hover}
        }}
        QPushButton[active = true]:focus {{
            background-color: {background};
            {icon_active_focused}
        }}
        QPushButton[active = true]:pressed {{
            background-color: {background};
            {icon_active_pressed}
        }}
        QPushButton[active = true]:checked,
        QPushButton[active = true]:checked:hover,
        QPushButton[active = true]:checked:focus {{
            background-color: {background_checked};
            {icon_active}
        }}
    """

    if (icon_disabled is not None) and (icon_disabled != ""):
        stylestr += f"""
            QPushButton:disabled {{
                background-color: {background};
                {icon_disabled}
            }}
        """

    return stylestr


def get_toolbutton():
    style_sheet = f"""
QToolButton {{
    background-color: transparent;
    border: none;
    margin: 2px;
}}
QToolButton:hover {{
    background-color: {data.theme["indication"]["hover"]};
}}
QToolButton:disabled {{
    background-color: transparent;
}}
    """
    return style_sheet


def get_picturebutton(
    name: str,
    icon_path_off: str,
    icon_path_on: str,
    icon_path_hover: str,
    icon_path_checked: str,
    icon_path_focused: str,
    icon_path_disabled: str,
    size: tuple,
    border: bool = True,
    transparent_background: bool = False,
) -> str:
    # Border
    if border:
        border_color = data.theme["button_border"]
        border_width = 1
        border_string = f"""
            border-color: {border_color};
            border-width: {border_width}px;
            border-style: solid;
        """
    else:
        border_string = "border: none;"
    # Icons
    image_off = iconfunctions.get_icon_abspath(icon_path_off)
    image_on = iconfunctions.get_icon_abspath(icon_path_on)
    image_hover = iconfunctions.get_icon_abspath(icon_path_hover)
    image_checked = iconfunctions.get_icon_abspath(icon_path_checked)
    image_focused = iconfunctions.get_icon_abspath(icon_path_focused)
    image_disabled = iconfunctions.get_icon_abspath(icon_path_disabled)
    # Other attributes
    padding = 0
    spacing = 0
    margin = 4
    width, height = size
    return f"""
        #{name} {{
            {border_string}
            padding: {padding}px;
            spacing: {spacing}px;
            margin: {margin}px;
            background: transparent;
            image: url({image_off});
            width: {width}px;
            height: {height}px;
            min-width: {width}px;
            min-height: {height}px;
            max-width: {width}px;
            max-height: {height}px;
        }}
        #{name}:hover {{
            image: url({image_hover});
        }}
        #{name}:pressed {{
            image: url({image_on});
        }}
        #{name}:checked {{
            image: url({image_checked});
        }}
        #{name}[focused = true] {{
            image: url({image_focused});
        }}
        #{name}:disabled {{
            image: url({image_disabled});
        }}
    """


# ^                               HELP FUNCTIONS                               ^#
# % ========================================================================== %#
# %                                                                            %#
# %                                                                            %#


def __get_icon(iconpath: str) -> str:
    if iconpath is None:
        return ""
    if not isinstance(iconpath, str):
        purefunctions.printc(
            f"\nWARNING: Given path to __get_icon() is not a string: "
            f"{q}{iconpath}{q}\n",
            color="warning",
        )
        traceback.print_stack()
        return ""
    if not os.path.isfile(iconpath):
        iconpath = iconfunctions.get_icon_abspath(iconpath)
    if not os.path.isfile(iconpath):
        purefunctions.printc(
            f"\nWARNING: Cannot find icon {q}{iconpath}{q}\n",
            color="warning",
        )
        traceback.print_stack()
        return ""
    return f"image: url({iconpath});"


def get_radio_style():
    icon_width = data.get_general_icon_pixelsize()
    icon_height = data.get_general_icon_pixelsize()
    checked_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/checked_dot.svg"
    )
    checked_hover_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/checked_dot_hover.svg"
    )
    checked_pressed_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/checked_dot_pressed.svg"
    )
    unchecked_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/unchecked_dot.svg"
    )
    unchecked_hover_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/unchecked_dot_hover.svg"
    )
    unchecked_pressed_icon = iconfunctions.get_icon_abspath(
        "icons/checkbox/unchecked_dot_pressed.svg"
    )
    style_sheet = f"""
        QRadioButton {{
            background-color: {data.theme['button_unchecked']};
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            color: {data.theme['fonts']['default']['color']};
        }}
        QRadioButton::indicator {{
            width: {icon_width}px;
            height: {icon_height}px;
        }}
        QRadioButton::icon {{
            width: 8px;
            height: 8px;
        }}
        QRadioButton::indicator::unchecked {{
            image: url({unchecked_icon});
        }}
        QRadioButton::indicator::unchecked:hover {{
            image: url({unchecked_hover_icon});
        }}
        QRadioButton::indicator::unchecked:pressed {{
            image: url({checked_pressed_icon});
        }}
        QRadioButton::indicator::checked {{
            image: url({checked_icon});
        }}
        QRadioButton::indicator::checked:hover {{
            image: url({checked_hover_icon});
        }}
        QRadioButton::indicator::checked:pressed {{
            image: url({checked_pressed_icon});
        }}
    """
    return style_sheet
