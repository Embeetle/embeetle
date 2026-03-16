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

import qt


class Hotspots:
    """Functions for styling text with hotspots (used by CustomEditor and
    PlainEditor)"""

    def style(self, editor, index_from, length, color=0xFF0000):
        """Style the text from/to with a hotspot."""
        send_scintilla = editor.SendScintilla
        qscintilla_base = qt.QsciScintillaBase
        # Use the scintilla low level messaging system to set the hotspot
        send_scintilla(qscintilla_base.SCI_STYLESETHOTSPOT, 2, True)
        send_scintilla(qscintilla_base.SCI_SETHOTSPOTACTIVEFORE, True, color)
        send_scintilla(qscintilla_base.SCI_SETHOTSPOTACTIVEUNDERLINE, True)
        send_scintilla(qscintilla_base.SCI_STARTSTYLING, index_from, 2)
        send_scintilla(qscintilla_base.SCI_SETSTYLING, length, 2)
