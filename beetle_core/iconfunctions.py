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

import os
import qt
import re
import data
import functions
import traceback
import purefunctions
from typing import *
from various.kristofstuff import *

# ==================================================================================================
# |                                      IMPROVED ICON SYSTEM                                      |
# ==================================================================================================
# This module should be the central access point to obtain all QIcon()s, QPixmap()s and QImage()s in
# Embeetle. Also wherever an absolute path to an image file is required, this module should be used.
# MAIN FUNCTIONS
# ==============
# The main functions in this module return a QIcon(), QPixmap() or QImage():
# > get_qicon(icon_relpath)
# > get_qimage(img_relpath) [function removed, was unused]
# > get_qpixmap(pixmap_relpath, width, height)
# > get_richt_text_pixmap(pixmap_relpath, width, height)
# > get_rich_text_pixmap_middle(pixmap_relpath, width, height)
# The first parameter to each of these functions is the relative(!) path to a .png or .svg file,
# like this:
#     'icons/gen/home.png'
# The relative path must always start with 'icons/' or 'figures/'! This module will then select
# the right folder, depending on the active style, such as:
#     'icons_tango/'
#     'figures_tango/'
#     ...
# You can choose the '.png' or '.svg' extension - it doesn't really matter. This module is flexible
# enough to check if the corresponding image in the chosen style (eg. 'tango' style, whatever) is
# available in the '.png' or '.svg' format.
# The relative path may contain suffixes between parentheses '()', like so:
#     'icons/gen/home(add)(warn).png'
# Each suffix modifies the icon, see paragraph below.
# SUFFIX SYSTEM
# =============
# To obtain certain modifications, you can add suffixes between parentheses '()' to the relative
# paths you feed to the functions in this module. For example:
#     'icons/gen/home(warn)(dis)(hid).png'
# There are three categories of suffixes:
#     1) OVERLAYS
#     If your suffix corresponds to the name of an image in 'resources/icons/overlay/', the suffix
#     will result in the overlay image being put on top of the base image. For example: the '(warn)'
#     suffix will put the 'resources/icons/overlay/warn.png' image on top.
#     You can add overlay images to this folder as you please. You don't need to change anything in
#     the code whatsoever!
#     2) GRAYSCALE
#     The '(dis)' suffix - named after 'disable' - causes the image to be transformed into gray-
#     scale.
#     3) TRANSPARENT
#     The '(hid)' suffix - named after 'hidden' - causes the image to become transparent. This means
#     the image gets a 0.1 opacity.
# An error message will be printed if your suffix doesn't fit in any of the three categories.
# OTHER FUNCTIONS
# ===============
# > get_language_document_qicon(filepath)
#     This function should be a simple wrapper around 'get_qicon()'. However, there is still a lot
#     of processing inside the function. Could that be duplication? To be checked (please help).
# > get_language_icon_relpath(language_name)
#     Returns the relative path to an icon that represents the given language. Used in
#     customeditor.py and newfiletreehandler.py
# > get_icon_abspath(icon_relpath)
#     Returns the absolute path to an icon whose relative path is given. Used only in newfiletree.py
#     module, where the absolute path is stuffed into an html token. Perhaps it's cleaner to provide
#     a function here in the 'iconfunctions.py' module that returns the html token directly?
# ==================================================================================================
# |                                         IMAGE STORAGE                                          |
# ==================================================================================================
# All images are stored on three levels:
#     1) ORIGINAL STORAGE
#     -------------------
#     All original images are located in 'resources/icons_<style>/' and 'resources/figures_<style>/'
#     within the embeetle installation. This module will always attempt to find the image file in
#     the correct style folder. However, if the requested image file is not present, this module
#     tries a backup style (which is 'tango' at the moment).
#     2) CACHE IN .EMBEETLE FOLDER
#     ----------------------------
#     The '<user>/.embeetle/icons_<style>_cache/' and '<user>/.embeetle/figures_<style>_cache/' fol-
#     ders in the user's directory keeps a copy of all the derived images created while Embeetle
#     runs, such as images with an overlay on top, grayscales and transparent images. These "deriv-
#     ed" images are stored as '.png' or '.svg' files with suffixes in their name to identify the
#     modifications that were applied. For more info, see the SUFFIX SYSTEM paragraph near the top.
#     Note that each style has its own cache folder. This avoids any mixups.
#     3) CACHE IN RAM
#     ---------------
#     I keep several dictionaries in this module to store all the QIcon(), QImage() and QPixmap()
#     objects that were created during the course of the program:
#         - ram_qicon_cache
#         - ram_qimage_cache
#         - ram_qimage_overlay_cache
#         - ram_qpixmap_cache
#     I currently assume that Embeetle needs a restart when the icon style changes. A restart will
#     of course flush these RAM-caches.

# STORAGE
# -------
# The chosen icon style gets stored in '~/.embeetle/beetle.btl' at the end of the json-file, like
# so:
#     "icon_style": "plump_color"
# As you can see, the icon style is stored with the key(!) of the style, as represented in the dict-
# ionary below. In other words, the keys in this dictionary uniquely identify each icon style.

# CURRENT STYLE
# -------------
# The currently active style is held by 'data.icon_style'. Again, this variable can only hold the
# keys from the dictionary below.
icon_styles = {
    "plump_color": {
        "name": "plump color",  # Name for dropdown menu
        "icon_source_folder": "<resources>/icons_plump_color",
        "fig_source_folder": "<resources>/figures_plump_color",
        "icon_cache_folder": "<dot_embeetle>/icons_plump_color_cache",
        "fig_cache_folder": "<dot_embeetle>/figures_plump_color_cache",
    },
    "plump_color_light": {
        "name": "plump color light",  # Name for dropdown menu
        "icon_source_folder": "<resources>/icons_plump_color_light",
        "fig_source_folder": "<resources>/figures_plump_color_light",
        "icon_cache_folder": "<dot_embeetle>/icons_plump_color_light_cache",
        "fig_cache_folder": "<dot_embeetle>/figures_plump_color_light_cache",
    },
}


