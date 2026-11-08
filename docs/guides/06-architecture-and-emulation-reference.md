# Architecture and Emulation Reference

[← Previous: Toolchain Reference](./05-toolchain-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Peripherals and I/O Reference →](./07-peripherals-and-io-reference.md)

---

This document is for readers who want to understand how the emulator reproduces the behavior of the Intel 4004. It does not teach you to write programs — for that, see the [Assembly Programming Guide](./03-assembly-programming-guide.md) and the [BASIC Programming Guide](./04-basic-programming-guide.md) — and it does not describe peripherals (those are in the [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md)). Here we focus on the core: CPU state, the instruction cycle, the ALU, memory, and the bus.

The document is organized as a reference: sections are grouped by topic, each with an explanation and implementation details. If you want to look up how a specific instruction is emulated or how the stack works, open the relevant section.

---

## 1. Emulation philosophy: instruction-level accuracy

The emulator reproduces 4004 behavior at the **instruction level**, not at the cycle level. This means each instruction executes fully within one `step()` call, and intermediate bus states inside an instruction are not modeled. This choice is deliberate: it keeps the code readable and fast while preserving functional accuracy.

What this means in practice. A real 4004 executes `ADD` in 8 clock cycles and `JUN` in 16, but the emulator does not distinguish these delays: both instructions complete in one step. For programs that do not depend on precise timing (which is most of them), this has no effect. For the few cases where timing matters (for example, bit-banging on the teletype), the emulator uses other synchronization mechanisms — covered in section 11.

**What is emulated accurately.** Instruction logic, register, flag, stack, and memory behavior all follow Intel's documentation. If a program on a real 4004 produces result X, the emulator produces X as well.

**What is simplified.** Internal delays, bus states between cycles, and physical signal timings. These details do not affect program logic, but it is worth knowing them if you compare the emulator's behavior with a real chip.

---

## 2. CPU state

The `CPU` class stores the entire processor state in a handful of fields. Understanding these fields is the key to understanding how the emulator executes instructions.

### Accumulator and carry

| Field | Size | Purpose |
|-------|------|---------|
| `acc` | 4 bits | Accumulator. The main register for arithmetic and logic. |
| `carry` | 1 bit | Carry flag. Set on overflow; used in conditional jumps. |

The accumulator is the workhorse of the 4004. Most instructions either load a value into it, modify it, or use it as a data source. The carry flag is the only flag in the processor; it is set on addition (if the result exceeds `0xF`) and on subtraction (if no borrow occurred).

### Program counter

| Field | Size | Purpose |
|-------|------|---------|
| `pc` | 12 bits | Program Counter. Address of the next instruction in ROM. |

Twelve bits is not arbitrary. The 4004 could address only 4,096 bytes of program memory (`2^12 = 4096`). The program counter increments after each instruction: by 1 for one-byte instructions, by 2 for two-byte instructions. Jump instructions (`JUN`, `JMS`, `JCN`, `ISZ`) write a new value into it.

### Register banks

The 4004 has 16 registers, but they are organized differently from modern CPUs. There are two banks of 8 registers, and `R8`–`R15` are shared between them.

| Field | Purpose |
|-------|---------|
| `index_banks` | A list of two arrays of 16 elements. `index_banks[0]` is bank 0, `index_banks[1]` is bank 1. |
| `selected_register_bank` | Active bank number (0 or 1). Switched by `SB0` and `SB1`. |

**How it works.** When a program accesses register `R3`, the emulator reads `index_banks[selected_register_bank][3]`. If bank 0 is active, this is `R3` of bank 0; if bank 1 is active, it is `R3` of bank 1. But when a program accesses `R10`, the emulator reads `index_banks[0][10]` or `index_banks[1][10]` depending on the bank — and it is the same value, because `R8`–`R15` are shared.

**Why banks exist.** On a real 4004, banks allowed fast context switching: a subroutine could use bank 1 without touching the main program's registers in bank 0. It was a primitive but effective way to save memory.

### Stack

The 4004 stack is one of the most unusual parts of the architecture. It is built into the chip and holds only three 12-bit addresses.

| Field | Purpose |
|-------|---------|
| `stack` | Array of three 12-bit addresses. |
| `sp` | Stack pointer (0 to 2). |

**How it works.** On a subroutine call (`JMS`), the return address is written to `stack[sp]`, then `sp` increments modulo 3: `sp = (sp + 1) % 3`. On return (`BBL`), `sp` decrements modulo 3, and the address is read from `stack[sp]`.

