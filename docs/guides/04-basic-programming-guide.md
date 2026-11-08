# BASIC Programming Guide

[← Previous: Assembly Programming Guide](./03-assembly-programming-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Toolchain Reference →](./05-toolchain-reference.md)

---

This guide is for anyone who wants to write programs for the emulator without diving straight into assembly. BASIC in this project is a teaching language: it compiles to Intel 4004 assembly, and that assembly is then turned into machine code. BASIC is not a complete recreation of the classic 1970s language, but it provides enough to learn the fundamentals of programming for a 4-bit processor.

We assume you have read the [Introduction and Overview](./01-introduction-and-overview.md) and are familiar with the basic ideas: 4-bit registers, a 12-bit program counter, and the fact that a byte travels as two halves. If you want to write assembly directly, see the [Assembly Programming Guide](./03-assembly-programming-guide.md).

---

## 1. Why BASIC exists in a 4004 emulator

Writing assembly for the 4004 means juggling registers, nibbles, and jumps. It is powerful, but it demands discipline. BASIC lets you learn the *logic* of a program first — variables, conditions, loops, subroutines — and then, if you want, look at the generated assembly to see how it all works under the hood.

Our BASIC is a teaching tool. That means it has deliberate simplifications. We do not try to hide them: section 8 explains in detail what the language cannot do and why. Those are not bugs; they are consequences of 4-bit architecture and of keeping the code generator simple enough to read.

---

## 2. How BASIC becomes machine code

Before writing your first program, it helps to understand the path your text takes. This will make it easier to interpret error messages and understand where something went wrong.

```text
BASIC source
    │
    ▼
BasicLexer.tokenize()       — lexical analysis: text → list of tokens
    │
    ▼
BasicParser.parse()         — syntactic analysis: tokens → AST
    │
    ▼
BasicCodeGen.generate()     — code generation: AST → assembly text
    │
    ▼
Assembler.assemble()        — assembly: assembly text → machine bytes
    │
    ▼
4004 emulator
```

Three files, three stages. The **lexer** (`basic_lexer.py`) chops the source into tokens: numbers, keywords, variables, operators, and strings. The **parser** (`basic_parser.py`) builds a syntax tree (AST) in which each BASIC line is represented by an object. The **code generator** (`basic_codegen.py`) walks the tree and prints assembly lines. Then the assembler takes over, as described in the [Assembly Programming Guide](./03-assembly-programming-guide.md).

This is a classic teaching-compiler design. There is no intermediate representation, no optimization, and no register allocation: everything is as straightforward as possible. That is why the code generator can be read from top to bottom and understood.

---

## 3. Program structure: line numbers

A BASIC program is a set of lines, each beginning with a number. The number is an integer, and it is used for addressing: `GOTO 100` means "jump to line 100".

```basic
10 LET A = 5
20 PRINT A
30 END
```

The order of lines in the file does not matter: the parser stores them in a dictionary `{number: node}`, and the code generator sorts them by number. This means you can write lines in any order, and the program still executes in ascending numeric order. If two numbers collide, the second line silently overwrites the first — a limitation to keep in mind.

**Comments.** There are two ways to leave a comment in BASIC. First, the `REM` keyword: everything after it until the end of the line is ignored. Second, the characters `//` and `;` — everything after them is also discarded. The second form is convenient, but it has a catch: comments are stripped **before** the line is parsed, so `PRINT "A;B"` will be cut at `;` and the program will break. This is covered in more detail in section 8.

**Blank lines.** They are ignored and exist only for readability.

---

## 4. Variables: only A–H

In our BASIC, a variable is a single letter from `A` to `H`. Each variable corresponds to a processor register:

| Variable | Register |
|----------|----------|
| `A` | `R0` |
| `B` | `R1` |
| `C` | `R2` |
| `D` | `R3` |
| `E` | `R4` |
| `F` | `R5` |
| `G` | `R6` |
| `H` | `R7` |

