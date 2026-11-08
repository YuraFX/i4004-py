# Toolchain Reference: Assembler and Linker

[← Previous: BASIC Programming Guide](./04-basic-programming-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Architecture and Emulation Reference →](./06-architecture-and-emulation-reference.md)

---

This document is a reference, not a tutorial. You do not need to read it from cover to cover. If you already write assembly and want to look up an opcode, an operand format, or a relocation rule, open the relevant section and find the answer.

If you are just starting, read the [Assembly Programming Guide](./03-assembly-programming-guide.md) first: it explains how to write programs, which directives exist, and how modular assembly works. This document assumes you are familiar with the basics and want to look up details.

---

## 1. Assembler: general architecture

The assembler runs in two passes. This is the classic design that lets you use labels before they are defined.

**Pass 1 (`pass1`)** computes addresses. It walks through the source, records the position of every label in the `labels` table, and calculates how many bytes each instruction occupies. No machine code is generated yet: the assembler only maps out the program.

**Pass 2 (`pass2`)** generates bytes. It walks through the source again, but now it has the label table. For each instruction, it takes the base opcode, ORs in the register number or operand value, and appends the result to the output array `binary`.

**Data structures.** The `Assembler` class has several key fields:

| Field | Purpose |
|-------|---------|
| `opcodes` | Mnemonic dictionary: `{'LDM': (0xD0, 'D'), ...}`. The key is the instruction name; the value is a tuple of base byte and operand format. |
| `conditions` | Condition dictionary for `JCN`: `{'Z': 0x4, 'C': 0x2, ...}`. |
| `labels` | Symbol table: `{'loop': 0x010, ...}`. |
| `externals` | Set of labels not found in the current file that must be resolved by the linker. |
| `relocations` | List of records describing where in the code an external label address must be patched. |
| `binary` | Output byte array. |

---

## 2. Syntax: lines, labels, and comments

An assembly line may contain a label, a mnemonic, operands, and a comment. The order is flexible, but a few rules apply.

**Labels.** In the modern syntax, a label ends with a colon: `loop:`. In the historical syntax, with a comma: `loop,`. A label may appear on its own line or before an instruction. The assembler records the address of the next instruction or data item.

**Mnemonics.** Case does not matter: `LDM`, `ldm`, and `LdM` are the same. The assembler uppercases the mnemonic before looking it up in the `opcodes` table.

**Comments.** Three styles are supported: `//`, `;`, and `/`. Everything after the first comment character is discarded. The `_clean_line()` method processes them in order of length: `//` first, then `;`, then `/`.

**Blank lines.** They are ignored.

---

## 3. Directives

Directives are commands for the assembler, not for the processor. They do not become machine bytes.

### ORG

Sets the address at which the next instruction or data item will be placed.

| Syntax | Example |
|--------|---------|
| `ORG <expression>` | `ORG 0x000` |
| `= <expression>` (historical) | `= 0x000` |

### EQU

Assigns a value to a symbolic name. In the modern syntax, `=` plays the same role.

| Syntax | Example |
|--------|---------|
| `NAME EQU <expression>` | `BUFFER_SIZE EQU 64` |
| `NAME = <expression>` | `BUFFER_SIZE = 64` |

### DB

Places a sequence of bytes in memory. Each value is masked to 8 bits (`& 0xFF`).

| Syntax | Example |
|--------|---------|
| `DB <value> [, <value> ...]` | `DB 0x48, 0x65, 0x6C` |

### END

Tells the assembler that the source text is finished. Everything after `END` is ignored. Pass 2 also stops at `END`.

---

## 4. Expressions and the `*` symbol

Expressions may be used in operands and directives. The assembler supports `+`, `-`, `*`, and parentheses.

**The `*` symbol** means the current address (the value of `PC` at the moment of parsing). This lets you write position-independent code: `JUN *+4` means "jump 4 bytes forward".

**Labels in expressions.** The assembler substitutes the addresses of known labels. For example, `LDM BUFFER_SIZE - 1` computes the value of `BUFFER_SIZE` and subtracts one.

