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

import re


class Codec:
    r"""Converter between raw bytes and strings for a serial line monitor.

    Decoding is the process of converting raw bytes to a string.  Encoding is
    the process of converting a string to raw bytes.

    While there are plenty of codecs for standard string encodings like UTF-8,
    none of them is really suited for use in a serial line monitor.

    This codec offers:

     - display of non-printable ascii bytes as an escape sequence when decoding
       raw bytes to a string, using the same backslash-based escape codes as C
       strings, which are well known to C programmers;

     - conversion of C escape esequences back to bytes;

     - an option to show line endings explicitly using \r and/or \n;

     - decoding to html-style strings, with html escapes for characters that are
       special in html, and html tag (user definable, default <br>) for line
       endings, and user-definable tags around escape sequences (e.g. to give
       them a different color);

     - an option to decode to or encode from hex strings for all bytes.

    The following escapes are supported in strings:

        \a (  7 07): bell / make a sound
        \t (  9 09): horizontal tab
        \n ( 10 0A): line feed / new line
        \v ( 11 0B): vertical tab
        \f ( 12 0C): form feed / new page
        \r ( 13 0D): carriage return / to beginning of line
        \\ ( 92 5C): backslash
        \b (127 7F): backspace / del
        \xhh where hh are two arbitrary hexadecimal digits (upper- or lowercase)

    *Notes on reversibility*

    Desirable properties for a codec are that encoding reverses decoding and
    decoding reverses encoding.

    In hex mode, encoding always reverses decoding. Decoding only reverses
    encoding for strings consisting of an even number of lowercase hex digits;
    for other strings, encoding fails with an exception.

    In html-ascii mode, reversibility cannot be achieved, because html tags and
    escape sequences are not eliminated during ascii encoding.

    Note however that copying text from a window displaying html text will
    typically remove the html tags and convert html escape sequences (e.g.
    '&nbsp;' to a single space character, etc). It is possible to reverse such
    copied html-encoded bytes to the original bytes on condition that the
    original line endings are present in the html, i.e.  show_line_endings is
    set during decoding.

    If line endings are not shown, full reversibility cannot be achieved for
    line endings.

    In ascii mode, encoding reverses decoding.  Whether decoding reverses
    encoding depends on the original string, and the rules are complex.  If the
    string was or could have been created by ascii decoding, then its encoding
    can be reversed, and otherwise not.

    For example, an escape sequence like \x0a is encoded to a 0A bytes which
    decodes to \n, so there is no reversibility in this case.
    """

    def __init__(
        self,
        mode="ascii",
        show_line_endings=True,
        html_line_ending="<br>",
        html_begin_escape="",
        html_end_escape="",
        line_ending=None,
        hex_bytes_per_block=2,
        hex_line_width=80,
        column=0,
    ):
        """Create a codec with given options.

        All options are also available as data members with the same name and
        can be changed at any time.

        :param mode:         Mode to be used for encoding and decoding.  Allowed
                             values are 'ascii', 'hex', 'html-ascii' and
                             'html-hex'

                             Note: the mode applies only to the generic
                             `encode()` and `decode()` methods. There is also a
                             separate method for each mode that bypasses the
                             mode setting.  The effect of each mode is explained
                             there.

        :param show_line_endings: During html decoding, if true, make line
                             endings visible: insert '\r' for each CR byte and
                             '\n' for each LF byte.

        :param html_line_ending: During html decoding, replace line endings
                             by this string (default: '<br>') .

        :param html_begin_escape: During html decoding, insert this string
                             before any sequence of consecutive escapes starting
                             with a backslash. This can be used together with
                             html_end_escape to give escapes a special
                             formatting, e.g. another color than the rest of the
                             string.

        :param html_end_escape: During html decoding, insert this string before
                             any sequence of consecutive escapes starting with a
                             backslash. This can be used together with
                             html_begin_escape to give escapes a special
                             formatting, e.g. another color than the rest of the
                             string.

        :param line_ending:  During ascii encoding: if not None, replace any CR,
                             LF or CRLF line ending by this string.  Default
                             None. Typical values '\r', '\n' or '\r\n'.

                             This setting is intended to facilitate re-encoding
                             of html data copied from output in a serial
                             monitor.  Typically, the data is displayed as html,
                             and copying the data from the screen eliminates all
                             html tags or html escape sequences. It may contain
                             \r or \n escapes (if show_line_endings is set), and
                             it will contain CR, LF or CRLF characters for any
                             copied line endings.  If it contains \r or \n
                             escapes, correct line endings can be restored from
                             them and the following CR, LF or CRLF can and will
                             be ignored. If it doesn't, the line endings will
                             reflect the conventions of the current platform.
                             This setting will replace them with the desired
                             line endings.

                             This is not a replacement for an 'Enter sends ...'
                             setting in a serial monitor.  Pressing enter in the
                             serial monitor should append the desired characters
                             to the string before encoding it. If local echoing
                             is enabled, it should then be decoded for local
                             display.

        :param hex_bytes_per_block: During hex decoding: if non-zero, split
                             decoded bytes in blocks of this size.

        :param hex_line_width: During hex decoding: if non-zero, limit line
                             length to this value.  At least one block will be
                             shown per line, or at least one byte if no block
                             size is configured, even if the line is shorter.

        :column:             The column in which hex output should start. This is
                             used to determine the correct position to insert
                             line breaks for hex decoding.  Initially zero,
                             meaning that the first output character is assumed
                             to be in the first column.  Updated after each
                             decode call, assuming that no other output is
                             generated. If output is generated that does not
                             come from a hex decode call, the column must be
                             adjested accordingly.  In particular,  an ascii
                             decode call does not update the column.
        """
        self.mode = mode
        self.show_line_endings = show_line_endings
        self.html_line_ending = html_line_ending
        self.html_begin_escape = html_begin_escape
        self.html_end_escape = html_end_escape
        self.line_ending = line_ending
        self.hex_bytes_per_block = hex_bytes_per_block
        self.hex_line_width = hex_line_width
        self.column = column

    def encode(self, text):
        """Encode string to raw bytes according to the current mode."""
        if self.mode in ["hex", "html-hex"]:
            return self.encode_hex(text)
        return self.encode_ascii(text)

    def decode(self, data):
        """Decode raw bytes to string according to the current mode.

        :param data: The bytes to be decoded,  as a byte string
        """
        if self.mode == "html-ascii":
            return self.decode_html_ascii(data)
        if self.mode == "html-hex":
            return self.decode_html_hex(data)
        if self.mode == "hex":
            return self.decode_hex(data)
        assert self.mode == "ascii"
        return self.decode_ascii(data)

    def encode_hex(self, text):
        """Encode string to raw bytes in hex mode.

        :param text: A string consisting of an even number of hex digits
            (lowercase or uppercase). Whitespace between pairs of hex digits is
            skipped. Whitespace inside a pair of hex digits is not allowed.
            Other characters are not allowed.
        """
        return bytes.fromhex(text)

    def decode_hex(self, data):
        """Decode raw bytes to string in hex mode.

        :param data: The bytes to be decoded, as a byte string If
            hex_bytes_per_block is non-zero, bytes are split in groups using a
            single space as separator. If hex_line_width is non-zero, the line
            width is limited to that number of columns. At least one block will
            be shown per line, even if the line is shorter. The current column
            is taken into account to determine where to insert block separators
            and line breaks. It is updated to prepare for the next decode call.
        """
        return self.__to_hex(data, " ", "\n")

    def decode_html_hex(self, data):
        """Decode raw bytes to html in hex mode.

        :param data: The bytes to be decoded,  as a byte string
        :param column: The column in which the first output character will be
            written. This information is needed for hex decoding ('hex' and
            'html-hex' modes) to align blocks and to determine where a line
            ending is needed. It is ignored for ascii decoding ('ascii' and
            'html-ascii' modes). If hex_bytes_per_block is non-zero, blocks are
            split in groups using a single html non-breaking space as separator.
            If hex_line_width is non-zero, the number of blocks per line is
            limited to the number that fits on a line of that length. At least
            one block will be shown per line, even if the line is shorter. The
            current column is taken into account to determine where to insert
            block separators and line breaks. It is updated to prepare for the
            next decode call.
        """
        return self.__to_hex(data, "&nbsp;", self.html_line_ending)

    def __to_hex(self, data, sep, eol):
        """Decode raw bytes to string in hex mode.

        :param sep: Use this string as block separator if hex_bytes_per_block is
            non-zero. Assume sep takes 1 column, regardless of its length.
        :param eol: Use this string as line separator if hex_line_width is non-
            zero. Set the current column to zero after inserting this string.
        """

        def hex(data):
            bpb = self.hex_bytes_per_block
            if bpb:
                eob = sep if len(sep) == 1 else " "
                text = data.hex(eob, -bpb)
                if len(sep) != 1:
                    text = text.replace(" ", sep)
                return text
            return data.hex()

        # Separator size is always 1,  even if the string is longer.
        # For example,  in html &nbsp; represents a single character.
        sep_size = 1
        # To limit the number of special cases in the calculations, we define an
        # 'unlimited' to be used instead of zero for an unlimited block size or
        # line width.  The value should be at least big enough so that the new
        # data fits on the current line, and it should be greater than zero when
        # there is no data.
        unlimited = self.hex_line_width + (2 + sep_size) * len(data) + 1
        bytes_per_block = (
            self.hex_bytes_per_block if self.hex_bytes_per_block else unlimited
        )
        # Make sure that the line width is enough to show at least one block.
        line_width = max(
            self.hex_line_width if self.hex_line_width else unlimited,
            2 * bytes_per_block,
        )
        # Every block occupies 2 hex chars per byte plus a separator
        block_size = 2 * bytes_per_block + sep_size
        # The last block on a line does not need a separator, and the line
        # ending does not contribute to the line width.  If we reason in terms
        # of full blocks (including a separator after the last block), the
        # available line width is larger than the user-requested line width by
        # the separator width.  The separator at the end of the line will never
        # be added.
        blocks_per_line = (line_width + sep_size) // block_size
        assert blocks_per_line > 0
        bytes_per_line = blocks_per_line * bytes_per_block
        assert bytes_per_line > 0

        # Aux function
        def adjust_column(used_blocks, bytes_to_add):
            self.column = (
                used_blocks + bytes_to_add // bytes_per_block
            ) * block_size
            pb_bytes = bytes_to_add % bytes_per_block
            if pb_bytes:
                self.column += 2 * pb_bytes
            else:
                self.column -= sep_size

        # List of lines already decoded.  These will be joined by eol once all
        # lines are computed.
        lines = []
        # Index of next byte to be decoded.
        data_index = 0
        # If there is not enough room on the current line to add a single
        # byte, start a new line.
        if self.column + 2 + sep_size > blocks_per_line * block_size:
            lines.append("")
            self.column = 0
        # If column is non-zero, the first line cannot be a complete line and
        # must be treated separately. We need to compute for how many bytes
        # room is still available and possibly write a partial block to start.
        if self.column:
            # Compute partial block. Assume at least one byte will be written:
            # unconditionally insert any spacing needed before the first byte.
            # We will insert spaces if needed to align data and blocks with
            # lines that start from column zero.
            # Count blocks that are partially or fully used.
            used_blocks = (self.column - 1) // block_size + 1
            # How much room is left is the partial block?
            pb_free_size = used_blocks * block_size - self.column
            if pb_free_size >= sep_size + 2:
                # There is room left for at least one byte in the partial block.
                pb_used_size = block_size - pb_free_size
                pb_used_bytes = (pb_used_size - 1) // 2 + 1
                pb_free_bytes = bytes_per_block - pb_used_bytes
                fill = 2 * pb_used_bytes - pb_used_size
                line = sep * fill + hex(data[0:pb_free_bytes])
                data_index = pb_free_bytes
                if pb_free_bytes < len(data):
                    # Not all data has been decoded yet.  Add a block separator
                    # before the next block. No need to fix the column yet.
                    line += sep
                else:
                    # All data has been decoded. Fix the column.
                    self.column = (
                        used_blocks * block_size - sep_size - 2 * len(data)
                    )
            else:
                # No room left for data in the partial block.  Fill with
                # separators upto the start of the next block.  No need to fix
                # the column yet.
                line = sep * pb_free_size

            # Generate any remaining blocks on this line.
            if data_index < len(data):
                # Assume that the used blocks are fully filled now, and that a
                # block separator has been added.
                free_blocks = blocks_per_line - used_blocks
                free_bytes = free_blocks * bytes_per_block
                bytes_to_add = min(len(data) - data_index, free_bytes)
                line += hex(data[data_index : data_index + bytes_to_add])
                data_index += bytes_to_add
                # Fix the column only if data was added here.  Otherwise,
                # the column was fixed above or will be fixed below.
                adjust_column(used_blocks, bytes_to_add)

            lines.append(line)

        if data_index < len(data):
            while data_index < len(data):
                bytes_to_add = min(len(data) - data_index, bytes_per_line)
                lines.append(hex(data[data_index : data_index + bytes_to_add]))
                data_index += bytes_to_add
            adjust_column(0, bytes_to_add)

        return eol.join(lines)

    def decode_html_ascii(self, data):
        """Decode raw bytes to string in html-ascii mode.

        In addition to ascii decoding,  this does the following:

         - replace special html characters by html escapes (e.g. space by
           &nbsp;)

         - insert an html_line_ending tag (default <br>) for each line ending;

         - remove \r, \n and \r\n escape sequences if show_line_endings is not
           set;

         - insert html_escape_begin and html_escape_end tags around backslash
           escape sequences.

        There is no encode_html() method that reverses these changes.  Html is
        mainly intended to be displayed on screen. Copying the displayed data
        will typically implicitly eliminate all html tags and escape sequences,
        and the resulting string can be directly ascii-encoded.

        Only printable characters are processed; non-printable characters are
        left unchanged. An ascii-decoded string contains only printable
        characters.
        """
        return self.__to_html(self.decode_ascii(data))

    def __to_html(self, text):
        """Convert an ascii-decoded string to an html-ascii decoded string.

        See decode_html() for details.
        """
        eol = re.escape(self.html_line_ending)

        def patch_eol(match):
            text = match.group()
            if text[0] == "\\":
                if self.show_line_endings:
                    return text + eol
                else:
                    return eol
            else:
                return self.__html_escape_map[text[0]]

        html = re.sub(self.__html_eol_regex, patch_eol, text)

        def patch_esc(match):
            return self.html_begin_escape + match.group() + self.html_end_escape

        return re.sub(self.__html_esc_regex, patch_esc, html)

    __html_eol_regex = re.compile(r'[\'"&<> ]|(\\r\\n|\\n|\\r)')

    __html_esc_regex = re.compile(r"(\\(x[0-9a-fA-F][0-9a-fA-F]|[\\abfnrtv]))+")

    __html_escape_map = {
        '"': "&quot;",
        "'": "&apos;",
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        " ": "&nbsp;",
    }

    def encode_ascii(self, text):
        """Encode string to raw bytes in ascii mode.

        Any backslash escape sequences in the string are interpreted.  Existing
        non-printable characters are passed unchanged into to raw bytes output,
        with one exception: CR, LF or CRLF characters that immediately follow \r
        or \n are deleted, and remaining CR, LF or CRLF characters are replaced
        by line_ending if that setting is not None. This exception is intended
        to facilitate copying from on-screen html,  as explained above for the
        line_ending setting.

        Note: an ascii-decoded string never contains non-printable characters,
        so any handling of non-printable characters does not affect the
        reversibility of ascii decoding.

        :param text: The string to be encoded.
        """

        def patch(match):
            data = match.group()
            if data[0] == ord("\\"):
                esc_char = data[1]
                if data[1] == ord("x"):
                    return bytes([int(data[2:], 16)])
                return self.__ascii_escape_encode_map[data[1]]
            if self.line_ending is None:
                return data
            return self.line_ending

        return re.sub(self.__ascii_escape_regex, patch, text.encode())

    __ascii_escape_regex = re.compile(b"\\\\(x..|[\\\\abfnrtv])|\r\n?|\n")

    __ascii_escape_encode_map = {
        ord("\\"): b"\\",  # backslash
        ord("a"): b"\a",  # bell
        ord("b"): b"\b",  # backspace
        ord("f"): b"\f",  # form feed
        ord("n"): b"\n",  # new line
        ord("r"): b"\r",  # carriage return
        ord("t"): b"\t",  # horizontal tab
        ord("v"): b"\v",  # vertical tab
    }

    def decode_ascii(self, data):
        """Decode raw bytes to string in ascii mode.

        Non-printable bytes and backslashes are replaced by a backslash escape
        sequence that will be converted to the original byte by ascii encoding.
        """
        return "".join([self.__ascii_decode_table[code] for code in data])

    __ascii_decode_table = None

    @staticmethod
    def _build_ascii_decode_table():
        temp = "\\x"
        table = [f"{temp}{code:02x}" for code in range(0, 256)]
        for code in range(32, 127):
            table[code] = chr(code)
        table[ord("\\")] = "\\\\"
        table[ord("\a")] = "\\a"
        table[ord("\b")] = "\\b"
        table[ord("\f")] = "\\f"
        table[ord("\n")] = "\\n"
        table[ord("\r")] = "\\r"
        table[ord("\t")] = "\\t"
        table[ord("\v")] = "\\v"
        Codec.__ascii_decode_table = table


