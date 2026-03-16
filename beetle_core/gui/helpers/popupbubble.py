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
import os.path
import collections
import traceback
import ast
import inspect
import math
import functools
import textwrap
import difflib
import re
import time
import settings
import functions
import gui
import qt
import data
import components.actionfilter
import themes

"""
---------------------------------------------------------
Popup bubble for displaying information
---------------------------------------------------------
"""


class PopupBubble(qt.QLabel):
    click = qt.pyqtSignal()

    def __init__(self, *args, corner="bottom-left", **kwargs):
        super().__init__(*args, **kwargs)
        valid_corners = (
            "bottom-left",
            "bottom-right",
            "top-left",
            "top-right",
        )
        if not (corner in valid_corners):
            raise Exception(f"[PopupBubble] Unknown corner type: {corner}")
        self.corner = corner
        self.set_colors("white", "black")
        self.setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        self.setFont(
            qt.QFont(
                data.get_global_font_family(), data.get_general_font_pointsize()
            )
        )

    def set_colors(self, back_color, text_color):
        self.color_background = back_color
        self.color_text = text_color
        self.height_adjustment = 10 * data.get_global_scale()
        self.padding = 10
        if self.corner == "bottom-left" or self.corner == "bottom-right":
            margin_line = f"margin-bottom: {self.height_adjustment}px;"
        elif self.corner == "top-left" or self.corner == "top-right":
            margin_line = f"margin-top: {self.height_adjustment}px;"
        self.setStyleSheet(
            f"""
                background-color: transparent;
                color: {self.color_text};
                {margin_line}
            """
        )
        self.repaint()

    def sizeHint(self):
        sh = super().sizeHint()
        return qt.create_qsize(
            sh.width() + self.padding,
            sh.height() + self.height_adjustment,
        )

    def setText(self, text):
        super().setText(text)
        self.resize(self.sizeHint())

    def paintEvent(self, e):
        # Paint the pointy bubble
        qp = qt.QPainter()
        qp.begin(self)

        size = self.size()
        width = size.width()
        height = size.height()

        triangle_size = self.height_adjustment
        draw_width = width - 1
        draw_height = (height - 1) - triangle_size

        if self.corner == "bottom-left":
            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.setBrush(qt.QColor(self.color_background))
            qp.drawRect(0, 0, int(draw_width), int(draw_height))

            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(0, 0, 0, int(draw_height))

            offset = 1
            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.drawLine(
                int(offset),
                int(draw_height),
                int(triangle_size + offset),
                int(draw_height),
            )

            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(
                int(triangle_size + offset),
                int(draw_height),
                int(draw_width),
                int(draw_height),
            )
            qp.drawLine(int(draw_width), int(draw_height), int(draw_width), 0)
            qp.drawLine(int(draw_width), 0, 0, 0)

            # Triangle
            qp.drawLine(
                0, int(draw_height), 0, int(draw_height + triangle_size)
            )
            qp.drawLine(
                0,
                int(draw_height + triangle_size),
                int(triangle_size + offset),
                int(draw_height),
            )
            # Fill triangle
            path = qt.QPainterPath()
            path.moveTo(1, draw_height - 1)
            path.lineTo(1, draw_height + triangle_size - 1)
            path.lineTo(triangle_size + offset - 1, draw_height - 1)
            qp.fillPath(path, qt.QColor(self.color_background))

        elif self.corner == "bottom-right":
            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.setBrush(qt.QColor(self.color_background))
            qp.drawRect(0, 0, int(draw_width), int(draw_height))

            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(0, 0, 0, int(draw_height))

            offset = 1
            qp.drawLine(
                int(offset),
                int(draw_height),
                int(draw_width - (triangle_size + offset)),
                int(draw_height),
            )

            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.drawLine(
                int(draw_width - (triangle_size + offset) + 1),
                int(draw_height),
                int(draw_width),
                int(draw_height),
            )

            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(int(draw_width), int(draw_height), int(draw_width), 0)
            qp.drawLine(int(draw_width), 0, 0, 0)

            # Triangle
            qp.drawLine(
                int(draw_width - (triangle_size + offset) + 1),
                int(draw_height),
                int(draw_width),
                int(draw_height + triangle_size),
            )
            qp.drawLine(
                int(draw_width),
                int(draw_height + triangle_size),
                int(draw_width),
                int(draw_height),
            )
            # Fill triangle
            path = qt.QPainterPath()
            path.moveTo(draw_width - (triangle_size + offset) + 1, draw_height)
            path.lineTo(draw_width, draw_height + triangle_size - 1)
            path.lineTo(draw_width, draw_height - 1)
            qp.fillPath(path, qt.QColor(self.color_background))

        elif self.corner == "top-left":
            offset = 1
            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.setBrush(qt.QColor(self.color_background))
            qp.drawRect(
                0, int(triangle_size), int(draw_width), int(draw_height)
            )
            # Main border
            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(
                0, int(triangle_size), 0, int(draw_height + triangle_size)
            )
            qp.drawLine(
                0,
                int(draw_height + triangle_size),
                int(draw_width),
                int(draw_height + triangle_size),
            )
            qp.drawLine(
                int(draw_width),
                int(draw_height + triangle_size),
                int(draw_width),
                int(triangle_size),
            )
            qp.drawLine(
                int(draw_width),
                int(triangle_size),
                int(triangle_size),
                int(triangle_size),
            )

            # Triangle
            qp.drawLine(int(triangle_size), int(triangle_size), 0, 0)
            qp.drawLine(0, 0, 0, int(triangle_size))
            # Fill triangle
            path = qt.QPainterPath()
            path.moveTo(1, 1)
            path.lineTo(1, triangle_size)
            path.lineTo(triangle_size + offset - 2, triangle_size)
            qp.fillPath(path, qt.QColor(self.color_background))

        elif self.corner == "top-right":
            offset = 1
            qp.setPen(
                qt.QPen(
                    qt.QColor(self.color_background),
                    1,
                    qt.Qt.PenStyle.SolidLine,
                )
            )
            qp.setBrush(qt.QColor(self.color_background))

            # Main background
            qp.drawRect(
                0, int(triangle_size), int(draw_width), int(draw_height)
            )

            # Main border
            qp.setPen(
                qt.QPen(qt.QColor(self.color_text), 1, qt.Qt.PenStyle.SolidLine)
            )
            qp.drawLine(
                0, int(triangle_size), 0, int(draw_height + triangle_size)
            )
            qp.drawLine(
                0,
                int(draw_height + triangle_size),
                int(draw_width),
                int(draw_height + triangle_size),
            )
            qp.drawLine(
                int(draw_width),
                int(draw_height + triangle_size),
                int(draw_width),
                int(triangle_size),
            )
            qp.drawLine(
                int(draw_width - triangle_size - offset),
                int(triangle_size),
                0,
                int(triangle_size),
            )

            # Fill triangle
            path = qt.QPainterPath()
            path.moveTo(
                int(draw_width - (triangle_size + offset)), int(triangle_size)
            )
            path.lineTo(int(draw_width), 1)
            path.lineTo(int(draw_width), int(triangle_size))
            qp.fillPath(path, qt.QColor(self.color_background))
            # Triangle border
            qp.drawLine(
                int(draw_width - (triangle_size + offset)),
                int(triangle_size),
                int(draw_width),
                0,
            )
            qp.drawLine(int(draw_width), 0, int(draw_width), int(triangle_size))

        qp.end()

        # Paint the rest
        super().paintEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.click.emit()

    def popup(self, new_position, text):
        super().show()
        self.setText(text)
        self.reposition(new_position)

    def reposition(self, new_position):
        if self.corner == "bottom-right":
            offset_left = -self.width()
            offset_top = -self.height()
        else:
            raise Exception(
                f"[{self.__class__.__name__}] Unknown display corner: '{self.corner}'!"
            )
        self.move(
            int(new_position.x() + offset_left),
            int(new_position.y() + offset_top),
        )
        self.raise_()
