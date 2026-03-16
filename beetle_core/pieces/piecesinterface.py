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

from typing import *
from pydantic import *

# Standard library
import os
import enum
import time
import queue
import threading
import traceback
import multiprocessing
import os_checker

# Libraries
import pieces_os_client
import pieces_os_client.configuration
import pieces_os_client.api_client
import pieces_os_client.api.conversation_message_api
import pieces_os_client.api.conversation_messages_api
import pieces_os_client.api.conversation_api
import pieces_os_client.api.conversations_api
import pieces_os_client.api.qgpt_api
import pieces_os_client.api.user_api
import pieces_os_client.wrapper
import pieces_os_client.wrapper.client
import pieces_os_client.wrapper.basic_identifier.chat
import pieces_os_client.wrapper.websockets
import pieces_os_client.wrapper.websockets.base_websocket
import pieces_os_client.models.seeded_conversation_message
import pieces_os_client.models.qgpt_stream_enum as _stream_enum_
import pieces_os_client.models.qgpt_stream_output
import pieces_os_client.models.qgpt_question_answer
import pieces_os_client.models.qgpt_stream_input
import pieces_os_client.models.seeded_connector_connection
import pieces_os_client.models.seeded_tracked_application

# Local
import qt
import data
import purefunctions

if TYPE_CHECKING:
    import pieces_os_client.models
    import pieces_os_client.models.conversation_message
    import pieces_os_client.models.application
    import pieces_os_client.models.relevant_qgpt_seeds
    import pieces_os_client.models.seed
    import pieces_os_client.models.seeds
    import pieces_os_client.models.qgpt_relevance_input
    import pieces_os_client.models.qgpt_question_input
    import pieces_os_client.models.qgpt_question_output
    import pieces_os_client.models.seeded_conversation
    import pieces_os_client.models.conversation

# ^                                          PIECES BRIDGE                                         ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#


