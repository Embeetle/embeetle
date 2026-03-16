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

import data
import functions
import iconfunctions


def __get_scrollbutton_style_old(
    scale_factor=1.0, align_text=None, padding="2px"
):
    scale = scale_factor
    border_color = data.theme["button_border"]
    border_color_passive = data.theme["button_border"]
    color_default = data.theme["shade"][2]
    color_hover = data.theme["shade"][5]
    color_pressed = data.theme["shade"][11]
    color_checked = data.theme["shade"][12]
    color_checked_hover = data.theme["shade"][4]
    color_checked_pressed = data.theme["shade"][9]
    border_width = 0
    border_radius = 0
    right_arrow_image_enabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_right.png"
    )
    right_arrow_image_disabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_right.png"
    )
    left_arrow_image_enabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_left.png"
    )
    left_arrow_image_disabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_left.png"
    )
    if align_text:
        align_text_str = "text-align: {};".format(align_text)
    else:
        align_text_str = ""
    style_sheet = f"""
QTabBar {{
    color: {data.theme["fonts"]["default"]["color"]};
}}

QTabBar::tab {{
    background-color: {data.theme["tab_headers"]["standard"]["other_index"]["background"]};
    border-left: 1px solid {border_color_passive};
    border-top: 1px solid {border_color_passive};
    border-bottom: none;
    padding-left: 8px;
    padding-right: 4px;
    padding-top: 4px;
    padding-bottom: 4px;
    spacing: 0px;
    font: normal;
}}
QTabBar::tab:last {{
    border-right: 1px solid {border_color_passive};
}}
QTabBar::tab::selected {{
    border-right: 1px solid {border_color_passive};
    background-color: {data.theme["tab_headers"]["standard"]["current_index"]["background"]};
    font: bold;
}}
QTabBar[indicated=true]::tab::selected {{
    background-color: {data.theme["tab_headers"]["standard_indicated"]["current_index"]["background"]};
    color: {data.theme["tab_headers"]["standard_indicated"]["current_index"]["color"]};
    font: bold;
}}

QTabBar::tear {{
    width: 0px;
}}

QTabBar QToolButton {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: (border_radius)px;
    padding: {padding};
    background: {color_default};
    margin: 0px 0px 0px 0px;
    {align_text_str}
}}
QTabBar QToolButton:hover {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: {border_radius}px;
    padding: {padding};
    background: {color_hover};
    margin: 0px 0px 0px 0px;
}}
QTabBar QToolButton:pressed {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: {border_radius}px;
    padding: {padding};
    background: {color_pressed};
    margin: 0px 0px 0px 0px;
}}
QTabBar QToolButton:checked {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: {border_radius}px;
    padding: {padding};
    background: {color_checked};
    margin: 0px 0px 0px 0px;
}}
QTabBar QToolButton:checked:hover {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: {border_radius}px;
    padding: {padding};
    background: {color_checked_hover};
    margin: 0px 0px 0px 0px;
}}
QTabBar QToolButton:checked:pressed {{
    border-color: {border_color};
    border-width: {border_width}px;
    border-style: solid;
    border-radius: {border_radius}px;
    padding: {padding};
    background: {color_checked_pressed};
    margin: 0px 0px 0px 0px;
}}
QTabBar QToolButton::right-arrow:enabled {{
    image: url({right_arrow_image_enabled});
}}
QTabBar QToolButton::right-arrow:disabled {{
    image: url({right_arrow_image_disabled});
}}
QTabBar QToolButton::left-arrow:enabled {{
    image: url({left_arrow_image_enabled});
}}
QTabBar QToolButton::left-arrow:disabled {{
    image: url({left_arrow_image_disabled});
}}

QTabBar::scroller {{width: 0px;}}
    """
    return style_sheet


def get_scrollbutton_style(scale_factor=1.0, align_text=None, padding="2px"):
    scale = scale_factor
    border_color = data.theme["button_border"]
    border_color_passive = data.theme["button_border"]
    color_default = data.theme["shade"][2]
    color_hover = data.theme["shade"][5]
    color_pressed = data.theme["shade"][11]
    color_checked = data.theme["shade"][12]
    color_checked_hover = data.theme["shade"][4]
    color_checked_pressed = data.theme["shade"][9]
    border_width = 0
    border_radius = 0
    right_arrow_image_enabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_right.png"
    )
    right_arrow_image_disabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_right.png"
    )
    left_arrow_image_enabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_left.png"
    )
    left_arrow_image_disabled = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_left.png"
    )
    if align_text:
        align_text_str = "text-align: {};".format(align_text)
    else:
        align_text_str = ""
    style_sheet = f"""
        QTabBar {{
            color: {data.theme["fonts"]["default"]["color"]};
        }}
        
        QTabBar::tab {{
            background-color: {data.theme["tab_headers"]["standard"]["other_index"]["background"]};
            border: none;
            border-right: 1px solid {data.theme["editor_background"]};
            padding-left: 8px;
            padding-right: 4px;
            padding-top: 4px;
            padding-bottom: 4px;
            spacing: 0px;
            font: normal;
        }}
        QTabBar::tab:last {{
            border: none;
        }}
        QTabBar::tab::selected {{
            background-color: {data.theme["tab_headers"]["standard"]["current_index"]["background"]};
            font: bold;
        }}
        QTabBar[indicated=true]::tab::selected {{
            background-color: {data.theme["tab_headers"]["standard_indicated"]["current_index"]["background"]};
            color: {data.theme["tab_headers"]["standard_indicated"]["current_index"]["color"]};
            font: bold;
        }}
        
        QTabBar::tear {{
            width: 0px;
        }}
        
        QTabBar QToolButton {{
            border: none;
            padding: {padding};
            background: {color_default};
            margin: 0px 0px 0px 0px;
            {align_text_str}
        }}
        QTabBar QToolButton:hover {{
            border: none;
            padding: {padding};
            background: {color_hover};
            margin: 0px 0px 0px 0px;
        }}
        QTabBar QToolButton:pressed {{
            border: none;
            padding: {padding};
            background: {color_pressed};
            margin: 0px 0px 0px 0px;
        }}
        QTabBar QToolButton:checked {{
            border: none;
            padding: {padding};
            background: {color_checked};
            margin: 0px 0px 0px 0px;
        }}
        QTabBar QToolButton:checked:hover {{
            border: none;
            padding: {padding};
            background: {color_checked_hover};
            margin: 0px 0px 0px 0px;
        }}
        QTabBar QToolButton:checked:pressed {{
            border: none;
            padding: {padding};
            background: {color_checked_pressed};
            margin: 0px 0px 0px 0px;
        }}
        QTabBar QToolButton::right-arrow:enabled {{
            image: url({right_arrow_image_enabled});
        }}
        QTabBar QToolButton::right-arrow:disabled {{
            image: url({right_arrow_image_disabled});
        }}
        QTabBar QToolButton::left-arrow:enabled {{
            image: url({left_arrow_image_enabled});
        }}
        QTabBar QToolButton::left-arrow:disabled {{
            image: url({left_arrow_image_disabled});
        }}
        
        QTabBar::scroller {{width: 0px;}}
    """
    return style_sheet
