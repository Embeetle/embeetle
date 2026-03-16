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
import os
import re
import time
import fnmatch
import threading
import traceback
import urllib
import urllib.parse
import urllib.request
import urllib.error
import urllib3.util.retry
import qt
import data
import functions
import purefunctions
import requests
from requests.adapters import HTTPAdapter
import tempfile
import components.thread_switcher
from various.kristofstuff import nop
import os_checker

_url_tempfiles = []


def urlretrieve_beetle(
    url: str,
    reporthook: Callable,
    stopfunc: Optional[Callable] = None,
    verbose: bool = False,
    max_retries: int = 5,
    timeout: int = 20,
) -> Tuple[Optional[str], Optional[requests.Response]]:
    """Retrieve a URL into a temporary location on disk with enhanced resilience
    for bad internet connections.

    :param url:         Requires a URL argument.
    :param reporthook:  A callable that accepts a block number, a read size, and the total file size
                        of the URL target.
    :param stopfunc:    Optional callable that can be used to stop the download process.
    :param verbose:     If True, enables verbose output for debugging purposes.

    :return: Returns a tuple containing the path to the newly created data file as well as the
             resulting `requests.Response` object.
    """
    # Skip the request if internet is known to be down
    if data.internet_down:
        if verbose:
            purefunctions.printc(
                "Internet connection is down, skipping URL retrieval"
            )
        return None, None

    if verbose:
        purefunctions.printc(f"urlretrieve_beetle('{url}')")
    # Validate the URL
    if url.startswith("file://"):
        raise IOError("Given URL is a local file!")

    # Handle URL adjustments (assuming `data.new_mode` and `data.resources_directory` are defined)
    if data.new_mode:
        if url.startswith("https://www.embeetle"):
            url = url.replace("https://www.embeetle", "https://new.embeetle")
        elif url.startswith("https://embeetle"):
            url = url.replace("https://embeetle", "https://new.embeetle")
        url = url.replace("embeetle.cn", "embeetle.com")
        if verbose:
            purefunctions.printc(f"    url modified to '{url}'")

    # Find `cacert.pem` file
    cacert_filepath = os.path.join(
        data.resources_directory, "cacert.pem"
    ).replace("\\", "/")
    if not os.path.isfile(cacert_filepath):
        raise RuntimeError(f"Cacert file not found at: '{cacert_filepath}'")
    if verbose:
        purefunctions.printc(f"    Using cacert file at '{cacert_filepath}'")

    # Setup for resilient downloading
    chunk_size = 1024 * 8  # 8 KB chunks

    # Set up session with retries
    session = requests.Session()
    retries = urllib3.util.Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if verbose:
        purefunctions.printc("    Session and retries set up.")

    # Handle temporary file setup
    with tempfile.NamedTemporaryFile(delete=False) as tfp:
        filename = tfp.name.replace("\\", "/")
        _url_tempfiles.append(filename)
    if verbose:
        purefunctions.printc(f"    Temporary file created at '{filename}'")

    total_size = None
    downloaded = 0
    blocknum = 0

    for attempt in range(max_retries):
        try:
            if verbose:
                purefunctions.printc(
                    f"    Attempt {attempt + 1} of {max_retries}"
                )
            headers = {}
            if downloaded > 0:
                headers["Range"] = f"bytes={downloaded}-"
                if verbose:
                    purefunctions.printc(
                        f"    Resuming download from byte {downloaded}"
                    )
            if verbose:
                purefunctions.printc(
                    f"    Trying to connect ... (timeout = {timeout}s)"
                )
            with session.get(
                url,
                stream=True,
                timeout=timeout,
                verify=cacert_filepath,
                headers=headers,
            ) as response:
                if verbose:
                    purefunctions.printc(
                        f"    Received response with status code {response.status_code}"
                    )
                response.raise_for_status()

                # Get total size
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    total_size = int(content_length)
                    if downloaded > 0 and "Content-Range" in response.headers:
                        # Adjust total_size based on Content-Range
                        content_range = response.headers["Content-Range"]
                        total_size = int(content_range.split("/")[-1])
                    else:
                        if downloaded > 0:
                            # Server did not support resuming
                            downloaded = 0
                            with open(filename, "wb"):
                                pass  # Truncate the file
                            if verbose:
                                purefunctions.printc(
                                    "    Server did not support resuming. Restarting download."
                                )
                else:
                    total_size = 0  # Unknown total size

                if downloaded == 0:
                    if total_size == 0:
                        # Give a fake total_size back to the reporthook, so the bar would at least
                        # move.
                        reporthook(0, chunk_size, chunk_size * 100)
                    else:
                        reporthook(0, chunk_size, total_size)

                with open(filename, "ab") as tfp:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            tfp.write(chunk)
                            downloaded += len(chunk)
                            blocknum += 1
                            if total_size == 0:
                                # Give a fake total_size back to the reporthook, so the bar would at
                                # least move.
                                if blocknum < 100:
                                    reporthook(
                                        blocknum, chunk_size, chunk_size * 100
                                    )
                                else:
                                    reporthook(
                                        blocknum,
                                        chunk_size,
                                        chunk_size * (blocknum + 2),
                                    )
                            else:
                                reporthook(blocknum, chunk_size, total_size)

                            if stopfunc and stopfunc():
                                raise RuntimeError(
                                    "Download stopped by stopfunc"
                                )
                # Download complete
                if verbose:
                    purefunctions.printc("    Download complete.")
                return filename, response
        except (
            requests.RequestException,
            requests.exceptions.ContentDecodingError,
            RuntimeError,
        ) as e:
            if verbose:
                purefunctions.printc(f"    An error occurred: {e}")
            if attempt < max_retries - 1:
                # Update downloaded size
                if os.path.exists(filename):
                    downloaded = os.path.getsize(filename)
                else:
                    downloaded = 0
                time.sleep(2**attempt)  # Exponential backoff
                if verbose:
                    purefunctions.printc(
                        f"    Retrying after {2 ** attempt} seconds..."
                    )
                continue
            else:
                if verbose:
                    purefunctions.printc(
                        f"    Cannot reach '{url}': {str(e)}\n", color="error"
                    )
                raise
    return None, None


