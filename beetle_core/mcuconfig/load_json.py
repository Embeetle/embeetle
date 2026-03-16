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
import json
import os

# Allow relative imports during stand-alone execution
__package__ = __package__ or os.path.basename(os.path.dirname(__file__))

from .model import (
    packages,
    Series,
    Pad,
    Part,
    Peripheral,
    Signal,
    Bus,
    InternalClock,
    ExternalClock,
    MuxClock,
    MultipliedClock,
    DividedClock,
    Setting,
    PadSetting,
    ConfigError,
    PadMode,
    PadType,
    Register,
    Field,
    validate_name,
    POWER,
    SettingKind,
    PeripheralSetting,
    CustomPeripheral,
    AI,
    FI,
    PU,
    PD,
    PP,
    PP_AF,
    OD,
    OD_AF,
)
from .clock_layout import set_clock_layout
from .frequency import Frequency
from .expression import (
    Expression,
    Equal,
    And,
    Or,
    Literal,
    Always,
    Never,
    parse,
    truncate,
)
from .svd_to_json import svd_to_json

type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None


# For debugging: print(_json(data))
def _json(data: JSON):
    return json.dumps(data, indent=4)


def truncate(data):
    text = str(data)
    max = 40
    ellipsis = "..."
    return text if len(text) <= max else text[: max - len(ellipsis)] + ellipsis


def fatal(message):
    raise ConfigError(message)


def load_part(json_path: str, part_name: str) -> Part:
    """Load part from JSON file."""
    # print(f"load {part_name} from {json_path} [")
    series = _load_series(json_path)
    part = series.part(part_name)
    if part is None:
        raise ConfigError(f"{json_path}: part '{part_name}' not found")
    series.set_focus(part)
    series.freeze()
    # print("]")
    return part


class Index:
    """Enable part loading by name based on indexed JSON files."""

    def __init__(self):
        self._map = {}

    def load_part(self, part_name: str):
        filename = self._map.get(part_name)
        if not filename:
            raise ConfigError(f"unknown part '{part_name}'")
        return load_part(filename, part_name)

    def add_file(self, series_filename: str):
        data = _load_json(series_filename)
        series_name = data.get("series")
        if type(series_name) is not str:
            raise ConfigError(
                f"{series_filename}: series name should be a string "
                f"instead of '{series_name}'"
            )
        parts_data = data.get("parts")
        if type(parts_data) is not list:
            raise ConfigError(f"{series_filename}: 'parts' should be a list")
        for part_data in parts_data:
            part_name = part_data.get("name")
            if type(part_name) is not str:
                raise ConfigError(
                    f"{series_filename}: part name should be a string "
                    f"instead of '{part_name}'"
                )
            self._map[part_name] = series_filename

    def load(self, index_filename: str):
        with open(index_filename) as file:
            data = json.load(file)
            if type(data) is not dict:
                raise ConfigError(
                    f"invalid config index data in '{index_filename}'"
                )
            self._map.update(data)

    def save(self, index_filename: str):
        with open(index_filename, "w") as file:
            json.dump(self._map, file)


def _load_json(json_path: str):
    # _data = purefunctions.load_json_file_with_comments(json_path)
    # if _data is None:
    #    raise RuntimeError(f"CANNOT LOAD JSON FILE {json_path}")
    # return _data
    try:
        with open(
            json_path, "r", encoding="utf-8", newline="\n", errors="replace"
        ) as file:
            if os.path.splitext(json_path)[1] == ".json5":
                data = json.loads(
                    "".join(
                        "\n" if line.strip().startswith(("//", "#")) else line
                        for line in file
                    )
                )
            else:
                data = json.load(file)
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"{json_path}:{error.lineno}:{error.colno}: {error.msg}"
        ) from None
    return data


