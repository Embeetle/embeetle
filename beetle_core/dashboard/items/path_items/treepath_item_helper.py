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
import os, gui
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import data
import helpdocs.help_texts as _ht_
import purefunctions

if TYPE_CHECKING:
    import gui.dialogs.popupdialog
    import dashboard.items.path_items.treepath_items as _treepath_items_
nop = lambda *a, **k: None
q = "'"
dq = '"'


def select_location(
    self: _treepath_items_.TreepathItem,
    autolocate: bool,
    given_abspath: Optional[str],
    callback: Optional[Callable],
) -> None:
    """Select/change the location of the represented PROJECT_LAYOUT item. >
    callback(success)

    WARNING:
    Behavior is now the same for Dashboard and Intro Wizard. Check if this is okay.
    """
    if autolocate:
        assert given_abspath is None
    treepath_obj = self.get_treepath_obj()
    unicum = treepath_obj.get_unicum()
    # Note: The TreepathSeg()-instance is acquired from one's own method.
    treepath_seg = self.get_treepath_seg()
    proj_rootpath = data.current_project.get_proj_rootpath()
    all_rootpaths = data.current_project.get_all_rootpaths()

    def select_dashboard_mk(*args) -> None:
        _ht_.makefiles_together()
        abort()
        return

    def select_filetree_mk(*args) -> None:
        _ht_.makefiles_together()
        abort()
        return

    def select_builddir(*args) -> None:
        # Does the makefile perform shadow or inline building?
        reply = _ht_.what_kind_of_building()
        if reply == "inline":
            finish_selection(proj_rootpath)
            return
        if reply == "shadow":
            if autolocate:
                autolocate_self()
                return
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/folder/closed/folder.png",
                title_text="Select folder",
                text=str(
                    f"Click OK to select the subfolder that will contain all your<br>"
                    f"build artifacts (object files, binaries, ...)."
                ),
            )
            select_folder()
            return
        # Invalid reply
        abort()
        return

    def select_file(*args) -> None:
        # $ Show dialog to make selection
        if given_abspath is None:
            new_abspath = gui.dialogs.popupdialog.PopupDialog.choose_file(
                start_directory=proj_rootpath
            )
            if (new_abspath is not None) and (isinstance(new_abspath, str)):
                finish_selection(new_abspath)
                return
            # Invalid reply
            abort()
            return
        # $ Just use 'given_abspath'
        assert given_abspath is not None
        if os.path.isdir(given_abspath):
            css = purefunctions.get_css_tags()
            blue = css["blue"]
            end = css["end"]
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/folder/closed/folder.png",
                title_text="This is not a file",
                text=str(
                    f"What you entered:<br>"
                    f"{blue}{q}{given_abspath}{q}{end}<br>"
                    f"is not a file!"
                ),
            )
            abort()
            return
        finish_selection(given_abspath)
        return

    def select_folder(*args) -> None:
        # $ Show dialog to make selection
        if given_abspath is None:
            new_abspath = gui.dialogs.popupdialog.PopupDialog.choose_folder(
                start_directory=proj_rootpath
            )
            if (new_abspath is not None) and (isinstance(new_abspath, str)):
                finish_selection(new_abspath)
                return
            # Invalid reply
            abort()
            return
        # $ Just use 'given_abspath'
        assert given_abspath is not None
        if os.path.isfile(given_abspath):
            css = purefunctions.get_css_tags()
            blue = css["blue"]
            end = css["end"]
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/folder/closed/folder.png",
                title_text="This is not a directory",
                text=str(
                    f"What you entered:<br>"
                    f"{blue}{q}{given_abspath}{q}{end}<br>"
                    f"is not a directory!"
                ),
            )
            abort()
            return
        finish_selection(given_abspath)
        return

    def autolocate_self(*args) -> None:
        # Don't add to history here, nor apply it yet. The found abspath will be evaluated in
        # 'finish_selection()' and applied there.
        treepath_obj.call_autolocate_func(
            force=False,
            adapt=False,
            history=False,
            callback=finish_selection,
            callbackArg=None,
        )
        return

    def finish_selection(new_abspath: Optional[str], *args) -> None:
        # & Selection failed
        if (new_abspath is None) or (new_abspath.lower() == "none"):
            # $ Offer retry (if autolocated)
            if autolocate:
                reply = _ht_.do_manual_selection(
                    unicum.get_name(),
                    treepath_obj.is_file(),
                )
                # Retry accepted
                if reply:
                    if treepath_obj.is_file():
                        select_file()
                        return
                    select_folder()
                    return
            # $ Do nothing
            abort()
            return

        # & Selection is within one of the toplevel folders
        if new_abspath is None:
            abort()
            return
        new_abspath = _pp_.standardize_abspath(new_abspath)
        assert isinstance(new_abspath, str)
        if any(
            new_abspath.startswith(rootfolder) for rootfolder in all_rootpaths
        ):
            # $ Nothing changed
            if autolocate and (new_abspath == treepath_obj.get_abspath()):
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/folder/closed/folder.png",
                    title_text="Autodetect",
                    text=str(f"Autodetection didn{q}t find another location."),
                )
                finish()
                return
            # $ Dashboard + Intro wizard
            # Don't refresh the TreepathSeg() yet. That will happen at the
            # finish().
            treepath_seg.set_abspath(
                unicum=unicum,
                abspath=new_abspath,
                history=True,
                refresh=False,
                callback=finish,
                callbackArg=None,
            )
            return

        # & Selection outside toplevel folders
        _ht_.cannot_select_path_outside_project(new_abspath)
        self._v_emitter.refresh_later_sig.emit(False, False, None, None)
        abort()
        return

    def finish(*args) -> None:
        treepath_seg.trigger_dashboard_refresh(
            callback=callback,
            callbackArg=True,
        )
        return

    def abort(*args) -> None:
        treepath_seg.trigger_dashboard_refresh(
            callback=callback,
            callbackArg=False,
        )
        return

    # * Start
    # Observe the TreepathObj() behind this TreepathItem()-instance. What file does it represent?
    if treepath_obj.get_name() == "BUILD_DIR":
        select_builddir()
        return
    if treepath_obj.get_name() == "DASHBOARD_MK":
        select_dashboard_mk()
        return
    if treepath_obj.get_name() == "FILETREE_MK":
        select_filetree_mk()
        return
    if autolocate:
        autolocate_self()
        return
    if treepath_obj.is_file():
        select_file()
        return
    select_folder()
    return


