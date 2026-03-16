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

from __future__ import annotations
from typing import *
import re

if TYPE_CHECKING:
    pass


class Libfilter:
    """"""

    __slots__ = (
        "__gen_filter",
        "__author_filter",
        "__topic_filter",
        "__origin_filter",
    )

    def __init__(self) -> None:
        """"""
        self.__gen_filter: Optional[str] = None
        self.__author_filter: Optional[str] = None
        self.__topic_filter: Optional[str] = None
        self.__origin_filter: List[str] = []
        return

    #! ===========[ SETTERS ]=========== !#

    def set_search_filter(self, gen_filter: str) -> None:
        if gen_filter is not None:
            self.__gen_filter = gen_filter.lower()
            return
        self.__gen_filter = None
        return

    def set_author_filter(self, author_filter: str) -> None:
        if author_filter is not None:
            self.__author_filter = author_filter.lower()
            return
        self.__author_filter = None
        return

    def set_topic_filter(self, topic_filter: str) -> None:
        if topic_filter is not None:
            self.__topic_filter = topic_filter.lower()
            return
        self.__topic_filter = None
        return

    def set_origin_filter(self, origin_filter: List[str]) -> None:
        if origin_filter is not None:
            self.__origin_filter = origin_filter
            return
        self.__origin_filter = []
        return

    #! ===========[ GETTERS ]=========== !#

    def get_search_filter(self) -> Optional[str]:
        return self.__gen_filter

    def get_author_filter(self) -> Optional[str]:
        return self.__author_filter

    def get_topic_filter(self) -> Optional[str]:
        return self.__topic_filter

    def get_origin_filter(self) -> List[str]:
        return self.__origin_filter

    def get_search_pattern(self) -> Optional[re.Pattern]:
        return get_pattern(self.__gen_filter)

    def get_author_pattern(self) -> Optional[re.Pattern]:
        return get_pattern(self.__author_filter)

    def get_topic_pattern(self) -> Optional[re.Pattern]:
        return get_pattern(self.__topic_filter)

    def get_search_pattern_subst(self) -> str:
        return (
            '<span style="background-color: rgba(255, 255, 0, 0.4);">\\1</span>'
        )

    def get_author_pattern_subst(self) -> str:
        return '<span style="background-color: rgba(252, 175, 62, 0.4);">\\1</span>'


def sanitize_regex(user_input: str) -> str:
    """Sanitize the given string such that it will never mess up a regex
    pattern."""
    # Define the whitelist pattern
    whitelist_pattern: re.Pattern = re.compile(r"[^a-zA-Z0-9_]")
    # Remove characters not in the whitelist
    sanitized_input = whitelist_pattern.sub("", user_input)
    return sanitized_input


def get_pattern(user_input: Optional[str]) -> Optional[re.Pattern]:
    """Take the given 'user_input', which is entered by the user in one of the
    text fields and stored.

    as one of these:
     - self.__gen_filter
     - self.__author_filter
     - self.__topic_filter

    Then try to construct a regex pattern from this. Put the '(?i)' in front such that the whole
    pattern is case insensitive. Accept special regex characters - maybe the user wants to enter a
    regex. However, clean the regex characters if they would cause a crash.
    """
    if user_input is None:
        return None
    # (?i) makes rest of pattern case insensitive
    p_str: Optional[str] = None
    p: Optional[re.Pattern] = None
    try:
        # Try with the raw user input
        p_str = "(?i)(" + user_input + ")"
        p = re.compile(p_str)
    except:
        try:
            # Sanitize the user input first
            p_str = "(?i)(" + sanitize_regex(user_input=user_input) + ")"
            p = re.compile(p_str)
        except:
            # Give up
            p = None
    return p
