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
import iconfunctions


def __get_images():
    func = iconfunctions.get_icon_abspath
    return {
        "down": func(data.theme["scroll_bar"]["arrow_down"]),
        "left": func(data.theme["scroll_bar"]["arrow_left"]),
        "right": func(data.theme["scroll_bar"]["arrow_right"]),
        "up": func(data.theme["scroll_bar"]["arrow_up"]),
    }


def get_arrow_size():
    return int(data.get_scrollbar_zoom_pixelsize() * 0.12)


def get_bar_width():
    return int(data.get_scrollbar_zoom_pixelsize() * 0.12)


"""
Horizontal
"""


def get_horizontal():
    if data.theme["scroll_bar"]["show_arrows"]:
        return __horizontal_with_arrows()
    else:
        return __horizontal()


def __horizontal():
    size = get_bar_width()
    background = data.theme["scroll_bar"]["background"]
    handle_color = data.theme["scroll_bar"]["handle"]
    hover_color = data.theme["scroll_bar"]["handle_hover"]
    style = f"""
        QScrollBar:horizontal {{
            border: none;
            background-color: {background};
            height: {size}px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {handle_color};
            min-width: 20px;
        }}
        QScrollBar::handle:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::handle:horizontal:pressed {{
            background-color: {hover_color};
        }}
        
        QScrollBar::sub-line:horizontal,
        QScrollBar::add-line:horizontal,
        QScrollBar::left-arrow:horizontal,
        QScrollBar::right-arrow:horizontal,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal
        {{
            border: none;
            background: none;
            width: 0px;
            height: 0px;
        }}
    """

    return style


def __horizontal_with_arrows():
    size = get_bar_width()
    images = __get_images()
    arrow_size = get_arrow_size()
    background = data.theme["scroll_bar"]["background"]
    handle_color = data.theme["scroll_bar"]["handle"]
    hover_color = data.theme["scroll_bar"]["handle_hover"]
    style = f"""
        QScrollBar:horizontal {{
            border: none;
            background-color: {background};
            height: {size}px;
            margin: 0px {size}px 0px {size}px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {handle_color};
            min-width: 20px;
        }}
        QScrollBar::handle:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::handle:horizontal:pressed {{
            background-color: {hover_color};
        }}
        
        QScrollBar::sub-line:horizontal{{
            background-color: none;
            border: none;
            width: {size}px;
            height: {size}px;
            subcontrol-position: left;
            subcontrol-origin: margin;
        }}
        QScrollBar::add-line:horizontal {{
            background-color: none;
            border: none;
            width: {size}px;
            height: {size}px;
            subcontrol-position: right;
            subcontrol-origin: margin;
        }}
        
        QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
            background-color: {background};
            width: {arrow_size}px;
            height: {arrow_size}px;
        }}
        QScrollBar::left-arrow:horizontal {{
            image: url({images["left"]});
            background-color: {handle_color};
        }}
        QScrollBar::left-arrow:horizontal:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::right-arrow:horizontal {{
            image: url({images["right"]});
            background-color: {handle_color};
        }}
        QScrollBar::right-arrow:horizontal:hover {{
            background-color: {hover_color};
        }}
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background-color: none;
        }}
    """

    return style


"""
Vertical
"""


def get_vertical():
    if data.theme["scroll_bar"]["show_arrows"]:
        return __vertical_with_arrows()
    else:
        return __vertical()


def __vertical():
    size = get_bar_width()
    background = data.theme["scroll_bar"]["background"]
    handle_color = data.theme["scroll_bar"]["handle"]
    hover_color = data.theme["scroll_bar"]["handle_hover"]
    style = f"""
        QScrollBar:vertical {{
            border: none;
            background-color: {background};
            background-image: none;
            width: {size}px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {handle_color};
            min-height: 20px;
        }}
        QScrollBar::handle:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::handle:vertical:pressed {{
            background-color: {hover_color};
        }}
        
        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
        {{
            border: none;
            background: none;
            width: 0px;
            height: 0px;
        }}
    """
    return style


def __vertical_with_arrows():
    size = get_bar_width()
    images = __get_images()
    arrow_size = get_arrow_size()
    background = data.theme["scroll_bar"]["background"]
    handle_color = data.theme["scroll_bar"]["handle"]
    hover_color = data.theme["scroll_bar"]["handle_hover"]
    style = f"""
        QScrollBar:vertical {{
            border: none;
            background-color: {background};
            background-image: none;
            width: {size}px;
            margin: {size}px 0px {size}px 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {handle_color};
            min-height: 20px;
        }}
        QScrollBar::handle:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::handle:vertical:pressed {{
            background-color: {hover_color};
        }}
        
        QScrollBar::add-line:vertical {{
            background-color: none;
            height: {size}px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }}
        QScrollBar::sub-line:vertical {{
            background-color: none;
            height: {size}px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }}
        
        
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            background-color: {background};
            width: {arrow_size}px;
            height: {arrow_size}px;
        }}
        QScrollBar::up-arrow:vertical {{
            image: url({images["up"]});
            background-color: {handle_color}
        }}
        QScrollBar::up-arrow:vertical:hover {{
            background-color: {hover_color};
        }}
        QScrollBar::down-arrow:vertical {{
            image: url({images["down"]});
            background-color: {handle_color}
        }}
        QScrollBar::down-arrow:vertical:hover {{
            background-color: {hover_color};
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """
    return style


"""
Vertical & horizontal
"""


def get_general():
    style = "{}\n{}".format(
        get_vertical(),
        get_horizontal(),
    )
    return style
