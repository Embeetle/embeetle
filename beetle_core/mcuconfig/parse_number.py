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

import re
from .error import ConfigError


# Parse unsigned number (could be floating point, plus an SI scale factor, at
# the beginning of a string.  Return a pair (number, rest) where 'rest' is the
# remaining string.
def parse_unsigned_float(string):
    if type(string) is not str:
        raise ConfigError(f"expected string, not '{string}'")
    number = re.match(r"(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", string)
    if not number:
        raise ValueError(f"Not a number: {string}")
    value = float(number.group(0))
    unit = string[number.end() :].lstrip()
    match unit[0:1]:
        case "T":
            return (value * 1e12, unit[1:])
        case "G":
            return (value * 1e9, unit[1:])
        case "M":
            return (value * 1e6, unit[1:])
        case "k":
            return (value * 1e3, unit[1:])
        case _:
            return (value, unit)