def check_default_style(funcname: str) -> None:
    """This is a help function to print an error message in case the default
    style is undefined and reset it."""
    if (data.icon_style is not None) and (
        data.icon_style in icon_styles.keys()
    ):
        return
    #    purefunctions.printc(
    #        f'ERROR: {funcname}() running with data.icon_style={q}{data.icon_style}{q}\n'
    #        f'Fall back to {q}plump_color{q}\n'
    #    )
    data.icon_style = "plump_color"
    return


def check_style(funcname: str, style: str) -> str:
    """This is a help function to print an error message in case the given style
    is undefined and reset it."""
    if (style is not None) and (style in icon_styles.keys()):
        return style
    #    purefunctions.printc(
    #        f'ERROR: {funcname}() running with style={q}{style}{q}\n'
    #        f'Fall back to {q}plump_color{q}\n'
    #    )
    return "plump_color"


def change_style(style: str) -> None:
    """
    Set the icon style: 'plump_color' or 'plump_color_light'.
    """
    style = check_style("change_style", style)
    data.icon_style = style
    global ram_qicon_cache
    ram_qicon_cache = {}
    global ram_qimage_cache
    ram_qimage_cache = {}
    global ram_qpixmap_cache
    ram_qpixmap_cache = {}
    global ram_qimage_overlay_cache
    ram_qimage_overlay_cache = {}


def update_style() -> None:
    if data.theme["is_dark"]:
        change_style("plump_color_light")
    else:
        change_style("plump_color")


# STYLE NAMES
# -----------
# The style names, as seen in the dictionary above, are only used to fill the dropdown menus. They
# won't ever be used to refer to a specific style, anywhere. The functions Matic added at the bottom
# of this file, enable him to:
#     - List all the names, to fill the dropdown.
#     - Obtain the corresponding key after a user has chosen a dropdown entry.
# The obtained key (like 'plump_color') is then stored in '~/.embeetle/beetle.btl' and in
# 'data.icon_style'.


def get_backup_style() -> str:
    """Get the backup style."""
    check_default_style("get_backup_style")
    if data.icon_style == "plump_color":
        return "plump_color_light"
    return "plump_color"


allowed_extensions = (".png", ".svg", ".gif", ".ico")

language_icons = {
    "beetle": "icons/logo/embeetle.png",
    "python": "icons/languages/python.png",
    "linkerscript": "icons/file/file_ld.png",
    "cython": "icons/languages/cython.png",
    "c": "icons/languages/c.png",
    "h": "icons/languages/c.png",
    "c++": "icons/languages/c.png",
    "h++": "icons/languages/cpp.png",
    "c / c++": "icons/languages/cpp.png",
    "cmake": "icons/languages/cmake.png",
    "oberon/modula": "icons/languages/oberon.png",
    "d": "icons/languages/d.png",
    "nim": "icons/languages/nim.png",
    "ada": "icons/languages/ada.png",
    "css": "icons/languages/css.png",
    "html": "icons/languages/html.png",
    "json": "icons/languages/json.png",
    "lua": "icons/languages/lua.png",
    "matlab": "icons/languages/matlab.png",
    "perl": "icons/languages/perl.png",
    "ruby": "icons/languages/ruby.png",
    "tcl": "icons/languages/tcl.png",
    "tex": "icons/languages/tex.png",
    "idl": "icons/languages/idl.png",
    "bash": "icons/languages/bash.png",
    "batch": "icons/languages/batch.png",
    "fortran": "icons/languages/fortran.png",
    "fortran77": "icons/languages/fortran77.png",
    "ini": "icons/languages/makefile.png",
    "makefile": "icons/languages/makefile.png",
    "coffeescript": "icons/languages/coffeescript.png",
    "c#": "icons/languages/csharp.png",
    "java": "icons/languages/java.png",
    "javascript": "icons/languages/javascript.png",
    "pascal": "icons/languages/pascal.png",
    "routeros": "icons/languages/routeros.png",
    "sql": "icons/languages/sql.png",
    "verilog": "icons/languages/verilog.png",
    "vhdl": "icons/languages/vhdl.png",
    "xml": "icons/languages/xml.png",
    "yaml": "icons/languages/yaml.png",
    "text": "icons/file/file.png",
}

complete_file_images = {
    "c": f"icons/file/file_c.png",
    "c++": f"icons/file/file_cpp.png",
    "d": f"icons/file/file_d.png",
    "h": f"icons/file/file_h.png",
    "h++": f"icons/file/file_hpp.png",
    "json": f"icons/file/file_json.png",
    "o": f"icons/file/file_o.png",
    "makefile": f"icons/file/file_mk.png",
    "bin": f"icons/file/file_bin.png",
    "elf": f"icons/file/file_elf.png",
}

# RAM CACHES
ram_qicon_cache: Dict[str, qt.QIcon] = {}
ram_qimage_cache: Dict[str, qt.QImage] = {}
ram_qimage_overlay_cache: Dict[str, qt.QImage] = {}
ram_qpixmap_cache: Dict[str, qt.QPixmap] = {}

# ^                                            QICON()                                             ^#
# % ============================================================================================== %#
# % Functions returning a QIcon()                                                                  %#
# %                                                                                                %#


