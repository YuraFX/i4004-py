# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

class CPU:
    def __init__(self):

        # 256 bytes of memory
        self.memory = bytearray(256)

        # accumulator
        self.acc = 0

        # program counter
        self.pc = 0

    # NOP instruction (No Operation)
    def NOP(self):
        self.pc += 1

    # INC instruction (Increment index register)
    def INC(self):
        self.acc = (self.acc + 1) % 256
        self.pc += 1

    # ISZ instruction (Increment index register skip if zero)
    def ISZ(self, address):
        self.memory[address] = (self.memory[address] + 1) % 256

        if self.memory[address] == 0:
            self.pc += 2
        else:
            self.pc += 1

    # ADD instruction (Add index register to accumulator with carry)
    def ADD(self, address):
        self.acc = (self.acc + self.memory[address]) % 256
        self.pc += 2

    # SUB instruction (Subtract index register to accumulator with borrow)
    def SUB(self, address):
        self.acc = (self.acc - self.memory[address]) % 256
        self.pc += 2

    # LD instruction (Load index register to Accumulator)
    def LD(self, address):
        self.acc = self.memory[address]
        self.pc += 2

    # XCH instruction (Exchange index register and accumulator)
    def XCH(self, address):
        temp = self.acc
        self.acc = self.memory[address]
        self.memory[address] = temp
        self.pc += 2

    def run(self):
        while self.pc < len(self.memory):
            opcode = self.memory[self.pc]

            # NOP instruction opcode
            if opcode == 0x0:
                self.NOP()

            # INC instruction opcode
            elif opcode == 0x6:
                self.INC()

            # ISZ instruction opcode
            elif opcode == 0x7:
                self.ISZ(self.memory[self.pc + 1])

            # ADD instruction opcode
            elif opcode == 0x8:
                self.ADD(self.memory[self.pc + 1])

            # SUB instruction opcode
            elif opcode == 0x9:
                self.SUB(self.memory[self.pc + 1])

            # LD instruction opcode
            elif opcode == 0xA:
                self.LD(self.memory[self.pc + 1])

            # XCH instruction opcode
            elif opcode == 0xB:
                self.XCH(self.memory[self.pc + 1])

            else:
                print('Unknown opcode!!!')
                return

            self.pc += 1