def _load_series(json_path: str) -> Series:
    # print(f"load {json_path}")
    data = _load_json(json_path)

    def get_tag(data, tag: str, expected_type):
        tag_data = data.get(tag)
        if type(tag_data) != expected_type:
            if tag_data is None:
                fatal(f"missing '{tag}' tag in '{truncate(data)}'")
            else:
                fatal(
                    f"value '{truncate(tag_data)}' for '{tag}'"
                    f" is not a {expected_type.__name__}"
                )
        return tag_data

    def get_list_of_dicts(data, tag: str, keykey="name"):
        """Get a list of dicts.

        If tag data is a dict of dicts, transform it into a list of dicts by
        adding the top level key as a field to the sub dicts.
        """
        tag_data = data.get(tag)
        if type(tag_data) not in [dict, list]:
            if tag_data is None:
                fatal(f"missing '{tag}' tag in '{truncate(data)}'")
            else:
                fatal(
                    f"value for '{tag}' is not a list or dict: "
                    f"{truncate(tag_data)}"
                )
        if type(tag_data) is dict:
            list_data = []
            for key, value in tag_data.items():
                if type(value) is not dict:
                    fatal(
                        f"value for '{tag} {key}' is not a dict: "
                        f"{truncate(value)}"
                    )
                value[keykey] = key
                list_data.append(value)
        else:
            list_data = tag_data
        for item in list_data:
            if type(item) is not dict:
                fatal(f"item {item} in '{tag}' is not a dict")
        return list_data

    def get_optional_tag(data, tag: str, expected_type, fallback=None):
        if data.get(tag) is None:
            return fallback
        else:
            return get_tag(data, tag, expected_type)

    def get_optional_list_of_dicts(data, tag: str, keykey="name"):
        if data.get(tag) is None:
            return []
        else:
            return get_list_of_dicts(data, tag, keykey)

    def get_description(data, default="") -> str:
        return get_optional_tag(data, "description", str) or default

    def get_number(data, tag: str) -> int:
        tag_data = data.get(tag)
        if tag_data is None:
            fatal(f"missing '{tag}' tag in '{truncate(data)}'")
        if type(tag_data) is int:
            number = tag_data
        elif type(tag_data) is str:
            number = parse(tag_data).value
        else:
            fatal(
                f"value '{truncate(tag_data)}' for '{tag}'"
                f" is not an int or a string"
            )
        if number < 0:
            fatal(f"value for '{tag}' cannot be negative in '{truncate(data)}'")
        return number

    def get_optional_frequency(data, tag: str) -> Optional[Frequency]:
        value = data.get(tag)
        if value is None:
            return None
        return Frequency(value)

    def get_optional_number(data, tag: str, default: int = 0) -> int:
        if data.get(tag) is None:
            return default
        else:
            return get_number(data, tag)

    def get_mode(mode_name):
        mode = series.pad_mode(mode_name)
        if not mode:
            fatal(f"unknown mode '{mode_name}' for pad type '{name}'")
        return mode

    scope_names: {str} = set()

    def load_svd_data(svd_data):
        for scope_name, scope_data in get_tag(
            svd_data, "peripherals", dict
        ).items():
            scope_names.add(scope_name)
            for register_name, register_data in get_tag(
                scope_data, "registers", dict
            ).items():
                try:
                    register_description = get_description(register_data)
                    width = get_number(register_data, "size")
                    register = Register(
                        series,
                        scope=scope_name,
                        name=register_name,
                        description=register_description,
                        address=get_number(register_data, "address"),
                        width=width,
                        reset_value=get_optional_number(
                            register_data, "reset_value"
                        ),
                        reset_mask=get_optional_number(
                            register_data, "reset_mask", (1 << width) - 1
                        ),
                    )
                except ConfigError as error:
                    raise ConfigError(
                        f"{error} while processing {scope_name}.{register_name}"
                    ) from None
                fields_data = get_tag(register_data, "fields", dict)
                for field_name, field_data in fields_data.items():
                    try:
                        field = Field(
                            register=register,
                            name=field_name,
                            description=get_description(field_data),
                            offset=get_number(field_data, "bit_offset"),
                            width=get_number(field_data, "bit_width"),
                        )
                        # print(f"created field {field}")
                    except ConfigError as error:
                        raise ConfigError(
                            f"{error} while processing "
                            f"{register}.{field_name}"
                        ) from None

    series_name = get_tag(data, "series", str)

    dir_path, base_name = os.path.split(json_path)
    # if series_name != os.path.splitext(base_name)[0]:
    #    fatal(
    #        f"series name '{series_name}' "
    #        f"does not match file name '{base_name}'"
    #    )

    svd_data = data.get("svd_data")
    if type(svd_data) is str:
        filename = os.path.join(dir_path, svd_data)
        extension = os.path.splitext(svd_data)[1].lower()
        if extension == ".json":
            svd_data = _load_json(filename)
        elif extension == ".svd":
            svd_data = svd_to_json(filename)
        else:
            fatal(f"unknown file type '{svd_data}' for SVD data")
    else:
        filename = json_path
    if type(svd_data) is not dict:
        fatal(f"unexpected SVD data type {type(svd_data)}")
    series = Series(
        name=series_name,
        description=get_description(data),
        address_unit_bits=get_optional_number(
            svd_data,
            "address_unit_bits",
            get_optional_number(data, "address_unit_bits", 8),
        ),
    )
    try:
        load_svd_data(svd_data)
    except ConfigError as error:
        raise ConfigError(f"{error} in {filename}") from None

    def load_mode_list(data, context: str) -> list[PadMode]:
        return (
            [
                series.pad_mode(name)
                or fatal(f"unknown mode '{mode_name}' for {context}")
                for name in ([data] if type(data) is str else data)
            ]
            if data
            else series.pad_modes
        )

    def load_and_expand_setting_data(
        data,
        parse: Callable[[str], Expression] = series.expression,
        expand: Callable[[str], str] = _null_expand,
    ) -> Iterable[dict[str, Any]]:
        """Load and parameter-expand json data for a plain or pad setting.

        Return an iterable over dicts,  one dict for each expanded setting.

        Data is a dict representing json data for the setting constructor.
        Returning this as a dict allows us to reuse this function for different
        setting classes, such as PeripheralSetting, PadSetting and ClockSetting,
        each time adding a different additional parameter.
        """
        return (
            load_setting_data(data, parse, expand2)
            for expand2 in _expand_parameters(data, expand)
        )

    def load_setting_data(
        data,
        parse: Callable[[str], Expression] = series.expression,
        expand: Callable[[str], str] = _null_expand,
        default_label: str = "",
    ) -> dict[str, Any]:
        """Load json data for a setting, expanding any expandable fields.

        Return a dict with parameters for the Setting constructor. In contrast
        to load_and_expand_setting_data, this ignores parameter settings in data
        and returns a single dict instead of an iterable over dicts. See
        load_and_expand_setting_data for details.
        """

        def load_value(value_text: str) -> Iterable[int]:
            """Parse value, including x for dont-cares in a binary value.

            Return a list of values including all values matching an x pattern.
            """
            try:
                if value_text.startswith("0b"):
                    return (
                        int(v, 2) for v in _expand_bit_pattern(value_text[2:])
                    )
                if value_text.startswith("0x"):
                    return [int(value_text[2:], 16)]
                if value_text.startswith("0") and not value_text == "0":
                    raise ValueError()
                return [int(value_text)]
            except ValueError:
                fatal(f"invalid value '{value_text}' for '{label}' setting")

        description = expand(get_optional_tag(data, "description", str) or "")
        label = (
            expand(get_optional_tag(data, "label", str) or "")
            or default_label
            or description
        )
        if not label:
            fatal(f"Setting '{data}' has neither label nor description")
        try:
            description = description or label
            predicate = parse(
                expand(get_optional_tag(data, "predicate", str) or "1")
            )
            selector = parse(expand(get_tag(data, "selector", str)))
            sel2val = None
            minimum = None
            maximum = None
            options = None
            options_data = data.get("values")
            if options_data is not None:
                kind = SettingKind.LIST
                if type(options_data) is list:
                    options = options_data
                    for option in options:
                        if not type(option) is str:
                            raise ConfigError(
                                f"option {option} is not a string"
                            )
                elif type(options_data) is dict:
                    sel2val = {}
                    options = []
                    for key, option in options_data.items():
                        if not type(option) is str:
                            raise ConfigError(
                                f"option {option} is not a string"
                            )
                        index = len(options)
                        options.append(option)
                        try:
                            for value in load_value(key):
                                sel2val[value] = index
                        except ConfigError as error:
                            print(f"options_data: {_json(options_data)}")
                            raise error from None
            else:
                if selector.width == 1:
                    kind = SettingKind.FLAG
                else:
                    kind = SettingKind.NUMBER
                    minimum = get_optional_number(data, "minimum")
                    maximum = get_optional_number(data, "maximum")
                    if not maximum:
                        if selector.width is not None:
                            maximum = (1 << selector.width) - 1
                        else:
                            # fatal(
                            #  f"maximum value required for numeric setting "
                            #  f"'{label}' (cannot derive maximum for {selector}"
                            # )
                            # TODO: I need to derive maximum value for baud rate,
                            # which depends on maximum clock speed and does not
                            # have a bit width. For now, return a very large
                            # value.
                            maximum = 1000000000

            return dict(
                label=label,
                description=description,
                kind=kind,
                predicate=predicate,
                selector=selector,
                sel2val=sel2val,
                options=options,
                minimum=minimum,
                maximum=maximum,
            )
        except ConfigError as error:
            raise ConfigError(f"'{label}' {error}") from None

    def load_pad_types(series_data):
        pins_data = get_tag(series_data, "pins", dict)
        for name, data in get_tag(pins_data, "types", dict).items():
            mode_data = data.get("mode")
            if not mode_data:
                modes = set()
            elif type(mode_data) is str:
                modes = {get_mode(mode_data)}
            else:
                modes = {get_mode(name) for name in get_tag(data, "mode", list)}

            def get_kind(kind_name):
                kind = series.pad_kind(kind_name)
                if not kind:
                    fatal(f"unknown kind '{kind_name}' for pad type '{name}'")
                return kind

            kind = get_kind(get_tag(data, "kind", str))
            PadType(
                series=series,
                name=name,
                desc=str(data.get("description") or name),
                kind=kind,
                modes=modes,
            )

    def load_pad_config(series_data):
        pins_data = get_tag(series_data, "pins", dict)
        for name, data in get_tag(pins_data, "config", dict).items():
            settings_data = data.get("settings")
            mode_settings = load_pad_mode_settings(name, data)
            map_selector_text = get_optional_tag(data, "map_selector", str)
            enable_text = get_optional_tag(data, "enable", str)
            for expand in _expand_parameters(data):
                load_single_pad_config(
                    name=name,
                    settings_data=settings_data,
                    mode_settings=mode_settings,
                    map_selector_text=map_selector_text,
                    enable_text=enable_text,
                    expand=expand,
                )

    map_selector_by_pad = {}

    def load_single_pad_config(
        name: str,
        settings_data: Any,
        mode_settings: dict["Mode", dict[str, str]],
        map_selector_text: Optional[str],
        enable_text: Optional[str],
        expand: Callable[[str], str],
    ):
        """Load and expand pad configuration data.

        'name' is the potentially parameterized pad name.

        'settings_data' is json data with pad settings, in other words the data
            found in the json file at pins.config.<name>.settings

        'mode_settings' is a dict listing required settings for each mode. This
            is the return value of load_pad_mode_settings(...) below.

        'map_selector_text' is an optional string containing the selector
            expression for the signal (function) mapped to the pad. It selects a
            column in the global map table. The corresponding expression will be
            stored in the map_selector_by_pad dict.

        'enable_text' is an optional string containing the enable expression for
            the pad. It can also be the enable expression for the port to which
            the pad belongs. It must be true to use the pad.
        """
        pad_name = expand(name)
        pad = series.pad(pad_name)
        if not pad:
            # Only complain about unknown pad if pad name was not expanded.
            # A parametrized pad name does not have to exist for each expansion.
            if name == pad_name:
                fatal(f"unknown pad '{pad_name}' in pad_config")
            return
        if enable_text is not None:
            pad._set_enable(series.expression(expand(enable_text)))
        mode_predicates = {
            mode: And.join(
                Equal(
                    series.expression(expand(selector)),
                    Literal(int(value, base=2)),
                )
                for selector, value in settings.items()
            )
            for mode, settings in mode_settings.items()
            if not pad.type.modes or mode in pad.type.modes
        }
        if settings_data is not None:
            # Backward compatibility: convert dict to list
            if type(settings_data) is dict:
                data = []
                for setting_key, setting_data in settings_data.items():
                    if type(setting_data) is not dict:
                        fatal(
                            f"pad {name} setting {setting_key} data "
                            "must be a dict"
                        )
                    setting_data["key"] = setting_key
                    data.append(setting_data)
                settings_data = data
            # Load pad settings
            if type(settings_data) is not list:
                fatal(f"pad {name} settings must be a list")

            modes = (
                set(
                    load_mode_list(
                        setting_data.get("only_for_mode"),
                        context=f"pad config for {pad_name}",
                    )
                )
                & pad.type.modes
            )
            if name == pad_name:
                for mode in modes:
                    if mode not in pad.possible_modes:
                        fatal(
                            f"mode '{mode}' not available " f"for pad '{pad}'"
                        )
            for params in load_and_expand_setting_data(
                data=setting_data,
                parse=series.expression,
                expand=expand,
            ):
                setting = PadSetting(pad=pad, **params, modes=modes)
                # Potential values of the setting that are not mentioned in
                # the settings data are assumed to be 'reserved' and should
                # not be used.
                # It is essential to avoid reserved values when applying a mode
                # to a pad for which this setting is applicable, because
                # reserved values can enable a different mode. See CH32V003,
                # where the reserved value "00" for the output speed of a pad
                # enables an input mode instead of an output mode.
                # To implement this, we add to each mode predicate an expression
                # called nre or not-reserved-expression that is true iff the
                # setting is valid for that mode. When you select that mode, the
                # mode predicate is forced to be true, so the setting is also
                # forced to a non-reserved value.
                if setting.has_reserved_values:
                    nre = setting.not_reserved_expression()
                    for mode in modes:
                        mode_predicate = mode_predicates.get(mode)
                        if mode_predicate:
                            mode_predicates[mode] = And(
                                mode_predicate,
                                setting.not_reserved_expression(),
                            )
        # Add mode options to pad
        for mode, predicate in mode_predicates.items():
            pad._add_mode_option(mode, predicate)
        if map_selector_text:
            map_selector = series.expression(expand(map_selector_text))
            map_selector_by_pad[pad] = map_selector
            if not map_selector.is_assignable:
                fatal(f"map selector '{map_selector_text}' is not assignable")

    def load_pad_mode_settings(
        pad_name: str,
        pad_config_data,
    ) -> dict["Mode", dict[str, str]]:
        """Load the pins.config.<pad_name>.mode data.

        'pad_name' is a potentially parameterized pad name.

        'pad_config_data' is the pad configuration data to be loaded. It should
               include a 'mode' field. The mode field must be one of:

                - a mode name as a string

                - a dict with selector expressions as keys and value dicts
                  as data. The keys of the value dict are the possible values of
                  the selector. The value is either a single mode or a list of
                  modes for which the selector must have this value.

        Returns a mode dict. The key of a mode dict is a mode, and the value is
        a mode selection dict.  The key of a mode selection dict is a selector
        expression, and the value is the value this selector must have for the
        mode to be applied. If the selection dict is empty,  the mode is applied
        unconditionally. So:

        {
            "<mode-1>": {
                "<selector-expression-1>" : "<value-1>",
                "<selector-expression-2>" : "<value-2>",
                ...
            },
            "<mode-2>": {
                ...
            },
            ...
        }

        Selectors and values are returned as strings and must be parsed and
        checked later, when the pad name is expanded.
        """

        def get_mode(mode_name) -> PadMode:
            mode = series.pad_mode(mode_name)
            if not mode:
                fatal(f"unknown mode '{mode_name}' for pad config {pad_name}")
            return mode

        mode_settings: Dict[Mode, Dict[str, str]] = {}
        mode_data = pad_config_data.get("mode")
        if type(mode_data) is str:
            mode_settings[get_mode(mode_data)] = {}
        elif type(mode_data) is dict:
            for selector_text, data in mode_data.items():
                for selector_value, mode_names in data.items():
                    for mode_name in mode_names:
                        mode = get_mode(mode_name)
                        settings = mode_settings.get(mode)
                        if not settings:
                            settings = {}
                            mode_settings[mode] = settings
                        settings[selector_text] = selector_value
        return mode_settings

    def load_parts_and_pads(series_data):
        def get_package(data):
            package_name = get_tag(data, "package", str)
            package = packages.get(package_name)
            if not package:
                fatal(f"unknown package '{package_name}')")
            return package

        parts = []
        layout_dict = {}
        for data in get_tag(series_data, "parts", list):
            part = Part(
                series=series,
                name=get_tag(data, "name", str),
                package=get_package(data),
            )
            parts.append(part)
            layout_name = data.get("wirebonding-layout") or data.get("package")
            layout_parts = layout_dict.get(layout_name)
            if not layout_parts:
                layout_parts = []
                layout_dict[layout_name] = layout_parts
            layout_parts.append(part)

        pins_data = get_tag(series_data, "pins", dict)

        layout_order = pins_data.get("wirebonding-layout")
        if layout_order is not None:
            layout_parts_list = [
                layout_dict.get(layout_name) for layout_name in layout_order
            ]
        else:
            layout_parts_list = [[part] for part in parts]
        for pad_data in get_list_of_dicts(pins_data, "wirebonding", "pad"):
            pad_name = get_tag(pad_data, "pad", str)
            type_name = get_tag(pad_data, "type", str)
            type = series.pad_type(type_name)
            if not type:
                fatal(f"unknown type '{type_name}' for pad '{pad_name}'")
            # Allow duplicate pad names, avoiding pad duplication
            pad = series.pad(pad_name)
            if pad:
                if pad.type != type:
                    fatal(
                        f"Duplicate pads '{name}' with types '{pad.type}' "
                        f"and '{type}'"
                    )
            else:
                pad = Pad(name=pad_name, type=type)
                assert series.pad(pad_name) == pad
            pins = get_tag(pad_data, "pins", list)
            if len(pins) != len(layout_parts_list):
                fatal(
                    f"number of pins for {pad_name} ({len(pins)}) "
                    f"does not match number of part layouts "
                    f"({len(layout_parts_list)})"
                )
            for layout_index, pin_name in enumerate(pins):
                if pin_name is not None:
                    for part in layout_parts_list[layout_index]:
                        pin = part.pin(str(pin_name))
                        if pin is None:
                            fatal(f"unknown pin {pin_name} for '{pad}'")
                        part._bond(pad, pin)

    def load_peripherals(series_data):
        for peri_data in get_list_of_dicts(series_data, "peripherals"):
            peri_name = get_tag(peri_data, "name", str)
            for expand in _expand_parameters(peri_data):
                load_peripheral(peri_name, peri_data, expand=expand)

    def load_peripheral(peri_name_template, peri_data, expand):
        peri_name = expand(peri_name_template)
        try:
            scope_data = peri_data.get("scope", peri_name)
            scope_list = (
                scope_data if type(scope_data) is list else [scope_data]
            )
            scopes = {
                expand(scope) for scope in scope_list if type(scope) is str
            }
            bus = bus_map.get(peri_name)
            if not bus:
                # If all scopes (SVD peripherals) are on the same bus, use that
                # bus. For example, for GPIO, if all GPIOx are on the same bus,
                # associate GPIO with that bus. TODO: what if GPIOx peripherals
                # are on different busses?  Currently, when creating the clock
                # tree, we create a single ClockSink for all *peripherals* on
                # the same bus; we should actually create it for all *scopes* on
                # the same bus. The scopes are connected to a bus, not the
                # peripherals.  So we need a Scope object in our mode.
                busses = {
                    b
                    for b in (bus_map.get(scope) for scope in scopes)
                    if b is not None
                }
                if len(busses) == 1:
                    bus = next(iter(busses))
            if bus:
                expand = _expand_parameter("bus", bus.name, expand)
                expand = _expand_parameter("bus.clock", bus.clock.name, expand)
            description = expand(peri_data.get("description", ""))

            def get_predicate(name: str) -> Expression:
                predicate = get_optional_tag(peri_data, name, str)
                if predicate is None:
                    return Always
                else:
                    return series.scoped_expression(expand(predicate), scopes)

            peripheral_enable_predicate = get_predicate("enable")
            clock_enable_predicate = get_predicate("clock-enable")
            custom_modes_data = get_optional_tag(
                peri_data, "custom-signal-modes", list, []
            )
            clocks = peri2clock_map.get(peri_name, set())
            for scope in scopes:
                clocks |= peri2clock_map.get(scope, set())
            clock = series.clock(peri_name)
            if clock:
                clocks.add(clock)
            if custom_modes_data:
                peripheral = CustomPeripheral(
                    modes=[get_mode(d) for d in custom_modes_data],
                    series=series,
                    scopes=scopes,
                    name=peri_name,
                    description=description,
                    peripheral_enable_predicate=peripheral_enable_predicate,
                    clock_enable_predicate=clock_enable_predicate,
                    clocks=clocks,
                    bus=bus,
                )
            else:
                peripheral = Peripheral(
                    series=series,
                    scopes=scopes,
                    name=peri_name,
                    description=description,
                    peripheral_enable_predicate=peripheral_enable_predicate,
                    clock_enable_predicate=clock_enable_predicate,
                    clocks=clocks,
                    bus=bus,
                )
            load_signals(peripheral, peri_data, expand)
            map_data = get_optional_tag(peri_data, "map", dict)
            if map_data:
                load_peripheral_map(peripheral, map_data, expand)
            load_peripheral_settings(peripheral, peri_data, expand)
        except ConfigError as error:
            error.args = (f"in data for '{peri_name}': {error}",)
            raise error from None

    def load_peripheral_settings(peripheral, peri_data, expand):
        for setting_data in get_optional_list_of_dicts(
            peri_data, "settings", "selector"
        ):
            # print(f"load peripheral {peripheral} setting: {setting_data}")
            for params in load_and_expand_setting_data(
                data=setting_data, parse=peripheral.expression, expand=expand
            ):
                PeripheralSetting(peripheral=peripheral, **params)

    def load_signals(peripheral, data, expand):
        if not "signals" in data:
            return
        signals_data = get_list_of_dicts(data, "signals", "name")
        for signal_data in signals_data:
            signal_name = get_tag(signal_data, "name", str)
            nr_of_expansions = _count_expansions(signal_data, expand)
            map_data = signal_data.get("map")
            if map_data:
                if type(map_data) is not list:
                    map_data = [map_data]
                if len(map_data) != nr_of_expansions:
                    fatal(
                        f"map size {len(map_data)} does not match number"
                        f" of parameter values {nr_of_expansions}"
                    )
            for i, expand2 in enumerate(
                _expand_parameters(signal_data, expand=expand)
            ):
                load_signal(
                    peripheral=peripheral,
                    name_template=signal_name,
                    data=signal_data,
                    map_data=map_data[i] if map_data else None,
                    expand=expand2,
                )

    def load_signal(peripheral, name_template, data, map_data, expand):
        name = expand(name_template)

        def load_mode_predicates(mode_data) -> dict[PadMode, Expression]:
            if mode_data is None:
                return None

            def add_mode_option(mode_name, predicate_text=None):
                if type(mode_name) is not str:
                    fatal(
                        f"mode name must be string instead of "
                        f"'{mode_name}' for {peripheral}.{name}"
                    )
                mode = series.pad_mode(mode_name)
                assert mode is not PP_AF, f"{peripheral}.{name} {mode_data}"
                assert mode is not OD_AF, f"{peripheral}.{name} {mode_data}"
                if mode is PP:
                    mode = PP_AF
                elif mode is OD:
                    mode = OD_AF
                if not mode:
                    fatal(f"unknown mode '{mode_name}' for {peripheral}.{name}")
                predicate = (
                    peripheral.expression(expand(predicate_text))
                    if predicate_text is not None
                    else Always
                )
                predicates = modes.get(mode, [])
                if not predicates:
                    modes[mode] = predicates
                predicates.append(predicate)

            modes = {}
            if type(mode_data) is str:
                add_mode_option(mode_data)
            elif type(mode_data) is list:
                for mode_name in mode_data:
                    if type(mode_name) is str:
                        add_mode_option(mode_name)
            elif type(mode_data) is dict:
                for predicate_text, mode_value in mode_data.items():
                    if type(mode_value) is str:
                        add_mode_option(mode_value, predicate_text)
                    elif type(mode_value) is list:
                        for mode_name in mode_value:
                            if type(mode_name) is str:
                                add_mode_option(mode_name, predicate_text)
            return {
                mode: Or.join(predicates) for mode, predicates in modes.items()
            }

        enable_text = get_optional_tag(data, "enable", str)
        if enable_text is None:
            enable_predicate = Always
        else:
            enable_predicate = peripheral.expression(expand(enable_text))
        signal = Signal(
            peripheral=peripheral,
            name=name,
            description=expand(data.get("description", "")),
            enable_predicate=enable_predicate,
            mode_predicates=load_mode_predicates(data.get("mode")),
        )
        if map_data is None or type(map_data) is str:
            pad = series.pad(map_data or name)
            if pad:
                series._map(signal, pad)
            elif map_data:
                fatal(f"unknown pad '{map_data}' for {signal}")
        else:
            fatal(
                f"pad name expected instead of {map_data} "
                f"in map data for {signal}"
            )

    def load_peripheral_map(peripheral, map_data, expand):
        for data in map_data.values():
            if type(data) is str:
                load_fixed_peripheral_map(peripheral, map_data, expand)
            elif type(data) is dict:
                load_remapping_peripheral_map(peripheral, map_data, expand)
            else:
                fatal("unexpected peripheral {peripheral} map format {data}")
            break

    def load_fixed_peripheral_map(peripheral, map_data, expand):
        for signal_str, pad_str in map_data.items():
            signal_name = expand(signal_str)
            pad_name = expand(pad_str)
            signal = peripheral.signal(signal_name)
            if not signal:
                fatal(f"unknown signal '{signal_name}' for {peripheral} map")
            pad = peripheral.series.pad(pad_name)
            if not pad:
                fatal(f"unknown pad '{pad_name}' for {peripheral} map")
            peripheral.series._map(signal, pad, Always)

    def load_remapping_peripheral_map(peripheral, map_data, expand):
        for expr_str, expr_data in map_data.items():
            selector = peripheral.expression(expand(expr_str))
            if not selector.is_assignable:
                fatal(f"map selector '{expr_str}' is not assignable")
            if type(expr_data) != dict:
                fatal(f"data for {expr_str} is not a dict")
            width = selector.width
            # Map table has 1<<width columns (one for each selector value) and a
            # row for each signal in expr_data.  We build the table explicitly
            # to detect and remove duplicate columns.
            row_headers = []
            columns = [[] for index in range(1 << width)]
            for signal_str, signal_data in expr_data.items():
                signal_name = expand(signal_str)
                signal = peripheral.signal(signal_name)
                if not signal:
                    fatal(
                        f"unknown signal '{signal_name}' for {peripheral}"
                        f" {expr_str} map"
                    )
                if type(signal_data) != list:
                    fatal(f"map data for {signal_name} is not a list")
                if len(signal_data) != (1 << width):
                    fatal(
                        f"map data for expression {expr_str} with width "
                        f"{width} must contain {1 << width} pads; "
                        f"found {len(expr_data)} pads"
                    )
                row_headers.append(signal)
                for index, pad_str in enumerate(signal_data):
                    if pad_str is None:
                        pad = None
                    else:
                        pad_name = expand(pad_str)
                        pad = peripheral.series.pad(pad_name)
                        if not pad:
                            fatal(
                                f"unknown pad '{pad_name}' for "
                                f"{peripheral} {expr_str} {signal_name} map"
                            )
                    columns[index].append(pad)
            unique_columns = {}
            for index, column in enumerate(columns):
                predicate = Equal(selector, Literal(index, width))
                key = tuple(column)
                if key in unique_columns:
                    unique_columns[key] = Or(unique_columns[key], predicate)
                else:
                    unique_columns[key] = predicate
            for column, predicate in unique_columns.items():
                for signal, pad in zip(row_headers, column):
                    if pad:
                        peripheral.series._map(signal, pad, predicate)

    def load_global_map(series_data):
        # print("load global map")
        pins_data = get_tag(series_data, "pins", dict)
        map_data = get_optional_tag(pins_data, "map", dict)
        if map_data is None:
            return
        for pad_name, map_row_data in map_data.items():
            # print(f"  load map for {pad_name}")
            pad = series.pad(pad_name)
            if pad is None:
                fatal(f"unknown pad '{pad_name}' in map")
            selector = map_selector_by_pad.get(pad)
            if selector is None:
                fatal(f"no selector expression for {pad}")
            if type(map_row_data) is not list:
                fatal(f"map data for pad {pad} is not a list")
            width = selector.width
            # Map table has 1<<width columns (one for each selector value)
            if len(map_row_data) != (1 << width):
                fatal(
                    f"map data for pad {pad} has selector expression "
                    f"{selector} with width {width}, so must contain "
                    f"{1 << width} entriess; "
                    f"found {len(map_row_data)} entries"
                )
            unassigned_values = []
            for selector_value, signal_data in enumerate(map_row_data):
                # print(f"    column {selector_value}: {signal_data}")
                if signal_data is None:
                    unassigned_values.append(selector_value)
                    continue
                if type(signal_data) is str:
                    signal_data = [signal_data]
                for signal_name in signal_data:
                    signal = series.signal(signal_name)
                    if not signal:
                        fatal(
                            f"unknown signal '{signal_name}' in map column "
                            f"{selector_value} for pad '{pad_name}'"
                        )
                    predicate = Equal(selector, Literal(selector_value, width))
                    # print(f"map {signal} to {pad} when {predicate}")
                    series._map(signal, pad, predicate, True)
            if len(unassigned_values) == (1 << width):
                pad._set_no_altfun_predicate(Always)
            else:
                pad._set_no_altfun_predicate(
                    Or.join(
                        Equal(selector, Literal(selector_value, width))
                        for selector_value in unassigned_values
                    )
                )

    def load_clock_tree(series_data):
        clock_tree_data = get_tag(series_data, "clock-tree", dict)
        load_clocks(clock_tree_data)

    def load_clocks(clock_tree_data):
        data = get_tag(clock_tree_data, "clocks", dict)
        for name, clock_data in data.items():
            description = clock_data.get("description", "")

            def get_clock(clock_name):
                clock = series.clock(clock_name)
                if not clock:
                    fatal(
                        f"unknown input clock '{clock_name}' for clock {name}"
                    )
                return clock

            def get_expression(key):
                value = clock_data.get(key)
                if type(value) != str:
                    if not value:
                        fatal(f"missing '{key}' for {name}")
                    else:
                        fatal(f"'{key}' for {name} must be a string")
                return series.expression(value)

            def get_optional_expression(key, fallback=None) -> Expression:
                if clock_data.get(key) is None:
                    return fallback
                return get_expression(key)

            def check_positive_int(label, value):
                if type(value) != int:
                    fatal(f"{label} '{value}' for {name} must be an integer")
                if value <= 0:
                    fatal(f"{label} for {name} must be positive")
                return value

            def get_value_and_optional_setting() -> (
                Expression,
                Setting | None,
            ):
                if clock_data.get("selector"):
                    # setting = Setting(**load_setting_data(
                    #    clock_data,
                    #    parse = series.expression,
                    #    default_label = name,
                    # ))
                    # return (setting.selector, setting)
                    return (
                        series.scoped_expression(
                            clock_data.get("selector"), {name}
                        ),
                        None,
                    )

                data = clock_data.get("value")
                if data is None:
                    fatal(f"Missing 'selector' or 'value' tag for {name} clock")
                if type(data) is int:
                    if data == 0:
                        fatal(f"Value for {name} clock cannot be zero")
                    return (Literal(data), None)
                elif type(data) is str:
                    return (series.scoped_expression(data, {name}), None)
                else:
                    fatal(
                        f"value '{truncate(data)}' for 'value' tag"
                        f" is not an int or a string"
                    )

            enable_predicate = get_optional_expression("enable") or Always
            ready_predicate = get_optional_expression("ready") or Always
            if not ready_predicate.is_always_true and not isinstance(
                ready_predicate, Field
            ):
                # In generated C code, we must be able to test the ready
                # predicate, which means that we must be able to generate an
                # equivalent C expression. This is currently only implemented
                # for fields.  An always true predicate suppresses the
                # generation of the test in C code, so is also acceptable. Other
                # expressions are not supported yet.
                fatal(
                    f"unsupported ready predicate '{ready_predicate}'"
                    f" for clock {name}"
                )
            common_args = {
                "series": series,
                "name": name,
                "description": description,
                "enable_predicate": enable_predicate,
                "ready_predicate": ready_predicate,
            }
            kind = clock_data.get("kind")
            match kind:
                case "internal":
                    frequency = Frequency(clock_data.get("freq"))
                    # print(f'Internal clock {name} {frequency}')
                    clock = InternalClock(
                        frequency=frequency,
                        **common_args,
                    )
                case "external":
                    min_freq = get_optional_frequency(clock_data, "min_freq")
                    max_freq = get_optional_frequency(clock_data, "max_freq")
                    bypass_predicate = get_optional_expression("bypass", Always)
                    # print(f'External clock {name}'
                    #      f' {minimum_frequency}:{maximum_frequency}'
                    # )
                    clock = ExternalClock(
                        minimum_frequency=min_freq,
                        maximum_frequency=max_freq,
                        bypass_predicate=bypass_predicate,
                        **common_args,
                    )
                    xin = get_optional_tag(clock_data, "xin", str)
                    xout = get_optional_tag(clock_data, "xout", str)
                    external_clock_signals.append((clock, xin, xout))
                case "mux":
                    selector = get_expression("selector")
                    input_names = get_tag(clock_data, "inputs", list)
                    inputs = [get_clock(name) for name in input_names]
                    # print(f"Selected clock {name} "
                    #      f"selector={selector} (width={selector.width}) "
                    #      f"{input_names}')"
                    # )
                    clock = MuxClock(
                        inputs=inputs,
                        selector=selector,
                        **common_args,
                    )
                case "multiplier":
                    input = get_clock(clock_data.get("input"))
                    expression, setting = get_value_and_optional_setting()
                    clock = MultipliedClock(
                        input=input,
                        expression=expression,
                        setting=setting,
                        **common_args,
                    )
                case "divider":
                    input = get_clock(clock_data.get("input"))
                    expression, setting = get_value_and_optional_setting()
                    clock = DividedClock(
                        input=input,
                        expression=expression,
                        setting=setting,
                        **common_args,
                    )
                case _:
                    fatal(f"unknown clock kind '{kind}' for {name}")
            peripherals = get_optional_tag(clock_data, "peripherals", list, [])
            for peripheral in peripherals:
                if type(peripheral) is not str:
                    fatal(f"Invalid peripheral name 'peripheral' for {clock}")
                bind_peri2clock(peripheral, clock)

    def bind_external_clocks():
        for clock, xin_name, xout_name in external_clock_signals:
            if xin_name:
                xin = series.signal(xin_name)
                if not xin:
                    fatal(
                        f"unknown xin signal '{xin_name}' "
                        f"for external clock {name}"
                    )
                clock._set_xin(xin)
            if xout_name:
                xout = series.signal(xout_name)
                if not xout:
                    fatal(
                        f"unknown xout signal '{xout_name}' "
                        f"for external clock {name}"
                    )
                clock._set_xout(xout)

    def load_busses(series_data):
        busses_data = series_data.get("busses")
        if busses_data is None:
            return
        for bus_data in busses_data:
            if type(bus_data) is not dict:
                fatal(f"bus data is not a dict: '{truncate(bus_data)}'")
            name = get_tag(bus_data, "name", str)
            clock_name = get_tag(bus_data, "clock", str)
            clock = series.clock(clock_name)
            if not clock:
                fatal(f"unknown clock {clock_name} for {name} bus")
            bus = Bus(series, name, clock)
            for peripheral_name in get_optional_tag(
                bus_data, "peripherals", list, []
            ):
                if type(peripheral_name) is not str:
                    fatal(
                        f"{name} bus peripheral name is not a string: "
                        f"{truncate(peripheral_name)}"
                    )
                old_bus = bus_map.get(peripheral_name)
                if old_bus:
                    fatal(
                        f"{peripheral_name} cannot be connected to "
                        f"{old_bus} bus and {name} bus"
                    )
                bus_map[peripheral_name] = bus
                bind_peri2clock(peripheral_name, clock)

    def bind_peri2clock(peripheral_name: str, clock: Clock):
        # print(f"bind peripheral clock {peripheral_name} to {clock}")
        clocks = peri2clock_map.get(peripheral_name)
        if clocks is None:
            clocks = set()
            peri2clock_map[peripheral_name] = clocks
        clocks.add(clock)

    def check_peri2clock_map():
        for name, clocks in peri2clock_map.items():
            if not series.peripheral(name) and not name in scope_names:
                fatal(
                    f"Unknown peripheral '{name}' "
                    f"for clock {next(iter(clocks))}"
                )

    external_clock_signals: [(ExternalClock, str, str)] = []
    bus_map: {str: Bus} = {}
    peri2clock_map: {str: {Clock}} = {}
    try:
        load_pad_types(data)
        load_parts_and_pads(data)
        load_pad_config(data)
        load_clock_tree(data)
        load_busses(data)
        load_peripherals(data)
        check_peri2clock_map()
        bind_external_clocks()
        load_global_map(data)
        set_clock_layout(series)
    except ConfigError as error:
        error.args = (f"{json_path}: {error}",)
        raise error from None
    return series


