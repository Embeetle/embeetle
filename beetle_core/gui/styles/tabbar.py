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
import functools
import qt
import data
import gui
import functions
import traceback
import gui.stylesheets.menu
import gui.stylesheets.tabbar
import gui.stylesheets.tabwidget
import components.thesquid


class TabBarProxyStyle(qt.QProxyStyle):
    #    def drawControl(self, element, option, painter, widget):
    #        items = (
    #            qt.QPalette.ColorRole.Window,
    #            qt.QPalette.Background,
    #            qt.QPalette.ColorRole.WindowText,
    #            qt.QPalette.Foreground,
    #            qt.QPalette.ColorRole.Base,
    #            qt.QPalette.ColorRole.AlternateBase,
    #            qt.QPalette.ColorRole.ToolTipBase,
    #            qt.QPalette.ColorRole.ToolTipText,
    #            qt.QPalette.ColorRole.PlaceholderText,
    #            qt.QPalette.ColorRole.Text,
    #            qt.QPalette.ColorRole.Button,
    #            qt.QPalette.ColorRole.ButtonText,
    #            qt.QPalette.ColorRole.BrightText,
    #            qt.QPalette.ColorRole.Light,
    #            qt.QPalette.ColorRole.Midlight,
    #            qt.QPalette.ColorRole.Dark,
    #            qt.QPalette.ColorRole.Mid,
    #            qt.QPalette.ColorRole.Shadow,
    #            qt.QPalette.ColorRole.Highlight,
    #            qt.QPalette.ColorRole.HighlightedText,
    #            qt.QPalette.ColorRole.Link,
    #            qt.QPalette.ColorRole.LinkVisited,
    #        )
    #        color = qt.QColor("red")
    #        for p in items:
    #            option.palette.setColor(p, color)
    #            option.palette.setBrush(p, color)
    #        painter.setPen(color)
    #        painter.setBrush(color)
    #        painter.setBackground(color)
    #        painter.setFont(qt.QFont("Arial", data.get_general_font_pointsize()))
    #        return qt.QProxyStyle.drawControl(self, element, option, painter, widget)

    def drawItemText(self, painter, rect, flags, pal, enabled, text, textRole):
        items = (
            qt.QPalette.ColorRole.WindowText,
            qt.QPalette.ColorRole.PlaceholderText,
            qt.QPalette.ColorRole.Text,
            qt.QPalette.ColorRole.ButtonText,
            qt.QPalette.ColorRole.BrightText,
            qt.QPalette.ColorRole.HighlightedText,
        )
        color = qt.QColor("orange")
        for p in items:
            pal.setColor(p, color)
            pal.setBrush(p, color)
        #        painter.setFont(qt.QFont("Arial", data.get_general_font_pointsize()))
        return qt.QProxyStyle.drawItemText(
            self, painter, rect, flags, pal, enabled, text, textRole
        )