Why only eight? The 4004 has 16 registers, but half of them are used by the code generator as temporaries (`R8`–`R12`) and as the teletype port (`R14`–`R15`). The remaining eight are available to the programmer.

Variables `I`–`Z` are not supported: the lexer recognizes only single-letter names, and the code generator looks them up in the `var_map` table. If you try to use `I`, the parser reports `Unknown word`.

Numbers in BASIC are 4-bit values. If you write `LET A = 20`, the code generator produces `LDM 20 & 0xF`, which is `LDM 4`. This is not an error — it is a consequence of architecture: the 4004 accumulator holds only 4 bits. Keep values in the range `0`–`15` and remember that anything larger will be truncated.

> [!WARNING]
> `LET A = 20` does not fail. It silently becomes `LET A = 4`. The language does not warn you about truncation.

---

## 5. Expressions: numbers, variables, and operators

BASIC expressions consist of numbers, variables, and operators. The parser supports three precedence levels:

- **Addition and subtraction** (`+`, `-`) — lowest priority.
- **Multiplication and division** (`*`, `/`) — higher.
- **Comparisons** (`=`, `<`, `>`, `<=`, `>=`, `<>`) — at the same level as `+` and `-`.

Parentheses `(` and `)` allow you to group expressions. There is no unary minus: `-5` does not parse as an expression, but `0 - 5` works.

**An important limitation.** The parser understands `*`, `/`, `<`, `>`, `<=`, `>=`, and `<>`, but the code generator produces code only for `+`, `-`, and `=`. If you use `*` or `/`, the program will build, but the result will be wrong, because the code generator simply does nothing for those operators. We state this openly here so you do not spend time debugging it.

---

## 6. Language statements

Here is the full list of statements our BASIC supports. For each, we show the syntax, an example, and what it turns into in assembly.

### LET — assignment

```basic
10 LET A = 5
```

Evaluates the expression and stores the result in a variable. In assembly this looks as follows: the expression leaves the result in the accumulator, then `XCH R0` swaps the accumulator and register `R0`. After that, `R0` (variable `A`) holds the result.

### PRINT — output

`PRINT` has two modes.

**PRINT with an expression** outputs a number as a single hexadecimal character `0`–`F`:

```basic
10 PRINT A
```

Under the hood the following happens. The expression is evaluated and the result ends up in the accumulator. Then `WRM` executes — a write to RAM at the address stored in the pair `R0:R1`. This is the "legacy behavior" inherited from early versions; it can be dangerous if you do not control `R0` and `R1`. After that, the number is converted to a character: if it is less than 10, `'0'` (0x30) is added; if it is 10 or greater, `'A'` (0x41) is added. The character is sent to the teletype via the `TTY_SEND_CHAR` subroutine, followed by carriage return and line feed.

**PRINT with a string** outputs text:

```basic
10 PRINT "HELLO"
```

Each character is encoded in ASCII, split into two 4-bit nibbles, and sent to the teletype: low nibble first, then high nibble. A `\r\n` follows automatically.

### GOTO — unconditional jump

```basic
10 GOTO 100
```

Compiles to `JUN L100`, an unconditional jump to the label corresponding to line 100.

### IF...THEN — conditional jump

```basic
10 IF A = 5 THEN GOTO 100
```

Evaluates the condition and, if true, jumps to the specified line. In assembly this looks as follows: the condition leaves a difference in the accumulator. If `A = 5`, the difference is zero, and `JCN Z L100` fires (jump if zero). If the condition is not `=`, `JCN NZ L100` fires (jump if not zero).

**An important limitation.** Only the form `IF ... THEN GOTO ...` works reliably. The reason is that the code generator expects `then_stmt` to have a `line_num` attribute, and only `GotoStmt` has one. If you write `IF A = 5 THEN PRINT A`, the code generator raises an error. This is a deliberate simplification: full conditional constructs require a more complex code generator.

### FOR...NEXT — loop

```basic
10 FOR I = 1 TO 5
20 PRINT I
30 NEXT I
```

