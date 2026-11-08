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

import re


class Assembler:
    def __init__(self):
        self.opcodes = {
            'NOP': (0x00, 'N'), 'HLT': (0x01, 'N'),
            'OR4': (0x04, 'N'), 'OR5': (0x05, 'N'),
            'AN6': (0x06, 'N'), 'AN7': (0x07, 'N'),
            'DB0': (0x08, 'N'), 'DB1': (0x09, 'N'),
            'SB0': (0x0A, 'N'), 'SB1': (0x0B, 'N'),
            'JCN': (0x10, 'COND'), 'FIM': (0x20, 'P'),
            'SRC': (0x21, 'P'), 'FIN': (0x30, 'P'), 'JIN': (0x31, 'P'),
            'JUN': (0x40, 'A12'), 'JMS': (0x50, 'A12'), 'INC': (0x60, 'R'),
            'ISZ': (0x70, 'ISZ'), 'ADD': (0x80, 'R'), 'SUB': (0x90, 'R'),
            'LD':  (0xA0, 'R'), 'XCH': (0xB0, 'R'), 'BBL': (0xC0, 'D'),
            'LDM': (0xD0, 'D'), 'WRM': (0xE0, 'N'), 'WMP': (0xE1, 'N'),
            'WRR': (0xE2, 'N'), 'WPM': (0xE3, 'N'),
            'WR0': (0xE4, 'N'), 'WR1': (0xE5, 'N'),
            'WR2': (0xE6, 'N'), 'WR3': (0xE7, 'N'), 'SBM': (0xE8, 'N'),
            'RDM': (0xE9, 'N'), 'RDR': (0xEA, 'N'), 'ADM': (0xEB, 'N'),
            'RD0': (0xEC, 'N'), 'RD1': (0xED, 'N'), 'RD2': (0xEE, 'N'),
            'RD3': (0xEF, 'N'), 'CLB': (0xF0, 'N'), 'CLC': (0xF1, 'N'),
            'IAC': (0xF2, 'N'), 'CMC': (0xF3, 'N'), 'CMA': (0xF4, 'N'),
            'RAL': (0xF5, 'N'), 'RAR': (0xF6, 'N'), 'TCC': (0xF7, 'N'),
            'DAC': (0xF8, 'N'), 'TCS': (0xF9, 'N'), 'STC': (0xFA, 'N'),
            'DAA': (0xFB, 'N'), 'KBP': (0xFC, 'N'), 'DCL': (0xFD, 'N'),
        }
        self.conditions = {
            'T':   0x0, 'Z': 0x4, 'C': 0x2, 'TN': 0x8, 
            'ZN': 0xC, 'CN': 0xA, 'ZCN': 0xE, 'NC': 0xA, 
            'NZ': 0xC, 'NT': 0x9
        }
        self.labels = {}
        self.binary = []
        self.pc = 0
        
        # --- For the linker ---
        self.symbols = {}
        self.externals = set()
        self.relocations = []

    def _clean_line(self, line):
        """Remove all supported comment types: //, ;, /"""
        # First remove // (the longest), then ;, then /
        line = line.split('//')[0]
        line = line.split(';')[0]
        line = line.split('/')[0]
        return line.strip()

    def _eval_expression(self, expr, current_pc):
        """
        Evaluate a simple expression: numbers, labels, *, +, -.
        Supports the historical * syntax (current address) and label+1.
        """
        expr = expr.strip()
        # Replace * with the current PC
        expr = expr.replace('*', str(current_pc))
        
        # Substitute known labels
        for label, addr in self.labels.items():
            # Use word boundaries to avoid replacing part of another name
            expr = re.sub(r'\b' + re.escape(label) + r'\b', str(addr), expr)
            
        try:
            # Safely evaluate simple arithmetic expressions
            return int(eval(expr, {"__builtins__": None}, {}))
        except Exception:
            # If the expression cannot be evaluated (e.g. an external label), return 0
            return 0

    def _parse_value(self, val_str, current_pc=0):
        val_str = val_str.strip()
        
        # 1. Direct number formats
        if val_str.startswith('0x') or val_str.startswith('0X'): 
            return int(val_str, 16)
        if val_str.startswith('0b') or val_str.startswith('0B'): 
            return int(val_str, 2)
        try: 
            return int(val_str)
        except ValueError: 
            pass

        # 2. Expression (e.g. label+1, *+14, BUFFER_SIZE)
        # If the string contains operators or *, try to evaluate it as an expression
        if any(op in val_str for op in ['+', '-', '*']):
            result = self._eval_expression(val_str, current_pc)
            # If the expression contains only known labels, the result will be > 0
            # If it is an external label, it will be added to externals below
            # Check whether the expression contains unknown names
            # (simple heuristic: if the result is 0 and the string is not "0", it may be an external label)
            if result != 0 or val_str == '0':
                return result
                
        # 3. Single label
        if val_str in self.labels:
            return self.labels[val_str]
            
        # 4. External label
        self.externals.add(val_str)
        return 0x00

    def _get_reg(self, reg_str):
        reg_str = reg_str.strip().upper()
        # Support historical format 0R..15R
        match = re.match(r'^(\d+)R$', reg_str)
        if match:
            return int(match.group(1)) & 0xF
        # Support modern format R0..R15
        if reg_str.startswith('R'):
            return int(reg_str[1:]) & 0xF
        return int(reg_str) & 0xF

    def _get_pair(self, pair_str):
        pair_str = pair_str.strip().upper()
        # Support historical format 0P..7P
        match = re.match(r'^(\d+)P$', pair_str)
        if match:
            return (int(match.group(1)) * 2) & 0xE
        # Support modern format P0..P7
        if pair_str.startswith('P'):
            return (int(pair_str[1:]) * 2) & 0xE
        return self._get_reg(pair_str.split('R')[0] if 'R' in pair_str else pair_str) & 0xE

    def pass1(self, lines):
        self.pc = 0
        for line in lines:
            line = self._clean_line(line)
            if not line:
                continue

            # 1. Label (ends with : or ,)
            if line.endswith(':') or line.endswith(','):
                label = line[:-1].strip()
                self.labels[label] = self.pc
                continue

            parts = line.split()
            mnemonic = parts[0].upper()

            # 2. Historical ORG directive via '='
            if mnemonic == '=':
                self.pc = self._parse_value(parts[1], self.pc)
                continue

            # 3. ORG directive
            if mnemonic == 'ORG':
                self.pc = self._parse_value(parts[1], self.pc)
                continue

            # 4. EQU directive or NAME = value
            if mnemonic == 'EQU' or (len(parts) > 1 and parts[1].upper() == 'EQU'):
                name = parts[0]
                if mnemonic == 'EQU':
                    name = parts[1]
                    value_str = ' '.join(parts[2:])
                else:
                    value_str = ' '.join(parts[2:])
                self.labels[name] = self._parse_value(value_str, self.pc)
                continue
            if len(parts) > 1 and parts[1] == '=':
                name = parts[0]
                value_str = ' '.join(parts[2:])
                self.labels[name] = self._parse_value(value_str, self.pc)
                continue

            # 5. Other instructions
            if mnemonic == 'DB':
                self.pc += len(parts) - 1
            elif mnemonic in self.opcodes:
                op, fmt = self.opcodes[mnemonic]
                if fmt in ['N', 'R', 'D']:
                    self.pc += 1
                elif fmt in ['A12', 'ISZ', 'COND']:
                    self.pc += 2
                elif fmt == 'P':
                    self.pc += 2 if mnemonic == 'FIM' else 1
            elif mnemonic == 'END':
                break
            else:
                raise ValueError(f"Unknown instruction during pass 1: {mnemonic}")

    def pass2(self, lines):
        self.binary = []
        self.pc = 0
        for line in lines:
            line = self._clean_line(line)
            if not line:
                continue

            if line.endswith(':') or line.endswith(','):
                continue

            parts = line.split()
            mnemonic = parts[0].upper()

            # Skip ORG and EQU directives during pass 2
            if mnemonic == '=':
                self.pc = self._parse_value(parts[1], self.pc)
                continue
            if mnemonic == 'ORG':
                self.pc = self._parse_value(parts[1], self.pc)
                continue
            if mnemonic == 'EQU' or (len(parts) > 1 and parts[1].upper() == 'EQU'):
                continue
            if len(parts) > 1 and parts[1] == '=':
                continue

            if mnemonic == 'DB':
                for val in parts[1:]:
                    self.binary.append(self._parse_value(val, self.pc) & 0xFF)
                    self.pc += 1
                continue

            if mnemonic == 'END':
                break

            if mnemonic not in self.opcodes:
                raise ValueError(f"Unknown instruction: {mnemonic}")

            op, fmt = self.opcodes[mnemonic]
            byte1 = op
            byte2 = None
            reloc_label = None

            if fmt == 'N':
                pass
            elif fmt == 'R':
                byte1 |= self._get_reg(parts[1])
            elif fmt == 'D':
                byte1 |= self._parse_value(parts[1], self.pc) & 0xF
            elif fmt == 'P':
                byte1 |= self._get_pair(parts[1])
                if mnemonic == 'FIM':
                    byte2 = self._parse_value(parts[2], self.pc) & 0xFF
            elif fmt == 'A12':
                addr = self._parse_value(parts[1], self.pc)
                byte1 |= (addr >> 8) & 0xF
                byte2 = addr & 0xFF
                if parts[1] in self.labels or parts[1] in self.externals:
                    reloc_label = parts[1]
            elif fmt == 'ISZ':
                byte1 |= self._get_reg(parts[1])
                page_addr = self._parse_value(parts[2], self.pc)
                byte2 = page_addr & 0xFF
                if parts[2] in self.labels or parts[2] in self.externals:
                    reloc_label = parts[2]
            elif fmt == 'COND':
                cond_str = parts[1].upper().replace('?', '')  # Remove ? for historical syntax
                cond_bits = self.conditions.get(cond_str, 0x0)
                byte1 |= cond_bits
                page_addr = self._parse_value(parts[2], self.pc)
                byte2 = page_addr & 0xFF
                if parts[2] in self.labels or parts[2] in self.externals:
                    reloc_label = parts[2]

            self.binary.append(byte1)
            self.pc += 1

            if byte2 is not None:
                if reloc_label:
                    self.relocations.append((self.pc, reloc_label, fmt))
                self.binary.append(byte2)
                self.pc += 1

    def assemble(self, source_code):
        lines = source_code.split('\n')

        self.labels = {}
        self.externals = set()
        self.relocations = []

        self.pass1(lines)
        self.pass2(lines)

        return {
            'code': bytearray(self.binary),
            'symbols': self.labels,
            'externals': list(self.externals),
            'relocations': self.relocations
        }