**What this means.** The stack is circular. If you call four subroutines in a row, the fourth call overwrites the return address of the first. This is not an emulator bug — it is a limitation of the real chip. Deep `JMS` nesting does not work, and programs for the 4004 were designed with this constraint in mind.

### Other fields

| Field | Purpose |
|-------|---------|
| `selected_rom_bank` | Active ROM bank (0 or 1). Switched by `DB0` and `DB1`. |
| `ram_control` | Control bits for RAM bank selection. Set by `DCL`. |
| `halted` | Halt flag. Set by `HLT`. |

---

## 3. The instruction cycle

The `step()` method is the heart of the emulator. It implements the classic **fetch-decode-execute** cycle.

### Fetch

```python
opcode = self.rom.read(self.pc)
```

The emulator reads a byte from ROM at address `pc`. On a real 4004 this happened in two phases (two nibbles), but the emulator reads the byte whole — a simplification that does not affect logic.

### Decode

```python
opr = opcode >> 4       # high 4 bits — opcode group
opa = opcode & 0xF      # low 4 bits — operand
```

The byte is split into two parts: the high nibble `opr` determines the instruction group, and the low nibble `opa` selects the specific instruction or operand. For example, `0xD5` is `LDM 5`: `opr = 0xD` (the `LDM` group), `opa = 5` (the value).

### Execute

A large `if/elif` block calls the appropriate method depending on `opr`. Each instruction group has its own handler:

- `opr == 0x0` — control, logic, bank switching.
- `opr == 0x1` — `JCN` (conditional jump).
- `opr == 0x2` — `FIM` and `SRC`.
- `opr == 0x3` — `FIN` and `JIN`.
- `opr == 0x4` — `JUN`.
- `opr == 0x5` — `JMS`.
- `opr == 0x6` — `INC`.
- `opr == 0x7` — `ISZ`.
- `opr == 0x8` — `ADD`.
- `opr == 0x9` — `SUB`.
- `opr == 0xA` — `LD`.
- `opr == 0xB` — `XCH`.
- `opr == 0xC` — `BBL`.
- `opr == 0xD` — `LDM`.
- `opr == 0xE` — memory and ports.
- `opr == 0xF` — accumulator and carry operations.

**Updating PC.** For one-byte instructions, `pc` increments by 1. For two-byte instructions (`JUN`, `JMS`, `JCN`, `ISZ`, `FIM`), it increments by 2 (or by 3 for `ISZ` when the skip fires). Jump methods write the new value into `pc` directly.

---

## 4. Two-byte instructions

Some instructions occupy two bytes because their operand does not fit in 4 bits. These are `JUN`, `JMS`, `JCN`, `ISZ`, and `FIM`.

### Reading the second byte

```python
def _fetch_next_byte(self):
    if self.rom:
        return self.rom.read(self.pc + 1)
    return 0
```

The `_fetch_next_byte()` method reads the byte at `pc + 1`. This works because at the moment of the call, `pc` still points to the first byte of the instruction. After the method executes, `pc` is updated.

### Format A12 (JUN, JMS)

These instructions use a 12-bit address split into two parts:

- **First byte:** `0x40` (or `0x50` for `JMS`) + the high 4 bits of the address.
- **Second byte:** the low 8 bits of the address.

For example, `JUN 0xABC` is encoded as `0x4A, 0xBC`: `0x40 | 0x0A = 0x4A`, then `0xBC`.

### Format ISZ

`ISZ` combines a register and a page address:

- **First byte:** `0x70` + the register number.
- **Second byte:** the low byte of the page address.

### Format COND (JCN)

`JCN` combines a condition and a page address:

- **First byte:** `0x10` + the 4-bit condition code.
- **Second byte:** the low byte of the page address.

### Format P (FIM)

`FIM` loads a register pair with an 8-bit value:

- **First byte:** `0x20` + the pair number (an even register).
- **Second byte:** the 8-bit value, split into two nibbles and written into the pair.

---

## 5. Page-based addressing

The `JCN` and `ISZ` instructions cannot specify a full 12-bit address: their second byte holds only 8 bits. As a result, they operate **within the current page** — a 256-byte region defined by the high 4 bits of `pc`.

### How the full address is computed

```python
def _get_full_address(self, page_byte):
    ph = (self.pc & 0xF00) + (0x100 if (self.pc & 0xFF) == 0xFF else 0)
    return ph | (page_byte & 0xFF)
```

