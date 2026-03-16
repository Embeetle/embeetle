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

import traceback

# Standard library
from typing import *
import re, os

# Local
import qt
import data
import functions
import gui.templates.baseobject
import gui.templates.textmanipulation
import gui.templates.widgetgenerator
import pieces.piecesinterface
import pieces.helperfunctions
import helpdocs.help_texts

if TYPE_CHECKING:
    import gui.dialogs
    import gui.dialogs.popupdialog
    import gui.helpers.simplecombobox
    import gui.helpers.advancedcombobox
    import gui.helpers.buttons


class ThinkingAnimationState(TypedDict):
    running: bool
    timer: Optional[qt.QTimer]
    nr_of_dots: int
    direction: int


class AnswerAnimationState(TypedDict):
    running: bool
    snippet_cntr: int


class GroupboxDict(TypedDict):
    top_groupbox: Optional[qt.QGroupBox]


class ButtonDict(TypedDict):
    add_button: Optional[gui.helpers.buttons.CustomPushButton]
    remove_button: Optional[gui.helpers.buttons.CustomPushButton]


class LabelDict(TypedDict):
    conv_combo_lbl: Optional[gui.templates.widgetgenerator.Label]
    model_combo_lbl: Optional[gui.templates.widgetgenerator.Label]
    state_lbl: Optional[gui.templates.widgetgenerator.Label]


class ComboboxDict(TypedDict):
    conv_combo: Optional[gui.helpers.advancedcombobox.AdvancedComboBox]
    model_combo: Optional[gui.helpers.advancedcombobox.AdvancedComboBox]


