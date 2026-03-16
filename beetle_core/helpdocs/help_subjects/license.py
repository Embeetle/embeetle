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
import data, functions, serverfunctions, gui

if TYPE_CHECKING:
    import qt
    import gui.dialogs
    import gui.dialogs.popupdialog


def show_license(
    parent: qt.QWidget,
    txt: str,
    typ: str = "accept_decline",
) -> Union[
    qt.QMessageBox.StandardButton.Ok, qt.QMessageBox.StandardButton.Cancel
]:
    """"""

    def catch_click(key, *args, **kwargs) -> None:
        if key.startswith("http"):
            functions.open_url(key)
            return
        key = key.lower()
        funcs = {
            "#licenses/clang_license.txt": show_clang_license,
            "#licenses/gpl-3.0.txt": show_gplv3_license,
            "#licenses/lgpl-3.0.txt": show_lgplv3_license,
            "#licenses/gcc-arm-none-eabi_license.txt": show_gcc_license,
            "#licenses/license-openocd.txt": show_openocd_license,
            "#licenses/license-hidapi.txt": show_hidapi_license,
            "#licenses/license-libftdi.txt": show_ftdi_license,
            "#licenses/license-libusb.txt": show_libusb_license,
            "#licenses/license-libusb-win32.txt": show_libusb_win32_license,
            "#licenses/pyelftools_license.pre": show_pyelftools_license,
            "#licenses/construct_license.pre": show_construct_license,
            "#licenses/cubemx.pre": show_cubemx_license,
            "/content/licenses/sla0048_stm32cubemx.pdf": show_cubemx_license,
        }
        funcs[key]()
        return

    text = txt.replace("\n", "<br>")
    text += """
        <br>
        Click <b>Accept</b> if you accept the Embeetle license and all licenses for third party<br>
        software distributed with Embeetle - as listed above.<br>
        <br>
    """
    popup = gui.dialogs.popupdialog.PopupDialog.accept_decline
    if typ == "ok":
        popup = gui.dialogs.popupdialog.PopupDialog.ok
    result = popup(
        icon_path="icons/gen/certificate.png",
        text=text,
        title_text="License agreement",
        text_click_func=catch_click,
        parent=parent,
    )
    if typ == "accept_decline":
        result = result[0]
    return result


def show_clang_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "clang_license.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="Clang license",
        text=text,
    )
    return


def show_libusb_win32_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "license-libusb-win32.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="libusb-win32 license",
        text=text,
    )
    return


def show_libusb_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "license-libusb.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="libusb license",
        text=text,
    )
    return


def show_ftdi_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "license-libftdi.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="libftdi license",
        text=text,
    )
    return


def show_hidapi_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "license-hidapi.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="hidapi license",
        text=text,
    )
    return


def show_openocd_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "license-openocd.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="OpenOCD license",
        text=text,
    )
    return


def show_gplv3_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "gpl-3.0.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="GPLv3 license",
        text=text,
    )
    return


def show_lgplv3_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "lgpl-3.0.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="LGPLv3 license",
        text=text,
    )
    return


def show_gcc_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "gcc-arm-none-eabi_license.txt",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="GCC Toolchain license",
        text=text,
        large_text=True,
    )
    return


def show_pyelftools_license(*args) -> None:
    """"""

    def catch_click(key, *_args, **kwargs):
        if key.startswith("http"):
            functions.open_url(key)
            return
        key = key.lower()
        funcs = {
            "#licenses/construct_license.pre": show_construct_license,
        }
        funcs[key]()
        return

    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "pyelftools_license.pre",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="Pyelftools license",
        text=text,
        text_click_func=catch_click,
    )
    return


def show_construct_license(*args) -> None:
    """"""
    license_path = functions.unixify_path_join(
        data.beetle_licenses_directory,
        "construct_license.pre",
    )
    text = functions.get_file_text(license_path).replace("\n", "<br>")
    gui.dialogs.popupdialog.PopupDialog.ok(
        icon_path="icons/gen/certificate.png",
        title_text="Construct license",
        text=text,
        text_click_func=functions.open_url,
    )
    return


def show_cubemx_license(*args) -> None:
    """"""
    functions.open_url(
        f"{serverfunctions.get_base_url_wfb()}/content/licenses/SLA0048_STM32CubeMX.pdf"
    )
    return
