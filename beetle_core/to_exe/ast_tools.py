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
# import ast
# class FunctionTransformer(ast.NodeTransformer):
#     def visit_FunctionDef(self, node):
# #        print(node.name)
#         # remove the return type defintion
#         node.returns = None
#         # remove all argument annotations
#         if node.args.args:
#             for arg in node.args.args:
#                 arg.annotation = None
#             insert_default_values = []
#             reversed_defaults = list(reversed(node.args.defaults))
#             for i, arg in enumerate(node.args.args):
#                 if arg.arg == "self":
#                     continue
#                 test = (len(node.args.args) - i)
#                 if test > len(node.args.defaults):
#                     insert_default_values.append(ast.NameConstant(None))
#             for v in insert_default_values:
#                 node.args.defaults.insert(0, v)
#         children = ast.iter_child_nodes(node)
#         for c in children:
#             if isinstance(c, ast.FunctionDef):
#                 self.visit_FunctionDef(c)
#         return node
# #    def visit_Import(self, node):
# #        node.names = [n for n in node.names if n.name != 'typing']
# #        return node if node.names else None
# #
# #    def visit_ImportFrom(self, node):
# #        return node if node.module != 'typing' else None
# def test_ast():
#     import astunparse
#     with open("transformation_input.test.1", 'r', encoding="utf-8", errors="replace") as f:
#         text = f.read()
#     parsed_source = ast.parse(text)
#     # remove all type annotations, function return type definitions
#     # and import statements from 'typing'
#     transformed = FunctionTransformer().visit(parsed_source)
#     # convert the AST back to source code
#     unannotated_text = astunparse.unparse(transformed)
#     with open("output.py", 'w+', encoding="utf-8") as f:
#         f.write(unannotated_text)
# if __name__ == "__main__":
#     test_ast()