def get_qicon(icon_relpath: str) -> qt.QIcon:
    """Create and cache a QIcon()-instance for the given relative icon path.

    :param icon_relpath: The relative path to the image file, potentially with suffixes,
                         eg: 'icons/gen/home.png'
                         eg: 'icons/gen/home(add).png'

    :return: QIcon()
    """
    check_default_style("get_qicon")
    # & 1. Process inputs
    __check_icon_or_fig_relpath(icon_relpath)
    stripped_icon_relpath, suffixed_icon_relpath, extracted_suffixes = (
        __format_suffixes(icon_relpath)
    )

    # & 2. Look in RAM cache
    if suffixed_icon_relpath in ram_qicon_cache:
        return ram_qicon_cache[suffixed_icon_relpath]

    # & 3. Look on harddrive
    abspath = __find_or_create_icon_on_hdd(
        stripped_icon_relpath=stripped_icon_relpath,
        suffixed_icon_relpath=suffixed_icon_relpath,
        ordered_suffixes=extracted_suffixes,
    )
    assert os.path.isfile(abspath)

    # & 4. Create and cache QIcon()
    qpixmap = qt.QPixmap(abspath)
    icon = qt.QIcon(
        qpixmap.scaled(
            128,
            128,
            qt.Qt.AspectRatioMode.KeepAspectRatio,
            qt.Qt.TransformationMode.SmoothTransformation,
        )
    )
    ram_qicon_cache[suffixed_icon_relpath] = icon
    return icon


def get_language_document_qicon(filepath: str) -> qt.QIcon:
    """Same as function 'get_language_icon_relpath()', with two differences:

    - Provide the whole document image (as shown in the Filetree) instead.
    - Return a QIcon().
    """
    check_default_style("get_language_document_qicon")
    filetype = functions.get_file_type(filepath)
    if filetype in complete_file_images:
        return get_qicon(complete_file_images[filetype])
    lang_qicon: qt.QIcon = get_qicon(get_language_icon_relpath(filetype))
    if filetype == "text":
        return lang_qicon
    document_qimage = qt.QImage(
        get_icon_abspath(
            icon_relpath="icons/file/file.png",
            create_if_needed=False,
        )
    )
    icon_size_on_image = document_qimage.size() / 1.4
    qpixmap = lang_qicon.pixmap(lang_qicon.actualSize(icon_size_on_image))

    qimage = qt.QImage(
        document_qimage.size(), qt.QImage.Format.Format_ARGB32_Premultiplied
    )
    qimage.fill(qt.Qt.GlobalColor.transparent)
    painter = qt.QPainter(qimage)
    painter.setRenderHints(
        qt.QPainter.RenderHint.Antialiasing
        | qt.QPainter.RenderHint.TextAntialiasing
        | qt.QPainter.RenderHint.SmoothPixmapTransform
    )
    painter.drawImage(
        qt.QRect(0, 0, qimage.width(), qimage.height()), document_qimage
    )
    painter.drawImage(
        qt.QRect(0, 0, icon_size_on_image.width(), icon_size_on_image.height()),
        qpixmap.toImage(),
    )
    painter.end()
    qpixmap = qt.QPixmap.fromImage(qimage)
    return qt.QIcon(qpixmap)


# ^                                            QIMAGE()                                            ^#
# % ============================================================================================== %#
# % Functions returning a QImage()                                                                 %#
# %                                                                                                %#


def __fill_ram_qimage_overlay_cache() -> None:
    """Fill the 'ram_qimage_overlay_cache' dictionary with QImage()s."""
    check_default_style("__fill_ram_qimage_overlay_cache")
    assert len(ram_qimage_overlay_cache.keys()) == 0

    def fill_for_style(stylename: str) -> None:
        # & Fill the ram cache with overlays from the given style
        overlay_folderpath = f"{__get_icon_source_folder(stylename)}/overlay"
        if not os.path.isdir(overlay_folderpath):
            return
        for filename in os.listdir(overlay_folderpath):
            assert "/" not in filename
            if not (filename.endswith(allowed_extensions)):
                continue
            filepath = f"{overlay_folderpath}/{filename}"
            assert os.path.isfile(filepath)
            suffix = __remove_extension(filename)
            if suffix in ram_qimage_overlay_cache.keys():
                # A previous round of this subfunction already filled the cache with this overlay
                # image.
                pass
            else:
                ram_qimage_overlay_cache[suffix] = qt.QImage(filepath)
            assert not ram_qimage_overlay_cache[suffix].isNull()
            continue
        return

    # First fill the RAM-cache with overlay images pulled from the active icon style. Then add over-
    # lay images from the backup icon style if there are some missing.
    fill_for_style(data.icon_style)
    fill_for_style(get_backup_style())
    assert len(ram_qimage_overlay_cache.keys()) > 0
    return


# ^                                           QPIXMAP()                                            ^#
# % ============================================================================================== %#
# % Functions returning a QPixmap()                                                                %#
# %                                                                                                %#


