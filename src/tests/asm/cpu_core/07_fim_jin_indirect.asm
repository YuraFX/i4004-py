// Test 7: Check indirect addressing and jumps via register pairs (FIM and JIN)
ORG 0x000
    FIM P0 0x08      // Load address 0x008 into pair P0 (R0 and R1)
    JIN P0           // Jump to the address in P0
    LDM 1            // Skipped
    HLT
ORG 0x008
    LDM 9            // The processor should end up here
    HLT