class PiecesWindow(qt.QStackedWidget, gui.templates.baseobject.BaseObject):

    def __del__(self) -> None:
        """"""
        if self.__pieces_communicator:
            self.__pieces_communicator.close()
        del self.__pieces_communicator
        return

    def __init__(
        self,
        parent,
        main_form,
        project_path: str,
    ) -> None:
        """"""
        qt.QStackedWidget.__init__(self)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name="PiecesWindow",
            icon="icons/logo/pieces.svg",
        )
        self.__project_path = project_path
        self.__conv_popup_busy = False
        # Keep a dictionary with all known conversations. For example:
        # self.__known_convs = {
        #     '<conv1_id>': {
        #         'id'  : '<conv1_id>',
        #         'name': '<conv1_name>'
        #     },
        #     '<conv2_id>': {
        #         'id'  : '<conv2_id>',
        #         'name': '<conv2_name>'
        #     },
        # }
        self.__known_convs = {}

        # & WIDGETS
        # $ MAIN FRAME
        # Contains everything
        self.__frame: Optional[qt.QFrame] = None
        self.__splitter: Optional[qt.QSplitter] = None
        # $ TOP GROUPBOX
        # Contains all buttons, labels and groupboxes at the top
        self.__groupbox_dict: GroupboxDict = {
            "top_groupbox": None,
        }
        # $ BUTTONS
        self.__button_dict: ButtonDict = {
            "add_button": None,
            "remove_button": None,
        }
        # $ COMBOBOXES
        self.__combobox_dict: ComboboxDict = {
            "conv_combo": None,
            "model_combo": None,
        }
        self.__conversations_initialized = False
        self.__models_initialized = False
        # $ LABELS
        self.__label_dict: LabelDict = {
            "conv_combo_lbl": None,
            "model_combo_lbl": None,
            "state_lbl": None,
        }
        self.__state_lbl_timer_clearance = False
        # $ CHAT DISPLAY
        self.__chat_display: Optional[
            gui.templates.textmanipulation.ConsoleDisplay
        ] = None
        self.__bubble_frames: list[qt.QTextFrame] = []
        self.__thinking_animation_state: ThinkingAnimationState = {
            "running": False,
            "timer": None,
            "nr_of_dots": 0,
            "direction": 1,
        }
        self.__answer_animation_state: AnswerAnimationState = {
            "running": False,
            "snippet_cntr": 0,
        }
        # $ CHAT INPUT
        self.__chat_input: Optional[
            gui.templates.textmanipulation.InputEditor
        ] = None
        self.__need_to_fire_first_prompt = False

        # & PIECES
        self.__pieces_communicator: Optional[
            pieces.piecesinterface.PiecesCommunicator
        ] = None
        self.__init_widgets()
        return

    def __init_widgets(self) -> None:
        """Initialize all widgets."""
        # & MAIN FRAME
        self.__frame = gui.templates.widgetgenerator.create_frame(
            name="MainFrame",
            parent=self,
            layout_vertical=True,
        )
        self.__splitter = qt.QSplitter(qt.Qt.Orientation.Vertical)

        # & TOP GROUPBOX
        self.__groupbox_dict["top_groupbox"] = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                name="ConversationGroupBox",
                parent=self.__frame,
                vertical=False,
                spacing=2,
                margins=(2, 2, 2, 2),
                borderless=True,
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft
        )
        self.__frame.layout().addWidget(self.__groupbox_dict["top_groupbox"])

        # $ BUTTON: Add Conversation
        button_width = int(50 * data.get_global_scale())
        add_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self.__frame,
            name="add-conversation",
            icon_name="icons/tab/plus.svg",
            tooltip="Add a new Pieces conversation",
            statustip="Add a new Pieces conversation",
            click_func=self.__conv_popup_add,
            style="debugger",
        )
        add_button.setMaximumWidth(button_width)
        self.__groupbox_dict["top_groupbox"].layout().addWidget(add_button)
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            add_button,
            qt.Qt.AlignmentFlag.AlignLeft,
        )
        self.__button_dict["add_button"] = add_button

        # $ BUTTON: Delete Conversation
        remove_button = gui.templates.widgetgenerator.create_pushbutton(
            parent=self.__frame,
            name="remove-conversation",
            icon_name="icons/gen/trash.svg",
            tooltip="Delete the selected Pieces conversation",
            statustip="Delete the selected Pieces conversation",
            click_func=self.__conv_popup_remove,
            style="debugger",
        )
        remove_button.setMaximumWidth(button_width)
        self.__groupbox_dict["top_groupbox"].layout().addWidget(remove_button)
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            remove_button,
            qt.Qt.AlignmentFlag.AlignLeft,
        )
        self.__button_dict["remove_button"] = remove_button

        # $ SPACER
        space_size = int(data.get_general_icon_pixelsize() / 2)
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            gui.templates.widgetgenerator.create_spacer(space_size, space_size)
        )

        # $ LABEL: Select Conversation
        tooltip = "Select Pieces AI conversation"
        self.__label_dict["conv_combo_lbl"] = (
            gui.templates.widgetgenerator.create_label(
                parent=self.__frame,
                text="Conversation:",
                tooltip=tooltip,
                transparent_background=True,
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            self.__label_dict["conv_combo_lbl"]
        )

        # $ COMBOBOX: Select Conversation
        self.__combobox_dict["conv_combo"] = (
            gui.templates.widgetgenerator.create_advancedcombobox(
                parent=self.__frame,
                image_size=int(data.get_general_icon_pixelsize() * 1.5),
                no_selection_icon="icons/dialog/message_clear.png",
                no_selection_text="select...",
            )
        )
        self.__combobox_dict["conv_combo"].setToolTip(tooltip)
        self.__combobox_dict["conv_combo"].setStatusTip(tooltip)
        self.__combobox_dict["conv_combo"].update_style()
        self.__combobox_dict["conv_combo"].selection_changed_from_to.connect(
            self.__conv_combobox_clicked
        )
        self.__combobox_dict["conv_combo"].setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Fixed,
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            self.__combobox_dict["conv_combo"]
        )
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            self.__combobox_dict["conv_combo"], qt.Qt.AlignmentFlag.AlignLeft
        )

        # $ SPACER
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            gui.templates.widgetgenerator.create_spacer(space_size, space_size)
        )

        # $ LABEL: Select Model
        tooltip = "Select AI model"
        self.__label_dict["model_combo_lbl"] = (
            gui.templates.widgetgenerator.create_label(
                parent=self.__frame,
                text="Model: ",
                tooltip=tooltip,
                transparent_background=True,
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            self.__label_dict["model_combo_lbl"]
        )

        # $ COMBOBOX: Select Model
        self.__combobox_dict["model_combo"] = (
            gui.templates.widgetgenerator.create_advancedcombobox(
                parent=self.__frame,
                image_size=int(data.get_general_icon_pixelsize() * 1.5),
                no_selection_icon="icons/gen/gear.png",
                no_selection_text="select...",
            )
        )
        self.__combobox_dict["model_combo"].setToolTip(tooltip)
        self.__combobox_dict["model_combo"].setStatusTip(tooltip)
        self.__combobox_dict["model_combo"].update_style()
        self.__combobox_dict["model_combo"].selection_changed_from_to.connect(
            self.__model_combobox_clicked
        )
        self.__combobox_dict["model_combo"].setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.MinimumExpanding,
                qt.QSizePolicy.Policy.Fixed,
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            self.__combobox_dict["model_combo"]
        )
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            self.__combobox_dict["model_combo"],
            qt.Qt.AlignmentFlag.AlignLeft,
        )

        # $ SPACER
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            gui.templates.widgetgenerator.create_spacer(space_size, space_size)
        )

        # $ LABEL: State
        self.__label_dict["state_lbl"] = (
            gui.templates.widgetgenerator.create_label(
                parent=self.__frame,
                text="Retrieving conversations ...",
                size_policy=qt.QSizePolicy(
                    qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Fixed
                ),
            )
        )
        self.__groupbox_dict["top_groupbox"].layout().addWidget(
            self.__label_dict["state_lbl"]
        )
        self.__groupbox_dict["top_groupbox"].layout().setAlignment(
            self.__label_dict["state_lbl"], qt.Qt.AlignmentFlag.AlignLeft
        )

        # & CHAT DISPLAY
        self.__chat_display = gui.templates.textmanipulation.ConsoleDisplay(
            parent=self.__frame,
            parent_window=self,
            max_block_cnt=0,
        )
        self.__chat_display.setLineWrapMode(
            qt.QTextEdit.LineWrapMode.WidgetWidth
        )
        self.__chat_display.link_and_pos_clicked_signal.connect(
            self.__open_clicked_link
        )
        self.__chat_display.setMinimumHeight(150)
        self.__splitter.addWidget(self.__chat_display)

        # & CHAT INPUT
        self.__chat_input = gui.templates.textmanipulation.InputEditor(
            parent=self.__frame,
            parent_window=self,
        )
        self.__chat_input.submit_signal.connect(self.__input_enter_pressed)
        self.__chat_input.stop_answer_generation_signal.connect(
            self.__stop_answer_generation
        )
        self.__chat_input.setSizePolicy(
            qt.QSizePolicy(
                qt.QSizePolicy.Policy.Expanding,
                qt.QSizePolicy.Policy.Preferred,
            )
        )
        self.__chat_input.setMinimumHeight(70)
        self.__splitter.addWidget(self.__chat_input)

        # & ADD TO MAIN FRAME
        # Add frame to main layout
        self.__splitter.setSizes([400, 70])
        self.__splitter.splitterMoved.connect(self.__handle_splitter_moved)
        self.__frame.layout().addWidget(self.__splitter)
        self.addWidget(self.__frame)

        # & LOAD PIECES
        # Instantiate the `PiecesCommunicator()` and show the user Pieces is loading.
        self.__load_pieces()
        return

    def __load_pieces(
        self,
        conv_id: Optional[str] = None,
    ) -> None:
        """Spawn a new `PiecesCommunicator()`-instance which in turn launches a
        `Thread()` and a `Process()` to handle all communications with Pieces
        OS.

        NOTE:
            If a `PiecesCommunicator()`-instance already exists, this method first closes it cleanly
            before spawning a new one.
        """

        def __spawn_communicator(*args, **kwargs) -> None:
            """Spawn the `PiecesCommunicator()`"""
            if self.__pieces_communicator:
                self.__pieces_communicator.close()
                del self.__pieces_communicator
            self.__pieces_communicator = (
                pieces.piecesinterface.PiecesCommunicator(
                    proj_rootpath=data.current_project.get_proj_rootpath(),
                    pieces_packet_received_slot=self.__PTG_message_received,
                )
            )
            if conv_id:
                self.__pieces_communicator.GTP_select_conversation_by_id(
                    conv_id
                )
            # The state label will be cleared once messages come in. Same for the chat display.
            return

        self.__clear_chat()
        self.__disable_input()
        self.__set_state_text("Loading Pieces...")
        self.insert_complete_answer_bubble(
            answer="Loading Pieces...",
            md_to_html=True,
            div_class="answer",
            new_bubble=True,
        )
        if self.__pieces_communicator:
            # Closing the old communicator might take a while. Use a timer to delay this action such
            # that the "Loading Pieces..." chat bubble has time to display itself.
            qt.QTimer.singleShot(1000, __spawn_communicator)
            return

        # No need to wait. Spawn the thing immediately.
        __spawn_communicator()
        return

    # % -------------------------------------%#
    # % -           M O D E L S            - %#
    # % -------------------------------------%#
    def __fill_model_combobox(
        self,
        cur_model_name: Optional[str],
        cur_model_id: Optional[str],
        all_models_dict: dict[str, dict[str, str]],
    ) -> None:
        """Fill the combobox (dropdown) widget with all models and select
        current one.

        The models get listed with:
            - `model_type/model_id`   as key, where `model_type` can be:
                                            - "online_models"
                                            - "offline_downloaded_models"
                                            - "offline_downloading_models"
                                            - "offline_not_yet_downloaded_models"
            - `model_name`            as text
        """
        self.__combobox_dict["model_combo"].clear()
        try:
            # Fill item with everything that needs to go into the `AdvancedCombobox()`. Also return
            # the current selection in this format:
            #     - 'online_models/<model_id>'
            #     - 'offline_downloaded_models/<model_id>'
            #     - 'offline_downloading_models/<model_id>'
            #     - 'offline_not_yet_downloaded_models/<model_id>'
            selection, items = (
                pieces.helperfunctions.generate_item_list_for_models_advanced_combobox(
                    cur_model_name=cur_model_name,
                    cur_model_id=cur_model_id,
                    all_models_dict=all_models_dict,
                )
            )
        except:
            traceback.print_exc()
            return
        self.__combobox_dict["model_combo"].add_items(items)
        self.__combobox_dict["model_combo"].set_selected_name(
            selection
        )  # Can be None
        self.__combobox_dict["model_combo"].adjust_size()
        return

    def __model_combobox_clicked(
        self,
        top_node_from_model_id: str,
        top_node_to_model_id: str,
    ) -> None:
        """"""
        if (
            (not self.__models_initialized)
            or (top_node_to_model_id is None)
            or (top_node_to_model_id.lower() == "empty")
        ):
            try:
                self.__combobox_dict["model_combo"].set_selected_name(
                    top_node_from_model_id
                )
            except:
                traceback.print_exc()
            return

        # & User selected a toplevel node
        # Go back to the initial selection
        if "/" not in top_node_to_model_id:
            self.__combobox_dict["model_combo"].set_selected_name(
                top_node_from_model_id
            )
            return

        # & User selected a leaf node
        top_node = top_node_to_model_id.split("/")[0]
        to_model_id = top_node_to_model_id.split("/")[-1]

        # $ Option 1: User made valid selection
        if top_node in ("online_models", "offline_downloaded_models"):
            self.__combobox_dict["model_combo"].set_selected_name(
                top_node_to_model_id
            )
            self.__pieces_communicator.GTP_select_model_by_id(to_model_id)
            if self.__need_to_fire_first_prompt:
                qt.QTimer.singleShot(
                    100,
                    self.fire_first_prompt,
                )
                self.__need_to_fire_first_prompt = False
            return

        # $ Option 2: User made invalid selection
        elif top_node in (
            "offline_downloading_models",
            "offline_not_yet_downloaded_models",
        ):
            self.__combobox_dict["model_combo"].set_selected_name(
                top_node_from_model_id
            )
            qt.QTimer.singleShot(
                100,
                helpdocs.help_texts.show_model_download_help,
            )
            return

        # $ Option 3: Unrecognized
        else:
            raise RuntimeError(
                f"__model_changed({top_node_from_model_id}, {top_node_to_model_id})"
            )
        return

    def __get_selected_model_id(self) -> Optional[str]:
        """"""
        if not self.__models_initialized:
            return None
        if self.__combobox_dict["model_combo"].get_selected_item_name() is None:
            return None
        if (
            self.__combobox_dict["model_combo"].get_selected_item_name().lower()
            == "empty"
        ):
            return None
        return self.__combobox_dict["model_combo"].get_selected_item_name()

    def __get_selected_model_name(self) -> Optional[str]:
        """"""
        if not self.__models_initialized:
            return None
        if self.__combobox_dict["model_combo"].get_selected_item_name() is None:
            return None
        if (
            self.__combobox_dict["model_combo"].get_selected_item_name().lower()
            == "empty"
        ):
            return None
        model_id = self.__combobox_dict["model_combo"].get_selected_item_name()
        model_name = None
        _data = self.__combobox_dict["model_combo"].get_selected_item()
        for widg in _data["widgets"]:
            if widg["type"] != "text":
                continue
            model_name = widg["text"]
            continue
        return model_name

    # % -------------------------------------%#
    # % -    C O N V E R S A T I O N S     - %#
    # % -------------------------------------%#
    def __fill_conv_combobox(
        self,
        cur_conv_name: Optional[str],
        cur_conv_id: Optional[str],
        all_convs_dict: dict[str, dict[str, str]],
    ) -> None:
        """Fill the combobox (dropdown) widget with all conversations and select
        current one.

        The conversations get listed with:
            - `conv_id`   as key
            - `conv_name` as text

        :param cur_conv_name:   Name of current conversations - can be None.
        :param cur_conv_id:     ID of current conversations - can be None.
        :param all_convs_dict:  Dict listing all conversations, eg:
                                all_convs_dict = {
                                    '<conv1_id>': {
                                        'id'  : '<conv1_id>',
                                        'name': '<conv1_name>'
                                    },
                                    '<conv2_id>': {
                                        'id'  : '<conv2_id>',
                                        'name': '<conv2_name>'
                                    },
                                }
        """
        self.__combobox_dict["conv_combo"].clear()
        selection, items = (
            pieces.helperfunctions.generate_item_list_for_conversation_advanced_combobox(
                cur_conv_name=cur_conv_name,
                cur_conv_id=cur_conv_id,
                all_convs_dict=all_convs_dict,
            )
        )
        self.__known_convs = all_convs_dict
        assert selection == cur_conv_id
        self.__combobox_dict["conv_combo"].add_items(items)
        self.__combobox_dict["conv_combo"].set_selected_name(
            selection
        )  # Can be None
        self.__combobox_dict["conv_combo"].adjust_size()
        return

    def __get_selected_conv_id(self) -> Optional[str]:
        """"""
        if not self.__conversations_initialized:
            return None
        if self.__combobox_dict["conv_combo"].get_selected_item_name() is None:
            return None
        if (
            self.__combobox_dict["conv_combo"].get_selected_item_name().lower()
            == "empty"
        ):
            return None
        return self.__combobox_dict["conv_combo"].get_selected_item_name()

    def __get_selected_conv_name(self) -> Optional[str]:
        """"""
        if not self.__conversations_initialized:
            return None
        if self.__combobox_dict["conv_combo"].get_selected_item_name() is None:
            return None
        if (
            self.__combobox_dict["conv_combo"].get_selected_item_name().lower()
            == "empty"
        ):
            return None
        conv_id = self.__combobox_dict["conv_combo"].get_selected_item_name()
        conv_name = None
        _data = self.__combobox_dict["conv_combo"].get_selected_item()
        for widg in _data["widgets"]:
            if widg["type"] != "text":
                continue
            conv_name = widg["text"]
            continue
        return conv_name

    def __conv_combobox_clicked(
        self,
        from_conv_id: str,
        to_conv_id: str,
    ) -> None:
        """Handles a change of the selected conversation."""
        if (
            (not self.__conversations_initialized)
            or (to_conv_id is None)
            or (to_conv_id.lower() == "empty")
        ):
            try:
                self.__combobox_dict["conv_combo"].set_selected_name(
                    from_conv_id
                )
            except:
                traceback.print_exc()
            return
        if to_conv_id.lower() == "add_conversation":
            try:
                self.__combobox_dict["conv_combo"].set_selected_name(
                    from_conv_id
                )
            except:
                traceback.print_exc()
            qt.QTimer.singleShot(100, self.__conv_popup_add)
            return
        if from_conv_id == to_conv_id:
            # Nothing to do
            return
        # Clear whatever was in the chat, then insert a bubble to let the user know that another
        # conversation is being loaded and send a request to Pieces to switch to the selected
        # conversation. Pieces will do the switch and load all raw messages from this conversation,
        # returning them in a `PTG_MessagesLoaded` packet.
        # As soon as the GUI packet receive loop gets that, it clears the chat display once more and
        # spawns new question- and answer-bubbles from the raw messages. Then it re-enables the
        # input.
        self.__clear_chat()
        self.__disable_input()
        self.insert_complete_answer_bubble(
            answer="Loading conversation ...",
            md_to_html=True,
            div_class="answer",
            new_bubble=True,
        )
        self.__pieces_communicator.GTP_select_conversation_by_id(to_conv_id)
        return

    def __conv_popup_add(self, *args, **kwargs) -> None:
        """Open a popup dialog to create a new conversation.

        Sanitize the input first. If the user enters no name, create a
        conversation named 'nameless'.
        """
        if self.__conv_popup_busy:
            return
        self.__conv_popup_busy = True

        # $ Acquire a name
        def sanitize_input(_name: str) -> str:
            _name = _name.strip()  # No leading and trailing spaces
            _name = _name[:100]  # Limiting length
            _name = re.sub(
                r"[^A-Za-z0-9 _.-]", "", _name
            )  # Allow only sane characters
            if _name == "":
                return "nameless"
            return _name

        message = str("Enter a name for the conversation:\n")
        buttons = [
            ("Create", "create"),
            ("Cancel", "cancel"),
        ]
        reply, text = (
            gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
                dialog_type="custom_buttons",
                text=message,
                title_text="Create Conversation",
                parent=self,
                add_textbox=True,
                buttons=buttons,
            )
        )
        name = sanitize_input(text)

        # $ Check if name already exists
        name_exists: bool = False
        known_conv_names = [
            v["name"].lower() for k, v in self.__known_convs.items()
        ]
        if name.lower() in known_conv_names:
            name_exists = True

        # $ Act on button press
        if reply == "create":
            # OPTION 1: Name already taken. Show a popup and quit.
            if name_exists:
                gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
                    dialog_type="ok",
                    text="A conversation with this name already exists.",
                    title_text="Name Taken",
                    parent=self,
                )
                self.__conv_popup_busy = False
                return
            # OPTION 2: Name not taken. Create the requested conversation and switch to it.
            self.__pieces_communicator.GTP_create_conversation(name)
            self.__pieces_communicator.GTP_select_conversation_by_name(name)
            # FIX:
            # In the edge case where the user has deleted all(!) conversations, the input field has
            # been disabled as a consequence of that - with the exception of the add button to give
            # him at least the option to start a new conversation.
            # However, when creating a new conversation here, the input field must then of course be
            # re-activated:
            self.__enable_input()
        elif reply == "cancel":
            pass
        self.__conv_popup_busy = False
        return

    def __conv_popup_remove(self, *args, **kwargs) -> None:
        """Open a popup dialog to delete the selected conversation."""
        if self.__conv_popup_busy:
            return
        self.__conv_popup_busy = True

        conv_id = self.__get_selected_conv_id()
        conv_name = self.__get_selected_conv_name()

        # $ No conversation selected yet
        if conv_id is None:
            gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
                dialog_type="ok",
                text="No conversation has been selected yet.",
                title_text="Delete Conversation",
                parent=self,
            )
            self.__conv_popup_busy = False
            return

        # $ Delete selected conversation
        message = (
            f"Are you sure you wish to delete\nconversation: '{conv_name}'?"
        )
        buttons = [
            ("Delete", "delete"),
            ("Cancel", "cancel"),
        ]
        reply, text = (
            gui.dialogs.popupdialog.PopupDialog.create_dialog_with_text(
                dialog_type="custom_buttons",
                text=message,
                title_text="Delete Conversation",
                parent=self,
                buttons=buttons,
            )
        )
        if reply == "delete":
            self.__pieces_communicator.GTP_delete_conversation(conv_id=conv_id)
            self.__clear_chat()
        elif reply == "cancel":
            pass
        self.__conv_popup_busy = False
        return

    # % -------------------------------------%#
    # % -            I N P U T             - %#
    # % -------------------------------------%#
    def __input_enter_pressed(self, text: str) -> None:
        """The user pressed the enter key in the input field.

        Clear the input field. Check if a conversation and model are selected,
        then send the question to Pieces.
        """
        self.__chat_input.clear()
        if self.__get_selected_conv_name() and self.__get_selected_model_name():
            self.__ask_question(text)
            return

        self.insert_complete_question_bubble(
            question=text,
            md_to_html=True,
            div_class="question",
            new_bubble=True,
        )
        self.insert_complete_answer_bubble(
            answer=str(
                f"<p>"
                f"Select conversation and model:<br>"
                f"****Selected Conversation:*{self.__get_selected_conv_name()}<br>"
                f"****Selected Model:********{self.__get_selected_model_name()}<br>"
                f"</p>"
            ).replace("*", "&nbsp;"),
            md_to_html=True,
            div_class="server-error",
            new_bubble=True,
        )
        return

    def __list_relevant_paths(self) -> List[str]:
        """
        List all the relevant paths in the current project:
            - paths to source files
            - paths to hdirs
        The caller of this function passes these paths to Pieces. Pieces can then look up things
        in these files to answer the question better.

        TODO:
            - Replace 'paths to hdirs' with 'paths to h-files'. Instead of giving the entire
              directory, it's better to give the precise h-files. Sadly I cannot extract that from
              filetree.mk myself.
            - Get the relevant paths from Matic instead of extracting them myself from 'filetree.mk'
        """
        # $ STEP 1: Find 'filetree.mk'
        filetree_mk_path = data.current_project.get_treepath_seg().get_abspath(
            "FILETREE_MK"
        )
        if (filetree_mk_path is None) or (not os.path.isfile(filetree_mk_path)):
            filetree_mk_path = f"{self.__project_path}/config/filetree.mk"
            if not os.path.isfile(filetree_mk_path):
                return [
                    self.__project_path,
                ]
        filetree_mk_path = filetree_mk_path.replace("\\", "/")
        assert os.path.isfile(filetree_mk_path)

        # $ STEP 2: Extract source files
        source_files = []
        extensions = [
            ".c",
            "c++",
            "cc",
            "cpp",
            "cxx",
            ".h",
            "h++",
            "hh",
            "hpp",
            "hxx",
            "H",
            "s",
            "asm",
            "S",
        ]
        try:
            pattern = re.compile(
                r"(\S+("
                + "|".join(re.escape(ext) for ext in extensions)
                + r"))\.o"
            )
            with open(filetree_mk_path, "r") as file:
                for line in file:
                    match = pattern.search(line)
                    if match:
                        src_file = match.group(1).strip()
                        if src_file.endswith("\\"):
                            src_file = src_file[0:-1]
                        src_file = src_file.strip()
                        if src_file.startswith("project/"):
                            src_file = src_file.replace(
                                "project", self.__project_path, 1
                            )
                        if os.path.isfile(src_file):
                            source_files.append(src_file)
        except:
            traceback.print_exc()
            return [
                self.__project_path,
            ]

        # $ STEP 3: Extract h-dirs
        h_directories = []
        hdir_flag_section = False
        try:
            pattern = re.compile(r"-I\$(SOURCE_DIR)?(.*)")
            with open(filetree_mk_path, "r") as file:
                for line in file:
                    if line.startswith("# INCLUDED HDIRS:"):
                        hdir_flag_section = True  # Start of HDIR_FLAGS section
                        continue
                    if hdir_flag_section:
                        # Break if we reach another section (indicated by '#')
                        if line.strip().startswith("#"):
                            break
                        match = pattern.search(line)
                        if match:
                            # Extract the directory path after the `-I` flag
                            h_dir = match.group(2).strip()
                            if h_dir.endswith("\\"):
                                h_dir = h_dir[0:-1]
                            h_dir = h_dir.strip()
                            if h_dir.startswith("(SOURCE_DIR)"):
                                h_dir = h_dir.replace(
                                    "(SOURCE_DIR)", f"{self.__project_path}/", 1
                                )
                            if os.path.isdir(h_dir):
                                h_directories.append(h_dir)
        except:
            traceback.print_exc()
            return [
                self.__project_path,
            ]

        return source_files + h_directories

    def __ask_question(self, question: str) -> None:
        """Asks a question to the Pieces communicator.

        Disable the input until the answer arrives.
        """
        # Check if everything is ready for a question to be asked. There must be a conversation
        # selected as well as a model.
        if not self.__conversations_initialized:
            raise RuntimeError(
                "__ask_question() invoked while conversations not initialized!"
            )
        if not self.__models_initialized:
            raise RuntimeError(
                "__ask_question() invoked while models not initialized!"
            )
        if self.__get_selected_conv_name() is None:
            raise RuntimeError(
                "__ask_question() invoked while conversation unselected!"
            )
        if self.__get_selected_model_name() is None:
            raise RuntimeError(
                "__ask_question() invoked while model unselected!"
            )
        # 1. Disable input
        self.__disable_input(show_stop_answer_btn=True)

        # 2. Add additional paths
        self.__pieces_communicator.GTP_add_paths(self.__list_relevant_paths())

        # 3. Insert question bubble
        self.insert_complete_question_bubble(
            question=question,
            md_to_html=True,
        )

        # 4. Start thinking animation bubble
        self.start_thinking_animation_bubble()
        self.__set_state_text("Thinking...")

        # 5. Fire the question to Pieces
        self.__pieces_communicator.GTP_ask_question(question)
        return

    def __stop_answer_generation(self, *args, **kwargs) -> None:
        """"""
        self.__pieces_communicator.GTP_stop_stream()
        return

    # %============================================================================================%#
    # %                           P A C K E T   R E C E I V E   L O O P                            %#
    # %============================================================================================%#
    # % This `__PTG_message_received` slot gets invoked each time the Pieces interface fires a     %#
    # % new package to the GUI.                                                                    %#
    # %                                                                                            %#
    @qt.pyqtSlot(dict)
    def __PTG_message_received(self, message: dict) -> None:
        """The `PTG_receive_loop` from the `PiecesCommunicator()` listens in on
        the `PTG_queue` and stuffs all packets it gets from that queue into the
        `pieces_packet_received_signal`.

        This is the slot of that signal.
        """
        _type = message["type"]
        _data = message["data"]

        # & MESSAGE: SERVER ERROR
        if _type == pieces.piecesinterface.MessageType.PTG_ServerError:
            c_def = data.theme["fonts"]["default"]["color"]
            c_red = data.theme["fonts"]["red"]["color"]
            c_blue = data.theme["fonts"]["blue"]["color"]
            c_green = data.theme["fonts"]["green"]["color"]
            text = str(
                f"<span style='color: {c_red}'>WARNING:</span><br>"
                f"<span style='color: {c_red}'>Pieces OS is not reachable!</span><br>"
                f"<br>"
                f"<span style='color: {c_blue}; font-weight: bold;'>If you already installed Pieces:</span><br>"
                f"<span style='color: {c_blue}; font-weight: bold;'>--------------------------------</span><br>"
                f"<span style='color: {c_def}'>"
                f"Start Pieces OS:<br>"
                f"&nbsp;&nbsp;- WINDOWS: Click the Windows Start button (bottom left or<br>"
                f"{'&nbsp;'*13}middle of the Windows taskbar), then start typing<br>"
                f"{'&nbsp;'*13}\"Pieces\". Find and launch \"Pieces OS\".<br>"
                f"<br>"
                f"&nbsp;&nbsp;- LINUX: Launch a terminal and issue the command:<br>"
                f"{'&nbsp;'*11}<span style='color: {c_red}'>&#36;</span> pieces-os<br>"
                f"<br>"
                f"Wait a minute. Then <a href='reload_pieces'>click here</a> to reload.<br>"
                f"<br><br>"
                f"<span style='color: {c_blue}; font-weight: bold'>If you did not yet install Pieces:</span><br>"
                f"<span style='color: {c_blue}; font-weight: bold'>----------------------------------</span><br>"
                f"<span style='color: {c_def}'>"
                f"Pieces AI is an integrated assistant in Embeetle IDE that uses your current "
                f"project code to provide context-aware coding help. You can select from multiple "
                f"LLMs that Pieces supports. Additionally, you can use Pieces AI as a general "
                f"assistant on any topic.<br>"
                f"<br>"
                f"Check our installation instructions here:<br>"
                f"&nbsp;&nbsp;&nbsp;-&#62;&nbsp;<a href='https://embeetle.com/#embeetle-ide/manual/pieces-ai'>https://embeetle.com/#embeetle-ide/manual/pieces-ai</a><br>"
                f"Check out the Pieces for Developers website here:<br>"
                f"&nbsp;&nbsp;&nbsp;-&#62;&nbsp;<a href='https://pieces.app'>https://pieces.app</a><br>"
                f"<br>"
                f"<a href='reload_pieces'>Click here</a> to reload after you finished the installation.<br>"
                f"</span>"
            )

            self.__combobox_dict["conv_combo"].clear()
            self.__combobox_dict["model_combo"].clear()
            self.__set_state_text("Cannot reach Pieces OS")
            self.__clear_chat()
            self.__disable_input()
            self.insert_complete_answer_bubble(
                answer=text,
                md_to_html=True,
                div_class="server-error",
                new_bubble=True,
            )

        # & MESSAGE: CONVERSATIONS COMBOBOX UPDATE
        elif (
            _type == pieces.piecesinterface.MessageType.PTG_ConvsComboboxUpdate
        ):
            self.__fill_conv_combobox(
                cur_conv_name=_data["cur-conv-name"],
                cur_conv_id=_data["cur-conv-id"],
                all_convs_dict=_data["all-convs-dict"],
            )
            self.__conversations_initialized = True

        # & MESSAGE: MODELS COMBOBOX UPDATE
        elif (
            _type == pieces.piecesinterface.MessageType.PTG_ModelsComboboxUpdate
        ):
            self.__fill_model_combobox(
                cur_model_name=_data["cur-model-name"],
                cur_model_id=_data["cur-model-id"],
                all_models_dict=_data["all-models-dict"],
            )
            self.__models_initialized = True

        # & MESSAGE: PIECES INITIALIZED
        elif _type == pieces.piecesinterface.MessageType.PTG_PiecesInitialized:
            self.__clear_chat()
            self.__enable_input()
            self.__set_state_text("Pieces Initialized", 2000)

        # & MESSAGE: ANSWER
        elif _type == pieces.piecesinterface.MessageType.PTG_Answer:
            answer = _data["answer"]
            # $ Answer arrives during thinking animation
            if self.__thinking_animation_state["running"]:
                self.stop_thinking_animation_bubble()
                self.insert_complete_answer_bubble(
                    answer=answer,
                    md_to_html=True,
                    new_bubble=False,
                )

            # $ No thinking animation ongoing
            else:
                self.insert_complete_answer_bubble(
                    answer=answer,
                    md_to_html=True,
                )
            self.__enable_input()
            self.__set_state_text("Answer complete", 2000)

        # & MESSAGE: START ANSWER GENERATION
        # This means the `prompt_cur_conv()` has released its generator object (which should happen
        # instantaneously). Snippets will come later when the generator spits them out.
        elif (
            _type
            == pieces.piecesinterface.MessageType.PTG_StartAnswerGeneration
        ):
            # $ Thinking animation ongoing
            if self.__thinking_animation_state["running"]:
                # No need to stop the thinking animation just yet. Do that as soon as the first
                # answer snippet arrives.
                pass

            # $ No thinking animation ongoing
            else:
                self.start_answer_animation_bubble(new_bubble=True)
                self.__set_state_text("Receiving answer...")

        # & MESSAGE: ANSWER SNIPPET
        # The generator object is spitting out answer snippets in a for-loop. Each of them is
        # catched and sent out on the queue, arriving here.
        elif _type == pieces.piecesinterface.MessageType.PTG_AnswerSnippet:
            if self.__thinking_animation_state["running"]:
                self.stop_thinking_animation_bubble()
                self.start_answer_animation_bubble(new_bubble=False)
                self.__set_state_text("Receiving answer...")
            self.update_answer_animation_bubble(_data["answer-snippet"])

        # & MESSAGE: FINISH ANSWER GENERATION
        # The generator object has exhausted the for-loop. After that, a final message is sent out
        # and arrives here. It contains the prompt status as well as the complete answer.
        elif (
            _type
            == pieces.piecesinterface.MessageType.PTG_FinishAnswerGeneration
        ):
            complete_answer = _data["complete-answer"]
            prompt_status = _data["prompt-status"]
            # Act according to the state of this GUI (chat bubbles) and the state from the Pieces
            # prompt.
            # $ THINKING + ANSWER ANIMATION
            if (
                self.__thinking_animation_state["running"]
                and self.__answer_animation_state["running"]
            ):
                raise RuntimeError(
                    "Thinking and Answer Animation running simultaneously!"
                )
            # $ THINKING ANIMATION
            elif self.__thinking_animation_state["running"]:
                # We're still in the 'Thinking...' stage, which means no answer snippet has arrived
                # at all. This almost certainly means the answer failed to be formed. Let the user
                # know.
                self.stop_thinking_animation_bubble()
                answer = f"{prompt_status} - {complete_answer}"
                if (complete_answer is None) or (complete_answer.strip() == ""):
                    answer = prompt_status
                self.insert_complete_answer_bubble(
                    answer=answer,
                    md_to_html=True,
                    new_bubble=False,
                )
                self.__set_state_text("Failed", 3000)
            # $ ANSWER ANIMATION
            elif self.__answer_animation_state["running"]:
                # We're in the 'answer animation ...' stage, which means one or more answer snippets
                # have arrived earlier. This usually means the answer is okay, but double check by
                # means of the prompt status from Pieces.
                self.stop_answer_animation_bubble()
                if prompt_status == "COMPLETED":
                    self.insert_complete_answer_bubble(
                        answer=complete_answer,
                        md_to_html=True,
                        new_bubble=False,
                    )
                    self.__set_state_text("Answer complete", 2000)
                else:
                    answer = f"{prompt_status} - {complete_answer}"
                    if (complete_answer is None) or (
                        complete_answer.strip() == ""
                    ):
                        answer = prompt_status
                    self.insert_complete_answer_bubble(
                        answer=answer,
                        md_to_html=True,
                        new_bubble=False,
                    )
                    self.__set_state_text("Failed", 3000)
            # $ NO ANIMATION
            else:
                # At least one animation should be running. So print a warning.
                print(
                    "WARNING: PTG_FinishAnswerGeneration received while no animation was running!"
                )
                answer = f"{prompt_status} - {complete_answer}"
                if (complete_answer is None) or (complete_answer.strip() == ""):
                    answer = prompt_status
                self.insert_complete_answer_bubble(
                    answer=answer,
                    md_to_html=True,
                    new_bubble=False,
                )
                self.__set_state_text("Answer complete", 2000)
            # At this point the answer (or notification of failure) should be well presented in a
            # completed answer chat bubble. So we're ready to re-enable the input:
            self.__enable_input()

        # & MESSAGE: CONVERSATION CREATED
        elif (
            _type == pieces.piecesinterface.MessageType.PTG_ConversationCreated
        ):
            # Set a flag to keep in mind that the first prompt still needs to be fired. It normally
            # fires as soon as the messages are loaded (in practice zero messages get loaded, but
            # anyway). However, if no model has been selected, the first prompt cannot fire. In that
            # case, the flag just lingers on, waiting for the right moment.
            self.__need_to_fire_first_prompt = True

        # & MESSAGE: MESSAGES LOADED
        elif _type == pieces.piecesinterface.MessageType.PTG_MessagesLoaded:
            self.__fill_conv_combobox(
                cur_conv_name=message["data"]["cur-conv-name"],
                cur_conv_id=message["data"]["cur-conv-id"],
                all_convs_dict=message["data"]["all-convs-dict"],
            )
            self.__conversations_initialized = True
            self.__fill_model_combobox(
                cur_model_name=message["data"]["cur-model-name"],
                cur_model_id=message["data"]["cur-model-id"],
                all_models_dict=message["data"]["all-models-dict"],
            )
            self.__models_initialized = True

            # $ Clear chat and load all messages
            # Clear whatever was in the chat and load all messages from this (new) conversation as
            # question- and anwer-bubbles.
            self.__clear_chat()
            for m in message["data"]["raw-messages"]:
                message = m["message"]
                is_user_message = m["is_user_message"]
                if is_user_message:
                    self.insert_complete_question_bubble(
                        question=message,
                        md_to_html=True,
                    )
                else:
                    self.insert_complete_answer_bubble(
                        answer=message,
                        md_to_html=True,
                    )
                continue

            # $ Enable input and fire first prompt
            self.__enable_input()
            self.__set_state_text("Messages loaded", 3000)
            if self.__need_to_fire_first_prompt:
                if (
                    self.__conversations_initialized
                    and self.__models_initialized
                    and (self.__get_selected_conv_id() is not None)
                    and (self.__get_selected_model_id() is not None)
                ):
                    qt.QTimer.singleShot(
                        100,
                        self.fire_first_prompt,
                    )
                    self.__need_to_fire_first_prompt = False
                else:
                    # The situation is not ready to fire the first prompt. Let the user know that!
                    self.insert_complete_answer_bubble(
                        answer="Make sure you have selected both a conversation and a model.",
                        md_to_html=True,
                        div_class="answer",
                        new_bubble=True,
                    )

        # & MESSAGE: NO CONVERSATIONS AVAILABLE
        elif (
            _type
            == pieces.piecesinterface.MessageType.PTG_NoConversationsAvailable
        ):
            # Clear conversation text
            self.__clear_chat()
            # Clear combobox
            self.__combobox_dict["conv_combo"].clear()
            self.__combobox_dict["model_combo"].clear()
            self.__set_state_text("No conversations available!")
            # Add warning text
            text = "No conversations are available!<br />Create a new conversation to continue."
            self.insert_complete_answer_bubble(
                answer=text,
                md_to_html=True,
                div_class="server-error",
            )
            self.__disable_input(disable_add_btn=False)
            self.__set_state_text("")

        # & MESSAGE: STREAM STOPPED
        elif _type == pieces.piecesinterface.MessageType.PTG_StreamStopped:
            self.__load_pieces(self.__get_selected_conv_id())

        # * VIEW ADJUSTMENT
        # Only do this for messages that don't fire regularly.
        if not _type == pieces.piecesinterface.MessageType.PTG_AnswerSnippet:
            self.__combobox_dict["conv_combo"].adjust_size()
            self.__combobox_dict["model_combo"].adjust_size()
            qt.QTimer.singleShot(
                100,
                self.__scroll_to_bottom,
            )
        else:
            if self.__answer_animation_state["snippet_cntr"] % 10 == 0:
                qt.QTimer.singleShot(
                    100,
                    self.__scroll_to_bottom,
                )
        return

    # % ========================================================================================== %#
    # %                                  C H A T    B U B B L E S                                  %#
    # % ========================================================================================== %#
    # % The following methods insert "chat bubbles" into the chat display, and perform all kinds   %#
    # % of manipulations on them.                                                                  %#
    # %                                                                                            %#

    # * ---------------------------------[ RAW BUBBLE FUNCTIONS ]--------------------------------- *#
    # These functions directly operate on the `ConsoleDisplay()`.

    def __clear_chat(self) -> None:
        """Delete all chat bubbles."""
        self.__chat_display.clear()
        self.__bubble_frames = []
        return

    def insert_bubble(
        self,
        html_snippet: Optional[str] = None,
        code_list: Optional[List[str]] = None,
        background_color: str = "#ffffff",
        border_color: str = "#000000",
        margin_left: int = 0,
        margin_right: int = 0,
    ) -> None:
        """Insert a chat bubble in the chat display.

        :param html_snippet: The content of the bubble in HTML format.
        :param code_list: List of code snippets that belong to this bubble.
        :param background_color: The background color of the bubble.
        :param border_color: The color of the bubble border.
        :param margin_left: Margin on the left side for the bubble.
        :param margin_right: Margin on the right side for the bubble.
        """
        if qt.sip.isdeleted(self.__chat_display):
            print(
                f"ERROR: Cannot insert chat bubble because `self.__chat_display` is deleted."
            )
            return

        # & Beware of animations
        # While animations are ongoing, no new bubbles should get inserted! That's because every
        # animation interacts with the last bubble and assumes that no new bubbles are added.
        if self.__thinking_animation_state["running"]:
            raise Exception(
                "insert_bubble() called while thinking animation was running!"
            )
        if self.__answer_animation_state["running"]:
            raise Exception(
                "insert_bubble() called while answer animation was running!"
            )

        # & Prepare format for new frame
        frame_format = qt.QTextFrameFormat()
        frame_format.setBackground(qt.QColor(background_color))
        frame_format.setBorder(1)
        frame_format.setPadding(8)
        frame_format.setMargin(8)
        frame_format.setBorderStyle(
            qt.QTextFrameFormat.BorderStyle.BorderStyle_Solid
        )
        frame_format.setBorderBrush(qt.QBrush(qt.QColor(border_color)))
        if margin_left > 0:
            frame_format.setLeftMargin(margin_left)
        if margin_right > 0:
            frame_format.setRightMargin(margin_right)

        # & Create and insert the new frame
        cursor = self.__chat_display.textCursor()
        if qt.sip.isdeleted(cursor):
            print(
                f"ERROR: Cannot insert chat bubble because `self.__chat_display.textCursor()` "
                f"is deleted."
            )
            return
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        frame: qt.QTextFrame = cursor.insertFrame(frame_format)
        if qt.sip.isdeleted(frame):
            print(
                f"ERROR: Cannot insert chat bubble because `cursor.insertFrame(frame_format)` "
                f"returns a frame that is deleted."
            )
            return
        frame.code_list = code_list
        self.__bubble_frames.append(frame)

        # & Insert content in the new frame
        # Move cursor to start of the frame and insert HTML content
        cursor.setPosition(frame.firstPosition())
        if html_snippet:
            if qt.sip.isdeleted(cursor):
                print(
                    f"ERROR: Cannot insert chat bubble because `cursor` is deleted."
                )
                return
            cursor.insertHtml(html_snippet)
            if qt.sip.isdeleted(frame):
                print(
                    f"ERROR: Cannot insert chat bubble because `frame` is deleted."
                )
                return
            cursor.setPosition(frame.lastPosition() + 1)
            cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return

    def replace_last_bubble(
        self,
        html_snippet: str,
        code_list: Optional[List[str]] = None,
    ) -> None:
        """Replace the content of the last text bubble (without deleting the
        bubble itself!).

        :param html_snippet: The content of the bubble in HTML format.
        :param code_list: List of code snippets that belong to this bubble.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if not self.__bubble_frames:
            # No frames found. Insert a new one.
            self.insert_bubble(
                html_snippet=html_snippet,
                code_list=code_list,
            )
            return

        # & Get last frame
        frame: qt.QTextFrame = self.__bubble_frames[-1]
        if qt.sip.isdeleted(frame):
            print(f"ERROR: self.__bubble_frames[-1] pointed at empty shell!")
            self.__bubble_frames.pop()
            self.replace_last_bubble(
                html_snippet=html_snippet,
                code_list=code_list,
            )
            return

        # & Replace frame's content
        # First set the cursor at the beginning of the frame. Then drag it to the end of the frame
        # to select all of the frame's text. Eventually remove it and insert new text.
        cursor = self.__chat_display.textCursor()
        if qt.sip.isdeleted(cursor):
            return
        cursor.setPosition(frame.firstPosition())
        cursor.setPosition(
            frame.lastPosition(), qt.QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        cursor.insertHtml(html_snippet)

        # & Replace frame's `code_list`
        frame.code_list = code_list

        # & Move cursor to end
        cursor.setPosition(frame.lastPosition() + 1)
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return

    def append_to_last_bubble(self, raw_text: str) -> None:
        """Append the given raw text to the end of the last chat bubble.

        The given text should *not* be in html-format, as incrementally added
        html doesn't render correctly.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if not self.__bubble_frames:
            raise RuntimeError(
                "append_to_last_bubble() invoked while no chat bubbles exist!"
            )

        # & Get last frame
        frame: qt.QTextFrame = self.__bubble_frames[-1]
        if qt.sip.isdeleted(frame):
            print(f"ERROR: self.__bubble_frames[-1] pointed at empty shell!")
            self.__bubble_frames.pop()
            self.append_to_last_bubble(raw_text)
            return

        # & Append raw text to frame
        cursor = self.__chat_display.textCursor()
        if qt.sip.isdeleted(cursor):
            return
        cursor.setPosition(frame.lastPosition())
        cursor.insertText(raw_text)
        return

    def remove_last_bubble(self) -> None:
        """Remove the most recent chat bubble.

        Not only the content is removed, but the entire frame.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if not self.__bubble_frames:
            return

        # & Get last frame
        frame: qt.QTextFrame = self.__bubble_frames.pop()
        if qt.sip.isdeleted(frame):
            print(f"ERROR: self.__bubble_frames[-1] points at empty shell!")
            self.remove_last_bubble()
            return

        # & Delete frame
        # First set the cursor at the beginning of the frame. Then drag it to one step *beyond* the
        # end of the frame. That selects not only the frame's text, but the frame itself too! Delete
        # this to remove the entire frame.
        cursor = self.__chat_display.textCursor()
        if qt.sip.isdeleted(cursor):
            return
        cursor.setPosition(frame.firstPosition())
        cursor.setPosition(
            frame.lastPosition() + 1, qt.QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()

        # & Move cursor to end
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return

    # * -----------------------------[ CONVENIENCE BUBBLE FUNCTIONS ]----------------------------- *#
    # These functions make use of the raw functions defined above to do stuff.

    # * ------[ COMPLETE QUESTION & ANSWER BUBBLES ]------ *#
    def insert_complete_question_bubble(
        self,
        question: str,
        md_to_html: bool,
        div_class: str = "question",
        new_bubble: bool = True,
    ) -> None:
        """Insert a question bubble in the chat display, aligned to the right.
        The question bubble is *complete*. Assume that it won't change anymore.

        :param question:    The question to be inserted. Can be html, markdown or just text.
        :param md_to_html:  Assume that the question is in markdown format and convert it to html.
        :param div_class:   If previous parameter is set, wrap the question between these div tags.
        :param new_bubble:  Create a new chat bubble for this question. If False, replace the
                            content of the previous chat bubble.

        NOTE:
        Only when the markdown flag is set, will code snippets be found between the triple backticks
        and saved to the corresponding bubble frame.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if self.__thinking_animation_state["running"]:
            raise RuntimeError(
                "ERROR: Cannot insert question while animation is running!"
            )

        content = ""
        if md_to_html:
            content, code_list = pieces.helperfunctions.get_html_page(
                question, div_class
            )
        else:
            code_list = (None,)
            content = question

        # $ Insert the question as a new bubble
        self.insert_bubble(
            html_snippet=content,
            code_list=code_list,
            background_color=data.theme["pieces_question_background"],
            border_color=data.theme["pieces_question_border"],
            margin_left=100,
        )
        return

    def insert_complete_answer_bubble(
        self,
        answer: str,
        md_to_html: bool,
        div_class: str = "answer",
        new_bubble: bool = True,
    ) -> None:
        """Insert an answer bubble in the chat display, aligned to the left. The
        answer bubble is *complete*. Assume that it won't change anymore.

        :param answer:      The answer to be inserted. Can be html, markdown or just text.
        :param md_to_html:  Assume that the answer is in markdown format and convert it to html.
        :param div_class:   If previous parameter is set, wrap the answer between these div tags.
        :param new_bubble:  Create a new chat bubble for this answer. If False, replace the
                            content of the previous chat bubble.

        NOTE:
        Only when the markdown flag is set will code snippets be found between the triple backticks
        and saved to the corresponding bubble frame.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return

        content = ""
        if md_to_html:
            content, code_list = pieces.helperfunctions.get_html_page(
                answer, div_class
            )
        else:
            content = answer
            code_list = None

        # $ Insert the answer as a new bubble
        if new_bubble:
            self.insert_bubble(
                html_snippet=content,
                code_list=code_list,
                background_color=data.theme["pieces_answer_background"],
                border_color=data.theme["pieces_answer_border"],
                margin_right=100,
            )
            return

        # $ Replace content of previous bubble
        # Just assume that the previous bubble is already in the correct style.
        self.replace_last_bubble(
            html_snippet=content,
            code_list=code_list,
        )
        return

    # * ------[ THINKING ANIMATION ]------ *#
    def start_thinking_animation_bubble(self) -> None:
        """Start an animated bubble."""
        if qt.sip.isdeleted(self.__chat_display):
            return
        if self.__thinking_animation_state["running"]:
            raise RuntimeError(
                "start_thinking_animation_bubble() invoked while "
                "thinking animation was running!"
            )
        if self.__answer_animation_state["running"]:
            raise RuntimeError(
                "start_thinking_animation_bubble() invoked while "
                "answer animation was running!"
            )

        # $ Insert bubble
        self.insert_bubble(
            html_snippet="<p>Thinking</p>",
            code_list=None,
            background_color=data.theme["pieces_answer_background"],
            border_color=data.theme["pieces_answer_border"],
            margin_right=100,
        )

        # $ Initialize state and start the cycle
        self.__thinking_animation_state["running"] = True
        self.__thinking_animation_state["nr_of_dots"] = 0
        self.__thinking_animation_state["direction"] = 1
        self.__thinking_animation_state["timer"] = qt.QTimer()
        self.__thinking_animation_state["timer"].timeout.connect(
            self.update_thinking_animation_bubble
        )
        self.__thinking_animation_state["timer"].start(500)
        return

    def update_thinking_animation_bubble(self) -> None:
        """Show the next animation state."""
        if qt.sip.isdeleted(self.__chat_display):
            return
        if not self.__thinking_animation_state["running"]:
            raise RuntimeError(
                "update_thinking_animation_bubble() called while "
                "thinking animation was not running!"
            )
            return
        if self.__answer_animation_state["running"]:
            raise RuntimeError(
                "update_thinking_animation_bubble() called while "
                "answer animation was running!"
            )
            return

        # $ Update animation state
        if self.__thinking_animation_state["direction"] == 1:
            if self.__thinking_animation_state["nr_of_dots"] < 3:
                self.__thinking_animation_state["nr_of_dots"] += 1
            else:
                self.__thinking_animation_state["direction"] = -1
                self.__thinking_animation_state["nr_of_dots"] -= 1
        elif self.__thinking_animation_state["direction"] == -1:
            if self.__thinking_animation_state["nr_of_dots"] > 0:
                self.__thinking_animation_state["nr_of_dots"] -= 1
            else:
                self.__thinking_animation_state["direction"] = 1
                self.__thinking_animation_state["nr_of_dots"] += 1

        # $ Generate content based on animation state
        content = (
            "<p>Thinking"
            + "." * self.__thinking_animation_state["nr_of_dots"]
            + "</p>"
        )

        # $ Replace content in the last bubble
        self.replace_last_bubble(
            html_snippet=content,
            code_list=None,
        )
        return

    def stop_thinking_animation_bubble(
        self, remove_bubble: bool = False
    ) -> None:
        """Stop the thinking animation.

        Optionally remove the last bubble (in which the animation took place).
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if not self.__thinking_animation_state["running"]:
            raise RuntimeError(
                f"stop_thinking_animation_bubble() invoked while "
                f"thinking animation was not running!"
            )
            return
        if self.__answer_animation_state["running"]:
            raise RuntimeError(
                f"stop_thinking_animation_bubble() invoked while "
                f"answer animation was running!"
            )
            return

        # $ Stop the timer and reset animation state
        if self.__thinking_animation_state["timer"] is not None:
            self.__thinking_animation_state["timer"].stop()
            self.__thinking_animation_state["timer"] = None
        self.__thinking_animation_state["running"] = False
        self.__thinking_animation_state["nr_of_dots"] = 0
        self.__thinking_animation_state["direction"] = 1

        # $ [Optional] Remove animation bubble
        if remove_bubble:
            self.remove_last_bubble()
        return

    # * ------[ ANSWER ANIMATION ]------ *#
    def start_answer_animation_bubble(self, new_bubble: bool = True) -> None:
        """Start a new answer bubble in the chat display, aligned to the left.

        The bubble is empty at the beginning, ready to get text via
        `update_answer_animation_bubble(..)`.
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if self.__thinking_animation_state["running"]:
            raise RuntimeError(
                f"start_answer_animation_bubble() invoked while "
                f"thinking animation was running!"
            )
        if self.__answer_animation_state["running"]:
            raise RuntimeError(
                f"start_answer_animation_bubble() invoked while "
                f"answer animation was running!"
            )

        # $ Insert empty bubble
        if new_bubble:
            self.insert_bubble(
                html_snippet=None,
                code_list=None,
                background_color=data.theme["pieces_answer_background"],
                border_color=data.theme["pieces_answer_border"],
                margin_left=0,
                margin_right=100,
            )
        else:
            self.replace_last_bubble(
                html_snippet="",
                code_list=None,
            )

        # $ Initialize state
        self.__answer_animation_state["running"] = True
        self.__answer_animation_state["snippet_cntr"] = 0
        return

    def update_answer_animation_bubble(self, raw_text: str) -> None:
        """Add a snippet of raw text to the answer bubble (which must be the
        most recent bubble in the chat)."""
        if qt.sip.isdeleted(self.__chat_display):
            return
        if self.__thinking_animation_state["running"]:
            raise RuntimeError(
                "update_answer_animation_bubble() called while "
                "thinking animation was running!"
            )
        if not self.__answer_animation_state["running"]:
            raise RuntimeError(
                "update_answer_animation_bubble() called while "
                "answer animation was not running!"
            )
        self.__answer_animation_state["snippet_cntr"] += 1

        # $ Append content to last bubble
        self.append_to_last_bubble(raw_text)
        return

    def stop_answer_animation_bubble(self, remove_bubble: bool = False) -> None:
        """Stop the answer animation.

        Optionally remove the last bubble (in which the animation took place).
        """
        if qt.sip.isdeleted(self.__chat_display):
            return
        if self.__thinking_animation_state["running"]:
            raise RuntimeError(
                "stop_answer_animation_bubble() called while "
                "thinking animation was running!"
            )
        if not self.__answer_animation_state["running"]:
            raise RuntimeError(
                "stop_answer_animation_bubble() called while answer "
                "animation was not running!"
            )

        # $ Reset animation state
        self.__answer_animation_state["running"] = False
        self.__answer_animation_state["snippet_cntr"] = 0

        # $ [Optional] Remove animation bubble
        if remove_bubble:
            self.remove_last_bubble()
        return

    # % ========================================================================================== %#
    # %                                   O T H E R   S T U F F                                    %#
    # % ========================================================================================== %#
    # %                                                                                            %#

    def __handle_splitter_moved(self, pos: int, index: int) -> None:
        """Prevent the splitter from collapsing."""
        console_height = self.__chat_display.height()
        input_height = self.__chat_input.height()
        if input_height < self.__chat_input.minimumHeight():
            input_height = self.__chat_input.minimumHeight()
        if console_height < self.__chat_display.minimumHeight():
            console_height = self.__chat_display.minimumHeight()
        self.__splitter.setSizes([console_height, input_height])
        return

    def __open_clicked_link(
        self,
        clicked_url: str,
        x: int,
        y: int,
    ) -> None:
        """Opens the clicked URL in the default browser."""
        if clicked_url == "reload_pieces":
            self.__load_pieces()
            return
        if clicked_url.startswith("copy_code"):
            try:
                pos = qt.QPoint(x, y)
                cursor = self.__chat_display.cursorForPosition(pos)
                frame: qt.QTextFrame = cursor.currentFrame()
                assert frame in self.__bubble_frames
                code_index = int(clicked_url[10:-1])
                code = frame.code_list[code_index]  # noqa
                clipboard = data.application.clipboard()
                clipboard.setText(code)
            except:
                traceback.print_exc()
            return
        functions.open_url(clicked_url)
        return

    def __set_state_text(
        self,
        text: str,
        duration: int = -1,
        fired_from_timer: bool = False,
    ) -> None:
        """Set the state text.

        Erase it after `duration` milliseconds. Enter -1 for indefinite.
        """
        if qt.sip.isdeleted(self.__label_dict["state_lbl"]):
            return
        # Check if this call was made from a timer. If so, only let it pass through if the flag is
        # okay.
        if fired_from_timer:
            if not self.__state_lbl_timer_clearance:
                # Ignore this
                return
        # Clear the timer flag, such that whatever this call is doing won't be overrun by a timed
        # event that can come in any moment.
        self.__state_lbl_timer_clearance = False
        try:
            self.__label_dict["state_lbl"].setText(text)
            if (not fired_from_timer) and (duration > 0):
                qt.QTimer.singleShot(
                    duration, lambda *args: self.__set_state_text("", -1, True)
                )
                self.__state_lbl_timer_clearance = True
        except:
            pass
        return

    def __enable_input(self) -> None:
        """Enable the input field."""
        self.__button_dict["add_button"].setEnabled(True)
        self.__button_dict["remove_button"].setEnabled(True)
        self.__combobox_dict["conv_combo"].setEnabled(True)
        self.__combobox_dict["model_combo"].setEnabled(True)
        self.__chat_input.switch_state(
            newstate=gui.templates.textmanipulation.InputEditorState.Enabled
        )
        return

    def __disable_input(
        self,
        disable_add_btn: bool = True,
        disable_del_btn: bool = True,
        show_stop_answer_btn: bool = False,
    ) -> None:
        """Disable the input field.

        :param disable_add_btn: Disable also the 'add conversation' button.
        :param disable_del_btn: Disable also the 'del conversation' button.
        :param show_stop_answer_btn: Show an html-rendered button to stop the
            answer stream.
        """
        self.__button_dict["add_button"].setEnabled(not disable_add_btn)
        self.__button_dict["remove_button"].setEnabled(not disable_del_btn)
        self.__combobox_dict["conv_combo"].setEnabled(False)
        self.__combobox_dict["model_combo"].setEnabled(False)
        if show_stop_answer_btn:
            self.__chat_input.switch_state(
                newstate=gui.templates.textmanipulation.InputEditorState.DisabledWithStopAnswerBtn
            )
            return
        self.__chat_input.switch_state(
            newstate=gui.templates.textmanipulation.InputEditorState.Disabled
        )
        return

    def __scroll_to_bottom(self) -> None:
        """"""
        self.__chat_display.verticalScrollBar().setValue(
            self.__chat_display.verticalScrollBar().maximum()
        )
        return

    def set_focus(self) -> None:
        """Sets the focus to the input field."""
        self.setFocus()
        return

    def copy(self) -> None:
        """"""
        if qt.sip.isdeleted(self.__chat_display):
            return
        self.__chat_display.copy()
        cursor = self.__chat_display.textCursor()
        if qt.sip.isdeleted(cursor):
            return
        cursor.clearSelection()
        self.__chat_display.setTextCursor(cursor)
        return

    def update_style(self, *args, **kwargs) -> None:
        """Update the style of the Pieces window and all of its widgets."""
        if (
            self.__thinking_animation_state["running"]
            or self.__answer_animation_state["running"]
        ):
            qt.QTimer.singleShot(250, self.update_style)
            return
        for k, v in self.__button_dict.items():
            v.update_style(
                new_size=(
                    data.get_general_icon_pixelsize(),
                    data.get_general_icon_pixelsize(),
                )
            )
        for k, v in self.__combobox_dict.items():
            v.update_style(
                image_size=int(data.get_general_icon_pixelsize() * 1.5),
                font=data.get_general_font(),
            )
        for k, v in self.__label_dict.items():
            v.update_style()
        for k, v in self.__groupbox_dict.items():
            # The stored groupboxes are of type `qt.QGroupBox()`, however Matic has added the
            # `update_style()` method to them dynamically:
            v.update_style()  # noqa
        # Update the chat input field
        self.__chat_input.update_style()
        # Reload the entire conversation, because the chat bubbles are probably all in the wrong
        # colors right now.
        self.__clear_chat()
        self.__disable_input()
        self.insert_complete_answer_bubble(
            answer="Loading conversation ...",
            md_to_html=True,
            div_class="answer",
            new_bubble=True,
        )
        self.__pieces_communicator.GTP_reload_conversation()
        return

    def fire_first_prompt(self, *args, **kwargs) -> None:
        """"""
        self.__clear_chat()

        # $ CRAFT THE FIRST PROMPT
        question = ""
        if data.current_project is not None:
            question = f"""