The `_get_full_address()` method takes the high 4 bits of `pc` (the page number), adds `0x100` if `pc` points at the last byte of a page (a boundary crossing), and combines the result with the low byte of the address.

### Why this exists

On a real 4004, page-based addressing was a compromise: it saved bits in the instruction, but required programmers to ensure jumps did not cross page boundaries. If a program wanted to jump to another page, it used `JUN` (full 12-bit address) or `JMS`.

### What this means in practice

If you write a program and use `JCN` or `ISZ` to jump to a label, make sure the label is in the same page as the instruction. Otherwise the jump will be wrong. The linker does not check this automatically — it is the programmer's responsibility.

> [!WARNING]
> `JCN` and `ISZ` silently produce incorrect jumps when a label is in a different page. The assembler and linker do not detect this. Always verify page boundaries when using page-based jumps.

---

## 6. Arithmetic Logic Unit (ALU)

The 4004 has no hardware subtract instruction. Subtraction is implemented as addition with two's complement. This is a classic computer architecture technique, and the emulator reproduces it exactly.

### Addition

```python
def _add(self, value, ignore_carry=False):
    result = self.acc + value + (0 if ignore_carry else self.carry)
    self.acc = result & 0xF
    self.carry = 1 if result > 0xF else 0
```

The `_add()` method adds the accumulator, the value, and the carry flag. The result is masked to 4 bits (`& 0xF`), and the carry flag is set if the result exceeds `0xF`.

**The `ignore_carry` parameter.** Some instructions (`IAC`, `DAC`) ignore the current carry flag. For them, `ignore_carry=True`.

### Subtraction

```python
def _sub(self, value, ignore_carry=False):
    self.carry = 1 if ignore_carry else ((~self.carry) & 0x1)
    self._add((~value) & 0xF)
```

The `_sub()` method implements subtraction via two's complement. It first inverts the carry flag (because on the 4004 subtraction uses the inverted carry as "borrow"), then adds the accumulator to the inverted value.

**Example.** To subtract `5` from `8`:

1. `~5 & 0xF = 0xA` (the 4-bit complement of `5`).
2. `8 + 0xA + 1 = 0x13` (with carry).
3. `0x13 & 0xF = 3` (result).
4. `carry = 1` (because `0x13 > 0xF`).

The result `3` is correct (`8 - 5 = 3`). The carry flag is set, meaning "no borrow occurred".

### Flags

There is only one flag on the 4004 — carry. It is used in conditional jumps (`JCN C`, `JCN NC`) and in arithmetic. Logic operations (`OR4`, `AN6`) do not affect the carry flag.

---

## 7. Special instructions

Some 4004 instructions behave unusually. Here is how they are emulated.

### ISZ — Increment and Skip if Zero

```python
def ISZ(self, reg, page_byte):
    val = (self._read_reg(reg) + 1) & 0xF
    self._write_reg(reg, val)
    if val == 0:
        self.pc += 3
    else:
        self.pc = self._get_full_address(page_byte)
```

`ISZ` increments a register by 1. If the result is zero, the instruction skips the next command (`pc += 3`, because `ISZ` occupies 2 bytes and one more byte is skipped). If the result is not zero, control jumps to the page address.

**Why it exists.** `ISZ` is the classic loop instruction. It combines increment, test, and jump in one command, saving both memory and cycles.

### JIN — Jump Indirect

```python
def JIN(self, reg_pair):
    addr = (self._read_reg(reg_pair) << 4) | self._read_reg(reg_pair + 1)
    self.pc = addr
```

`JIN` takes a register pair (for example, `R0:R1`), combines the values into an 8-bit address, and jumps there. This is an indirect jump: the address lives in registers, not in the instruction.

**Why it exists.** `JIN` was used to return from complex subroutines where the return address was computed dynamically. In the monitor, `JIN` drives the `G` (Go) command: the address is loaded into pair `P0`, and `JIN P0` is executed.

### FIN — Fetch Indirect

```python
def FIN(self, reg_pair):
    addr = (self._read_reg(reg_pair) << 4) | self._read_reg(reg_pair + 1)
    data = self.rom.read(addr) if self.rom else 0
    self._write_reg(0, (data >> 4) & 0xF)
    self._write_reg(1, data & 0xF)
```

`FIN` reads a byte from ROM at the address stored in a register pair and writes it to `R0` and `R1` (high and low nibbles). This is an indirect read: the address comes from registers, not the instruction.

