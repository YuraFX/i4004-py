# Introduction and Overview

[← Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: User Guide →](./02-user-guide.md)

---

Welcome to the Intel 4004 emulator. This document is your starting point. It does not repeat the installation steps — those live in the project `README.md`. Instead, it explains what you are holding, why the Intel 4004 is worth your time, and how to get your first meaningful result in a few minutes.

The emulator is more than a processor simulator. It is an environment where the 4-bit world of 1971 meets modern development tools: an assembler, a linker, a BASIC compiler, and virtual peripherals. You can write code, debug it, watch registers change, and even boot a small monitor that reads and writes disk sectors.

---

## 1. What is the Intel 4004, and why emulate it?

The Intel 4004 is the first commercially available microprocessor. Intel introduced it in 1971 with roughly 2,300 transistors. A modern CPU can contain hundreds of millions, but the 4004 proved that a complete computing machine could fit on a single chip.

Intel originally built the 4004 for the Japanese Busicom calculator. The company later bought back the rights and released it as a general-purpose programmable processor — a building block that engineers could adapt to their own tasks through software.

Emulating the 4004 is not just nostalgia. It is a way to understand constraints. When you have sixteen 4-bit registers, a 12-bit program counter, and a three-level hardware stack, every instruction matters. You start to appreciate design decisions that look strange to a modern programmer: subtraction implemented as addition with a complement, or a byte transmitted as two 4-bit halves.

This emulator reproduces that architecture at the instruction level and adds something the original 4004 never had: a complete development toolchain and virtual devices that make the machine tangible.

---

## 2. Key features

Here is what you get out of the box. Use this list to decide which parts of the project matter most to you.

- **Full CPU emulation.** All 46 Intel 4004 instructions, including two-byte commands, page-based addressing, and the three-level circular stack.
- **Assembler with dual syntax.** Write in the modern style (`R0`–`R15`, `//` comments) or the historical style (`0R`–`15R`, `/` comments, `ORG` written as `=`). Programs from 1970s manuals assemble without modification.
- **Linker.** Split your program into modules, resolve external references, and patch 12-bit addresses into 8-bit instructions. If you know `PUBLIC` and `EXTRN`, you will feel at home.
- **BASIC compiler.** A teaching language: variables `A`–`H` map to registers `R0`–`R7`, and `PRINT`, `GOTO`, `IF`, `FOR/NEXT`, and `GOSUB` are supported. A gentle way to start without diving into assembly.
- **Virtual peripherals.** A Shugart SA 800-1 disk drive with IBM 3740 disk images, a Teletype Model 33 ASR, an AY-5-1013 UART, an Intel 4003 shift register, and an adaptation of the Atari TIA video controller.
- **Built-in monitor.** A one-click "operating system" with commands `D` (dump), `S` (edit), `X` (examine registers), `G` (go), `R` (read sector), and `W` (write sector). The monitor is written in 4004 assembly and runs inside the emulator.

---

## 3. Intel 4004 architecture in plain words

Before you run the first program, a few basic ideas will help. We will skip deep technical details — those belong in the architecture reference. Here is the minimum you need.

**Registers and the accumulator.** The 4004 has 16 registers, but each holds only 4 bits (one hexadecimal digit, `0` to `F`). Registers are organized in two banks of eight; `R8`–`R15` are shared between banks. The most important register is the accumulator (`ACC`): most arithmetic operations work on it.

**Program counter and stack.** The processor addresses up to 4,096 bytes of program memory using a 12-bit program counter (`PC`). The call stack is built into the chip and holds only three 12-bit return addresses. A fourth nested call overwrites the oldest return address — that is a limitation of the original hardware, not a bug in the emulator.

**Harvard architecture.** Program memory (ROM) and data memory (RAM) are two separate spaces. Code cannot execute from RAM, and data is not stored in ROM. Keep this in mind when you look at a memory map.

**Everything is 4 bits wide.** Anything larger than 4 bits travels in pieces. A byte is two 4-bit nibbles. A 12-bit address is three nibbles transmitted in different clock cycles. That is why assembler code so often works with register pairs: a pair is needed to combine two 4-bit values into one 8-bit value.

---

## 4. Your first run: "Hello, World!" for the Intel 4004

Now for the fun part. We assume you have cloned the project and followed the setup steps in `README.md`. If not, return to `README.md` first, then continue here.

### Step 1: Open the example

In the `examples/` folder (or wherever your project keeps sample code), find `hello.asm`. Open it in the code editor: click **Open** and select the file. You will see a short program that prints a greeting on the teletype.

### Step 2: Build

Click **Build**. The emulator checks the syntax, assembles the source into machine bytes, and runs the linker to combine your file with any modules it needs. The status bar reports a successful build and the size of the resulting ROM image.

### Step 3: Run

Switch to the **IO** tab in the right panel and make sure **Teletype Model 33 ASR** is selected in the display mode dropdown. Then click **Run**. Within a moment the greeting appears in the teletype window.

If you see the greeting, congratulations — you just ran a program for a processor designed more than fifty years ago. If nothing appears, check that the correct display mode is selected, then open the **General** tab: you can watch registers and the program counter change in real time. The program may have already finished (the `HLT` instruction stops the CPU), in which case press **Stop** and then **Run** again.

### What happened under the hood

While you were clicking buttons, the emulator did the following. The assembler translated mnemonics (`LDM`, `XCH`, `JMS`, and others) into bytes. The linker placed the code at specific addresses and resolved references to subroutines. The CPU began executing instructions one at a time: it loaded a character code into the accumulator, sent it to the teletype port, waited for the device to become ready, and repeated for each character. The virtual teletype assembled the incoming bits into bytes and printed the characters on "paper".

---

## 5. Where to go next: documentation map

This document is only the entrance. From here, several paths are open depending on what interests you.

**If you want to use the emulator as a tool** (load programs, work with disk images, debug code), open the [User Guide](./02-user-guide.md). It describes the interface tabs, keyboard shortcuts, the monitor, and disk image handling in detail.

**If you want to write assembly code**, your next document is the [Assembly Programming Guide](./03-assembly-programming-guide.md). It covers syntax, directives, expressions, modularity, and linking. The [Toolchain Reference](./05-toolchain-reference.md) will become your desk reference once you start writing code.

**If you want to write BASIC programs**, start with the [BASIC Programming Guide](./04-basic-programming-guide.md). It explains the teaching dialect, its limitations (and why they exist), and how BASIC source becomes assembly.

**If you are curious how the emulator works internally**, the [Architecture and Emulation Reference](./06-architecture-and-emulation-reference.md) explains the instruction cycle, the ALU, and emulation details. The [Peripherals and I/O Reference](./07-peripherals-and-io-reference.md) describes how the 4-bit CPU drives the disk, teletype, and video chips.

**If you want to understand the monitor and disk operations**, the [System Monitor and Disk Operations guide](./08-system-monitor-and-disk-operations.md) walks through monitor commands and how the monitor reads and writes sectors.

---

## Conclusion

The Intel 4004 is a reminder that great ideas often begin with hard constraints. This emulator tries to preserve the spirit of those constraints while making exploration safe and convenient. You can experiment, make mistakes, watch registers, and try again. No hardware will be harmed.

If something in the documentation is unclear or inaccurate, that is expected for a first release. Feedback is welcome. For now, head to the [User Guide](./02-user-guide.md) or jump straight into your first program.

---

[← Back to documentation index](https://github.com/YuraFX/i4004-py/blob/main/README.md) | [Next: User Guide →](./02-user-guide.md)
