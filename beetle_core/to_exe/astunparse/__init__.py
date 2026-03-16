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

# #
# """
# """
# from __future__ import absolute_import
# from six.moves import cStringIO
# from .unparser import Unparser
# from .printer import Printer
# __version__ = '1.6.3'
# def unparse(tree):
#     v = cStringIO()
#     Unparser(tree, file=v)
#     return v.getvalue()
# def dump(tree):
#     v = cStringIO()
#     Printer(file=v).visit(tree)
#     return v.getvalue()
