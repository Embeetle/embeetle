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
import re
import functools
import time
import qt
import data
import functions
import parsing

"""
---------------------------------------------------------
Finder for all header files referenced in a source file
---------------------------------------------------------
"""


class FileParser(qt.QObject):
    ALL_EXTENSIONS = [".h", ".c", ".hpp", ".cpp", ".h++", ".c++"]
    HEADER_EXTENSIONS = [".h", ".hpp", ".h++"]

    file_with_path = None  # type: str
    base_search_paths = None  # type: typing.List[str]
    source_files = None  # type: typing.List[str]
    found_headers = None  # type: typing.Dict[str, str]
    ctags_parser = None  # type: parsing.CtagsParser
    parsed_tags = None  # type: typing.List[parsing.Tag]

    def __init__(
        self,
        file_with_path,
        base_search_paths,
        sync=False,
        file_parsed_func=None,
        completed_func=None,
    ):
        extension = functions.get_file_extension(file_with_path)
        if not (extension in self.ALL_EXTENSIONS):
            raise Exception(
                "File '{}' is not a C or C++ file!".format(file_with_path)
            )

        self.file_with_path = file_with_path
        if isinstance(base_search_paths, str):
            self.base_search_paths = [base_search_paths]
        elif isinstance(base_search_paths, list) and all(
            [isinstance(x, str) for x in base_search_paths]
        ):
            self.base_search_paths = base_search_paths
        else:
            raise Exception("FileParser: Wrong base paths in the constructor!")
        self.parsed_tags = []
        self.ctags_parser = parsing.CtagsParser()
        if sync == True:
            self.ctags_parser.set_synchronous(True)
        else:
            if completed_func is not None:
                self.ctags_parser.parsedFile.connect(file_parsed_func)
            if completed_func is not None:
                self.ctags_parser.parsingComplete.connect(completed_func)
        self.find_and_parse_headers()

    @staticmethod
    def get_referenced_headers(file_with_path):
        """Function for returning a list of all header file includes.

        This is for C/C++ source files only!
        """
        pattern = r'^\s*\#\s*include\s+["<]([^">]+)*[">]'
        text = ""
        with open(file_with_path, "r", newline="\n") as f:
            text = f.read()
            f.close()
        result = re.findall(pattern, text, re.MULTILINE)
        return result

    def _recurse_for_headers(self, file_with_path, header_list=None):
        # These are names WITHOUT THE PATH!
        if header_list is None:
            header_list = []
        file_header_references = FileParser.get_referenced_headers(
            file_with_path
        )
        for header in file_header_references:
            header = os.path.basename(header)
            extension = functions.get_file_extension(header)
            if not (extension in self.HEADER_EXTENSIONS):
                continue
            if header in self.found_headers.keys():
                #                print(header)
                header = self.found_headers[header][0]
                header_name = os.path.basename(header)
                if header_name in header_list:
                    continue
                header_list.append(header_name)
                header_list.extend(
                    self._recurse_for_headers(header, header_list)
                )
            #                    raise Exception(
            #                        "Too many '{} / {}' headers to choose from!".format(
            #                            header, len(self.found_headers[header])
            #                        )
            #                    )
            else:
                #                raise Exception(
                #                    "Header '{}' was not found!".format(header)
                #                )
                message = "Header '{}' was not found, ".format(header)
                message += "skipping it!"
                print(message)
        return list(set(header_list))

    def get_headers_recursively(self):
        """Function for returning all of the header include directives
        recursively through all of the headers.

        This is for C/C++ source files only!
        """
        #        self.create_source_file_listing()
        #        start_time = time.time()
        headers = self._recurse_for_headers(self.file_with_path)
        #        for h in headers:
        #            print(h)
        #        print("Header traversal time: ", time.time() - start_time)
        return headers

    def create_source_file_listing(self):
        self.source_files = []
        self.found_headers = {}
        # Get all source files
        self.source_files = []
        for path in self.base_search_paths:
            self.source_files.extend(
                functions.get_file_list(path, extensions=self.HEADER_EXTENSIONS)
            )
        # Parse the header files into a dictionary
        for f in self.source_files:
            file_name_only = os.path.basename(f)
            extension = functions.get_file_extension(f)
            #            print(file_name_only)
            if extension in self.HEADER_EXTENSIONS:
                if file_name_only in self.found_headers.keys():
                    self.found_headers[file_name_only].append(f)
                else:
                    self.found_headers[file_name_only] = [f]

    def find_and_parse_headers(self):
        self.create_source_file_listing()
        # These are names WITHOUT THE PATH!
        file_header_references = self.get_headers_recursively()
        # Add the root file for parsing
        self.ctags_parser.add(self.file_with_path)
        for header in file_header_references:
            if header in self.found_headers.keys():
                #                print(self.found_headers[header])
                if len(self.found_headers[header]) > 0:
                    header_with_path = self.found_headers[header][0]
                    if (
                        header_with_path
                        in self.ctags_parser.get_files_to_parse()
                    ):
                        print(
                            "Already added header '{}' to ctags parser.".format(
                                header  # header_with_path
                            )
                        )
                        continue
                    if self.ctags_parser.add(header_with_path) == False:
                        raise Exception(
                            "Could not add '{}' to ctags parser!".format(
                                header_with_path
                            )
                        )
                    else:
                        print(
                            "Added header '{}' to ctags parser.".format(
                                header  # header_with_path
                            )
                        )
                else:
                    raise Exception(
                        "Too many '{} / {}' headers to choose from!".format(
                            header, len(self.found_headers[header])
                        )
                    )
            else:
                print("Header '{}' was not found!".format(header))
        # Parse the headers
        #        start_time = time.time()
        self.ctags_parser.parse()


#        print("CTags parsing time: ", time.time() - start_time)
