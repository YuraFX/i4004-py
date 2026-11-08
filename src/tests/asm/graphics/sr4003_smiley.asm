ORG 0x000

    // --- Top arc ---
    LDM 5
    XCH R6
    LDM 2
    XCH R7
    JMS DRAW_PIXEL
    LDM 6
    XCH R6
    JMS DRAW_PIXEL
    LDM 7
    XCH R6
    JMS DRAW_PIXEL
    LDM 8
    XCH R6
    JMS DRAW_PIXEL
    LDM 9
    XCH R6
    JMS DRAW_PIXEL
    LDM 10
    XCH R6
    JMS DRAW_PIXEL

    // --- Second row ---
    LDM 4
    XCH R6
    LDM 3
    XCH R7
    JMS DRAW_PIXEL
    LDM 11
    XCH R6
    JMS DRAW_PIXEL

    // --- Third row ---
    LDM 3
    XCH R6
    LDM 4
    XCH R7
    JMS DRAW_PIXEL
    LDM 12
    XCH R6
    JMS DRAW_PIXEL

    // --- Fourth row ---
    LDM 2
    XCH R6
    LDM 5
    XCH R7
    JMS DRAW_PIXEL
    LDM 13
    XCH R6
    JMS DRAW_PIXEL

    // --- Fifth row (left and right borders) ---
    LDM 1
    XCH R6
    LDM 6
    XCH R7
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Left eye (2x2) ---
    LDM 4
    XCH R6
    LDM 6
    XCH R7
    JMS DRAW_PIXEL
    LDM 5
    XCH R6
    JMS DRAW_PIXEL
    LDM 4
    XCH R6
    LDM 7
    XCH R7
    JMS DRAW_PIXEL
    LDM 5
    XCH R6
    JMS DRAW_PIXEL

    // --- Right eye (2x2) ---
    LDM 10
    XCH R6
    LDM 6
    XCH R7
    JMS DRAW_PIXEL
    LDM 11
    XCH R6
    JMS DRAW_PIXEL
    LDM 10
    XCH R6
    LDM 7
    XCH R7
    JMS DRAW_PIXEL
    LDM 11
    XCH R6
    JMS DRAW_PIXEL

    // --- Sixth row (sides) ---
    LDM 1
    XCH R6
    LDM 7
    XCH R7
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Seventh row (sides) ---
    LDM 1
    XCH R6
    LDM 8
    XCH R7
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Eighth row (sides) ---
    LDM 1
    XCH R6
    LDM 9
    XCH R7
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Ninth row (sides and smile corners) ---
    LDM 1
    XCH R6
    LDM 10
    XCH R7
    JMS DRAW_PIXEL
    LDM 3
    XCH R6
    JMS DRAW_PIXEL
    LDM 12
    XCH R6
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Tenth row (mouth corners) ---
    LDM 1
    XCH R6
    LDM 11
    XCH R7
    JMS DRAW_PIXEL
    LDM 4
    XCH R6
    JMS DRAW_PIXEL
    LDM 11
    XCH R6
    JMS DRAW_PIXEL
    LDM 14
    XCH R6
    JMS DRAW_PIXEL

    // --- Eleventh row (bottom of mouth) ---
    LDM 5
    XCH R6
    LDM 11
    XCH R7
    JMS DRAW_PIXEL
    LDM 6
    XCH R6
    JMS DRAW_PIXEL
    LDM 7
    XCH R6
    JMS DRAW_PIXEL
    LDM 8
    XCH R6
    JMS DRAW_PIXEL
    LDM 9
    XCH R6
    JMS DRAW_PIXEL
    LDM 10
    XCH R6
    JMS DRAW_PIXEL

    // --- Twelfth row (bottom) ---
    LDM 2
    XCH R6
    LDM 12
    XCH R7
    JMS DRAW_PIXEL
    LDM 13
    XCH R6
    JMS DRAW_PIXEL

    // --- Thirteenth row (bottom) ---
    LDM 3
    XCH R6
    LDM 13
    XCH R7
    JMS DRAW_PIXEL
    LDM 4
    XCH R6
    JMS DRAW_PIXEL
    LDM 11
    XCH R6
    JMS DRAW_PIXEL
    LDM 12
    XCH R6
    JMS DRAW_PIXEL

    // --- Fourteenth row (very bottom) ---
    LDM 5
    XCH R6
    LDM 14
    XCH R7
    JMS DRAW_PIXEL
    LDM 6
    XCH R6
    JMS DRAW_PIXEL
    LDM 7
    XCH R6
    JMS DRAW_PIXEL
    LDM 8
    XCH R6
    JMS DRAW_PIXEL
    LDM 9
    XCH R6
    JMS DRAW_PIXEL
    LDM 10
    XCH R6
    JMS DRAW_PIXEL

    HLT


// =================================================================
// PIXEL DRAWING SUBROUTINE
// Input: R6 = X, R7 = Y
// =================================================================
DRAW_PIXEL:
    FIM P0 0x00    // Register 0 (X)
    SRC P0
    LD R6
    WMP

    FIM P0 0x10    // Register 1 (Y)
    SRC P0
    LD R7
    WMP

    FIM P0 0x80    // Register 8 (Chip 2, Data)
    SRC P0
    LDM 1
    WMP

    BBL 0