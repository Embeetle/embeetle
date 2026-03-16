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

import os_checker

USING_WINDOWS = os_checker.is_os("windows")


def print_red(x):
    if USING_WINDOWS:
        print(x)
    else:
        print("\033[91m {}\033[00m".format(x))


def print_green(x):
    if USING_WINDOWS:
        print(x)
    else:
        print("\033[92m {}\033[00m".format(x))


def print_cyan(x):
    if USING_WINDOWS:
        print(x)
    else:
        print("\033[96m {}\033[00m".format(x))


def fmt_green(x):
    if USING_WINDOWS:
        return x
    else:
        return "\033[92m {}\033[00m".format(x)


def fmt_cyan(x):
    if USING_WINDOWS:
        return x
    else:
        return "\033[96m {}\033[00m".format(x)
