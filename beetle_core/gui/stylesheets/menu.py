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


def get_popup_stylesheet(font_scale=10, icon_scale=40, isconsole=False):
    """Stylesheet for the rightmouse button menu. Note: the size of the icons
    are unfortunately not decided here. After applying this stylesheet to a
    popup-menu, you've got to write the following codeline:

        components.thesquid.TheSquid.customize_menu_style(self, enlarge=...)

    with the parameter 'enlarge' being the enlargement of the icons you want, compared to the standard icon sizes
    of other menus (like the toplevel menus).
    """
    if isconsole:
        return get_consolepopup_stylesheet(font_scale, icon_scale)
    styleStr = f"""
        QMenu {{
            font-family: Inconsolata;
            font-size: {data.get_general_font_pointsize()}pt;
            color: #ff2e3436;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                              stop: 0   #fffefefe, stop: 0.5 #ffeeeeec,
                                              stop: 0.6 #ffeeeeec, stop: 1   #fffefefe);
            border-color: #ffd3d7cf;
            border-style: solid;
            border-width: 1px;
            border-radius: 2px;
            margin: 0px 0px 0px 0px;
        }}
        QMenu::item {{
            border: none;
            padding: 2px {int(1.1*icon_scale)}px 2px {int(1.1*icon_scale)}px;
            spacing: {int(0.30*icon_scale)}px;
        }}
        QMenu::item:selected {{
            font-size: {data.get_general_font_pointsize()}pt;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                             stop: 0   #ffffffff, stop: 0.5 #ffeeeeec,
                                             stop: 0.6 #ffeeeeec, stop: 1   #ffffffff);
            border-color: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                                          stop: 0   #ffb6b6b6, stop: 0.5 #ffd2d2d1,
                                          stop: 0.6 #ffd2d2d1, stop: 1   #ffb6b6b6);
            border-style: solid;
            border-width: 1px;
            border-radius: 2px;
        }}
        QMenu::separator {{
            height: 2px;
            margin: 2px {int(0.20*icon_scale)}px 2px {int(0.20*icon_scale)}px;
        }}
    """
    return styleStr


def get_consolepopup_stylesheet(font_scale, icon_scale):
    """Stylesheet for the rightmouse button menu. Note: the size of the icons
    are unfortunately not decided here. After applying this stylesheet to a
    popup-menu, you've got to write the following codeline:

        components.TheSquid.customize_menu_style(self, enlarge=...)

    with the parameter 'enlarge' being the enlargement of the icons you want, compared to the standard icon sizes
    of other menus (like the toplevel menus).
    """
    styleStr = f"""
        QMenu {{
            font-family: {data.get_global_font_family()};
            font-size: {data.get_general_font_pointsize()}pt;
            color: #ffeeeeec;
            background-color: qlineargradient(x1:0, y1:1, x2:1, y2:1,
                                              stop: 0 #ff2e3436, stop: 1 #ff888a85);
            border-color: #ffd3d7cf;
            border-style: solid;
            border-width: 1px;
            border-radius: 2px;
            margin: 0px 0px 0px 0px;
        }}
        QMenu::item {{
            border: none;
            padding: 2px {int(1.1*icon_scale)}px 2px {int(1.1*icon_scale)}px;
            spacing: {int(0.30*icon_scale)}px;
        }}
        QMenu::item:selected {{
            font-size: {data.get_general_font_pointsize()}pt;
            color: #ffffffff;
            background-color: #883465a4;
            border-color: 1px solid #cc204a87;
        }}
        QMenu::separator {{
            height: 2px;
            margin: 2px {int(0.20*icon_scale)}px 2px {int(0.20*icon_scale)}px;
        }}
    """
    return styleStr


