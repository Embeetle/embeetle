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

# '''
# '''
# from __future__ import unicode_literals
# import sys
# import ast
# import six
# class Printer(ast.NodeVisitor):
#     def __init__(self, file=sys.stdout, indent="  "):
#         self.indentation = 0
#         self.indent_with = indent
#         self.f = file
#     # overridden to make the API obvious
#     def visit(self, node):
#         super(Printer, self).visit(node)
#     def write(self, text):
#         self.f.write(six.text_type(text))
#     def generic_visit(self, node):
#         if isinstance(node, list):
#             nodestart = "["
#             nodeend = "]"
#             children = [("", child) for child in node]
#         else:
#             nodestart = type(node).__name__ + "("
#             nodeend = ")"
#             children = [(name + "=", value) for name, value in ast.iter_fields(node)]
#         if len(children) > 1:
#             self.indentation += 1
#         self.write(nodestart)
#         for i, pair in enumerate(children):
#             attr, child = pair
#             if len(children) > 1:
#                 self.write("\n" + self.indent_with * self.indentation)
#             if isinstance(child, (ast.AST, list)):
#                 self.write(attr)
#                 self.visit(child)
#             else:
#                 self.write(attr + repr(child))
#             if i != len(children) - 1:
#                 self.write(",")
#         self.write(nodeend)
#         if len(children) > 1:
#             self.indentation -= 1