def _load_expression(data, key, parse):
    text = data.get(key)
    if type(text) is not str:
        fatal(f"expected string for expression '{key}' in '{truncate(data)}'")
    return parse(text)


def _expand_bit_pattern(pattern: str) -> Iterable[str]:
    def expand(pattern, bits):
        result = []
        for c in pattern:
            if c not in "01":
                c = "1" if bits & 1 else "0"
                bits >>= 1
            result.append(c)
        return "".join(result)

    return (expand(pattern, bits) for bits in range(1 << pattern.count("x")))


def _null_expand(text: str):
    return text


def _expand(name: str, value: str, text: str):
    return text.replace(f"{{{name}}}", value)


def _expand_parameter(name: str, value: str, expand=_null_expand):
    """Return a function that expands the given parameter to the given value.

    After expansion,  the returned function will apply the given expand
    function.
    """
    return lambda text: expand(_expand(name, value, text))


def _expand_parameters(data, expand=_null_expand):
    """From JSON data,  create and yield parameter expansion functions.

    This interprets "parameters" and "only-if" fields in the JSON data.  For
    each combination of parameter values for which only-if is true (if present),
    a function is returned that replaces the parameters by the corresponding
    values,  and then calls the passed-in expand function.

    The signature of the constructed functions is: Callable[[str],str]
    """
    parameter_data = data.get("parameters")
    if not parameter_data or type(parameter_data) is not dict:
        parameter_data = {}
    for parameter_name, parameter_values in parameter_data.items():
        if type(parameter_values) != list:
            fatal(f"values for {parameter_name} must be list")
    only_if = data.get("only-if", "1")

    def aux(data: list[(str, list[str])]):
        if not data:
            yield {}
        else:
            # dict.popitem() return the most recently added item, which yields
            # an unnatural iteration order. Convert to list and take head and
            # tail to fix.
            (name, values), *tail = data.copy()
            for value in values:
                for rest in aux(tail):
                    rest[name] = value
                    yield rest

    def expand_dict(text: str, parameter_dict: dict[str, str]) -> str:
        for parameter_name, parameter_value in parameter_dict.items():
            text = _expand(parameter_name, parameter_value, text)
        return text

    for parameter_dict in aux(list(parameter_data.items())):

        def expand2(x):
            return expand(expand_dict(x, parameter_dict))

        if parse(expand2(only_if)).value:
            yield expand2


