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
import os.path
import json
import time
import certifi
import traceback
import concurrent.futures
from urllib.request import urlopen
from typing import *

# Setup the SSL certificate
import ssl

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context

import qt
import data
import themes
import settings
import iconfunctions
import purefunctions
import serverfunctions


class NewsManipulator(qt.QObject):
    STORE_FILENAME: str = "news_cache.btl"

    check_completed = qt.pyqtSignal(object)

    __store_file: Optional[str] = None

    def __init__(self) -> None:
        super().__init__()
        # Store file preparation
        settings.check_settings_directory()
        self.__store_file = purefunctions.unixify_path_join(
            data.settings_directory, self.STORE_FILENAME
        )

    def cached_news_update(self) -> None:
        self.check_news(callback=self.__cached_news_update)

    def __cached_news_update(self, current_news):
        if current_news is not None:
            with open(self.__store_file, "w+", encoding="utf-8") as f:
                f.write(json.dumps(current_news, indent=4, ensure_ascii=False))

    def cached_news_read(self) -> Optional[str]:
        result: Optional[str] = None
        if os.path.isfile(self.__store_file):
            with open(self.__store_file, "r", encoding="utf-8") as f:
                result = json.loads(f.read())
        return result

    def check_news(self, callback=None):
        self.worker_thread = NewsCheckerWorker()
        if callable(callback):
            self.worker_thread.finished.connect(callback)
        else:
            self.worker_thread.finished.connect(self.__check_news_finished)
        self.worker_thread.start()

    def __check_news_finished(self, current_news):
        stored_news = self.cached_news_read()
        result = None
        if stored_news is None or (
            current_news is not None
            and (
                max(current_news["news-items"])
                != max(stored_news["news-items"])
            )
        ):
            result = current_news
        self.check_completed.emit(result)


class NewsCheckerWorker(qt.QThread):
    finished = qt.pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def __del__(self):
        self.wait()

    def run(self):
        result = get_news()
        self.finished.emit(result)


def get_news() -> Optional[str]:
    result = None
    try:
        url = f"{serverfunctions.get_base_url_wfb()}/app/news"

        # $ Old
        # content = urllib.request.urlopen(url).read().decode("utf-8")
        # $ New
        content = urlopen(
            url, context=ssl.create_default_context(cafile=certifi.where())
        ).read()

        result = json.loads(content)
    except:
        print("[NewsManipulator] Error getting news feed data!")
        traceback.print_exc()

    return result
