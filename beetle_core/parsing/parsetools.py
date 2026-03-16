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

#!/usr/bin/python3

import sys
import os
import functools
import data
import functions
import parsing

"""
Helper functions for parsing source code
"""


def parse_file_sync(file_path, source_directories):
    cp = data.current_project
    if cp is None:
        raise Exception("No active project, open a project to enable parsing!")
    elif cp.check_if_project_file(file_path) == False:
        raise Exception(
            "File '{}' is not part of the current project!".format(file_path)
        )
    parser = parsing.FileParser(file_path, source_directories, sync=True)
    return data.tag_database.get_all_tags()


def parse_file_async(
    file_path, source_directories, file_parsed_func, completed_func
):
    cp = data.current_project
    if cp is None:
        raise Exception("No active project, open a project to enable parsing!")
    elif cp.check_if_project_file(file_path) == False:
        raise Exception(
            "File '{}' is not part of the current project!".format(file_path)
        )
    parser = parsing.FileParser(
        file_path,
        source_directories,
        sync=False,
        file_parsed_func=file_parsed_func,
        completed_func=completed_func,
    )