**Why it exists.** `FIN` was used to read tables and constants stored in ROM. The emulator supports it, but programs rarely use it.

### FIM — Fetch Immediate

```python
def FIM(self, reg_pair, data):
    self._write_reg(reg_pair, (data >> 4) & 0xF)
    self._write_reg(reg_pair + 1, data & 0xF)
    self.pc += 2
```

`FIM` loads an 8-bit value into a register pair. The high nibble goes into the first register of the pair, the low nibble into the second. It is the only way to load an 8-bit value into registers with a single instruction.

### SRC — Send Register Control

```python
def SRC(self, reg_pair):
    high = self._read_reg(reg_pair)
    low = self._read_reg(reg_pair + 1)
    self.pins.set_ram_address(high, low)
    
    if self.ram:
        bank = self.ram.banks[0]
        bank['selected_register'] = high & 0xF
        bank['selected_character'] = low & 0xF
```

`SRC` is the "key" to external devices. It tells the next `WRM` or `RDM` which register and which cell to work with. Without `SRC`, those instructions do not know where to read or write.

**How it works.** `SRC` takes a register pair, extracts the register number (`high`) and the cell number (`low`), and stores them in the selected RAM bank. The next `WRM` or `RDM` uses those values.

---

## 8. Bus and pins

The CPU does not work with memory directly. It talks to the outside world through a **bus** — a set of signal lines that carry addresses, data, and control signals. In the emulator, the bus is represented by the `CPUPins` class.

### Data lines D0–D3

```python
D0 = "D0"
D1 = "D1"
D2 = "D2"
D3 = "D3"
```

Four data lines form a 4-bit **multiplexed bus**. Everything travels over it: addresses, data, and instructions. At any moment, only one chip may "speak" (drive the bits); the others must stay silent.

**Multiplexing.** On a real 4004, the same bus carried different types of information in different clock cycles. This kept the chip at 16 pins instead of 30+. The emulator simplifies multiplexing: `set_pins_data()` and `get_pins_data()` just write and read values.

### SYNC signal

```python
SYNC = "SYNC"
```

`SYNC` is the main clock signal. The 4004 generates it every 8 cycles (one machine cycle). It tells all other chips: "Attention, a new instruction cycle begins!"

In the emulator, `SYNC` is used in `ram.py` and `rom.py` for synchronization: when `SYNC` is set, the state resets.

### CM-RAM and CM-ROM lines

```python
CM_RAM0 = "CM_RAM0"
CM_RAM1 = "CM_RAM1"
CM_RAM2 = "CM_RAM2"
CM_RAM3 = "CM_RAM3"
CM_ROM0 = "CM_ROM0"
CM_ROM1 = "CM_ROM1"
```

These lines select a memory bank. `CM_RAM0`–`CM_RAM3` select a RAM bank (up to 8 banks with external logic), and `CM_ROM0`–`CM_ROM1` select a ROM bank.

**Initial state.** After reset, `CM_RAM0 = 1` (bank 0 selected) and `CM_ROM0 = 1` (ROM bank 0 selected). This matches Intel's documentation.

### Pin methods

The `CPUPins` class provides several methods:

| Method | Purpose |
|--------|---------|
| `set_pin(pin, value)` | Set one line to 1 or 0. |
| `get_pin(pin)` | Read one line. |
| `set_pins_data(pins_list, value)` | Write a number to a group of lines. |
| `get_pins_data(pins_list)` | Read a number from a group of lines. |
| `write_ram(value)` | Wrapper for `WRM`: write a value to D0–D3. |
| `read_ram()` | Wrapper for `RDM`: read a value from D0–D3. |
| `set_ram_address(high, low)` | Wrapper for `SRC`: set the RAM address. |
| `set_rom_bank(bank)` | Wrapper for `DB0`/`DB1`: switch the ROM bank. |

These wrappers are syntactic sugar. They keep CPU code clean: instead of `pins.set_pins_data([D0, D1, D2, D3], value)`, you write `pins.write_ram(value)`.

---

## 9. Memory: ROM and RAM

The 4004 uses a **Harvard architecture**: program memory (ROM) and data memory (RAM) are two physically separate spaces that do not overlap.

### ROM (program memory)

```python
class ROM:
    def __init__(self, pins):
        self.pins = pins
        self.banks = [bytearray(0), bytearray(0)]
        self.selected_bank = 0
```

ROM holds instructions. In the emulator there are two banks, each a `bytearray`. The bank is selected by `CM_ROM1` (switched by `DB0`/`DB1`).

