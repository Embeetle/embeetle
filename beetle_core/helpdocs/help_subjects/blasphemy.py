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
import threading, html
import data, purefunctions, functions, gui, iconfunctions

if TYPE_CHECKING:
    pass

from various.kristofstuff import *

# $ --- IMPORTANT NOTE --- ?#
# I have tried to find a balance between making these
# 'blasphemy warnings' fun to read while avoiding insults
# to religious people. Here are some expressions I
# changed:
# "His Holiness the GNU"      -> "the GNU"
# "His Excellency the beetle" -> "the beetle"
# "The gods shall punish ..." -> "The heavens shall punish ..."
# "holiness of filenames"     -> "pureness of filenames"

# ! FUNNY PHRASES ! #
# ! ============= ! #


def __get_phrase_spaces_hurt(isfile):
    phrase = f"""
        Thee not knoweth spaces in {'file' if isfile else 'directory '}names cause great pain and suffering<br>
        to the GNU?
    """
    return phrase


def __get_phrase_foreswear_heresy(heresy):
    phrase = f"""
        Thou shalt foreswear, renounce and abjure the vile heresy which claimeth<br>
        that '{heresy}', and have no commerce with the benighted<br>
        heathens who cling to this barbarous belief.<br>
    """
    return phrase


def __get_phrase_beetle_wisdom():
    phrase = f"""
        The Beetle, in his great wisdom, hath ruled that any character rejected by one of<br>
        the great Operating Systems, shall not trespass the territory of thy project. For<br>
        sure if thou thinkest "it cannot happen to me", the code from thy hands will one day<br>
        be opened in another Operating System by thy fellow man, leading him into the pits of<br>
        damnation and subtle bugs. Portability is a blessing for mankind. Woe to him who breaketh<br>
        its rules! Therefore, thou shalt study the chronicles of Wikipedia and educate thyself<br>
        on the <a href="https://en.wikipedia.org/wiki/Filename" style="color: #729fcf;">limitations of filenames</a>
    """
    return phrase


def __get_phrase_gnu_canon():
    phrase = f"""
        The Beetle hath also added that one must consider the canon of GNU and its<br>
        sacred build program 'GNU Make'. Spaces in filenames(&#42;) - although deemed legal<br>
        by the Great Operating Systems - cause great pain and suffering to the GNU.<br>
        Certainly, don't bring the wrath of the GNU upon thyself!
    """
    return phrase


def __get_phrase_sinneth_no_more():
    phrase = f"""
        Henceforth, sinneth no more, that thy files may be pure and thy days pleasant<br>
        and productive.<br>
    """
    return phrase


def __get_phrase_os_doctrines():
    css = purefunctions.get_css_tags()
    red = css["red"]
    end = css["end"]
    phrase = f"""
        The great Operating Systems of our times cling onto different doctrines<br>
        regarding the pureness of filenames. The {red}'&#60;'{end} character is accepted in<br>
        the Linux doctrine, but renounced and excommunicated by the followers of<br>
        Windows.
    """
    return phrase


def __get_phrase_spaces_allowed_conditionally():
    phrase = f"""
        <i>(&#42;)Note: Spaces in the path up to - and including - thy project folder<br>
        art not f'rbidden, as longeth as thee feedeth only relative paths to 'GNU Make'.<br>
        Yet, spaces are considered shadowy, and the pure of heart shouldst not useth them<br>
        in any file- or directory name.</i>
    """
    return phrase


def __get_phrase_repent(cleanse_action, revenger="they"):
    phrase = f"""
        Now repent, go forward and {cleanse_action},<br>
        even when thou art convinced that this is unnecessary, lest {revenger} take<br>
        cruel vengeance upon thee when thou least expect it.
    """
    return phrase


def __get_phrase_beetle_listed():
    phrase = f"""
        Behold,
        The Beetle hast meticulously listed the blasphemous names thou hast<br>
        assigned to thy files and folders:<br>
    """
    return phrase


def __get_paragraph_gnu_angry():
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    h = data.get_general_font_height()
    img = iconfunctions.get_rich_text_pixmap(
        pixmap_relpath="figures/beetle/gnu_angry.png",
        width=h * 10,
    )
    paragraph = f"""
    <p align="left">
        Thou hast angered the GNU! Chaos and madness await thee at its end.<br>
        <br>
        {tab}{tab}{img}<br>
    </p>
    """
    return paragraph


