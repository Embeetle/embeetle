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
import os, functools
import qt, data, gui, purefunctions, functions
import bpathlib.path_power as _pp_
import bpathlib.file_power as _fp_
import tree_widget.items.item as _cm_
import tree_widget.widgets.item_btn as _cm_btn_
import tree_widget.widgets.item_arrow as _cm_arrow_
import tree_widget.widgets.item_lbl as _cm_lbl_
import helpdocs.help_texts as _ht_
import libmanager.libobj as _libobj_
import libmanager.libmanager as _libmanager_
import hardware_api.chip_unicum as _chip_unicum_
import dashboard.items.lib_items.info.lib_name_item as _lib_name_item_
import dashboard.items.lib_items.info.lib_version_item as _lib_version_item_
import dashboard.items.lib_items.info.lib_author_item as _lib_author_item_
import dashboard.items.lib_items.info.lib_arch_item as _lib_arch_item_
import dashboard.items.lib_items.info.lib_dependency_item as _lib_dependency_item_
import dashboard.items.lib_items.info.lib_sample_item as _lib_sample_item_
import dashboard.items.lib_items.info.lib_projpath_item as _lib_projpath_item_
import dashboard.items.lib_items.info.lib_storagepath_item as _lib_storagepath_item_
import dashboard.items.lib_items.info.lib_url_item as _lib_url_item_

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import dashboard.items.lib_items.lib_root_item as _lib_root_item_
    import project.segments.lib_seg.lib_seg as _lib_seg_
    import project.segments.chip_seg.chip as _chip_
from various.kristofstuff import *


