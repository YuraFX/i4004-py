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

class BasicCodeGen:
    def __init__(self):
        self.var_map = {
            'A': 'R0', 'B': 'R1', 'C': 'R2', 'D': 'R3',
            'E': 'R4', 'F': 'R5', 'G': 'R6', 'H': 'R7'
        }
        self.asm_lines = []
        self.line_map = {}
        self.label_counter = 0

    def _emit(self, line):
        self.asm_lines.append(line)

    def generate(self, program_ast):
        self.asm_lines = []
        self.line_map = {}
        self.label_counter = 0

        self._emit("ORG 0x000")

        sorted_lines = sorted(program_ast.keys())
        if sorted_lines:
            first_line = sorted_lines[0]
            self._emit(f"JUN L{first_line}")
            self.line_map[0] = first_line
            self.line_map[1] = first_line
        self._emit("")

        current_pc = 2

        for line_num in sorted_lines:
            self.line_map[current_pc] = line_num
            self._emit(f"L{line_num}:")
            start_idx = len(self.asm_lines)
            self._generate_statement(program_ast[line_num])

            for asm_line in self.asm_lines[start_idx:]:
                asm_line = asm_line.strip()
                if not asm_line or asm_line.startswith(';') or asm_line.endswith(':'):
                    continue
                op = asm_line.split()[0].upper()
                if op in ['JUN', 'JMS', 'JCN', 'ISZ', 'FIM']:
                    current_pc += 2
                elif op not in ['ORG', 'END']:
                    current_pc += 1
            self._emit("")

        self._emit("L_HALT:")
        self._emit("    HLT")
        
        # Teletype output subroutine
        self._emit("")
        self._emit("TTY_SEND_CHAR:")
        self._emit("    FIM P7 0x00")     # Configure Port 0 via the free pair R14/R15
        self._emit("    SRC P7")
        self._emit("    LDM 0")           # Start bit
        self._emit("    WMP")
        
        self._emit("    LDM 12")          # Counter for 4 iterations
        self._emit("    XCH R12")
        self._emit("TTY_SEND_LOW:")
        self._emit("    LD R10")          # Low nibble (from R10)
        self._emit("    RAR")
        self._emit("    XCH R10")
        self._emit("    TCC")
        self._emit("    WMP")
        self._emit("    ISZ R12 TTY_SEND_LOW")
        self._emit("    NOP")
        
        self._emit("    LDM 12")
        self._emit("    XCH R12")
        self._emit("TTY_SEND_HIGH:")
        self._emit("    LD R11")          # High nibble (from R11)
        self._emit("    RAR")
        self._emit("    XCH R11")
        self._emit("    TCC")
        self._emit("    WMP")
        self._emit("    ISZ R12 TTY_SEND_HIGH")
        self._emit("    NOP")
        
        self._emit("    LDM 1")           # Stop bits
        self._emit("    WMP")
        self._emit("    LDM 1")
        self._emit("    WMP")
        self._emit("    BBL 0")           # Return

        return "\n".join(self.asm_lines)

    def _generate_statement(self, stmt):
        stmt_type = type(stmt).__name__

        if stmt_type == 'LetStmt':
            self._generate_expression(stmt.expr)
            reg = self.var_map[stmt.var_name]
            self._emit(f"    XCH {reg}")

        elif stmt_type == 'PrintStmt':
            # Evaluate expression (result in ACC)
            self._generate_expression(stmt.expr)
            
            # 1. Legacy behavior: output number/variable to RAM
            self._emit("    WRM")
            
            # 2. New behavior: output to teletype
            num_id = self.label_counter
            self.label_counter += 1
            
            self._emit("    XCH R9")           # ACC -> R9 (save the number)
            self._emit("    LDM 10")           # ACC = 10
            self._emit("    XCH R8")           # R8 = 10
            self._emit("    LD R9")            # ACC = number
            self._emit("    SUB R8")           # ACC = number - 10
            
            # If number >= 10 (CY flag == 1, since subtraction has no borrow), go to the HEX branch
            self._emit(f"    JCN C L_HEX_{num_id}")
            
            # DECIMAL (0-9)
            self._emit("    LD R9")            # ACC = number
            self._emit("    XCH R10")          # R10 = low nibble (number)
            self._emit("    LDM 3")            # Base for '0' (0x30)
            self._emit("    XCH R11")          # R11 = high nibble
            self._emit("    JMS TTY_SEND_CHAR")
            self._emit(f"    JUN L_DONE_{num_id}")
            
            # HEX (10-15 -> A-F)
            self._emit(f"L_HEX_{num_id}:")
            self._emit("    LD R9")            # ACC = number
            self._emit("    SUB R8")           # ACC = number - 10 (0-5)
            self._emit("    XCH R10")          # R10 = low nibble
            self._emit("    LDM 4")            # Base for 'A' (0x41)
            self._emit("    XCH R11")          # R11 = high nibble
            self._emit("    JMS TTY_SEND_CHAR")
            
            self._emit(f"L_DONE_{num_id}:")
            # Add carriage return (13) and line feed (10)
            self._emit("    LDM 13")
            self._emit("    XCH R10")
            self._emit("    LDM 0")
            self._emit("    XCH R11")
            self._emit("    JMS TTY_SEND_CHAR")
            
            self._emit("    LDM 10")
            self._emit("    XCH R10")
            self._emit("    LDM 0")
            self._emit("    XCH R11")
            self._emit("    JMS TTY_SEND_CHAR")

        elif stmt_type == 'PrintStrStmt':
            # Output string to teletype
            for char in stmt.text:
                ascii_val = ord(char)
                low_nibble = ascii_val & 0xF
                high_nibble = (ascii_val >> 4) & 0xF
                self._emit(f"    LDM {low_nibble}")
                self._emit(f"    XCH R10")
                self._emit(f"    LDM {high_nibble}")
                self._emit(f"    XCH R11")
                self._emit(f"    JMS TTY_SEND_CHAR")
            
            # Add carriage return and line feed (\r\n)
            for char in '\r\n':
                ascii_val = ord(char)
                low_nibble = ascii_val & 0xF
                high_nibble = (ascii_val >> 4) & 0xF
                self._emit(f"    LDM {low_nibble}")
                self._emit(f"    XCH R10")
                self._emit(f"    LDM {high_nibble}")
                self._emit(f"    XCH R11")
                self._emit(f"    JMS TTY_SEND_CHAR")

        elif stmt_type == 'GotoStmt':
            self._emit(f"    JUN L{stmt.line_num}")

        elif stmt_type == 'IfStmt':
            self._generate_expression(stmt.condition)
            op = stmt.condition.op if hasattr(stmt.condition, 'op') else '='
            if op == '=':
                self._emit(f"    JCN Z L{stmt.then_stmt.line_num}")
            else:
                self._emit(f"    JCN NZ L{stmt.then_stmt.line_num}")

        elif stmt_type == 'EndStmt':
            self._emit("    JUN L_HALT")

        elif stmt_type == 'RemStmt':
            pass

        elif stmt_type == 'GosubStmt':
            self._emit(f"    JMS L{stmt.line_num}")

        elif stmt_type == 'ReturnStmt':
            self._emit("    BBL 0")

        elif stmt_type == 'StopStmt':
            self._emit("    JUN L_HALT")

        elif stmt_type == 'ForStmt':
            self._generate_expression(stmt.start_expr)
            self._emit("    XCH R8")
            self._generate_expression(stmt.end_expr)
            self._emit("    XCH R9")

            loop_label = f"L_FOR_{self.label_counter}"
            self.label_counter += 1
            self._emit(f"{loop_label}:")

            for body_stmt in stmt.body:
                self._generate_statement(body_stmt)

            self._emit("    LD R8")
            self._emit("    IAC")
            self._emit("    XCH R8")
            self._emit("    SUB R9")
            self._emit(f"    JCN NZ {loop_label}")

    def _generate_expression(self, expr):
        expr_type = type(expr).__name__

        if expr_type == 'NumberExpr':
            val = expr.value & 0xF
            self._emit(f"    LDM {val}")

        elif expr_type == 'VarExpr':
            reg = self.var_map[expr.name]
            self._emit(f"    LD {reg}")

        elif expr_type == 'BinaryExpr':
            self._generate_expression(expr.left)
            self._emit(f"    XCH R8")
            self._generate_expression(expr.right)
            op = expr.op
            if op == '+':
                self._emit(f"    ADD R8")
            elif op == '-':
                self._emit(f"    XCH R8")
                self._emit(f"    SUB R8")
            elif op == '=':
                self._emit(f"    XCH R8")
                self._emit(f"    SUB R8")