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

class ShiftRegister4003:
    def __init__(self):
        # 10-bit register. Initially all zeros (power-on clear).
        # Index 0 is the input (LSB), index 9 is the output (MSB).
        self.bits = [0] * 10
        self.enable = 1  # 1 = outputs disabled (High-Z), 0 = outputs active

    def set_data(self, bit):
        # Set the bit on the serial input (Data In)
        # On the real chip, data is latched on the CP edge.
        self.data_in = bit & 0x1

    def clock_pulse(self):
        # Emulate a clock pulse (CP).
        # Shift all bits to the right (toward the higher bits), and feed data_in into the input.
        for i in range(9, 0, -1):
            self.bits[i] = self.bits[i - 1]
        self.bits[0] = self.data_in

    def set_enable(self, value):
        # E = low (0) -> outputs active.
        # E = high (1) -> outputs in the Vgg state (inactive).
        self.enable = 1 if value else 0

    def get_parallel_out(self):
        # Return the 10-bit value if the outputs are active.
        # If not, return 0 or None (depending on the connection logic).
        if self.enable == 0:
            result = 0
            for i in range(10):
                if self.bits[i]:
                    result |= (1 << i)
            return result
        else:
            return 0