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
import os, functools, sys
import qt, data, functions
import gui.templates.widgetgenerator
import gui.dialogs.projectcreationdialogs as _gen_wizard_
import wizards.lib_wizard.lib_table as _lib_table_
import wizards.lib_wizard.gen_widgets.progbar as _progbar_
import wizards.lib_wizard.filter_widgets.search_groupbox as _search_groupbox_
import wizards.lib_wizard.filter_widgets.author_groupbox as _author_groupbox_
import wizards.lib_wizard.filter_widgets.topic_groupbox as _topic_groupbox_
import wizards.lib_wizard.storage_widgets.proj_storage_groupbox as _proj_storage_groupbox_
import wizards.lib_wizard.storage_widgets.local_storage_groupbox as _local_storage_groupbox_
import wizards.lib_wizard.storage_widgets.search_paths_groupbox as _search_paths_groupbox_
import libmanager.libmanager as _libmanager_
import libmanager.libobj as _libobj_

if TYPE_CHECKING:
    import gui.templates.paintedgroupbox
    import gui.dialogs.popupdialog


class LibWizard(_gen_wizard_.GeneralWizard):
    """"""

    def __init__(
        self,
        parent: Optional[qt.QWidget],
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Create LibWizard(). The callback gets invoked after this instance has
        served its purpose and is already destroyed. > callback(result,
        callbackArg)

        The 'result' parameter is True if the user clicked 'APPLY', False
        otherwise.
        """
        if parent is None:
            parent = data.main_form
        super().__init__(parent)
        self.__callback = callback
        self.__callbackArg = callbackArg
        self.__apply_clicked = False
        self.setWindowTitle("Libraries")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.__resize_and_center()

        # * Horizontal layout
        # Horizontal layout to hold the storage groupboxes.
        self.__hlyt_storage = qt.QHBoxLayout()
        self.__hlyt_storage.setAlignment(qt.Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addLayout(self.__hlyt_storage, stretch=2)

        # * Vertical layout
        # Vertical layout to hold the filter groupboxes.
        self.__vlyt_filters = qt.QVBoxLayout()
        self.__vlyt_filters.setAlignment(qt.Qt.AlignmentFlag.AlignTop)
        self.__hlyt_storage.addLayout(self.__vlyt_filters)

        # * Progbar
        self.__progbar: _progbar_.TableProgbar = _progbar_.TableProgbar(self)
        self.main_layout.addWidget(self.__progbar, stretch=1)

        #! Storage groupboxes
        # Project/Local storage groupbox
        self.__proj_storage_groupbox: Optional[
            _proj_storage_groupbox_.ProjStorageGroupBox
        ] = None
        self.__local_storage_groupbox: Optional[
            _local_storage_groupbox_.LocalStorageGroupBox
        ] = None
        if not data.is_home:
            self.__init_proj_storage()
        else:
            self.__init_local_storage()

        # Search paths groupbox
        self.__search_paths_groupbox: Optional[
            _search_paths_groupbox_.SearchPathsGroupBox
        ] = None
        self.__init_search_paths()

        #! Filter groupboxes
        self.__filters_groupbox: (
            gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton
        ) = gui.templates.paintedgroupbox.PaintedGroupBoxWithLayoutAndInfoButton(
            parent=parent,
            name="Filters",
            text="Filters:",
            info_func=lambda *args: print("info clicked!"),
            h_size_policy=qt.QSizePolicy.Policy.Expanding,
            v_size_policy=qt.QSizePolicy.Policy.Maximum,
        )
        self.__filters_groupbox.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignTop
        )
        self.__filters_groupbox.layout().setContentsMargins(10, 10, 10, 10)
        self.__filters_groupbox.layout().setSpacing(5)

        # Search filter groupbox
        self.__search_groupbox: Optional[_search_groupbox_.SearchGroupBox] = (
            None
        )
        self.__init_gen_filter()

        # Author filter groupbox
        self.__author_groupbox: Optional[_author_groupbox_.AuthorGroupBox] = (
            None
        )
        self.__init_author_filter()

        # Topic filter groupbox
        self.__topic_groupbox: Optional[_topic_groupbox_.TopicGroupBox] = None
        self.__init_topic_filter()

        #! Library table
        # Library Table groupbox
        self.__libtable_groupbox: Optional[_lib_table_.LibTableGroupBox] = None
        self.__resize_and_center()

        if not data.is_home:
            target = "PROJECT"
        else:
            target = "EMBEETLE"

        def page_buttons(*args) -> None:
            self.add_page_buttons()
            self.repurpose_cancel_next_buttons(
                cancel_name=None,  # Keep current situation
                cancel_func=self._cancel_clicked,
                cancel_en=True,
                next_name=f" ADD 0 LIBS TO {target} ",
                next_func=self._complete_wizard,
                next_en=False,
            )
            return

        # Apply the given filters immediately. This also resets the table.
        self.__apply_new_filter(
            callback=page_buttons,
            callbackArg=None,
        )
        return

    def set_callback(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """Set the callback to be invoked at the end of this wizard."""
        assert self.__callback is None
        self.__callback = callback
        self.__callbackArg = callbackArg
        return

    def show(self, category_prefill: Optional[str] = None) -> None:
        """Show this LibWizard()-instance and prefill the category, if given."""

        # print(f'category_prefill = {category_prefill}')
        # if category_prefill is None:
        #     raise RuntimeError()
        def finish(*args):
            _gen_wizard_.GeneralWizard.show(self)
            if category_prefill is not None:
                self.__topic_groupbox.get_combobox().set_selected_text(
                    category=category_prefill
                )
                self.__apply_new_filter(
                    callback=None,
                    callbackArg=None,
                )
            return

        if self.__proj_storage_groupbox is not None:
            self.__proj_storage_groupbox.other_storage_selected()

        # If the LibManager() is already completely initialized - probably because of a previous run
        # - it should refresh now its databases.
        if _libmanager_.LibManager().is_initialized(
            ["proj_relpath", "local_abspath", "zip_url"]
        ):
            _libmanager_.LibManager().refresh(
                origins=["proj_relpath", "local_abspath", "zip_url"],
                callback=finish,
                callbackArg=None,
            )
            return

        finish()
        return

    def resizeEvent(self, e: qt.QResizeEvent) -> None:
        """Each time you resize the window, the widths of the table header cells
        need recomputation."""
        if self.__libtable_groupbox is not None:
            if self.__libtable_groupbox.get_libtable() is not None:
                self.__libtable_groupbox.get_libtable().finish_adding_rows()
        return

    def __resize_and_center(self, *args) -> None:
        """"""
        self.resize(cast(qt.QSize, self.main_layout.sizeHint() * 1.1))  # type: ignore
        self.center_to_parent()
        # self.adjustSize()
        try:
            w, h = functions.get_screen_size()
        except:
            s = functions.get_screen_size()
            w = s.width()
            h = s.height()
        self.resize(int(w * 0.8), int(h * 0.8))
        return

    # ^                                            STORAGE                                             ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def __init_proj_storage(self, *args) -> None:
        """Initialize the project storage groupbox."""
        assert not data.is_home
        self.__proj_storage_groupbox = (
            _proj_storage_groupbox_.ProjStorageGroupBox(parent=None)
        )
        self.__vlyt_filters.addWidget(self.__proj_storage_groupbox)
        return

    def __init_local_storage(self, *args) -> None:
        """Initialize the local storage groupbox."""
        assert data.is_home
        self.__local_storage_groupbox = (
            _local_storage_groupbox_.LocalStorageGroupBox(parent=None)
        )
        self.__vlyt_filters.addWidget(self.__local_storage_groupbox)
        return

    def __init_search_paths(self, *args) -> None:
        """Initialize the search paths groupbox."""
        self.__search_paths_groupbox = (
            _search_paths_groupbox_.SearchPathsGroupBox(parent=None)
        )
        self.__search_paths_groupbox.line_toggled_sig.connect(
            self.__apply_new_filter
        )
        self.__hlyt_storage.addWidget(self.__search_paths_groupbox)
        return

    # ^                                            FILTERS                                             ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def __init_gen_filter(self, *args) -> None:
        """Initialize groupbox for the general filtering."""
        self.__search_groupbox = _search_groupbox_.SearchGroupBox(
            parent=None,
        )
        self.__search_groupbox.btn_clicked_sig.connect(self.__apply_new_filter)
        self.__search_groupbox.lineedit_return_pressed_sig.connect(
            self.__apply_new_filter
        )
        self.__search_groupbox.lineedit_tab_pressed_sig.connect(
            lambda: self.__author_groupbox.get_lineedit().setFocus(
                qt.Qt.FocusReason.TabFocusReason
            )
        )
        self.__vlyt_filters.addWidget(self.__filters_groupbox)  # noqa
        self.__filters_groupbox.layout().addWidget(self.__search_groupbox)
        self.__vlyt_filters.addStretch()
        return

    def __init_author_filter(self, *args) -> None:
        """Initialize groupbox for the author filtering."""
        self.__author_groupbox = _author_groupbox_.AuthorGroupBox(
            parent=None,
        )
        self.__author_groupbox.btn_clicked_sig.connect(self.__apply_new_filter)
        self.__author_groupbox.lineedit_return_pressed_sig.connect(
            self.__apply_new_filter
        )
        self.__author_groupbox.lineedit_tab_pressed_sig.connect(
            lambda: self.__search_groupbox.get_lineedit().setFocus(
                qt.Qt.FocusReason.TabFocusReason
            )
        )
        self.__filters_groupbox.layout().addWidget(self.__author_groupbox)
        return

    def __init_topic_filter(self, *args) -> None:
        """"""
        self.__topic_groupbox = _topic_groupbox_.TopicGroupBox(
            parent=None,
        )
        self.__topic_groupbox.new_topic_selected_sig.connect(
            self.__apply_new_filter
        )
        self.__filters_groupbox.layout().addWidget(self.__topic_groupbox)
        return

    # ^                                         LIBRARY TABLE                                          ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    def __reset_table(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Initialize the Table groupbox and the LibTable() widget. Then show
        the first slice of data.

        If the library table already exists, do a complete refresh.

        MUTEX:
        ======
        While this function runs, it locks the json cruncher's ability to add rows to the table.

        If this function cannot grab the mutex, it will try again after some milliseconds. But it
        will tell the json cruncher to stop adding rows before going in the wait-state.
        """
        if not _libmanager_.LibManager().lock_adding_rows_mutex():
            _libmanager_.LibManager().stop_adding_rows()
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.__reset_table,
                    callback,
                    callbackArg,
                ),
            )
            return

        def initialize_libmanager(*args) -> None:
            origins_to_initialize = (
                _libmanager_.LibManager().get_uninitialized_origins()
            )
            if len(origins_to_initialize) == 0:
                clean()
                return
            _libmanager_.LibManager().initialize(
                libtable=self.__libtable_groupbox.get_libtable(),
                progbar=self.__progbar,
                origins=origins_to_initialize,
                callback=clean,
                callbackArg=None,
            )
            return

        def clean(*args) -> None:
            # It could be that the LibManager() singleton is already initialized beforehand. Make
            # sure the linking to the libtable and progbar is okay.
            _libmanager_.LibManager().link(
                libtable=self.__libtable_groupbox.get_libtable(),
                progbar=self.__progbar,
            )
            # Apply the set json filters.
            _libmanager_.LibManager().apply_filters()
            self.__libtable_groupbox.get_libtable().clean(
                progbar=self.__progbar,
                callback=show_first_slice,
                callbackArg=True,
            )
            return

        def show_first_slice(*args) -> None:
            _libmanager_.LibManager().release_adding_rows_mutex()
            _libmanager_.LibManager().give_more_data(
                callback=finish,
                callbackArg=None,
            )
            return

        def finish(*args) -> None:
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # $ First initialization
        if self.__libtable_groupbox is None:
            self.__libtable_groupbox = _lib_table_.LibTableGroupBox(None)
            self.main_layout.addWidget(self.__libtable_groupbox, stretch=8)
            self.__libtable_groupbox.change_final_btn_sig.connect(
                self.__set_nr_for_final_btn
            )
            qt.QTimer.singleShot(100, initialize_libmanager)
            return
        # $ Just a refreshment
        assert _libmanager_.LibManager().is_initialized(
            ["zip_url", "local_abspath", "proj_relpath"]
        )
        clean()
        return

    # ^                                            ACTIONS                                             ^#
    # % ============================================================================================== %#
    # %                                                                                                %#
    # %                                                                                                %#

    @qt.pyqtSlot(int)
    def __set_nr_for_final_btn(self, n: int) -> None:
        """Set the nr shown in the final button."""
        if not data.is_home:
            target = "PROJECT"
        else:
            target = "EMBEETLE"
        if hasattr(self, "next_button") and (self.next_button is not None):
            self.repurpose_cancel_next_buttons(
                cancel_name=None,  # Keep current situation
                cancel_func=None,  # Keep current situation
                cancel_en=None,  # Keep current situation
                next_name=f" ADD {n} LIBS TO {target} ",
                next_func=None,  # Keep current situation
                next_en=True if n > 0 else False,
            )
        return

    @qt.pyqtSlot()
    def __apply_new_filter(
        self,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """"""

        def finish(*args) -> None:
            self.__set_nr_for_final_btn(0)
            if callback is not None:
                callback(callbackArg)
            return

        json_filter = _libmanager_.LibManager().get_json_filter()

        # & Sanitize filter keywords
        # $ general
        gen_keyword = (
            self.__search_groupbox.get_lineedit().get_text().lower().strip()
        )
        if gen_keyword == "":
            gen_keyword = None
        # $ author
        author_keyword = (
            self.__author_groupbox.get_lineedit().get_text().lower().strip()
        )
        if author_keyword == "":
            author_keyword = None
        # $ topic
        topic_keyword = (
            self.__topic_groupbox.get_combobox()
            .get_selected_text()
            .lower()
            .strip()
        )
        if (
            (topic_keyword == "")
            or (topic_keyword.lower() == "all")
            or (topic_keyword.lower() == "any")
        ):
            topic_keyword = None
        # $ origin
        origin_list = [
            t[0]
            for t in self.__search_paths_groupbox.get_lines()
            if t[1] == True
        ]

        # & Apply keywords on the json filter
        json_filter.set_author_filter(author_filter=author_keyword)
        json_filter.set_search_filter(gen_filter=gen_keyword)
        json_filter.set_topic_filter(topic_filter=topic_keyword)
        json_filter.set_origin_filter(origin_filter=origin_list)

        # & Reset table
        # Within self.__reset_table(), the following function will also be invoked:
        #     _libmanager_.LibManager().apply_filters()
        self.__reset_table(
            callback=finish,
            callbackArg=None,
        )
        return

    # ^                                        COMPLETE WIZARD                                         ^#
    # % ============================================================================================== %#
    # % The user clicks 'APPLY', 'CANCEL' or 'X'.                                                      %#
    # %                                                                                                %#

    def _cancel_clicked(self, *args) -> None:
        """Click 'CANCEL'."""
        # Same effect as clicking 'X'
        self.reject()
        return

    def _complete_wizard(self, *args) -> None:
        """Click 'APPLY'."""
        if self.__apply_clicked or self.dead:
            return
        self.__apply_clicked = True
        callback = self.__callback
        callbackArg = self.__callbackArg

        def _self_destruct(success: bool, *_args) -> None:
            if success:
                self.self_destruct(
                    callback=finish,
                    callbackArg=None,
                )
                return
            self.__apply_clicked = False
            return

        def finish(*_args) -> None:
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        True,
                        callbackArg,
                    ),
                )
            return

        self.__download_and_copy_selected_libs(
            callback=_self_destruct,
            callbackArg=None,
        )
        return

    def __download_and_copy_selected_libs(
        self,
        callback: Optional[Callable],
        callbackArg: Any,
    ) -> None:
        """
        SUMMARY
        =======
        This method is invoked at the end of the wizard - see 'self._complete_wizard()'. The purpose
        is to download/copy/unzip all selected libraries into the cache folder '~/.embeetle/libra-
        ries' (both home and project mode) and into a chosen location in the current project (pro-
        ject mode only).

        The actual download/copy/unzip actions take place in a dedicated method from the LibMana-
        ger()-singleton. That's because those actions can also run aside from this wizard, eg. when
        you update a library.

        CALLBACK
        ========
        Return False (in the callback) if cannot proceed.
            > callback(success, callbackArg)
        """
        # Directory where libraries end up.
        target_libcollection_dir: Optional[str] = None
        # List of all libraries that some of the chosen ones depend on. Only library names are
        # listed.
        dependencies_list: List[str] = []
        # Dictionary of chosen libobjs. Keys are the row numbers.
        checked_libobjs: Optional[Dict[int, _libobj_.LibObj]] = None

        def unselect_all(success: bool, *args) -> None:
            if not success:
                abort()
                return
            self.__libtable_groupbox.get_libtable().unselect_all_checked_rows(
                list(checked_libobjs.keys())
            )
            qt.QTimer.singleShot(25, finish)
            return

        def abort(reason: Optional[str] = None, *args) -> None:
            if reason is not None:
                gui.dialogs.popupdialog.PopupDialog.ok(
                    icon_path="icons/dialog/stop.png",
                    title_text="WARNING",
                    text=reason,
                )
            callback(False, callbackArg)
            return

        def finish(*args) -> None:
            callback(True, callbackArg)
            return

        # * STEP 1: Observe 'target_libcollection_dir'
        # The selected libraries will end up in the 'target_libcollection_dir' - a directory chosen
        # by the user (project mode) or in the cache folder '~/.embeetle/libraries' (home mode). In
        # this section, the 'target_libcollection_dir' is determined and checked to be valid.

        # & PROJECT MODE
        if not data.is_home:
            assert self.__proj_storage_groupbox is not None
            assert self.__local_storage_groupbox is None
            if self.__proj_storage_groupbox.has_error():
                assert not data.is_home
                abort(
                    "Please select a valid folder inside your project to store<br>"
                    "the downloaded libraries."
                )
                return
            target_libcollection_dir = (
                self.__proj_storage_groupbox.get_abspath()
            )

        # & HOME MODE
        else:
            assert self.__proj_storage_groupbox is None
            assert self.__local_storage_groupbox is not None
            target_libcollection_dir = (
                self.__local_storage_groupbox.get_text().replace("\\", "/")
            )

        # & BOTH
        if (target_libcollection_dir is None) or (
            not os.path.isdir(target_libcollection_dir)
        ):
            abort(
                "Please select a valid folder to<br>"
                "store the downloaded libraries."
            )
            return

        # * STEP 2: Extract LibObj()s
        # Extract all LibObj()s checked by the user in the LibTable(). Abort the operation if none
        # were checked.
        try:
            checked_libobjs = (
                self.__libtable_groupbox.get_libtable().get_checked_libobjs()
            )
        except Exception as e:
            # Probably the table is adding or cleaning rows right now. Try again in a moment.
            qt.QTimer.singleShot(
                200,
                functools.partial(
                    self.__download_and_copy_selected_libs,
                    callback,
                    callbackArg,
                ),
            )
            return
        if len(checked_libobjs) == 0:
            abort(
                "You did not select any libraries to be<br>"
                "added to your project."
            )
            return

        # * STEP 3: Start download/copy/unzip procedure
        # At this point, the target location for the libraries is known to be valid and the selected
        # LibObj()s have been extracted. The actual download/copy/unzip operation can start. This is
        # offloaded to the LibManager()-singleton.
        _libmanager_.LibManager().download_or_copy_libraries(
            selected_libobjs=checked_libobjs,
            target_libcollection_dir=target_libcollection_dir,
            callback=unselect_all,
            callbackArg=None,
        )
        return

    def reject(self) -> None:
        """Click 'X'."""
        if self.dead:
            return
        if self.__apply_clicked:
            # How to get here:
            # ----------------
            # User clicks 'X' or 'CANCEL' *after* clicking 'APPLY'. However, after downloading the
            # libraries, this wizards kills itself. So there wouldn't be any chance for the user to
            # click 'X' or 'CANCEL'. Therefore, the only moments to get here are:
            #     - 'APPLY' is clicked, but library downloading didn't start yet
            #     - Library downloading is still ongoing
            # The first option is very unlikely, as downloading starts right away after clicking
            # 'APPLY'. Therefore it makes sense to assume the second option, and show a popup ac-
            # cordingly:
            text = """
            <p>
                Embeetle is busy downloading libraries. Maybe the download<br>
                window is hidden behind the other window(s), so you can't see<br>
                it right now.
            </p>
            """
            gui.dialogs.popupdialog.PopupDialog.ok(
                icon_path="icons/gen/hourglass.png",
                title_text="Please wait",
                text=text,
            )
            # Do not kill the LibWizard() now! Let the download continue. The LibWizard() kills it-
            # self afterwards.
            # If the download fails, the self-destruction is canceled and 'self.__apply_clicked'
            # gets cleared. So the user can then click 'X' again and kill the LibWizard() anyhow.
            return

        callback = self.__callback
        callbackArg = self.__callbackArg

        def finish(*_args) -> None:
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed
            if callback is not None:
                qt.QTimer.singleShot(
                    50,
                    functools.partial(
                        callback,
                        False,
                        callbackArg,
                    ),
                )
            return

        self.self_destruct(
            callback=finish,
            callbackArg=None,
        )
        return

    def is_dead(self) -> bool:
        """"""
        return self.dead

    def self_destruct(
        self,
        death_already_checked: bool = False,
        additional_clean_list: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        callbackArg: Optional[Any] = None,
    ) -> None:
        """Kill this LibWizard()-instance.

        MUTEX:
        ======
        While this method runs, it locks the json cruncher's ability to add rows to the table.

        If this method cannot grab the mutex, it will try again after some milliseconds. First it
        declares this LibWizard()-instance dead and tells the json cruncher to stop adding rows.

        INVOCATIONS:
        ============
            > At the end of 'self._complete_wizard()', which runs when user clicks 'APPLY'.
            > At the end of 'self.reject()', which runs when the user clicks 'X' or 'CANCEL'.

        Both 'self._complete_wizard()' and 'self.reject()' store what's in 'self.__callback' and
        'self.__callbackArg' before invoking the self-destruct method, to be able to call the call-
        back afterwards.

        WARNING:
        ========
        Self destruction happens in this order: first hide(), then kill all widgets and finally
        close() this QDialog(). Invoking close() immediately, without first hiding, causes the
        reject() method to run, which I've overridden to invoke this 'self_destruct()' method! That
        would cause this method to run twice.
        """
        if not death_already_checked:
            if self.dead:
                raise RuntimeError(f"Trying to kill LibWizard() twice!")
            self.dead = True  # noqa

        if not _libmanager_.LibManager().lock_adding_rows_mutex():
            _libmanager_.LibManager().stop_adding_rows()
            qt.QTimer.singleShot(
                100,
                functools.partial(
                    self.self_destruct,
                    True,
                    additional_clean_list,
                    callback,
                    callbackArg,
                ),
            )
            return

        def self_destruct_super(*args) -> None:
            # $ Supercall reject
            # _gen_wizard_.GeneralWizard.reject(self) <= not sure if needed

            # $ Close and destroy
            # 'self.close()' happens in the superclass method:
            _gen_wizard_.GeneralWizard.self_destruct(
                self,
                additional_clean_list=None,
                callback=finish,
                callbackArg=None,
                death_already_checked=True,
            )
            return

        def finish(*args) -> None:
            # $ Clear variables
            self.__callback = None
            self.__callbackArg = None
            data.libman_wizard = None
            _libmanager_.LibManager().release_adding_rows_mutex()
            if callback is not None:
                callback(callbackArg)
            return

        # * Start
        # $ Unlink this wizard from the LibManager()-singleton
        if data.libman is not None:
            data.libman.unlink(
                libtable=self.__libtable_groupbox.get_libtable(),
                progbar=self.__progbar,
            )

        # $ Hide
        self.hide()

        # $ Delete page buttons
        self.delete_page_buttons()

        # $ Destroy stuff
        # self.main_layout
        #     > self.__hlyt_storage
        #         > self.__search_paths_groupbox
        self.__hlyt_storage.removeWidget(self.__search_paths_groupbox)
        self.__search_paths_groupbox.self_destruct()
        self.__search_paths_groupbox = None

        # self.main_layout
        #     > self.__hlyt_storage
        #         > self.__vlyt_filters
        #             > self.__filters_groupbox.layout()
        #                 > self.__search_groupbox
        #                 > self.__author_groupbox
        self.__filters_groupbox.layout().removeWidget(self.__search_groupbox)
        self.__filters_groupbox.layout().removeWidget(self.__author_groupbox)
        self.__filters_groupbox.layout().removeWidget(self.__topic_groupbox)
        self.__search_groupbox.self_destruct()
        self.__author_groupbox.self_destruct()
        self.__topic_groupbox.self_destruct()
        self.__search_groupbox = None
        self.__author_groupbox = None
        self.__topic_groupbox = None

        # self.main_layout
        #     > self.__hlyt_storage
        #         > self.__vlyt_filters
        #             > self.__proj_storage_groupbox
        #             > self.__local_storage_groupbox
        #             > self.__filters_groupbox
        if self.__proj_storage_groupbox is not None:
            self.__vlyt_filters.removeWidget(self.__proj_storage_groupbox)
            self.__proj_storage_groupbox.self_destruct()
            self.__proj_storage_groupbox = None
        if self.__local_storage_groupbox is not None:
            self.__vlyt_filters.removeWidget(self.__local_storage_groupbox)
            self.__local_storage_groupbox.self_destruct()
            self.__local_storage_groupbox = None
        self.__vlyt_filters.removeWidget(self.__filters_groupbox)
        self.__filters_groupbox.self_destruct()
        self.__filters_groupbox = None
        functions.clean_layout(self.__vlyt_filters)
        self.__vlyt_filters = None

        # self.main_layout
        #     > self.__hlyt_storage
        functions.clean_layout(self.__hlyt_storage)
        self.__hlyt_storage = None

        # self.main_layout
        #     > self.__progbar
        self.main_layout.removeWidget(self.__progbar)
        self.__progbar.self_destruct()
        self.__progbar = None

        # self.main_layout
        #     > self.__libtable_groupbox
        self.main_layout.removeWidget(self.__libtable_groupbox)
        print("lib_wizard_02a")
        self.__libtable_groupbox.self_destruct(
            callback=self_destruct_super,
            callbackArg=None,
        )
        return
