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


def get_styled() -> str:
    """"""
    height = 8 * data.get_global_scale()
    radius_bar = 0
    radius_handle = 1
    background_color = data.theme["fonts"]["default"]["background"]
    border_color_bar = data.theme["button_border"]
    border_color_handle = data.theme["shade"][-1]
    stylesheet = f"""
        QSlider::groove:horizontal {{
            border: 1px solid #bbb;
            background: {background_color};
            height: {height}px;
            border-radius: {radius_bar}px;
        }}
        
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                stop:0 {data.theme["shade"][5]}, stop:1 {data.theme["shade"][-1]});
            border: 1px solid {border_color_bar};
            height: {height}px;
            border-radius: {radius_bar}px;
        }}
        
        QSlider::add-page:horizontal {{
            background: {background_color};
            border: 1px solid {border_color_bar};
            height: {height}px;
            border-radius: {radius_bar}px;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid {border_color_handle};
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: {radius_handle}px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: {radius_handle}px;
        }}
        
        QSlider::sub-page:horizontal:disabled {{
            background: #bbb;
            border-color: #999;
        }}
        
        QSlider::add-page:horizontal:disabled {{
            background: #eee;
            border-color: #999;
        }}
        
        QSlider::handle:horizontal:disabled {{
            background: #eee;
            border: 1px solid #aaa;
            border-radius: {radius_handle}px;
        }}
    """
    return stylesheet


def get_styled_ticked() -> str:
    """"""
    height = 8 * data.get_global_scale()
    radius_bar = 0
    radius_handle = 1
    background_color = data.theme["fonts"]["default"]["background"]
    border_color_bar = data.theme["button_border"]
    border_color_handle = data.theme["shade"][-1]
    tickmark_color = "#cc0000"  # Color setting doesn't work
    stylesheet = f"""
        QSlider::groove:horizontal {{
            /* Putting anything here removes the tickmarks. */
            /* I don't know why. */
        }}
        
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                stop:0 {data.theme["shade"][5]}, stop:1 {data.theme["shade"][-1]});
            border: 1px solid {border_color_bar};
            height: {height}px;
            border-radius: {radius_bar}px;
        }}
        
        QSlider::add-page:horizontal {{
            background: {background_color};
            border: 1px solid {border_color_bar};
            height: {height}px;
            border-radius: {radius_bar}px;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid {border_color_handle};
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: {radius_handle}px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: {radius_handle}px;
        }}
        
        QSlider::sub-page:horizontal:disabled {{
            background: #bbb;
            border-color: #999;
        }}
        
        QSlider::add-page:horizontal:disabled {{
            background: #eee;
            border-color: #999;
        }}
        
        QSlider::handle:horizontal:disabled {{
            background: #eee;
            border: 1px solid #aaa;
            border-radius: {radius_handle}px;
        }}
        
        QSlider::tickmark:horizontal {{
            background: {tickmark_color};
            height: 10px;
        }}
    """
    return stylesheet
