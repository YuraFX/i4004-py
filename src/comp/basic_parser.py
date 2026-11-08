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

# =================================================================
# AST NODES
# =================================================================
class LetStmt:
    def __init__(self, var_name, expr):
        self.var_name = var_name
        self.expr = expr

class PrintStmt:
    def __init__(self, expr):
        self.expr = expr

class PrintStrStmt:
    def __init__(self, text):
        self.text = text

class GotoStmt:
    def __init__(self, line_num):
        self.line_num = line_num

class IfStmt:
    def __init__(self, condition, then_stmt):
        self.condition = condition
        self.then_stmt = then_stmt

class EndStmt:
    pass

class RemStmt:
    pass

class GosubStmt:
    def __init__(self, line_num):
        self.line_num = line_num

class ReturnStmt:
    pass

class ForStmt:
    def __init__(self, var_name, start_expr, end_expr, step_expr, body):
        self.var_name = var_name
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.step_expr = step_expr
        self.body = body

class NextStmt:
    def __init__(self, var_name):
        self.var_name = var_name

class StopStmt:
    pass

class BinaryExpr:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class NumberExpr:
    def __init__(self, value):
        self.value = value

class VarExpr:
    def __init__(self, name):
        self.name = name

# =================================================================
# PARSER
# =================================================================
class BasicParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0

    def parse(self, tokens):
        self.tokens = tokens
        self.pos = 0
        program = {}
        while self.pos < len(self.tokens):
            if self._peek()[0] == 'NEWLINE':
                self.pos += 1
                continue

            if self._peek()[0] != 'NUMBER':
                raise ValueError(f"Line {self._peek()[1] if self._peek()[0]=='NEWLINE' else '?'}: Expected a line number")

            line_num = self._next()[1]
            stmt = self._parse_statement()
            program[line_num] = stmt

            while self.pos < len(self.tokens) and self._peek()[0] == 'NEWLINE':
                self.pos += 1
        return program

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', None)

    def _next(self):
        token = self._peek()
        self.pos += 1
        return token

    def _expect(self, token_type):
        token = self._next()
        if token[0] != token_type:
            raise ValueError(f"Expected {token_type}, got {token[0]}")
        return token

    def _parse_statement(self):
        token = self._peek()
        if token[0] != 'KEYWORD':
            raise ValueError("Expected a command")

        keyword = token[1]
        self._next()

        if keyword == 'LET':
            var_name = self._expect('VARIABLE')[1]
            self._expect('OPERATOR')  # '='
            expr = self._parse_expression()
            return LetStmt(var_name, expr)

        elif keyword == 'PRINT':
            if self._peek()[0] == 'STRING':
                text = self._next()[1]
                return PrintStrStmt(text)
            else:
                expr = self._parse_expression()
                return PrintStmt(expr)

        elif keyword == 'GOTO':
            line_num = self._expect('NUMBER')[1]
            return GotoStmt(line_num)

        elif keyword == 'IF':
            condition = self._parse_expression()
            self._expect('KEYWORD')  # THEN
            then_stmt = self._parse_statement()
            return IfStmt(condition, then_stmt)

        elif keyword == 'END':
            return EndStmt()

        elif keyword == 'REM':
            while self.pos < len(self.tokens) and self._peek()[0] != 'NEWLINE':
                self.pos += 1
            return RemStmt()

        elif keyword == 'GOSUB':
            line_num = self._expect('NUMBER')[1]
            return GosubStmt(line_num)

        elif keyword == 'RETURN':
            return ReturnStmt()

        elif keyword == 'STOP':
            return StopStmt()

        elif keyword == 'FOR':
            var_name = self._expect('VARIABLE')[1]
            self._expect('OPERATOR')  # '='
            start_expr = self._parse_expression()
            self._expect('KEYWORD')  # TO
            end_expr = self._parse_expression()
            step_expr = None
            if self._peek()[0] == 'KEYWORD' and self._peek()[1] == 'STEP':
                self._next()
                step_expr = self._parse_expression()
            body = []
            while self.pos < len(self.tokens):
                if self._peek()[0] == 'KEYWORD' and self._peek()[1] == 'NEXT':
                    self._next()
                    var_name_next = self._expect('VARIABLE')[1]
                    break
                body.append(self._parse_statement())
            return ForStmt(var_name, start_expr, end_expr, step_expr, body)

        elif keyword == 'NEXT':
            var_name = self._expect('VARIABLE')[1]
            return NextStmt(var_name)

        elif keyword in ['RUN', 'LIST', 'NEW']:
            return RemStmt()

        else:
            raise ValueError(f"Unknown command: {keyword}")

    def _parse_expression(self):
        left = self._parse_term()
        while self._peek()[0] == 'OPERATOR' and self._peek()[1] in ['+', '-', '=', '<', '>', '<=', '>=', '<>']:
            op = self._next()[1]
            right = self._parse_term()
            left = BinaryExpr(left, op, right)
        return left

    def _parse_term(self):
        left = self._parse_factor()
        while self._peek()[0] == 'OPERATOR' and self._peek()[1] in ['*', '/']:
            op = self._next()[1]
            right = self._parse_factor()
            left = BinaryExpr(left, op, right)
        return left

    def _parse_factor(self):
        token = self._peek()
        if token[0] == 'NUMBER':
            self._next()
            return NumberExpr(token[1])
        elif token[0] == 'VARIABLE':
            self._next()
            return VarExpr(token[1])
        elif token[0] == 'OPERATOR' and token[1] == '(':
            self._next()
            expr = self._parse_expression()
            self._expect('OPERATOR')
            return expr
        else:
            raise ValueError(f"Unexpected token in expression: {token}")