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
import sys, os, argparse, inspect, shutil, re
import colorama, lowbar
import fnmatch as _fn_

q = "'"

# * Folder locations
src_iconfolder = os.path.realpath(
    os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
).replace("\\", "/")
resources = os.path.dirname(src_iconfolder).replace("\\", "/")
dst_iconfolders = {
    "color_light": resources + "/icons_plump_color_light",
}

# * Color matrix
color_matrix = {
    "color": {
        "yellow": {"light": "#fce94f", "middle": "#edd400", "dark": "#c4a000"},
        "orange": {"light": "#fcaf3e", "middle": "#f57900", "dark": "#ce5c00"},
        "brown": {"light": "#e9b96e", "middle": "#c17d11", "dark": "#8f5902"},
        "green": {"light": "#8ae234", "middle": "#73d216", "dark": "#4e9a06"},
        "blue": {"light": "#729fcf", "middle": "#3465a4", "dark": "#204a87"},
        "purple": {"light": "#ad7fa8", "middle": "#75507b", "dark": "#5c3566"},
        "red": {"light": "#ef2929", "middle": "#cc0000", "dark": "#a40000"},
        "white": {"light": "#eeeeec", "middle": "#d3d7cf", "dark": "#babdb6"},
        "gray": {"light": "#888a85", "middle": "#555753", "dark": "#2e3436"},
    }
}


# ^                                         FIX SVG FILES                                          ^#
# % ============================================================================================== %#
# % Fix svg-files with inconsistent color definitions.                                             %#
# %                                                                                                %#


def fix_svg_files() -> None:
    """Some svg-files have inconsisten color definitions, like:

    <path
            fill="#1575E5"
            fill-rule="evenodd"
            d="M17.2247 11.8031C17.6771 ..."
            clip-rule="evenodd"
            id="path2"
            style="fill:#888a85;fill-opacity:1"
        />
    Here the color '#888a85' overrides the color '#1575E5' defined at the top. However, this is
    confusing for my automated scripts. Therefore, this function will do the overrides once and for
    all.
    """
    # & Intro
    printc(f"Fix svg files", color="yellow")
    printc(f"-------------", color="yellow")
    print(
        f"Fix the svg-issues in the icons from the source folder:\n"
        f"{q}{src_iconfolder}{q}\n"
    )

    # & Progressbar
    bar: lowbar.lowbar = lowbar.lowbar()
    bar.new()
    file_count = sum(
        len([f for f in files if f.endswith(".svg")])
        for _, _, files in os.walk(src_iconfolder)
    )
    i = 0

    # & Loop
    p = re.compile(r"(fill=\")(#\w+)(\"[^<]*)(fill:)(#\w+)")
    for root, folders, files in os.walk(src_iconfolder):
        for f in files:
            if not f.endswith(".svg"):
                continue
            i += 1
            # Update the bar once in a while
            if i % 20 == 0:
                perc: float = max(
                    0.0,
                    min(
                        100.0,
                        100.0 * (i / file_count),
                    ),
                )
                bar.update(int(perc))
            src_filepath = os.path.join(root, f).replace("\\", "/")
            src_filecontent = read_file(src_filepath)
            new_content = p.sub("\g<1>\g<5>\g<3>\g<4>\g<5>", src_filecontent)
            new_content = (
                new_content.replace("#a6cfff", "#729fcf")
                .replace("#1575e5", "#204a87")
                .replace("#A6CFFF", "#729fcf")
                .replace("#1575E5", "#204a87")
            )
            write_file(
                filepath=src_filepath,
                filecontent=new_content,
            )
            continue
        continue
    bar.clear()
    print()
    return


# ^                                        LIGHT SVG FILES                                         ^#
# % ============================================================================================== %#
# % Lighten up all svg-files to fit on a dark background.                                          %#
# %                                                                                                %#


