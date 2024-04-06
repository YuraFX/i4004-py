<p align="center"><img src="https://github.com/YuraFX/i4004-py/blob/main/images/4004.png?raw=true" width="360"></p>
<h1 align="center">Intel 4004 emulator with very reduced functionality</h1>

## Introduction

In September this year, I decided to sign up for Future Code in order to gain knowledge of the Python language. Alas, after a very long period of time (until October), 
after filling out all the paperwork and so on, we were told that because of two, pardon the expression, morons who didn't get something and somewhere 
in time to fill out and pass, had to cancel this program in my technical school. I was not really upset, on the contrary, it even gave me a good impetus. 
to learn this programming language on my own at home, as I did with all previous languages :) My last projects were 
video games, so this time I decided to write something more serious, namely a CPU emulator, specifically [Intel 4004](https://en.wikipedia.org/wiki/Intel_4004) with very reduced functionality. 
Bottom line: I got it all (not at once), but it worked and I want to share this creation with you, dear comrades!

## About the emulator

The emulator has 256 bytes of memory into which program results are stored.

There is the Accumulator (acc), a processor register in which the results of arithmetic and logical instructions are stored, 
and the instruction counter (pc), a processor register that indicates which instruction to execute next.

An opcode, a piece of machine language called an instruction that defines the operation that to be performed. 
Here is a table of opcodes and their corresponding operation:

|Opcode |Operation                                                             |
|------|-----------------------------------------------------------------------|
|`0x0`|No Operation                                                            |
|`0x6`|Increment index register                                                |
|`0x7`|Increment index register skip if zero                                   |
|`0x8`|Add index register to accumulator with carry                            |
|`0x9`|Subtract index register to accumulator with borrow                      |
|`0xA`|Load index register to Accumulator                                      |
|`0xB`|Exchange index register and accumulator                                 |

### How is the program set up?

You should make the program directly in the code, specifically in [program.py](https://github.com/YuraFX/i4004-py/blob/main/src/program.py). 
Here is an example program where the number 5 is subtracted from the number 12 and then the number 2 is added:

```
cpu.memory[0x10] = 12
cpu.memory[0x11] = 5
cpu.memory[0x12] = 2

cpu.LD(0x10)
cpu.SUB(0x11)
cpu.ADD(0x12)
cpu.NOP()
```

## Additional material

[Intel 4004 datasheet](https://archive.org/download/intel-4004/intel-4004.pdf)

## About license

<img src="https://www.gnu.org/graphics/gplv3-with-text-136x68.png" width="160" align="right">

This program is [free software](https://www.gnu.org/philosophy/free-sw.en.html): you can redistribute it and/or modify it under the terms of the [GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.en.html) as published by the [Free Software Foundation](https://www.fsf.org/), either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a [copy](https://github.com/YuraFX/i4004-py/blob/main/LICENSE) of the GNU General Public License along with this program. If not, see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/licenses.en.html).