Codec._build_ascii_decode_table()

if __name__ == "__main__":
    # Selftest

    print("Hello world")

    codec = Codec(
        mode="html-hex",
        show_line_endings=True,
        html_line_ending="<br>",
        html_begin_escape="<span class=yellow>",
        html_end_escape="</span>",
        line_ending=None,
        hex_line_width=20,
    )
    html = (
        codec.decode(b"\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64\x0d\x0a")
        + codec.decode(b"\x46\x6f\x6f\x62\x61\x72\x0d\x0a")
        + codec.decode(b"\x46\x6f\x6f\x62\x61\x72\x0d\x0a")
        + codec.decode(b"\x46\x6f\x6f\x62\x61\x72\x0d\x0a")
        + codec.decode(b"\x46\x6f\x6f\x62\x61\x72\x0d\x0a")
    )
    print(f"html: {html}")
    assert html == (
        "4865&nbsp;6c6c&nbsp;6f20&nbsp;576f<br>"
        "726c&nbsp;640d&nbsp;0a46&nbsp;6f6f<br>"
        "6261&nbsp;720d&nbsp;0a46&nbsp;6f6f<br>"
        "6261&nbsp;720d&nbsp;0a46&nbsp;6f6f<br>"
        "6261&nbsp;720d&nbsp;0a46&nbsp;6f6f<br>"
        "6261&nbsp;720d&nbsp;0a"
    )
    assert codec.column == 12

    test_data = [
        (
            b"foo\fbar",
            r"foo\fbar",
            " 66 6f6f 0c62 6172",
            r"foo[\f]bar",
        ),
        (
            "😀 ∑ Π ∫ ∂ √".encode(),
            r"\xf0\x9f\x98\x80 \xe2\x88\x91 \xce\xa0"
            r" \xe2\x88\xab \xe2\x88\x82 \xe2\x88\x9a",
            " f0 9f98 8020 e288\n9120 cea0 20e2 88ab\n20e2 8882 20e2 889a",
            r"[\xf0\x9f\x98\x80]&nbsp;[\xe2\x88\x91]&nbsp;[\xce\xa0]"
            r"&nbsp;[\xe2\x88\xab]&nbsp;[\xe2\x88\x82]&nbsp;[\xe2\x88\x9a]",
        ),
        (
            b"\xc3\x28\x09\r\n\\r",
            r"\xc3(\t\r\n\\r",
            " c3 2809 0d0a 5c72",
            r"[\xc3]([\t\r\n\\]r",
        ),
        ("\x06:".encode(), r"\x06:", " 06 3a", r"\x06:"),
    ]

    # Decode test
    codec = Codec(
        html_begin_escape="[",
        html_end_escape="]",
        hex_line_width=20,
    )
    for data, good, good_hex, good_html in test_data:
        print()
        text = codec.decode(data)
        print(f"bytes: {data}")
        print(f"good:  -{good}-")
        print(f"found: -{text}-")
        assert text == good
        codec.column = 1
        hex = codec.decode_hex(data)
        print(f'good hex:   -{"."*codec.column}{good_hex}-')
        print(f'found hex:  -{"."*codec.column}{hex}-')
        assert hex == good_hex
        html = codec.decode_html_ascii(data)
        print(f"good html:  -{good_html}-")
        print(f"found html: -{html}-")

    # Encode test
    for text in [
        r"hello\nworld",
        r"\xae",
        r"end\nline\zand more",
        "\x06:",
    ]:
        print()
        print(f"text:  {text}")
        data = codec.encode(text)
        print(f"bytes: {data}")
        ascii = codec.decode_ascii(data)
        print(f"ascii: {ascii}")
        codec.column = 0
        hex = codec.decode_hex(data)
        print(f"hex:   {hex}")
        html_ascii = codec.decode_html_ascii(data)
        print(f"htmla: {html_ascii}")
        codec.column = 0
        html_hex = codec.decode_html_hex(data)
        print(f"htmlx: {html_hex}")

    print()
    data = "\x80".encode()
    print(f"data: {data}")
    dec_data = codec.decode(data)
    print(f"dec:  {dec_data}")
    enc_data = codec.encode(dec_data)
    print(f"enc:  {enc_data}")
    assert enc_data == data

    codec.user_line_ending_suppresses_standard_line_ending = False
    print(codec.encode("x\\n\ny"))
    print(codec.decode(codec.encode("x\\n\ny")))
    data = b"\\n\n"
    assert codec.encode(codec.decode(data)) == data

    from hypothesis import given, settings, Verbosity, example, note
    from hypothesis.strategies import text, lists, integers
    import time

    # Test reversibility

    codec.mode = "ascii"
    print(f"Testing reversibility for {codec.mode} mode")

    @settings(max_examples=1000)
    @given(lists(integers(0, 255)))
    def test_encode_inverts_decode_1(xs):
        data = bytes(xs)
        note(f"original: {data}")
        decoded = codec.decode(data)
        note(f"decoded:  {repr(decoded)}")
        encoded = codec.encode(decoded)
        note(f"encoded:  {encoded}")
        assert encoded == data

    test_encode_inverts_decode_1()

    @settings(max_examples=300)
    @given(text())
    def test_encode_inverts_decode_2(text):
        data = text.encode()
        note(f"original: {data}")
        decoded = codec.decode(data)
        note(f"decoded:  {repr(decoded)}")
        encoded = codec.encode(decoded)
        note(f"encoded:  {encoded}")
        assert encoded == data

    test_encode_inverts_decode_2()

    codec.mode = "hex"
    print(f"Testing reversibility for {codec.mode} mode")

    @settings(max_examples=1000, deadline=300)
    @given(
        xs=lists(integers(0, 255)),
        block=integers(0, 10),
        line=integers(0, 80),
        column=integers(0, 80),
    )
    @example([0x5, 0xD9, ord("2")], 2, 1, 0)
    @example([0x5, 0xD9, ord("2")], 2, 1, 1)
    def test_hex_encode_inverts_decode(xs, block, line, column):
        codec.hex_bytes_per_block = block
        codec.hex_line_width = line
        data = bytes(xs)
        note(f'original: [{" ".join([f"{code:02x}" for code in data])}]')
        codec.column = column
        decoded = codec.decode(data)
        note(f"decoded:  {repr(decoded)}")
        encoded = codec.encode(decoded)
        note(f"encoded:  {encoded}")
        assert encoded == data

    test_hex_encode_inverts_decode()

    print("Bye")