def create_build_folder(
    self: _treepath_items_.TreepathItem,
    callback: Optional[Callable],
    callbackArg: Any,
) -> None:
    """Create a new build folder for the 'BUILD_DIR' entry in the
    PROJECT_LAYOUT.

    WARNING:
    Behavior is now the same for Dashboard and Intro Wizard. Check if this is
    okay.
    """
    treepath_obj = self.get_treepath_obj()
    assert treepath_obj.get_name() == "BUILD_DIR"
    treepath_seg = self.get_treepath_seg()
    proj_rootpath = data.current_project.get_proj_rootpath()
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    green = css["green"]
    end = css["end"]

    def start(*args) -> None:
        builddir_abspath = _pp_.rel_to_abs(
            rootpath=proj_rootpath,
            relpath="build",
        )
        # * Ask about build procedure
        # Does the makefile perform shadow or inline building?
        reply = _ht_.what_kind_of_building()
        # $ INLINE BUILDING => no need for new folder
        if reply == "inline":
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/info.png",
                title_text="No need to create new build directory",
                text=f"""
                <p>
                    You chose 'INLINE BUILDING' - so Embeetle will make<br>
                    'BUILD_DIR' point to your toplevel project folder:<br>
                    {tab}{green}{proj_rootpath}{end}
                </p>
                <p>
                    There is no need to create a new build folder.
                </p>
                """,
            )
            finish_selection(proj_rootpath)
            return
        # $ SHADOW BUILDING => create new folder (or point to existing one)
        if reply == "shadow":
            if os.path.isdir(builddir_abspath):
                already_exists(builddir_abspath)
                return
            make_new(builddir_abspath)
        # Invalid reply
        abort()
        return

    def already_exists(builddir_abspath: str, *args) -> None:
        gui.dialogs.popupdialog.PopupDialog.ok(
            icon_path="icons/dialog/info.png",
            title_text="Build folder exists",
            text=f"""
            <p>
                The build folder already exists:<br>
                {tab}{green}{builddir_abspath}{end}<br>
                The entry 'BUILD_DIR' will now point to this folder.<br>
            </p>
            """,
        )
        finish_selection(builddir_abspath)
        return

    def make_new(builddir_abspath: str, *args) -> None:
        success = _fp_.make_dir(
            dir_abspath=builddir_abspath,
            printfunc=nop,
            catch_err=True,
            overwr=False,
        )
        if not success:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="No permission",
                text=f"""
                <p>
                    Embeetle failed to create the following directory:<br>
                    {tab}{green}{builddir_abspath}{end}<br>
                    This could be due to missing write permissions. Please<br>
                    close Embeetle and check your permissions for the<br>
                    project folder. Otherwise, you'll run into countless<br>
                    errors.<br>
                </p>
                """,
            )
            abort()
            return
        # Making new 'build' subfolder succeeded!
        finish_selection(builddir_abspath)
        return

    def finish_selection(new_abspath: str, *args) -> None:
        # $ Dashboard + Intro wizard
        treepath_seg.set_abspath(
            unicum="BUILD_DIR",
            abspath=new_abspath,
            history=True,
            refresh=False,
            callback=finish,
            callbackArg=None,
        )
        return

    def finish(*args) -> None:
        treepath_seg.trigger_dashboard_refresh(
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    def abort(*args) -> None:
        treepath_seg.trigger_dashboard_refresh(
            callback=callback,
            callbackArg=callbackArg,
        )
        return

    start()
    return
