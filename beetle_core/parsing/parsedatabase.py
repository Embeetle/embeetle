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
import sqlite3
import time
import traceback
import qt
import data
import functions
import parsing


def lock_function(func):
    def lock_wrapper(*args, **kwargs):
        try:
            while ParseDatabase.lock == True:
                time.sleep(0.001)
            ParseDatabase.lock = True
            result = func(*args, **kwargs)
            ParseDatabase.lock = False
            return result
        except Exception as ex:
            ParseDatabase.lock = False
            raise ex

    return lock_wrapper


class ParseDatabase(qt.QObject):
    if parsing.CtagsParser.USING_DATABASE:
        DATABASE_NAME = "EODATABASE"
        lock = False

        def __init__(self):
            super().__init__()
            self.conn = sqlite3.connect(":memory:", check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._init_table()
            lock = False

        def _init_table(self):
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS {db} (".format(
                    db=self.DATABASE_NAME
                )
                + "   _type TEXT, "
                + "   name TEXT, "
                + "   path TEXT, "
                + "   line TEXT, "
                + "   pattern TEXT, "
                + "   typeref TEXT, "
                + "   kind TEXT, "
                + "   scope TEXT, "
                + "   scopeKind TEXT"
                + ")"
            )

        def add_tag(self, tag):
            self.cursor.execute(
                """
                INSERT INTO {db} 
                    (_type, name, path, line, pattern, 
                    typeref, kind, scope, scopeKind) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """.format(
                    db=self.DATABASE_NAME
                ),
                tag,
            )

        def add_tags(self, tag_list):
            self.cursor.executemany(
                """
                INSERT INTO {db}
                    (_type, name, path, line, pattern,
                    typeref, kind, scope, scopeKind)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """.format(
                    db=self.DATABASE_NAME
                ),
                tag_list,
            )

        def get_tag(self, name):
            data = None
            try:
                self.cursor.execute(
                    """
                    SELECT name, path, line FROM {db}
                      WHERE name = \"{n}\"
                    """.format(
                        db=self.DATABASE_NAME, n=name
                    )
                )
                data = self.cursor.fetchone()
            except:
                traceback.print_exc()

            if data is None:
                return (None, None, None)
            else:
                return data

        def get_tag_for_styling(self, name):
            data = None
            try:
                self.cursor.execute(
                    "SELECT name, kind FROM {db} ".format(db=self.DATABASE_NAME)
                    + '   WHERE name = "{n}"'.format(n=name)
                )
                data = self.cursor.fetchone()
            except:
                traceback.print_exc()

            if data is None:
                return (None, None)
            else:
                return data

        def get_all_tags(self):
            self.cursor.execute(
                "SELECT name FROM {db}".format(db=self.DATABASE_NAME)
            )
            data = self.cursor.fetchall()
            return [x[0] for x in data]

    else:
        tag_dict = None  # type: Dict[str, parsing.Tag]

        def __init__(self):
            super().__init__()
            self.tag_dict = {}  #

        def add_tag(self, tag):
            self.tag_dict[tag.name] = tag

        def get_tag(self, name):
            if name in self.tag_dict.keys():
                tag = self.tag_dict[name]
                return tag.name, tag.path, tag.line
            else:
                return (None, None, None)

        def get_tag_for_styling(self, name):
            if name in self.tag_dict.keys():
                tag = self.tag_dict[name]
                return tag.name, tag.kind
            else:
                return (None, None)

        def get_all_tags(self):
            d = self.tag_dict
            return [d[x].name for x in d.keys()]