**Prompt:**

You are an AI assistant integrated into Embeetle IDE, assisting an embedded software engineer with their project.

**Project Details:**

- **Project Location:** `{data.current_project.get_proj_rootpath()}`
- **Microcontroller:** `{data.current_project.get_chip().get_name()}`
- **Board:** `{data.current_project.get_board().get_name()}`
- **Flash/Debug Probe:** `{data.current_project.get_probe().get_name()}`

**Build Configuration:**

- **Makefile Location:** `{data.current_project.get_treepath_seg().get_abspath('MAKEFILE')}`
- **Compiler Flags File:** `{data.current_project.get_treepath_seg().get_abspath('DASHBOARD_MK')}`
- **Source Files List:** `{data.current_project.get_treepath_seg().get_abspath('FILETREE_MK')}`
- **Compiler Toolchain:** `{data.current_project.get_toolpath_seg().get_unique_id('COMPILER_TOOLCHAIN')}`

**Flash and Debug Tools:**

- **Flash Tool:** `{data.current_project.get_toolpath_seg().get_unique_id('FLASHTOOL')}`
- **OpenOCD Chip Config:** `{data.current_project.get_treepath_seg().get_abspath('OPENOCD_CHIPFILE')}`
- **OpenOCD Probe Config:** `{data.current_project.get_treepath_seg().get_abspath('OPENOCD_PROBEFILE')}`

**Your Role:**

- Utilize the provided project information to assist the engineer with code development, debugging, build configuration, and problem-solving.
- Offer clear and concise explanations tailored to embedded software development.
- Provide code examples when helpful, using appropriate formatting.
- If additional information is needed due to context limitations, politely ask the user for specific details.
- Focus on optimizing performance, resolving compiler errors, and enhancing code quality within the project's scope.
"""
        else:
            print(
                "ERROR: data.current_project is None at the moment `get_first_prompt()` was "
                "invoked!"
            )
            question = "No project info available"

        # $ FIRE THE PROMPT AT PIECES
        self.__ask_question(question=question)
        return
