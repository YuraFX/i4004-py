// =================================================================
// DISK_DRIVER.ASM — Shugart SA 800-1 (IBM 3740 / v3)
// Ports: reg4 = Commands, reg5 = Data
// Public: DISK_INIT, DISK_SEEK, DISK_READ_SECTOR,
//         DISK_WRITE_SECTOR, DISK_FORMAT_TRACK
// Note: do not touch R0–R7 (lower banks) unless stated;
//       we use R2,R3,R6,R7,R8,R9,R14,R15.
// =================================================================
ORG 0x000

// --- SELECT + HOME (common INIT) ---
DISK_INIT:
    FIM P0 0x40        // R0=4, R1=0
    SRC P0
    LDM 0x4            // SELECT
    WMP
    LDM 0x3            // OUTWARD
    WMP
DISK_HOME_LOOP:
    FIM P0 0x40
    SRC P0
    RDM
    RAR                 // bit0 = Track00
    JCN C DISK_HOME_DONE
    LDM 0x1            // STEP
    WMP
    JUN DISK_HOME_LOOP
DISK_HOME_DONE:
    BBL 0

// --- SEEK: R2 = track ---
DISK_SEEK:
    FIM P0 0x40
    SRC P0
    LDM 0x4            // SELECT
    WMP
    LDM 0x3            // OUTWARD (to start)
    WMP
SEEK_HOME:
    FIM P0 0x40
    SRC P0
    RDM
    RAR
    JCN C SEEK_INWARD
    LDM 0x1
    WMP
    JUN SEEK_HOME
SEEK_INWARD:
    LDM 0x2            // INWARD
    WMP
SEEK_LOOP:
    LD R2
    JCN Z SEEK_DONE
    LDM 0x1
    WMP
    LD R2
    DAC
    XCH R2
    JUN SEEK_LOOP
SEEK_DONE:
    BBL 0

// --- READ_SECTOR: R2=trk, R3=sec, R6=destReg, R7=destChar ---
// 128 bytes, 8*16 loop, each byte = 2 nibbles
DISK_READ_SECTOR:
    JMS DISK_SEEK
    // Set sector
    FIM P0 0x50        // R0=5, R1=0 (data)
    SRC P0
    LD R3
    WMP
    // READ command
    FIM P0 0x40
    SRC P0
    LDM 0x8
    WMP
WAIT_R:
    FIM P0 0x40
    SRC P0
    RDM
    RAR
    RAR                 // bit1 = Ready
    JCN NC WAIT_R
    // 8 × 16 = 128 iterations (1 byte per iteration)
    LDM 8
    XCH R9             // outer
RD_OUT:
    LDM 0
    XCH R8             // inner (16)
RD_IN:
    // nibble low
    FIM P0 0x50
    SRC P0
    RDM
    XCH R10
    // nibble high
    SRC P0
    RDM
    XCH R11
    // Write low to (R6,R7)
    FIM P3 0x00
    SRC P3
    LD R10
    WRM
    JMS RD_INC
    // Write high to (R6,R7) — already incremented
    SRC P3
    LD R11
    WRM
    JMS RD_INC
    ISZ R8 RD_IN
    NOP
    ISZ R9 RD_OUT
    NOP
    BBL 0

// Increment pair (R6,R7) with carry across the 16 boundary
RD_INC:
    LD R7
    IAC
    XCH R7
    JCN C RD_INC_RET
    LD R6
    IAC
    XCH R6
RD_INC_RET:
    BBL 0

// --- WRITE_SECTOR: same parameters ---
DISK_WRITE_SECTOR:
    JMS DISK_SEEK
    FIM P0 0x40
    SRC P0
    LDM 0x6            // WRITE GATE ON
    WMP
    FIM P0 0x50
    SRC P0
    LD R3
    WMP
    FIM P0 0x40
    SRC P0
    LDM 0x9            // WRITE
    WMP
    LDM 8
    XCH R9
WR_OUT:
    LDM 0
    XCH R8
WR_IN:
    // Read low nibble from (R6,R7)
    FIM P3 0x00
    SRC P3
    RDM
    XCH R10
    JMS RD_INC
    // Read high nibble from the next cell
    SRC P3
    RDM
    XCH R11
    JMS RD_INC
    // Send to UART (low, high)
    FIM P0 0x50
    SRC P0
    LD R10
    WMP
    LD R11
    WMP
    ISZ R8 WR_IN
    NOP
    ISZ R9 WR_OUT
    NOP
    FIM P0 0x40
    SRC P0
    LDM 0x7            // WRITE GATE OFF
    WMP
    BBL 0

// --- FORMAT_TRACK: R2 = track, fill 26 sectors with zeros ---
DISK_FORMAT_TRACK:
    JMS DISK_SEEK
    LDM 0
    XCH R3             // sector = 0
FMT_SECT:
    // SRC P3 points to the sector buffer (empty)
    FIM P3 0x00
    SRC P3
    LDM 0              // counter for 16 iterations
    XCH R8
FMT_WR:
    LDM 0
    WMP                 // WRM writes nibble 0
    ISZ R8 FMT_WR
    NOP
    // Next sector
    LD R3
    IAC
    XCH R3
    SUB R4              // R4=26 (outer limit)
    JCN NZ FMT_SECT
    BBL 0

END