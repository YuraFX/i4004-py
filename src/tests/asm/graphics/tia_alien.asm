// =================================================================
// Wide alien from Space Invaders (12x8) on TIA
// =================================================================
ORG 0x000

    // Configure port P0 on Chip 2, Register 15 (pixel output)
    FIM P0 0xF0      
    SRC P0           

    // Row 0 (Y=4): antennas (X=5, 10)
    LDM 5
    WMP
    LDM 4
    WMP
    LDM 10
    WMP
    LDM 4
    WMP

    // Row 1 (Y=5): antennas (X=6, 9)
    LDM 6
    WMP
    LDM 5
    WMP
    LDM 9
    WMP
    LDM 5
    WMP

    // Row 2 (Y=6): head (X=4..11)
    LDM 4
    WMP
    LDM 6
    WMP
    LDM 5
    WMP
    LDM 6
    WMP
    LDM 6
    WMP
    LDM 6
    WMP
    LDM 7
    WMP
    LDM 6
    WMP
    LDM 8
    WMP
    LDM 6
    WMP
    LDM 9
    WMP
    LDM 6
    WMP
    LDM 10
    WMP
    LDM 6
    WMP
    LDM 11
    WMP
    LDM 6
    WMP

    // Row 3 (Y=7): EYES (X=2,3,4, 6,7,8,9, 11,12,13)
    // Gaps at X=5 and X=10 are the eyes!
    LDM 2
    WMP
    LDM 7
    WMP
    LDM 3
    WMP
    LDM 7
    WMP
    LDM 4
    WMP
    LDM 7
    WMP
    LDM 6
    WMP
    LDM 7
    WMP
    LDM 7
    WMP
    LDM 7
    WMP
    LDM 8
    WMP
    LDM 7
    WMP
    LDM 9
    WMP
    LDM 7
    WMP
    LDM 11
    WMP
    LDM 7
    WMP
    LDM 12
    WMP
    LDM 7
    WMP
    LDM 13
    WMP
    LDM 7
    WMP

    // Row 4 (Y=8): body (X=2..13)
    LDM 2
    WMP
    LDM 8
    WMP
    LDM 3
    WMP
    LDM 8
    WMP
    LDM 4
    WMP
    LDM 8
    WMP
    LDM 5
    WMP
    LDM 8
    WMP
    LDM 6
    WMP
    LDM 8
    WMP
    LDM 7
    WMP
    LDM 8
    WMP
    LDM 8
    WMP
    LDM 8
    WMP
    LDM 9
    WMP
    LDM 8
    WMP
    LDM 10
    WMP
    LDM 8
    WMP
    LDM 11
    WMP
    LDM 8
    WMP
    LDM 12
    WMP
    LDM 8
    WMP
    LDM 13
    WMP
    LDM 8
    WMP

    // Row 5 (Y=9): belly (X=2,3, 5..10, 12,13)
    LDM 2
    WMP
    LDM 9
    WMP
    LDM 3
    WMP
    LDM 9
    WMP
    LDM 5
    WMP
    LDM 9
    WMP
    LDM 6
    WMP
    LDM 9
    WMP
    LDM 7
    WMP
    LDM 9
    WMP
    LDM 8
    WMP
    LDM 9
    WMP
    LDM 9
    WMP
    LDM 9
    WMP
    LDM 10
    WMP
    LDM 9
    WMP
    LDM 12
    WMP
    LDM 9
    WMP
    LDM 13
    WMP
    LDM 9
    WMP

    // Row 6 (Y=10): legs (X=2, 5, 10, 13)
    LDM 2
    WMP
    LDM 10
    WMP
    LDM 5
    WMP
    LDM 10
    WMP
    LDM 10
    WMP
    LDM 10
    WMP
    LDM 13
    WMP
    LDM 10
    WMP

    // Row 7 (Y=11): feet (X=5,6, 9,10)
    LDM 5
    WMP
    LDM 11
    WMP
    LDM 6
    WMP
    LDM 11
    WMP
    LDM 9
    WMP
    LDM 11
    WMP
    LDM 10
    WMP
    LDM 11
    WMP

    // Frame render trigger (VSYNC, Register 9)
    FIM P0 0x90
    SRC P0
    LDM 1
    WMP

    HLT