A counted loop. The code generator uses `R8` (counter) and `R9` (limit). On each iteration it increments `R8`, compares with `R9`, and jumps back to the loop label if they are not equal.

**Important limitations.** First, the variable name after `FOR` is ignored: the body does not see `I` even if it references `I`. Second, `STEP` is ignored: the step is always one. Third, there is an off-by-one problem: `FOR I = 1 TO 3` runs the body for `1` and `2` but not for `3`. Fourth, `R8` and `R9` are used as temporaries in expressions and `PRINT`, so a loop with `PRINT` inside it may break when the counter is overwritten. That is an architectural constraint: there are too few registers to dedicate separate ones for loops and expressions. We recommend using `FOR` for simple loops without complex expressions inside.

### GOSUB...RETURN — subroutine

```basic
10 GOSUB 100
20 END
100 PRINT "HI"
110 RETURN
```

A subroutine call and return. `GOSUB` compiles to `JMS L100`, `RETURN` to `BBL 0`. Remember that the 4004 stack has only three levels, so deep `GOSUB` nesting will fail: the fourth call overwrites the oldest return address.

### END, STOP — termination

`END` and `STOP` compile to `JUN L_HALT`, and the `L_HALT` label contains `HLT`. The program stops.

### REM — comment

Everything after `REM` to the end of the line is ignored. This is convenient for explanations.

### RUN, LIST, NEW

These keywords are recognized by the lexer, but the parser turns them into `RemStmt` — that is, "do nothing". They do not implement an interactive mode in the current version; they simply let a program assemble if you copy code from an old manual.

### INPUT

The `INPUT` keyword is in the list, but the parser does not implement it: using `INPUT` produces `Unknown command`. This is a place holder for the future.

---

## 7. How BASIC becomes assembly

The code generator is the heart of the compiler. It walks the AST and prints assembly lines. Here is what to know to understand the generated code.

**Entry point.** The first line of the program is `ORG 0x000` and `JUN L<first_line_number>`. After reset, the CPU jumps straight to the first BASIC line.

**Line labels.** Each BASIC line gets a label `L<number>`. Line 10 becomes `L10:`. `GOTO`, `GOSUB`, and `IF` use these labels for jumps.

**Temporary registers.** The code generator uses `R8` and `R9` to hold intermediate values in expressions and `PRINT`. `R10` and `R11` hold the low and high nibbles of a character for the teletype. `R12` is the bit counter in `TTY_SEND_CHAR`. `R14` and `R15` (pair `P7`) form the port for `SRC`.

**The TTY_SEND_CHAR subroutine.** To keep `PRINT` code compact, character output is moved into a subroutine. It configures the port, sends a start bit, then 4 bits of the low nibble, 4 bits of the high nibble, and two stop bits. This is classic asynchronous LSB-first transmission. The subroutine does not save `R10`, `R11`, or `R12`, so it is not reentrant — acceptable for a teaching language.

**Line map.** The code generator fills in a dictionary mapping an assembly address to a BASIC line number. This is used for debugging: when you look at `PC` in the interface, the emulator can highlight the corresponding BASIC line. The map does not affect assembly itself.

---

## 8. Language limitations and why they exist

We deliberately do not hide limitations, because honesty helps you understand faster. Here is what our BASIC cannot do and why.

**Variables only `A`–`H`.** Of the 16 registers, 8 are taken by the code generator. This is a compromise between convenience and code simplicity.

**Numbers are masked to 4 bits.** `LET A = 20` produces `4`. This is a consequence of 4-bit architecture: the accumulator holds only 4 bits. If you need more, use register pairs manually — but that is assembly-level work.

**`PRINT` outputs one hex character, not a decimal number.** Our `PRINT` cannot print `123` as `123`. It prints `F` for `15`, `A` for `10`, and so on. For a teaching language, this is acceptable; full decimal output would require a more complex code generator.