def _count_expansions(data, expand=_null_expand):
    return len(list(_expand_parameters(data, expand)))


def parameter_selftest():
    print("parameter selftest")
    data = {
        "parameters": {
            "x": ["A", "B"],
            "y": ["1", "2", "3"],
        }
    }
    for expand, expect in zip(
        _expand_parameters(data), ["@A1", "@A2", "@A3", "@B1", "@B2", "@B3"]
    ):
        pattern = "@{x}{y}"
        expanded = expand(pattern)
        # print(f"{expanded}")
        assert expanded == expect, f"expected '{expect}', got '{expanded}'"
    data2 = {"parameters": {"x": ["X", "Y"]}, "only-if": "{y} != 2"}
    results2 = []
    for expand in _expand_parameters(data):
        for expand2 in _expand_parameters(data2, expand=expand):
            # print(f"  {expand2('@{x}{y}')}")
            results2.append(expand2("@{x}{y}"))
    assert results2 == [
        "@X1",
        "@Y1",
        "@X3",
        "@Y3",
        "@X1",
        "@Y1",
        "@X3",
        "@Y3",
    ], results2

    print(f"{_count_expansions(data)} expanded values from {data}:")
    for i, expand in enumerate(_expand_parameters(data)):
        print(f"  {i}: {expand('@{x}{y}')}")

    assert _count_expansions(data) == 6
    assert _count_expansions({}) == 1