class PiecesBridge:
    def __init__(
        self,
        proj_rootpath: Optional[str],
        pieces_client: pieces_os_client.wrapper.PiecesClient,
    ) -> None:
        """The `PiecesBridge()`-instance does all interactions with Pieces OS.

        This is the single point of communication between Embeetle IDE and
        Pieces OS.
        """
        self.__pieces_client = pieces_client
        self.__api_client = self.__pieces_client.api_client
        self.__conversation_message_api = (
            self.__pieces_client.conversation_message_api
        )
        self.__conversation_messages_api = (
            self.__pieces_client.conversation_messages_api
        )
        self.__conversations_api = self.__pieces_client.conversations_api
        self.__conversation_api = self.__pieces_client.conversation_api
        self.__qgpt_api = self.__pieces_client.qgpt_api
        self.__user_api = self.__pieces_client.user_api

        # $ CURRENT CONV
        # Keep a pointer to a conversation that we'll consider to be the 'current conversation'.
        # This is the conversation that is shown currently in Embeetle IDE and that the user is
        # interacting with right now. It starts out as None, and needs to be set explicitely.
        self.__cur_conv: Optional[
            pieces_os_client.models.conversation.Conversation
        ] = None

        # $ CURRENT MODEL
        # The current model is already stored at `self.__pieces_client.model_name` (and also here:
        # `self.__pieces_client.model_id`). However, it starts out from a default value. I want to
        # start from default None, so I keep a flag to indicate if it has been explicitely
        # initialized yet.
        self.__model_initialized = False

        # Keep a status of the latest prompt.
        self.__prompt_status: str = "UNKNOWN"

        self.__proj_rootpath = proj_rootpath

        self.__additional_paths = []
        # self.__pieces_client.ensure_initialization()
        return

    @staticmethod
    def application_to_dict(
        application: pieces_os_client.models.application.Application,
    ) -> dict:
        """"""
        return {
            "id": application.id,
            "name": application.name,
            "version": application.version,
            "platform": application.platform,
            "onboarded": application.onboarded,
            "privacy": application.privacy,
        }

    def get_prompt_status(self) -> str:
        """Get the latest prompt status."""
        return self.__prompt_status

    # % -------------------------------------%#
    # % -           P R O M P T            - %#
    # % -------------------------------------%#
    def prompt_cur_conv(self, message: str) -> Generator[str, None, None]:
        """"""

        def __debug_print(txt: str) -> None:
            # print(f"prompt_cur_conv() -> {txt}")
            return

        # & SET MODEL
        # Should already be done
        if self.get_cur_model_id() is None:
            raise RuntimeError(
                f"prompt_cur_conv() called while current model is None!"
            )
        if self.get_cur_model_name() != self.__pieces_client.model_name:
            raise RuntimeError(
                f"prompt_cur_conv() called with "
                f"self.get_cur_model_name() = '{self.get_cur_model_name()}' and "
                f"self.__pieces_client.model_name = '{self.__pieces_client.model_name}'"
            )
        __debug_print(f"model = " f"{self.get_cur_model_name()}")

        # & SET CURRENT CONVERSATION
        # Check if a current conversation has been selected already by means of the GUI. Then, check
        # if a copilot chat already exists in Pieces. If yes, check if the conversation in that chat
        # matches the one selected by the GUI. Create a new chat with matching conversation id if
        # needed.
        if self.get_cur_conv_id() is None:
            raise RuntimeError(
                f"prompt_cur_conv() called while current conv is None!"
            )
        if self.__pieces_client.copilot.chat is None:
            __debug_print(f"create new chat ...")
            self.__pieces_client.copilot.chat = (
                pieces_os_client.wrapper.basic_identifier.chat.BasicChat(
                    self.get_cur_conv_id()
                )
            )
        else:
            try:
                copilot_chat_conv = (
                    self.__pieces_client.copilot.chat.conversation
                )
                if copilot_chat_conv.id == self.get_cur_conv_id():
                    __debug_print(f"chat matches cur conv")
                else:
                    __debug_print(f"ignore chat, create new chat ...")
                    self.__pieces_client.copilot.chat = pieces_os_client.wrapper.basic_identifier.chat.BasicChat(
                        self.get_cur_conv_id()
                    )
            except ValueError:
                __debug_print(f"ignore chat, create new chat ...")
                self.__pieces_client.copilot.chat = (
                    pieces_os_client.wrapper.basic_identifier.chat.BasicChat(
                        self.get_cur_conv_id()
                    )
                )

        if (
            self.get_cur_conv_id()
            != self.__pieces_client.copilot.chat.conversation.id
        ):
            raise RuntimeError(
                f"prompt_cur_conv() failed to match the chat with the cur conv!"
            )
        __debug_print(
            f"cur conv = "
            f"[name: '{self.__pieces_client.copilot.chat.conversation.name}', "
            f"id: '{self.__pieces_client.copilot.chat.conversation.id}']"
        )

        # & ADD ADDITIONAL PATHS
        for p in self.__additional_paths:
            if p not in self.__pieces_client.copilot.context.paths:
                self.__pieces_client.copilot.context.paths.append(p)
            continue
        __debug_print(
            f"additional paths = "
            f"{self.__pieces_client.copilot.context.paths}"
        )

        # & CHECK CONTEXT
        # __debug_print(f"relevant context = {self.__pieces_client.copilot.relevant_context}")

        # & GET REPLY
        # The copilot `stream_question(..)` method returns a generator that yields instances from
        # `QGPTStreamOutput()`. These instances can hold a part of the answer, but also other
        # things, like:
        #     - A status enum
        #     - The ID of the request (question)
        #     - The ID of the conversation
        #     - ...
        for response in self.__pieces_client.copilot.stream_question(message):
            assert isinstance(
                response,
                pieces_os_client.models.qgpt_stream_output.QGPTStreamOutput,
            )

            # $ STATUS
            if response.status:
                if (
                    response.status
                    == _stream_enum_.QGPTStreamEnum.IN_MINUS_PROGRESS
                ):
                    # Streaming the answer is ongoing.
                    self.__prompt_status = "PROGRESS"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.COMPLETED:
                    # Streaming the answer has completed. However, I never have to act on this
                    # status, because the for-loop stops by itself.
                    self.__prompt_status = "COMPLETED"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.CANCELED:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "CANCELED"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.INITIALIZED:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "INITIALIZED"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.FAILED:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "FAILED"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.UNKNOWN:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "UNKNOWN"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.STOPPED:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "STOPPED"
                    pass
                if response.status == _stream_enum_.QGPTStreamEnum.RESET:
                    # NOT SURE -> never seen this one happening.
                    self.__prompt_status = "RESET"
                    pass

            # $ RELEVANCE
            if response.relevance:
                # NOT SURE -> I read about this relevance-instance: "This will return the snippets
                # that we found are relevant to the query you provided." However, how do I print
                # out those snippets? I've tried a few things but can't seem to find that. I'd like
                # to print them out, so I better understand which snippets Pieces passes to the
                # context window of the LLM.
                pass

            # $ REQUEST
            if response.request:
                # NOT SURE -> I think it is an ID that represents the question.
                pass

            # $ CONVERSATION
            if response.conversation:
                # This must be the ID that belongs to the `Conversation()` we're interacting with.
                assert response.conversation == self.get_cur_conv_id()

            # $ QUESTION - ANSWER
            if response.question:
                # This holds a chunk of the answer. You have to unwrap an interable to get that
                # chunk.
                answers = response.question.answers.iterable
                for answer in answers:
                    assert isinstance(
                        answer,
                        pieces_os_client.models.qgpt_question_answer.QGPTQuestionAnswer,
                    )
                    yield answer.text
                    if (
                        response.status
                        == _stream_enum_.QGPTStreamEnum.COMPLETED
                    ):
                        # Not sure -> I put a print statement here, and it never printed anything.
                        # So perhaps this if-statement can be removed?
                        break
                continue
            continue

        # & RETURN REPLY
        # We get here after the for-loop exhausted the `stream_question(..)` generator. The answer
        # should now be complete and ready to return.
        # Nothing to return -> already yielded the answer snippets!
        return

    def stop_stream(self) -> None:
        """"""
        self.__pieces_client.copilot.ask_stream_ws.send_message(
            pieces_os_client.models.qgpt_stream_input.QGPTStreamInput(
                conversation=self.__pieces_client.copilot._chat_id,
                reset=True,
            )
        )
        return

    def add_additional_paths(self, additional_paths: list[str]) -> None:
        """Add the given additional paths to the context (if they"re not yet in
        there).

        This must happen ONCE PER CONVERSATION. I assume it must also happen
        after every conversation switch.
        """
        for p in additional_paths:
            if p not in self.__additional_paths:
                self.__additional_paths.append(p)
            continue
        return

    # % -------------------------------------%#
    # % -           M O D E L S            - %#
    # % -------------------------------------%#
    def get_all_models_dict(self) -> dict[str, dict[str, str]]:
        """Return a dictionary with all models, the model id being the key in
        the dictionary.

        For
        each model, provide another dictionary that contains the name, id, version, cloud, ...
        parameters.
        """
        return {
            model.id: {
                "id": model.id,
                "name": model.name,
                "version": model.version,
                "cloud": model.cloud,
                "downloaded": model.downloaded,
                "downloading": model.downloading,
            }
            for model in (
                self.__pieces_client.models_api.models_snapshot().iterable
            )
        }

    def get_cur_model_id(self) -> Optional[str]:
        """"""
        if not self.__model_initialized:
            return None
        return self.__pieces_client.model_id

    def get_cur_model_name(self) -> Optional[str]:
        """Get currently used model."""
        if not self.__model_initialized:
            return None
        return self.__pieces_client.model_name

    def set_cur_model(
        self,
        model_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """"""
        # Ensure that only one parameter is used
        assert (
            sum(p is None for p in [model_id, model_name]) == 1
        ), "Exactly one of the parameters (model_id, model_name) must be None"

        # $ `model_id` is entered
        if model_id:
            if model_id == self.get_cur_model_id():
                return
            if model_id not in self.__list_available_model_ids():
                raise RuntimeError(
                    f"set_cur_model('{model_id}') failed "
                    f"because specified model is not available!"
                )
            for (
                model
            ) in self.__pieces_client.models_api.models_snapshot().iterable:
                if model_id == model.id:
                    self.__pieces_client.model_name = model.name
                    self.__model_initialized = True
                    if self.get_cur_conv_id() is not None:
                        self.__store_json_conv_entry(
                            conv_id=self.get_cur_conv_id(),
                            conv_name=self.get_cur_conv_name(),
                            model_id=model.id,
                            model_name=model.name,
                        )
            return

        # $ `model_name` is entered
        if model_name:
            if model_name == self.get_cur_model_name():
                return
            if model_name not in self.__list_available_model_names():
                raise RuntimeError(
                    f"set_cur_model('{model_name}') failed "
                    f"because specified model is not available!"
                )
            self.__pieces_client.model_name = model_name
            self.__model_initialized = True
            model_id = None
            for (
                model
            ) in self.__pieces_client.models_api.models_snapshot().iterable:
                if model_name == model.name:
                    model_id = model.id
                    break
            if model_id is None:
                raise RuntimeError(
                    f"set_cur_model('{model_name}') failed "
                    f"because specified model id could not be determined!"
                )
            if self.get_cur_conv_id() is not None:
                self.__store_json_conv_entry(
                    conv_id=self.get_cur_conv_id(),
                    conv_name=self.get_cur_conv_name(),
                    model_id=model_id,
                    model_name=model_name,
                )
            return

        RuntimeError(f"set_cur_model() called without parameters!")
        return

    def __list_available_model_names(self) -> list[str]:
        """List model names that are either available on the cloud or already
        downloaded."""
        return [
            model.name
            for model in (
                self.__pieces_client.models_api.models_snapshot().iterable
            )
            if model.cloud or model.downloaded
        ]

    def __list_available_model_ids(self) -> list[str]:
        """"""
        return [
            model.id
            for model in (
                self.__pieces_client.models_api.models_snapshot().iterable
            )
            if model.cloud or model.downloaded
        ]

    # % -------------------------------------%#
    # % -    C O N V E R S A T I O N S     - %#
    # % -------------------------------------%#
    def __list_all_convs_instances(
        self,
        project_only: bool,
    ) -> list[pieces_os_client.models.conversation.Conversation]:
        """List all `Conversation()`-instances known to Pieces.

        The `project_only` parameter specifies
        if only those recognized by this Embeetle project must be returned.
        NOTE:
            This function also cleans up json conversation entries that are no longer in Pieces.
        """
        if not project_only:
            return list(
                self.__conversations_api.conversations_snapshot().iterable
            )
        json_dict = self.__load_json_file()

        # $ Empty json dictionary
        # If the json dictionary is empty or has no conversation entries at all, just return an
        # empty list.
        if (json_dict is None) or ("convs" not in json_dict.keys()):
            return []

        # $ Create id lists
        # List of conv ids known by project:
        proj_conv_ids = list(json_dict["convs"].keys())
        if len(proj_conv_ids) == 0:
            return []
        # List of conv ids known by Pieces:
        pieces_conv_ids = [
            conv.id
            for conv in (
                self.__conversations_api.conversations_snapshot().iterable
            )
        ]

        # $ Clean up json conv entries
        # Search for conversation entries in the json dictionary with the intention to clean up
        # those that are no longer known by Pieces.
        for conv_id in proj_conv_ids:
            if conv_id not in pieces_conv_ids:
                self.__del_json_conv_entry(conv_id=conv_id)

        # $ Return relevant conv instances
        # Return those conversation instances that are *both* known by Pieces and the json file.
        return [
            conv
            for conv in (
                self.__conversations_api.conversations_snapshot().iterable
            )
            if conv.id in proj_conv_ids
        ]

    def get_all_convs_dict(
        self, project_only: bool
    ) -> dict[str, dict[str, str]]:
        """"""
        return {
            conv.id: {
                "id": conv.id,
                "name": conv.name,
            }
            for conv in self.__list_all_convs_instances(
                project_only=project_only
            )
        }

    def create_conv(
        self,
        name: Optional[str] = None,
    ) -> Optional[pieces_os_client.models.conversation.Conversation]:
        """Create and return new `Conversation()`-instance with the given name.
        Return None if making the new conversation failed.

        WARNING:
            The new conversation is not automatically declared to be the 'current' one! You still
            need to call the `set_current_conversation(..)` method for that.
        """
        if (name is None) or name.strip() == "":
            print(
                f"WARNING: create_conversation() called without a name! Use fallback name."
            )
            name = "nameless"
        try:
            # $ Create new conversation
            new_conversation: (
                pieces_os_client.models.conversation.Conversation
            ) = self.__conversations_api.conversations_create_specific_conversation(
                seeded_conversation=pieces_os_client.models.seeded_conversation.SeededConversation.from_dict(
                    {
                        "name": name,
                        "type": "COPILOT",
                    }
                )
            )
            # $ Store conversation id in project
            self.__store_json_conv_entry(
                conv_id=new_conversation.id,
                conv_name=new_conversation.name,
                model_id=self.get_cur_model_id(),
                model_name=self.get_cur_model_name(),
            )
            return new_conversation
        except:
            print(f"ERROR: Cannot create conversation '{name}'")
            traceback.print_exc()
        return None

    def get_cur_conv_id(self) -> Optional[StrictStr]:
        """"""
        if self.__cur_conv is None:
            return None
        return self.__cur_conv.id

    def get_cur_conv_name(self) -> Optional[str]:
        """"""
        if self.__cur_conv is None:
            return None
        return self.__cur_conv.name

    def set_cur_conv(
        self,
        conv: Optional[
            pieces_os_client.models.conversation.Conversation
        ] = None,
        conv_id: Optional[str] = None,
        conv_name: Optional[str] = None,
    ) -> Optional[str]:
        """Set the current conversation based on one of the parameters (only one
        parameter should be used).

        NOTE:
            This method also stores an entire conversation-entry to the json file. But before that,
            it checks if the conversation was already stored earlier. If so, it extracts the model
            that was used back then and returns that. The code calling this method *might* or *might
            not* switch to that earlier model - depending on the policy.

        :return:    previous_model_id - The id of the model that was used for this particular
                                        conversation last time it was opened. Can be None.
        """
        # Ensure that only one parameter is used
        assert (
            sum(p is None for p in [conv, conv_id, conv_name]) == 2
        ), "Exactly two of the parameters (conv, conv_id, conv_name) must be None"

        def __get_conv_id(
            _conv: Optional[pieces_os_client.models.conversation.Conversation],
            _conv_id: Optional[str],
            _conv_name: Optional[str],
        ) -> Optional[str]:
            """Extract `conv_id` from the parameters."""
            if _conv:
                return _conv.id
            if _conv_id:
                return _conv_id
            for c in self.__list_all_convs_instances(project_only=True):
                if c.name.strip() == _conv_name.strip():
                    return c.id
            return None

        # $ Determine conv_id
        # Determine the conversation id - regardless of the parameter that was provided.
        conv_id = __get_conv_id(
            _conv=conv, _conv_id=conv_id, _conv_name=conv_name
        )
        if conv_id is None:
            raise RuntimeError(
                f"set_cur_conv({conv}, {conv_id}, {conv_name}) failed to find the conversation!"
            )

        # $ Find old model
        # Try to figure out if the conversation we're gonna switch to is known by the json-file, and
        # if it was tied to a specific model.
        previous_model_id: Optional[str] = None
        conv_entry = self.__get_json_conv_entry(conv_id=conv_id)
        if conv_entry is not None:
            previous_model_id = conv_entry["model_id"]

        if conv_id == self.get_cur_conv_id():
            return previous_model_id
        for conv in self.__list_all_convs_instances(project_only=True):
            if conv.id == conv_id:
                self.__cur_conv = conv
                self.__store_json_conv_entry(
                    conv_id=self.__cur_conv.id,
                    conv_name=self.__cur_conv.name,
                    model_id=self.get_cur_model_id(),
                    model_name=self.get_cur_model_name(),
                )
                return previous_model_id
            continue
        RuntimeError(f"Cannot find given conversation '{conv_id}' in the list!")
        return previous_model_id

    def delete_conv(
        self,
        conv: Optional[
            pieces_os_client.models.conversation.Conversation
        ] = None,
        conv_id: Optional[StrictStr] = None,
        conv_name: Optional[str] = None,
    ) -> None:
        """Loop over the stored conversations and match their names with the
        given one. Delete the conversation with a matching name.

        :return:    True  - Deletion succeeded
                    False - Deletion failed
        """
        # Ensure that only one parameter is used
        assert (
            sum(p is None for p in [conv, conv_id, conv_name]) == 2
        ), "Exactly two of the parameters (conv, conv_id, conv_name) must be None"

        # $ `conv` is entered
        if conv:
            if conv not in self.__list_all_convs_instances(project_only=False):
                RuntimeError(
                    f"delete_conv() called with non-existing conversation!"
                )
            if conv.id == self.get_cur_conv_id():
                self.__cur_conv = None
            self.__conversations_api.conversations_delete_specific_conversation(
                conv.id
            )
            self.__del_json_conv_entry(conv_id=conv.id)
            return

        # $ `conv_id` is entered
        if conv_id:
            for conv in self.__list_all_convs_instances(project_only=False):
                if conv.id == conv_id:
                    break
                continue
            else:
                RuntimeError(
                    f"delete_conv() called with non-existing conversation!"
                )
            if conv_id == self.get_cur_conv_id():
                self.__cur_conv = None
            self.__conversations_api.conversations_delete_specific_conversation(
                conv_id
            )
            self.__del_json_conv_entry(conv_id=conv_id)
            return

        # $ `conv_name` is entered
        if conv_name:

            def name_match(_name1: str, _name2: str) -> bool:
                _name1 = _name1.strip() if _name1 else ""
                _name2 = _name2.strip() if _name2 else ""
                return _name1 == _name2

            conv_id = None
            for conv in self.__list_all_convs_instances(project_only=False):
                if name_match(conv_name, conv.name):
                    conv_id = conv.id
                    break
                continue
            else:
                RuntimeError(
                    f"delete_conv() called with non-existing conversation!"
                )
            if conv_id == self.get_cur_conv_id():
                self.__cur_conv = None
            self.__conversations_api.conversations_delete_specific_conversation(
                conv_id
            )
            self.__del_json_conv_entry(conv_id=conv_id)
            return

        RuntimeError("delete_conv() called without arguments!")
        return

    def get_cur_conv_raw_messages(self) -> list[dict[str, Union[str, bool]]]:
        """Get the raw messages from the current conversation, in the following
        format:

        raw_messages = [
            {
                "message"         : "This is the first user message",
                "is_user_message" : True,
            },
            {
                "message"         : "This is the first AI reply",
                "is_user_message" : False,
            },
            ...
        ]
        """
        if self.get_cur_conv_id() is None:
            raise RuntimeError(
                f"get_cur_conv_raw_messages() called while current conv is None!"
            )
        try:
            # $ Obtain Conversation()-instance
            conversation: pieces_os_client.models.conversation.Conversation = (
                self.__conversation_api.conversation_get_specific_conversation(
                    conversation=self.get_cur_conv_id(),
                )
            )

            # $ Return with raw messages
            raw_messages = []
            for message_id, index in (
                conversation.messages.indices or {}
            ).items():
                message_response: (
                    pieces_os_client.models.conversation_message.ConversationMessage
                ) = self.__conversation_message_api.message_specific_message_snapshot(
                    message=StrictStr(message_id),
                )
                if (
                    not message_response.fragment
                    or not message_response.fragment.string
                    or not message_response.fragment.string.raw
                ):
                    continue
                raw_messages.append(
                    {
                        "message": message_response.fragment.string.raw,
                        "is_user_message": message_response.role == "USER",
                    }
                )
            return raw_messages
        except:
            print(
                f"ERROR: Cannot extract raw messages from '{self.get_cur_conv_name()}'"
            )
            traceback.print_exc()
        return []

    # % -------------------------------------%#
    # % -     J S O N    S T O R A G E     - %#
    # % -------------------------------------%#
    def __store_json_file(self, json_dict: dict) -> None:
        """Store the given dict as 'pieces_ai.json5'.

        WARNING:
            Overwrites anything already stored there!
        """
        purefunctions.write_json_file(
            filepath=f"{self.__proj_rootpath}/.beetle/pieces_ai.json5",
            json_dict=json_dict,
        )
        return

    def __load_json_file(self) -> dict[str, dict[str, dict[str, str]]]:
        """
        Load the content of the 'pieces_ai.json5' file. If doesn't exist, just return an empty dict.
        The json dict should look like this:

        json_dict = {
            "convs" : {
                "<conv_id>" : {
                    "name"       : "<conv_name>",  # Conversation Name
                    "model_id"   : "<model_id>",   # Last used model (id)
                    "model_name" : "<model_name>", # Last used model (name)
                },
                ...
            },
        }
        """
        storage_location = f"{self.__proj_rootpath}/.beetle/pieces_ai.json5"
        if not os.path.isfile(storage_location):
            return {}
        json_dict: Optional[dict] = purefunctions.load_json_file_with_comments(
            storage_location
        )
        if json_dict is None:
            return {}
        return json_dict

    def __get_json_conv_entry(self, conv_id: str) -> Optional[dict[str, str]]:
        """Extract the conversation entry from the json file.

        If not found, return None.
        """
        json_dict = self.__load_json_file()
        if "convs" not in json_dict.keys():
            json_dict["convs"] = {}
        if conv_id not in json_dict["convs"].keys():
            return None
        return json_dict["convs"][conv_id]

    def __store_json_conv_entry(
        self,
        conv_id: str,
        conv_name: str,
        model_id: Optional[str],
        model_name: Optional[str],
    ) -> None:
        """
        Store the given conversation, along with the specified model, to the json file.
        WARNING:
            It will overwrite a conversation in the json file if the id matches!

        CALLED:
            - Create new conversation
            - Switch current conversation (model might need an update in the entry)
            - Switch current model (model might need an update in the entry, if cur conv exists)
        """
        json_dict = self.__load_json_file()
        if "convs" not in json_dict.keys():
            json_dict["convs"] = {}
        if conv_id not in json_dict["convs"].keys():
            json_dict["convs"][conv_id] = {}
        json_dict["convs"][conv_id]["name"] = conv_name
        json_dict["convs"][conv_id]["model_id"] = model_id
        json_dict["convs"][conv_id]["model_name"] = model_name
        self.__store_json_file(json_dict)
        return

    def __del_json_conv_entry(self, conv_id: str) -> None:
        """Delete the specified conversation entry from the json file."""
        json_dict = self.__load_json_file()
        if "convs" not in json_dict.keys():
            json_dict["convs"] = {}
        if conv_id in json_dict["convs"].keys():
            del json_dict["convs"][conv_id]
        self.__store_json_file(json_dict)
        return


# ^                                      PIECES COMMUNICATOR                                       ^#
# % ============================================================================================== %#
# %                                                                                                %#
# %                                                                                                %#
# The `PiecesWindow()` instantiates this `PiecesCommunicator()` class once and then uses it for all
# its interactions with Pieces OS. In the constructor from `PiecesCommunicator()`, two processes
# are spawn:
#     1. pieces_start_process() function - runs in entirely different process
#     2. self.PTG_receive_loop() method - runs in a Thread()
# 1. The proces loop continuously interacts with the send and receive queues.
# 2. The receive loop interacts with the receive queue only.
# GUI-TO-PIECES
# -------------
# The methods in this `PiecesCommunicator()` class start with 'GTP_', which means: 'GUI-TO-PIECES'.
# They are methods that the GUI can call directly to send something to Pieces. These methods then
# stuff that in the `GTP_queue`.
# PIECES-TO-GUI
# -------------
# The loop in `pieces_start_process()` stuffs things back into the reversed queue: `PTG_queue`.
# The packets in that queue get read continuously in the `self.PTG_receive_loop()` method, from
# where it then reaches the GUI through the signal-slot-mechanism.


class PiecesCommunicator(qt.QObject):
    pieces_packet_received_signal = qt.pyqtSignal(dict)

    def __init__(
        self,
        proj_rootpath: str,
        pieces_packet_received_slot: Callable,
    ) -> None:
        """"""
        super().__init__()
        self.__closed = False
        self.pieces_packet_received_signal.connect(pieces_packet_received_slot)

        # Queues and stop event
        self.GTP_queue = multiprocessing.Queue()
        self.PTG_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

        # & Process for communicating with Pieces server
        self.communication_process = multiprocessing.Process(
            target=pieces_start_process,
            args=(
                self.GTP_queue,
                self.PTG_queue,
                self.stop_event,
                proj_rootpath,
            ),
            daemon=True,
        )
        self.communication_process.start()

        # & Start the receiving Thread
        self.receiving_thread = threading.Thread(
            target=self.PTG_receive_loop,
            args=(
                self.PTG_queue,
                self.stop_event,
            ),
            daemon=True,
        )
        self.receiving_thread.start()
        return

    def __del__(self) -> None:
        """"""
        self.close()
        return

    def PTG_receive_loop(
        self,
        PTG_queue: multiprocessing.Queue,
        stop_event: multiprocessing.Event,
    ) -> None:
        """"""
        while not stop_event.is_set():
            try:
                pieces_packet = PTG_queue.get(timeout=0.1)
                self.pieces_packet_received_signal.emit(pieces_packet)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Exception in self.receiving_thread: {e}")
                break
            continue
        return

    def close(self) -> None:
        """Stop and close both `self.communication_process` and
        `self.receiving_thread` in a clean way."""
        # Make sure this method can only run once.
        if self.__closed:
            return
        self.__closed = True

        # NOTE:
        # When closing down Embeetle, many of the following statements might throw an OSError:
        #     On Windows: 'OSError: [WinError 6] The handle is invalid'
        #     On Linux:   'OSError: [Errno 9] Bad file descriptor'
        # Ignore those.

        # $ STEP 1: Signal Process and Thread to Stop
        # Fire stop event such that `self.communication_process` and `self.receiving_thread` both
        # exit their loops and hit the `return` statement. Wait a moment to give them that chance.
        try:
            self.stop_event.set()
            time.sleep(1)
        except OSError:
            pass

        # $ STEP 2: Flush Queues
        # Flush the queues prior to calling `join()` on the process and thread.
        try:
            try:
                while not self.GTP_queue.empty():
                    self.GTP_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                while not self.PTG_queue.empty():
                    self.PTG_queue.get_nowait()
            except queue.Empty:
                pass
        except OSError:
            pass

        # $ STEP 3: Join `self.receiving_thread`
        # Wait for `self.receiving_thread` to finish.
        try:
            self.receiving_thread.join(timeout=2)
            if self.receiving_thread.is_alive():
                print("ERROR: self.receiving_thread did not exit in time!")
        except OSError:
            pass

        # $ STEP 4: Close and Join Queues
        # Each queue spawns a background thread to handle messages (this is default Python
        # implementation). These background threads should be stopped.
        try:
            self.GTP_queue.close()
            self.GTP_queue.join_thread()
            self.PTG_queue.close()
            self.PTG_queue.join_thread()
        except OSError:
            pass
        except:
            traceback.print_exc()

        # $ STEP 5: Join `self.communication_process`
        # Wait for `self.communication_process` to finish.
        try:
            self.communication_process.join(timeout=2)
            if self.communication_process.is_alive():
                print(
                    "ERROR: self.communication_process did not exit in time! Terminate it..."
                )
                self.communication_process.terminate()
                self.communication_process.join()
        except OSError:
            pass

        # $ STEP 6: Disconnect Signals
        try:
            if not qt.sip.isdeleted(self):
                self.pieces_packet_received_signal.disconnect()
        except OSError:
            pass
        except:
            pass
        return

    def GTP_ask_question(self, question: str) -> None:
        """"""
        send_data = {
            "type": MessageType.GTP_Question,
            "data": {
                "question": question,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_stop_stream(self) -> None:
        """"""
        send_data = {
            "type": MessageType.GTP_StopStream,
            "data": {},
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_add_paths(self, additional_paths: Optional[list] = None) -> None:
        """"""
        if additional_paths is None:
            return
        send_data = {
            "type": MessageType.GTP_AddPaths,
            "data": {
                "additional-paths": additional_paths,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_create_conversation(self, conversation_name: str) -> None:
        """Invoked by the "Create New Conversation" popup."""
        send_data = {
            "type": MessageType.GTP_CreateConversation,
            "data": {
                "conversation-name": conversation_name,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_select_conversation_by_name(self, conv_name: str) -> None:
        """Invoked if you created a new conversation with the "Create New
        Conversation" popup (after the previous function completes)."""
        send_data = {
            "type": MessageType.GTP_SelectConversation,
            "data": {
                "conv-name": conv_name,
                "conv-id": None,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_select_conversation_by_id(self, conv_id: str) -> None:
        """Invoked if you select another conversation from the dropdown."""
        send_data = {
            "type": MessageType.GTP_SelectConversation,
            "data": {
                "conv-name": None,
                "conv-id": conv_id,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_reload_conversation(self) -> None:
        """"""
        send_data = {
            "type": MessageType.GTP_ReloadConversation,
            "data": {},
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_delete_conversation(self, conv_id: str) -> None:
        """Invoked by the "Delete Current Conversation" popup."""
        send_data = {
            "type": MessageType.GTP_DeleteConversation,
            "data": {
                "conv-name": None,
                "conv-id": conv_id,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_select_model_by_name(self, model_name: str) -> None:
        """"""
        send_data = {
            "type": MessageType.GTP_SelectModel,
            "data": {
                "model-name": model_name,
                "model-id": None,
            },
        }
        self.GTP_queue.put(send_data)
        return

    def GTP_select_model_by_id(self, model_id: str) -> None:
        """"""
        send_data = {
            "type": MessageType.GTP_SelectModel,
            "data": {
                "model-name": None,
                "model-id": model_id,
            },
        }
        self.GTP_queue.put(send_data)
        return


class MessageType(enum.Enum):
    # GUI-TO-PIECES Messages
    GTP_CreateConversation = enum.auto()
    GTP_DeleteConversation = enum.auto()
    GTP_SelectConversation = enum.auto()
    GTP_ReloadConversation = enum.auto()
    GTP_Question = enum.auto()
    GTP_SelectModel = enum.auto()
    GTP_AddPaths = enum.auto()
    GTP_StopStream = enum.auto()

    # PIECES-TO-GUI Messages
    PTG_ConvsComboboxUpdate = enum.auto()
    PTG_ModelsComboboxUpdate = enum.auto()
    PTG_PiecesInitialized = enum.auto()
    PTG_ConversationCreated = enum.auto()
    PTG_MessagesLoaded = enum.auto()
    PTG_Answer = enum.auto()
    PTG_StartAnswerGeneration = enum.auto()
    PTG_AnswerSnippet = enum.auto()
    PTG_FinishAnswerGeneration = enum.auto()
    PTG_ServerError = enum.auto()
    PTG_NoConversationsAvailable = enum.auto()
    PTG_StreamStopped = enum.auto()


def pieces_start_process(
    GTP_queue: multiprocessing.Queue,
    PTG_queue: multiprocessing.Queue,
    stop_event: multiprocessing.Event,
    proj_rootpath: str,
) -> None:
    """"""
    import queue
    import concurrent.futures

    pieces_bridge: Optional[PiecesBridge] = None
    pieces_client: Optional[pieces_os_client.wrapper.PiecesClient] = None

    def __debug_print(txt: str) -> None:
        """Print debug messages."""
        # print(txt)
        return

    def __exit() -> None:
        """Exit this process in a clean way."""
        if pieces_client is not None:
            pieces_client.close()
        # Flush Queues
        try:
            while not GTP_queue.empty():
                GTP_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            while not PTG_queue.empty():
                PTG_queue.get_nowait()
        except queue.Empty:
            pass
        # Close and Join Queues
        try:
            GTP_queue.close()
            GTP_queue.join_thread()
            PTG_queue.close()
            PTG_queue.join_thread()
        except:
            traceback.print_exc()
        return

    def __check_if_stop_stream_msg_in_queue() -> bool:
        """Check if a GTP_StopStream message is in the GTP_queue."""
        _stop_stream = False
        temp_list = []
        # Exhaust the queue, check if a stop stream message is in there and keep all others in a
        # temporary list, to refill the queue afterwards.
        try:
            while True:
                _gui_packet = GTP_queue.get_nowait()
                if _gui_packet["type"] == MessageType.GTP_StopStream:
                    __debug_print(f">>> MessageType.GTP_StopStream")
                    # Discard this packet, but keep in mind that a stop stream was invoked!
                    _stop_stream = True
                    continue
                temp_list.append(_gui_packet)
                continue
        except queue.Empty:
            pass
        # Re-queue the items we want to keep
        for _gui_packet in temp_list:
            GTP_queue.put(_gui_packet)
            continue
        # Return the result of the search
        return _stop_stream

    # * ----------------------------------[ INITIALIZE PROCESS ]---------------------------------- *#
    # Initizalize the server connection and the bridge to Pieces. Then send the following three
    # messages:
    #     1. Update the Conversations Combobox
    #     2. Update the Models Combobox
    #     3. Pieces is Initialized

    # Make one PiecesClient()-instance that will be used throughout the entire program.

    if os_checker.is_os("windows"):
        pf = "WINDOWS"
    elif os_checker.is_os("linux"):
        pf = "LINUX"
    elif os_checker.is_os("macos"):
        pf = "MACOS"
    else:
        pf = "WEB"
    pieces_client = pieces_os_client.wrapper.PiecesClient(
        seeded_connector=pieces_os_client.models.seeded_connector_connection.SeededConnectorConnection(
            application=pieces_os_client.models.seeded_tracked_application.SeededTrackedApplication(
                name="EMBEETLE",
                platform=pf,
                version="1.13.0",
            ),
        ),
    )
    if not is_server_listening(pieces_client):
        # $ INFORM GUI: MessageType.PTG_ServerError
        __debug_print(f"<<< PTG_queue.put(MessageType.PTG_ServerError)")
        PTG_queue.put(
            {
                "type": MessageType.PTG_ServerError,
                "data": None,
            }
        )
        __exit()
        return

    # Make one PiecesBridge()-instance that will be used throughout the entire program. It must be
    # based on the one PiecesClient()-instance.
    pieces_bridge = PiecesBridge(proj_rootpath, pieces_client)

    # $ INFORM GUI: MessageType.PTG_ConvsComboboxUpdate
    __debug_print(f"<<< PTG_queue.put(MessageType.PTG_ConvsComboboxUpdate)")
    PTG_queue.put(
        {
            "type": MessageType.PTG_ConvsComboboxUpdate,
            "data": {
                "cur-conv-name": None,
                "cur-conv-id": None,
                "all-convs-dict": pieces_bridge.get_all_convs_dict(
                    project_only=True
                ),
            },
        }
    )

    # $ INFORM GUI: MessageType.PTG_ModelsComboboxUpdate
    __debug_print(f"<<< PTG_queue.put(MessageType.PTG_ModelsComboboxUpdate)")
    PTG_queue.put(
        {
            "type": MessageType.PTG_ModelsComboboxUpdate,
            "data": {
                "cur-model-name": None,
                "cur-model-id": None,
                "all-models-dict": pieces_bridge.get_all_models_dict(),
            },
        }
    )

    # $ INFORM GUI: MessageType.PTG_PiecesInitialized
    __debug_print(f"<<< PTG_queue.put(MessageType.PTG_PiecesInitialized)")
    PTG_queue.put(
        {
            "type": MessageType.PTG_PiecesInitialized,
            "data": {},
        }
    )

    # * -----------------------------------------[ LOOP ]----------------------------------------- *#
    # At this point we know that the current conversation is up-and-running. Now enter the loop.
    while not stop_event.is_set():
        try:
            gui_packet = GTP_queue.get(timeout=0.2)

            # & FROM GUI: MessageType.GTP_StopStream
            # If a stop stream message is catched here, it must be a leftover. They are only
            # relevant once an answer is being formed while exhausting the generator object returned
            # by the prompt.
            if gui_packet["type"] == MessageType.GTP_StopStream:
                __debug_print(f">>> MessageType.GTP_StopStream [ignored]")

            # & FROM GUI: MessageType.GTP_CreateConversation
            # The GUI requests the creation of a new conversation, and provides a name for it.
            # Create the new conversation and report back to the GUI that this succeeded.
            # NOTE:
            # Do not yet specify this new conversation as the 'current' one. There is a follow-up
            # message coming from the GUI for that: MessageType.SelectConversation
            elif gui_packet["type"] == MessageType.GTP_CreateConversation:
                __debug_print(f">>> MessageType.GTP_CreateConversation")
                conversation_name = gui_packet["data"]["conversation-name"]
                new_conv_instance = pieces_bridge.create_conv(
                    name=conversation_name,
                )
                if new_conv_instance is None:
                    raise RuntimeError(f"Failed to create new conversation!")
                if conversation_name != new_conv_instance.name:
                    raise RuntimeError(
                        f"Newly created conversation '{new_conv_instance.name}' doesn't match the "
                        f"requested name '{conversation_name}'"
                    )
                # $ INFORM GUI: MessageType.PTG_ConversationCreated
                __debug_print(f"<<< MessageType.PTG_ConversationCreated")
                # The GUI will set a flag to fire the first prompt as soon as the messages have
                # been loaded.
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_ConversationCreated,
                        "data": {},
                    }
                )

            # & FROM GUI: MessageType.GTP_SelectConversation
            # The GUI requests the selection of a specific conversation. Do that, then request from
            # the 'PiecesBridge()' the raw messages from this newly selected conversation and pass
            # them back to the GUI, so the GUI can load them on the display.
            elif gui_packet["type"] == MessageType.GTP_SelectConversation:
                __debug_print(f">>> MessageType.GTP_SelectConversation")
                if gui_packet["data"]["conv-id"]:
                    previous_model_id = pieces_bridge.set_cur_conv(
                        conv_id=gui_packet["data"]["conv-id"]
                    )
                elif gui_packet["data"]["conv-name"]:
                    previous_model_id = pieces_bridge.set_cur_conv(
                        conv_name=gui_packet["data"]["conv-name"]
                    )
                else:
                    raise RuntimeError(
                        f"MessageType.GTP_SelectConversation doesn't provide conversation to "
                        f"switch to!"
                    )
                # $ INFORM GUI: MessageType.PTG_MessagesLoaded
                # Inform the GUI that the requested conversation has been selected and pass it all
                # the raw messages. Also, pass it the currently selected model, but first check if
                # the current model should be switched. Only if the current model is None, switch to
                # whatever used to be the model for this conversation. Otherwise, keep the current
                # model unchanged.
                __debug_print(f"<<< MessageType.PTG_MessagesLoaded")
                cur_model_id = pieces_bridge.get_cur_model_id()
                if (cur_model_id is None) and (previous_model_id is not None):
                    pieces_bridge.set_cur_model(model_id=previous_model_id)
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_MessagesLoaded,
                        "data": {
                            # Conversations
                            "cur-conv-name": pieces_bridge.get_cur_conv_name(),
                            "cur-conv-id": pieces_bridge.get_cur_conv_id(),
                            "all-convs-dict": pieces_bridge.get_all_convs_dict(
                                project_only=True
                            ),
                            # Models
                            "cur-model-name": (
                                pieces_bridge.get_cur_model_name()
                            ),
                            "cur-model-id": pieces_bridge.get_cur_model_id(),
                            "all-models-dict": (
                                pieces_bridge.get_all_models_dict()
                            ),
                            # Raw Messages
                            "raw-messages": (
                                pieces_bridge.get_cur_conv_raw_messages()
                            ),
                        },
                    }
                )

            # & FROM GUI: MessageType.GTP_ReloadConversation
            # The GUI requests to reload the conversation. This typically happens when the user
            # changes the theme. Then all chat bubbles are in the wrong color. So it's best to clear
            # the entire chat display and start over.
            elif gui_packet["type"] == MessageType.GTP_ReloadConversation:
                __debug_print(f">>> MessageType.GTP_ReloadConversation")
                # $ INFORM GUI: MessageType.PTG_MessagesLoaded
                __debug_print(f"<<< MessageType.PTG_MessagesLoaded")
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_MessagesLoaded,
                        "data": {
                            # Conversations
                            "cur-conv-name": pieces_bridge.get_cur_conv_name(),
                            "cur-conv-id": pieces_bridge.get_cur_conv_id(),
                            "all-convs-dict": pieces_bridge.get_all_convs_dict(
                                project_only=True
                            ),
                            # Models
                            "cur-model-name": (
                                pieces_bridge.get_cur_model_name()
                            ),
                            "cur-model-id": pieces_bridge.get_cur_model_id(),
                            "all-models-dict": (
                                pieces_bridge.get_all_models_dict()
                            ),
                            # Raw Messages
                            "raw-messages": (
                                pieces_bridge.get_cur_conv_raw_messages()
                            ),
                        },
                    }
                )

            # & FROM GUI: MessageType.GTP_AddPaths
            # The GUI wants to add additional paths to the context. This typically happens before
            # a question is asked (although it's a bit overkill to repeat it before every question).
            elif gui_packet["type"] == MessageType.GTP_AddPaths:
                __debug_print(f">>> MessageType.GTP_AddPaths")
                pieces_bridge.add_additional_paths(
                    gui_packet["data"]["additional-paths"]
                )

            # & FROM GUI: MessageType.GTP_Question
            # The GUI sends a question for Pieces AI. Prompt the current conversation with that
            # question and send back the response to the GUI.
            elif gui_packet["type"] == MessageType.GTP_Question:
                __debug_print(f">>> MessageType.GTP_Question")
                response_gen = pieces_bridge.prompt_cur_conv(
                    gui_packet["data"]["question"]
                )
                # $ INFORM GUI: MessageType.PTG_StartAnswerGeneration
                __debug_print(f"<<< MessageType.PTG_StartAnswerGeneration")
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_StartAnswerGeneration,
                        "data": None,
                    }
                )

                # $ INFORM GUI: MessageType.PTG_AnswerSnippet [repeat ...]
                # Extract snippets from the `response_gen` generator and send them back to the GUI.
                # Meanwhile, also check if the GUI fired a 'stop stream' message. So we'll have to
                # check for that regularly, therefore we need a trick to poll the generator object
                # with a timeout.
                __debug_print(f"<<< MessageType.PTG_AnswerSnippet [repeat ...]")
                answer_list = []
                gen_iter = iter(response_gen)
                stream_stopped = False
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=1
                ) as executor:
                    future = None
                    while True:
                        if future is None:
                            # We only submit a new `next()` call if `future` is `None`, meaning
                            # there's no pending call. This ensures that at any given time, there's
                            # at most one `next()` call in progress.
                            # By not submitting new `next()` calls until the previous one has
                            # finished, we prevent overlapping calls that could cause the generator
                            # to skip items. This approach maintains the correct sequence of items
                            # from the generator.
                            future = executor.submit(
                                next, gen_iter, None
                            )  # noqa
                        try:
                            # Try to get the result of the future with a timeout. If it completes
                            # within the timeout, we process the `answer_snippet` and set future
                            # back to `None` to indicate readiness for a new `next()` call in the
                            # next iteration.
                            answer_snippet = future.result(timeout=0.3)
                            future = None
                            if answer_snippet is None:
                                # Generator is exhausted. Break out of the `while True` loop.
                                break
                            # We have a snippet. Store it and also send it back to the GUI.
                            answer_list.append(answer_snippet)
                            PTG_queue.put(
                                {
                                    "type": MessageType.PTG_AnswerSnippet,
                                    "data": {
                                        "answer-snippet": answer_snippet,
                                    },
                                }
                            )
                        except concurrent.futures.TimeoutError:
                            # If the `future` doesn't complete within the timeout, we catch the
                            # `TimeoutError` and leave the `future` as is (the pending `next()` call
                            # continues running).
                            pass
                        finally:
                            # This runs every iteration of the `while True` loop. Before extracting
                            # another snippet from the `response_gen` generator, let's first check
                            # if the GUI fired a stop stream message. This function to check the
                            # queue for such message(s) will leave the other elements in the queue
                            # (if any) unharmed.
                            if __check_if_stop_stream_msg_in_queue():
                                pieces_bridge.stop_stream()
                                stream_stopped = True
                        continue
                    # -- end of with -- #

                # $ INFORM GUI: MessageType.PTG_FinishAnswerGeneration
                __debug_print(f"<<< MessageType.PTG_FinishAnswerGeneration")
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_FinishAnswerGeneration,
                        "data": {
                            "complete-answer": "".join(answer_list),
                            "prompt-status": pieces_bridge.get_prompt_status(),
                        },
                    }
                )

                # $ INFORM GUI: MessageType.PTG_StreamStopped
                if stream_stopped:
                    # Stopping the stream causes all kinds of side-effects. Therefore, I prefer to
                    # reset everything. Let the GUI take care of that. Just inform the GUI that the
                    # stream has stopped, so it knows what to do next.
                    PTG_queue.put(
                        {
                            "type": MessageType.PTG_StreamStopped,
                            "data": {},
                        }
                    )

            # & FROM GUI: MessageType.GTP_SelectModel
            # The GUI requests to select another model. Pass the model name to `PiecesBridge()`,
            # where it gets checked for availability before it's actually applied.
            elif gui_packet["type"] == MessageType.GTP_SelectModel:
                __debug_print(f">>> MessageType.GTP_SelectModel")
                if gui_packet["data"]["model-id"]:
                    pieces_bridge.set_cur_model(
                        model_id=gui_packet["data"]["model-id"]
                    )
                elif gui_packet["data"]["model-name"]:
                    pieces_bridge.set_cur_model(
                        model_name=gui_packet["data"]["model-name"]
                    )

            # & FROM GUI: MessageType.GTP_DeleteConversation
            # The GUI requests to delete the current conversation.
            # NOTE:
            # Do not yet switch to another 'current' conversation here.
            elif gui_packet["type"] == MessageType.GTP_DeleteConversation:
                __debug_print(f">>> MessageType.GTP_DeleteConversation")
                if gui_packet["data"]["conv-id"]:
                    if (
                        gui_packet["data"]["conv-id"]
                        != pieces_bridge.get_cur_conv_id()
                    ):
                        raise RuntimeError(
                            f"Request to delete current conversation, but ids don't match: "
                            f"{gui_packet['data']['conv-id']} - "
                            f"{pieces_bridge.get_cur_conv_id()}"
                        )
                    pieces_bridge.delete_conv(
                        conv_id=gui_packet["data"]["conv-id"]
                    )
                elif gui_packet["data"]["conv-name"]:
                    if (
                        gui_packet["data"]["conv-name"]
                        != pieces_bridge.get_cur_conv_name()
                    ):
                        raise RuntimeError(
                            f"Request to delete current conversation, but names don't match: "
                            f"{gui_packet['data']['conv-name']} - "
                            f"{pieces_bridge.get_cur_conv_name()}"
                        )
                    pieces_bridge.delete_conv(
                        conv_name=gui_packet["data"]["conv-name"]
                    )
                # $ INFORM GUI: MessageType.PTG_ConvsComboboxUpdate
                # As the current conversation is deleted, Pieces should give an update for the GUI's
                # combobox and let it know that no conversation is selected right now.
                __debug_print(
                    f"<<< PTG_queue.put(MessageType.PTG_ConvsComboboxUpdate)"
                )
                assert pieces_bridge.get_cur_conv_id() is None
                PTG_queue.put(
                    {
                        "type": MessageType.PTG_ConvsComboboxUpdate,
                        "data": {
                            "cur-conv-name": None,
                            "cur-conv-id": None,
                            "all-convs-dict": pieces_bridge.get_all_convs_dict(
                                project_only=True
                            ),
                        },
                    }
                )

            else:
                __debug_print(f"ERROR: unknown packet: {gui_packet['type']}")

        except queue.Empty:
            continue
        except queue.Full:
            print("ERROR: Queue is full. Skipping messages")
            continue
        except:
            traceback.print_exc()
            break
        continue

    __exit()
    return


def is_server_listening(
    pieces_client: pieces_os_client.wrapper.PiecesClient,
) -> bool:
    """"""
    is_pos_stream_running = pieces_client.is_pos_stream_running
    if is_pos_stream_running:
        # running fine no problem
        return True
    else:
        # Let's send a request to double check
        if pieces_client.is_pieces_running():
            # it is running so let's open the websockets
            pieces_os_client.wrapper.websockets.base_websocket.BaseWebsocket.start_all()
            return True
        else:
            return False
    return False