def get_qpixmap(
    pixmap_relpath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> qt.QPixmap:
    """Create and cache a QPixmap()-instance for the given relative path.

    :param pixmap_relpath: The relative path to the image file, potentially with suffixes,
                           eg: 'icons/gen/home.png'
                           eg: 'icons/gen/home(add).png'

    :param width:          [Optional] Width for the returned qt.QPixmap().

    :param height:         [Optional] Height for the returned qt.QPixmap().

    :return: QPixmap()
    """
    check_default_style("get_qpixmap")

    # & 1. Process inputs
    __check_icon_or_fig_relpath(pixmap_relpath)
    stripped_pixmap_relpath, suffixed_pixmap_relpath, extracted_suffixes = (
        __format_suffixes(pixmap_relpath)
    )

    # & 2. Look in RAM cache
    if suffixed_pixmap_relpath in ram_qpixmap_cache.keys():
        qpixmap = ram_qpixmap_cache[suffixed_pixmap_relpath]
        if width:
            qpixmap = qpixmap.scaledToWidth(
                int(width),
                qt.Qt.TransformationMode.SmoothTransformation,
            )
        if height:
            qpixmap = qpixmap.scaledToHeight(
                int(height),
                qt.Qt.TransformationMode.SmoothTransformation,
            )
        return qpixmap

    # & 3. Look on harddrive
    abspath = __find_or_create_icon_on_hdd(
        stripped_icon_relpath=stripped_pixmap_relpath,
        suffixed_icon_relpath=suffixed_pixmap_relpath,
        ordered_suffixes=extracted_suffixes,
    )
    assert os.path.isfile(abspath)

    # & 4. Create and cache QPixmap()
    qpixmap = qt.QPixmap(abspath)
    ram_qpixmap_cache[suffixed_pixmap_relpath] = qpixmap
    if width:
        qpixmap = qpixmap.scaledToWidth(
            int(width),
            qt.Qt.TransformationMode.SmoothTransformation,
        )
    if height:
        qpixmap = qpixmap.scaledToHeight(
            int(height),
            qt.Qt.TransformationMode.SmoothTransformation,
        )
    return qpixmap


def __qpixmap_to_overlayed_qpixmap(
    qpixmap: qt.QPixmap,
    suffix: str,
) -> Optional[qt.QPixmap]:
    """Put an overlay on the given QPixmap() and return it as another
    QPixmap()."""
    check_default_style("__qpixmap_to_overlayed_qpixmap")
    if len(ram_qimage_overlay_cache.keys()) == 0:
        __fill_ram_qimage_overlay_cache()
    overlay_qimage: Optional[qt.QImage] = ram_qimage_overlay_cache.get(suffix)
    if overlay_qimage is None:
        purefunctions.printc(
            f"\nERROR: Suffix {q}({suffix}){q} is not present in the {q}icons/overlay/{q} "
            f"folder!\n",
            color="error",
        )
        return None
    assert not overlay_qimage.isNull()
    scaled_overlay_qimage: Optional[qt.QImage] = None
    qimage = qt.QImage(qpixmap)
    if (
        overlay_qimage.size().width() != qimage.size().width()
        or overlay_qimage.size().height() != qimage.size().height()
    ):
        purefunctions.printc(
            f"\nERROR: The overlay image corresponding to the {q}({suffix}){q} suffix has "
            f"not the right dimensions:\n"
            f"    - width: {overlay_qimage.size().width()}\n"
            f"    - height: {overlay_qimage.size().height()}\n",
            color="error",
        )
        return None
    painter = data.painter
    painter.begin(qimage)
    if scaled_overlay_qimage is not None:
        painter.drawImage(0, 0, scaled_overlay_qimage)
    else:
        painter.drawImage(0, 0, overlay_qimage)
    painter.end()
    return qt.QPixmap.fromImage(qimage)


def __qpixmap_to_grayscale_qpixmap(qpixmap: qt.QPixmap) -> qt.QPixmap:
    """Gray out a QPixmap() and return it as another QPixmap()."""
    check_default_style("__qpixmap_to_grayscale_qpixmap")
    qimage = qt.QImage(qpixmap)
    for i in range(qimage.width()):
        for j in range(qimage.height()):
            point = qt.create_qpoint(i, j)
            color = qt.QColor(qimage.pixelColor(point))
            if color.alpha() > 100:
                color.setHsl(color.hue(), 10, color.lightness())
                qimage.setPixelColor(point, color)
    return qt.QPixmap.fromImage(qimage)


def __qpixmap_to_transparent_qpixmap(qpixmap: qt.QPixmap) -> qt.QPixmap:
    """Duplicate the given QPixmap() and make it transparent."""
    check_default_style("__qpixmap_to_transparent_qpixmap")
    base_qimage = qt.QImage(qpixmap)
    qimage = qt.QImage(
        base_qimage.size(), qt.QImage.Format.Format_ARGB32_Premultiplied
    )
    qimage.fill(qt.Qt.GlobalColor.transparent)
    painter = qt.QPainter(qimage)
    painter.setRenderHints(
        qt.QPainter.RenderHint.Antialiasing
        | qt.QPainter.RenderHint.TextAntialiasing
        | qt.QPainter.RenderHint.SmoothPixmapTransform
    )
    # Apply a number between 0.0 and 1.0 with 0.0 being completely transparent and 1.0 completely
    # opaque.
    painter.setOpacity(0.1)
    painter.drawImage(
        qt.QRect(0, 0, qimage.width(), qimage.height()), base_qimage
    )
    painter.end()
    return qt.QPixmap.fromImage(qimage)


# ^                                       RICH TEXT PIXMAP                                         ^#
# % ============================================================================================== %#
# % Functions returning a rich text pixmap string                                                  %#
# %                                                                                                %#


def get_rich_text_pixmap(
    pixmap_relpath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Create a pixmap, but in the form of a string.

    :param pixmap_relpath: The relative path to the image file, potentially with suffixes,
                           eg: 'icons/gen/home.png'
                           eg: 'icons/gen/home(add).png'

    :param width:          [Optional] Width for the returned pixmap.

    :param height:         [Optional] Height for the returned pixmap.
    """
    check_default_style("get_rich_text_pixmap")
    qpixmap = get_qpixmap(pixmap_relpath, width, height)
    byteArray = qt.QByteArray()
    buffer = qt.QBuffer(byteArray)
    qpixmap.save(buffer, "PNG")
    return f'<img src="data:image/png;base64,{str(byteArray.toBase64())[2 : -1]}"/>'


def get_rich_text_pixmap_middle(
    pixmap_relpath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Same as previous function, but put try to put the pixmap in the middle of
    a text-line.

    :param pixmap_relpath: The relative path to the image file, potentially with suffixes,
                           eg: 'icons/gen/home.png'
                           eg: 'icons/gen/home(add).png'

    :param width:          [Optional] Width for the returned pixmap.

    :param height:         [Optional] Height for the returned pixmap.
    """
    check_default_style("get_rich_text_pixmap_middle")
    qpixmap = get_qpixmap(pixmap_relpath, width, height)
    byteArray = qt.QByteArray()
    buffer = qt.QBuffer(byteArray)
    qpixmap.save(buffer, "PNG")
    return f'<img src="data:image/png;base64,{str(byteArray.toBase64())[2 : -1]}" align="top"/>'


# ^                                       ACCESS IMAGE PATHS                                       ^#
# % ============================================================================================== %#
# % These functions give access to the absolute paths of image files. You can use them, although   %#
# % it's better to use the functions above that return a QIcon(), QImage() or QPixmap()-instance   %#
# % directly, where you can benefit from the caching system.                                       %#
# %                                                                                                %#


def get_icon_abspath(
    icon_relpath: str,
    create_if_needed: bool = True,
    skip_style_check: bool = False,
) -> str:
    """Obtain the absolute path to the given icon. If there are no suffixes, the
    icon is simply looked after in the 'resources/icons_<style>/' folder.
    Otherwise, the modified icon is looked after in the cache folder at
    '<user>/.embeetle/icons_<style>_cache/'.

    :param icon_relpath:     The relative path to the image file, potentially with suffixes,
                             eg: 'icons/gen/home.png'
                             eg: 'icons/gen/home(add).png'

    :param create_if_needed: Only relevant if the previous parameter contains suffixes. In that
                             case, the icon file is looked after in the '<user>/.embeetle/icons_
                             <style>_cache/' directory. If the icon is not found, this 'create_
                             if_needed' parameter becomes relevant:
                                True:  Create the file and return the abspath to it.
                                False: Don't create the file, but still return the abspath to where
                                       it would be located.
    """
    if skip_style_check:
        pass
    else:
        check_default_style("get_icon_abspath")

    # * Without suffixes
    if "(" not in icon_relpath:
        if icon_relpath.startswith("icons/"):
            icon_abspath = f"{__get_icon_source_folder(skip_style_check=skip_style_check)}/{icon_relpath[6:]}"
        elif icon_relpath.startswith("figures/"):
            icon_abspath = f"{__get_fig_source_folder(skip_style_check=skip_style_check)}/{icon_relpath[8:]}"
        else:
            assert False
        icon_abspath = __get_abspath_with_correct_extension(
            icon_abspath, icon_abspath, skip_style_check=skip_style_check
        )
        if not os.path.isfile(icon_abspath):
            if icon_relpath.startswith("icons/"):
                icon_abspath = f"{__get_icon_source_folder(get_backup_style(), skip_style_check=skip_style_check)}/{icon_relpath[6:]}"
            elif icon_relpath.startswith("figures/"):
                icon_abspath = f"{__get_fig_source_folder(get_backup_style(), skip_style_check=skip_style_check)}/{icon_relpath[8:]}"
            else:
                assert False
            icon_abspath = __get_abspath_with_correct_extension(
                icon_abspath, icon_abspath, skip_style_check=skip_style_check
            )
        return icon_abspath

    # * With suffixes
    assert "(" in icon_relpath
    stripped_icon_relpath, suffixed_icon_relpath, ordered_suffixes = (
        __format_suffixes(icon_relpath)
    )
    abspath = __find_or_create_icon_on_hdd(
        stripped_icon_relpath=stripped_icon_relpath,
        suffixed_icon_relpath=suffixed_icon_relpath,
        ordered_suffixes=ordered_suffixes,
        create_if_needed=create_if_needed,
    )
    if create_if_needed:
        assert os.path.isfile(abspath)
    return abspath


def icon_exists(icon_relpath: str) -> bool:
    """Check if the given icon exists.

    The absolute path to the icon in the data.icon_style is computed first. If
    there's no file at that location, the absolute path to the icon in the
    BACKUP_STYLE is used instead. If there's still no file at that location,
    this function returns False.
    """
    check_default_style("icon_exists")
    icon_abspath = get_icon_abspath(
        icon_relpath=icon_relpath,
        create_if_needed=False,
    )
    return os.path.isfile(icon_abspath)


def get_icon_source_folder(style: Optional[str] = None) -> str:
    """Direct manipulations with the icon source folder folder must be avoided
    outside this central 'iconfunctions.py' module. Therefore, this function
    must only be called in exceptional situa- tions!

    :return: The icon source folder for the currently active style, eg.
        'C:/embeetle/beetle_core/resources/icons_tango'
    """
    if style is None:
        style = data.icon_style
    style = check_style("get_icon_source_folder", style)
    return __get_icon_source_folder(style)


# ^                                         HELP FUNCTIONS                                         ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


def color_change_brightness(color_str: str, amount: int) -> str:
    """
    :param color_str:   string representing color, eg. '#fff57900'
    :param amount:      amount by which to change the brightness

    :return:    string representing resulting color
    """
    check_default_style("color_change_brightness")
    c = qt.QColor(color_str)
    h, s, v, a = c.getHsv()
    v = 255 if v + 30 > 255 else v + 30
    c.setHsv(h, s, v, a)
    return c.name(qt.QColor.NameFormat.HexArgb)


def get_language_icon_relpath(language_name: str) -> str:
    """Get the relpath to the programming language icon for the given
    language."""
    check_default_style("get_language_icon_relpath")
    language_name = language_name.lower()
    # Determine iconpath
    if language_name in complete_file_images.keys():
        iconpath = complete_file_images[language_name]
    elif language_name in language_icons.keys():
        iconpath = language_icons[language_name]
    else:
        iconpath = language_icons["text"]
    return iconpath


def __get_icon_source_folder(
    style: Optional[str] = None, skip_style_check: bool = False
) -> str:
    """Get the full absolute path to the source folder with icons, like:

    'C:/embeetle/beetle_core/resources/icons_tango'
    """
    if skip_style_check:
        style = "plump_color"
    else:
        if style is None:
            style = data.icon_style
        style = check_style("__get_icon_source_folder", style)
    return icon_styles[style]["icon_source_folder"].replace(
        "<resources>",
        data.resources_directory,
    )


def __get_fig_source_folder(
    style: Optional[str] = None, skip_style_check=False
) -> str:
    """Get the full absolute path to the source folder with figures, like:

    'C:/embeetle/beetle_core/resources/figures_tango'
    """
    if skip_style_check:
        style = "plump_color"
    else:
        if style is None:
            style = data.icon_style
        style = check_style("__get_fig_source_folder", style)
    return icon_styles[style]["fig_source_folder"].replace(
        "<resources>",
        data.resources_directory,
    )


def __get_icon_cache_folder(style: Optional[str] = None) -> str:
    """Get the full absolute path to the cache folder with derived (suffixed)
    icons, like:

    'C:/Users/krist/.embeetle/icons_tango_cache'
    """
    if style is None:
        style = data.icon_style
    style = check_style("__get_icon_cache_folder", style)
    return icon_styles[style]["icon_cache_folder"].replace(
        "<dot_embeetle>",
        data.settings_directory,
    )


def __get_fig_cache_folder(style: Optional[str] = None) -> str:
    """Get the full absolute path to the cache folder with derived (suffixed)
    figures, like:

    'C:/Users/krist/.embeetle/figures_tango_cache'
    """
    if style is None:
        style = data.icon_style
    style = check_style("__get_fig_cache_folder", style)
    return icon_styles[style]["fig_cache_folder"].replace(
        "<dot_embeetle>",
        data.settings_directory,
    )


def __check_icon_or_fig_relpath(relpath: str) -> None:
    """Each relative icon or figure path must start with 'icons/' or 'figures/'
    and end in '.png' or '.svg'."""
    check_default_style("__check_icon_or_fig_relpath")
    if relpath.startswith(
        ("icons/", "figures/", "icons_static/")
    ) and relpath.endswith(allowed_extensions):
        pass
    else:
        msg = str(
            f"\nERROR:\n"
            f"An invalid icon path was passed to the {q}iconfunctions.py{q} module:\n"
            f"{q}{relpath}{q}\n"
            f"Icon paths passed to this module must be relative and end in {allowed_extensions}:\n"
            f"{q}icons/gen/home.png{q}\n"
            f"The paths may contain suffixes between parenthesis, like:\n"
            f"{q}icons/gen/home(add).png{q}\n"
        )
        traceback.print_exc()
        purefunctions.printc(msg, color="error")
        # raise RuntimeError(msg)
    return


def __check_overlay_suffix(suffix: str) -> bool:
    """Return True if the given suffix corresponds to an overlay image."""
    check_default_style("__check_overlay_suffix")
    if len(ram_qimage_overlay_cache.keys()) == 0:
        __fill_ram_qimage_overlay_cache()
    if suffix in ram_qimage_overlay_cache.keys():
        return True
    if suffix in ("hid", "dis"):
        return True
    purefunctions.printc(
        f"\nERROR: Icon suffix {q}({suffix}){q} is not valid.\n",
        color="error",
    )
    return False


def __format_suffixes(
    icon_relpath: str,
) -> Tuple[str, str, Optional[List[str]]]:
    """Observe the given 'icon_relpath' (eg. 'icons/gen/home.png'). First clean
    it from any suffixes. Then apply all the suffixes again in a predetermined
    way. Finally, return a tuple: ( stripped_icon_relpath,
    suffixed_icon_relpath,

            ordered_suffixes,
        )

    :param icon_relpath:     The relative path to the icon, potentially with suffixes,
                             eg: 'icons/gen/home.png'
                             eg: 'icons/gen/home(add).png'

    :return:
            > stripped_icon_relpath: [str] The given icon_relpath devoid of all suffixes,
                                     eg. 'icons/board/arduino_nano.png'

            > suffixed_icon_relpath: [str] The given icon_relpath with all suffixes applied,
                                     eg. 'icons/board/arduino_nano(warn)(dis).png'

            > ordered_suffixes:  Optional[List[str]] A list of suffixes extracted from the given
                                 'icon_relpath' parameter, eg. ['warn', 'err', 'dis', 'hid']
    """
    # * Without suffixes
    if "(" not in icon_relpath:
        return icon_relpath, icon_relpath, None

    # * With suffixes
    stripped_icon_relpath: Optional[str] = None  # eg. 'icons/chip/chip.png'
    suffixed_icon_relpath: Optional[str] = (
        None  # eg. 'icons/chip/chip(warn)(dis).png'
    )
    extracted_suffixes: List[str] = []

    # & 1. Collect and strip off all suffixes
    p = re.compile(r"\(([\d\w]*)\)")

    # Collect all suffixes
    for m in p.finditer(icon_relpath):
        suffix = m.group(1)
        if not __check_overlay_suffix(suffix):
            # Error msg printed in the check function
            continue
        extracted_suffixes.append(suffix)
        continue
    assert len(extracted_suffixes) > 0

    # Strip off all suffixes
    stripped_icon_relpath = p.sub("", icon_relpath)

    # & 2. Re-apply and order suffixes
    # Order suffixes alphabetically and remove duplicates
    extracted_suffixes = sorted(set(extracted_suffixes))

    # Re-apply suffixes
    suffixed_icon_relpath = stripped_icon_relpath
    for s in extracted_suffixes:
        for e in allowed_extensions:
            suffixed_icon_relpath = suffixed_icon_relpath.replace(
                e, f"({s}){e}"
            )
            continue
        continue
    return stripped_icon_relpath, suffixed_icon_relpath, extracted_suffixes


def __find_or_create_icon_on_hdd(
    stripped_icon_relpath: str,
    suffixed_icon_relpath: str,
    ordered_suffixes: Optional[List[str]],
    create_if_needed: bool = True,
) -> str:
    """WITHOUT SUFFIXES ================ If it's an icon without suffixes, this
    function merely returns the abspath to the basic icon, eg.
    'C:/.../embeetle/beetle_core/resources/icons/gen/home.png'.

    WITH SUFFIXES
    =============
    If it's a derived (suffixed) icon, this function looks in the '.embeetle/icon_cache/' folder for
    the corresponding file. If not found, or if it's too old, it gets created on the fly and its
    abspath is returned,
    eg. 'C:/Users/krist/.embeetle/icon_cache/gen/home(add).png'

    :param stripped_icon_relpath: Relative path to the basic icon,
                                  eg. 'icons/gen/home.png'

    :param suffixed_icon_relpath: Relative path to the suffixed icon,
                                  eg. 'icons/gen/home(add).png'

    :param ordered_suffixes: Ordered list of suffixes, as applied on 'suffixed_icon_relpath',
                             eg. ['add', 'warn', 'dis']

    :return: Absolute path to the basic icon or to the derived (suffixed) icon in the '.embeetle/
             icon_cache/' folder.
    """
    # The given iconpaths must NOT be absolute!
    __check_icon_or_fig_relpath(stripped_icon_relpath)
    __check_icon_or_fig_relpath(suffixed_icon_relpath)

    # Absolute path to stripped icon
    if stripped_icon_relpath.startswith("icons/"):
        stripped_icon_abspath = (
            f"{__get_icon_source_folder()}/{stripped_icon_relpath[6:]}"
        )
    elif stripped_icon_relpath.startswith("figures/"):
        stripped_icon_abspath = (
            f"{__get_fig_source_folder()}/{stripped_icon_relpath[8:]}"
        )
    elif stripped_icon_relpath.startswith("icons_static/"):
        stripped_icon_abspath = (
            f"{data.resources_directory}/{stripped_icon_relpath}"
        )
    else:
        # Use a fallback icon
        purefunctions.printc(
            f"ERROR: Cannot find icon: {q}{stripped_icon_relpath}{q}\n",
            color="error",
        )
        stripped_icon_relpath = "icons/checkbox/question.svg"
        suffixed_icon_relpath = "icons/checkbox/question.svg"
        ordered_suffixes = None
        stripped_icon_abspath = (
            f"{__get_icon_source_folder()}/{stripped_icon_relpath[6:]}"
        )
        # assert False

    stripped_icon_abspath = __get_abspath_with_correct_extension(
        stripped_icon_abspath
    )
    if (stripped_icon_abspath is None) or (
        not os.path.isfile(stripped_icon_abspath)
    ):
        if stripped_icon_relpath.startswith("icons/"):
            stripped_icon_abspath = f"{__get_icon_source_folder(get_backup_style())}/{stripped_icon_relpath[6:]}"
        elif stripped_icon_relpath.startswith("figures/"):
            stripped_icon_abspath = f"{__get_fig_source_folder(get_backup_style())}/{stripped_icon_relpath[8:]}"
        else:
            # Use a fallback icon
            purefunctions.printc(
                f"ERROR: Cannot find icon: {q}{stripped_icon_abspath}{q}\n",
                color="error",
            )
            stripped_icon_relpath = "icons/checkbox/question.svg"
            stripped_icon_abspath = f"{__get_icon_source_folder(get_backup_style())}/{stripped_icon_relpath[6:]}"
            # assert False
        stripped_icon_abspath = __get_abspath_with_correct_extension(
            stripped_icon_abspath
        )

    # At this point, the icon MUST be found on the harddrive (if not the original icon, then at
    # least the fallback one).
    if (stripped_icon_abspath is None) or (
        not os.path.isfile(stripped_icon_abspath)
    ):
        purefunctions.printc(
            f"ERROR: Cannot find fallback icon: {q}{stripped_icon_relpath}{q}\n",
            color="error",
        )
        stripped_icon_relpath = "icons/checkbox/question.svg"
        suffixed_icon_relpath = "icons/checkbox/question.svg"
        ordered_suffixes = None
        stripped_icon_abspath = (
            f"{__get_icon_source_folder()}/{stripped_icon_relpath[6:]}"
        )

    # * WITHOUT SUFFIXES
    # Without suffixes, simply return the absolute path to the basic icon.
    if stripped_icon_relpath == suffixed_icon_relpath:
        assert (ordered_suffixes is None) or (len(ordered_suffixes) == 0)
    if (ordered_suffixes is None) or (len(ordered_suffixes) == 0):
        assert stripped_icon_relpath == suffixed_icon_relpath
        return stripped_icon_abspath

    # * WITH SUFFIXES
    # With suffixes, check if an icon file exists in the cache folder. If it doesn't exist yet, or
    # it is too old, create a new one. Then return the abspath to that icon.
    assert stripped_icon_relpath != suffixed_icon_relpath
    assert len(ordered_suffixes) > 0

    # Absolute path to derived icon
    if suffixed_icon_relpath.startswith("icons/"):
        suffixed_icon_abspath = (
            f"{__get_icon_cache_folder()}/{suffixed_icon_relpath[6:]}"
        )
    elif suffixed_icon_relpath.startswith("figures/"):
        suffixed_icon_abspath = (
            f"{__get_fig_cache_folder()}/{suffixed_icon_relpath[8:]}"
        )
    else:
        assert False

    # & Create suffixed file if it doesn't exist
    # If the suffixed file doesn't exist yet, create it. If it exists but it's deprecated, delete
    # and recreate it.

    # $ Suffixed file exists
    try:
        if os.path.isfile(suffixed_icon_abspath):
            original_filetime = os.path.getmtime(stripped_icon_abspath)
            suffixed_filetime = os.path.getmtime(suffixed_icon_abspath)
            # Compare original filetime with suffixed filetime
            if suffixed_filetime < original_filetime:
                # Remove the file such that next code block will execute
                os.remove(suffixed_icon_abspath)
            # Also compare original filetime with overlay image filetime
            else:
                if ordered_suffixes is not None:
                    for s in ordered_suffixes:
                        if s in ("dis", "hid"):
                            # Skip
                            continue
                        overlay_filepath = (
                            f"{__get_icon_source_folder()}/overlay/{s}.svg"
                        )
                        if not os.path.isfile(overlay_filepath):
                            overlay_filepath = f"{__get_icon_source_folder(get_backup_style())}/overlay/{s}.svg"
                        if not os.path.isfile(overlay_filepath):
                            purefunctions.printc(
                                f"ERROR: Cannot find icon overlay: {q}{overlay_filepath}{q}\n",
                                color="error",
                            )
                            continue
                        assert os.path.isfile(overlay_filepath)
                        overlay_filetime = os.path.getmtime(overlay_filepath)
                        if suffixed_filetime < overlay_filetime:
                            # Remove the file such that next code block will execute
                            if os.path.isfile(suffixed_icon_abspath):
                                os.remove(suffixed_icon_abspath)
                        continue
    except:
        traceback.print_exc()

    # $ Suffixed file didn't exist or was removed
    if create_if_needed and (not os.path.isfile(suffixed_icon_abspath)):
        # Create a QPixmap() from the base icon
        qpixmap = qt.QPixmap.fromImage(qt.QImage(stripped_icon_abspath))

        # Apply all overlays first
        for s in ordered_suffixes:
            if s in ("dis", "hid"):
                # Skip for now
                continue
            temp = __qpixmap_to_overlayed_qpixmap(qpixmap, s)
            if temp is not None:
                qpixmap = temp
            continue

        # Apply grayscale
        if "dis" in ordered_suffixes:
            temp = __qpixmap_to_grayscale_qpixmap(qpixmap)
            if temp is not None:
                qpixmap = temp

        # Apply transparency
        if "hid" in ordered_suffixes:
            temp = __qpixmap_to_transparent_qpixmap(qpixmap)
            if temp is not None:
                qpixmap = temp

        # Save the QPixmap()
        suffixed_abspath_folder = os.path.dirname(
            suffixed_icon_abspath
        ).replace("\\", "/")
        if not os.path.isdir(suffixed_abspath_folder):
            os.makedirs(suffixed_abspath_folder)
        qpixmap.save(suffixed_icon_abspath)

    # At this point, the suffixed file surely exists on the harddrive in the cache folder.
    if create_if_needed:
        assert os.path.isfile(suffixed_icon_abspath)
    return suffixed_icon_abspath


def __get_abspath_with_correct_extension(
    icon_abspath: str,
    value_if_not_found: Optional[str] = None,
    skip_style_check: bool = False,
) -> Optional[str]:
    """Return the icon abspath with the correct extension (eg.

    '.svg', '.png' or '.gif'). If none of these exists on the harddrive at the
    requested location, return whatever was given to the 'value_if_not_found'
    parameter.
    """
    if skip_style_check:
        pass
    else:
        check_default_style("__get_abspath_with_correct_extension")
    if os.path.isfile(icon_abspath):
        return icon_abspath
    p = re.compile(r"\.\w+$")
    for e in allowed_extensions:
        abspath = p.sub(e, icon_abspath)
        if os.path.isfile(abspath):
            return abspath
        continue
    return value_if_not_found


def __remove_extension(filename_or_path: str) -> str:
    """"""
    check_default_style("__remove_extension")
    p = re.compile(r"\.\w+$")
    return p.sub("", filename_or_path)


#######################
## General functions ##
#######################


def get_all_styles() -> Tuple[str]:
    """Get all the icon style names the way they are stored in the 'icon_styles'
    dictionary.

    For
    example:
    icon_styles = {
        'plump_color'  : {'name': 'plump color',  'icon_source_folder': ... },
        'plump_blue'   : {'name': 'plump blue',   'icon_source_folder': ... },
        'plump_yellow' : {'name': 'plump yellow', 'icon_source_folder': ... },
        'plump_green'  : {'name': 'plump green',  'icon_source_folder': ... },
    }
    :return: ('plump color', 'plump blue', 'plump yellow', 'plump green', )
    """
    return tuple(v["name"] for k, v in icon_styles.items())


def get_style_value_by_name(name: str) -> str:
    """For the given style name, return the key in the 'icon_styles' dictionary.
    For example:

    'plump color'  -> 'plump_color' 'plump blue'   -> 'plump_blue' 'plump
    yellow' -> 'plump_yellow' 'plump green'  -> 'plump_green'
    """
    for k, v in icon_styles.items():
        if name == v["name"]:
            return k


def filter_style(style: str) -> str:
    """
    Icon styles are identified by the keys in the 'icon_styles' dictionary. For the moment, those
    keys are:
        ['plump_color', 'plump_blue', 'plump_yellow', 'plump_green']

    It could be that old styles are still stored in the file at '~/.embeetle/beetle.btl', for
    example:

    # File: ~/.embeetle/beetle.btl
    {
          "diagnostic_cap": 65536,
          "ribbon_style_toolbar": true,
          "icon_style": "my_old_iconstyle"
    }

    These styles are no longer recognized. They must be filtered out and replaced by the default
    style.

    This function plays an important role at startup. When loading the icon style, it ensures that
    no incompatible (old) styles can be loaded.
    """
    style = style.lower()
    if style in icon_styles.keys():
        return style
    return "plump_color"