class Status(_cm_.Item.Status):
    __slots__ = ()

    def __init__(
        self,
        item: LibItemShared,
        name: str,
    ) -> None:
        """"""
        super().__init__(item=item)
        self.closedIconpath = "icons/gen/book.png"
        self.openIconpath = "icons/gen/book.png"
        self.lblTxt = "Lib?"
        self.lineeditTxt = "Version?"
        self.imgpath = "icons/folder/closed/folder.png"
        return

    def sync_state(
        self,
        refreshlock: bool,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        ATTENTION: Used to run only if self.get_item()._v_layout is not None, but now it runs
        always!
        """

        def start(*args) -> None:
            if self.get_item() is None:
                callback(callbackArg) if callback is not None else nop()
                return
            if self.get_item().get_libobj() is None:
                callback(callbackArg) if callback is not None else nop()
                return
            if refreshlock:
                if not self.get_item().acquire_refresh_mutex():
                    qt.QTimer.singleShot(
                        10,
                        functools.partial(
                            self.sync_state,
                            refreshlock,
                            callback,
                            callbackArg,
                        ),
                    )
                    return
            _cm_.Item.Status.sync_state(
                self,
                refreshlock=False,
                callback=sync_self,
                callbackArg=None,
            )
            return

        def sync_self(*args) -> None:
            libobj = cast(
                _libobj_.LibObj,
                self.get_item().get_libobj(),
            )
            if libobj is None:
                finish()
                return
            # $ Name
            name = libobj.get_name()
            if name is None:
                name = "none"
            self.lblTxt = name
            # $ Errors
            # Show error sign on the icon, but don't let it
            # propagate upwards.
            if data.is_home:
                # $ HOME
                if _libmanager_.chip_exists_compatible_with_lib_archs(
                    libobj.get_architectures()
                ):
                    self.closedIconpath = "icons/gen/book.png"
                    self.openIconpath = "icons/gen/book.png"
                else:
                    self.closedIconpath = "icons/gen/book(err).png"
                    self.openIconpath = "icons/gen/book(err).png"
            else:
                # $ PROJECT
                lib_seg_root_item: _lib_root_item_.LibSegRootItem = (
                    self.get_item().get_rootdir()
                )
                lib_seg: _lib_seg_.LibSeg = lib_seg_root_item.get_projSegment()
                chip: _chip_.Chip = data.current_project.get_chip()
                chip_unicum: _chip_unicum_.CHIP = chip.get_chip_unicum()
                if _libmanager_.is_chip_compatible_with_lib_archs(
                    chip_unicum=chip_unicum,
                    archs=libobj.get_architectures(),
                ):
                    self.closedIconpath = "icons/gen/book.png"
                    self.openIconpath = "icons/gen/book.png"
                else:
                    self.closedIconpath = "icons/gen/book(err).png"
                    self.openIconpath = "icons/gen/book(err).png"
            # functions.assign_icon_err_warn_suffix(itemstatus=self)
            finish()
            return

        def finish(*args) -> None:
            if refreshlock:
                self.get_item().release_refresh_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        start()
        return


class LibItemShared:
    """Shared code between the LibItem() for the Dashboard and the LibItem() for
    the Home Window.

    When used in multiple-inheritance, always put this class second!
    """

    def __init__(self, superclass) -> None:
        """"""
        self.__superclass = superclass
        return

    def init_guiVars(self) -> None:
        """"""
        if self._v_layout is not None:  # noqa
            return
        self.__superclass.init_layout(self)
        self.__superclass.bind_guiVars(
            self,
            itemBtn=_cm_btn_.ItemBtn(owner=self),
            itemArrow=_cm_arrow_.ItemArrow(owner=self),
            itemLbl=_cm_lbl_.ItemLbl(owner=self),
        )
        return

    def leftclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        self.__superclass.leftclick_itemBtn(self, event)

        def start(*args):
            if len(self.get_childlist()) == 0:
                self.refill_children_later(
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args):
            if len(self.get_childlist()) > 0:
                self.toggle_open()
            else:
                self.show_contextmenu_itemBtn(event)
            return

        start()
        return

    def rightclick_itemBtn(self, event: qt.QEvent) -> None:
        """"""
        self.__superclass.rightclick_itemBtn(self, event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLbl(self, event: qt.QEvent) -> None:
        """"""
        self.__superclass.leftclick_itemLbl(self, event)

        def start(*args) -> None:
            if len(self.get_childlist()) == 0:
                self.refill_children_later(
                    callback=finish,
                    callbackArg=None,
                )
                return
            finish()
            return

        def finish(*args) -> None:
            if len(self.get_childlist()) > 0:
                self.toggle_open()
            else:
                self.show_contextmenu_itemBtn(event)
            return

        start()
        return

    def rightclick_itemLbl(self, event: qt.QEvent) -> None:
        self.__superclass.rightclick_itemLbl(self, event)
        self.show_contextmenu_itemBtn(event)
        return

    def leftclick_itemLineedit(self, event: qt.QEvent) -> None:
        self.__superclass.leftclick_itemLineedit(self, event)
        self.show_contextmenu_itemBtn(event)
        return

    def rightclick_itemLineedit(self, event: qt.QEvent) -> None:
        self.__superclass.rightclick_itemLineedit(self, event)
        self.show_contextmenu_itemBtn(event)
        return

    def contextmenuclick_itemBtn(self, key: str) -> None:
        """"""
        key = functions.strip_toplvl_key(key)
        self.__superclass.contextmenuclick_itemBtn(self, key)
        libobj: _libobj_.LibObj = self.get_libobj()
        css = purefunctions.get_css_tags()
        tab = css["tab"]
        red = css["red"]
        green = css["green"]
        blue = css["blue"]
        end = css["end"]

        def wrong(*args):
            "Explain user what is wrong with library"
            incompatible = False
            if data.is_home:
                incompatible = (
                    not _libmanager_.chip_exists_compatible_with_lib_archs(
                        libobj.get_architectures()
                    )
                )
                if incompatible:
                    gui.dialogs.popupdialog.PopupDialog.ok(
                        icon_path="icons/gen/book(err).png",
                        title_text="INCOMPATIBLE LIBRARY",
                        text=str(
                            f"The library {q}{libobj.get_name()}{q} is compatible with the<br>"
                            f"following microcontroller architectures:<br>"
                            f"{tab}{libobj.get_architectures()}<br>"
                            f"<br>"
                            f"Unfortunately, Embeetle doesn{q}t support any microcontroller yet<br>"
                            f"from these architectures."
                        ),
                    )
                    return
            else:
                chip_unicum = data.current_project.get_chip().get_chip_unicum()
                incompatible = (
                    not _libmanager_.is_chip_compatible_with_lib_archs(
                        chip_unicum=chip_unicum,
                        archs=libobj.get_architectures(),
                    )
                )
                if incompatible:
                    gui.dialogs.popupdialog.PopupDialog.ok(
                        icon_path="icons/gen/book(err).png",
                        title_text="INCOMPATIBLE LIBRARY",
                        text=str(
                            f"The library {q}{libobj.get_name()}{q} is compatible with the<br>"
                            f"following microcontroller architectures:<br>"
                            f"{tab}{libobj.get_architectures()}<br>"
                            f"<br>"
                            f"Your microcontroller {q}{chip_unicum.get_name()}{q} belongs to<br>"
                            f"the following architecture(s):<br>"
                            f'{tab}{chip_unicum.get_chip_dict(board=None)["arduino_params"]["library_architectures"]}<br>'
                            f"<br>"
                            f"This microcontroller and library simply don{q}t match.<br>"
                        ),
                    )
                    return

        def open_func(*args):
            "Navigate to library - either in Filetree or native explorer"
            _libmanager_.LibManager().navigate_to_library(
                libobj=self.get_libobj()
            )
            return

        def website_func(*args):
            "Open library website"
            libobj.go_to_website()
            return

        def check_update(*args):
            "Check for updates"
            _libmanager_.LibManager().check_for_updates(
                libobj=libobj,
                callback=lambda *a, **k: print("check_for_updates() finished!"),
                callbackArg=None,
            )
            return

        def show_dependencies(*args):
            "Show libraries this one depends on"
            _libmanager_.LibManager().show_dependencies_recursively(
                libobj=libobj,
                callback=None,
                callbackArg=None,
            )
            return

        def samples(_key):
            "Launch sample project from this library"
            launch_sample_project(
                sketch_key=_key,
                libobj=libobj,
            )
            return

        def delete(*args):
            "Delete the library"
            if not data.is_home:
                library_path = libobj.get_proj_relpath()
                text = str(
                    f"Are you sure you want to delete this library from "
                    f"your project?<br>"
                    f"{tab}{green}{q}{library_path}{q}{end}<br>"
                    f"<br>"
                    f"Click CANCEL to go back."
                )
            else:
                library_path = libobj.get_local_abspath()
                text = str(
                    f"Are you sure you want to delete this library from "
                    f"Embeetle{q}s cache?<br>"
                    f"{tab}{green}{q}{library_path}{q}{end}<br>"
                    f"<br>"
                    f"Click CANCEL to go back."
                )
            ok, _ = gui.dialogs.popupdialog.PopupDialog.ok_cancel(
                icon_path="icons/gen/book.png",
                title_text="DELETE LIBRARY",
                text=text,
            )
            if ok != qt.QMessageBox.StandardButton.Ok:
                return
            self.delete_library(
                None,
                None,
            )
            return

        def _help(_key):
            "Show help for this library"
            version = libobj.get_version()
            if version is None:
                version = "none"
            name = libobj.get_name()
            if name is None:
                name = "none"
            if not data.is_home:
                shown_path = libobj.get_proj_relpath()
            else:
                shown_path = libobj.get_local_abspath()
            if shown_path is None:
                proj_relpath = "none"
            _ht_.specific_lib_help(
                libname=name,
                libversion=version,
                libpath=shown_path,
            )
            return

        funcs = {
            "wrong": wrong,
            "open": open_func,
            "website": website_func,
            "check_update": check_update,
            "show_dependencies": show_dependencies,
            "<samples>": samples,
            "delete": delete,
            "help": _help,
        }
        keylist = key.split("/")
        basekey = keylist[0]
        funcs[basekey](key)
        return

    def refill_children_later(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Add the info-children."""
        libobj: _libobj_.LibObj = self.get_libobj()
        rootItem = self.get_rootdir()

        def start(*args):
            assert len(self.get_childlist()) == 0
            childlist = []  # noqa
            childlist.append(
                _lib_name_item_.LibnameItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            childlist.append(
                _lib_version_item_.LibversionItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            childlist.append(
                _lib_author_item_.LibauthorItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            childlist.append(
                _lib_arch_item_.LibarchItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            childlist.append(
                _lib_dependency_item_.LibdependenciesItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            if (libobj.get_origin() == "proj_relpath") and (not data.is_home):
                childlist.append(
                    _lib_projpath_item_.LibprojpathItem(
                        libobj=libobj,
                        rootdir=rootItem,
                        parent=self,
                    )
                )
            else:
                sample_sketches_dict = (
                    _libmanager_.LibManager().list_sample_sketches(
                        libobj=libobj
                    )
                )
                childlist.append(
                    _lib_sample_item_.LibSampleNodeItem(
                        libobj=libobj,
                        rootdir=rootItem,
                        parent=self,
                        sample_folder_name="topnode",
                        sketch_dict=sample_sketches_dict,
                    )
                )
                childlist.append(
                    _lib_storagepath_item_.LibstoragepathItem(
                        libobj=libobj,
                        rootdir=rootItem,
                        parent=self,
                    )
                )

            childlist.append(
                _lib_url_item_.LiburlItem(
                    libobj=libobj,
                    rootdir=rootItem,
                    parent=self,
                )
            )
            add_children(iter(childlist))
            return

        def add_children(childiter):
            try:
                child = next(childiter)
            except StopIteration:
                finish()
                return
            self.add_child(
                child=child,
                alpha_order=False,
                show=True,
                callback=add_children,
                callbackArg=childiter,
            )
            return

        def finish(*args):
            callback(callbackArg) if callback is not None else nop()
            return

        start()
        return

    #! ====================[ non-implemented functions ]===================== !#
    # The following functions must be implemented in either the child class it-
    # self, or another parent class in the case of multiple inheritance. As long
    # as the other parent is mentioned first, its methods get priority.

    def add_child(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def get_childlist(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def get_rootdir(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def get_libobj(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def delete_library(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def show_contextmenu_itemBtn(self, *args, **kwargs) -> Any:
        raise NotImplementedError()

    def toggle_open(self, *args, **kwargs) -> Any:
        raise NotImplementedError()


def launch_sample_project(sketch_key: str, libobj: _libobj_.LibObj) -> None:
    """Launch a sample project for the given LibObj() library. The chosen sample
    project is defined by 'sketch_key'.

    WARNING: The 'sketch_key' is based on the choice in the context menu. It
             resembles the relpath to the sketch - but with some tweaks. For ex-
             ample: the last foldername - which has the same name as the sketch
             file itself - isn't in this key.

    USAGES
    ======
    Function used here in 'lib_item_shared.py' and in 'lib_sample_item.py'.
    """
    assert data.is_home
    sketch_name: Optional[str] = None
    sketch_abspath: Optional[str] = None
    default_parent_folder: Optional[str] = None
    dot_embeetle_libcollection_dir = (
        _libmanager_.LibManager().get_potential_libcollection_folder(
            "dot_embeetle"
        )
    )
    css = purefunctions.get_css_tags()
    tab = css["tab"]
    red = css["red"]
    green = css["green"]
    blue = css["blue"]
    end = css["end"]

    def start(*args):
        nonlocal sketch_name, sketch_abspath, default_parent_folder
        # * Sanity checks
        if not sketch_key.endswith(".ino"):
            # Abort silently. Incomplete keys are passed first before
            # the complete one arrives.
            abort(None)
            return
        if libobj.get_local_abspath() is None:
            abort("Sketch file is invalid.")
            return
        examples_folder = _pp_.rel_to_abs(
            rootpath=libobj.get_local_abspath(),
            relpath="examples",
        )
        if not os.path.isdir(examples_folder):
            abort("Sketch file is invalid.")
            return

        # * Define abspath to chosen sketch file
        sketch_abspath = sketch_key.replace(
            "<samples>/",
            f"{examples_folder}/",
            1,
        ).replace("//", "/")
        # The last foldername - which has the same name as the
        # sketch file - isn't in the sketch_key. So I need
        # to insert it.
        sketch_name = sketch_abspath.split("/")[-1][0:-4]
        sketch_abspath = "/".join(sketch_abspath.split("/")[0:-1])
        sketch_abspath += f"/{sketch_name}/{sketch_name}.ino"
        sketch_abspath = sketch_abspath.replace("//", "/")
        if not os.path.isfile(sketch_abspath):
            # The 'ArduinoMenu' Library caused an issue, ending up here. It has the
            # following sketches:
            #  - adafruitGfx_eTFT/TFT_eSPI/TFT_eSPI.ino
            #  - adafruitGfx_eTFT/TFT_eSPI/ArduinoMenu_LilyGo_TTGO_T-display_demo/ArduinoMenu_LilyGo_TTGO_T-display_demo.ino
            # So search for the .ino file.
            sketch_abspath = ""
            for root, dirs, files in os.walk(examples_folder):
                for file in files:
                    if file.endswith(f"{sketch_name}.ino"):
                        sketch_abspath = f"{root}/{file}"
                        break
                    continue
                if sketch_abspath != "":
                    break
                continue
            if not os.path.isfile(sketch_abspath):
                abort(
                    f"Sketch file doesn{q}t exist:<br>"
                    f"{q}{sketch_name}.ino{q}<br>"
                )
                return
            else:
                print(
                    f"INFO: Found sketch file with brute force search: {q}{sketch_abspath}{q}"
                )
        else:
            print(f"INFO: Found sketch file: {q}{sketch_abspath}{q}")

        # * Define default location for sample project
        default_parent_folder = _pp_.rel_to_abs(
            rootpath=data.settings_directory,
            relpath="temp_projects",
        )
        if not os.path.isdir(default_parent_folder):
            success = _fp_.make_dir(
                dir_abspath=default_parent_folder,
                printfunc=print,
                catch_err=True,
                overwr=False,
            )
            if not success:
                abort(
                    f"Embeetle failed to create this folder:<br>"
                    f"{q}{default_parent_folder}{q}<br>"
                )
                return
        init_all_origins()
        return

    def init_all_origins(*args):
        "Make sure all origins are initialized"
        origins = _libmanager_.LibManager().get_uninitialized_origins()
        if len(origins) > 0:
            _libmanager_.LibManager().initialize(
                libtable=None,
                progbar=None,
                origins=origins,
                callback=check_library_compatibility,
                callbackArg=None,
            )
            return
        check_library_compatibility()
        return

    def check_library_compatibility(*args):
        "Check if Embeetle supports any chip from the listed lib architectures"

        # $ CASE 1: Architectures not specified
        if libobj.get_architectures() is None:
            check_dependencies()
            return

        # $ CASE 2: Architectures supported
        if _libmanager_.chip_exists_compatible_with_lib_archs(
            libobj.get_architectures()
        ):
            check_dependencies()
            return

        # $ CASE 3: Not supported
        reply = gui.dialogs.popupdialog.PopupDialog.question(
            parent=data.main_form,
            title_text="LIBRARY INCOMPATIBLE",
            icon_path="icons/gen/book.png",
            text=str(
                f"The {q}{libobj.get_name()}{q} library supports the following<br>"
                f"architectures:<br>"
                f"{tab}{libobj.get_architectures()}<br>"
                f"<br>"
                f"Unfortunately, Embeetle doesn{q}t support any microcontroller<br>"
                f"yet based on one of these architectures. Are you sure you want<br>"
                f"to continue?"
            ),
        )
        if reply == qt.QMessageBox.StandardButton.Yes:
            check_dependencies()
            return
        abort(None)
        return

    def check_dependencies(*args):
        "Check if dependent libraries are already cached"
        dependencies_list = (
            _libmanager_.LibManager().list_dependencies_recursively(
                libobj=libobj,
                initial_call=True,
            )
        )
        if dependencies_list is None:
            dependencies_list = []

        # $ Remove dependencies that are already fulfilled
        existing_libnames = _libmanager_.LibManager().list_cached_libs_names()
        if existing_libnames is None:
            existing_libnames = []
        # Do the removal
        for i, libname in reversed(list(enumerate(dependencies_list))):
            if libname in existing_libnames:
                del dependencies_list[i]
        if len(dependencies_list) == 0:
            # Just show the Arduino importer wizard, see
            # finish() sub-function.
            finish(True)
            return

        # $ Ask user about dependencies
        text = str(
            f"This library depens on others that are not yet stored<br>"
            f"by Embeetle. Do you want to download them?<br>"
            f"Note: default libraries storage place is:<br>"
            f"{green}{q}{dot_embeetle_libcollection_dir}{q}{end}<br>"
            f"<br>"
            f"Dependencies:<br>"
        )
        for libname in dependencies_list:
            text += f"&nbsp;&nbsp;- {green}{libname}</span><br>"
        reply = gui.dialogs.popupdialog.PopupDialog.question(
            parent=data.main_form,
            title_text="DOWNLOAD DEPENDENCIES?",
            icon_path="icons/gen/book.png",
            text=text,
        )
        libobjs_to_download = []
        if reply == qt.QMessageBox.StandardButton.Yes:
            for libname in dependencies_list:
                _libobj = _libmanager_.LibManager().get_libobj_from_merged_libs(
                    libname=libname,
                    libversion=None,
                    origins=["zip_url", "local_abspath"],
                )
                if _libobj is not None:
                    libobjs_to_download.append(_libobj)
                else:
                    purefunctions.printc(
                        f"ERROR: Coud not find a LibObj() for {q}{libname}{q}",
                        color="error",
                    )

        # $ Download needed dependencies or make shortcut
        if len(libobjs_to_download) == 0:
            finish(True)
            return
        _libmanager_.LibManager().download_or_copy_libraries(
            selected_libobjs={
                r: _libobj for r, _libobj in enumerate(libobjs_to_download)
            },
            target_libcollection_dir=dot_embeetle_libcollection_dir,
            callback=finish,
            callbackArg=None,
        )
        return

    def abort(reason, *args):
        if reason is not None:
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/dialog/stop.png",
                title_text="ERROR",
                text=reason,
            )
        return

    def finish(success, *args):
        if not success:
            abort(None)
            return
        data.main_form.display.dialog_show_arduino_import_prefilled(
            sketch_name=sketch_name,
            sketch_abspath=sketch_abspath,
            parent_dirpath=default_parent_folder,
        )
        return

    start()
    return
