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
# from __future__ import print_function
# import sys
# import os
# import argparse
# from .unparser import roundtrip
# from . import dump
# def roundtrip_recursive(target, dump_tree=False):
#     if os.path.isfile(target):
#         print(target)
#         print("=" * len(target))
#         if dump_tree:
#             dump(target)
#         else:
#             roundtrip(target)
#         print()
#     elif os.path.isdir(target):
#         for item in os.listdir(target):
#             if item.endswith(".py"):
#                 roundtrip_recursive(os.path.join(target, item), dump_tree)
#     else:
#         print(
#             "WARNING: skipping '%s', not a file or directory" % target,
#             file=sys.stderr
#         )
# def main(args):
#     parser = argparse.ArgumentParser(prog="astunparse")
#     parser.add_argument(
#         'target',
#         nargs='+',
#         help="Files or directories to show roundtripped source for"
#     )
#     parser.add_argument(
#         '--dump',
#         type=bool,
#         help="Show a pretty-printed AST instead of the source"
#     )
#     arguments = parser.parse_args(args)
#     for target in arguments.target:
#         roundtrip_recursive(target, dump_tree=arguments.dump)
# if __name__ == "__main__":
#     main(sys.argv[1:])