# ! BLASPHEMY AT STARTUP  ! #
# ! ===================== ! #

unholy_relpaths: Set = set()


def register_unholy_char(relpath: str) -> None:
    global unholy_relpaths
    unholy_relpaths.add(relpath)
    return


def __space_startup_warning():
    """Show the 'space warning' if spaces have been detected in an opened
    project (but no other unholy characters)."""
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}Blasphemy!{css['/hx']}
    {__get_paragraph_gnu_angry()}
    {css['h2']}What have I done?{css['/hx']}
    <p align="left">
        {__get_phrase_spaces_hurt(True)}
    </p>
    <p align="left">
        {__get_phrase_beetle_listed()}
        <br>
    """
    # * List entries with spaces
    relpaths = list(unholy_relpaths)
    for i in range(len(relpaths)):
        name = relpaths[i].split("/")[-1]
        invalid_chars = purefunctions.get_invalid_chars(name)
        for c in invalid_chars:
            assert c == " "
        length = len(relpaths[i])
        relpath = relpaths[i]  # .replace('&', '&amp;')
        relpath = html.escape(relpath)
        relpaths[i] = f"{tab}> {blue}'{relpath}'{end}" + "&nbsp;" * max(
            0, 30 - length
        )
    if len(relpaths) > 10:
        relpaths = relpaths[0:9]
        relpaths.append(f"{tab}> {blue}...{end}")
    listing = "<br>".join(relpaths) + "<br>"
    text += listing

    text += f"""
    </p>
    {css['h2']}What should I do?{end}
    <p align="left">
        {__get_phrase_foreswear_heresy('spaces in filenames are okay')}
    </p>
    <p align="left">
        {__get_phrase_repent('cleanse the heretic spaces from thy filenames(&#42;)')}
    </p>
    <p align="left">
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
    )
    return


def __blasphemy_startup_warning():
    """Show the 'blasphemy warning' when unholy characters (and spaces) have
    been detected in an opened project."""
    assert threading.current_thread() is threading.main_thread()

    def catch_click(key, parent=None):
        if key.startswith("http"):
            print(f"open url {q}{key}{q}")
            functions.open_url(key)
            return
        return

    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/unholy_files.png", width=h * 26
    )
    img2 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/darkness.png", width=h * 3
    )
    img3 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/holy_file.png", width=h * 6
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    text = f"""
    {css['h1']}Blasphemy!{end}
    <p align="left">
        Thou hast sinned against the rules of proper file/directory naming.<br>
        <br>
        {tab}{tab}{img1}<br>
        <br>
        The heavens shall surely punish thee for thy arrogance!<br>
    </p>
    {css['h2']}What have I done?{end}
    <p align="left">
        {__get_phrase_beetle_listed()}
        <br>
    """

    # * List entries with unholy characters
    relpaths = list(unholy_relpaths)
    for i in range(len(relpaths)):
        name = relpaths[i].split("/")[-1]
        invalid_chars = ", ".join(
            ["'" + s + "'" for s in purefunctions.get_invalid_chars(name)]
        )
        invalid_chars = invalid_chars.replace("&", "&amp;")
        invalid_chars = html.escape(invalid_chars)
        length = len(relpaths[i])
        relpath = relpaths[i]  # .replace('&', '&amp;')
        relpath = html.escape(relpath)
        relpaths[i] = (
            f"{tab}> {blue}'{relpath}'{end}"
            + "&nbsp;" * max(0, 30 - length)
            + f"{tab}heretic: {red}{invalid_chars}{end}"
        )
    if len(relpaths) > 10:
        relpaths = relpaths[0:9]
        relpaths.append(f"{tab}> {blue}...{end}")
    listing = "<br>".join(relpaths) + "<br>"
    text += listing

    text += f"""
    </p>
    {css['h2']}What should I do?{end}
    <p align='left'>
        {__get_phrase_foreswear_heresy('all characters are okay in filenames')}
    </p>
    <p align='left'>
        {__get_phrase_repent('cleanse the heretic filenames in they project')}<br>
        <br>
        {tab}{img2}
    </p>
    {css['h2']}Recognize heretic characters{end}
    <p align='left'>
        {__get_phrase_os_doctrines()}
    </p>
    <p align='left'>
        {__get_phrase_beetle_wisdom()}
    </p>
    <p align='left'>
        {__get_phrase_gnu_canon()}
    </p>
    <p align='left'>
        {__get_phrase_sinneth_no_more()}
        <br>
        {tab}{img3}
    </p>
    <p align='left'>
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path=f"icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
        text_click_func=catch_click,
    )
    return


def blasphemy_startup_warning():
    """Show the '__blasphemy_startup_warning' or '__space_startup_warning'."""
    for relpath in list(unholy_relpaths):
        name = relpath.split("/")[-1]
        invalid_chars = purefunctions.get_invalid_chars(name)
        for c in invalid_chars:
            if c != " ":
                __blasphemy_startup_warning()
                return
    __space_startup_warning()
    return


# ! BLASPHEMY TRESSPASS WARNINGS  ! #
# ! ============================= ! #


def __refuse_operation_on_blasphemous_directory(relpath: str) -> None:
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    text = f"""
    <p>
        You cannot add files or subfolders to this blasphemous directory!
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
    )
    return


