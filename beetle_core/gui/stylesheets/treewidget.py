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


def get_default(style=None, branches=False):
    if style == "old-style":
        node_closed_only = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_closed_only"]
            )
        )
        node_closed_middle = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_closed_middle"]
            )
        )
        node_closed_last = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_closed_last"]
            )
        )
        node_open_only = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_open_only"]
            )
        )
        node_open_middle = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_open_middle"]
            )
        )
        node_open_last = "url({})".format(
            iconfunctions.get_icon_abspath(
                data.theme["tree_widget_branch_images"]["node_open_last"]
            )
        )
    # New style tree
    else:
        node_closed_only = "none"
        node_closed_middle = "none"
        node_closed_last = "none"
        node_open_only = "none"
        node_open_middle = "none"
        node_open_last = "none"

    t = "url({})".format(
        iconfunctions.get_icon_abspath(
            data.theme["tree_widget_branch_images"]["t"]
        )
    )
    l = "url({})".format(
        iconfunctions.get_icon_abspath(
            data.theme["tree_widget_branch_images"]["l"]
        )
    )
    line = "url({})".format(
        iconfunctions.get_icon_abspath(
            data.theme["tree_widget_branch_images"]["line"]
        )
    )

    # Note from @Kristof:
    # I changed the background color in 'QTreeView::item:hover' from:
    #     data.theme["shade"][4]
    # into:
    #     data.theme["indication"]["hover"]
    # This makes the widget consistent with other buttons. Also, the shade nr. 4 is good for light
    # themes (like Air), but barely visible for dark themes (like Obsidian).
    if branches:
        style_sheet = f"""
            QTreeView {{
                background-color: {data.theme["fonts"]["default"]["background"]};
                border: none;
                margin: 0px;
                padding: 0px;
            }}

            QTreeView::item {{
                background-color: {data.theme["fonts"]["default"]["background"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
                height: {data.get_general_icon_pixelsize()}px;
                margin: 0px;
                padding: 0px;
            }}

            QTreeView::item:selected {{
                background-color: {data.theme["indication"]["background_selection"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
            }}

            QTreeView::item:hover {{
                background-color: {data.theme["indication"]["hover"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
            }}

            QTreeView::branch {{
                background-color: {data.theme["fonts"]["default"]["background"]};
            }}
            QTreeView::branch:has-siblings:!adjoins-item {{
                border-image: {line} 0;
            }}
            QTreeView::branch:has-siblings:adjoins-item {{
                border-image: {t} 0;
            }}
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
                border-image: {l} 0;
            }}

            QTreeView::branch:closed:has-children:!has-siblings {{
                border-image: {node_closed_last};
            }}
            QTreeView::branch:closed:has-children:has-siblings {{
                border-image: {node_closed_middle};
            }}

            QTreeView::branch:open:has-children:!has-siblings {{
                border-image: {node_open_last};
            }}
            QTreeView::branch:open:has-children:has-siblings  {{
                border-image: {node_open_middle};
            }}
        """
    else:
        style_sheet = f"""
            QTreeView {{
                background-color: {data.theme["fonts"]["default"]["background"]};
                border: none;
                margin: 0px;
                padding: 0px;
            }}

            QTreeView::item {{
                background-color: {data.theme["fonts"]["default"]["background"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
                height: {data.get_general_icon_pixelsize()}px;
                margin: 0px;
                padding: 0px;
            }}

            QTreeView::item:selected {{
                background-color: {data.theme["indication"]["background_selection"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
            }}

            QTreeView::item:hover {{
                background-color: {data.theme["indication"]["hover"]};
                color: {data.theme["fonts"]["default"]["color"]};
                border: none;
            }}
        """
    return style_sheet