**External labels.** If a label is not found in the `labels` table, the assembler does not raise an error immediately. It adds the label to `externals`, leaves `0x00` in the code, and creates a `relocations` record. The linker later patches in the correct address.

**Safety.** The `_eval_expression()` method uses `eval()` with built-ins disabled (`{"__builtins__": None}`). This prevents arbitrary code execution if something unexpected ends up in an expression.

> [!NOTE]
> Because expressions are evaluated with `eval()`, only arithmetic operators and parentheses are supported. Function calls and attribute access are not available.

---

## 5. Operand formats

Each instruction has a format. The format determines how many bytes the instruction occupies and how the operand is encoded.

| Format | Description | Size | Example |
|--------|-------------|------|---------|
| `N` | No operands | 1 byte | `NOP`, `HLT`, `CLB` |
| `R` | One register | 1 byte | `ADD R3`, `XCH R0`, `INC R2` |
| `D` | 4-bit immediate value | 1 byte | `LDM 5`, `BBL 0` |
| `P` | Register pair | 1 byte (2 bytes for `FIM`) | `SRC P4`, `FIN P2`, `JIN P6` |
| `A12` | 12-bit address | 2 bytes | `JUN 0x123`, `JMS loop` |
| `COND` | Condition for `JCN` | 2 bytes | `JCN Z, loop` |
| `ISZ` | Register + page address | 2 bytes | `ISZ R2, loop` |

**Registers.** Both styles are supported: `R0`–`R15` and `0R`–`15R`. The `_get_reg()` method clamps the number to the range `0`–`15`.

**Pairs.** Both `P0`–`P7` and `0P`–`7P` are supported. The `_get_pair()` method converts the pair number to an even register number: `P0` → `0`, `P1` → `2`, `P7` → `14`.

**12-bit address.** The assembler splits the address into a high nibble and a low byte. The high nibble goes into the low 4 bits of the first byte (alongside the opcode); the low byte goes into the second byte.

**Conditions for `JCN`.** The condition string is uppercased, the `?` character is removed (for historical syntax), and the result is looked up in the `conditions` dictionary.

---

## 6. Full instruction table

Below are all instructions the assembler supports. The table is grouped by the high nibble of the opcode to make orientation easier.

### Group 0x0: control and logic

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `NOP` | `0x00` | `N` | No operation |
| `HLT` | `0x01` | `N` | Halt the processor |
| `OR4` | `0x04` | `N` | Logical OR with register `R4` |
| `OR5` | `0x05` | `N` | Logical OR with register `R5` |
| `AN6` | `0x06` | `N` | Logical AND with register `R6` |
| `AN7` | `0x07` | `N` | Logical AND with register `R7` |
| `DB0` | `0x08` | `N` | Select ROM bank 0 |
| `DB1` | `0x09` | `N` | Select ROM bank 1 |
| `SB0` | `0x0A` | `N` | Select register bank 0 |
| `SB1` | `0x0B` | `N` | Select register bank 1 |

### Group 0x1: conditional jump

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `JCN` | `0x10` | `COND` | Conditional jump |

### Group 0x2: pairs and ports

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `FIM` | `0x20` | `P` | Load a register pair with an 8-bit value (2 bytes) |
| `SRC` | `0x21` | `P` | Select a port for the next operation |

### Group 0x3: indirect jumps and ROM reads

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `FIN` | `0x30` | `P` | Indirect read from ROM at the address in the pair |
| `JIN` | `0x31` | `P` | Indirect jump to the address in the pair |

### Groups 0x4–0x5: jumps

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `JUN` | `0x40` | `A12` | Unconditional jump to a 12-bit address |
| `JMS` | `0x50` | `A12` | Call a subroutine (return address pushed onto the stack) |

### Group 0x6: increment

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `INC` | `0x60` | `R` | Increment a register by 1 |

### Group 0x7: loop

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `ISZ` | `0x70` | `ISZ` | Increment a register; if the result is not zero, jump to the address |