**`*` and `/` are parsed but not generated.** The parser understands these operators, but the code generator does nothing for them. The result will be incorrect. If you need multiplication, implement it through repeated addition in a loop.

**Comparisons work only with `=` and `<>` (via `IF`).** The `IF` code generator looks at the operator and produces `JCN Z` for `=` and `JCN NZ` for everything else. Operators `<`, `>`, `<=`, `>=` do not generate correct code.

**`FOR` ignores `STEP` and the variable name.** The counter is always in `R8`, the limit in `R9`, and the step is always 1. The loop body does not see the loop variable. There is an off-by-one issue: the last value is not executed.

**Comments are stripped before parsing.** The line `PRINT "A;B"` is cut at `;`. The same applies to `//` inside a string. If you need a string containing these characters, use a `REM` comment or avoid them.

**`INPUT`, `RUN`, `LIST`, `NEW` are not implemented.** They are recognized but do nothing. This is a place holder for the future.

All these limitations are consequences of BASIC being a teaching language rather than a full compiler. If you need more, use assembly: it gives full control.

> [!NOTE]
> All of these limitations are documented in the source of `basic_codegen.py`. If you want to extend the language, that is the file to study.

---

## 9. Example: a complete program

Here is a small program that adds two numbers and prints the result to the teletype.

```basic
10 LET A = 5
20 LET B = 3
30 LET C = A + B
40 PRINT C
50 END
```

**What happens step by step.**

- **Line 10.** The expression `5` generates `LDM 5`. Then `XCH R0` stores the result in `A`.
- **Line 20.** Same pattern: `LDM 3` and `XCH R1` for `B`.
- **Line 30.** The expression `A + B`: `LD R0` (load `A` into the accumulator), `XCH R8` (save the left operand), `LD R1` (load `B`), `ADD R8` (add). The result is in the accumulator. Then `XCH R2` stores it in `C`.
- **Line 40.** `PRINT C` loads `C` into the accumulator, executes `WRM`, converts the number to a hex character, and sends it to the teletype through `TTY_SEND_CHAR`. Then it prints `\r\n`.
- **Line 50.** `END` compiles to `JUN L_HALT`, and `L_HALT` contains `HLT`.

As a result, `8` (because `5 + 3 = 8`) appears on the teletype, followed by a newline.

---

## 10. Debugging: finding out what went wrong

When a program does not behave as expected, several tools are available.

**Error messages.** The lexer and parser report line numbers. For example, `Line 3: Unknown word 'PRINTX'` means an unknown word was encountered on line 3. If the error is in assembly, it appears during the build — check the mnemonic or label.

**General tab.** After pressing **Build** and **Step over**, you can observe registers. For example, if `PRINT` outputs the wrong character, look at `ACC` and `R8`–`R12` before `TTY_SEND_CHAR`.

**Line map.** If you want to know which BASIC line is currently executing, use the editor highlight: the emulator maps `PC` to a line number through `line_map`.

**Generated assembly.** Although the interface does not show it directly, you can save the BASIC program and then inspect `line_map` or add debug output. Understanding how BASIC turns into assembly helps find logical errors.

---

## Conclusion

BASIC in this emulator is not an attempt to recreate the classic language of the 1970s, but a teaching tool. It lets you learn programming logic without worrying about registers and nibbles, while honestly showing where its capabilities end. If you need more control, move on to assembly: the [Assembly Programming Guide](./03-assembly-programming-guide.md) and the [Toolchain Reference](./05-toolchain-reference.md) will help.

If you want to understand the code generator from the inside, see the [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) and the source of `basic_codegen.py`. You can see how each decision — using `R8`/`R9`, moving `TTY_SEND_CHAR` into a subroutine, dropping `*` and `/` — is tied to the constraints of a 4-bit world.

Try writing something of your own: a loop that prints the numbers from `0` to `F`, or a program that adds several values. Even with these limitations, you can do a lot.

---

[← Previous: Assembly Programming Guide](./03-assembly-programming-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Toolchain Reference →](./05-toolchain-reference.md)
