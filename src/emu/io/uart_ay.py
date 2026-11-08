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

class AY51013UART:
    def __init__(self, teletype=None):
        self.teletype = teletype
        self.control_reg = 0
        self.status_reg = 0
        self.rx_state = 'IDLE'
        self.tx_state = 'IDLE'
        self.rx_pulses = 0
        self.tx_pulses = 0
        self.total_pulses = 0
        self.second_stop_bit = 0
        self.rx_buffer = 0
        self.tx_buffer = 0
        self.rx_data = 0
        self.tx_data = 0
        self.rx_bit_count = 0
        self.tx_bit_count = 0
        self.rx_parity = 0
        self.tx_parity = 0
        self.data_in_low = 0
        self.data_in_phase = 0
        self.data_out_phase = 0
        self.rx_data_latch = 0
        
        self.STATUS_TBMT = 0x01
        self.STATUS_DAV  = 0x02
        self.STATUS_OR   = 0x04
        self.STATUS_FE   = 0x08
        self.STATUS_PE   = 0x10
        self.STATUS_EOC  = 0x20

        self.internal_reset()

    def internal_reset(self):
        nb1 = (self.control_reg >> 2) & 1
        nb2 = (self.control_reg >> 3) & 1
        data_bits = 5 + nb1 + (nb2 * 2)
        self.total_pulses = data_bits << 4
        self.second_stop_bit = 16 if (self.control_reg & 0x04) else 0
        if data_bits == 5 and self.second_stop_bit == 16:
            self.second_stop_bit = 8
        self.status_reg = self.STATUS_EOC | self.STATUS_TBMT
        self.tx_data = 0
        self.rx_state = 'IDLE'
        self.tx_state = 'IDLE'
        self.rx_pulses = 0
        self.rx_data = 0
        self.rx_buffer = 0

    def write_control(self, nibble):
        self.control_reg = nibble
        self.internal_reset()

    def write_data(self, nibble):
        if self.data_in_phase == 0:
            self.data_in_low = nibble
            self.data_in_phase = 1
        else:
            data_byte = (nibble << 4) | self.data_in_low
            self.data_in_phase = 0
            self.set_transmit_data(data_byte)

    def read_data(self):
        if self.data_out_phase == 0:
            self.data_out_phase = 1
            return self.rx_data_latch & 0x0F
        else:
            self.data_out_phase = 0
            val = (self.rx_data_latch >> 4) & 0x0F
            self.status_reg &= ~self.STATUS_DAV
            return val

    def read_status(self):
        status = 0
        if self.status_reg & self.STATUS_TBMT: status |= 0x1
        if self.status_reg & self.STATUS_DAV:  status |= 0x2
        if self.status_reg & self.STATUS_OR:   status |= 0x4
        if self.status_reg & self.STATUS_FE:   status |= 0x8
        return status

    def set_transmit_data(self, data):
        if self.status_reg & self.STATUS_TBMT:
            self.tx_buffer = data
            self.status_reg &= ~self.STATUS_TBMT
            self.status_reg &= ~self.STATUS_EOC

    def tick(self):
        # REMOVED ACCELERATION to avoid race conditions
        self.rx_process()
        self.tx_process()

    def tx_process(self):
        if self.tx_state == 'IDLE':
            if not (self.status_reg & self.STATUS_TBMT):
                self.tx_state = 'PREP_TIME'
                self.tx_pulses = 1
        elif self.tx_state == 'PREP_TIME':
            self.tx_pulses -= 1
            if self.tx_pulses <= 0:
                self.tx_state = 'START_BIT'
                self.tx_pulses = 16
        elif self.tx_state == 'START_BIT':
            if self.tx_pulses == 16:
                self.tx_data = self.tx_buffer
                if self.teletype:
                    self.teletype.receive_bit(0, 0)
                self.tx_parity = 0
                self.tx_bit_count = 0
            self.tx_pulses -= 1
            if self.tx_pulses <= 0:
                self.tx_state = 'PROCESSING'
                self.tx_pulses = self.total_pulses
        elif self.tx_state == 'PROCESSING':
            if (self.tx_pulses % 16) == 0:
                bit = self.tx_data & 1
                if self.teletype:
                    self.teletype.receive_bit(bit, 0)
                if bit: self.tx_parity += 1
                self.tx_data >>= 1
                self.tx_bit_count += 1
            self.tx_pulses -= 1
            if self.tx_pulses <= 0:
                self.tx_pulses = 16
                self.tx_state = 'FIRST_STOP_BIT'
        elif self.tx_state == 'FIRST_STOP_BIT':
            if self.tx_pulses == 16:
                if self.teletype:
                    self.teletype.receive_bit(1, 0)
            self.tx_pulses -= 1
            if self.tx_pulses <= 0:
                self.status_reg |= self.STATUS_EOC | self.STATUS_TBMT 
                self.tx_state = 'IDLE'

    def rx_process(self):
        if not self.teletype:
            return
        if self.rx_pulses > 0:
            self.rx_pulses -= 1
            return
        bit = self.teletype.get_tx_bit()
        if self.rx_state == 'IDLE':
            if bit == 0:
                self.rx_state = 'DATA'
                self.rx_bit_count = 0
                self.rx_data = 0
                self.rx_pulses = 16
        elif self.rx_state == 'DATA':
            if bit: self.rx_data |= (1 << self.rx_bit_count)
            self.rx_bit_count += 1
            self.rx_pulses = 16
            if self.rx_bit_count == 8:
                self.rx_state = 'STOP'
        elif self.rx_state == 'STOP':
            self.rx_pulses = 16
            if bit == 1:
                if not (self.status_reg & self.STATUS_DAV):
                    self.rx_data_latch = self.rx_data
                    self.status_reg |= self.STATUS_DAV
                else:
                    self.status_reg |= self.STATUS_OR
            self.rx_state = 'IDLE'