# Assembly Programming Guide

[← Previous: User Guide](./02-user-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: BASIC Programming Guide →](./04-basic-programming-guide.md)

---

This guide is for anyone who wants to write programs in Intel 4004 assembly. It assumes you have read the [Introduction and Overview](./01-introduction-and-overview.md) and are familiar with the basics: 4-bit registers, a 12-bit program counter, and the Harvard architecture. Here we focus on the practical side: syntax, directives, expressions, and building a program from several modules.

If you want to start with something simpler, see the [BASIC Programming Guide](./04-basic-programming-guide.md). If you need a quick lookup for specific instructions and operand formats, keep the [Toolchain Reference](./05-toolchain-reference.md) nearby.

---

## 1. Two syntaxes: historical and modern

The assembler supports two styles of notation. This is not a whim — it is a deliberate choice. Programs from Intel's 1970s documentation must assemble unchanged, while new programs should be comfortable to write.

**The historical syntax** was used by the original Intel 4004 Toolkit. Registers are written as `0R`–`15R`, pairs as `0P`–`7P`, comments begin with `/`, and the `ORG` directive is written as `=`. For example:

```asm
/ This is a comment
    = 0x000
loop,   LDM 5
        XCH 0R
        JUN loop
```

**The modern syntax** is closer to what you are probably used to. Registers are written as `R0`–`R15`, pairs as `P0`–`P7`, comments begin with `//` or `;`, and `ORG` is written explicitly. The same example:

```asm
// This is a comment
    ORG 0x000
loop:   LDM 5
        XCH R0
        JUN loop
```

The assembler understands both forms and does not require you to choose one permanently. You can mix them within a single file, although consistency improves readability.

---

## 2. Program structure

An assembly program consists of lines. Each line may contain a label, an instruction mnemonic, operands, and a comment. The order is flexible, but a few rules make code predictable.

**Labels.** A label is a name that you assign to an address in memory. In the historical syntax, a label ends with a comma (`loop,`); in the modern syntax, with a colon (`loop:`). Labels are used by jump instructions (`JUN`, `JMS`, `JCN`, `ISZ`) and by the `EQU` and `=` directives.

**Mnemonics.** These are instruction names: `LDM`, `XCH`, `ADD`, `JUN`, and others. Case does not matter: `ldm`, `LDM`, and `LdM` are the same.

**Operands.** Depending on the instruction, there may be no operands (`NOP`, `HLT`), one operand (`LDM 5`, `ADD R3`), or two (`FIM P0, 0xE0`, `ISZ R2, loop`). Operand formats are explained in section 5.

**Comments.** Everything after `//`, `;`, or `/` is ignored by the assembler. Comments help explain what the code does, and we recommend using them.

**Blank lines.** They are ignored and exist only for readability.

---

## 3. Directives: controlling assembly

Directives are commands for the assembler, not for the processor. They do not become machine bytes, but they control how the assembler processes the source.

### ORG — origin

The `ORG` directive sets the address at which the next byte of code or data will be placed. In the historical syntax it is written as `=`. For example:

```asm
    ORG 0x000
```

This line tells the assembler: "the next instruction should land at address `0x000`". `ORG` is usually used at the start of a program to set the entry point, but it can appear mid-file to place a data table at a fixed address.

### EQU — equate

The `EQU` directive assigns a value to a symbolic name. This is convenient for constants:

```asm
BUFFER_SIZE EQU 64
PORT_UART   EQU 0xE0
```

After this, you can use `BUFFER_SIZE` and `PORT_UART` anywhere in the program, and the assembler substitutes the numbers. In the modern syntax, the `=` sign plays the same role:

```asm
BUFFER_SIZE = 64
```

### DB — define bytes

The `DB` directive places a sequence of bytes in memory. This is useful for tables, strings, or initial values:

```asm
message: DB 0x48, 0x65, 0x6C, 0x6C, 0x6F
```

Each value in the list occupies one byte.

### END — end of program

The `END` directive tells the assembler that the source text is finished. Everything after it is ignored. This is useful when you want to temporarily disable part of the code without deleting it.

---

## 4. Expressions and the `*` symbol

Operands in instructions and directives can be more than just numbers and labels. The assembler supports addition (`+`), subtraction (`-`), multiplication (`*`), and parentheses for grouping.

**The `*` symbol** is a special case. In an expression, it means **the current address** (the value of the program counter at that moment). This lets you write position-independent code:

```asm
    JUN *+4     // Jump 4 bytes forward
```

This form was common in 4004 programs because it avoided labels for short jumps.

**Labels in expressions.** You can use labels as numbers:

```asm
    LDM BUFFER_SIZE - 1
    JUN loop + 2
```

The assembler substitutes the label addresses and computes the result.

**External labels.** If a label is not defined in the current file, the assembler does not raise an error immediately. It marks the label as `external`, leaves a placeholder (`0x00`) in the code, and records a relocation. Later the linker finds that label in another module and patches the correct address. This is the foundation of modular assembly, which we cover in section 6.

> [!NOTE]
> Expressions are evaluated with Python's `eval()` function, but built-ins are disabled (`{"__builtins__": None}`). This prevents arbitrary code execution if something unexpected ends up in an expression.

---

## 5. Instruction set and operand formats

The Intel 4004 has 46 instructions. The full reference with opcodes and examples is in the [Toolchain Reference](./05-toolchain-reference.md). Here we cover how the assembler interprets operands.

