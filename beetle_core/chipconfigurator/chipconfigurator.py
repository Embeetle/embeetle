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

# Libraries
from typing import Optional, Any, Dict, Iterable, List, Callable
import os
import enum
import json
import uuid
import shutil
import dataclasses

# Local
import data
import functions
import chipconfigurator.constants
import mcuconfig


class CallbackType(enum.Enum):
    AddMapping = enum.auto()
    RemoveMapping = enum.auto()
    SetMappingState = enum.auto()
    OnPadModeChange = enum.auto()
    OnPeripheralEnabled = enum.auto()
    OnSettingEnabled = enum.auto()
    OnSettingChange = enum.auto()
    OnSignalEnabled = enum.auto()
    OnSignalMapped = enum.auto()
    OnUnsavedChanges = enum.auto()
    OnAddSignal = enum.auto()
    OnRemoveSignal = enum.auto()


@dataclasses.dataclass
class CallbackData:
    type: CallbackType
    data: Dict[str, Any]


class ChipConfigurator:
    DEBUG = True

    def __init__(self, callback_cache: Dict[str, callable]) -> None:
        # MCUConfig variables
        self.part: Optional[Any] = None
        self.package_information: Optional[Any] = None
        self.config: Optional[Any] = None
        self.__peripheral_data: Dict[mcuconfig.Pin, Any] = {}
        self.__pin_data_overrides: Dict[mcuconfig.Pin, Any] = {}
        self.__scale: float = 1.0

        # Check callback cache keys
        needed_keys = (
            "set_chip_draw_data",
            "callback_handler",
        )
        for k in needed_keys:
            if k not in callback_cache.keys():
                raise Exception(
                    f"[{self.__class__.__name__}] Key '{k}' missing in callback cache!"
                )
        for k in callback_cache.keys():
            if k not in needed_keys:
                raise Exception(
                    f"[{self.__class__.__name__}] Unknown key '{k}' in callback cache!"
                )
        # Store callback cache
        self.callback_cache = callback_cache

    def echo(self, *args, **kwargs) -> None:
        if self.DEBUG:
            print(f"[{self.__class__.__name__}]", *args, **kwargs)

    def initialize(self, series_filename: str, part_name: str) -> None:
        try:
            self.part = mcuconfig.load_json.load_part(
                series_filename, part_name
            )

            # Check for part validity
            if not self.part:
                raise Exception(
                    f"[{self.__class__.__name__}] "
                    + f"Part {part_name} not found in series {series_filename}!"
                )

            # Load package information
            self.package_information = self.part.package

            # Set the draw data for the display widget
            self.set_draw_data()

        except mcuconfig.ConfigError as error:
            self.echo(f"Error: {error}")
            raise error

    def initialize_config(self) -> None:
        if self.part is None:
            raise Exception(
                f"[{self.__class__.__name__}] "
                + f"Part not yet initialized, cannot initialize Config!"
            )

        # Load configuration
        self.config = CustomConfig(
            self.part,
            callback_handler=self.callback_handler,
        )

    def save(self, project_path: str) -> None:
        save_path = functions.unixify_path_join(
            project_path, data.chipconfigurator_data_file
        )
        # Save configuratin to a file
        configuration = self.config.get_data()
        with open(save_path, "w+", encoding="utf-8") as f:
            f.write(json.dumps(configuration, indent=2, ensure_ascii=False))

    def load(self, project_path: str) -> None:
        if self.part is None:
            raise Exception(
                f"[{self.__class__.__name__}] "
                + f"Part not yet initialized, cannot load configuration!"
            )

        load_path = functions.unixify_path_join(
            project_path, data.chipconfigurator_data_file
        )
        if os.path.isfile(load_path):
            # Load the configuration from a file
            with open(load_path, "r", encoding="utf-8") as f:
                configuration = json.loads(f.read())
            # self.config.set_data(configuration)
            self.part.series.set_data(configuration)

    def generate(self, project_path: str) -> None:
        # Create the path that the code will be generated into
        generate_path = functions.unixify_path_join(
            project_path, data.chipconfigurator_code_generation_directory
        )
        shutil.os.makedirs(generate_path, exist_ok=True)
        # Generate the code to the project directory
        self.config.generate_code(generate_path)

    def peripheral_data_get(
        self, pin: mcuconfig.Pin, id: str
    ) -> Optional[dict]:
        return (
            self.__peripheral_data[pin][id]
            if pin in self.__peripheral_data.keys()
            else None
        )

    def peripheral_data_add(
        self,
        pin: mcuconfig.Pin,
        text: str,
        signal: mcuconfig.Signal,
        id: str,
        bg_color: str,
        fg_color: str,
        opacity: float = 1.0,
    ) -> None:
        # Create the new peripheral
        new_peripheral = {
            "text": text,
            "id": id,
            "signal": signal,
            "bg-color": bg_color,
            "fg-color": fg_color,
            "opacity": opacity,
        }

        # Check if peripherals on this pin need to be created
        if pin not in self.__peripheral_data.keys():
            self.__peripheral_data[pin] = {}

        # Add the peripheral
        self.__peripheral_data[pin][id] = new_peripheral

    def peripheral_data_update(
        self,
        pin: mcuconfig.Pin,
        id: str,
        new_data: dict,
    ) -> None:
        self.__peripheral_data[pin][id] = new_data

    def peripheral_data_remove(
        self,
        pin: mcuconfig.Pin,
        id: str,
    ) -> None:
        # Remove the item
        del self.__peripheral_data[pin][id]
        # Remove the pin cache if needed
        if len(self.__peripheral_data[pin].keys()) == 0:
            del self.__peripheral_data[pin]

    def callback_handler(self, callback_data: CallbackData) -> None:
        #        self.echo("CALLBACK:", callback_data)

        # Handle callback by type
        if callback_data.type in CallbackType:
            self.callback_cache["callback_handler"](callback_data)

        else:
            raise Exception(
                f"[{self.__class__.__name__}] "
                + f"Unhandled callback type: {type}"
            )

    def pin_overrides_clear(self) -> None:
        self.__pin_data_overrides = {}

    def pin_override_set(
        self, pin: mcuconfig.Pin, key: str, value: object
    ) -> None:
        if pin not in self.__pin_data_overrides.keys():
            self.__pin_data_overrides[pin] = {}
        self.__pin_data_overrides[pin][key] = value

    def get_view_scale(self) -> float:
        return self.__scale

    def set_view_scale(self, new_scale: float) -> None:
        minimum_level = 0.2
        if new_scale < minimum_level:
            new_scale = minimum_level
        self.__scale = new_scale

    def set_draw_data(self, draw: bool = True) -> None:
        # Check if MCUConfig was loaded
        if self.config is None or self.config.part is None:
            return

        # Package
        package_type = self.package_information.type

        # Pin height
        pin_height = 24

        # Pin gap
        pin_gap = 8

        # Fonts
        chip_title_font_size = 16
        chip_title_font_family = data.get_global_font_family()
        pin_font_size = 10
        pin_font_family = data.get_global_font_family()

        # Scaling
        scale = self.__scale
        pin_height = int(pin_height * scale)
        pin_gap = int(pin_gap * scale)
        chip_title_font_size = int(chip_title_font_size * scale)
        pin_font_size = int(pin_font_size * scale)

        # Number of pins
        divider = -1
        if package_type == mcuconfig.PackageType.SIDES2:
            divider = 2
        elif package_type == mcuconfig.PackageType.SIDES4:
            divider = 4
        else:
            raise Exception(
                f"[{self.__class__.__name__}] "
                + f"Unhandled package type: {package_type}"
            )
        num_pins_on_side = int(self.package_information.nr_of_pins / divider)

        # Size
        main_rect_height = (num_pins_on_side * pin_height) + int(
            num_pins_on_side * pin_gap * 1.5
        )
        main_rect_width = main_rect_height
        if self.package_information.aspect_ratio is not None:
            main_rect_width = int(
                main_rect_height * (self.package_information.aspect_ratio / 100)
            )

        # Initialize pin texts
        pin_data = {}
        for pin in self.config.part.pins:
            if pin is not None:
                bg_color = "#ffffff"
                fg_color = "#000000"
                if self.config.is_power_pin(pin):
                    bg_color = chipconfigurator.constants.pin_special_colors[
                        "power"
                    ]["bg"]
                    fg_color = chipconfigurator.constants.pin_special_colors[
                        "power"
                    ]["fg"]
                pin_text = "/".join(
                    [pad.name for pad in self.config.part.pads_for_pin(pin)]
                )
                pin_data[pin] = {
                    "index": int(pin.name),
                    "pin": pin,
                    "text": pin_text,
                    "bg-color": bg_color,
                    "fg-color": fg_color,
                }
                if pin in self.__pin_data_overrides.keys():
                    for k, v in self.__pin_data_overrides[pin].items():
                        pin_data[pin][k] = v

        self.pin_data = pin_data

        # Chip title and logo
        main_rect_text = self.part.name
        main_rect_logo = "icons/logo/geehy.svg"

        # Prepare the draw data
        self.draw_data = {
            "scale": scale,
            "bg_color": data.theme["fonts"]["default"]["background"],
            "main_rect_package_type": package_type,
            "main_rect_width": main_rect_width,
            "main_rect_height": main_rect_height,
            "main_rect_bg_color": "#2e3436",
            "main_rect_text": main_rect_text,
            "main_rect_logo": main_rect_logo,
            "main_text_color": "#ffffff",
            "small_rect_height": pin_height,
            "num_rects_on_side": num_pins_on_side,
            "side_rect_fixed_gap": pin_gap,
            "pin_border_color": "#000000",
            "chip_title_font_size": chip_title_font_size,
            "chip_title_font_family": chip_title_font_family,
            "pin_font_size": pin_font_size,
            "pin_font_family": pin_font_family,
            "pin_text_color": "#000000",
            "inner_pin_text_color": "#ffffff",
            "pin_data": pin_data,
            "peripheral_data": self.__peripheral_data,
        }

        # Execute callback with generated data
        if draw:
            self.draw()

    def draw(self) -> None:
        self.callback_cache["set_chip_draw_data"](self.draw_data)

    def get_pin_mappings(self, pin: mcuconfig.Pin) -> List[mcuconfig.Mapping]:
        return self.part.sorted_pin_mappings(pin)

    def get_signal_mappings(
        self, signal: mcuconfig.Signal
    ) -> List[mcuconfig.Mapping]:
        return self.part.sorted_signal_mappings(signal)