### Groups 0x8–0xB: arithmetic and transfer

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `ADD` | `0x80` | `R` | Add a register to the accumulator (with carry) |
| `SUB` | `0x90` | `R` | Subtract a register from the accumulator (via two's complement) |
| `LD` | `0xA0` | `R` | Load a register into the accumulator |
| `XCH` | `0xB0` | `R` | Exchange the accumulator and a register |

### Groups 0xC–0xD: return and load

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `BBL` | `0xC0` | `D` | Return from a subroutine, loading a 4-bit value into the accumulator |
| `LDM` | `0xD0` | `D` | Load a 4-bit value into the accumulator |

### Group 0xE: memory and ports

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `WRM` | `0xE0` | `N` | Write the accumulator to main RAM |
| `WMP` | `0xE1` | `N` | Write the accumulator to an output port |
| `WRR` | `0xE2` | `N` | Write to a ROM port (not used by the emulator) |
| `WPM` | `0xE3` | `N` | Write to program memory (not used by the emulator) |
| `WR0` | `0xE4` | `N` | Write to status register 0 |
| `WR1` | `0xE5` | `N` | Write to status register 1 |
| `WR2` | `0xE6` | `N` | Write to status register 2 |
| `WR3` | `0xE7` | `N` | Write to status register 3 |
| `SBM` | `0xE8` | `N` | Subtract memory from the accumulator |
| `RDM` | `0xE9` | `N` | Read from main RAM into the accumulator |
| `RDR` | `0xEA` | `N` | Read from a ROM port (not used by the emulator) |
| `ADM` | `0xEB` | `N` | Add memory to the accumulator |
| `RD0` | `0xEC` | `N` | Read status register 0 |
| `RD1` | `0xED` | `N` | Read status register 1 |
| `RD2` | `0xEE` | `N` | Read status register 2 |
| `RD3` | `0xEF` | `N` | Read status register 3 |

### Group 0xF: accumulator and carry operations

| Mnemonic | Opcode | Format | Description |
|----------|--------|--------|-------------|
| `CLB` | `0xF0` | `N` | Clear the accumulator and carry |
| `CLC` | `0xF1` | `N` | Clear the carry |
| `IAC` | `0xF2` | `N` | Increment the accumulator by 1 (ignoring carry) |
| `CMC` | `0xF3` | `N` | Invert the carry |
| `CMA` | `0xF4` | `N` | Invert the accumulator |
| `RAL` | `0xF5` | `N` | Rotate the accumulator left through carry |
| `RAR` | `0xF6` | `N` | Rotate the accumulator right through carry |
| `TCC` | `0xF7` | `N` | Load the carry into the accumulator, clear carry |
| `DAC` | `0xF8` | `N` | Decrement the accumulator by 1 (ignoring carry) |
| `TCS` | `0xF9` | `N` | Load `9` or `10` into the accumulator depending on carry |
| `STC` | `0xFA` | `N` | Set the carry |
| `DAA` | `0xFB` | `N` | Decimal adjust the accumulator |
| `KBP` | `0xFC` | `N` | Keyboard code conversion |
| `DCL` | `0xFD` | `N` | Select a RAM bank |

---

## 7. Conditions for JCN

The `JCN` instruction takes a 4-bit condition. In assembly, the condition is written as a mnemonic and converted to a code via the `conditions` dictionary.

| Mnemonic | Code | Meaning |
|----------|------|---------|
| `T` | `0x0` | Always true |
| `Z` | `0x4` | Accumulator is zero |
| `C` | `0x2` | Carry is set |
| `TN` | `0x8` | Always false (inverse of `T`) |
| `ZN` | `0xC` | Accumulator is not zero |
| `CN` | `0xA` | Carry is not set |
| `ZCN` | `0xE` | Accumulator is not zero AND carry is not set |
| `NC` | `0xA` | Synonym for `CN` |
| `NZ` | `0xC` | Synonym for `ZN` |
| `NT` | `0x9` | Synonym for `TN` |

**Historical syntax.** In old programs a condition may be written with a `?`, for example `JCN Z? loop`. The assembler removes the `?` before looking up the condition, so both forms work.

---

## 8. External labels and relocations

When the assembler encounters a label that is not in the `labels` table, it does not raise an error. Instead, it does three things:

1. Adds the label to the `externals` set.
2. Writes `0x00` into the code instead of the address (leaving a gap).
3. Appends a `(offset, label_name, format)` record to `relocations`.

**Offset** is the position in the output array `binary` where the address must be patched. For two-byte instructions (`A12`, `ISZ`, `COND`), the offset points at the second byte (the low byte of the address), because the high nibble is already written into the first byte.

**Format** tells the linker how to patch the code. For `A12`, the top 4 bits of the address are written into the low nibble of the preceding byte, and the low 8 bits into the current byte. For `ISZ` and `COND`, only the low byte is written, because those instructions stay within a page.

---

## 9. Linker: general architecture

The linker combines several object modules into a single ROM image. It runs in two passes, like the assembler.

**Pass 1 (`_pass1`)** places modules in memory and collects symbols. The linker starts at `base_address` (default `0x0000`) and allocates a contiguous region for each module. If a new module overlaps an existing one, the linker reports `Address overlap`. It then collects global symbols (those the module exports) and external references (those the module expects to find).

**Pass 2 (`_pass2`)** patches relocations. For each entry in `relocations`, the linker looks up the label in the global table. If found, it computes the absolute address and writes it into the code. If not found, it leaves the record for error reporting.

**Error checking.** After pass 2, the linker verifies that every external symbol is resolved. If any remain, it reports `Unresolved external symbols` with the list of names.

---

## 10. Module placement and overlap protection

The linker keeps a list of occupied ranges in `occupied_ranges`. Each range is a `(start, end)` pair. When a new module claims `[base, base + size)`, the linker checks that it does not intersect any existing range.

**Overlap check.** Two ranges do not overlap if `base + size <= start` or `base >= end`. If this condition fails for any existing range, the linker reports an error.

**Module order.** Modules are placed in the order they are passed to `link()`. If you need a particular module to land at a fixed address, use `ORG` inside it, or pass modules in the required order.

---

## 11. Symbol resolution

**Global symbols (`global_symbols`).** Each module may export labels. The linker adds them to the global table with an absolute address: `base + offset`. If two modules export a label with the same name, the linker reports `Duplicate public symbol`. This guards against accidental name conflicts.

**External symbols (`external_symbols`).** Each module may reference labels it does not define. The linker collects them into a dictionary where the key is the label name and the value is a list of `(absolute_offset, format)` pairs. Once all modules are placed, the linker verifies that each external label exists in the global table. If it does, it is resolved. If not, it stays in `external_symbols` and triggers an error.

---

## 12. Relocation patching: 4004 specifics

The `_patch_relocation()` method is where the linker accounts for the 4004 architecture. The instructions `JUN`, `JMS`, `JCN`, and `ISZ` occupy two bytes, but the address inside them is split in a nonstandard way.

**For format `A12`** (`JUN`, `JMS`), a 12-bit address is stored as follows: the high 4 bits go into the low nibble of the first byte (alongside the opcode); the low 8 bits go into the second byte. The linker does the following:

- Checks that the address does not exceed `0xFFF` (12 bits). If it does, it reports an error.
- Writes the high 4 bits into the low nibble of the preceding byte, preserving the high nibble (the opcode): `total_code[address - 1] = (total_code[address - 1] & 0xF0) | ((value >> 8) & 0x0F)`.
- Writes the low 8 bits into the current byte: `total_code[address] = value & 0xFF`.

**For formats `ISZ` and `COND`**, only the low byte of the address is used, because those instructions stay within the current page (256 bytes). The linker simply writes `value & 0xFF` into the current byte.

**Why.** The 4004 has no 16-bit registers to hold a full address in a single instruction. So the assembler emits a placeholder `(0x40, 0x00)` when it sees `JUN LABEL` and creates a relocation record. The linker later inserts the high 4 bits into the first byte without clobbering the opcode.

> [!NOTE]
> Relocation patching for `A12` preserves the opcode by masking the existing byte with `0xF0` before OR-ing in the high address nibble. This is why the linker must receive the correct format from the assembler — patching with the wrong format would corrupt the opcode.

---

## 13. Error handling

The linker is strict, like its historical ancestor LINK-80. Here are the main errors it can report.

| Error | Cause | How to fix |
|-------|-------|------------|
| `Address overlap` | Two modules claim the same memory region | Change module order or use `ORG` inside the module |
| `Duplicate public symbol` | Two modules export a label with the same name | Rename one of the labels |
| `Unresolved external symbols` | A module references a label that no module defines | Add the module that defines it, or fix the typo |
| `Address 0x... exceeds 12-bit limit` | The address is greater than `0xFFF` | Verify the program does not exceed 4 KB |
| `Unknown relocation format` | Internal error: relocation format not recognized | Report it; likely an assembler bug |

---

## 14. Map file

If `map_file=True` is passed when creating the linker, a map is printed after linking. It shows which module starts at which address and which symbols are exported.

**Output format.** A table with columns `Module`, `Symbol`, `Address`, and `Type`. For each public symbol, the module, name, absolute address, and type (`PUBLIC`) are shown. At the end, the total code size and start address are printed.

**Why you need it.** When a program behaves unexpectedly, the map helps you understand where control was transferred. If `PC` stops at `0x123`, open the map and find which module and which symbol live in that area.

---

## 15. Object module format

The `Assembler.assemble()` method returns a dictionary with four keys. This dictionary is what you pass to the linker.

| Key | Type | Contents |
|-----|------|----------|
| `code` | `bytearray` | Module machine bytes |
| `symbols` | `dict` | Exported labels: `{name: offset}` |
| `externals` | `list` | Names of external labels that must be resolved |
| `relocations` | `list` | Records `(offset, label_name, format)` |

**Offsets in `symbols`** are relative to the start of the module. The linker adds `base_address` to obtain the absolute address.

**Offsets in `relocations`** point to a position in `code` where the address must be patched. For two-byte instructions, this is the second byte (the low byte of the address).

---

## 16. Example: assembling and linking two modules

Consider two modules. `main.asm` calls a subroutine `print_char` defined in `io.asm`.

**main.asm:**

```asm
    ORG 0x000
start:
    LDM 0x41
    JMS print_char
    HLT
    END
```

**io.asm:**

```asm
print_char:
    XCH R2
    // ... output code ...
    BBL 0
    END
```

**What happens when `main.asm` is assembled.** The assembler sees `JMS print_char`, but `print_char` is not in the `labels` table. It adds `print_char` to `externals`, writes the placeholder `(0x50, 0x00)` into the code, and creates a relocation `(1, 'print_char', 'A12')`. The offset `1` points to the second byte of the `JMS` instruction.

**What happens when `io.asm` is assembled.** The assembler sees the `print_char` label and records its offset (in this case `0`). The `symbols` dictionary gets an entry `{'print_char': 0}`.

**What happens during linking.** The linker places `main.asm` at `0x000` and `io.asm` immediately after it at `0x004` (because `main.asm` occupies 4 bytes: `LDM` is 1, `JMS` is 2, `HLT` is 1). It then finds `print_char` in the global table: absolute address `0x004`. It patches the relocation: the high 4 bits (`0x0`) go into the low nibble of the first `JMS` byte (which stays `0x50`), and the low 8 bits (`0x04`) go into the second byte. Now `JMS` points at `0x004`.

---

## Conclusion

This reference covers the two main parts of the toolchain: the assembler and the linker. If you want to understand how to write code, return to the [Assembly Programming Guide](./03-assembly-programming-guide.md). If you want to explore how the CPU and instruction cycle work, open the [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md). And if you plan to work with the monitor and disks, the [System Monitor and Disk Operations guide](./08-system-monitor-and-disk-operations.md) will help.

This reference does not try to explain *why* — it answers *what* and *how*. For the philosophy behind the design — historical accuracy, dual syntaxes, modularity — read the guides. Keep this document at hand when you need to look up an opcode or a relocation rule.

---

[← Previous: BASIC Programming Guide](./04-basic-programming-guide.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Architecture and Emulation Reference →](./06-architecture-and-emulation-reference.md)
