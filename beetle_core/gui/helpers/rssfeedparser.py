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

import os
import sys
import time
import urllib
import datetime
import functools
import threading
import traceback
import feedparser
import qt
import data
import functions
import iconfunctions
import purefunctions
import gui.templates.widgetgenerator
import gui.forms.messagewindow
import gui.helpers.buttons
from various.kristofstuff import *

# Setup the SSL certificate
import ssl

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


class RSSFeedParser(qt.QGroupBox, gui.templates.baseobject.BaseObject):
    __feed_url: str
    __feed_cache: str
    __feed_list: list
    __button_list: list
    __feed_index: int
    __icon_on = None
    __icon_off = None
    __state = False
    __blink_timer = None
    __blink_state = False
    __blink_count = 0

    add_button_signal = qt.pyqtSignal(bool)

    def __init__(self, parent, main_form, name, feed_url, feed_cache):
        self.__feed_url = feed_url
        self.__feed_cache = feed_cache
        self.__feed_list = []
        self.__button_list = []
        self.__feed_index = 0
        self.__state = False
        self.__icon_on = iconfunctions.get_qicon("icons/gen/lightbulb_on.png")
        self.__icon_off = iconfunctions.get_qicon("icons/gen/lightbulb_off.png")

        qt.QGroupBox.__init__(self, parent)
        gui.templates.baseobject.BaseObject.__init__(
            self,
            parent=parent,
            main_form=main_form,
            name=name,
            icon=self.__icon_on,
        )
        self.setObjectName(name)

        self.add_button_signal.connect(self.__add_button)

        # Initilize layout
        main_layout = gui.templates.widgetgenerator.create_layout(
            parent=self,
            vertical=True,
        )
        self.setLayout(main_layout)

        # Initilize the window layout
        groupbox = gui.templates.widgetgenerator.create_borderless_groupbox(
            parent=self,
            name="WindowBox",
        )
        layout = gui.templates.widgetgenerator.create_layout(
            parent=groupbox,
            vertical=True,
        )
        main_layout.addWidget(groupbox)
        self.window_groupbox = groupbox

        # Initialize display widget
        window = gui.forms.messagewindow.MessageWindow(
            parent=self,
            main_form=parent,
        )
        layout.addWidget(window)
        self.window = window

        # Create the lower groupbox
        groupbox = gui.templates.widgetgenerator.create_borderless_groupbox(
            parent=self,
            name="LowerBox",
        )
        lower_layout = gui.templates.widgetgenerator.create_layout(
            parent=groupbox,
            vertical=False,
        )
        layout.addWidget(groupbox)
        self.lower_groupbox = groupbox

        # Back button
        back_button = gui.helpers.buttons.PictureButton(
            name="BackButton",
            off_image="icons/arrow/triangle/triangle_left.png",
            on_image="icons/arrow/triangle/triangle_full_left.png",
            hover_image="icons/arrow/triangle/triangle_left.png",
            checked_image="icons/arrow/triangle/triangle_left.png",
            focus_image="icons/arrow/triangle/triangle_left.png",
            disabled_image="icons/arrow/triangle/triangle_left.png",
            function=self.__feed_backward,
            size=(
                data.get_home_window_button_pixelsize(),
                data.get_home_window_button_pixelsize(),
            ),
            parent=self,
            border=False,
        )
        lower_layout.addWidget(back_button)
        self.back_button = back_button

        # Initilize the window layout
        button_groupbox = (
            gui.templates.widgetgenerator.create_groupbox_with_layout(
                parent=self,
                name="ButtonBox",
                vertical=False,
                borderless=True,
                spacing=0,
                margins=(0, 0, 0, 0),
            )
        )
        button_groupbox.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter
        )
        lower_layout.addWidget(button_groupbox)
        self.button_groupbox = button_groupbox

        # Forward button
        forward_button = gui.helpers.buttons.PictureButton(
            name="ForwardButton",
            off_image="icons/arrow/triangle/triangle_right.png",
            on_image="icons/arrow/triangle/triangle_full_right.png",
            hover_image="icons/arrow/triangle/triangle_right.png",
            checked_image="icons/arrow/triangle/triangle_right.png",
            focus_image="icons/arrow/triangle/triangle_right.png",
            disabled_image="icons/arrow/triangle/triangle_right.png",
            function=self.__feed_forward,
            size=(
                data.get_home_window_button_pixelsize(),
                data.get_home_window_button_pixelsize(),
            ),
            parent=self,
            border=False,
        )
        lower_layout.addWidget(forward_button)
        self.forward_button = forward_button

        # Update the style
        self.update_style()

        # Connect the feed signal
        data.signal_dispatcher.feed_update.connect(self.__feed_loaded)

        # Start the feed retrieval
        t = threading.Thread(
            target=self.__feed_check,
            daemon=True,
        )
        t.start()

    def __get_icons(self, state):
        valid_states = {
            False: self.__icon_off,
            True: self.__icon_on,
        }
        return valid_states[state]

    def blink_icon_start(self):
        self.blink_icon_stop()
        self.__blink_count = 0
        self.__blink_timer.start()

    def blink_icon_stop(self):
        if self.__blink_timer is None:
            self.__blink_timer = qt.QTimer(self)
            self.__blink_timer.setSingleShot(True)
            self.__blink_timer.setInterval(200)
            self.__blink_timer.timeout.connect(self.__blink)
        self.__blink_timer.stop()
        self.__blink_state = True
        self.__blink_count = 0
        self.icon_manipulator.set_icon(self, self.__get_icons(self.__state))

    def __blink(self):
        self.__blink_state = not self.__blink_state
        self.icon_manipulator.set_icon(
            self, self.__get_icons(self.__blink_state)
        )
        self.__blink_count += 1
        if self.__blink_count < 6:
            self.__blink_timer.start()
        else:
            self.blink_icon_stop()

    def news_show(self):
        self.icon_manipulator.set_icon(self, self.__get_icons(True))
        self.__state = True

    def news_hide(self):
        self.icon_manipulator.set_icon(self, self.__get_icons(False))
        self.__state = False

    def __set_default_feed(self):
        hello_text = f"""
<p>
    <table>
        <tr style="vertical-align: middle;">
            <td>
                <img src="{data.application_icon_abspath}" width="60" height="60" />
            </td>
            <td>
                <h3>Hi, welcome to Embeetle IDE :)</h3>
            </td>
        </tr>
    </table>
</p>
        """
        default_text = functions.get_feed_from_resource_file()
        if not isinstance(default_text, str):
            default_text = ""
        self.__feed_add(
            title="Startup page",
            date=functions.rss_format_time(datetime.datetime.now()),
            text=hello_text,  # hello_text + default_text,
            checked=True,
        )

    def __feed_check(self, *args) -> None:
        """"""
        rss_text = None
        # Try to use the website feed
        try:
            with urllib.request.urlopen(self.__feed_url) as response:
                rss_text = response.read()

            # Store the feed into a cache file
            with open(data.rss_local_file, "wb+") as f:
                f.write(rss_text)
        except urllib.error.URLError:
            purefunctions.printc(
                f"WARNING: Failed to download {q}{self.__feed_url}{q}",
                color="warning",
            )
        except:
            print(traceback.format_exc())

        # Try to use the stored feed if the website one is inaccessible
        try:
            if rss_text is None and os.path.isfile(data.rss_local_file):
                with open(data.rss_local_file, "r", encoding="utf-8") as f:
                    rss_text = f.read()
        except:
            print(traceback.format_exc())

        # Parse the feed
        if rss_text is None:
            # Set default feed content
            self.__set_default_feed()
            # Finish feed update
            data.signal_dispatcher.feed_update.emit()
            return

        try:
            feed = feedparser.parse(rss_text)
            for e in feed["entries"]:
                dt = datetime.datetime.fromtimestamp(
                    time.mktime(e["published_parsed"])
                )
                title = e["title"]
                description = e["summary_detail"]["value"]
                time_string = functions.rss_format_time(dt)
                text = "<h2>{}</h2><h3>{}</h3><p>{}</p>".format(
                    title, time_string, description
                )
                self.__feed_add(
                    title=title,
                    date=time_string,
                    text=text,
                )

            # Finish feed update
            data.signal_dispatcher.feed_update.emit()
        except:
            # An error happened, print the error and set the default feed
            print(traceback.format_exc())
            self.__set_default_feed()
            # Finish feed update
            data.signal_dispatcher.feed_update.emit()
        return

    @qt.pyqtSlot()
    def __feed_loaded(self):
        # Update feed
        self.__feed_initialize()
        # Set the last checked feed
        #        last_checked_index = 0
        #        for i,f in enumerate(self.__feed_list):
        #            if f["checked"] == True:
        #                last_checked_index = i
        #        self.__feed_set(last_checked_index)
        self.__feed_set(len(self.__feed_list) - 1)

        # Update the style
        self.update_style()

    def __feed_initialize(self):
        feed_data = {}
        if os.path.isfile(self.__feed_cache):
            feed_data = functions.load_json_file(self.__feed_cache)
        if feed_data is not None:
            for fl in self.__feed_list:
                for fd in feed_data:
                    if fl["title"] == fd["title"]:
                        fl["checked"] = fd["checked"]
                        break
        self.__feed_update()

    def __feed_update(self):
        functions.write_json_file(self.__feed_cache, self.__feed_list)

    def __feed_add(self, title, date, text, checked=False):
        new_item = {
            "title": title,
            "date": date,
            "text": text,
            "checked": checked,
        }
        self.__feed_list.append(new_item)
        self.add_button_signal.emit(checked)

    @qt.pyqtSlot(bool)
    def __add_button(self, checked):
        # Add the button
        new_button = gui.helpers.buttons.PictureButton(
            name="FeedButton",
            off_image="icons/checkbox/grey.svg",
            on_image="icons/checkbox/grey.svg",
            hover_image="icons/checkbox/grey.svg",
            checked_image="icons/checkbox/grey.svg",
            focus_image="icons/checkbox/checked_pressed_no_tick.svg",
            disabled_image="icons/checkbox/grey.svg",
            function=functools.partial(
                self.__feed_set, len(self.__button_list)
            ),
            size=(
                data.get_general_icon_pixelsize(),
                data.get_general_icon_pixelsize(),
            ),
            parent=self.button_groupbox,
            border=False,
        )
        new_button.setCheckable(True)
        new_button.setChecked(checked)
        self.button_groupbox.layout().addWidget(new_button)
        self.button_groupbox.layout().setAlignment(
            new_button,
            qt.Qt.AlignmentFlag.AlignHCenter | qt.Qt.AlignmentFlag.AlignVCenter,
        )
        self.__button_list.append(new_button)

    def __feed_set(self, index):
        try:
            # Safety check
            if index < 0:
                index = 0
            elif index > (len(self.__button_list) - 1):
                index = len(self.__button_list) - 1
            # Select index
            self.__feed_list[index]["checked"] = True
            for i, b in enumerate(self.__button_list):
                b.setChecked(self.__feed_list[i]["checked"])
                b.setProperty("focused", i == index)
                b.style().unpolish(b)
                b.style().polish(b)
            self.__feed_index = index
            # Update display window
            self.window.clear()
            feed_data = self.__feed_list[index]
            self.window.append(feed_data["text"])
            # Update the feed cache
            self.__feed_update()
            # Scrool text to top
            self.window.goto_start()
        except:
            traceback.print_exc()

    def __feed_forward(self, *args):
        self.__feed_set(self.__feed_index + 1)

    def __feed_backward(self, *args):
        self.__feed_set(self.__feed_index - 1)

    def update_style(self):
        # Buttons
        self.back_button.set_size(
            data.get_home_window_button_pixelsize(),
            data.get_home_window_button_pixelsize(),
        )
        back_button_stylesheet = self.back_button.get_stylesheet()
        self.forward_button.set_size(
            data.get_home_window_button_pixelsize(),
            data.get_home_window_button_pixelsize(),
        )
        forward_button_stylesheet = self.forward_button.get_stylesheet()

        feed_button_stylesheet = ""
        if len(self.__button_list) > 0:
            self.__button_list[0].set_size(
                data.get_home_window_button_pixelsize(),
                data.get_home_window_button_pixelsize(),
            )
            feed_button_stylesheet = self.__button_list[0].get_stylesheet()

        self.setStyleSheet(
            back_button_stylesheet
            + forward_button_stylesheet
            + feed_button_stylesheet
        )
        # Window
        self.window.update_variable_settings()
        # Icons
        if self.icon_manipulator is not None:
            self.icon_manipulator.set_icon(self, self.__get_icons(self.__state))