def urlcleanup_beetle():
    """Clean up temporary files from urlretrieve calls."""
    for temp_file in _url_tempfiles:
        try:
            os.unlink(temp_file)
        except OSError:
            pass

    del _url_tempfiles[:]
    return


def __get_remote_info__(
    callback: Optional[Callable],
    func: Callable,
    url: str,
    max_retries: int = 5,
    timeout: int = 20,
) -> None:
    """Download file at the given url and apply the given function on the
    filepath. The result is then passed to the callback.

    In case of error, the string 'none' is passed to the callback.

    Help function for:
        - get_remote_embeetle_version(callback)
        - get_remote_embeetle_builddate(callback)
        - get_remote_beetle_toollist(callback)
    """
    # If internet is down (as detected by earlier checks), exit early
    # This prevents unnecessary network requests and waiting for timeouts
    if data.internet_down:
        if callback:
            callback("none")
        return

    origthread = qt.QThread.currentThread()
    mortal_thread: qt.QThread = qt.QThread()

    def print_errmsg(_msg: Optional[str], _url: str) -> None:
        purefunctions.printc(
            f'WARNING: Failed to download "{_url}"',
            color="warning",
        )
        if _msg is not None:
            purefunctions.printc(f"{_msg}\n", color="warning")
        return

    def download_file(*args) -> None:
        "Download file at url [runs in mortal thread]"
        assert qt.QThread.currentThread() is mortal_thread
        nonlocal url
        if data.new_mode:
            if url.startswith("https://www.embeetle"):
                url = url.replace(
                    "https://www.embeetle", "https://new.embeetle"
                )
            if url.startswith("https://embeetle"):
                url = url.replace("https://embeetle", "https://new.embeetle")
            url = url.replace("embeetle.cn", "embeetle.com")
        filepath: Optional[str] = None
        response = None  # Updated variable name from 'headers' to 'response'
        try:
            filepath, response = urlretrieve_beetle(
                url=url,
                reporthook=nop,
                stopfunc=None,
                verbose=False,
                max_retries=max_retries,
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError:
            # This exception occurs when there's no internet connection or DNS failure.
            print_errmsg(None, url)
            finish_mt("none")
            return
        except requests.exceptions.Timeout:
            # The request timed out.
            print_errmsg(traceback.format_exc(), url)
            finish_mt("none")
            return
        except requests.exceptions.HTTPError as e:
            # HTTP error occurred (e.g., 404 Not Found, 500 Internal Server Error)
            print_errmsg(traceback.format_exc(), url)
            finish_mt("none")
            return
        except requests.exceptions.ContentDecodingError as e:
            # The response content could not be decoded.
            print_errmsg(traceback.format_exc(), url)
            finish_mt("none")
            return
        except requests.exceptions.RequestException as e:
            # A general exception from the requests library (e.g., invalid URL)
            print_errmsg(traceback.format_exc(), url)
            finish_mt("none")
            return
        except RuntimeError as e:
            # Custom exceptions raised by urlretrieve_beetle (e.g., download stopped by stopfunc)
            print_errmsg(str(e), url)
            finish_mt("none")
            return
        except Exception as e:
            # Catch any other unforeseen exceptions.
            print_errmsg(traceback.format_exc(), url)
            finish_mt("none")
            return
        finish_mt(func(filepath))
        return

    def finish_mt(info: str) -> None:
        "Finish [runs in mortal thread]"
        assert qt.QThread.currentThread() is mortal_thread
        components.thread_switcher.switch_thread_new(
            qthread=origthread,
            callback=finish_ot,
            args=info,
        )
        return

    def finish_ot(info: str) -> None:
        "Finish [runs in original thread]"
        assert qt.QThread.currentThread() is origthread
        mortal_thread.quit()
        callback(info)
        return

    def delete_mt(*args) -> None:
        "Delete mortal thread [runs in original thread]"
        assert qt.QThread.currentThread() is origthread
        assert mortal_thread.isFinished()
        components.thread_switcher.remove_thread(qthread=mortal_thread)
        mortal_thread.deleteLater()
        return

    # mortal_thread.started.connect(lambda: print(''))
    mortal_thread.finished.connect(delete_mt)
    mortal_thread.start()

    # * 1. Check if 'origthread' is already registered.
    try:
        components.thread_switcher.get_name(qthread=origthread)
    except:
        if threading.current_thread() is threading.main_thread():
            components.thread_switcher.register_thread(
                name="main",
                qthread=origthread,
            )
        else:
            purefunctions.printc(
                "\nWARNING: Unknown thread registered at "
                "functions.__get_remote_info__()\n",
                color="warning",
            )
            components.thread_switcher.register_thread(
                name=f"not_known_thread_{id(origthread)}",
                qthread=qt.QThread.currentThread(),
            )

    # * 2. Register 'mortal_thread'.
    components.thread_switcher.register_thread(
        name=f"remote_info_{id(mortal_thread)}", qthread=mortal_thread
    )

    # * 3. Start procedure.
    components.thread_switcher.switch_thread_new(
        qthread=mortal_thread,
        callback=download_file,
        args=None,
    )
    return


def get_remote_embeetle_version(callback: Optional[Callable]) -> None:
    """Call the given `callback` function and pass it the following parameter:

    '0.0.1'     -> Latest embeetle version on the server. Equals
    'none' if error while downloading the version.txt file.
    """
    # Skip if internet is down
    if data.internet_down and callback:
        callback("none")
        return

    # MIGRATION TO GITHUB:
    # No longer fetch the `version.txt` file from the Embeetle server, but
    # from the Embeetle GitHub repo instead. So comment out the fetching from
    # the Embeetle server:
    # guid = functions.get_embeetle_unique_identifier()
    # version_url = f"{get_base_url_wfb()}/downloads/{os_checker.get_os()}/embeetle/beetle_core/version.txt?id = {guid}"
    #
    # The `embeetle` repo is not yet public, so for now, we fetch the version
    # file from a public test repo:
    version_url = "https://github.com/Embeetle/embeetle/releases/latest/download/version.txt"
    __get_remote_info__(
        callback=callback,
        func=functions.get_embeetle_version,
        url=version_url,
        max_retries=2,
        timeout=3,
    )
    return


def get_remote_embeetle_builddate(callback: Optional[Callable]) -> None:
    """Call the given 'callback' function and pass it the following parameter:

    '13 dec 2019' -> Latest embeetle build date on the server. Equals 'none' if
    error while downloading the                  version.txt file.
    """
    # Skip if internet is down
    if data.internet_down and callback:
        callback("none")
        return

    __get_remote_info__(
        callback=callback,
        func=functions.get_embeetle_builddate,
        url=f"{get_base_url_wfb()}/downloads/{os_checker.get_os()}/embeetle/beetle_core/version.txt",
        max_retries=2,
        timeout=3,
    )
    return


def get_remote_beetle_projlist(callback: Optional[Callable]) -> None:
    """
    Invoke the given 'callback' function and pass it a Python dictionary with
    all the projects listed on the server.
    Example:

    output =
    {
        'stmicro':
        {
            'beetle_f767zi_baremetal':
            {
                'boardfamily' : 'beetle',
                'chip'        : 'stm32f767zi',
                'os'          : 'baremetal',
                'path'        : 'stmicro/beetle/baremetal/beetle_f767zi.7z'
            },
            'beetle_l412kb_baremetal':
            {
                'boardfamily' : 'beetle',
                'chip'        : 'stm32l412kb',
                'os'          : 'baremetal',
                'path'        : 'stmicro/beetle/baremetal/beetle_l412kb.7z'
            },
            ...
    }
    """
    # Skip if internet is down
    if data.internet_down and callback:
        callback(None)
        return

    # Determine makefile version (deprecated)
    # ==========================
    # version: Optional[int] = None
    # if data.makefile_version_new_projects is not None:
    #     version = data.makefile_version_new_projects
    # else:
    #     version = functions.get_latest_makefile_interface_version()
    #
    # MIGRATION TO GITHUB:
    # Makefile versions for new projects are deprecated. We only put the
    # projects with the latest makefile version on GitHub.

    # Provide key for some projects (deprecated)
    # =============================
    # A key can be given to the html request for the 'project_list.json' file,
    # for example to obtain the Atmosic-specific one.
    #
    # MIGRATION TO GITHUB:
    # No more key is needed to access specific projects since the migration
    # to GitHub.
    # key_filepath = os.path.join(data.settings_directory, "key.btl").replace(
    #     "\\", "/"
    # )
    # key = ""
    # if os.path.isfile(key_filepath):
    #     with open(
    #         key_filepath, "r", encoding="utf-8", newline="\n", errors="replace"
    #     ) as f:
    #         key = urllib.parse.quote(f.read())
    #     __get_remote_info__(
    #         callback=callback,
    #         func=functions.get_json_dictionary,
    #         url=f"{get_base_url_wfb()}/downloads/projects_m{version}/project_list.json?key = {key}",
    #         max_retries=2,
    #         timeout=3,
    #     )
    #     return

    # Construct URL
    # =============
    # proj_list_url = f"{get_base_url_wfb()}/downloads/projects_m{version}/project_list.json"
    proj_list_url = "https://github.com/Embeetle/projects/releases/download/project_list/project_list.json"
    print(f"Obtain project list from GitHub...")
    __get_remote_info__(
        callback=callback,
        func=functions.get_json_dictionary,
        url=proj_list_url,
        max_retries=2,
        timeout=3,
    )
    return


def get_remote_beetle_toollist(callback: Optional[Callable]) -> None:
    """
    IMPORTANT:
    Always use the 'data.toolman.get_remote_beetle_toollist(..)' function instead of this one. The
    'data.toolman.get_remote_beetle_toollist(..)' function is more complete!

    Call the given 'callback' function and pass it the following parameter:
    parameter =
    [
        {
            'name'     : 'gnu_arm_toolchain',
            'kind'     : 'COMPILER_TOOLCHAIN',
            'version'  : '9.2.1_9-2019-q4-major',
            'bitness'  : '32b',
            'unique_id': 'gnu_arm_toolchain_9.2.1_9-2019-q4-major_32b',
        },

        {
            'name'     : 'gnu_make',
            'kind'     : 'BUILD_AUTOMATION',
            'version'  : '4.2.0',
            'bitness'  : '32b',
            'unique_id': 'gnu_make_4.2.0_32b',
        },
        ...
    ]

    In case of error, pass None.
    """
    # Skip if internet is down
    if data.internet_down and callback:
        callback(None)
        return

    os_arch = os_checker.get_os_with_arch()
    # GitHub repositories that host Embeetle tools, one per tool category
    github_repos = [
        ("FLASHTOOL",          "flashtool"),
        ("BUILD_AUTOMATION",   "build_automation"),
        ("COMPILER_TOOLCHAIN", "compiler_toolchain"),
    ]
    github_tool_repos = [
        "flashtool",
        "build_automation",
        "compiler_toolchain",
    ]
    accumulated: List[Dict] = []
    pending = [len(github_tool_repos)]

    def on_repo_assets(kind: str, rawlist: List[str]) -> None:
        if not (
            (rawlist is None)
            or (isinstance(rawlist, str) and rawlist.lower() == "none")
            or (isinstance(rawlist, list) and len(rawlist) == 0)
        ):
            try:
                p_name = re.compile(r"([\w-]+)_[v\d]")
                p_ver = re.compile(r"([\w\.-]+)_(32b|64b).7z")
                for filename in rawlist:
                    # $ Find name
                    name: Optional[str] = None
                    try:
                        m_name = p_name.match(filename)
                        name = m_name.group(1).strip("_")
                    except:
                        # There is no '_v' or '_<digit>' found in the filename
                        name = filename.replace(".zip", "")
                        name = filename.replace(".7z", "")
                    assert name is not None

                    # $ Find version and bitness
                    remainder = filename.replace(name, "")
                    version: Optional[str] = None
                    bitness: Optional[str] = None
                    try:
                        m_ver = p_ver.match(remainder)
                        version = m_ver.group(1).strip("_")
                        bitness = m_ver.group(2).strip("_")
                    except:
                        version = "none"
                        bitness = "none"
                    accumulated.append(
                        {
                            "name": name,
                            "kind": kind,
                            "version": version,
                            "bitness": bitness,
                            "unique_id": (
                                f"{name}_{version}_{bitness}"
                                if version != "none"
                                else name
                            ),
                        }
                    )
            except:
                traceback.print_exc()
                purefunctions.printc(
                    f"ERROR: Cannot interpret rawlist = {rawlist}"
                )
        pending[0] -= 1
        if pending[0] == 0:
            import pprint
            pprint.pprint(accumulated)
            callback(accumulated if accumulated else None)
        return

    for repo in github_tool_repos:
        kind = repo.upper()
        __get_remote_info__(
            callback=lambda rawlist, k=kind: on_repo_assets(k, rawlist),
            func=functions.extract_github_release_assets,
            url=(
                f"https://api.github.com/repos/Embeetle/{repo}"
                f"/releases/tags/{os_arch}"
            ),
            max_retries=2,
            timeout=10,
        )
    return


def __fetch_url(
    url: str, result: Dict[str, Any], event: threading.Event
) -> None:
    """Fetches URL and records timing and response data.

    Used by get_fastest_response to determine the best server.
    """
    # Skip the request if internet is down
    if data.internet_down:
        return

    start_time = time.time()
    try:
        with urllib.request.urlopen(url) as response:
            response_data = response.read().decode("utf-8")
            end_time = time.time()
            response_time = end_time - start_time
            result["url"] = url
            result["response_time"] = response_time
            result["response_data"] = response_data
            event.set()  # Signal that the fastest response is found
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
    return


def get_fastest_response(
    urls: Tuple[str],
) -> Optional[
    Tuple[str | float | None, str | float | None, str | float | None]
]:
    """Tests multiple URLs to determine which one responds the fastest.

    Returns None if internet connectivity is unavailable.
    """
    # Return None if internet is down to avoid unnecessary testing
    if data.internet_down:
        return None
    results = [
        {"url": None, "response_time": float("inf"), "response_data": None}
        for _ in urls
    ]
    event = threading.Event()

    threads = []
    for i, url in enumerate(urls):
        thread = threading.Thread(
            target=__fetch_url, args=(url, results[i], event)
        )
        thread.start()
        threads.append(thread)

    # Wait until the event is set (i.e., fastest response is found) or all threads finish
    event.wait(timeout=1.0)

    # Find the fastest response and print it
    if all([(x["response_time"] == float("inf")) for x in results]):
        return None
    fastest_result = min(results, key=lambda x: x["response_time"])
    return (
        fastest_result["url"],
        fastest_result["response_time"],
        fastest_result["response_data"],
    )


def determine_base_url() -> str:
    """Determines the fastest base URL for Embeetle connectivity.

    If internet is down, uses the default URL without trying network operations.
    """
    base_url = "https://embeetle.com"

    # If internet is down, use default URL without trying network operations
    if data.internet_down:
        return base_url

    try:
        # Response timing check
        result = get_fastest_response(data.BASE_URLS)
        if result is not None:
            url, response_time, response_data = result
            base_url = url
    except:
        traceback.print_exc()
    store_url(base_url=base_url, base_url_override=None)
    return base_url


def store_url(
    base_url: Optional[str] = None,
    base_url_override: Optional[str] = None,
) -> None:
    """Store the given urls (provided that they're not None).

    If None, just ignore.
    """
    server_file = f"{data.settings_directory}/server.btl"
    # First try to load the json data from the 'server.btl' file. Then, only replace the 'base_url'
    # field in there with the given 'base_url' parameter. Finally, write the json data back to the
    # file.
    json_dict = {
        "base_url": None,
        "base_url_override": None,
    }
    try:
        if os.path.isfile(server_file):
            loaded_dict = functions.load_json_file(server_file)
            if loaded_dict is not None:
                json_dict = loaded_dict
    except:
        traceback.print_exc()
    if base_url is not None:
        json_dict["base_url"] = base_url
    if base_url_override is not None:
        json_dict["base_url_override"] = base_url_override
    try:
        functions.write_json_file(filepath=server_file, json_dict=json_dict)
    except:
        traceback.print_exc()
    return


def get_stored_urls() -> Tuple[str, str]:
    """Return the stored 'base_url' and the stored 'base_url_override' from the
    'server.btl' file.

    If nothing found, return the default values.
    """
    server_file = f"{data.settings_directory}/server.btl"
    # Default values
    base_url = "https://embeetle.com"
    base_url_override = "AUTOMATIC"
    try:
        if os.path.isfile(server_file):
            loaded_dict = functions.load_json_file(server_file)
            if loaded_dict is not None:
                base_url = loaded_dict.get("base_url", base_url)
                base_url_override = loaded_dict.get(
                    "base_url_override", base_url_override
                )
    except:
        traceback.print_exc()
    return base_url, base_url_override


def get_base_url() -> Optional[str]:
    """
    Returns the base URL for our website:
        - 'https://embeetle.com'
        - 'https://new.embeetle.com'
        - 'https://embeetle.cn'
    You can use this only after line 168 of 'beetle_core/embeetle.py' is executed. Before that, it
    returns None!
    """
    if data.new_mode:
        return "https://new.embeetle.com"
    elif data.embeetle_base_url_override is not None:
        return data.embeetle_base_url_override
    else:
        return data.embeetle_base_url


def get_base_url_wfb() -> str:
    """
    Same as previous function, but with a 'https://embeetle.com' fallback value.
    """
    base_url = get_base_url()
    if base_url is None:
        print("WARNING: Cannot determine base URL!")
        return "https://embeetle.com"
    return base_url


def _get_tool_category(tool_uid: str) -> str:
    """Determine the tool category (FLASHTOOL, BUILD_AUTOMATION, or
    COMPILER_TOOLCHAIN) for a given tool unique ID.

    :param tool_uid: Tool unique ID, e.g. 'avrdude_7.3_64b'.
    :return: Tool category string.
    """
    p_flashtool = data.toolversion_extractor.get_patterns("FLASHTOOL")
    p_buildauto = data.toolversion_extractor.get_patterns("BUILD_AUTOMATION")
    for p in p_flashtool:
        if fnmatch.fnmatch(name=tool_uid, pat=p):
            return "FLASHTOOL"
    for p in p_buildauto:
        if fnmatch.fnmatch(name=tool_uid, pat=p):
            return "BUILD_AUTOMATION"
    return "COMPILER_TOOLCHAIN"


def get_github_tool_url(remote_uid: str) -> str:
    """Return the GitHub download URL for the given tool unique ID.

    :param remote_uid: Tool unique ID, e.g. 'gnu_arm_toolchain_9.2.1_64b'.
    :return: Full GitHub download URL for the .7z archive.
    """
    category = _get_tool_category(remote_uid)
    repo = category.lower()
    os_arch = os_checker.get_os_with_arch()
    return (
        f"https://github.com/Embeetle/{repo}"
        f"/releases/download/{os_arch}/{remote_uid}.7z"
    )


def get_news_url() -> str:
    """"""
    # base_url = get_base_url()
    # return f"{base_url}/#news"
    return "https://embeetle.com/#news"


def get_rsync_remote_domain() -> str:
    """
    Returns the rsync remote domain for our website:
        - 'embeetle.com'
        - 'embeetle.cn'
    There's no 'https://' prefix. Also, the 'new.' prefix is never part of that, because the
    distinction between the public and testserver is made locally on the server.
    """
    base_url = get_base_url_wfb()
    remote_domain = base_url.replace("https://", "").replace("new.", "")
    if remote_domain.startswith("embeetle"):
        return remote_domain
    print(f"WARNING: Cannot determine rsync remote domain from {base_url}!")
    return "embeetle.com"


def get_rsync_known_hosts_url(remote_domain: Optional[str] = None) -> str:
    """
    Return:
        - 'https://embeetle.com/keys/known_hosts'
        - 'https://embeetle.cn/keys/known_hosts'
    """
    if remote_domain is None:
        remote_domain = get_rsync_remote_domain()
    return f"https://{remote_domain}/keys/known_hosts"


def get_rsync_client_id_rsa_url(remote_domain: Optional[str] = None) -> str:
    """
    Return:
        - 'https://embeetle.com/keys/client_id_rsa'
        - 'https://embeetle.cn/keys/client_id_rsa'
    """
    if remote_domain is None:
        remote_domain = get_rsync_remote_domain()
    return f"https://{remote_domain}/keys/client_id_rsa"


def replace_base_url(url: Optional[str]) -> Optional[str]:
    """Provide a URL, like:

    'https://embeetle.com/#supported-hardware/arduino/boards/uno-r3' This
    function then replaces the base of this URL to match the best server, eg:
    'https://embeetle.cn/#supported-hardware/arduino/boards/uno-r3'
    """
    if url is None:
        return None
    try:
        if url.startswith("#"):
            return f"{get_base_url_wfb()}/{url}"
        if url.startswith(("https://embeetle", "https://new.embeetle")):
            return re.sub(r"https?://[^/]+", get_base_url_wfb(), url)
    except:
        traceback.print_exc()
    return url