**Reading instructions.** When the CPU executes `step()`, it calls `rom.read(pc)`. The method checks the address and returns a byte from the selected bank. If the address is out of range, it returns `0` (a signal that the program has left ROM).

**Loading a dump.** The `load_dump()` method loads a ready-made ROM image (for example, the output of the linker). It is used in `System.__init__()`.

### RAM (data memory)

```python
class RAM:
    def __init__(self, pins, ram_dump=None, output_handler=None):
        self.banks = self._get_empty_ram()
```

RAM holds data. In the emulator there are 8 banks, each containing 16 registers, each register containing 16 main cells and 4 status registers. Plus 8 output ports per bank.

**Bank structure.** Each bank is a dictionary:

| Key | Contents |
|-----|----------|
| `registers` | List of 16 registers. Each register is a dict with `main` (16 cells) and `status` (4 cells). |
| `outputs` | List of 8 output ports. |
| `selected_register` | Selected register number (set via `SRC`). |
| `selected_character` | Selected cell number (set via `SRC`). |

**Bank selection.** The `_selected_bank()` method reads the state of `CM_RAM0`–`CM_RAM3` and determines which bank is active. If the lines are not set, it returns `None`.

**Instruction handling.** The `_execute()` method is called from `tick()` and performs the operation on the selected bank. For `RDM`, for example, it reads a value from memory and places it on lines D0–D3. For `WMP`, it writes a value to an output port and invokes `output_handler` if one is set.

### Harvard architecture: what it means

In a Harvard architecture, code and data are separated. You cannot execute an instruction from RAM or write data to ROM. This matters when you look at a memory map: address `0x100` in ROM and address `0x100` in RAM are different cells.

**Why.** In 1971, a Harvard architecture was simpler and cheaper: different memory types could be used for code and data, each optimized for its task. Modern CPUs more often use a von Neumann architecture (shared memory), but the 4004 remains in history as a Harvard example.

---

## 10. Memory clock cycle

Memory in the emulator does more than store values — it participates in the CPU's clock cycle. The `tick()` method in `RAM` and `ROM` emulates the 8 phases of a machine cycle.

### RAM phases

`RAM.tick()` walks through states:

- `A1`, `A2`, `A3` — bank selection.
- `M1`, `M2` — command acquisition.
- `X1`, `X2` — execution and address.

At phase `M2` memory records the operation code (`opa`), and at phase `X2` it executes it. This reproduces real chip behavior where command and data travel in different clock cycles.

### ROM phases

`ROM.tick()` works similarly:

- `A1`, `A2`, `A3` — address formation.
- `M1`, `M2` — instruction delivery.

At phase `A3` ROM checks address validity and selects the bank. At `M1` and `M2` it places the high and low nibbles of the instruction on the bus.

### Why this matters

Without phase-based emulation it would be impossible to run complex programs (such as the monitor) that depend on exactly when `SRC` places data on the bus. Phase-based cycles make the emulator more accurate, at the cost of more complex code.

---

## 11. Synchronization and asynchronous devices

On a real 4004, the CPU and peripherals run at different frequencies. The 4004 runs at 740 kHz, the UART at 110 baud, and the teletype at 10 characters per second. In the emulator, all of them run in a single Python thread, so artificial synchronization is needed.

### The instruction() method

```python
def instruction(self):
    if self.is_finished():
        return
    self.cpu.step()
    for _ in range(10):
        self.uart.tick()
    self.instruction_cycles += 1
```

`instruction()` executes one CPU step, then "spins" the UART 10 times. This compensates for the frequency gap: while the CPU executes one instruction, the UART generates several bits.

**Why 10.** It is an empirical value. It was chosen so the UART processes data without loss. If you change CPU or UART frequency, you may need to tune this number.

### What this means in practice

If you write a program that heavily uses the UART (for example, printing text on the teletype), the emulator runs slower because each CPU step is accompanied by 10 UART ticks. If a program does not use the UART, these ticks still execute — a small price for universality.

---

## 12. System lifecycle

The `System` class manages the emulator's lifecycle: initialization, execution, and shutdown.

### Initialization

```python
def __init__(self, rom_dump, ram_dump=None, ram_output_handler=None):
    self.pins = CPUPins()
    self.rom = ROM(self.pins)
    self.ram = RAM(self.pins, ram_dump, ram_output_handler)
    self.cpu = CPU(self.pins)
    self.cpu.rom = self.rom
    self.cpu.ram = self.ram
    # ... peripheral wiring ...
    self.rom.load_dump(rom_dump)
```

