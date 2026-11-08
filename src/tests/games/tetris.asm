// =================================================================
// TETRIS FOR INTEL 4004 (Prototype)
// =================================================================
ORG 0x000

    // --- 0. Initialization ---
    LDM 0
    XCH R12        // R12 = Y of the landed block
    XCH R13        // R13 = X of the landed block

    // =============================================================
    // 1. Well (Walls and Bottom)
    // =============================================================
    LDM 7          // Initial Y for walls (top)
    XCH R7
WALL_LOOP:
    // Left wall (X = 5)
    LDM 5
    XCH R6
    JMS DRAW_PIXEL
    // Right wall (X = 10)
    LDM 10
    XCH R6
    JMS DRAW_PIXEL
    
    // Increment Y and check whether we reached the bottom (Y=15)
    LD R7
    IAC
    XCH R7
    LDM 15
    XCH R8
    LD R7
    SUB R8
    JCN NZ WALL_LOOP

    // Draw the bottom at Y=15 (line from X=5 to X=10)
    LDM 5
    XCH R6
FLOOR_LOOP:
    LDM 15
    XCH R7
    JMS DRAW_PIXEL
    LD R6
    IAC
    XCH R6
    LDM 11         // Exit condition: reached X=11 (meaning X=10 has been drawn)
    XCH R8
    LD R6
    SUB R8
    JCN NZ FLOOR_LOOP

    // =============================================================
    // 2. Spawn
    // =============================================================
SPAWN_NEW:
    LDM 7          // X = 7 (center of the field)
    XCH R0
    LDM 8          // Y = 8 (top of the field)
    XCH R1
    JMS DRAW_BLOCK

    // =============================================================
    // 3. Falling
    // =============================================================
FALL_LOOP:
    LDM 10
    XCH R10
DELAY_OUTER:
    LDM 15
    XCH R11
DELAY_INNER:
    JMS CHECK_INPUT
    ISZ R11 DELAY_INNER
    NOP
    ISZ R10 DELAY_OUTER
    NOP

    // --- Bottom check ---
    // If Y + 1 == 15, lock the block
    LD R1
    IAC
    XCH R2         // R2 = Y + 1
    LDM 15
    XCH R3         // R3 = 15
    LD R2
    SUB R3
    JCN Z LAND_BLOCK

    // --- Collision check with the landed block ---
    LD R12
    JCN Z NO_COLLISION // If R12 == 0 (empty), keep falling
    
    // First check X (R0 == R13)
    LD R0
    XCH R2
    LD R13
    SUB R2
    JCN NZ NO_COLLISION // If X does not match, KEEP FALLING

    // If X matches, check Y (Y+1 == R12)
    LD R1
    IAC
    XCH R2
    LD R12
    SUB R2
    JCN Z LAND_BLOCK // If Y matches, lock the block

NO_COLLISION:
    JMS CLEAR_BLOCK
    LD R1
    IAC
    XCH R1         // Y = Y + 1
    JMS DRAW_BLOCK
    JUN FALL_LOOP

// =============================================================
// 4. Locking
// =============================================================
LAND_BLOCK:
    LD R1
    XCH R12        // Save Y
    LD R0
    XCH R13        // Save X
    JUN SPAWN_NEW

// =============================================================
// 5. Input
// =============================================================
CHECK_INPUT:
    FIM P4 0xF0
    SRC P4
    RDM
    JCN Z NO_INPUT

    XCH R2
    LDM 0
    WMP

    LD R2
    XCH R10

    // Left (1)
    CLC
    LDM 1
    XCH R3
    LD R10
    SUB R3
    JCN Z MOVE_LEFT

    // Right (2)
    CLC
    LDM 2
    XCH R3
    LD R10
    SUB R3
    JCN Z MOVE_RIGHT

NO_INPUT:
    BBL 0

// =============================================================
// 6-7. Shifts (Bounds: the block must not go into the walls)
// =============================================================
MOVE_LEFT:
    // If X == 6, cannot go further (wall at X=5)
    LD R0
    XCH R2
    LDM 5
    XCH R3
    LD R2
    SUB R3
    JCN Z NO_INPUT

    JMS CLEAR_BLOCK
    LD R0
    DAC
    XCH R0
    JMS DRAW_BLOCK
    BBL 0

MOVE_RIGHT:
    // If X == 9, cannot go further (wall at X=10)
    LD R0
    XCH R2
    LDM 8
    XCH R3
    LD R2
    SUB R3
    JCN Z NO_INPUT

    JMS CLEAR_BLOCK
    LD R0
    IAC
    XCH R0
    JMS DRAW_BLOCK
    BBL 0

// =============================================================
// 8-11. Drawing
// =============================================================
DRAW_BLOCK:
    LD R0
    XCH R6
    LD R1
    XCH R7
    JMS DRAW_PIXEL
    BBL 0

CLEAR_BLOCK:
    LD R0
    XCH R6
    LD R1
    XCH R7
    JMS CLEAR_PIXEL
    BBL 0

DRAW_PIXEL:
    FIM P4 0x00
    SRC P4
    LD R6
    WMP
    FIM P4 0x10
    SRC P4
    LD R7
    WMP
    FIM P4 0x80
    SRC P4
    LDM 1
    WMP
    BBL 0

CLEAR_PIXEL:
    FIM P4 0x00
    SRC P4
    LD R6
    WMP
    FIM P4 0x10
    SRC P4
    LD R7
    WMP
    FIM P4 0x80
    SRC P4
    LDM 0
    WMP
    BBL 0