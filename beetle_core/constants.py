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

## Only constants are allowed in this file!

from typing import *

HTML_TEMPLATE_ROW_NO_ICON = "<table>" "<tr>" "<td>{}</td>" "</tr>" "</table>"
HTML_TEMPLATE_ROW = (
    "<table>" "<tr>" "<td>{}</td>" "<td>{}</td>" "</tr>" "</table>"
)
HTML_TEMPLATE_ROW_TWO_ICONS = (
    "<table>"
    "<tr>"
    "<td>{}</td>"
    "<td>{}</td>"
    "<td>{}</td>"
    "</tr>"
    "</table>"
)
HTML_TEMPLATE_ROW_THREE_ICONS = (
    "<table>"
    "<tr>"
    "<td>{}</td>"
    "<td>{}</td>"
    "<td>{}</td>"
    "<td>{}</td>"
    "</tr>"
    "</table>"
)
HTML_TEMPLATE_ROW_TEXT_ONLY = "<table>" "<tr>" "<td>{}</td>" "</tr>" "</table>"
HTML_IMAGE_TEMPLATE = '<img class="image" src="{}" <<size-template>>/>'

file_extensions: Dict[str, Any] = {
    "beetle": [".btl"],
    "python": [".py", ".pyw", ".pyi", ".scons"],
    "cython": [".pyx", ".pxd", ".pxi"],
    "object": [".o"],
    "binary": [".bin"],
    "elf": [".elf"],
    "c": [".c"],
    "h": [".h"],
    "assembly": [".s", ".S", ".asm"],
    "cmake": [".cmake"],
    "linkerscript": [".ld"],
    "make": [".make", ".mk", ".mkf"],
    "matlab": [".mlx", ".matlab"],
    "cpp": [".c++", ".cc", ".cpp", ".cxx"],
    "hpp": [".h++", ".hh", ".hpp", ".hxx"],
    "pascal": [".pas", ".pp", ".lpr", ".cyp"],
    "oberon": [".mod", ".ob", ".ob2", ".cp"],
    "ada": [".ads", ".adb"],
    "json": [".json", ".json5", ".tjson5"],
    "lua": [".lua"],
    "d": [".d"],
    "nim": [".nim", ".nims"],
    "perl": [".pl", ".pm"],
    "xml": [".xml", ".tpy"],
    "batch": [".bat", ".batch"],
    "bash": [".sh"],
    "ini": [".ini"],
    "text": [".txt", ".text"],
    "coffeescript": [".coffee"],
    "csharp": [".cs"],
    "java": [".java"],
    "javascript": [".js"],
    "octave": [".m"],
    "routeros": [".rsc"],
    "sql": [".sql"],
    "postscript": [".ps"],
    "fortran": [".f90", ".f95", ".f03"],
    "fortran77": [".f", ".for"],
    "idl": [".idl"],
    "ruby": [".rb", ".rbw"],
    "html": [".html", ".htm"],
    "css": [".css"],
    "tcl": [".tcl"],
    "tex": [".tex"],
    "verilog": [".verilog", ".v"],
    "vhdl": [".vhdl"],
    "yaml": [".yml", ".yaml"],
    "zip": [
        ".zip",
        ".7z",
        ".tar",
        ".gz",
        ".tbz",
        ".txz",
        ".tzst",
        ".tgz",
        ".tar.gz",
        ".tar.br",
        ".tar.bz2",
        ".tar.xz",
        ".tar.zst",
    ],
}
