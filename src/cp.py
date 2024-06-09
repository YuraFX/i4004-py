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

print('     ##      ###         ###           ##')
print('    ###    ##   ##     ##   ##        ###')
print('   # ##   ##     ##   ##     ##      # ##')
print('  #  ##   ##     ##   ##     ##     #  ##')
print(' #   ##   ##     ##   ##     ##    #   ##')
print('#######   ##     ##   ##     ##   #######')
print('     ##    ##   ##     ##   ##         ##')
print('     ##      ###         ###           ##')
print('                                         ')
print('           Intel 4004 emulator           ')
print('     Emulator author: Yura_FX (2024)     ')

from cpu import CPU

cpu = CPU()

# Command Parser
def parse_command(cp):
    parts = cp.split()

    # Checking condition for 'memory' command
    if len(parts) == 3 and parts[0] == 'memory' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        value = int(parts[2])
        return 'memory', address, value

    # Checking condition for 'nop' command
    elif len(parts) == 1 and parts[0] == 'nop':
        return 'nop', None, None

    # Checking condition for 'jcn' command
    elif len(parts) == 1 and parts[0] == 'jcn':
        return 'jcn', None, None

    # Checking condition for 'fim' command
    elif len(parts) == 2 and parts[0] == 'fim' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'fim', address, None

    # Checking condition for 'fin' command
    elif len(parts) == 2 and parts[0] == 'fin' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'fin', address, None

    # Checking condition for 'jin' command
    elif len(parts) == 2 and parts[0] == 'jin' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'jin', address, None

    # Checking condition for 'jun' command
    elif len(parts) == 1 and parts[0] == 'jun':
        return 'jun', None, None

    # Checking condition for 'jms' command
    elif len(parts) == 1 and parts[0] == 'jms':
        return 'jms', None, None

    # Checking condition for 'inc' command
    elif len(parts) == 2 and parts[0] == 'inc' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'inc', address, None

    # Checking condition for 'isz' command
    elif len(parts) == 2 and parts[0] == 'isz' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'isz', address, None

    # Checking condition for 'add' command
    elif len(parts) == 2 and parts[0] == 'add' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'add', address, None

    # Checking condition for 'sub' command
    elif len(parts) == 2 and parts[0] == 'sub' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'sub', address, None

    # Checking condition for 'ld' command
    elif len(parts) == 2 and parts[0] == 'ld' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'ld', address, None

    # Checking condition for 'xch' command
    elif len(parts) == 2 and parts[0] == 'xch' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'xch', address, None

    # Checking condition for 'bbl' command
    elif len(parts) == 1 and parts[0] == 'bbl':
        return 'bbl', None, None

    # Checking condition for 'ldm' command
    elif len(parts) == 1 and parts[0] == 'ldm':
        return 'ldm', None, None

    # Checking condition for 'clb' command
    elif len(parts) == 1 and parts[0] == 'clb':
        return 'clb', None, None

    # Checking condition for 'clc' command
    elif len(parts) == 1 and parts[0] == 'clc':
        return 'clc', None, None

    # Checking condition for 'iac' command
    elif len(parts) == 1 and parts[0] == 'iac':
        return 'iac', None, None

    # Checking condition for 'cmc' command
    elif len(parts) == 1 and parts[0] == 'cmc':
        return 'cmc', None, None

    # Checking condition for 'cma' command
    elif len(parts) == 1 and parts[0] == 'cma':
        return 'cma', None, None

    # Checking condition for 'ral' command
    elif len(parts) == 1 and parts[0] == 'ral':
        return 'ral', None, None

    # Checking condition for 'rar' command
    elif len(parts) == 1 and parts[0] == 'rar':
        return 'rar', None, None

    # Checking condition for 'tcc' command
    elif len(parts) == 1 and parts[0] == 'tcc':
        return 'tcc', None, None

    # Checking condition for 'dac' command
    elif len(parts) == 2 and parts[0] == 'dac' and parts[1].startswith('0x'):
        address = int(parts[1], 16)
        return 'dac', address, None

    # Checking condition for 'tcs' command
    elif len(parts) == 1 and parts[0] == 'tcs':
        return 'tcs', None, None

    # Checking condition for 'stc' command
    elif len(parts) == 1 and parts[0] == 'stc':
        return 'stc', None, None

    # Checking condition for 'daa' command
    elif len(parts) == 1 and parts[0] == 'daa':
        return 'daa', None, None

    # Checking condition for 'start' command
    elif len(parts) == 1 and parts[0] == 'start':
        return 'start', None, None

    else:
        return None, None, None

while True:
    cp = input('>')
    command, address, value = parse_command(cp)

    if command == 'memory' and address is not None and value is not None:
        cpu.memory[address] = value
        print('OK')

    elif command == 'nop':
        cpu.NOP()
        print('OK')

    elif command == 'jcn':
        cpu.JCN()
        print('OK')

    elif command == 'fim' and address is not None:
        cpu.FIM(address)
        print('OK')

    elif command == 'fin' and address is not None:
        cpu.FIN(address)
        print('OK')

    elif command == 'jin' and address is not None:
        cpu.JIN(address)
        print('OK')

    elif command == 'jun':
        cpu.JUN()
        print('OK')

    elif command == 'jms':
        cpu.JMS()
        print('OK')

    elif command == 'inc' and address is not None:
        cpu.INC(address)
        print('OK')

    elif command == 'isz' and address is not None:
        cpu.ISZ(address)
        print('OK')

    elif command == 'add' and address is not None:
        cpu.ADD(address)
        print('OK')

    elif command == 'sub' and address is not None:
        cpu.SUB(address)
        print('OK')

    elif command == 'ld' and address is not None:
        cpu.LD(address)
        print('OK')

    elif command == 'xch' and address is not None:
        cpu.XCH(address)
        print('OK')

    elif command == 'bbl':
        cpu.BBL()
        print('OK')

    elif command == 'ldm':
        cpu.LDM()
        print('OK')

    elif command == 'clb':
        cpu.CLB()
        print('OK')

    elif command == 'clc':
        cpu.CLC()
        print('OK')

    elif command == 'iac':
        cpu.IAC()
        print('OK')

    elif command == 'cmc':
        cpu.CMC()
        print('OK')

    elif command == 'cma':
        cpu.CMA()
        print('OK')

    elif command == 'ral':
        cpu.RAL()
        print('OK')

    elif command == 'rar':
        cpu.RAR()
        print('OK')

    elif command == 'tcc':
        cpu.TCC()
        print('OK')

    elif command == 'dac' and address is not None:
        cpu.DAC(address)
        print('OK')

    elif command == 'tcs':
        cpu.TCS()
        print('OK')

    elif command == 'stc':
        cpu.STC()
        print('OK')

    elif command == 'daa':
        cpu.DAA()
        print('OK')

    elif command == 'start':
        print(f'  Result: {cpu.acc}')
        print('OK')

    else:
        print('WHAT?')