def get_general_stylesheet():
    arrow_icon = iconfunctions.get_icon_abspath(
        "icons/arrow/chevron/chevron_right.png"
    )
    arrow_size = data.get_general_icon_pixelsize() * 0.8
    style_sheet = f"""
QMenu {{
    background-color: {data.theme["menu_background"]};
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
    color: {data.theme["fonts"]["default"]["color"]};
    border-color: {data.theme["button_border"]};
    border-style: solid;
    border-width: 1px;
    border-radius: 2px;
    margin: 0px 0px 0px 0px;
    menu-scrollable: 1;
}}
QMenu::item {{
    border: none;
    padding-top: 2px;
    padding-bottom: 2px;
    padding-right: 20px;
    spacing: 12px;
    margin: 0px;
    color: {data.theme["fonts"]["default"]["color"]};
}}
QMenu::item:enabled {{
    color: {data.theme["fonts"]["default"]["color"]};
    border: none;
}}
QMenu::item:disabled {{
    color: {data.theme["fonts"]["disabled"]["color"]};
}}
QMenu::item:selected {{
    background-color: {data.theme["shade"][3]};
}}
QMenu::separator {{
    background: {data.theme["fonts"]["default"]["color"]};
    height: 1px;
    margin: 2px 8px 2px 8px;
}}
QMenu::right-arrow {{
    image: url({arrow_icon});
    width: {arrow_size}px;
    height: {arrow_size}px;
}}
    """
    return style_sheet


def get_selection_menu_stylesheet(
    font_name="Inconsolata", font_scale=10, icon_scale=40
):
    return f"""
QMenu {{
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
    color: #ff2e3436;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop: 0   #fffefefe, stop: 0.5 #ffeeeeec,
                                        stop: 0.6 #ffeeeeec, stop: 1   #fffefefe);
    border-color: #ffd3d7cf;
    border-style: solid;
    border-width: 1px;
    border-radius: 2px;
    margin: 0px 0px 0px 0px;
}}
QMenu::item {{
    border: none;
    padding-top: 2px;
    /* padding-left: {int(0.3*icon_scale)}px; */
    padding-bottom: 2px;
    padding-right: {int(1.5*icon_scale)}px;
    spacing: {int(0.30*icon_scale)}px;
    color: #ffaaaaaa;
}}
QMenu::item:enabled {{
    font-size: {data.get_general_font_pointsize()}pt;
    color: #ff000000;
}}
QMenu::item:selected {{
    font-size: {data.get_general_font_pointsize()}pt;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop: 0   #ffffffff, stop: 0.5 #ffeeeeec,
                                    stop: 0.6 #ffeeeeec, stop: 1   #ffffffff);
    border-color: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                                    stop: 0   #ffb6b6b6, stop: 0.5 #ffd2d2d1,
                                    stop: 0.6 #ffd2d2d1, stop: 1   #ffb6b6b6);
    border-style: solid;
    border-width: 1px;
    border-radius: 2px;
}}
QMenu::separator {{
    height: 2px;
    margin: 2px {int(0.20*icon_scale)}px 2px {int(0.20*icon_scale)}px;
}}
QMenu[red=true] {{
    color: #ffcc0000;
}}
    """


def get_menuFileFrm_stylesheet():
    styleStr = f"""
QFrame {{
    margin: 0px 0px 0px 0px;
    border: 0px solid #00000000;
    padding: 0px 0px 0px 0px;
    spacing: 0px 0px 0px 0px;
    background: #00000000;
}}
QFrame:hover {{
    background: #883465a4;
    border: 1px solid #cc204a87;
}}
    """
    return styleStr


def get_menuFileBtn_stylesheet():
    styleStr = f"""
QPushButton {{
    margin: 0px 0px 0px 0px;
    padding: 0px 0px 0px 0px;
    spacing: 0px 0px 0px 0px;
    background-color: #00000000;
    border-color: #00000000;
    border-style: solid;
}}
    """
    return styleStr


def get_menuFileLbl_stylesheet(color="#ff2e3436"):
    styleStr = f"""
QLabel {{
    margin: 0px 0px 0px 0px;
    border: 0px solid #00000000;
    
    padding-top: 2px;
    padding-bottom: 2px;
    padding-right: 20px;
    spacing: 12px;
    
    background-color: #00000000;
    color: {color};
    font-family: {data.get_global_font_family()};
    font-size: {data.get_general_font_pointsize()}pt;
}}
QLabel[red=true] {{
    color: #cc0000;
}}
    """
    return styleStr