def light_all() -> None:
    """
    Lighten up the svg-files from the folder with the given color-set:
    """
    __src_iconfolder = resources + f"/icons_plump_color"
    __dst_iconfolder = resources + f"/icons_plump_color_light"

    # & Intro
    txt = f"icons_plump_color => icons_plump_color_light"
    printc(txt, color="yellow")
    printc("-" * len(txt), color="yellow")

    # & Progressbar
    bar: lowbar.lowbar = lowbar.lowbar()
    bar.new()
    file_count = sum(
        len([f for f in files if f.endswith(".svg")])
        for _, _, files in os.walk(__src_iconfolder)
    )
    i = 0

    # & Loop
    depth = 0
    for root, folders, files in os.walk(__src_iconfolder):
        for f in files:
            # $ Ignore irrelevant files
            if not f.endswith(".svg"):
                continue
            # $ Update the bar once in a while
            i += 1
            if i % 20 == 0:
                perc: float = max(
                    0.0,
                    min(
                        100.0,
                        100.0 * (i / file_count),
                    ),
                )
                bar.update(int(perc))
            # $ Make it ligher and write file
            src_filepath = os.path.join(root, f).replace("\\", "/")
            src_filecontent = read_file(src_filepath)
            write_file(
                filepath=src_filepath.replace(
                    __src_iconfolder, __dst_iconfolder
                ),
                filecontent=light_file(src_filecontent),
            )
            continue
        continue
    bar.clear()
    print()
    return


def light_file(filecontent: str) -> str:
    """"""
    # $ Create conversion dictionary
    found_colors = find_colors(filecontent)
    conversion_dict = {}
    for color in found_colors:
        grayscale = hex_to_grayscale(color)
        inv_grayscale = max(0, 255 - grayscale)
        offset = 20 + int(inv_grayscale * 0.15)
        conversion_dict[color] = light_color(color, offset)

    # $ Apply conversion
    for k, v in conversion_dict.items():
        filecontent = filecontent.replace(k, v).replace(k.upper(), v)
    return filecontent


def light_color(hex_color: str, brightness_offset: int = 1) -> str:
    """Takes a color like '#87c95f' and produces a lighter or darker variant."""
    if len(hex_color) != 7:
        raise Exception(
            f"Passed {hex_color} into light_color(), needs to be in #87c95f format."
        )
    rgb_hex = [hex_color[x : x + 2] for x in [1, 3, 5]]
    new_rgb_int = [
        int(hex_value, 16) + brightness_offset for hex_value in rgb_hex
    ]
    # make sure new values are between 0 and 255
    new_rgb_int = [min([255, max([0, i])]) for i in new_rgb_int]
    # hex() produces "0x88", we want just "88"
    return "#" + "".join([hex(i)[2:] for i in new_rgb_int])


# ^                                         HELP FUNCTIONS                                         ^#
# % ============================================================================================== %#
# %                                                                                                %#


def print_intro() -> None:
    """Explain what this tool does."""
    header = (
        "\n"
        + "=" * 80
        + "\n"
        + "|"
        + " " * 28
        + "ICON RECOLORING TOOL"
        + " " * 29
        + "|"
        + "\n"
        + "=" * 80
    )
    printc(header, color="yellow")
    print(
        "This tool can fix svg-issues in the current icons and create a set of new icons \n"
        "in another folder. The tool operates on these two folders:"
    )
    printc(f"    Source folder: ".ljust(24), color="yellow")
    printc(f"    {q}{src_iconfolder}{q}")
    printc(f"    Destination folders: ".ljust(24), color="yellow")
    for color, dst in dst_iconfolders.items():
        printc(f"    {q}{dst}{q}")
    print()
    return


def print_exit() -> None:
    """"""
    printc(f"All operations completed.", color="yellow")
    print(
        f"TODO: Copy the folder {q}<resources>/spacer_light{q} to the right place!"
    )
    print(
        f"TODO: Copy the folder {q}<resources>/chevron_light{q} to the right place!"
    )
    return


def clean() -> None:
    """
    Clean the previous output folder:
      /icons_plump_color_light
    """
    printc(f"Clean previous output", color="yellow")
    printc(f"---------------------", color="yellow")
    for color, dst in dst_iconfolders.items():
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        printc(f"Folder {q}{dst}{q} has been cleaned.")
    print()
    return


