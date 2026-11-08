# Copyright (C) 2026 Yuriy Konyshev
#
# This file is part of i4004-py.
#
# i4004-py is free software: you can redistribute it and/or modify it under the terms of the GNU General 
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.
#
# i4004-py is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even 
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with i4004-py. If not, see 
# <https://www.gnu.org/licenses/>.

# Constants for naming pins (analogous to Symbol in JS)
SYNC = "SYNC"
CM_ROM0 = "CM_ROM0"
CM_ROM1 = "CM_ROM1"
CM_RAM0 = "CM_RAM0"
CM_RAM1 = "CM_RAM1"
CM_RAM2 = "CM_RAM2"
CM_RAM3 = "CM_RAM3"
D0 = "D0"
D1 = "D1"
D2 = "D2"
D3 = "D3"


class CPUPins:
    def __init__(self):
        # Initialize all pins to state 0 (LOW)
        self.pins = {
            SYNC: 0,
            CM_ROM0: 1,  # ROM bank 0 is selected by default
            CM_ROM1: 0,
            CM_RAM0: 1,  # RAM bank 0 is selected by default (CM_RAM0 = 1)
            CM_RAM1: 0,
            CM_RAM2: 0,
            CM_RAM3: 0,
            D0: 0,
            D1: 0,
            D2: 0,
            D3: 0,
        }
        
        # Internal states for CPU convenience
        self.ram_control = 0b0001
        self.selected_rom_bank = 0

    def set_pin(self, pin, value):
        # Set a single pin to HIGH (1) or LOW (0)
        self.pins[pin] = 1 if value else 0

    def set_pins_data(self, pins_list, value):
        # Set a numeric value on a group of pins.
        # For example, set_pins_data([D0, D1, D2, D3], 0xA) sets D0=0, D1=1, D2=0, D3=1.
        for idx, pin in enumerate(pins_list):
            self.pins[pin] = 1 if (value & (1 << idx)) else 0

    def get_pin(self, pin):
        # Read the state of a single pin
        return self.pins[pin]

    def get_pins_data(self, pins_list):
        # Read a numeric value from a group of pins
        result = 0
        for idx, pin in enumerate(pins_list):
            if self.pins[pin]:
                result |= (1 << idx)
        return result

    # =================================================================
    # WRAPPER METHODS FOR CPU (to avoid cluttering cpu.py with constants)
    # =================================================================

    def write_ram(self, value):
        # WRM: Write to RAM
        self.set_pins_data([D0, D1, D2, D3], value)

    def read_ram(self):
        # RDM: Read from RAM
        return self.get_pins_data([D0, D1, D2, D3])

    def write_ram_port(self, value):
        # WMP: Write to RAM port
        self.set_pins_data([D0, D1, D2, D3], value)

    def write_ram_status(self, idx, value):
        # WR0-WR3: Write to RAM status characters
        self.set_pins_data([D0, D1, D2, D3], value)

    def read_ram_status(self, idx):
        # RD0-RD3: Read RAM status characters
        return self.get_pins_data([D0, D1, D2, D3])

    def set_ram_address(self, high, low):
        # SRC: Send address to RAM (simplified version for the current cpu.py architecture)
        self.set_pins_data([D0, D1, D2, D3], low)
        self.set_pins_data([CM_RAM0, CM_RAM1, CM_RAM2, CM_RAM3], self.ram_control)
        
    def set_rom_bank(self, bank):
        # DB0/DB1: Switch ROM bank
        self.selected_rom_bank = bank
        self.set_pin(CM_ROM0, 1 if bank == 0 else 0)
        self.set_pin(CM_ROM1, 1 if bank == 1 else 0)