Each instruction has an **operand format**. The main formats are:

- **`N` (no operands).** Instructions without parameters: `NOP`, `HLT`, `CLB`, `CMC`, and others.
- **`R` (register).** A single 4-bit register: `ADD R3`, `XCH R0`, `INC R2`. The assembler encodes the register number in the low 4 bits of the opcode.
- **`D` (data).** A 4-bit immediate value: `LDM 5`, `BBL 0`. The value is masked to 4 bits, so numbers larger than `0xF` are truncated.
- **`P` (register pair).** A pair used as an 8-bit pointer: `FIM P0, 0xE0`, `SRC P4`, `FIN P2`, `JIN P6`. The assembler converts the pair number into an even register number.
- **`A12` (12-bit address).** Two-byte jump instructions: `JUN 0x123`, `JMS loop`. The assembler splits the address into a high nibble (first byte) and a low byte (second byte).
- **`COND` (condition).** A special format for `JCN`: `JCN Z, loop`, `JCN C, loop`. The assembler substitutes the 4-bit condition code.
- **`ISZ` (increment and skip).** A two-byte instruction that combines a register and a page address: `ISZ R2, loop`.

In the historical syntax, pairs and registers are written differently (`0P`–`7P`, `0R`–`15R`), but the principle is the same.

---

## 6. Modularity: building a program from parts

One of the strongest features of the toolchain is support for modular assembly. You can split a program into several files, each solving its own problem, and then combine them with the linker.

**Why this matters.** Imagine a program that uses the monitor, a disk driver, and several utilities. Keeping everything in one file is inconvenient: it becomes huge and hard to follow. Modules let you separate responsibilities.

**How it works.** Each module is assembled separately. The assembler produces an object file containing:

- **`code`** — machine bytes.
- **`symbols`** — labels that the module exports (makes available to others).
- **`externals`** — labels the module expects to find in other files.
- **`relocations`** — records of where in the code external label addresses must be patched.

The **linker** takes several object files, places them in memory, verifies that their addresses do not overlap, and patches all external references. If a label is not found in any module, the linker reports an error.

**Example.** Suppose you have `main.asm` that calls a subroutine `print_char`. In `main.asm` you write:

```asm
    JMS print_char
```

The assembler sees that `print_char` is not defined in this file and records a relocation. In `io.asm` you define:

```asm
print_char:
    // ... code ...
    BBL 0
```

The linker finds `print_char` in `io.asm`, computes its absolute address, and patches it into `JMS`. The result works exactly as if it were a single file.

**Map file.** The linker can print a map showing which module starts at which address and where exported symbols are located. This helps during debugging: if a program "crashes", you can look at the map and see where control was transferred.

> [!TIP]
> Place the entry-point module first in the list you pass to the linker. By default, the linker places modules in the order they are given, starting at `base_address`.

---

## 7. Example: from source to ROM image

Consider a small program that adds two numbers and stores the result in a register.

```asm
// example.asm
    ORG 0x000
start:
    LDM 5
    XCH R0      // R0 = 5
    LDM 3
    XCH R1      // R1 = 3
    LD R0       // ACC = 5
    ADD R1      // ACC = 8
    XCH R2      // R2 = 8
    HLT
    END
```

**What happens during assembly.** The assembler processes the file twice. The first pass (`pass1`) computes all label addresses and instruction sizes. The second pass (`pass2`) generates bytes: `LDM 5` becomes `0xD5`, `XCH R0` becomes `0xB0`, `ADD R1` becomes `0x81`, and so on. `HLT` is `0x01`. `END` stops assembly. The result is a short sequence of bytes ready to load into ROM.

**What happens during linking.** If the program referenced an external label, the linker would patch its address. In this case there are no external references, so the linker simply places the code at `0x000` and returns the finished image.

---

## 8. Debugging: finding out what went wrong

The assembler and linker try to help you find errors.

- **Syntax errors.** If the assembler encounters an unknown mnemonic or an invalid operand, it reports the line. For example: `Unknown instruction: LDA`.
- **Undefined labels.** If a label is not found and cannot be external (for example, you misspelled the name), the linker reports `Unresolved external symbols`.
- **Address overlaps.** If two modules claim the same memory region, the linker reports `Address overlap`.
- **Duplicate symbols.** If two modules export a label with the same name, the linker reports `Duplicate public symbol`.

Once the program is assembled, you can use the **General** tab in the emulator interface to observe registers and the program counter after each step. This is the most reliable way to understand why a program behaves differently from what you expected.

---

## Conclusion

Intel 4004 assembly is a language that rewards discipline with understanding. You work directly with registers, see every byte and every jump. The toolchain tries to make this process comfortable: two syntaxes, expression support, modular assembly, and detailed error messages.

If you want to go deeper into specific topics, see:

- [BASIC Programming Guide](./04-basic-programming-guide.md) — if you want to write in a high-level language.
- [Toolchain Reference](./05-toolchain-reference.md) — full reference for the assembler and linker.
- [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) — CPU internals and the instruction cycle.
- [System Monitor and Disk Operations](./08-system-monitor-and-disk-operations.md) — if you want to use the ready-made monitor and work with disks.

Now try writing something of your own. Start simple: add two numbers, print the result to the teletype, build a loop. With each step, the 4004 architecture becomes a little more familiar.

---

[← Previous: User Guide](./02-user-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: BASIC Programming Guide →](./04-basic-programming-guide.md)
