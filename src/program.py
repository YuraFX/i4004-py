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

print('Intel 4004 emulator with very reduced functionality')
print(' Emulator author: Konyshev Yuri aka Yura_FX (2024) ')

from cpu import CPU

cpu = CPU()

# Write the numbers 12, 5 and 2 to memory at arbitrary addresses (e.g. 0x10, 0x11 and 0x12)
cpu.memory[0x10] = 12
cpu.memory[0x11] = 5
cpu.memory[0x12] = 2

# Execute the commands to subtract the numbers 12 and 5, and then add the number 2 to the resulting number
cpu.LD(0x10)
cpu.SUB(0x11)
cpu.ADD(0x12)
cpu.NOP()

# The result of the program will be stored in the accumulator
print('')
print(f'  Result: {cpu.acc}')
print('')