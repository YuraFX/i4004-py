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

class BasicLexer:
    def __init__(self):
        # List of keywords for our BASIC
        self.keywords = [
            'PRINT', 'LET', 'GOTO', 'IF', 'THEN', 'END',
            'REM', 'GOSUB', 'RETURN', 'FOR', 'TO', 'STEP', 'NEXT',
            'STOP', 'RUN', 'LIST', 'NEW', 'INPUT'
        ]

    def tokenize(self, source_code):
        lines = source_code.split('\n')
        tokens = []

        for line_num, line in enumerate(lines, 1):
            # Remove comments (// and ;)
            line = line.split('//')[0].split(';')[0].strip()
            if not line:
                continue

            i = 0
            in_rem = False
            while i < len(line):
                if in_rem:
                    # If we encountered REM, ignore everything until the end of the line
                    break

                char = line[i]

                if char.isspace():
                    i += 1
                    continue

                # 1. Numbers
                if char.isdigit():
                    num_str = ''
                    while i < len(line) and line[i].isdigit():
                        num_str += line[i]
                        i += 1
                    tokens.append(('NUMBER', int(num_str)))
                    continue

                # 2. Words (keywords and variables)
                if char.isalpha():
                    word = ''
                    while i < len(line) and line[i].isalnum():
                        word += line[i]
                        i += 1
                    word_upper = word.upper()
                    
                    if word_upper in self.keywords:
                        tokens.append(('KEYWORD', word_upper))
                        if word_upper == 'REM':
                            in_rem = True
                    else:
                        if len(word) == 1:
                            tokens.append(('VARIABLE', word_upper))
                        else:
                            raise ValueError(f"Line {line_num}: Unknown word '{word}'")
                    continue

                # 3. Operators and punctuation
                if i + 1 < len(line):
                    two_chars = line[i:i+2]
                    if two_chars in ['<=', '>=', '<>']:
                        tokens.append(('OPERATOR', two_chars))
                        i += 2
                        continue

                if char in ['+', '-', '*', '/', '=', '<', '>', '(', ')']:
                    tokens.append(('OPERATOR', char))
                    i += 1
                    continue

                # 4. String literals (for PRINT)
                if char == '"':
                    i += 1
                    string_val = ''
                    while i < len(line) and line[i] != '"':
                        string_val += line[i]
                        i += 1
                    if i < len(line) and line[i] == '"':
                        i += 1
                    tokens.append(('STRING', string_val))
                    continue

                raise ValueError(f"Line {line_num}: Unknown character '{char}'")

            tokens.append(('NEWLINE', line_num))

        return tokens