class CustomConfig(mcuconfig.Config):
    """Over-ridden class to catch in the callbacks."""

    def __init__(
        self,
        *args,
        callback_handler: Optional[Callable[[CallbackData], None]] = None,
        **kwargs,
    ):
        # Store the callback handler function
        if callback_handler is None:
            raise Exception(
                f"[{self.__class__.__name__}] Callback handler cannot be None!"
            )
        self.callback_handler = callback_handler

        # Initialize parent class
        super().__init__(*args, **kwargs)

    def on_add_mapping(
        self, signal: mcuconfig.Signal, pin: mcuconfig.Pin
    ) -> Any:
        # Create the return data
        signal_package = {
            "pin": pin,
            "signal": signal,
            "id": uuid.uuid4().hex,
        }

        # Call the callback handler
        return_data = CallbackData(
            type=CallbackType.AddMapping, data=signal_package
        )
        self.callback_handler(return_data)

        # Return the needed data
        return signal_package

    def on_remove_mapping(self, data: dict):
        # Call the callback function
        return_data = CallbackData(type=CallbackType.RemoveMapping, data=data)
        self.callback_handler(return_data)

    def on_mapping_state(self, data: dict, state: mcuconfig.MappingState):
        """Set the state of an existing mapping.

        Mapping state can be MappingState.NORMAL, MappingState.TENTATIVELY_ADDED
        or MappingState.TENTATIVELY_REMOVED.  The initial mapping state is
        always MappingState.NORMAL.
        """
        # Add the 'state' key to the data
        data["state"] = state

        # Call the callback function
        return_data = CallbackData(
            type=CallbackType.SetMappingState,
            data=data,
        )
        self.callback_handler(return_data)

    def on_pad_mode_change(self, pad: mcuconfig.Pad):
        return_data = CallbackData(
            type=CallbackType.OnPadModeChange,
            data={
                "pad": pad,
            },
        )
        self.callback_handler(return_data)

    def on_peripheral_enabled(
        self, peripheral: mcuconfig.Peripheral, enabled: bool
    ):
        return_data = CallbackData(
            type=CallbackType.OnPeripheralEnabled,
            data={
                "peripheral": peripheral,
                "enabled": enabled,
            },
        )
        self.callback_handler(return_data)

    """
    Settings
    """

    def on_setting_enabled(self, setting: mcuconfig.Setting, enabled: bool):
        """Set the enabled state of a setting.

        Initial state is disabled.
        """
        #        print(f"'{setting.label}' set: {'enabled' if enabled else 'disabled'}")
        return_data = CallbackData(
            type=CallbackType.OnSettingEnabled,
            data={
                "setting": setting,
                "enabled": enabled,
            },
        )
        self.callback_handler(return_data)

    def on_setting(self, setting: mcuconfig.Setting, value: int):
        """Set value of a setting.

        Initial value is zero.
        """
        #        print(f"'{setting.label}' value changed to: {value}")
        return_data = CallbackData(
            type=CallbackType.OnSettingChange,
            data={
                "setting": setting,
                "value": value,
            },
        )
        self.callback_handler(return_data)

    """
    Signals
    """

    def on_signal_enabled(self, signal: mcuconfig.Signal, enabled: bool):
        """Set the enabled state of a signal.

        Current state is signal.is_enabled.
        """
        return_data = CallbackData(
            type=CallbackType.OnSignalEnabled,
            data={
                "signal": signal,
                "enabled": enabled,
            },
        )
        self.callback_handler(return_data)

    def on_signal_mapped(
        self, signal: mcuconfig.Signal, pads: Iterable[mcuconfig.Pad]
    ):
        """Update the user interface for changed mappings for the signal.

        Can be used for example to update the signal mapping table for each
        peripheral.
        """
        return_data = CallbackData(
            type=CallbackType.OnSignalMapped,
            data={
                "signal": signal,
                "pads": pads,
            },
        )
        self.callback_handler(return_data)

    def on_add_signal(self, signal: mcuconfig.Signal):
        """Update the user interface for a new signal."""
        return_data = CallbackData(
            type=CallbackType.OnAddSignal,
            data={
                "signal": signal,
            },
        )
        self.callback_handler(return_data)

    def on_remove_signal(self, signal: mcuconfig.Signal):
        """Update the user interface for a removed signal."""
        return_data = CallbackData(
            type=CallbackType.OnRemoveSignal,
            data={
                "signal": signal,
            },
        )
        self.callback_handler(return_data)

    """
    Signal ToDo list
    """

    def on_add_unmapped_active_signal(self, signal: mcuconfig.Signal):
        """Add a signal to the todo-list of signals to be mapped to a pin."""
        print("on_add_unmapped_active_signal", signal)
        pass

    def on_remove_unmapped_active_signal(self, signal: mcuconfig.Signal):
        """Remove a signal from the todo-list of signals to be mapped to a
        pin."""
        print("on_remove_unmapped_active_signal", signal)
        pass

    """
    Changes
    """

    def on_unsaved_changes(self, changed: bool):
        return_data = CallbackData(
            type=CallbackType.OnUnsavedChanges,
            data={
                "changed": changed,
            },
        )
        self.callback_handler(return_data)