def __space_tresspass_warning(
    name_or_relpath: str, isfile: bool, isrelpath: bool
) -> None:
    print(
        f">>> __space_tresspass_warning(name_or_relpath={name_or_relpath}, isfile={isfile}, isrelpath={isrelpath})"
    )
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Blasphemy!{css['/hx']}
    {__get_paragraph_gnu_angry()}
    {css['h2']}What have I done?{css['/hx']}
    <p align="left">
        {__get_phrase_spaces_hurt(isfile)}
    </p>
    {css['h2']}What should I do?{css['/hx']}
    <p align="left">
        {__get_phrase_foreswear_heresy('spaces in filenames are okay')}
    </p>
    <p align="left">
        {__get_phrase_repent(
            f"chooseth anoth'r name for thy {'file' if isfile else 'directory'}(&#42;)",
            f"the GNU",
        )}
    </p>
    <p align="left">
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
    )
    return


def __blasphemy_tresspass_warning(
    name_or_relpath: str, isfile: bool, isrelpath: bool
) -> None:
    print(
        f">>> __blasphemy_tresspass_warning(name_or_relpath={name_or_relpath}, isfile={isfile}, isrelpath={isrelpath})"
    )
    assert threading.current_thread() is threading.main_thread()

    def catch_click(key, parent=None):
        if key.startswith("http"):
            print(f"open url {key}")
            functions.open_url(key)
            return
        return

    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/heretic_file_tresspassing.png", width=h * 20
    )
    img2 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/holy_file.png", width=h * 6
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]

    text = f"""
    {css['h1']}Warning!{css['/hx']}
    <p align="left">
        An heretic {'file' if isfile else 'directory'} hast tried to tresspass into thy project! The Beetle<br>
        hast ceased the file with great force.<br>
        <br>
        {tab}{tab}{img1}
    </p>
    {css['h2']}Why did this happen?{css['/hx']}
    <p align="left">
        Thy fingers has't slipped whilst typing the name, thereby bringing forth<br>
        an heretic {'file' if isfile else 'directory'} with a vile name. The foul creature attempted to<br>
        tresspass onto the territory of thy project. Lest it not be for the bravery<br>
        of the Beetle, great misfortunes wouldst befall thee!
    </p>
    {css['h2']}What should I do?{css['/hx']}
    <p align="left">
        {__get_phrase_foreswear_heresy('all characters are okay in filenames')}
    </p>
    <p align="left">
        {__get_phrase_repent(
            f"chooseth anoth'r name for thy {'file' if isfile else 'directory'}",
            "file" if isfile else "directory",
        )}
    </p>
    {css['h2']}Recognize heretic characters{css['/hx']}
    <p align="left">
        {__get_phrase_os_doctrines()}
    </p>
    <p align="left">
        {__get_phrase_beetle_wisdom()}
    </p>
    <p align="left">
        {__get_phrase_gnu_canon()}
    </p>
    <p align="left">
        {__get_phrase_sinneth_no_more()}
        <br>
        {tab}{img2}
    </p>
    <p align="left">
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="WARNING!",
        text=text,
        text_click_func=catch_click,
    )
    return


def refuse_operation_on_blasphemous_directory(relpath: str):
    """"""
    __refuse_operation_on_blasphemous_directory(relpath)
    return


def blasphemy_tresspass_warning(name: str, isfile: bool):
    """Show when new filename or subdirname is filled in."""
    invalid_chars = purefunctions.get_invalid_chars(name)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_tresspass_warning(name, isfile, isrelpath=False)
            return
    __space_tresspass_warning(name, isfile, isrelpath=False)
    return


# ! BLASPHEMY EXISTING NAMES/RELPATHS WARNINGS  ! #
# ! =========================================== ! #


def __space_warning(
    name_or_relpath: str, isfile: bool, isrelpath: bool
) -> None:
    print(
        f">>> __space_warning(name_or_relpath={name_or_relpath}, isfile={isfile}, isrelpath={isrelpath})"
    )
    assert threading.current_thread() is threading.main_thread()
    h = data.get_general_font_height()
    css = purefunctions.get_css_tags()

    text = f"""
    {css['h1']}Blasphemy!{css['/hx']}
    {__get_paragraph_gnu_angry()}
    {css['h2']}What have I done?{css['/hx']}
    <p align="left">
        {__get_phrase_spaces_hurt(isfile)}
    </p>
    {css['h2']}What should I do?{css['/hx']}
    <p align="left">
        {__get_phrase_foreswear_heresy('spaces in filenames are okay')}
    </p>
    <p align="left">
        {__get_phrase_repent(
            f"cleanse thy {'file' if isfile else 'directory'}(&#42;)",
            f"the GNU"
        )}
    </p>
    <p align="left">
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="Illegal character!",
        text=text,
    )
    return