def read_file(filepath: str) -> str:
    """Make sure it's an existing '.svg' file."""
    assert filepath.endswith(".svg")
    assert os.path.isfile(filepath)
    filecontent = ""
    with open(filepath, "r", encoding="utf-8", newline="\n") as f:
        filecontent = f.read()
    return filecontent


def write_file(filepath: str, filecontent: str) -> None:
    """Make sure it's a '.svg' file."""
    assert filepath.endswith(".svg")
    assert isinstance(filecontent, str)
    parent_folder = os.path.dirname(filepath)
    if not os.path.isdir(parent_folder):
        os.makedirs(parent_folder)
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(filecontent)
    return


def _help() -> None:
    """"""
    print_intro()
    printc(
        f"Use this tool to recolor the icon set.\n",
    )
    printc("\nProvide the following arguments:")
    printc("    --new       ", end="", color="yellow")
    printc("[optional] Pull the update from the testserver.")
    printc("    --halt      ", end="", color="yellow")
    printc("[optional] Stop after every step to wait for a key press.")
    printc("    --local-dir ", end="", color="yellow")
    printc("[deprecated] Point to the installation directory.")


def get_all_values(d: Dict) -> Iterator[str]:
    """Get all the values from the given dictionary, regardless of how deeply
    nested it is."""
    for k, v in d.items():
        if isinstance(v, dict):
            yield from get_all_values(v)
            continue
        yield v
        continue


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    """"""
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def hex_to_grayscale(h: str) -> int:
    """
    See https://www.baeldung.com/cs/convert-rgb-to-grayscale
    """
    rgb = hex_to_rgb(h)
    return int(
        0.3 * float(rgb[0]) + 0.59 * float(rgb[1]) + 0.11 * float(rgb[2])
    )


def find_colors(filecontent: str) -> List[str]:
    """Observe the given filecontent.

    Find all colors from the 'color_matrix'.
    """
    found_colors = []
    for color in get_all_values(color_matrix):
        if color in filecontent.lower():
            if color not in found_colors:
                found_colors.append(color)
        continue
    return found_colors


def printc(
    *args,
    color: Optional[str] = None,
    bright: bool = False,
    **kwargs,
) -> None:
    """
    :param color:   Pass a color for the text. Choose one of these:
                        - None (default color)
                        - 'default'
                        - 'black'
                        - 'red'
                        - 'green'
                        - 'yellow'
                        - 'blue'
                        - 'magenta'
                        - 'cyan'
                        - 'white'
    """
    if (color is None) or (color.lower() == "default"):
        print(*args, **kwargs)
        return

    # & Define colors
    color = color.lower()
    color_codes = {
        "default": "",
        "black": "\u001b[30m",
        "red": "\u001b[31m",
        "green": "\u001b[32m",
        "yellow": "\u001b[33m",
        "blue": "\u001b[34m",
        "magenta": "\u001b[35m",
        "cyan": "\u001b[36m",
        "white": "\u001b[37m",
        "default_bright": "",
        "black_bright": "\u001b[30;1m",
        "red_bright": "\u001b[31;1m",
        "green_bright": "\u001b[32;1m",
        "yellow_bright": "\u001b[33;1m",
        "blue_bright": "\u001b[34;1m",
        "magenta_bright": "\u001b[35;1m",
        "cyan_bright": "\u001b[36;1m",
        "white_bright": "\u001b[37;1m",
        "reset": "\u001b[0m",
    }
    assert color in color_codes.keys()

    # & Print
    if bright:
        color = f"{color}_bright"
    sep = kwargs.get("sep", " ")
    print(
        f'{color_codes[color]}{sep.join(args)}{color_codes["reset"]}',
        **kwargs,
    )
    return


# ^                                         START PROGRAM                                          ^#
# % ============================================================================================== %#
# %                                                                                                %#

if __name__ == "__main__":
    colorama.init()
    parser = argparse.ArgumentParser(
        description="Recolor icons", add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true")
    _args = parser.parse_args()
    if _args.help:
        _help()
        sys.exit(0)

    # & Start processing
    print_intro()
    clean()
    fix_svg_files()
    light_all()
    print_exit()
    sys.exit(0)
