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
import sys
import itertools
import functools
import inspect
import keyword
import re
import collections
import textwrap
import qt
import data
import components
import themes
import gui.forms.mainwindow
import functions
import settings
import lexers
import traceback

"""
-------------------------------------------------------------------------
Overlay used for painting information point about the main window's
objects that are accessible with keyboard shortcuts
-------------------------------------------------------------------------
"""


class InformationOverlay:
    INFO_POINT_SIZE = (30, 30)
    parent = None
    overlay_label = None
    storage = []

    @staticmethod
    def create_info_point(
        parent,
        text,
        position,
        description=None,
        description_offset=True,
        store=True,
    ):
        width, height = InformationOverlay.INFO_POINT_SIZE
        text_size = 12
        info_label = qt.QLabel(parent)
        info_label.setGeometry(
            int(position[0]), int(position[1]), int(width), int(height)
        )
        info_point_color = data.theme["shade"][7]
        info_label.setStyleSheet(
            "QLabel {"
            + "    border-color: {0};".format(data.theme["button_border"])
            + "    border-width: 2px;"
            + "    border-style: solid;"
            + "    padding: 2px;"
            + "    background: #cc{0};".format(info_point_color)
            + "    margin: 0px 0px 0px 0px;"
            + "}"
            + "QLabel:hover {"
            + "    border-color: {0};".format(data.theme["button_border"])
            + "    border-width: 2px;"
            + "    border-style: solid;"
            + "    padding: 2px;"
            + "    background: #ff{0};".format(info_point_color)
            + "    margin: 0px 0px 0px 0px;"
            + "}"
        )
        info_label.setText(text)
        font = qt.QFont(data.current_font_name, text_size)
        font.setBold(True)
        info_label.setFont(font)
        info_label.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        if description is not None:
            if not description in descriptions.keys():
                raise ValueError(
                    "Information overlay: description "
                    + "'{}' does not exist!".format(description)
                )

            def info_click(event):
                if hasattr(info_label, "description"):
                    info_label.hide()
                    info_label.description.show()
                else:
                    description_label = qt.QLabel(parent)
                    description_label.setFont(
                        qt.QFont(data.current_font_name, int(text_size * 1.2))
                    )
                    description_label.setWordWrap(True)
                    description_label.setMaximumWidth(600)
                    description_label.setStyleSheet(
                        "QLabel {"
                        + "    border-color: {0};".format(
                            data.theme["button_border"]
                        )
                        + "    border-width: 2px;"
                        + "    border-style: solid;"
                        + "    padding: 2px;"
                        + "    background: #ff{0};".format(
                            data.theme["shade"][7]
                        )
                        + "    margin: 0px 0px 0px 0px;"
                        + "}"
                    )
                    description_label.setText(descriptions[description])
                    description_label.adjustSize()
                    info_label.description = description_label
                    info_label.hide()
                    description_label.show()
                    x_offset = info_label.pos().x()
                    y_offset = info_label.pos().y()
                    if description_offset == True:
                        x_offset -= (
                            description_label.size().width()
                            - info_label.size().width()
                        ) / 2
                        y_offset -= (
                            description_label.size().height()
                            - info_label.size().height()
                        ) / 2
                    else:
                        y_offset += height
                    description_label.move(x_offset, y_offset)

                    def description_click(event):
                        description_label.hide()
                        info_label.show()

                    description_label.mousePressEvent = description_click

            info_label.mousePressEvent = info_click
        if store == True:
            InformationOverlay.storage.append(info_label)
        return info_label

    def __init__(self, parent):
        if not isinstance(parent, gui.forms.mainwindow.MainWindow):
            raise ValueError(
                "Information overlay needs a MainWindow parent, "
                + "not {}!".format(parent.__class__)
            )
        self.parent = parent

    def show(self, widgets_with_text_list):
        self.overlay_label = qt.QFrame(self.parent)
        self.overlay_label.setGeometry(
            0, 0, self.parent.size().width(), self.parent.size().height()
        )
        for items in widgets_with_text_list:
            if len(items) == 2:
                widget, text = items
                description = None
                offset = True
            elif len(items) == 3:
                widget, text, description = items
                offset = True
            elif len(items) == 4:
                widget, text, description, offset = items
            else:
                raise ValueError("Information overlay: wrong widget arguments!")
            position = functions.center_rectangle_to_widget(
                widget, self.parent, self.INFO_POINT_SIZE
            )
            self.create_info_point(
                self.overlay_label, text, position, description, offset
            )
        self.overlay_label.show()

    def show_on_parent(self, widgets_with_text_list):
        for items in widgets_with_text_list:
            if len(items) == 2:
                widget, text = items
                description = None
                offset = True
            elif len(items) == 3:
                widget, text, description = items
                offset = True
            elif len(items) == 4:
                widget, text, description, offset = items
            else:
                raise ValueError("Information overlay: wrong widget arguments!")
            position = functions.center_rectangle_to_widget(
                widget, self.parent, self.INFO_POINT_SIZE
            )
            info_point = self.create_info_point(
                self.parent, text, position, description, offset
            )
            info_point.show()

    def hide(self):
        if self.overlay_label is not None:
            self.overlay_label.hide()
        for w in InformationOverlay.storage:
            if hasattr(w, "description"):
                d = w.description
                d.setParent(None)
                d.deleteLater()
                w.description = None
            w.setParent(None)
            w.deleteLater()
        InformationOverlay.storage = []


descriptions = {
    "Main Editing Window": (
        """
        This is the <b>Main Window</b>,
        which is mainly used for editing,
        but you can <b>drag&drop</b> tabs from other windows into it.
        Opening files will by default open them for editing in this window.
    """.strip()
    ),
    "Upper Editing Window": (
        """
        This is the <b>Upper Window</b>,
        which is where the <b>Filetree</b> and <b>Diagnostics Window</b>
        open in. You can <b>drag&drop</b> tabs from other windows into it.
    """.strip()
    ),
    "Lower Editing Window": (
        """
        This is the <b>Lower Window</b>,
        which is where the <b>Project Dashboard</b> and <b>Messages Window</b>
        open in. You can <b>drag&drop</b> tabs from other windows into it.
    """.strip()
    ),
    "Project Name": "Label showing the current project",
    "Clean Button": "Clean the current project directories",
    "Build Button": "Build the current project",
    "Flash Button": "Flash the current project",
    "Debug Button": "Start debugging the current project",
    "Home Button": "Open the home window for creating/loading/... projects",
}
