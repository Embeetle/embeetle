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

from pygdbmi.gdbescapes import advance_past_string_with_gdb_escapes


class StringStream:
    """A simple class to hold text so that when passed between functions, the
    object is passed by reference and memory does not need to be repeatedly
    allocated for the string.

    This class was written here to avoid adding a dependency to the project.
    """

    def __init__(self, raw_text, debug=False):
        self.raw_text = raw_text
        self.index = 0
        self.len = len(raw_text)

    def read(self, count):
        """Read count characters starting at self.index, and return those
        characters as a string."""
        new_index = self.index + count
        if new_index > self.len:
            buf = self.raw_text[self.index :]  # return to the end, don't fail
        else:
            buf = self.raw_text[self.index : new_index]
        self.index = new_index

        return buf

    def seek(self, offset):
        """Advance the index of this StringStream by offset characters."""
        self.index = self.index + offset

    def advance_past_chars(self, chars):
        """Advance the index past specific chars Args chars (list): list of
        characters to advance past.

        Return substring that was advanced past
        """
        start_index = self.index
        while True:
            current_char = self.raw_text[self.index]
            self.index += 1
            if current_char in chars:
                break

            elif self.index == self.len:
                break

        return self.raw_text[start_index : self.index - 1]

    def advance_past_string_with_gdb_escapes(self) -> str:
        """Advance the index past a quoted string until the end quote is
        reached, and return the string (after unescaping it)

        Must be called only after encountering a quote character.
        """
        assert self.index > 0 and self.raw_text[self.index - 1] == '"', (
            "advance_past_string_with_gdb_escapes called not at the start of a string "
            f"(at index {self.index} of text {self.raw_text!r}, "
            f"remaining string {self.raw_text[self.index:]!r})"
        )

        unescaped_str, self.index = advance_past_string_with_gdb_escapes(
            self.raw_text, start=self.index
        )
        return unescaped_str