def __blasphemy_warning(
    name_or_relpath: str, isfile: bool, isrelpath: bool
) -> None:
    print(
        f">>> __blasphemy_warning(name_or_relpath={name_or_relpath}, isfile={isfile}, isrelpath={isrelpath})"
    )
    assert threading.current_thread() is threading.main_thread()

    def catch_click(key, parent=None):
        if key.startswith("http"):
            print(f"open url {key}")
            functions.open_url(key)
            return
        return

    h = data.get_general_font_height()
    img1 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/beetle_registers_heretic.png", width=h * 20
    )
    img2 = iconfunctions.get_rich_text_pixmap(
        "figures/beetle/holy_file.png", width=h * 6
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    end = css["end"]

    text = f"""
    {css['h1']}Warning!{css['/hx']}
    <p align="left">
        An heretic {'file' if isfile else 'directory'} is living in thy project! His excellency,<br>
        the Beetle, hast written down its vile name: {red}'{name_or_relpath}'{end}<br>
        <br>
        {tab}{tab}{img1}
    </p>
    {css['h2']}What should I do?{css['/hx']}
    <p align="left">
        {__get_phrase_foreswear_heresy('all characters are okay in filenames')}
    </p>
    <p align="left">
        {__get_phrase_repent(
            f"cleanse thy {'file' if isfile else 'directory'}",
            "file" if isfile else "directory",
        )}
    </p>
    {css['h2']}Recognize heretic characters{css['/hx']}
    <p align="left">
        {__get_phrase_os_doctrines()}
    </p>
    <p align="left">
        {__get_phrase_beetle_wisdom()}
    </p>
    <p align="left">
        {__get_phrase_gnu_canon()}
    </p>
    <p align="left">
        {__get_phrase_sinneth_no_more()}
        <br>
        {tab}{img2}
    </p>
    <p align="left">
        {__get_phrase_spaces_allowed_conditionally()}
    </p>
    """
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/dialog/stop.png",
        title_text="WARNING!",
        text=text,
        text_click_func=catch_click,
    )
    return


def blasphemy_name_warning(name: str, isfile: bool):
    """Show the '__blasphemy_warning' or '__space_warning'."""
    invalid_chars = purefunctions.get_invalid_chars(name)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_warning(name, isfile, isrelpath=False)
            return
    __space_warning(name, isfile, isrelpath=False)
    return


def blasphemy_path_warning(relpath: str, isfile: bool):
    """Show the '__blasphemy_warning' or '__space_warning'."""
    invalid_chars = purefunctions.get_invalid_relpath_chars(relpath)
    for c in invalid_chars:
        if c != " ":
            __blasphemy_warning(relpath, isfile, isrelpath=True)
            return
    __space_warning(relpath, isfile, isrelpath=True)
    return
