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

class Teletype:
    def __init__(self, enable_parity=False, check_parity=False, emulate_timing=False, stop_bits=2):
        self.state = 0 
        self.bit_count = 0
        self.current_byte = 0
        self.parity_bit = 0
        self.buffer = []
        
        self.framing_error = False
        self.parity_error = False
        self.error_count = 0

        self.enable_parity = enable_parity
        self.check_parity = check_parity
        self.emulate_timing = emulate_timing
        self.stop_bits = stop_bits  # Default is 2 stop bits (as in the original)

        self.tx_buffer = []

    def _finish_char(self):
        self.framing_error = False
        
        # Parity check (if enabled)
        if self.enable_parity and self.check_parity:
            ones_count = bin(self.current_byte).count('1')
            expected_parity = ones_count % 2
            if self.parity_bit != expected_parity:
                self.parity_error = True
                self.error_count += 1
            else:
                self.parity_error = False

        # Keep only printable characters (32-126) and control characters (CR, LF)
        if 32 <= self.current_byte <= 126 or self.current_byte in (10, 13):
            char = chr(self.current_byte)
            self.buffer.append(char)

    def receive_bit(self, bit, time_us=None):
        # 0. Wait for the start bit
        if self.state == 0:
            if bit == 0: # Start bit
                self.state = 1
                self.bit_count = 0
                self.current_byte = 0
                self.parity_bit = 0
            return

        # 1. Receive data bits
        if self.state == 1:
            data_bits = 7 if self.enable_parity else 8
            
            if self.bit_count < data_bits:
                if bit:
                    self.current_byte |= (1 << self.bit_count)
                self.bit_count += 1
                return  # Data bits collected, exit
                
            elif self.enable_parity and self.bit_count == data_bits:
                self.parity_bit = bit
                self.bit_count += 1
                return  # Parity bit collected, exit
                
            else:
                # Data collected, the current bit is the first stop bit!
                self.state = 2
                self.stop_bit_count = 0
                # DO NOT RETURN so that the code below processes this bit

        # 2. Check stop bits
        if self.state == 2:
            if bit == 0:
                self.framing_error = True
                self.error_count += 1
                self.state = 0 # Framing error, reset
            else:
                self.stop_bit_count += 1
                if self.stop_bit_count >= self.stop_bits:
                    self._finish_char()
                    self.state = 0

    def get_text(self):
        return "".join(self.buffer)

    def type_char(self, char_code):
        if len(self.tx_buffer) > 0:
            return
        
        # 1 start bit
        self.tx_buffer.append(0)
        
        # 8 data bits (or 7 + parity)
        if self.enable_parity:
            # For parity: 7 data bits + 1 parity bit
            data_bits = 7
            char_code &= 0x7F  # Limit to 7 bits
        else:
            data_bits = 8
            
        for i in range(data_bits):
            self.tx_buffer.append((char_code >> i) & 1)
        
        # Parity bit (if enabled)
        if self.enable_parity:
            ones_count = bin(char_code).count('1')
            parity = ones_count % 2  # Even parity
            self.tx_buffer.append(parity)
        
        # Stop bits (1 or 2)
        for _ in range(self.stop_bits):
            self.tx_buffer.append(1)

    def get_tx_bit(self):
        if self.tx_buffer:
            return self.tx_buffer.pop(0)
        return 1 # Idle line is 1

    def clear(self):
        self.buffer = []
        self.tx_buffer = []
        self.state = 0
        self.bit_count = 0
        self.current_byte = 0
        self.parity_bit = 0
        self.error_count = 0