When a `System` is created, all components are created: pins, ROM, RAM, CPU, and peripherals. They are then "wired" together via references. This mirrors how an engineer inserts chips into sockets and connects them with wires.

### Completion check

```python
def is_finished(self):
    return (
        self.terminated or
        not self.rom.is_address_valid(self.cpu.pc) or
        self.cpu.halted
    )
```

The system is considered finished in three cases:

1. **Forced stop.** Someone called `terminate()` (for example, the user pressed **Stop**).
2. **PC left ROM.** `pc` points to an address that does not exist in ROM. This can happen if the program runs away or if the ROM image is smaller than needed.
3. **HLT instruction.** The CPU executed `HLT` and stopped.

### Stop

```python
def terminate(self):
    self.terminated = True
```

`terminate()` sets the `terminated` flag. After that, `instruction()` stops executing steps. It is analogous to a RESET signal or the **Stop** button.

---

## 13. Accuracy and simplifications

Here is a summary of what is emulated accurately and what is simplified. This will help you understand where the emulator's behavior may differ from a real chip.

### Emulated accurately

- **Logic of all 46 instructions.** Opcodes, operand formats, register, flag, and stack behavior all match Intel's documentation.
- **Two-byte instructions.** `JUN`, `JMS`, `JCN`, `ISZ`, and `FIM` occupy the correct number of bytes and update `pc` correctly.
- **Page-based addressing.** `JCN` and `ISZ` operate within the current page, as on a real 4004.
- **Three-level circular stack.** `JMS` and `BBL` work with a three-cell array, and `sp` wraps around.
- **Register banks.** `SB0`/`SB1` switch banks, and `R8`–`R15` are shared.
- **Harvard architecture.** ROM and RAM are separate, and code cannot execute from RAM.
- **Two's complement arithmetic.** `SUB` is implemented as addition with the inverted value.

### Simplified

- **Timing.** Instructions complete in one step instead of 8 or 16 cycles. This does not affect logic, but it does affect emulation speed.
- **Bus states between cycles.** On a real 4004, the bus passes through several states within one instruction. The emulator does not model these states (except `SYNC` in `RAM`/`ROM`).
- **Multiplexing.** On a real 4004, one bus carries addresses and data in different cycles. In the emulator, `set_pins_data()` and `get_pins_data()` simply write and read values.
- **Physical signal levels.** There are no voltages, currents, or high-impedance states in the emulator. Everything is represented as 0 and 1.

### What this means for you

If you write a program that depends on precise timing (for example, bit-banging on the teletype), the emulator may behave differently from a real chip. But for most programs (arithmetic, loops, memory access), the emulator produces the correct result.

---

## 14. Extending the emulator

If you want to add a new instruction or change the behavior of an existing one, here is what to know.

### Adding an instruction

1. **Add the opcode in `assembler.py`.** In the `opcodes` dictionary, add an entry `'MNEMONIC': (base_byte, format)`.
2. **Add a handler in `cpu.py`.** In the `step()` method, add a branch for the new opcode.
3. **Implement the method.** For example, `def MY_INSTR(self, operand): ...`.
4. **Update the documentation.** Add the instruction to the [Toolchain Reference](./05-toolchain-reference.md) and describe it in the [Assembly Programming Guide](./03-assembly-programming-guide.md).

### Changing behavior

If you want to change how an existing instruction behaves (for example, make `ISZ` more accurate), find the corresponding method in `cpu.py` and modify it. Make sure the changes do not break existing programs: run tests (if any) or verify manually.

### Adding a peripheral

If you want to connect a new device (for example, a printer), create a class that will handle writes to a port. Wire it in `System.__init__()` and in `cpu.py` (in the `WMP` method). See the [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md) for details.

---

## Conclusion

This reference covers the emulator's core: CPU state, instruction cycle, ALU, bus, and memory. If you want to understand how peripherals work (UART, disk drive, video), move on to the [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md). If you are interested in the monitor and disk operations, see the [System Monitor and Disk Operations guide](./08-system-monitor-and-disk-operations.md).

The emulator tries to be accurate where it matters for program logic and simple where accuracy is not required. Understanding that balance helps both when writing programs and when reading the emulator's source code.

---

[← Previous: Toolchain Reference](./05-toolchain-reference.md) | [Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: Peripherals and I/O Reference →](./07-peripherals-and-io-reference.md)
